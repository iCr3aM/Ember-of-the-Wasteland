# game/systems/utils.rpy
init -199 python:
# ==============================================================
# 数值工具
# ==============================================================
    def clamp_hp(actor, min_hp=0.0):
        """统一处理 HP 下限保护，并返回是否触发死亡"""
        if actor.hp <= 0.001:  # 浮点数容差
            actor.hp = 0.0
            actor.b_dead = True
            return True
        if actor.hp < min_hp:
            actor.hp = min_hp
        return False

    def advance_game_time(minutes):
        """推进游戏时间，并统一处理分钟、小时、天数进位。"""
        global game_time
        game_time['minute'] += minutes
        overflow_h = game_time['minute'] // 60
        game_time['minute'] = game_time['minute'] % 60
        game_time['hour'] += overflow_h
        overflow_d = game_time['hour'] // 24
        game_time['hour'] = game_time['hour'] % 24
        game_time['day'] += overflow_d

    def darken_background(image_path):
        """返回统一压暗后的背景图 displayable。"""
        return Transform(image_path, matrixcolor=BrightnessMatrix(BACKGROUND_DARKNESS))

    def roll_weighted_enemy_for_terrain(terrain_type):
        """根据地形敌人池和稀有度权重抽取敌人 ID。"""
        enemy_pool = TERRAIN_ENEMY_MAP.get(terrain_type, FALLBACK_ENEMY_POOL)
        if not enemy_pool:
            enemy_pool = FALLBACK_ENEMY_POOL

        candidates = {}
        for cid in enemy_pool:
            for rarity, data in ENEMY_RARITY.items():
                if cid in data["enemies"]:
                    candidates[cid] = data["weight"]
                    break
            else:
                candidates[cid] = 50

        total = sum(candidates.values())
        roll = renpy.random.random() * total
        cumulative = 0
        selected_id = enemy_pool[0]
        for cid, weight in candidates.items():
            cumulative += weight
            if roll <= cumulative:
                selected_id = cid
                break
        return selected_id

    def create_weighted_enemy_for_current_terrain():
        """按玩家当前所在地形创建一个加权随机敌人实例。"""
        tile = world_map.grid.get((player_hex_x, player_hex_y))
        terrain = tile.terrain_type if tile else "plains"
        creature_id = roll_weighted_enemy_for_terrain(terrain)
        return ActorInstance(creature_id=creature_id, is_player=False)

    def is_in_active_combat():
        """检查当前是否处于活跃战斗中（安全访问全局变量）"""
        try:
            return _current_combat_instance is not None and not _current_combat_instance.is_finished
        except NameError:
            return False

    def is_player_turn_available():
        """检查玩家当前是否可以操作背包/进行行动"""
        if not is_in_active_combat():
            return True
        try:
            return not _current_combat_instance.player_turn_disabled_by_inventory
        except NameError:
            return True

    def update_thirst_condition(actor):
        """根据当前口渴值自动维护口渴/脱水状态。"""
        # 先记录当前已有的口渴状态
        had_thirst = any(ac.id == COND_THIRST for ac in actor.active_conditions)
        had_dehydrated = any(ac.id == COND_DEHYDRATED for ac in actor.active_conditions)
        had_extreme = any(ac.id == COND_EXTREME_DEHYDRATED for ac in actor.active_conditions)
        had_organ = any(ac.id == COND_ORGAN_FAILURE for ac in actor.active_conditions)

        thirst_state = None
        if actor.thirst >= THIRST_THRESHOLDS['organ_failure']:
            thirst_state = COND_ORGAN_FAILURE
        elif actor.thirst >= THIRST_THRESHOLDS['extreme_dehydrated']:
            thirst_state = COND_EXTREME_DEHYDRATED
        elif actor.thirst >= THIRST_THRESHOLDS['dehydrated']:
            thirst_state = COND_DEHYDRATED
        elif actor.thirst >= THIRST_THRESHOLDS['thirst']:
            thirst_state = COND_THIRST

        # 清除旧的口渴相关状态
        actor.active_conditions = [ac for ac in actor.active_conditions if ac.id not in CONDITIONAL_THIRST_IDS]

        if thirst_state is not None:
            actor.add_condition(thirst_state)

    def update_hunger_condition(actor):
        """根据当前饥饿值自动维护饥饿/重度饥饿/极度饥饿/营养不良状态。"""
        # 先记录当前已有的饥饿状态
        had_hunger = any(ac.id == COND_HUNGER for ac in actor.active_conditions)
        had_severe = any(ac.id == COND_SEVERE_HUNGER for ac in actor.active_conditions)
        had_extreme = any(ac.id == COND_EXTREME_HUNGER for ac in actor.active_conditions)
        had_mal = any(ac.id == COND_MALNUTRITION for ac in actor.active_conditions)

        hunger_state = None
        if actor.hunger >= HUNGER_THRESHOLDS['malnutrition']:
            hunger_state = COND_MALNUTRITION
        elif actor.hunger >= HUNGER_THRESHOLDS['extreme_hunger']:
            hunger_state = COND_EXTREME_HUNGER
        elif actor.hunger >= HUNGER_THRESHOLDS['severe_hunger']:
            hunger_state = COND_SEVERE_HUNGER
        elif actor.hunger >= HUNGER_THRESHOLDS['hunger']:
            hunger_state = COND_HUNGER

        # 清除旧的饥饿相关状态
        actor.active_conditions = [ac for ac in actor.active_conditions if ac.id not in CONDITIONAL_HUNGER_IDS]

        if hunger_state is not None:
            actor.add_condition(hunger_state)

    def update_fatigue_condition(actor):
        """根据当前疲劳值自动维护疲劳状态。"""
        # 先记录当前已有的疲劳状态
        had_fatigue = any(ac.id == COND_FATIGUE for ac in actor.active_conditions)
        had_severe = any(ac.id == COND_SEVERE_FATIGUE for ac in actor.active_conditions)
        
        # 清除旧疲劳状态
        actor.active_conditions = [ac for ac in actor.active_conditions if ac.id not in (COND_FATIGUE, COND_SEVERE_FATIGUE)]

        if actor.fatigue >= FATIGUE_THRESHOLDS['severe_fatigue']:
            actor.add_condition(COND_SEVERE_FATIGUE)
        elif actor.fatigue >= FATIGUE_THRESHOLDS['fatigue']:
            actor.add_condition(COND_FATIGUE)

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

    def apply_baseline_metabolism(actor, minutes, hunger_mult=1.0, thirst_mult=1.0, fatigue_mult=1.0):
        """
        对指定角色 actor 应用 minutes 分钟的基础代谢消耗，
        支持三维各自的倍率因子（默认为1.0）。
        内部自动处理按5分钟步进循环、剩余分钟比例折算和上限保护（100.0）。
        """
        full_cycles = minutes // 5
        for i in range(full_cycles):
            actor.hunger += METABOLISM_PER_5MIN['hunger'] * hunger_mult
            actor.thirst += METABOLISM_PER_5MIN['thirst'] * thirst_mult
            actor.fatigue += METABOLISM_PER_5MIN['fatigue'] * fatigue_mult
        remaining = minutes % 5
        if remaining > 0:
            ratio = remaining / 5.0
            actor.hunger += METABOLISM_PER_5MIN['hunger'] * hunger_mult * ratio
            actor.thirst += METABOLISM_PER_5MIN['thirst'] * thirst_mult * ratio
            actor.fatigue += METABOLISM_PER_5MIN['fatigue'] * fatigue_mult * ratio
        # 上限保护
        actor.hunger = min(actor.hunger, 100.0)
        actor.thirst = min(actor.thirst, 100.0)
        actor.fatigue = min(actor.fatigue, 100.0)

    def get_map_tile_color(terrain_type):
        """根据地形类型返回十六进制颜色代码，用于地图格子的 UI 着色。"""
        colors = {
            "plains": "#888844",
            "forest": "#227722", 
            "city_ruins": "#663333",
            "lake": "#4488ff",
            "beach": "#d4c96c",
            "ocean": "#0044aa",
            "road": "#555555",     
            "farmland": "#88aa44",  
            "swamp": "#445533",
            "other": "#444444",
        }
        return colors.get(terrain_type, "#444444")

    def get_map_tile_label(terrain_type):
        """根据地形类型返回其中文标签（如平原、森林、废墟等）。"""
        labels = {
            "plains": "平原",
            "forest": "森林",
            "city_ruins": "废墟",
            "lake": "湖",
            "beach": "沙滩",
            "ocean": "大海",
            "road": "公路",      
            "farmland": "农田",   
            "swamp": "沼泽",
            "other": "未知",
        }
        return labels.get(terrain_type, "未知")

    def is_in_birth_protection_zone(x, y):
        """
        检查坐标是否在出生点保护区内。
        以 BIRTH_ZONE 中每个坐标为中心，检查 (x, y) 是否在 ±1 范围内。
        """
        for bx, by in BIRTH_ZONE:   # BIRTH_ZONE
            if abs(x - bx) <= 2 and abs(y - by) <= 2:
                return True
        return False    

