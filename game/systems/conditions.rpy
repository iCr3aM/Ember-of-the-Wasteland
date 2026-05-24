# =============================================================================
# # 状态/Buff定义与运算机制
# # 定义：状态/Buff/疾病静态数据库（`CONDITIONS_DB`，如流血、骨折、流感、饥饿、脱水，致命性等）。
# # 实现：状态的心跳更新机制（每过一小时/每一回合，计算脱水加重、伤口感染恶化、扣除对应生命值）。
# =============================================================================
init python:
    class Condition:
        """对应 conditions.xml 结构"""
        def __init__(self, id, name, desc, modifiers, b_fatal=False, duration=0.0, b_stackable=False):
            self.id = id
            self.name = name
            self.desc = desc            
            self.modifiers = modifiers  # 字典型，例如 {"fHungerRate": 1.5, "fMaxHP": -20}
            self.b_fatal = b_fatal
            self.duration = duration    # 持续小时数，0为永久
            self.b_stackable = b_stackable

    class ActiveCondition:
        """运行时挂载在 Actor 上的动态状态实例"""
        def __init__(self, condition_id, duration=None):
            self.id = condition_id
            self.config = CONDITIONS_DB[condition_id]
            self.remaining_duration = duration if duration is not None else self.config.duration

    # =============================================================================
    # 基础状态列表
    # =============================================================================
    CONDITIONS_DB[COND_THIRST] = Condition(
        COND_THIRST,
        "口渴",
        "口渴使得你难以集中注意力，并加速体力与生命的消耗。",
        modifiers={"fThirstRate": 0.2, "fFatigueRate": 0.1},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_HUNGER] = Condition(
        COND_HUNGER,
        "饥饿",
        "饥饿状态使身体疲劳更快，生命恢复变慢。",
        modifiers={"fHungerRate": 0.5},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_DEHYDRATED] = Condition(
        COND_DEHYDRATED,
        "脱水",
        "脱水使你感到虚弱、头晕，并降低整体抗性。",
        modifiers={"fThirstRate": 0.4, "fHungerRate": 0.1, "fDamageOverTime": 1.0},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_EXTREME_DEHYDRATED] = Condition(
        COND_EXTREME_DEHYDRATED,
        "极度脱水",
        "极度脱水正在侵蚀你的生命，若不及时补水将会死亡。",
        modifiers={"fThirstRate": 0.7, "fHungerRate": 0.2, "fDamageOverTime": 3.0},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_SHELTER] = Condition(
        COND_SHELTER,
        "闪避",
        "进入闪避姿态，降低受到的直接伤害。",
        modifiers={"fDamageCut": -0.2},
        b_fatal=False,
        duration=1.0,
        b_stackable=False
    )
    
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

    CONDITIONS_DB[COND_FAINT] = Condition(  #ID 403
        COND_FAINT,
        "睡觉中",
        "你正在睡眠中恢复疲劳。",
        modifiers={"fFatigueRate": -0.5},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_BLEED] = Condition(
        COND_BLEED,
        "流血",
        "伤口持续渗出血液，每回合损失少量生命值。",
        modifiers={
            "fDamageOverTime": 1.5,
            "fHitChance": -0.15,  # 流血降低命中率15%
        },
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_POISON] = Condition(  #ID 202
        COND_POISON,
        "中毒",
        "虫毒或化学毒素在体内扩散，疲劳值加速积累。",
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
            "fHitChance": -0.20,   # ← 失衡降低命中率20%
            "fDodgeBonus": -0.15,  # ← 失衡降低闪避率15%
        },
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_ENTANGLED] = Condition(
        COND_ENTANGLED,
        "被缠绕",
        "双腿被藤蔓、蛛网或根系捆住，无法移动。",
        modifiers={
            "fMoveSpeedFactor": 0.0,
            "fDodgeBonus": -0.50,  # ← 被缠绕降低闪避率50%
            "fHitChance": -0.10,   # ← 轻微影响命中率
        },
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_FRACTURE] = Condition(  #ID 205
        COND_FRACTURE,
        "骨折",
        "骨折导致行动受限，移动速度和战斗能力下降。",
        modifiers={"fMovementSpeed": -0.3, "fCombatEffectiveness": -0.2},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_INTERNAL_INJURY] = Condition(  #ID 206
        COND_INTERNAL_INJURY,
        "内伤",
        "内伤影响身体机能，导致生命恢复速度减慢。",
        modifiers={"fHealingRate": -0.5},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_DEFENSE] = Condition(  #ID 207
        COND_DEFENSE,
        "全力防御",
        "放弃攻击，专注格挡与闪避，受到的伤害大幅降低。",
        modifiers={"fDamageCut": -0.4, "fDodgeBonus": 0.3},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    def update_thirst_condition(actor):
        """根据当前口渴值自动维护口渴/脱水状态。"""
        thirst_state = None
        if actor.thirst >= THIRST_THRESHOLDS['extreme_dehydrated']:
            thirst_state = COND_EXTREME_DEHYDRATED
        elif actor.thirst >= THIRST_THRESHOLDS['dehydrated']:
            thirst_state = COND_DEHYDRATED
        elif actor.thirst >= THIRST_THRESHOLDS['thirst']:
            thirst_state = COND_THIRST

        # 清除旧的口渴相关状态
        actor.active_conditions = [ac for ac in actor.active_conditions if ac.id not in CONDITIONAL_THIRST_IDS]

        if thirst_state is not None:
            actor.add_condition(thirst_state)

    def update_fatigue_condition(actor):
        """根据当前疲劳值自动维护疲劳状态。"""
        # 清除旧疲劳状态
        actor.active_conditions = [ac for ac in actor.active_conditions if ac.id not in (COND_FATIGUE, COND_SEVERE_FATIGUE, COND_FAINT)]
    
        if actor.fatigue >= FATIGUE_THRESHOLDS['faint']:
            actor.add_condition(COND_FAINT)
        elif actor.fatigue >= FATIGUE_THRESHOLDS['severe_fatigue']:
            actor.add_condition(COND_SEVERE_FATIGUE)
        elif actor.fatigue >= FATIGUE_THRESHOLDS['fatigue']:
            actor.add_condition(COND_FATIGUE)

    def consume_travel_costs(actor, steps=1):
        """移动时消耗饥饿、口渴和疲劳，并刷新口渴状态。"""
        hunger_cost = TRAVEL_COSTS['hunger_per_step'] * steps * actor.get_modifier_multiplier("fHungerRate")
        thirst_cost = TRAVEL_COSTS['thirst_per_step'] * steps * actor.get_modifier_multiplier("fThirstRate")
        fatigue_cost = TRAVEL_COSTS['fatigue_per_step'] * steps * actor.get_modifier_multiplier("fFatigueRate")
        actor.hunger += hunger_cost
        actor.thirst += thirst_cost
        actor.fatigue += fatigue_cost
        actor.hunger = min(actor.hunger, 100.0)
        actor.thirst = min(actor.thirst, 100.0)
        actor.fatigue = min(actor.fatigue, 100.0)
        update_thirst_condition(actor)
        update_fatigue_condition(actor)  # 每次移动后也检查疲劳状态
        return hunger_cost, thirst_cost, fatigue_cost

    def tick_hour(actor, hours=1):
        """每小时环境及状态心跳更新内核"""
        # 1. 基础代谢更新
        actor.hunger += actor.get_modifier_multiplier("fHungerRate") * METABOLISM_PER_HOUR['hunger'] * hours
        actor.thirst += actor.get_modifier_multiplier("fThirstRate") * METABOLISM_PER_HOUR['thirst'] * hours
        actor.fatigue += actor.get_modifier_multiplier("fFatigueRate") * METABOLISM_PER_HOUR['fatigue'] * hours

        # ===== 确保代谢值不超过上限 =====
        actor.hunger = min(actor.hunger, 100.0)
        actor.thirst = min(actor.thirst, 100.0)
        actor.fatigue = min(actor.fatigue, 100.0)

        # 根据口渴值自动更新口渴/脱水状态
        update_thirst_condition(actor)
        update_fatigue_condition(actor)  # 每小时也检查疲劳状态

        # 2. 生物指标过载扣血判定
        if actor.hunger >= 100:
            actor.hp -= 5 * hours
            clamp_hp(actor)
        if actor.thirst >= 100:
            actor.b_dead = True
            actor.hp = max(0, actor.hp) # 立即死亡，HP归零

        # 3. 动态状态心跳与衰减
        expired = []
        for ac in actor.active_conditions:
            # 应用周期性伤害或效果
            if "fDamageOverTime" in ac.config.modifiers:
                actor.hp -= ac.config.modifiers["fDamageOverTime"] * hours
                clamp_hp(actor)
                
            if ac.config.duration > 0:
                ac.remaining_duration -= hours
                if ac.remaining_duration <= 0:
                    expired.append(ac)
                    
        # 移除过期状态
        for ex in expired:
            actor.active_conditions.remove(ex)
            
        # 4. 死亡判定
        if actor.hp <= 0:
            actor.hp = 0
            actor.b_dead = True

    def check_player_death(actor, death_label="game_over_dehydration"):
        """检查角色是否死亡（HP <= 0 或渴死），如果死亡则跳转到指定标签。
        注意：这会中断当前 Ren'Py 流程，不会返回到调用处。
        """
        clamp_hp(actor)

        # ===== 死亡判定：HP 归零 或 渴死 =====
        death_triggered = False

        if actor.thirst >= 100.0:
            actor.thirst = 100.0
            actor.hp = 0
            actor.b_dead = True
            death_triggered = True

        if actor.hp <= 0:
            actor.hp = 0
            actor.b_dead = True
            death_triggered = True

        # ===== 如果死亡，跳转到死亡标签 =====
        if death_triggered:
            renpy.jump(death_label)

    def check_and_apply_faint(actor, combat_instance=None, is_player=False):
        """
        通用昏阙检测与状态应用。
        参数：
            actor: Actor对象
            combat_instance: Combat对象（可选），如果有则附加战斗日志
            is_player: 是否是玩家触发
        返回：
            bool — 是否触发了昏阙
        """
        if actor.fatigue >= FATIGUE_THRESHOLDS['faint']:
            actor.fatigue = 100.0
            update_fatigue_condition(actor)
            if combat_instance:
                combat_instance.combat_log.append(f"{actor.name} 因为太过疲劳而昏阙了！")
                if is_player:
                    combat_instance.player_acted_this_turn = True
                else:
                    combat_instance.is_player_turn = True
            return True
        return False

    def check_and_trigger_faint_travel(actor):
        """
        大地图模式下的昏阙检测与触发。
        如果 fatigue >= 100，返回 True 表示触发昏阙，由调用者决定跳转事件。
        这个函数只做检测和状态更新，不执行跳转（因为 Ren'Py 跳转需要 label）。
        """
        if actor.fatigue >= FATIGUE_THRESHOLDS['faint']:
            actor.fatigue = 100.0
            update_fatigue_condition(actor)
            return True
        return False


    def remove_condition_by_id(actor, condition_id):
        """通用方法：从actor身上移除指定状态ID。"""
        for ac in list(actor.active_conditions):
            if ac.id == condition_id:
                actor.active_conditions.remove(ac)
                return True
        return False


    def is_fainted(actor):
        """判断角色是否处于昏阙状态（使用常量而非硬编码字符串）"""
        return any(ac.id == COND_FAINT for ac in actor.active_conditions)


    def faint_recovery_check(combat_instance):
        """
        昏阙恢复逻辑：每回合计数，3回合后自动解除。
        支持双方恢复：玩家使用 player_faint_counter，敌人使用 enemy_faint_counter。
        """
        any_recovered = False

        # ── 玩家恢复 ──
        if is_fainted(combat_instance.player):
            combat_instance.player_faint_counter += 1
            if combat_instance.player_faint_counter >= 3:
                remove_condition_by_id(combat_instance.player, COND_FAINT)
                # ★ 恢复时将疲劳值降到昏阙阈值以下（70-80之间）
                combat_instance.player.fatigue = max(0, combat_instance.player.fatigue - 60.0)  # 降低60
                if combat_instance.player.fatigue >= FATIGUE_THRESHOLDS['faint']:
                    combat_instance.player.fatigue = FATIGUE_THRESHOLDS['faint'] - 1.0
                combat_instance.player_faint_counter = 0
                combat_instance.combat_log.append("你在喘息中稍稍恢复了一些意识，又可以行动了。")
                any_recovered = True
        else:
            combat_instance.player_faint_counter = 0  # 重置计数器

        # ── 敌人恢复 ──
        if is_fainted(combat_instance.enemy):
            combat_instance.enemy_faint_counter += 1
            if combat_instance.enemy_faint_counter >= 3:
                remove_condition_by_id(combat_instance.enemy, COND_FAINT)
                # ★ 同样降低疲劳值
                combat_instance.enemy.fatigue = max(0, combat_instance.enemy.fatigue - 60.0)
                if combat_instance.enemy.fatigue >= FATIGUE_THRESHOLDS['faint']:
                    combat_instance.enemy.fatigue = FATIGUE_THRESHOLDS['faint'] - 1.0
                combat_instance.enemy_faint_counter = 0
                combat_instance.combat_log.append(f"{combat_instance.enemy.name} 恢复了意识，重新站了起来。")
                any_recovered = True
        else:
            combat_instance.enemy_faint_counter = 0
        
        return any_recovered