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

    def tick_minutes(actor, minutes=5):
        """每5分钟环境及状态心跳更新内核"""
        # 1. 基础代谢更新（按分钟比例折算）
        apply_baseline_metabolism(
            actor,
            minutes,
            hunger_mult=actor.get_modifier_multiplier("fHungerRate"),
            thirst_mult=actor.get_modifier_multiplier("fThirstRate"),
            fatigue_mult=actor.get_modifier_multiplier("fFatigueRate")
        )
        
        # 更新状态
        update_thirst_condition(actor)
        update_fatigue_condition(actor)
        
        # 2. 生物指标过载扣血判定（按分钟比例）
        if actor.hunger >= 100:
            actor.hp -= 5 * (minutes / 60.0)
            clamp_hp(actor)
        if actor.thirst >= 100:
            actor.b_dead = True
            actor.hp = 0
        
        # 3. 动态状态心跳
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