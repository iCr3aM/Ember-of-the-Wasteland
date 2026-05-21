# =============================================================================
# # 状态/Buff定义与运算机制
# # 定义：状态/Buff/疾病静态数据库（`CONDITIONS_DB`，如流血、骨折、流感、饥饿、脱水，致命性等）。
# # 实现：状态的心跳更新机制（每过一小时/每一回合，计算脱水加重、伤口感染恶化、扣除对应生命值）。
# =============================================================================
# 状态编号统一管理 - 从 constants.rpy 移入
init -200 python:
    # 战斗状态
    COND_BLEED = 201                # 流血
    COND_POISON = 202               # 中毒
    COND_STAGGER = 203              # 失衡
    COND_ENTANGLED = 204            # 被缠绕
    COND_FRACTURE = 205             # 骨折
    COND_INTERNAL_INJURY = 206      # 内伤
    COND_DEFENSE = 207              # 全力防御

    # 疾病状态
    COND_THIRST = 301
    COND_HUNGER = 302
    COND_DEHYDRATED = 303
    COND_EXTREME_DEHYDRATED = 304
    COND_SHELTER = 491

    # 疲劳状态
    COND_FATIGUE = 401
    COND_SEVERE_FATIGUE = 402
    COND_FAINT = 403

    # 口渴状态元组（用于批量清除）
    CONDITIONAL_THIRST_IDS = (COND_THIRST, COND_DEHYDRATED, COND_EXTREME_DEHYDRATED)

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
        "掩体掩护",
        "进入掩体姿态，降低受到的直接伤害。",
        modifiers={"fDamageCut": -0.2},
        b_fatal=False,
        duration=1.0,
        b_stackable=False
    )
    
    CONDITIONS_DB[COND_FATIGUE] = Condition(
        COND_FATIGUE,
        "疲劳",
        "疲劳使你的行动变得迟缓，战斗行动点-2。",
        modifiers={"fFatigueRate": 0.2, "fAP_Cut": -2},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_SEVERE_FATIGUE] = Condition(
        COND_SEVERE_FATIGUE,
        "重度疲劳",
        "重度疲劳让你的身体几乎无法行动，战斗行动点-4。",
        modifiers={"fFatigueRate": 0.4, "fAP_Cut": -4},
        b_fatal=False,
        duration=0.0,
        b_stackable=False
    )

    CONDITIONS_DB[COND_FAINT] = Condition(  #ID 403
        COND_FAINT,
        "睡觉中",
        "你正在睡眠中恢复疲劳。",
        modifiers={"fFatigueRate": -0.5, "fAP_Cut": -100},
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
        b_stackable=True
    )

    CONDITIONS_DB[COND_STAGGER] = Condition(
        COND_STAGGER,
        "失衡",
        "脚步踉跄，行动消耗额外疲劳。",
        modifiers={
            "fFatigueRate": 0.3,
            "fHitChance": -0.20,   # ← 新增：失衡降低命中率20%
            "fDodgeBonus": -0.15,  # ← 新增：失衡降低闪避率15%
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
            "fDodgeBonus": -0.50,  # ← 新增：被缠绕降低闪避率50%
            "fHitChance": -0.10,   # ← 新增：轻微影响命中率
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
        if actor.thirst > THIRST_THRESHOLDS['extreme_dehydrated']:
            thirst_state = COND_EXTREME_DEHYDRATED
        elif actor.thirst > THIRST_THRESHOLDS['dehydrated']:
            thirst_state = COND_DEHYDRATED
        elif actor.thirst > THIRST_THRESHOLDS['thirst']:
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
        update_fatigue_condition(actor)  # 新增：每次移动后也检查疲劳状态
        return hunger_cost, thirst_cost, fatigue_cost

    def consume_combat_costs(actor, action_type):
        """为战斗行动扣除饥饿、口渴、疲劳代谢。"""
        costs = COMBAT_ACTION_COSTS.get(action_type, {})
        hunger_cost = costs.get('hunger', 0.0) * actor.get_modifier_multiplier('fHungerRate')
        thirst_cost = costs.get('thirst', 0.0) * actor.get_modifier_multiplier('fThirstRate')
        fatigue_cost = costs.get('fatigue', 0.0) * actor.get_modifier_multiplier('fFatigueRate')

        actor.hunger = min(100.0, actor.hunger + hunger_cost)
        actor.thirst = min(100.0, actor.thirst + thirst_cost)
        actor.fatigue = min(100.0, actor.fatigue + fatigue_cost)

        if actor.thirst >= 100.0:
            actor.b_dead = True

        update_thirst_condition(actor)
        update_fatigue_condition(actor)
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
            if actor.hp < 0:
                actor.hp = 0.0
        if actor.thirst >= 100:
            actor.b_dead = True
            actor.hp = max(0, actor.hp) # 立即死亡，HP归零

            # =====  hp 下限保护 =====
        if actor.hp < 0:
            actor.hp = 0.0

        # 若在昏阙状态，自动恢复疲劳
        if any(ac.id == COND_FAINT for ac in actor.active_conditions):
            actor.fatigue = max(0.0, actor.fatigue - 20.0 * hours)  # 每小时恢复20点疲劳
            if actor.fatigue <= FATIGUE_THRESHOLDS['fatigue']:
                # 恢复清醒
                active_condition_configs = [ac.config.name for ac in actor.active_conditions]
                for ac in list(actor.active_conditions):
                    if ac.id == COND_FAINT:
                        # 使用临时列表避免迭代时修改
                        pass
        update_fatigue_condition(actor)

        # 3. 动态状态心跳与衰减
        expired = []
        for ac in actor.active_conditions:
            # 应用周期性伤害或效果
            if "fDamageOverTime" in ac.config.modifiers:
                actor.hp -= ac.config.modifiers["fDamageOverTime"] * hours
                # ===== 持续伤害后的 hp 下限保护 =====
                if actor.hp < 0:
                    actor.hp = 0.0
                
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