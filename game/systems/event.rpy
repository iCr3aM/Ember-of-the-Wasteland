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

    def is_in_birth_protection_zone(x, y):
        """
        检查坐标是否在出生点保护区内（3x3网格，共9个地块）。
        以 BIRTH_ZONE 中每个坐标为中心，检查 (x, y) 是否在 ±1 范围内。
        """
        for bx, by in _birth_zone:
            if abs(x - bx) <= 1 and abs(y - by) <= 1:
                return True
        return False    

    class RandomEventEngine:
        """根据地形和时间决定刷新遭遇战或是偶遇文本"""
        @staticmethod
        def check_trigger(tile_instance):
            # 简化概率模型判定：30%概率触发遭遇
            if random.random() <= 0.3:
                if tile_instance.terrain_type == "city_ruins":
                    return EVENT_ENCOUNTER_AMBUSH
                else:
                    return EVENT_ENCOUNTER_DEFAULT
            return None # 空无一人

    def trigger_random_map_event():
        """根据当前玩家所在格子触发随机地图遭遇事件。"""
        if disable_encounters:  # 全局禁用开关
            return None
        if world_map is None:
            return None
        
        # ★ 新增：检查是否在出生保护区内 ★
        if is_in_birth_protection_zone(player_hex_x, player_hex_y):
            return None  # 保护区内不触发任何事件，包括遭遇战
        
        tile = world_map.grid.get((player_hex_x, player_hex_y))
        if tile is None:
            return None
        
        return RandomEventEngine.check_trigger(tile)