# ==============================================================
# 时间工具
# ==============================================================
    def get_time_period_str(hour):
        """根据小时数（0-23）返回中文时段描述（凌晨/清晨/早上/中午/下午/晚上/深夜）。"""
        if 0 <= hour < 6:
            return "凌晨"
        elif 6 <= hour < 9:
            return "清晨"
        elif 9 <= hour < 12:
            return "早上"
        elif 12 <= hour < 15:
            return "中午"
        elif 15 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:  # 22 <= hour < 24
            return "深夜"

    def get_light_hit_modifier(hour, is_ranged=False):
        """根据当前小时返回光照对命中率的修正系数。
        
        时间段设计：
        - 6:00~18:00（清晨/早上/中午/下午）→ 白天，视野良好，命中率 100%
        - 18:00~20:00（黄昏）→ 光线渐暗，远程轻微下降，近战基本不受影响
        - 20:00~22:00（夜晚）→ 夜色已深，远程大幅下降，近战也受影响
        - 22:00~4:00（深夜/凌晨）→ 最黑暗时段，远程极低，近战明显下降
        - 4:00~6:00（黎明）→ 天色渐亮，命中率逐渐恢复
        """
        if 6 <= hour < 18:
            return 1.0                     # 白天：100%
        elif 18 <= hour < 20:
            return 0.85 if is_ranged else 0.95  # 黄昏：远程85%，近战95%
        elif 20 <= hour < 22:
            return 0.65 if is_ranged else 0.85  # 夜晚：远程65%，近战85%
        elif 22 <= hour < 4:
            return 0.50 if is_ranged else 0.75  # 深夜：远程50%，近战75%
        elif 4 <= hour < 6:
            return 0.75 if is_ranged else 0.90  # 黎明：远程75%，近战90%
        return 1.0  # 兜底
    
    # 颜色函数
    def get_condition_display_colors(condition_id):
        """根据状态ID返回 (背景色, 文字色) 元组，用于UI显示。
        
        严重程度分级：
        - 死亡：灰色
        - 致命（b_fatal）：深红
        - 危急（濒死、重度疲劳、极度饥饿/脱水、器官衰竭）：亮红
        - 伤害（流血、中毒、骨折、内伤、失衡、重度饥饿、脱水）：橙色
        - 警告（口渴、饥饿、疲劳、被缠绕）：琥珀色
        - 增益（掩体、睡觉、专注、耐渴、精力充沛、强硬、凶猛）：绿色
        - 减益（虚弱、孱弱、迟缓、衰竭）：紫色
        - 默认：灰色
        """
        # 死亡
        if condition_id == COND_DEAD:
            return ("#333333", "#888888")
        
        # 致命状态
        if condition_id in (COND_MORIBUND, COND_SEVERE_FATIGUE,
                            COND_EXTREME_HUNGER, COND_EXTREME_DEHYDRATED,
                            COND_ORGAN_FAILURE, COND_MALNUTRITION):
            return ("#551111", "#ff4444")
        
        # 伤害/减益状态
        if condition_id in (COND_BLEED, COND_POISON, COND_FRACTURE,
                            COND_INTERNAL_INJURY, COND_STAGGER,
                            COND_SEVERE_HUNGER, COND_DEHYDRATED,
                            COND_PRONE, COND_CUT_FOOT):
            return ("#553322", "#ff8844")
        
        # 警告状态
        if condition_id in (COND_THIRST, COND_HUNGER, COND_FATIGUE,
                            COND_ENTANGLED, COND_BARE_FOOT):
            return ("#333322", "#ffcc66")
        
        # 增益状态
        if condition_id in (COND_SHELTER, COND_FAINT,
                            TRAIT_FOCUSED, TRAIT_DROUGHT_RESISTANT,
                            TRAIT_ENERGETIC, TRAIT_TOUGH, TRAIT_FEROCIOUS):
            return ("#224422", "#66ff66")
        
        # 减益词条
        if condition_id in (TRAIT_WEAK, TRAIT_FRAIL, TRAIT_SLUGGISH, TRAIT_DECAYING,
                            COND_NICOTINE_MILD, COND_NICOTINE_MODERATE, COND_NICOTINE_SEVERE):
            return ("#332244", "#aa66cc")
        
        # 默认
        return ("#222222", "#cccccc")

    def smoke_cigarette():
        """执行吸烟操作：消耗1支香烟（货币），更新成瘾状态"""
        global cigarettes_smoked, last_cigarette_hour, last_cigarette_day, game_time
        
        # 检查是否有香烟
        if player_stats.cigarettes < 1:
            renpy.notify("你没有香烟可以抽！")
            return
        
        # 消耗1支香烟
        player_stats.cigarettes -= 1
        cigarettes_smoked += 1
        last_cigarette_hour = game_time['hour']
        last_cigarette_day = game_time['day']
        
        # 吸烟解除所有戒断状态
        remove_condition_by_id(player_stats, COND_NICOTINE_MILD)
        remove_condition_by_id(player_stats, COND_NICOTINE_MODERATE)
        remove_condition_by_id(player_stats, COND_NICOTINE_SEVERE)

        # 根据累计吸烟数更新成瘾状态（成瘾 ≠ 戒断，成瘾是永久标签）
        # 成瘾状态在 tick_minutes 中根据"是否长时间未吸烟"触发戒断
        
        # 应用疲劳值减少
        if cigarettes_smoked >= NICOTINE_MODERATE_THRESHOLD:
            player_stats.fatigue = max(0, player_stats.fatigue - 10)
        else:
            player_stats.fatigue = max(0, player_stats.fatigue - 5)
        
        update_fatigue_condition(player_stats)
        
        # 显示吸烟文本
        if cigarettes_smoked == 1:
            renpy.notify("你点燃香烟，深吸一口。尼古丁冲进血液，世界短暂地变得清晰了一些。")
        elif cigarettes_smoked <= NICOTINE_MILD_THRESHOLD:
            renpy.notify("你点燃香烟，深吸一口。尼古丁冲进血液，世界短暂地变得清晰了一些。")
        elif cigarettes_smoked <= NICOTINE_MODERATE_THRESHOLD:
            renpy.notify("你用颤抖的手指划燃火柴，在火焰舔舐烟卷的瞬间，你的身体已经提前松弛下来。")
        else:
            renpy.notify("你点燃香烟，深吸一口。尼古丁冲进血液，颤抖的手终于稳定下来。")
