# game/systems/combat.rpy
init -180 python:
    _current_combat_instance = None

    class CombatSystem:
        def __init__(self, player, enemy_instance):
            self.player = player
            self.enemy = enemy_instance
            self.range = renpy.random.randint(6, 16) # 初始距离随机在 6-16 米之间
            # 词条前缀
            if enemy_instance.trait_id is not None:
                trait_name = CONDITIONS_DB[enemy_instance.trait_id].name
                self.combat_log = [(f"战斗开始！你遭遇了【{trait_name}的{enemy_instance.name}】", "system")]
            else:
                self.combat_log = [(f"战斗开始！你遭遇了 {enemy_instance.name}", "system")]
            self.is_finished = False
            self.winner = None
            self.player_turn_disabled_by_inventory = False
            self.loot_drops = []
            self.corpse_searched = False
            self.corpse_container = None
            self.is_player_turn = True
            self.player_acted_this_turn = False
            self.move_cooldowns = {}  # {move_id: remaining_turns}     
            self.enemy_escape_attempted = False  # 敌人是否已尝试过逃跑       

        def _log(self, text, owner="system"):
            """
            添加战斗日志条目，自动封装为 (文本, 归属) 元组。
            
            参数:
                text: 日志文本
                owner: 归属方标识，可选值：
                    "player" — 玩家行为（显示为绿色）
                    "enemy"  — 敌人行为（显示为红色）
                    "system" — 系统/中立信息（显示为灰色，默认值）
            """
            self.combat_log.append((text, owner))
        
        def fade_out_music(self):
            """战斗开始时淡出背景音乐（1.5秒渐弱）。"""
            if renpy.music.get_playing():
                renpy.music.stop(fadeout=1.5)
        
        def restore_music(self):
            global _last_explore_music_hour, _last_explore_music_day
            if (hasattr(store, '_last_explore_music_hour') and hasattr(store, '_last_explore_music_day') 
                and _last_explore_music_hour >= 0 and _last_explore_music_day >= 0):
                hours_passed = (game_time['day'] - _last_explore_music_day) * 24 + (game_time['hour'] - _last_explore_music_hour)
                if hours_passed * 60 >= EXPLORE_MUSIC_COOLDOWN_MINUTES:
                    renpy.music.play("audio/bgm_explore.mp3", fadein=1.0, loop=False)
                    _last_explore_music_hour = game_time['hour']
                    _last_explore_music_day = game_time['day']  
            else:
                renpy.music.play("audio/bgm_explore.mp3", fadein=1.0, loop=False)
                _last_explore_music_hour = game_time['hour']
                _last_explore_music_day = game_time['day']   


        def can_player_act(self):
            """检查玩家是否可以执行战术动作/攻击（未行动、战斗未结束）。"""
            return (not self.player_acted_this_turn 
                    and not self.is_finished 
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
            final_hit = max(HIT_CHANCE_MIN, min(HIT_CHANCE_MAX, hit_chance - dodge_chance))

            # 光照修正（昼夜系统）
            is_ranged = weapon_type in ("pistol", "rifle", "throw")
            light_mod = get_light_hit_modifier(game_time['hour'], is_ranged)
            final_hit = max(HIT_CHANCE_MIN, min(HIT_CHANCE_MAX, final_hit * light_mod))

            # 玩家命中率浮动（0.9~1.1），仅玩家攻击时生效
            if is_player:
                player_hit_mod = renpy.random.uniform(*PLAYER_HIT_MULTIPLIER)
                final_hit = max(HIT_CHANCE_MIN, min(HIT_CHANCE_MAX, final_hit * player_hit_mod))
            
            return final_hit
        
        def _determine_weapon_type(self, attack_mode):
            """根据攻击模式对象 ID 查找武器类型（melee/pistol/rifle/throw/natural）"""
            for ids, weapon_type in WEAPON_TYPE_RULES:
                if attack_mode.id in ids:
                    return weapon_type
            return "melee"
        
        def _get_range_modifier(self, current_range):
            """根据当前战斗距离（米）返回命中率修正系数。使用 RANGE_HIT_MODIFIERS 表进行区间映射。"""
            for zone_name, (min_r, max_r, modifier) in RANGE_HIT_MODIFIERS.items():
                if min_r <= current_range <= max_r:
                    return modifier
            return RANGE_MOD_FALLBACK  # 超出所有范围
        
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

            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player

            # ── 前置条件验证（兜底保护） ──
            if not move_instance.is_usable(user, target, self.range):
                self._log(f"{user.name} 无法执行 [{move_instance.name}]：条件不满足。", "system")
                if is_player:
                    self.player_acted_this_turn = True
                return

            if move_instance.id == 6:
                # 先消耗基础三维（使用 BattleMove 定义的消耗值）
                hunger_mod = user.get_modifier_multiplier('fHungerRate')
                thirst_mod = user.get_modifier_multiplier('fThirstRate')
                fatigue_mod = user.get_modifier_multiplier('fFatigueRate')
                if is_player or self.range <= COMBAT_RANGE_MELEE_MAX:
                    user.hunger = min(100.0, user.hunger + move_instance.hunger_cost * hunger_mod)
                    user.thirst = min(100.0, user.thirst + move_instance.thirst_cost * thirst_mod)
                user.fatigue = min(100.0, user.fatigue + move_instance.fatigue_cost * fatigue_mod)
                update_thirst_condition(user)
                update_hunger_condition(user)
                update_fatigue_condition(user)
                
                # 逃离有 5% 概率摔倒
                if renpy.random.random() < ESCAPE_TRIP_CHANCE:
                    user.add_condition(COND_PRONE)
                    self._log(f"{user.name} 在逃离过程中脚下不稳，重重摔倒在地！", "player" if is_player else "enemy")
                
                if is_player:
                    enemy_hp_ratio = self.enemy.hp / self.enemy.max_hp
                    close_penalty = ESCAPE_CLOSE_PENALTY_VALUE if self.range <= COMBAT_RANGE_CLOSE_PENALTY else 0
                    
                    if enemy_hp_ratio <= ESCAPE_HP_LOW:
                        self._log("敌人已经重伤，无力追击。你成功脱离了战斗！", "player")
                        self.is_finished = True
                        self.winner = "player_escaped"
                        if move_instance.cooldown > 0:
                            self.move_cooldowns[move_instance.id] = move_instance.cooldown
                        return
                    elif enemy_hp_ratio <= ESCAPE_HP_MID:
                        # 敌人犹豫追击 → 拉开距离但战斗继续
                        base_escape = ESCAPE_BASE_FLEE
                        self.range = min(COMBAT_RANGE_ESCAPE, self.range + base_escape - close_penalty)
                        self._log(f"你奋力奔逃，拉开了距离（当前{self.range}米），但敌人仍在后方紧追不舍。", "player")
                    else:
                        # 敌人状态良好，全力追击 → 只拉开少量距离
                        base_escape = ESCAPE_BASE_CHASE
                        self.range = min(COMBAT_RANGE_ESCAPE, self.range + base_escape - close_penalty)
                        self._log(f"敌人怒吼着追了上来！你只拉开了少量距离（当前{self.range}米）。", "player")
                    
                    if is_player:
                        self.player_acted_this_turn = True
                    
                    # 如果距离达到20米，判定脱离
                    if self.range >= COMBAT_RANGE_ESCAPE:
                        self._log("你成功拉开了足够远的距离，脱离了战斗！", "player")
                        self.is_finished = True
                        self.winner = "player_escaped"
                        if move_instance.cooldown > 0:
                            self.move_cooldowns[move_instance.id] = move_instance.cooldown
                        return
                else:
                    # 敌人使用逃离 — 基于玩家HP比例的智能判定
                    player_hp_ratio = self.player.hp / self.player.max_hp
                    close_penalty = ESCAPE_CLOSE_PENALTY_VALUE if self.range <= COMBAT_RANGE_CLOSE_PENALTY else 0
                    
                    if player_hp_ratio <= ESCAPE_HP_LOW:
                        self._log(f"{self.enemy.name} 趁你重伤无力追击，成功逃离了战斗！", "enemy")
                        self.is_finished = True
                        self.winner = None
                        if move_instance.cooldown > 0:
                            self.move_cooldowns[move_instance.id] = move_instance.cooldown
                        return
                    elif player_hp_ratio <= ESCAPE_HP_MID:
                        # 玩家犹豫追击 → 拉开距离但战斗继续
                        base_escape = ESCAPE_BASE_FLEE
                        self.range = min(COMBAT_RANGE_ESCAPE, self.range + base_escape - close_penalty)
                        self._log(f"{self.enemy.name} 拼命向后逃窜，拉开了距离（当前{self.range}米），但你仍在后方紧追不舍。", "enemy")
                    else:
                        # 玩家状态良好，全力追击 → 只拉开少量距离
                        base_escape = ESCAPE_BASE_CHASE
                        self.range = min(COMBAT_RANGE_ESCAPE, self.range + base_escape - close_penalty)
                        self._log(f"{self.enemy.name} 试图逃跑，但你怒吼着追了上去！距离拉近到 {self.range}米。", "enemy")
                    
                    # 如果距离达到20米，判定脱离
                    if self.range >= COMBAT_RANGE_ESCAPE:
                        self._log(f"{self.enemy.name} 成功逃离了战场！", "enemy")
                        self.is_finished = True
                        self.winner = None
                        if move_instance.cooldown > 0:
                            self.move_cooldowns[move_instance.id] = move_instance.cooldown
                        return
                if move_instance.cooldown > 0:
                    self.move_cooldowns[move_instance.id] = move_instance.cooldown
                return

            if self.is_finished:
                return

            # 冷却检查
            if move_instance.id in self.move_cooldowns:
                self._log(f"{user.name} 的 [{move_instance.name}] 还在冷却中（剩余{self.move_cooldowns[move_instance.id]}回合）！", "player" if is_player else "enemy")
                if is_player:
                    self.player_acted_this_turn = True
                return

            # 被缠绕状态无法执行移动与攻击
            if any(ac.id == COND_ENTANGLED for ac in user.active_conditions):
                self._log(f"{user.name} 被束缚住了，无法移动与攻击！", "player" if is_player else "enemy")
                if is_player:
                    self.player_acted_this_turn = True
                return

            # 摔倒状态只能执行"起身"动作
            if any(ac.id == COND_PRONE for ac in user.active_conditions):
                if move_instance.id != 12:  # 12 = 起身
                    self._log(f"{user.name} 摔倒在地，必须先站起来才能做其他动作！", "player" if is_player else "enemy")
                    if is_player:
                        self.player_acted_this_turn = True
                    return

            # 玩家始终消耗；敌人仅在近战距离（≤6米）消耗
            hunger_mod = user.get_modifier_multiplier('fHungerRate')
            thirst_mod = user.get_modifier_multiplier('fThirstRate')
            fatigue_mod = user.get_modifier_multiplier('fFatigueRate')
            if is_player or self.range <= COMBAT_RANGE_MELEE_MAX:
                user.hunger = min(100.0, user.hunger + move_instance.hunger_cost * hunger_mod)  
                user.thirst = min(100.0, user.thirst + move_instance.thirst_cost * thirst_mod)  
            user.fatigue = min(100.0, user.fatigue + move_instance.fatigue_cost * fatigue_mod) 

            # 更新状态
            update_thirst_condition(user)
            update_hunger_condition(user)
            update_fatigue_condition(user)

            if user.b_dead:
                self.is_finished = True
                self.winner = target
                self._log(f"{user.name} 因徒劳的战斗消耗倒下了。", "player" if is_player else "enemy")
                return

            # 解析战术变更效果
            effects = move_instance.success_effects
            if "range_change" in effects:
                self.range = max(1, self.range + effects["range_change"])
                self._log(f"{user.name} 执行了 [{move_instance.name}]，距离变为 {self.range}米。", "player" if is_player else "enemy")

            if "set_pose" in effects:
                user.add_condition(COND_SHELTER)
                self._log(f"{user.name} 成功进入了隐蔽掩体。", "player" if is_player else "enemy")

            if "unset_pose" in effects and effects["unset_pose"] == "cover":
                remove_condition_by_id(user, COND_SHELTER)
                self.move_cooldowns[4] = SHELTER_COOLDOWN_TURNS  # 进入掩体冷却
                self._log(f"{user.name} 退出了掩体。", "player" if is_player else "enemy")

            if "unset_pose" in effects and effects["unset_pose"] == "prone":
                remove_condition_by_id(user, COND_PRONE)
                self._log(f"{user.name} 迅速从地上爬了起来，重新站稳了脚跟。", "player" if is_player else "enemy")

            if is_player:
                self.player_acted_this_turn = True

            # 设置动作冷却
            if move_instance.cooldown > 0:
                self.move_cooldowns[move_instance.id] = move_instance.cooldown

        # ================== 执行攻击（加入命中率计算） ==================
        
        def execute_attack(self, attack_mode, is_player=True):
            """执行直接伤害攻击（包含命中率计算）"""
            if self.is_finished:
                return

            user = self.player if is_player else self.enemy
            target = self.enemy if is_player else self.player

            # 摔倒状态无法攻击
            if any(ac.id == COND_PRONE for ac in user.active_conditions):
                self._log(f"{user.name} 摔倒在地，无法发动攻击！", "player" if is_player else "enemy")
                if is_player:
                    self.player_acted_this_turn = True
                return
            
            # 消耗战斗相关资源 — 直接使用 AttackMode 实例的消耗属性
            hunger_mod = user.get_modifier_multiplier('fHungerRate')
            thirst_mod = user.get_modifier_multiplier('fThirstRate')
            fatigue_mod = user.get_modifier_multiplier('fFatigueRate')

            if is_player or self.range <= COMBAT_RANGE_MELEE_MAX:
                user.hunger = min(100.0, user.hunger + attack_mode.hunger_cost * hunger_mod)
                user.thirst = min(100.0, user.thirst + attack_mode.thirst_cost * thirst_mod)
            user.fatigue = min(100.0, user.fatigue + attack_mode.fatigue_cost * fatigue_mod)

            update_thirst_condition(user)
            update_hunger_condition(user)
            update_fatigue_condition(user)

            if user.b_dead:
                self.is_finished = True
                self.winner = target
                self._log(f"{user.name} 因战斗消耗倒下，{target.name} 获得了上风。", "player" if is_player else "enemy")
                return
            
            # 距离判定（是否超出武器射程）
            if self.range < attack_mode.min_range:
                self._log(f"{user.name} 试图使用 [{attack_mode.name}]，但距离太近无法施展！", "player" if is_player else "enemy")
                if is_player:
                    self.player_acted_this_turn = True
                return
            
            if self.range > attack_mode.max_range:
                self._log(f"{user.name} 试图使用 [{attack_mode.name}]，但距离太远落空了！", "player" if is_player else "enemy")
                if is_player:
                    self.player_acted_this_turn = True
                return
            
            # 计算命中率
            hit_chance = self.calculate_hit_chance(attack_mode, is_player)
            roll = renpy.random.random()
            weapon_type = self._determine_weapon_type(attack_mode)
            
            # ★ 冲撞（ID 103）无论是否命中，先减少距离 ★
            if attack_mode.id == 103:
                old_range = self.range
                self.range = max(1, self.range - CHARGE_RANGE_REDUCE)
            
            # 命中判定
            if roll > hit_chance:
                self._log(f"{user.name} 使用 [{attack_mode.name}] 攻击未命中！", "player" if is_player else "enemy")
                if is_player:
                    self.player_acted_this_turn = True
                return
            
            # 伤害计算（取整数）
            base_damage = attack_mode.damage
            
            # 玩家使用独立浮动范围（0.8~1.2），敌人使用基础浮动（0.6~1.0）
            if is_player:
                damage_variance = renpy.random.uniform(*PLAYER_DAMAGE_MULTIPLIER)
            else:
                damage_variance = renpy.random.uniform(ENEMY_DAMAGE_MIN, ENEMY_DAMAGE_MAX)
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
            
            # 掩体判定：在掩体中且未被击破 → 完全免伤
            shelter_blocked = False
            if any(ac.id == COND_SHELTER for ac in target.active_conditions):
                if weapon_type in ("melee", "natural"):
                    # 近战/天然武器：80% 概率击破掩体
                    if renpy.random.random() < SHELTER_BREAK_MELEE:
                        remove_condition_by_id(target, COND_SHELTER)
                        if target is self.player:
                            self.move_cooldowns[4] = SHELTER_COOLDOWN_TURNS
                        self._log(f"{target.name} 的掩体被近身击破，退出了掩体状态。", "enemy" if is_player else "player")
                    else:
                        # 20% 掩体未被击破 → 完全挡住伤害
                        shelter_blocked = True
                        self._log(f"{user.name} 使用了 [{attack_mode.name}]，但是被 {target.name} 的掩体挡住了！", "enemy" if is_player else "player")
                else:
                    # 远程武器：20% 概率击破掩体
                    if renpy.random.random() < SHELTER_BREAK_RANGED:
                        remove_condition_by_id(target, COND_SHELTER)
                        if target is self.player:
                            self.move_cooldowns[4] = SHELTER_COOLDOWN_TURNS
                        self._log(f"{target.name} 的掩体被远程攻击击破，退出了掩体状态。", "enemy" if is_player else "player")
                    else:
                        # 80% 掩体未被击破 → 完全挡住伤害
                        shelter_blocked = True
                        self._log(f"{user.name} 使用了 [{attack_mode.name}]，但是被 {target.name} 的掩体挡住了！", "enemy" if is_player else "player")

            # 如果被掩体挡住，不造成伤害
            if not shelter_blocked:
                # 应用伤害
                target.hp -= raw_dmg
                clamp_hp(target)
                
                # 记录玩家承受伤害
                if not is_player:
                    store.total_damage_taken += int(raw_dmg)
                
                # ── 濒死/死亡状态更新（双方通用） ──
                if target.hp <= 0:
                    target.active_conditions = []
                    target.add_condition(COND_DEAD)
                else:
                    remove_condition_by_id(target, COND_DEAD)
                    if target.hp < target.max_hp * MORIBUND_HP_THRESHOLD:
                        target.add_condition(COND_MORIBUND)
                    else:
                        remove_condition_by_id(target, COND_MORIBUND)
                
                self._log(f"{user.name} 使用 [{attack_mode.name}] 击中了 {target.name}，造成了 {raw_dmg} 点伤害！", "player" if is_player else "enemy")
                
                # 玩家攻击后标记
                if is_player:
                    self.player_acted_this_turn = True

                # 附加状态（只有造成伤害时才施加）
                if attack_mode.attacker_conditions and renpy.random.random() <= attack_mode.condition_chance:
                    cond_to_apply = attack_mode.attacker_conditions[0]
                    if cond_to_apply == COND_ENTANGLED and self.move_cooldowns.get(ENTANGLE_COOLDOWN_KEY, 0) > 0:
                        pass  # 缠绕冷却中，跳过
                    else:
                        target.add_condition(cond_to_apply)
                        self._log(f"{target.name} 被施加了状态: {CONDITIONS_DB[cond_to_apply].name}", "enemy" if is_player else "player")
                        if cond_to_apply == COND_ENTANGLED:
                            self.move_cooldowns[ENTANGLE_COOLDOWN_KEY] = ENTANGLE_COOLDOWN_TURNS
                        if cond_to_apply == COND_STAGGER:
                            self._log(f"{target.name} 被打得脚步踉跄，失去了平衡！", "enemy" if is_player else "player")
                
                # 死亡检查 + 战利品掉落
                if target.b_dead or target.hp <= 0:
                    target.b_dead = True
                    self.is_finished = True
                    self.winner = user
                    
                    # ── 死亡状态：清空其他状态 ──
                    if not target.is_player:
                        target.active_conditions = []
                        target.add_condition(COND_DEAD)
                        if is_player:
                            store.enemies_killed += 1
                    
                    # 只有敌人死亡时才掉落战利品
                    if is_player:
                        self.loot_drops = LootTable.roll_loot(
                            target.treasure_id,
                            overall_chance=LOOT_OVERALL_CHANCE
                        )
                        self.corpse_searched = not bool(self.loot_drops)
                        self.corpse_container = get_current_ground_container()
                        if self.loot_drops:
                            self._log("你可以搜刮敌人的尸体，获得战利品。", "system")
                        else:
                            self._log("敌人的尸体上似乎没有什么值钱的东西。", "system")
                    else:
                        # 玩家死亡，没有战利品掉落
                        self._log(f"{target.name} 已经倒在了废土血泊中。", "enemy" if is_player else "player")
            else:
                # 被掩体挡住，但仍消耗行动
                if is_player:
                    self.player_acted_this_turn = True                    

        # ================== 敌人AI（智能决策） ==================
        
        def enemy_ai_turn(self):
            """敌人AI回合 - 智能判定"""

            if self.is_finished:
                return

            # 玩家被缠绕 → 自动跳过敌人回合
            if any(ac.id == COND_ENTANGLED for ac in self.player.active_conditions):
                self._log("你被藤蔓紧紧缠住，无法行动！", "player")
                self.is_player_turn = True
                return

            # 敌人被缠绕 → 自动跳过敌人回合
            if any(ac.id == COND_ENTANGLED for ac in self.enemy.active_conditions):
                self._log(f"{self.enemy.name} 被束缚住了，无法行动！", "enemy")
                self.is_player_turn = True
                return
            
            available_attacks = self.enemy.get_available_attack_modes(self.range)
            available_moves = self.enemy.get_available_battle_moves(self.player, self.range)


            # 敌人摔倒 → 优先起身
            if any(ac.id == COND_PRONE for ac in self.enemy.active_conditions):
                stand_up_moves = [m for m in available_moves if m.id == 12]
                if stand_up_moves:
                    self.execute_battle_move(stand_up_moves[0], is_player=False)
                    self.is_player_turn = True
                    return
                else:
                    self._log(f"{self.enemy.name} 摔倒在地，挣扎着试图爬起来。", "enemy")
                    self.is_player_turn = True
                    return
            
            # ── 敌人濒死状态更新 ──
            if not self.enemy.b_dead:
                if self.enemy.hp < self.enemy.max_hp * MORIBUND_HP_THRESHOLD:
                    self.enemy.add_condition(COND_MORIBUND)
                else:
                    remove_condition_by_id(self.enemy, COND_MORIBUND)

            if self.is_player_turn:
                return
            
            # === AI决策树 ===
            
            # 血量极低（<30%）或三维接近危险值（>=80）=> 尝试逃跑（仅一次判定）
            if (self.enemy.hp < (self.enemy.max_hp * MORIBUND_HP_THRESHOLD) or 
                self.enemy.hunger >= 80.0 or 
                self.enemy.thirst >= 80.0 or 
                self.enemy.fatigue >= 80.0) and not self.enemy_escape_attempted:
                self.enemy_escape_attempted = True
                # 有自我保存意识的生物（人类或设置了逃跑率的生物）才会逃跑
                if self.enemy.is_human or self.enemy.escape_rate > 0:
                    self.enemy_escape_attempted = True
                    # 优先使用"逃离战斗"（ID 6），无视距离限制
                    # 概率由敌人的 escape_rate 决定
                    escape_move = BATTLE_MOVES_DB.get(6)
                    if escape_move and escape_move.is_usable(self.enemy, self.player, self.range) and 6 not in self.move_cooldowns and renpy.random.random() < self.enemy.escape_rate:
                        self.execute_battle_move(escape_move, is_player=False)
                        if self.is_finished:
                            return
                        self.is_player_turn = True
                        return
                        
                    # 如果逃离在冷却中，使用其他能增加距离的动作
                    escape_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) > 0]
                    if escape_moves:
                        best_escape = max(escape_moves, key=lambda m: m.success_effects.get("range_change", 0))
                        self.execute_battle_move(best_escape, is_player=False)
                        if self.is_finished:
                            return
                        self.is_player_turn = True
                        return

            # 敌人在掩体中 → 只能使用掩体动作，不能攻击
            if any(ac.id == COND_SHELTER for ac in self.enemy.active_conditions):
                shelter_moves = [m for m in available_moves if m.id in (9, 10, 11)]
                if shelter_moves:
                    has_ranged = any(a.max_range >= COMBAT_RANGE_RANGED_MIN for a in available_attacks)
                    if has_ranged:
                        if self.range < COMBAT_RANGE_RANGED_MIN:
                            retreat_shelter = [m for m in shelter_moves if m.id == 10]
                            if retreat_shelter:
                                self.execute_battle_move(retreat_shelter[0], is_player=False)
                                if self.is_finished:
                                    return
                                self.is_player_turn = True
                                return
                        exit_move = [m for m in shelter_moves if m.id == 11]
                        if exit_move:
                            self.execute_battle_move(exit_move[0], is_player=False)
                            if self.is_finished:
                                return
                            self.is_player_turn = True
                            return
                    else:
                        if self.range > COMBAT_RANGE_MELEE_ADVANCE:
                            advance_shelter = [m for m in shelter_moves if m.id == 9]
                            if advance_shelter:
                                self.execute_battle_move(advance_shelter[0], is_player=False)
                                if self.is_finished:
                                    return
                                self.is_player_turn = True
                                return
                        exit_move = [m for m in shelter_moves if m.id == 11]
                        if exit_move:
                            self.execute_battle_move(exit_move[0], is_player=False)
                            if self.is_finished:
                                return
                            self.is_player_turn = True
                            return
                # 没有可用掩体动作 → 在掩体中等待
                self._log(f"{self.enemy.name} 在掩体中等待时机。", "enemy")
                self.is_player_turn = True
                return

            # 远程敌人（有远程武器）→ 主动保持距离
            has_ranged = any(a.max_range >= COMBAT_RANGE_RANGED_MIN for a in available_attacks)
            if has_ranged and self.range < COMBAT_RANGE_RANGED_MIN:
                retreat_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) > 0]
                if retreat_moves:
                    best_retreat = max(retreat_moves, key=lambda m: m.success_effects.get("range_change", 0))
                    self.execute_battle_move(best_retreat, is_player=False)
                    if self.is_finished:
                        return
                    self.is_player_turn = True
                    return

            # 近战敌人（只有近战武器）→ 主动拉近距离
            if not has_ranged and self.range > COMBAT_RANGE_MELEE_ADVANCE:
                advance_moves = [m for m in available_moves if m.success_effects.get("range_change", 0) < 0]
                if advance_moves:
                    best_advance = max(advance_moves, key=lambda m: abs(m.success_effects.get("range_change", 0)))
                    self.execute_battle_move(best_advance, is_player=False)
                    if self.is_finished:
                        return
                    self.is_player_turn = True
                    return

            # 不在掩体中且可用 → 进入掩体（仅人类敌人，且不在冷却中）
            # 条件：玩家有真正的远程武器（排除投掷杂物等低伤害攻击）
            if self.enemy.is_human and not any(ac.id == COND_SHELTER for ac in self.enemy.active_conditions):
                shelter_move = BATTLE_MOVES_DB.get(4)
                if shelter_move and shelter_move.is_usable(self.enemy, self.player, self.range) and 4 not in self.move_cooldowns:
                    # 概率判定：不是所有人类敌人都一定会进入掩体
                    if renpy.random.random() >= SHELTER_ENTER_CHANCE_HUMAN:
                        pass  # 跳过进入掩体，继续后续决策
                    else:
                        # 检查玩家是否有真正的远程武器
                        player_attacks = self.player.get_available_attack_modes(self.range)
                        player_has_real_ranged = any(
                            a.max_range >= COMBAT_RANGE_RANGED_MIN and a.id not in (4, 8) for a in player_attacks
                        )
                        if player_has_real_ranged:
                            self.execute_battle_move(shelter_move, is_player=False)
                            if self.is_finished:
                                return
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
                    self._log(f"{self.enemy.name} 在原地等待，无法发动有效攻击。", "enemy")
                    self.is_player_turn = True
                    return
            
            # 有可用攻击 → 直接攻击
            def expected_damage(attack):
                hit_chance = self.calculate_hit_chance(attack, is_player=False)
                return int(attack.damage * hit_chance)
            best_attack = max(available_attacks, key=expected_damage)
            self.execute_attack(best_attack, is_player=False)
            self.is_player_turn = True
            return

        # ================== 保留原有 end_turn 和 search_corpse ==================
        
        def end_turn(self):
            """结束己方回合 - 切换到敌人回合"""
            if not self.is_finished and self.is_player_turn:

                # 先推进一回合时间（无论本回合后续战斗是否结束）
                self._advance_one_turn()

                # 减少所有战术动作冷却
                for move_id in list(self.move_cooldowns.keys()):
                    self.move_cooldowns[move_id] -= 1
                    if self.move_cooldowns[move_id] <= 0:
                        del self.move_cooldowns[move_id]

                # 然后检查背包禁用标记，如果已禁用则记录日志
                if self.player_turn_disabled_by_inventory:
                    self.player_turn_disabled_by_inventory = False
                    self._log("你因为操作背包而失去了本回合的行动机会！", "player")
                elif not self.player_acted_this_turn:
                    self._log("你选择谨慎行事，没有做出任何行动就结束了本回合。", "player")
                
                self.is_player_turn = False
                self.player_acted_this_turn = False
                self.enemy_ai_turn()
                renpy.restart_interaction()

        def search_corpse(self):
            global player_inventory
            if not self.is_finished or self.winner != self.player or self.corpse_searched:
                return
            if not self.loot_drops:
                self.corpse_searched = True
                self._log("你搜刮了尸体，没有找到任何有用的东西。", "system")
                return

            picked_up_items = []
            remaining_items = []
            dropped_to_ground = []
            still_unclaimed = []

            for item in list(self.loot_drops):
                if player_inventory.add_item(item):
                    picked_up_items.append(item)
                else:
                    remaining_items.append(item)

            if picked_up_items:
                item_names = "、".join(item.config.name for item in picked_up_items)
                self._log(f"你从尸体上搜刮到了：{item_names}。", "player")

            if remaining_items:
                if self.corpse_container is not None:
                    for item in remaining_items:
                        if self.corpse_container.add_item(item):
                            dropped_to_ground.append(item)
                        else:
                            still_unclaimed.append(item)
                else:
                    still_unclaimed = list(remaining_items)

                if dropped_to_ground:
                    ground_names = "、".join(item.config.name for item in dropped_to_ground)
                    self._log(f"剩下的战利品掉在了地上：{ground_names}。", "system")

                if still_unclaimed:
                    self.loot_drops = still_unclaimed
                    self.corpse_searched = False
                    self._log("你的背包放不下剩下的战利品了。", "system")
                else:
                    self.loot_drops = []
                    self.corpse_searched = True
            else:
                self.loot_drops = []
                self.corpse_searched = True
                if not picked_up_items:
                    self._log("你搜刮了尸体，没有找到任何有用的东西。", "system")

        def finalize_corpse_loot(self):
            """离开战斗界面前，尽量将未处理战利品落到地面，成功后返回结算值。"""
            if self.winner != self.player or not self.loot_drops:
                return ["combat_end_trigger", self.winner]

            if self.corpse_container is None:
                self.corpse_container = get_current_ground_container()

            if self.corpse_container is None:
                renpy.notify("还有未处理的战利品，无法直接离开战场。")
                return None

            remaining_items = []
            for item in self.loot_drops:
                if not self.corpse_container.add_item(item):
                    remaining_items.append(item)

            self.loot_drops = remaining_items
            if not self.loot_drops:
                self.corpse_searched = True
                return ["combat_end_trigger", self.winner]

            renpy.notify("地面已满，还有未处理的战利品。")
            return None

        def _advance_one_turn(self):
            """推进一回合（5分钟）的全局时间，并对双方应用基础代谢"""
            advance_game_time(5)
            
            # 双方应用代谢
            tick_minutes(self.player, 5)
            tick_minutes(self.enemy, 5)
