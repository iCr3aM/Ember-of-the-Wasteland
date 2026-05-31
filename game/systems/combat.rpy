# game/systems/combat.rpy
init -180 python:
    import random
    # ===== 命中率基础配置 =====
    BASE_HIT_CHANCE = 0.85  # 基础命中率 85%
    
    # 距离修正（距离越远，命中率越低）
    RANGE_HIT_MODIFIERS = {
        "point_blank": (1, 2, 1.0),    # 近身：-0%（基准）
        "close": (3, 5, 0.9),          # 近距离：-10%
        "medium": (6, 10, 0.75),       # 中距离：-25%
        "long": (11, 15, 0.55),        # 远距离：-45%
        "extreme": (16, 20, 0.40),     # 极限距离：-60%
    }
    
    # 武器类型命中率基数
    WEAPON_HIT_BASE = {
        "melee": 0.95,    # 近战武器
        "pistol": 0.80,   # 手枪
        "rifle": 0.75,    # 步枪
        "throw": 0.60,    # 投掷/杂物
        "natural": 0.85,  # 天生武器（爪、牙等）
    }
    
    # 闪避基础值
    BASE_DODGE_CHANCE = 0.10  # 基础闪避率 10%

    _current_combat_instance = None


    class CombatSystem:
        def __init__(self, player, enemy_instance):
            self.player = player
            self.enemy = enemy_instance
            self.range = renpy.random.randint(8, 16) # 初始距离随机在 8-16 米之间
            self.combat_log = ["战斗开始！你遭遇了 " + enemy_instance.name]
            self.is_finished = False
            self.winner = None
            self.player_turn_disabled_by_inventory = False
            self.loot_drops = []
            self.corpse_searched = False
            self.is_player_turn = True
            self.player_acted_this_turn = False
            self.player_faint_counter = 0
            self.enemy_faint_counter = 0
            self.entangle_cooldown = 0  # 缠绕冷却回合数
        
        def fade_out_music(self):
            """战斗开始时淡出背景音乐（1.5秒渐弱）。"""
            if renpy.music.get_playing():
                renpy.music.stop(fadeout=1.5)
        
        def restore_music(self):
            """战斗结束后恢复大地图探索音乐。"""
            renpy.music.play("audio/bgm_explore.mp3", fadein=1.0, loop=True)


        def can_player_act(self):
            """检查玩家是否可以执行战术动作/攻击（非昏阙、未行动、战斗未结束）。"""
            return (not self.player_acted_this_turn 
                    and not self.is_finished 
                    and not is_fainted(self.player)
                    and not self.player_turn_disabled_by_inventory)

        # ================== 命中率相关方法 ==================
        
        def calculate_hit_chance(self, attack_mode, is_player=True):
            """计算命中率"""
            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player
            
            # 确定武器类型
            weapon_type = self._determine_weapon_type(attack_mode)
            base_hit = WEAPON_HIT_BASE.get(weapon_type, BASE_HIT_CHANCE)
            
            # 距离修正
            range_mod = self._get_range_modifier(self.range)
            
            # 状态修正
            user_cond_mod = self._get_condition_hit_modifier(user)
            target_cond_mod = self._get_condition_dodge_modifier(target)
            
            # 计算最终命中率
            hit_chance = base_hit * range_mod * user_cond_mod
            dodge_chance = BASE_DODGE_CHANCE * target_cond_mod
            
            # 限制范围 5%-99%
            final_hit = max(0.05, min(0.99, hit_chance - dodge_chance))
            
            return final_hit
        
        def _determine_weapon_type(self, attack_mode):
            """根据攻击模式对象 ID 查找武器类型（melee/pistol/rifle/throw/natural）"""
            for ids, weapon_type in WEAPON_TYPE_RULES:
                if attack_mode.id in ids:
                    return weapon_type
            return "melee"  # 默认回退
        
        def _get_range_modifier(self, current_range):
            """根据当前战斗距离（米）返回命中率修正系数。使用 RANGE_HIT_MODIFIERS 表进行区间映射。"""
            for zone_name, (min_r, max_r, modifier) in RANGE_HIT_MODIFIERS.items():
                if min_r <= current_range <= max_r:
                    return modifier
            return 0.5  # 超出所有范围
        
        def _get_condition_hit_modifier(self, actor):
            """计算 actor 当前挂载的所有状态对命中率的累加修正（基于 fHitChance 键）。返回倍率值。"""
            modifier = 1.0
            for ac in actor.active_conditions:
                if "fHitChance" in ac.config.modifiers:
                    modifier += ac.config.modifiers["fHitChance"]
            return max(0.0, modifier)
        
        def _get_condition_dodge_modifier(self, actor):
            """计算状态对闪避率的修正"""
            modifier = 1.0
            for ac in actor.active_conditions:
                if "fDodgeBonus" in ac.config.modifiers:
                    modifier += ac.config.modifiers["fDodgeBonus"]
            return max(0.0, modifier)
        
        def _get_condition_damage_modifier(self, actor):
            """计算状态对伤害输出的修正"""
            modifier = 1.0
            for ac in actor.active_conditions:
                if "fDamageBonus" in ac.config.modifiers:
                    modifier += ac.config.modifiers["fDamageBonus"]
            return max(0.0, modifier)
        
        def _get_condition_defense_modifier(self, actor):
            """计算状态对伤害减免的修正"""
            modifier = 1.0
            for ac in actor.active_conditions:
                if "fDamageCut" in ac.config.modifiers:
                    modifier += ac.config.modifiers["fDamageCut"]
            return max(0.0, modifier)

        # ================== 保留原有 execute_battle_move（无改动） ==================
        
        def execute_battle_move(self, move_instance, is_player=True):
            """执行战术动作"""

            # 如果用户是玩家且执行了逃离战斗（ID 6），并且距离已经 >= 20
            if is_player and move_instance.id == 6 and self.range >= 20:
                self.combat_log.append("你趁敌人不备，迅速逃离了战场！")
                self.is_finished = True
                self.winner = "player_escaped"  # 标记为玩家逃离
                return

            if self.is_finished:
                return

            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player

            # 玩家始终消耗；敌人仅在近战距离（≤6米）消耗
            if is_player or self.range <= 6:
                user.hunger = min(100.0, user.hunger + move_instance.hunger_cost)
                user.thirst = min(100.0, user.thirst + move_instance.thirst_cost)
            user.fatigue = min(100.0, user.fatigue + move_instance.fatigue_cost)

            # 更新状态
            update_thirst_condition(user)
            update_fatigue_condition(user)

            # 昏阙检测
            if check_and_apply_faint(user, combat_instance=self, is_player=is_player):
                return

            if user.b_dead:
                self.is_finished = True
                self.winner = target
                self.combat_log.append(f"{user.name} 因徒劳的战斗消耗倒下了。")
                return

            # 解析战术变更效果
            effects = move_instance.success_effects
            if "range_change" in effects:
                self.range = max(1, self.range + effects["range_change"])
                self.combat_log.append(f"{user.name} 执行了 [{move_instance.name}]，距离变为 {self.range}米。")
                
                # 距离变更后立即检查脱离条件
                if self.range >= 20:
                    if is_player:
                        # 玩家：只要不昏阙，就算成功逃离
                        if not is_fainted(self.player):
                            self.combat_log.append("你成功拉开了距离，脱离了战斗！")
                            self.is_finished = True
                            self.winner = "player_escaped"  # 标记为玩家逃离
                            return
                    else:
                        # 敌人：非人类不逃；人类按逃离率判定
                        if not self.enemy.is_human:
                            pass  # 非人类继续战斗
                        elif random.random() < self.enemy.escape_rate and not is_fainted(self.player):
                            self.combat_log.append(f"{self.enemy.name} 趁距离拉远，头也不回地逃走了！")
                            self.is_finished = True
                            self.winner = None  # 标记为敌人逃离
                            return
                        # 其他情况：战斗继续

            if "set_pose" in effects:
                user.add_condition(COND_SHELTER)
                self.combat_log.append(f"{user.name} 成功进入了隐蔽掩体。")

            if is_player:
                self.player_acted_this_turn = True

        # ================== 执行攻击（加入命中率计算） ==================
        
        def execute_attack(self, attack_mode, is_player=True):
            """执行直接伤害攻击（包含命中率计算）"""
            if self.is_finished:
                return
            
            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player
            
            # 消耗战斗相关资源 — 直接使用 AttackMode 实例的消耗属性
            hunger_mod = user.get_modifier_multiplier('fHungerRate')
            thirst_mod = user.get_modifier_multiplier('fThirstRate')
            fatigue_mod = user.get_modifier_multiplier('fFatigueRate')

            if is_player or self.range <= 6:
                user.hunger = min(100.0, user.hunger + attack_mode.hunger_cost * hunger_mod)
                user.thirst = min(100.0, user.thirst + attack_mode.thirst_cost * thirst_mod)
            user.fatigue = min(100.0, user.fatigue + attack_mode.fatigue_cost * fatigue_mod)

            update_thirst_condition(user)
            update_fatigue_condition(user)

            # 昏阙检测
            if check_and_apply_faint(user, combat_instance=self, is_player=is_player):
                return

            if user.b_dead:
                self.is_finished = True
                self.winner = target
                self.combat_log.append(f"{user.name} 因战斗消耗倒下，{target.name} 获得了上风。")
                return
            
            # 距离判定（是否超出武器射程）
            if self.range > attack_mode.range:
                self.combat_log.append(f"{user.name} 试图使用 [{attack_mode.name}]，但距离太远落空了！")
                if is_player:
                    self.player_acted_this_turn = True
                return
            
            # 计算命中率
            hit_chance = self.calculate_hit_chance(attack_mode, is_player)
            roll = random.random()
            
            # 命中判定
            if roll > hit_chance:
                self.combat_log.append(
                    f"{user.name} 使用 [{attack_mode.name}] 攻击未命中！"
                )
                if is_player:
                    self.player_acted_this_turn = True
                return
            
            # 伤害计算（随机浮动 -40%，取整数）
            base_damage = attack_mode.damage
            damage_variance = random.uniform(0.60, 1.00)
            raw_dmg = int(base_damage * damage_variance)
            
            # 攻击方增益修正
            attack_mod = self._get_condition_damage_modifier(user)
            raw_dmg = int(raw_dmg * attack_mod)
            
            # 防御方减伤修正
            defense_mod = self._get_condition_defense_modifier(target)
            raw_dmg = int(raw_dmg * defense_mod)
            
            # 保底至少 1 点伤害
            if raw_dmg < 1:
                raw_dmg = 1
            
            # 应用伤害
            target.hp -= raw_dmg
            clamp_hp(target)
            
            self.combat_log.append(
                f"{user.name} 使用 [{attack_mode.name}] 击中了 {target.name}，"
                f"造成了 {raw_dmg} 点伤害！"
            )
            
            # 附加状态
            if attack_mode.attacker_conditions and random.random() <= attack_mode.condition_chance:
                cond_to_apply = attack_mode.attacker_conditions[0]
                # 缠绕冷却检查
                if cond_to_apply == COND_ENTANGLED and self.entangle_cooldown > 0:
                    pass  # 冷却中，不触发
                else:
                    target.add_condition(cond_to_apply)
                self.combat_log.append(
                    f"{target.name} 被施加了状态: {CONDITIONS_DB[cond_to_apply].name}"
                )
                # 如果是缠绕，设置冷却（回合内不能再次使用）
                if cond_to_apply == COND_ENTANGLED:
                    self.entangle_cooldown = 3

                # 失衡日志
                if cond_to_apply == COND_STAGGER:
                    self.combat_log.append(f"{target.name} 被打得脚步踉跄，失去了平衡！")
            
            # 死亡检查
            if target.hp <= 0:
                target.b_dead = True
                self.is_finished = True
                self.winner = user
                self.loot_drops = LootTable.roll_loot(
                    target.treasure_id,
                    overall_chance=0.6
                )
                self.corpse_searched = False
                self.combat_log.append(f"{target.name} 已经倒在了废土血泊中。")
                if self.loot_drops:
                    self.combat_log.append("你可以搜刮敌人的尸体，获得战利品。")
            else:
                if is_player:
                    self.player_acted_this_turn = True

        # ================== 重写：敌人AI（智能决策） ==================
        
        def enemy_ai_turn(self):
            """敌人AI回合 - 智能判定"""

            if self.is_finished:
                return

            # 玩家被缠绕 → 自动跳过敌人回合
            if is_fainted(self.player):
                pass  # 昏阙已有处理
            elif any(ac.id == COND_ENTANGLED for ac in self.player.active_conditions):
                self.combat_log.append("你被藤蔓紧紧缠住，无法行动！")
                self.is_player_turn = True
                return
            
            # 敌人昏阙检测
            if check_and_apply_faint(self.enemy, combat_instance=self):
                return

            if self.is_player_turn:
                return
            
            from random import choice as random_choice
            
            available_attacks = self.enemy.get_available_attack_modes(self.range)
            available_moves = self.enemy.get_available_battle_moves(self.player, self.range)
            
            # === AI决策树 ===
            
            # 血量极低（<30%）=> 优先逃跑
            if self.enemy.hp < (self.enemy.max_hp * 0.3):
                # 只有人类生物才有逃跑想法
                if self.enemy.is_human and random.random() < self.enemy.escape_rate:
                    
                    # 如果玩家昏阙，敌人不应逃跑
                    if is_fainted(self.player):
                        pass  # 跳过逃跑
                    else:
                        escape_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) > 0]
                        if escape_moves:
                            self.execute_battle_move(escape_moves[0], is_player=False)
                            # 如果战斗已经因距离脱离结束，直接返回
                            if self.is_finished:
                                return
                            self.is_player_turn = True
                            return
                # 如果不是人类或没有成功逃跑，则改为攻击或前进

            # 被缠绕/无法近身 => 使用远程攻击
            entangled = any(ac.id == COND_ENTANGLED for ac in self.enemy.active_conditions)
            if entangled and self.range > 2:
                ranged_attacks = [a for a in available_attacks if a.range >= 8]
                if ranged_attacks:
                    self.execute_attack(random_choice(ranged_attacks), is_player=False)
                    self.is_player_turn = True
                    return
            
            # 距离太远没有合适攻击 => 突进
            if not available_attacks:
                advance_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) < 0]
                if advance_moves:
                    # 选择能最大程度缩短距离的战术动作
                    best_move = max(advance_moves, key=lambda m: abs(m.success_effects.get("range_change", 0)))
                    self.execute_battle_move(best_move, is_player=False)
                    self.is_player_turn = True
                    return
                else:
                    # 无法行动，跳过回合
                    self.combat_log.append(f"{self.enemy.name} 在原地等待，无法发动有效攻击。")
                    self.is_player_turn = True
                    return
            
            # 有多个攻击选项 => 选择预期伤害最高的
            if available_attacks:
                def expected_damage(attack):
                    hit_chance = self.calculate_hit_chance(attack, is_player=False)
                    return int(attack.damage * hit_chance)
                
                best_attack = max(available_attacks, key=expected_damage)
                self.execute_attack(best_attack, is_player=False)
                self.is_player_turn = True
                return
            
            # 兜底：尝试前进
            any_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) < 0]
            if any_moves:
                self.execute_battle_move(any_moves[0], is_player=False)
            else:
                self.combat_log.append(f"{self.enemy.name} 似乎有点不知所措。")
            self.is_player_turn = True
            renpy.restart_interaction()

        # ================== 保留原有 end_turn 和 search_corpse ==================
        
        def end_turn(self):
            """结束己方回合 - 切换到敌人回合"""
            if not self.is_finished and self.is_player_turn:

                # 减少缠绕冷却
                if self.entangle_cooldown > 0:
                    self.entangle_cooldown -= 1

                # 先推进一回合时间（无论本回合后续战斗是否结束）
                self._advance_one_turn()

                # 然后检查背包禁用标记，如果已禁用则记录日志
                if self.player_turn_disabled_by_inventory:
                    self.player_turn_disabled_by_inventory = False
                    self.combat_log.append("你因为操作背包而浪费了本回合的行动机会！")
                elif not self.player_acted_this_turn:
                    self.combat_log.append("你选择谨慎行事，没有做出任何行动就结束了本回合。")
                
                # 昏阙自动恢复检查（此时时间已推进，昏阙计数器会相应增加）
                faint_recovery_check(self)
                
                self.is_player_turn = False
                self.player_acted_this_turn = False
                self.enemy_ai_turn()
                renpy.restart_interaction()

        def search_corpse(self):
            global player_inventory
            if not self.is_finished or self.winner != self.player or self.corpse_searched:
                return
            self.corpse_searched = True
            if self.loot_drops:
                item_names = "、".join(item.config.name for item in self.loot_drops)
                for item in self.loot_drops:
                    player_inventory.add_item(item)
                self.combat_log.append(f"你从尸体上搜刮到了：{item_names}。")
            else:
                self.combat_log.append("你搜刮了尸体，却没有找到任何有用的东西。")
            self.loot_drops = []

        def _advance_one_turn(self):
            """推进一回合（5分钟）的全局时间，并对双方应用基础代谢"""
            global game_time
            # 推进5分钟
            game_time['minute'] += 5
            overflow = game_time['minute'] // 60
            game_time['minute'] = game_time['minute'] % 60
            game_time['hour'] += overflow
            if game_time['hour'] >= 24:
                game_time['hour'] = 0
                game_time['day'] += 1
            
            # 双方应用代谢
            tick_minutes(self.player, 5)
            tick_minutes(self.enemy, 5)

    