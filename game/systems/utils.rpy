# game/systems/utils.rpy
init -199 python:
# ==============================================================
# 数值工具
# ==============================================================
    def clamp_hp(actor, min_hp=0.0):
        """统一处理 HP 下限保护，并返回是否触发死亡"""
        if actor.hp < min_hp:
            actor.hp = min_hp
        return actor.hp <= 0

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

    def apply_baseline_metabolism(actor, minutes, hunger_mult=1.0, thirst_mult=1.0, fatigue_mult=1.0):
        """
        对指定角色 actor 应用 minutes 分钟的基础代谢消耗，
        支持三维各自的倍率因子（默认为1.0）。
        内部自动处理按5分钟步进循环、剩余分钟比例折算和上限保护（100.0）。
        """
        full_cycles = minutes // 5
        for _ in range(full_cycles):
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
            "ocean": "#0044aa"
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
            "ocean": "大海"
        }
        return labels.get(terrain_type, "未知")

    def is_in_birth_protection_zone(x, y):
        """
        检查坐标是否在出生点保护区内（3x3网格，共9个地块）。
        以 BIRTH_ZONE 中每个坐标为中心，检查 (x, y) 是否在 ±1 范围内。
        """
        for bx, by in BIRTH_ZONE:   # ← 把 _birth_zone 改成 BIRTH_ZONE
            if abs(x - bx) <= 1 and abs(y - by) <= 1:
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