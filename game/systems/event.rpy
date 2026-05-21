# =============================================================================
# # 随机事件
# # 定义：野外地图、时间切分下的随机遭遇触发概率引擎。 
# # 实现：根据玩家所在的地形（森林、废墟）以及昼夜时间，决定这一格是弹出“空无一人”、触发 `encounters.py` 的剧情、还是直接拉进 `combat.rpy` 的战斗。
# =============================================================================
init python:
    import random

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
        if disable_encounters:  # 添加检查
            return None
        if world_map is None:
            return None
        tile = world_map.grid.get((player_hex_x, player_hex_y))
        if tile is None:
            return None
        return RandomEventEngine.check_trigger(tile)
