# =============================================================================
# # 随机事件
# # 定义：野外地图、时间切分下的随机遭遇触发概率引擎。 
# # 实现：根据玩家所在的地形（森林、废墟）以及昼夜时间，决定这一格是弹出“空无一人”、触发 `encounters.py` 的剧情、还是直接拉进 `combat.rpy` 的战斗。
# =============================================================================
init python:
    import random
    # 安全获取 BIRTH_ZONE（可能在 db_data.rpy 中定义）
    try:
        _birth_zone = BIRTH_ZONE
    except NameError:
        # 默认出生区域，与 db_data.rpy 保持一致
        _birth_zone = [(3, 3), (3, 4), (4, 3), (4, 4)]

    class RandomEventEngine:
        """多地形与多时间段扩展版事件引擎（未实装一律默认版）"""
        @staticmethod
        def check_trigger(tile_instance):
            global game_time
            
            # 基础概率判定：30% 概率触发遭遇
            if random.random() > 0.3:
                return None 
                
            # 获取当前小时
            current_hour = game_time.get("hour", 12)
            
            # 四个时间段
            if 0 <= current_hour < 6:
                time_period = "midnight"  # 凌晨 (0:00 - 5:59)
            elif 6 <= current_hour < 12:
                time_period = "morning"   # 上午 (6:00 - 11:59)
            elif 12 <= current_hour < 18:
                time_period = "afternoon" # 下午 (12:00 - 17:59)
            else:
                time_period = "night"     # 深夜 (18:00 - 23:59)

            # 4. 根据【特定地形】+【时间段】派发事件（找不到编号则自动变更为默认事件）
            if tile_instance.terrain_type == "city_ruins":
                # ------- 城市废墟地形 -------
                if time_period in ["night", "midnight"]:
                    # 未来打算用 2002 (夜间伏击)，如果没实装，自动变为 2001
                    target_event = 2002 
                else:
                    # 未来打算用 2003 (白天拾荒偶遇)
                    target_event = 2003

            elif tile_instance.terrain_type == "forest":
                # ------- 森林地形 -------
                if time_period in ["night", "midnight"]:
                    # 未来打算用 2004 (夜间狼群)
                    target_event = 2004
                else:
                    target_event = EVENT_ENCOUNTER_DEFAULT

            else:
                # ------- 其他普通荒野地形 -------
                target_event = EVENT_ENCOUNTER_DEFAULT

            # 5. 【核心安全机制】
            # 如果 target_event 存在于注册表中，就返回它；如果不存在，无缝替换为默认事件（丛林低吼）
            if target_event in EVENT_LABEL_MAP:
                return target_event
            return EVENT_ENCOUNTER_DEFAULT

    def trigger_random_map_event():
        """根据当前玩家所在格子触发随机地图遭遇事件。"""
        if disable_encounters:  # 全局禁用开关
            return None
        if world_map is None:
            return None
        
        # 检查是否在出生保护区内
        if is_in_birth_protection_zone(player_hex_x, player_hex_y):
            return None  # 保护区内不触发任何事件，包括遭遇战
        
        tile = world_map.grid.get((player_hex_x, player_hex_y))
        if tile is None:
            return None
        
        return RandomEventEngine.check_trigger(tile)

