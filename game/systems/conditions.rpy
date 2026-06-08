# =============================================================================
# conditions.rpy — 状态/Buff 定义与运算机制
# 功能：定义状态静态数据库（CONDITIONS_DB）及运行时心跳更新机制
# 职责：管理状态挂载/移除、基础代谢 tick、昏阙恢复、死亡判定
# =============================================================================
# ── 状态类定义 ──
init python:
    class Condition:
        """状态静态原型：定义属性修正、致命性、持续时间、可堆叠性"""
        def __init__(self, id, name, desc, modifiers, b_fatal=False, duration=0.0, b_stackable=False):
            self.id = id
            self.name = name
            self.desc = desc            
            self.modifiers = modifiers  # 属性修正字典，如 {"fHungerRate": 1.5}
            self.b_fatal = b_fatal
            self.duration = duration    # 持续时间（小时），0=永久
            self.b_stackable = b_stackable

    class ActiveCondition:
        """运行时挂载在 Actor 上的动态状态实例"""
        def __init__(self, condition_id, duration=None):
            self.id = condition_id
            self.config = CONDITIONS_DB[condition_id]
            self.remaining_duration = duration if duration is not None else self.config.duration
    # ── 核心心跳函数 ──
    def tick_minutes(actor, minutes, thirst_multiplier=1.0):
        """每5分钟环境及状态心跳更新内核，应用基础代谢"""
        # 按分钟比例折算基础代谢
        apply_baseline_metabolism(
            actor,
            minutes,
            hunger_mult=actor.get_modifier_multiplier("fHungerRate"),
            thirst_mult=actor.get_modifier_multiplier("fThirstRate") * thirst_multiplier,
            fatigue_mult=actor.get_modifier_multiplier("fFatigueRate")
        )
        
        # 更新状态
        update_thirst_condition(actor)
        update_hunger_condition(actor)
        update_fatigue_condition(actor)
        
        # 动态状态心跳
        expired = []
        for ac in actor.active_conditions:
            if "fDamageOverTime" in ac.config.modifiers:
                actor.hp -= ac.config.modifiers["fDamageOverTime"] * (minutes / 60.0)
                clamp_hp(actor)
            if ac.config.duration > 0:
                ac.remaining_duration -= minutes / 60.0
                if ac.remaining_duration <= 0:
                    expired.append(ac)
        for ex in expired:
            actor.active_conditions.remove(ex)
        
        # ── 物品耐久度衰减（仅玩家背包和装备） ──
        if actor.is_player:
            global player_inventory
            if player_inventory is not None:
                hours = minutes / 60.0
                # 背包格子：衰减 + 耐久归零自动销毁
                for i, slot in enumerate(player_inventory.backpack_slots):
                    if slot is not None:
                        slot["item"].degrade(hours)
                        if slot["item"].durability <= 0:
                            player_inventory.backpack_slots[i] = None
                # 装备槽：衰减 + 耐久归零自动卸下
                for slot_name, item in list(player_inventory.slots.items()):
                    if item is not None:
                        item.degrade(hours)
                        if item.durability <= 0:
                            player_inventory.slots[slot_name] = None
                            if slot_name in ("backpack", "waist"):
                                player_inventory.refresh_backpack_grid()
        
        # 死亡判定
        if actor.hp <= 0:
            actor.hp = 0
            actor.b_dead = True

        # ── 尼古丁戒断检测（仅玩家） ──
        if actor.is_player and last_cigarette_hour >= 0:
            hours_since_last_smoke = (game_time['day'] - last_cigarette_day) * 24 + (game_time['hour'] - last_cigarette_hour)
            if cigarettes_smoked >= NICOTINE_SEVERE_THRESHOLD:
                if hours_since_last_smoke >= NICOTINE_SEVERE_HOURS:
                    if not any(ac.id == COND_NICOTINE_SEVERE for ac in actor.active_conditions):
                        actor.add_condition(COND_NICOTINE_SEVERE)
                        adventure_log.append("你的手指止不住地颤抖，冷汗从额头滑落。")
            elif cigarettes_smoked >= NICOTINE_MODERATE_THRESHOLD:
                if hours_since_last_smoke >= NICOTINE_MODERATE_HOURS:
                    if not any(ac.id == COND_NICOTINE_MODERATE for ac in actor.active_conditions):
                        actor.add_condition(COND_NICOTINE_MODERATE)
                        adventure_log.append("你已经好一阵子没碰到烟了。")
            elif cigarettes_smoked >= NICOTINE_MILD_THRESHOLD:          # ← 新增
                if hours_since_last_smoke >= NICOTINE_MILD_HOURS:       # ← 轻度：24小时未吸烟触发
                    if not any(ac.id == COND_NICOTINE_MILD for ac in actor.active_conditions):
                        actor.add_condition(COND_NICOTINE_MILD)
                        adventure_log.append("你有点想抽烟了。")

        # 自动生命恢复（无口渴/饥饿状态时缓慢回血）
        if actor.is_player and actor.hp < actor.max_hp:
            has_thirst_condition = any(
                ac.id in (COND_THIRST, COND_DEHYDRATED, COND_EXTREME_DEHYDRATED, COND_ORGAN_FAILURE)
                for ac in actor.active_conditions
            )
            has_hunger_condition = any(
                ac.id in (COND_HUNGER, COND_SEVERE_HUNGER, COND_EXTREME_HUNGER, COND_MALNUTRITION)
                for ac in actor.active_conditions
            )
            if not has_thirst_condition and not has_hunger_condition:
                hp_gain = AUTO_HP_RECOVERY_PER_5MIN * (minutes / 5.0)
                actor.hp = min(actor.max_hp, actor.hp + hp_gain)

        # 濒死自动移除（HP ≥ 30% 时）
        if actor.hp >= actor.max_hp * MORIBUND_HP_THRESHOLD:
            remove_condition_by_id(actor, COND_MORIBUND)

    def check_player_death(actor, death_label="game_over_death"):
        """检查角色是否死亡（HP ≤ 0），死亡则跳转至指定标签。
        注意：会中断当前 Ren'Py 流程，不返回调用处。
        """
        clamp_hp(actor)

        # 死亡判定：HP 归零
        death_triggered = False

        if actor.hp <= 0:
            actor.hp = 0
            actor.b_dead = True
            death_triggered = True

        # 死亡则跳转
        if death_triggered:
            renpy.jump(death_label)

    # =============================================================================
    # 状态数据库注册表
    # 功能：向 CONDITIONS_DB 注册所有状态原型
    # =============================================================================
    # ── 生理状态（口渴/饥饿系列） ──
    CONDITIONS_DB[COND_THIRST] = Condition(
        COND_THIRST,
        "口渴",
        "喉咙干涩，身体开始发出缺水的信号。",
        modifiers={"fFatigueRate": 0.2},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_HUNGER] = Condition(
        COND_HUNGER,
        "饥饿",
        "腹中空空，身体开始消耗储备的脂肪。",
        modifiers={"fFatigueRate": 0.15},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_SEVERE_HUNGER] = Condition(
        COND_SEVERE_HUNGER,
        "重度饥饿",
        "胃酸在空荡荡的胃里翻搅，四肢开始发软。",
        modifiers={"fFatigueRate": 0.30},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_EXTREME_HUNGER] = Condition(
        COND_EXTREME_HUNGER,
        "极度饥饿",
        "你的身体开始分解自己的肌肉来获取能量。再不进食就危险了。",
        modifiers={"fFatigueRate": 0.50, "fDamageOverTime": 1.2, "fHitChance": -0.15},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_MALNUTRITION] = Condition(
        COND_MALNUTRITION,
        "营养不良",
        "长期的饥饿让你的器官开始衰竭，身体正在不可逆转地走向崩溃。",
        modifiers={"fFatigueRate": 0.80, "fDamageOverTime": 5.0, "fHitChance": -0.35},
        b_fatal=True,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_DEHYDRATED] = Condition(
        COND_DEHYDRATED,
        "脱水",
        "脱水使你感到虚弱和头晕。",
        modifiers={"fFatigueRate": 0.4, "fDamageOverTime": 1.0},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_EXTREME_DEHYDRATED] = Condition(
        COND_EXTREME_DEHYDRATED,
        "极度脱水",
        "你的身体正在干涸，意识开始模糊，再不喝水就来不及了。",
        modifiers={"fFatigueRate": 0.6, "fDamageOverTime": 5.0, "fHitChance": -0.15},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_ORGAN_FAILURE] = Condition(
        COND_ORGAN_FAILURE,
        "器官衰竭",
        "肾脏和肝脏已经停止工作，身体正在从内部崩溃。死亡只是时间问题。",
        modifiers={"fFatigueRate": 1.0, "fDamageOverTime": 19.0, "fHitChance": -0.35},
        b_fatal=True,
        duration=0.0,
        b_stackable=False
    )

    # ── 脚部状态 ──
    CONDITIONS_DB[COND_BARE_FOOT] = Condition(
        COND_BARE_FOOT,
        "赤脚",
        "你光着脚踩在冰冷或滚烫的废墟地面上。每一脚下去，都不知道会碰到什么。",
        modifiers={},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_CUT_FOOT] = Condition(
        COND_CUT_FOOT,
        "脚底割伤",
        "碎玻璃或锈铁片划开了你的脚底。每走一步，都在地上留下淡淡的血印。",
        modifiers={"fDamageOverTime": 1.2},  
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    # ── 战斗状态 ──
    CONDITIONS_DB[COND_SHELTER] = Condition(
        COND_SHELTER,
        "进入掩体",
        "进入了掩体，降低受到的直接伤害。",
        modifiers={"fDamageCut": -0.2, "fDodgeBonus": 0.3},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_PRONE] = Condition(
        COND_PRONE,
        "摔倒",
        "你摔倒在地，必须站起来才能继续行动。",
        b_stackable=False,
        modifiers={"fDodgeBonus": -0.30}
    )

    CONDITIONS_DB[COND_MORIBUND] = Condition(
        COND_MORIBUND,
        "濒死",
        "生命垂危，随时可能倒下。",
        modifiers={},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_DEAD] = Condition(
        COND_DEAD,
        "死亡",
        "已经失去了生命迹象。",
        modifiers={},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    # ── 疲劳状态 ──
    CONDITIONS_DB[COND_FATIGUE] = Condition(
        COND_FATIGUE,
        "疲劳",
        "疲劳使你的行动变得迟缓。",
        modifiers={"fFatigueRate": 0.2},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_SEVERE_FATIGUE] = Condition(
        COND_SEVERE_FATIGUE,
        "重度疲劳",
        "重度疲劳让你的身体几乎无法行动。",
        modifiers={"fFatigueRate": 0.4},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_FAINT] = Condition(  
        COND_FAINT,
        "睡觉中",
        "你正在睡眠中恢复疲劳。",
        modifiers={"fFatigueRate": -0.5},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    # ── 伤害/减益状态 ──
    CONDITIONS_DB[COND_BLEED] = Condition(
        COND_BLEED,
        "流血",
        "伤口持续渗出血液，每回合损失少量生命值。",
        modifiers={
            "fDamageOverTime": 1.5,
            "fHitChance": -0.15,  # 命中率 -15%
        },
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_POISON] = Condition( 
        COND_POISON,
        "中毒",
        "不知名的毒素在体内扩散，疲劳值加速积累。",
        modifiers={"fFatigueRate": 0.3, "fDamageOverTime": 0.5},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_STAGGER] = Condition(
        COND_STAGGER,
        "失衡",
        "脚步踉跄，行动消耗额外疲劳。",
        modifiers={
            "fFatigueRate": 0.3,
            "fHitChance": -0.20,   # 命中率 -20%
            "fDodgeBonus": -0.15,  # 闪避率 -15%
        },
        b_fatal=False,
        duration=0.25,
        b_stackable=False
    )

    CONDITIONS_DB[COND_ENTANGLED] = Condition(
        COND_ENTANGLED,
        "被缠绕",
        "双腿被藤蔓、蛛网或根系捆住，无法移动。",
        modifiers={
            "fMoveSpeedFactor": 0.0,
            "fDodgeBonus": -0.50,  # 闪避率 -50%
            "fHitChance": -0.10,   # 命中率 -10%
        },
        b_fatal=False,
        duration=0.083,
        b_stackable=False
    )

    CONDITIONS_DB[COND_FRACTURE] = Condition(  
        COND_FRACTURE,
        "骨折",
        "骨骼断裂导致行动困难，闪避大幅下降，无法使用高消耗动作。需要夹板固定治疗。",
        modifiers={
            "fDodgeBonus": -0.30,   # 闪避率 -30%
            "fHitChance": -0.20,    # 命中率 -20%
        },
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_INTERNAL_INJURY] = Condition(  
        COND_INTERNAL_INJURY,
        "内伤",
        "内伤影响身体机能，你现在很虚弱。",
        modifiers={"fHealingRate": -0.5},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )
    
    # ── NPC 词条状态 ──
    CONDITIONS_DB[TRAIT_WEAK] = Condition(
        TRAIT_WEAK,
        "虚弱",
        "身体瘦弱，长期营养不良，肋骨透过皮毛清晰可见。",
        modifiers={"fMaxHpMultiplier": -0.30},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_FRAIL] = Condition(
        TRAIT_FRAIL,
        "孱弱",
        "它的肌肉萎缩，骨骼脆弱，既打不疼别人，也挨不住几下。",
        modifiers={"fDamageBonus": -0.15, "fDamageCut": 0.15},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_SLUGGISH] = Condition(
        TRAIT_SLUGGISH,
        "迟缓",
        "反应像是慢了半拍，攻击常常落空，闪避也总是慢一步。",
        modifiers={"fHitChance": -0.10, "fDodgeBonus": -0.10},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_DECAYING] = Condition(
        TRAIT_DECAYING,
        "衰竭",
        "它的身体机能正在衰退，每动一下都气喘吁吁，嘴唇干裂得说不出话。",
        modifiers={"fThirstRate": 0.25, "fFatigueRate": 0.25},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_FOCUSED] = Condition(
        TRAIT_FOCUSED,
        "专注",
        "它的感官异常敏锐，每一次攻击都经过精确计算，每一次闪避都恰到好处。",
        modifiers={"fHitChance": 0.08, "fDodgeBonus": 0.08},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_DROUGHT_RESISTANT] = Condition(
        TRAIT_DROUGHT_RESISTANT,
        "耐渴",
        "适应了干旱环境，能在烈日下行走很久而不需要找水。",
        modifiers={"fThirstRate": -0.25},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_ENERGETIC] = Condition(
        TRAIT_ENERGETIC,
        "精力充沛",
        "它似乎永远不会累，动作迅捷而有力，仿佛体内装了一台永动机。",
        modifiers={"fFatigueRate": -0.20},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_TOUGH] = Condition(
        TRAIT_TOUGH,
        "强硬",
        "肌肉结实，皮肤厚得像旧轮胎，普通的攻击很难在它身上留下痕迹。",
        modifiers={"fMaxHpMultiplier": 0.30},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_FEROCIOUS] = Condition(
        TRAIT_FEROCIOUS,
        "凶猛",
        "每一次攻击都带着同归于尽的狠劲，仿佛不知道什么是疼痛。",
        modifiers={"fDamageBonus": 0.25},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[TRAIT_EASTER_EGG] = Condition(
        TRAIT_EASTER_EGG,
        "彩蛋",
        "？？？",
        modifiers={},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    # ── 尼古丁成瘾状态 ──
    CONDITIONS_DB[COND_NICOTINE_MILD] = Condition(
        COND_NICOTINE_MILD,
        "尼古丁依赖",
        "你开始习惯在紧张时点上一支，烟雾让紧绷的神经松弛下来。",
        modifiers={"fHitChance": -0.01},  # 轻度减命中 1%
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_NICOTINE_MODERATE] = Condition(
        COND_NICOTINE_MODERATE,
        "尼古丁成瘾",
        "没有烟的时候，你的手指会不自觉地摸向口袋。注意力开始涣散，脾气变得暴躁。",
        modifiers={"fHitChance": -0.05, "fFatigueRate": 0.10},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_NICOTINE_SEVERE] = Condition(
        COND_NICOTINE_SEVERE,
        "尼古丁沉溺",
        "没有尼古丁，你的手会抖，牙关会紧咬，整个人像一台缺少机油的引擎。",
        modifiers={"fHitChance": -0.15, "fFatigueRate": 0.25},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )