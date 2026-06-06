# =============================================================================
# loot.rpy — 战利品/资源生成系统
# 功能：定义战利品生成表（TREASURE_DB）及掉落引擎
# 职责：管理地形/敌人战利品表、概率摇号、物品实例化（含随机耐久度）
# =============================================================================
# ── 战利品掉落引擎 ──
init python:
    import random

    class LootTable:
        """战利品掉落引擎：根据战利品表 ID 摇号生成物品实例"""
        @staticmethod
        def roll_loot(treasure_id, overall_chance=1.0):
            """根据战利品表 ID 执行概率摇号，返回掉落物品实例列表"""
            dropped_instances = []
            # 战利品表不存在则返回空
            if treasure_id not in TREASURE_DB:
                return dropped_instances
            # 整体掉落概率判定
            if random.random() > overall_chance:
                return dropped_instances
            # 逐条概率判定并生成物品实例
            for entry in TREASURE_DB[treasure_id]:
                if random.random() <= entry["chance"]:
                    new_item = create_item_instance(
                        item_id=entry["item_id"],
                        random_durability=True
                    )
                    dropped_instances.append(new_item)
            return dropped_instances

    # ═══════════════════════════════════════════
    # 搜刮点战利品重构系统
    # ═══════════════════════════════════════════

    # ── 稀有度权重定义 ──
    LOOT_RARITY = {
        "trash":   {"weight": 100, "items": [105, 115, 116, 117, 150, 160, 205, 207, 209, 213]},
        "common":  {"weight": 60,  "items": [113, 114, 138, 139, 140, 141, 143, 146, 149, 151, 152, 153, 161, 202, 203, 204, 206, 208, 210, 211, 212, 214, 217]},
        "rare":    {"weight": 20,  "items": [103, 106, 107, 108, 112, 118, 120, 121, 122, 123, 125, 128, 134, 142, 144, 145, 147, 148, 154, 162, 165, 166, 168, 201, 215, 216]},
        "precious":{"weight": 5,  "items": [101, 102, 104, 109, 110, 111, 119, 124, 126, 127, 130, 131, 132, 133, 135, 136, 137]},
    }

    # ── 标签 → 物品ID映射 ──
    TAG_ITEMS = {
        "商业":  [138, 140, 144, 153, 161, 165, 166, 168],
        "办公":  [118, 148, 151, 154],
        "居住":  [106, 107, 108, 120, 121, 122, 123, 125, 134, 138, 144, 145, 201, 165, 166, 168, 206],
        "医疗":  [103, 112, 113, 146, 147, 214, 217],
        "荒野":  [115, 116, 139, 141, 150, 152, 160, 202, 203, 204, 205, 206, 207, 215, 216],
        "狩猎":  [109, 110, 131, 132, 141, 162, 215],
        "水域":  [128, 143, 146, 150, 201, 208, 209],
        "海岸":  [128, 143, 152, 210, 211],
        "交通":  [105, 117, 149, 151, 152],
        "机械":  [104, 105, 110, 111, 130, 131, 132, 149, 151, 152],
        "军事":  [101, 102, 104, 119, 124, 126, 127, 130, 135, 136, 137, 142],
        "沼泽":  [115, 116, 139, 141, 150, 160, 212, 213, 214],
    }

    def roll_search_point_loot_new(search_point):
        """基于标签和稀有度权重的新搜刮逻辑"""
        if search_point.searched:
            return []

        tags = SEARCH_POINT_TAGS.get(search_point.point_id, [])
        
        # 收集所有匹配的物品及其权重
        candidate_items = {}  # item_id -> weight

        # 垃圾物品：始终加入，基础权重
        for item_id in LOOT_RARITY["trash"]["items"]:
            candidate_items[item_id] = LOOT_RARITY["trash"]["weight"]

        # 普通/稀有/珍贵物品：匹配标签则加入，权重 ×3
        for rarity in ["common", "rare", "precious"]:
            base_weight = LOOT_RARITY[rarity]["weight"]
            for item_id in LOOT_RARITY[rarity]["items"]:
                # 检查该物品是否匹配任一标签
                for tag in tags:
                    if item_id in TAG_ITEMS.get(tag, []):
                        candidate_items[item_id] = base_weight * 3
                        break

        # 基础搜刮成功率判定（约 60% 概率搜到东西）
        import random
        if random.random() > SEARCH_SUCCESS_CHANCE:
            return []  # 什么都没找到

        # 权重抽奖，抽取 1~3 件，不重复
        draw_count = random.randint(SEARCH_DROP_MIN, SEARCH_DROP_MAX)
        total_weight = sum(candidate_items.values())
        if total_weight <= 0:
            return []

        dropped = []
        available = dict(candidate_items)

        for _ in range(min(draw_count, len(available))):
            if not available:
                break
            total = sum(available.values())
            roll = random.random() * total
            cumulative = 0
            chosen_id = None
            for item_id, weight in available.items():
                cumulative += weight
                if roll <= cumulative:
                    chosen_id = item_id
                    break
            if chosen_id is not None:
                dropped.append(create_item_instance(chosen_id, random_durability=True))
                del available[chosen_id]

        return dropped

    # ── 敌人战利品表 ID ──
    LOOT_SMALL_CREATURE = 3001    # 小型生物
    LOOT_NORMAL_CREATURE = 3002   # 普通生物
    LOOT_INFECTED = 3003          # 感染者
    LOOT_HUMAN_COMMON = 3004      # 人类（普通）
    LOOT_HUMAN_ARMED = 3005       # 人类（武装）
    LOOT_HUMAN_ELITE = 3006       # 人类（精锐）

    # ── 平原搜刮点 ──
    SEARCH_POINT_ABANDONED_CAMP = 4001
    SEARCH_POINT_DEAD_TREE_HOLLOW = 4002
    SEARCH_POINT_LAKE_DRINK = 4003
    SEARCH_POINT_ABANDONED_CELLAR = 4026
    SEARCH_POINT_OLD_SIGNAL_TOWER = 4027
    SEARCH_POINT_DRIED_RIVERBED = 4028

    # ── 森林搜刮点 ──
    SEARCH_POINT_HUNTER_TREE_STAND = 4004   
    SEARCH_POINT_FALLEN_TREE_ROOT = 4005    
    SEARCH_POINT_DENSE_FOREST_CLEARING = 4006  
    SEARCH_POINT_RANGER_POST = 4029
    SEARCH_POINT_ABANDONED_SAWMILL = 4030
    SEARCH_POINT_ANIMAL_DEN = 4031

    # ── 废墟搜刮点 ──
    SEARCH_POINT_ABANDONED_STORE = 4007
    SEARCH_POINT_ABANDONED_OFFICE = 4008
    SEARCH_POINT_ABANDONED_PHARMACY = 4009
    SEARCH_POINT_ABANDONED_APARTMENT = 4010
    SEARCH_POINT_UNDERGROUND_GARAGE = 4011
    SEARCH_POINT_ABANDONED_FIRE_STATION = 4032
    SEARCH_POINT_ABANDONED_SCHOOL = 4033
    SEARCH_POINT_ABANDONED_LIBRARY = 4034
    SEARCH_POINT_SEWER_ENTRANCE = 4035

    # ── 湖泊搜刮点 ──
    SEARCH_POINT_ABANDONED_FISHING_BOAT = 4012
    SEARCH_POINT_LAKESIDE_CAMP = 4013
    SEARCH_POINT_SHORE_DEBRIS = 4014
    SEARCH_POINT_ABANDONED_BOATHOUSE = 4036
    SEARCH_POINT_FISHING_PIER = 4037
    SEARCH_POINT_LAKESIDE_REEDS = 4038

    # ── 沙滩搜刮点 ──
    SEARCH_POINT_ABANDONED_LIFEGUARD_TOWER = 4015
    SEARCH_POINT_SHIPWRECK = 4016
    SEARCH_POINT_TIDE_CAVE = 4039
    SEARCH_POINT_ABANDONED_BATHING_BEACH = 4040
    SEARCH_POINT_FISHERMAN_SHACK = 4041

    # ── 公路搜刮点 ──
    SEARCH_POINT_ABANDONED_GAS_STATION = 4017
    SEARCH_POINT_ABANDONED_VEHICLE = 4018
    SEARCH_POINT_ROAD_SIGN_SERVICE = 4019
    SEARCH_POINT_ABANDONED_TOLL_BOOTH = 4042
    SEARCH_POINT_OVERTURNED_TRUCK = 4043
    SEARCH_POINT_BRIDGE_CAMP = 4044

    # ── 农田搜刮点 ──
    SEARCH_POINT_ABANDONED_FARMHOUSE = 4020
    SEARCH_POINT_ABANDONED_BARN = 4021
    SEARCH_POINT_ABANDONED_TRACTOR = 4022
    SEARCH_POINT_ABANDONED_MILL = 4045
    SEARCH_POINT_ABANDONED_GREENHOUSE = 4046
    SEARCH_POINT_ABANDONED_WELL = 4047

    # ── 沼泽搜刮点 ──
    SEARCH_POINT_SWAMP_SHACK = 4023
    SEARCH_POINT_ABANDONED_TREEHOUSE = 4024
    SEARCH_POINT_SWAMP_SHIPWRECK = 4025
    SEARCH_POINT_COLLAPSED_HUNTING_STAND = 4048
    SEARCH_POINT_ABANDONED_PUMP_STATION = 4049

    # ── 占位符 ──
    SEARCH_POINT_PLACEHOLDER = 4999

    # ── 新手礼包 ──
    SEARCH_POINT_STARTER_PACK = 5000

    # ── 搜刮点 → 标签映射（必须放在所有 SEARCH_POINT_* 常量之后） ──
    SEARCH_POINT_TAGS = {
        SEARCH_POINT_ABANDONED_CAMP:        ["荒野", "居住"],
        SEARCH_POINT_DEAD_TREE_HOLLOW:      ["荒野"],
        SEARCH_POINT_HUNTER_TREE_STAND:     ["荒野", "狩猎"],
        SEARCH_POINT_FALLEN_TREE_ROOT:      ["荒野"],
        SEARCH_POINT_DENSE_FOREST_CLEARING: ["荒野"],
        SEARCH_POINT_ABANDONED_STORE:       ["商业"],
        SEARCH_POINT_ABANDONED_OFFICE:      ["办公"],
        SEARCH_POINT_ABANDONED_PHARMACY:    ["医疗"],
        SEARCH_POINT_ABANDONED_APARTMENT:   ["居住"],
        SEARCH_POINT_UNDERGROUND_GARAGE:    ["机械"],
        SEARCH_POINT_ABANDONED_FISHING_BOAT:["水域", "居住"],
        SEARCH_POINT_LAKESIDE_CAMP:         ["水域", "荒野"],
        SEARCH_POINT_SHORE_DEBRIS:          ["水域"],
        SEARCH_POINT_ABANDONED_LIFEGUARD_TOWER:["海岸", "居住"],
        SEARCH_POINT_SHIPWRECK:             ["海岸", "机械"],
        SEARCH_POINT_ABANDONED_GAS_STATION: ["交通", "商业"],
        SEARCH_POINT_ABANDONED_VEHICLE:     ["交通", "机械"],
        SEARCH_POINT_ROAD_SIGN_SERVICE:     ["交通", "办公"],
        SEARCH_POINT_ABANDONED_FARMHOUSE:   ["居住", "荒野"],
        SEARCH_POINT_ABANDONED_BARN:        ["居住", "荒野"],
        SEARCH_POINT_ABANDONED_TRACTOR:     ["机械", "荒野"],
        SEARCH_POINT_SWAMP_SHACK:           ["沼泽", "居住"],
        SEARCH_POINT_ABANDONED_TREEHOUSE:   ["沼泽", "荒野"],
        SEARCH_POINT_SWAMP_SHIPWRECK:       ["沼泽", "机械"],
        SEARCH_POINT_ABANDONED_CELLAR:       ["居住"],
        SEARCH_POINT_OLD_SIGNAL_TOWER:       ["办公", "机械"],
        SEARCH_POINT_DRIED_RIVERBED:         ["荒野"],
        SEARCH_POINT_RANGER_POST:            ["居住", "狩猎"],
        SEARCH_POINT_ABANDONED_SAWMILL:      ["机械", "荒野"],
        SEARCH_POINT_ANIMAL_DEN:             ["荒野", "狩猎"],
        SEARCH_POINT_ABANDONED_FIRE_STATION: ["居住", "机械"],
        SEARCH_POINT_ABANDONED_SCHOOL:       ["居住", "医疗"],
        SEARCH_POINT_ABANDONED_LIBRARY:      ["办公"],
        SEARCH_POINT_SEWER_ENTRANCE:         ["机械", "水域"],
        SEARCH_POINT_ABANDONED_BOATHOUSE:    ["水域", "居住"],
        SEARCH_POINT_FISHING_PIER:           ["水域"],
        SEARCH_POINT_LAKESIDE_REEDS:         ["水域", "荒野"],
        SEARCH_POINT_TIDE_CAVE:              ["海岸", "荒野"],
        SEARCH_POINT_ABANDONED_BATHING_BEACH:["海岸", "商业"],
        SEARCH_POINT_FISHERMAN_SHACK:        ["海岸", "居住"],
        SEARCH_POINT_ABANDONED_TOLL_BOOTH:   ["交通", "办公"],
        SEARCH_POINT_OVERTURNED_TRUCK:       ["交通", "商业"],
        SEARCH_POINT_BRIDGE_CAMP:            ["居住", "荒野"],
        SEARCH_POINT_ABANDONED_MILL:         ["居住", "机械"],
        SEARCH_POINT_ABANDONED_GREENHOUSE:   ["荒野", "居住"],
        SEARCH_POINT_ABANDONED_WELL:         ["荒野", "居住"],
        SEARCH_POINT_COLLAPSED_HUNTING_STAND:["沼泽", "狩猎"],
        SEARCH_POINT_ABANDONED_PUMP_STATION: ["沼泽", "机械"],
    }

    # ── 战利品表定义 ──
    TREASURE_DB = {
    # ── 小型生物（辐射鼠等） ──
    LOOT_SMALL_CREATURE: [
        {"item_id": 141, "chance": 0.60},  # 不明生肉
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 105, "chance": 0.15},  # 零件
    ],

    # ── 普通生物（野狗、蟑螂等） ──
    LOOT_NORMAL_CREATURE: [
        {"item_id": 141, "chance": 0.60},  # 不明生肉
        {"item_id": 105, "chance": 0.25},  # 零件
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 116, "chance": 0.10},  # 玻璃瓶
    ],

    # ── 感染者（枯萎兽、寄生体等） ──
    LOOT_INFECTED: [
        {"item_id": 115, "chance": 0.55},  # 破布
        {"item_id": 113, "chance": 0.15},  # 绷带
        {"item_id": 112, "chance": 0.08},  # 抗生素
        {"item_id": 139, "chance": 0.25},  # 干蘑菇
    ],

    # ── 人类（普通：流浪者、拾荒帮众） ──
    LOOT_HUMAN_COMMON: [
        {"item_id": 115, "chance": 0.40},  # 破布
        {"item_id": 114, "chance": 0.25},  # 压缩饼干
        {"item_id": 143, "chance": 0.20},  # 雨水收集瓶
        {"item_id": 105, "chance": 0.20},  # 零件
    ],

    # ── 人类（武装：掠夺者） ──
    LOOT_HUMAN_ARMED: [
        {"item_id": 114, "chance": 0.35},  # 压缩饼干
        {"item_id": 113, "chance": 0.30},  # 绷带
        {"item_id": 104, "chance": 0.15},  # 破旧手枪
        {"item_id": 130, "chance": 0.08},  # 砍刀
    ],

    # ── 人类（精锐：军械残兵） ──
    LOOT_HUMAN_ELITE: [
        {"item_id": 142, "chance": 0.35},  # 军用口粮
        {"item_id": 113, "chance": 0.30},  # 绷带
        {"item_id": 104, "chance": 0.25},  # 破旧手枪
        {"item_id": 127, "chance": 0.05},  # 防弹背心
    ],

    SEARCH_POINT_PLACEHOLDER: [
        {"item_id": 115, "chance": 0.30},
        {"item_id": 116, "chance": 0.20},
    ],
}

    def roll_and_collect_search_point(search_point):
        """对搜刮点执行掉落并放入地面容器，返回是否触发遭遇战"""
        if search_point.searched:
            return False
        
        dropped = roll_search_point_loot(search_point)
        search_point.searched = True
        
        tile = get_current_tile()
        if tile and dropped:
            for item in dropped:
                tile.ground_container.add_item(item)
            item_names = "、".join(item.config.name for item in dropped)
            adventure_log.append(f"你在{search_point.name}中翻找，找到了：{item_names}")
        else:
            adventure_log.append(f"你翻遍了{search_point.name}，一无所获。")
        
        # 根据地形决定遭遇概率
        _terrain_encounter_chances = {
            "city_ruins": 0.40,  # 废墟：高
            "swamp":      0.35,  # 沼泽：高
            "forest":     0.30,  # 森林：中高
            "road":       0.25,  # 公路：中
            "farmland":   0.25,  # 农田：中
            "plains":     0.20,  # 平原：中低
            "lake":       0.20,  # 湖泊：中低
            "beach":      0.15,  # 沙滩：低
        }
        tile = get_current_tile()
        terrain = tile.terrain_type if tile else "plains"
        encounter_chance = _terrain_encounter_chances.get(terrain, 0.20)
        
        if random.random() < encounter_chance:
            return True
        return False