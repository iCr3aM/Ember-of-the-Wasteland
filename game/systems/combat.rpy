# game/systems/combat.rpy
init python:
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


    class CombatSystem:
        def __init__(self, player, enemy_instance):
            self.player = player
            self.enemy = enemy_instance
            self.range = 12
            self.combat_log = ["战斗开始！你遭遇了 " + enemy_instance.name]
            self.is_finished = False
            self.winner = None
            self.loot_drops = []
            self.corpse_searched = False
            self.is_player_turn = True
            self.player_acted_this_turn = False

        # ================== 新增：命中率相关方法 ==================
        
        def calculate_hit_chance(self, attack_mode, is_player=True):
            """计算命中率"""
            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player
            
            # 1. 确定武器类型
            weapon_type = self._determine_weapon_type(attack_mode)
            base_hit = WEAPON_HIT_BASE.get(weapon_type, BASE_HIT_CHANCE)
            
            # 2. 距离修正
            range_mod = self._get_range_modifier(self.range)
            
            # 3. 状态修正
            user_cond_mod = self._get_condition_hit_modifier(user)
            target_cond_mod = self._get_condition_dodge_modifier(target)
            
            # 4. 计算最终命中率
            hit_chance = base_hit * range_mod * user_cond_mod
            dodge_chance = BASE_DODGE_CHANCE * target_cond_mod
            
            # 5. 限制范围 5%-99%
            final_hit = max(0.05, min(0.99, hit_chance - dodge_chance))
            
            return final_hit
        
        def _determine_weapon_type(self, attack_mode):
            """根据攻击模式ID确定武器类型"""
            if attack_mode.id in (1,):  # 徒手
                return "melee"
            elif attack_mode.id in (2, 3):  # 钝器/砍刀
                return "melee"
            elif attack_mode.id in (4,):  # 投掷
                return "throw"
            elif attack_mode.id in (5,):  # 手枪
                return "pistol"
            elif attack_mode.id in (6, 199):  # 步枪/压制射击
                return "rifle"
            elif attack_mode.id in (101, 102, 103, 106):  # 生物攻击
                return "natural"
            elif attack_mode.id in (104, 105, 107):  # 特殊远程
                return "throw"
            elif attack_mode.id in (108,):  # 自爆
                return "melee"
            elif attack_mode.id in (109, 110):  # 投掷类
                return "throw"
            else:
                return "melee"
        
        def _get_range_modifier(self, current_range):
            """根据距离获取命中率修正系数"""
            for zone_name, (min_r, max_r, modifier) in RANGE_HIT_MODIFIERS.items():
                if min_r <= current_range <= max_r:
                    return modifier
            return 0.5  # 超出所有范围
        
        def _get_condition_hit_modifier(self, actor):
            """计算状态对命中率的修正"""
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
            if self.is_finished:
                return

            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player

            # 消耗战斗相关资源
            consume_combat_costs(user, 'battle_move')
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

            if "set_pose" in effects:
                user.add_condition(COND_SHELTER)
                self.combat_log.append(f"{user.name} 成功进入了隐蔽掩体。")

            if is_player:
                self.player_acted_this_turn = True

        # ================== 重写：执行攻击（加入命中率计算） ==================
        
        def execute_attack(self, attack_mode, is_player=True):
            """执行直接伤害攻击（重写为包含命中率计算）"""
            if self.is_finished:
                return
            
            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player
            
            # 消耗战斗相关资源
            consume_combat_costs(user, 'attack')
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
                    f"(需求 {hit_chance*100:.0f}%，骰子 {roll*100:.0f}%)"
                )
                if is_player:
                    self.player_acted_this_turn = True
                return
            
            # 伤害计算（随机浮动 ±20%，取整数）
            base_damage = attack_mode.damage
            damage_variance = random.uniform(0.80, 1.20)
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
            target.hp = max(0, target.hp)
            
            self.combat_log.append(
                f"{user.name} 使用 [{attack_mode.name}] 击中了 {target.name}，"
                f"造成了 {raw_dmg} 点伤害！"
            )
            
            # 附加状态
            if attack_mode.attacker_conditions and random.random() <= 0.5:
                cond_to_apply = attack_mode.attacker_conditions[0]
                target.add_condition(cond_to_apply)
                self.combat_log.append(
                    f"{target.name} 被施加了恶性状态: {CONDITIONS_DB[cond_to_apply].name}"
                )
            
            # 死亡检查
            if target.hp <= 0:
                target.b_dead = True
                self.is_finished = True
                self.winner = user
                self.loot_drops = LootTable.roll_loot(target.treasure_id)
                self.corpse_searched = False
                self.combat_log.append(f"{target.name} 已经倒在了废土血泊中。")
                if self.loot_drops:
                    self.combat_log.append("你可以搜刮敌人的尸体，获得战利品。")
            else:
                if is_player:
                    self.player_acted_this_turn = True

        # ================== 重写：敌人AI（智能决策） ==================
        
        def enemy_ai_turn(self):
            """敌人AI回合 - 新增智能判定"""
            if self.is_finished:
                return
            
            if self.is_player_turn:
                return
            
            from random import choice as random_choice
            
            available_attacks = self.enemy.get_available_attack_modes(self.range)
            available_moves = self.enemy.get_available_battle_moves(self.player, self.range)
            
            # === AI决策树 ===
            
            # 1. 血量极低（<20%）=> 优先逃跑
            if self.enemy.hp < (self.enemy.max_hp * 0.2):
                escape_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) > 0]
                if escape_moves:
                    self.execute_battle_move(escape_moves[0], is_player=False)
                    self.is_player_turn = True
                    return
            
            # 2. 被缠绕/无法近身 => 使用远程攻击
            entangled = any(ac.id == COND_ENTANGLED for ac in self.enemy.active_conditions)
            if entangled and self.range > 2:
                ranged_attacks = [a for a in available_attacks if a.range >= 8]
                if ranged_attacks:
                    self.execute_attack(random_choice(ranged_attacks), is_player=False)
                    self.is_player_turn = True
                    return
            
            # 3. 距离太远没有合适攻击 => 突进
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
                    self.combat_log.append(f"{self.enemy.name} 在原地徘徊，无法发动有效攻击。")
                    self.is_player_turn = True
                    return
            
            # 4. 有多个攻击选项 => 选择预期伤害最高的
            if available_attacks:
                def expected_damage(attack):
                    hit_chance = self.calculate_hit_chance(attack, is_player=False)
                    return int(attack.damage * hit_chance)
                
                best_attack = max(available_attacks, key=expected_damage)
                self.execute_attack(best_attack, is_player=False)
                self.is_player_turn = True
                return
            
            # 5. 兜底：尝试前进
            any_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) < 0]
            if any_moves:
                self.execute_battle_move(any_moves[0], is_player=False)
            else:
                self.combat_log.append(f"{self.enemy.name} 似乎有点不知所措。")
            self.is_player_turn = True

        # ================== 保留原有 end_turn 和 search_corpse ==================
        
        def end_turn(self):
            """结束己方回合 - 切换到敌人回合"""
            if not self.is_finished and self.is_player_turn:
                self.is_player_turn = False
                self.player_acted_this_turn = False  # 重置标记
                # 立即触发敌人AI
                self.enemy_ai_turn()
                # 强制屏幕重新渲染，刷新按钮可用状态
                renpy.restart_interaction()

        def search_corpse(self):
            global player_inventory
            if not self.is_finished or self.winner != self.player or self.corpse_searched:
                return
            self.corpse_searched = True
            if not self.loot_drops:
                self.combat_log.append("你搜刮了尸体，却没有找到任何有用的东西。")
                return
            for item in self.loot_drops:
                player_inventory.add_item(item)
                self.combat_log.append(f"你从尸体上获得了 {item.config.name}。")
            self.loot_drops = []