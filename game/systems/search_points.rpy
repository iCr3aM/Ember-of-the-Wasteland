# =============================================================================
# search_points.rpy — 搜刮点生成系统
# 功能：定义搜刮点数据模型、地形→搜刮点池映射、动态生成逻辑
# 职责：管理搜刮点的生成、显示、独立掉落
# =============================================================================
init python:
    class SearchPoint:
        """一个具体的搜刮点实例"""
        def __init__(self, point_id, name, desc, loot_table_id=None, event_label=None):
            self.point_id = point_id          # 对应 TREASURE_DB 中的 ID
            self.name = name
            self.desc = desc
            self.loot_table_id = loot_table_id   # 普通搜刮点：对应 TREASURE_DB 的 ID
            self.event_label = event_label       # 事件搜刮点：对应 Ren'Py label 名
            self.searched = False             # 是否已被搜刮

    def generate_search_points(terrain_type):
        """根据地形类型随机生成搜刮点列表"""
        # 湖泊地形：必定包含湖水事件
        if terrain_type == "lake":
            pool_config = TERRAIN_SEARCH_POINT_POOLS.get("lake", TERRAIN_SEARCH_POINT_POOLS["other"])
            count = renpy.random.randint(pool_config["min_count"], pool_config["max_count"])
            # 从池中排除湖水，随机选其他点
            other_points = [p for p in pool_config["pool"] if p != SEARCH_POINT_LAKE_DRINK]
            selected = renpy.random.sample(other_points, min(count - 1, len(other_points)))
            # 必定加入湖水
            selected.append(SEARCH_POINT_LAKE_DRINK)
        else:
            # 40% 概率该区域没有任何搜刮点
            if renpy.random.random() > 0.60:
                return []
            
            pool_config = TERRAIN_SEARCH_POINT_POOLS.get(terrain_type, TERRAIN_SEARCH_POINT_POOLS["other"])
            count = renpy.random.randint(pool_config["min_count"], pool_config["max_count"])
            selected = renpy.random.sample(pool_config["pool"], min(count, len(pool_config["pool"])))
        
        points = []
        for point_id in selected:
            info = SEARCH_POINT_INFO.get(point_id, {"name": "未知", "desc": "一个可疑的地方。"})
            points.append(SearchPoint(
                point_id=point_id,
                name=info["name"],
                desc=info["desc"],
                loot_table_id=point_id if point_id != SEARCH_POINT_LAKE_DRINK else None,
                event_label=info.get("event_label", None),
            ))
        return points

    def roll_search_point_loot(search_point):
        """对单个搜刮点执行掉落摇号（基于标签+权重系统）"""
        if search_point.searched:
            return []
        return roll_search_point_loot_new(search_point)

    def has_unsearched_points(tile):
        """检查格子是否还有未搜刮的搜刮点"""
        if tile is None:
            return False
        points = getattr(tile, 'search_points', None)
        if not points:
            return False
        return any(not p.searched for p in points)

    def get_available_search_modes():
        """返回所有搜刮模式列表（撬棍模式始终显示，但需单独检查装备）"""
        return [SEARCH_MODE_NORMAL, SEARCH_MODE_THOROUGH, SEARCH_MODE_CROWBAR]

    def is_crowbar_equipped():
        """检查玩家右手是否装备了撬棍"""
        if player_inventory is None:
            return False
        right_hand = player_inventory.slots.get("right_hand")
        return right_hand is not None and right_hand.id == 111

    def get_search_action_text(mode, has_loot=True):
        """根据搜刮模式返回动作描述和结束描述"""
        if mode == SEARCH_MODE_NORMAL:
            action_text = "你弯腰翻找着脚下的杂物，用手拨开碎石和灰尘，看看有没有什么能用的东西。"
            if has_loot:
                end_text = "你拍了拍手上的灰，将翻出来的东西在面前的地上排开。"
            else:
                end_text = "你翻遍了每一个角落，什么有用的都没找到。这地方早被人搜过了。"
        elif mode == SEARCH_MODE_THOROUGH:
            action_text = "你蹲下来，用手指扒开碎石和灰尘，不放过任何一个角落。时间一分一秒过去，你能听到自己的心跳声——还有远处逐渐靠近的脚步声。"
            if has_loot:
                end_text = "你直起酸痛的腰，看着地上一小堆翻出来的物资，觉得这时间花得还算值得。"
            else:
                end_text = "你几乎把这块地皮翻了个底朝天，汗水顺着额角滴进泥土里。什么都没有。"
        elif mode == SEARCH_MODE_CROWBAR:
            action_text = "你把撬棍的弯头插进柜门的缝隙，用力一压，生锈的锁应声而碎。这比用手快多了，而且没那么大动静。"
            if has_loot:
                end_text = "撬棍的弯头轻松解决了所有碍事的锁扣。你迅速清点完里面的东西，动作利落得像做过无数次。"
            else:
                end_text = "你撬开了每一个锁，翻遍了每一个抽屉。很遗憾，在被你找到之前，已经有人光顾过了。"
        else:
            action_text = "你开始搜索周围..."
            end_text = "搜索完毕。"
        return action_text, end_text

    def get_encounter_description(enemy, mode):
        """根据敌人类型和搜刮模式返回遇敌描述（返回文本列表，每项一页）"""
        # 根据搜刮模式获取前缀
        if mode == SEARCH_MODE_NORMAL:
            prefix = "你正低头翻找着，忽然听到身后传来了细微的动静。你猛地回头——"
        elif mode == SEARCH_MODE_THOROUGH:
            prefix = "你跪在地上翻找着最后一个角落，手指终于摸到了什么。你抬头想借着光看清楚——"
        elif mode == SEARCH_MODE_CROWBAR:
            prefix = "你正专注地撬着一个铁柜，忽然听到身后传来一声低吼。你握紧了手里的撬棍——它不止能用来开门。"
        else:
            prefix = "你突然感觉到一阵危险的气息——"
        
        # 根据敌人类型获取描述
        if enemy.id == 1:  # 野狗
            base = "一声低沉嘶哑的嚎叫从你背后不远处响起。一双闪着凶光的眼睛正从废墟的阴影中盯着你。它已经饿了很久了。"
        elif enemy.id in [3, 4]:  # 枯萎者、枯萎兽
            base = "一阵湿漉漉的脚步声从你身后靠近。你转过头，一具扭曲的身影正拖着残破的肢体朝你蹒跚而来。"
        elif enemy.id in [7, 8, 10, 12]:  # 虫类
            base = "地面传来窸窸窣窣的声响，你抬头，一只变异生物正在快速穿行。它们早就发现你了。"
        elif enemy.is_human:  # 人类
            base = "一声金属碰撞的脆响让你猛地转过身。一个人影正从不远处的掩体后探出半个身子，手里握着的武器在昏暗的光线中闪着冷光。"
        else:
            base = "地面传来窸窸窣窣的声响，一只变异生物从废墟的缝隙中钻了出来。"
        
        # 返回分开的文本列表，每项独立一页
        return [prefix, base]