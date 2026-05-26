# =============================================================================
# # 地图与据点状态逻辑
# # 定义：大地图的网格数据（如 2D地图的定义），据点（如新世界城）的解锁状态。 
# # 实现：玩家在地图格子移动时的地形判定（消耗行动力 AP）、在该格子搜索资源的计算。
# =============================================================================
init python:
    class HexTile:
        def __init__(self, terrain_type, treasure_id, special_feature=None, merchant_id=None):
            self.terrain_type = terrain_type
            self.treasure_id = treasure_id
            self.scavenged = False
            self.special_feature = special_feature  # "lake_water", "merchant", "city", None
            self.merchant_id = merchant_id

    class WorldMap:
        """大地图网络矩阵"""
        def __init__(self, map_id, name, width, height, csv_def_string):
            self.id = map_id
            self.name = name
            self.grid = {} # 坐标元组 (x, y) 映射 HexTile 实例
            self.parse_map_data(width, height, csv_def_string)

        def parse_map_data(self, width, height, csv_str):
            """解析 maps.xml 的 csv 数据结构"""
            lines = csv_str.strip().split('\n')
            for y in range(min(height, len(lines))):
                cells = lines[y].split(',')
                for x in range(min(width, len(cells))):
                    tid = int(cells[x])
                    # 新的地形映射
                    if tid == 0:
                        terrain = "ocean" # 大海
                    elif tid == 1:
                        terrain = "lake"  # 湖
                    elif tid == 2:
                        terrain = "beach" # 沙滩
                    elif tid == 3:
                        terrain = "forest"
                    elif tid == 28:
                        terrain = "plains"
                    else:
                        terrain = "city_ruins"

                    # 特殊位置标记 (需要结合新地图调整坐标)
                    special = None
                    merchant_id = None
                    if (x, y) == (10, 5):  # 地图中间偏左
                        special = "merchant"
                        merchant_id = "wasteland_trader_01"
                    elif (x, y) == (18, 8):  # 地图右下区域
                        special = "city"
                        merchant_id = "city_trader_01"
                    elif terrain == "lake":
                        special = "lake_water"

                    self.grid[(x, y)] = HexTile(terrain_type=terrain, treasure_id=tid, special_feature=special, merchant_id=merchant_id)          

# 关键：这些 default 变量会被存档/读档管理
default map_width = 20
default map_height = 10

default world_map = WorldMap(
    1, "废土地图",
    map_width,
    map_height,
    """3,3,3,3,3,3,3,3,28,28,28,28,3,3,3,28,2,2,0,0
3,3,3,28,28,28,28,28,28,28,28,1,28,3,3,3,28,2,0,0
28,28,28,28,28,28,28,28,28,28,28,28,28,28,28,3,28,2,2,0
28,28,28,28,3,3,3,3,28,28,28,28,28,28,28,28,28,2,2,0
3,28,28,28,3,1,3,3,28,28,28,28,1,28,28,28,28,2,2,0
3,3,28,28,3,3,3,28,28,28,28,28,28,28,28,28,28,2,2,0
28,3,3,28,28,28,28,28,28,28,28,28,28,3,3,28,28,28,2,2
28,28,3,3,28,28,28,28,28,28,28,28,3,3,3,28,28,4,4,4
28,28,28,28,28,28,3,3,28,1,28,3,3,3,3,28,4,4,4,4
28,28,28,28,28,28,3,3,28,28,28,3,3,3,28,4,4,4,4,4"""
)


# 将函数定义移出条件块，确保始终可用
python early:
    def get_map_tile_color(terrain_type):
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
        labels = {
            "plains": "平原",
            "forest": "森林",
            "city_ruins": "废墟",
            "lake": "湖",
            "beach": "沙滩",
            "ocean": "大海"
        }
        return labels.get(terrain_type, "未知")

init python:
    def get_current_tile():
        if world_map is None:
            return None
        return world_map.grid.get((player_hex_x, player_hex_y))

    def scavenge_current_tile():
        tile = get_current_tile()
        if tile is None or getattr(tile, "scavenged", False):
            return False, None

        tile.scavenged = True
        player_stats.hunger = min(100.0, player_stats.hunger + SCAVENGE_COSTS['hunger'])
        player_stats.thirst = min(100.0, player_stats.thirst + SCAVENGE_COSTS['thirst'])
        player_stats.fatigue = min(100.0, player_stats.fatigue + SCAVENGE_COSTS['fatigue'])
        update_thirst_condition(player_stats)
        update_fatigue_condition(player_stats)

        # 战利品掉落
        dropped_items = loot_random_scavenge(player_inventory=player_inventory)
        if dropped_items:
            item_names = "、".join(item.config.name for item in dropped_items)
            renpy.notify(f"搜刮到了：{item_names}")
        else:
            renpy.notify("你翻遍了废墟，一无所获。")
            
        event_code = trigger_random_map_event()
        return True, event_code

    def move_player_hex(target_x, target_y):
        """处理玩家在大地图格子的移动损耗，并联动推动时间与代谢"""
        global player_hex_x, player_hex_y, game_time, last_map_event_code

        if not (0 <= target_x < map_width and 0 <= target_y < map_height):
            return None

        # 检查目标格子是否可通行
        tile = world_map.grid.get((target_x, target_y))
        if tile and tile.terrain_type in ("ocean"):
            renpy.notify("那里是一望无际的{0}，你无法穿越。".format(get_map_tile_label(tile.terrain_type)))
            return None

        # 移动推动时间流逝：每走一格过去1小时
        game_time["hour"] += 1
        if game_time["hour"] >= 24:
            game_time["hour"] = 0
            game_time["day"] += 1
            
        player_hex_x = target_x
        player_hex_y = target_y

        if not god_mode:
            # 移动消耗饥饿值与口渴值，并联动更新状态
            consume_travel_costs(player_stats)
            # 联动状态与内呼吸代谢心跳更新
            tick_hour(player_stats, hours=1)

        # 移动后检查本地随机遭遇事件
        last_map_event_code = trigger_random_map_event()
        return last_map_event_code


