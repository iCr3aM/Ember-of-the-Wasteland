# =============================================================================
# loot.rpy — 战利品/资源生成系统
# 功能：定义战利品生成表（TREASURE_DB）及掉落引擎
# 职责：管理地形/敌人战利品表、概率摇号、物品实例化（含随机耐久度）
# =============================================================================
# ── 战利品掉落引擎 ──
init python:
    class LootTable:
        """战利品掉落引擎：根据战利品表 ID 按权重摇号生成物品实例"""
        @staticmethod
        def roll_loot(treasure_id, overall_chance=1.0):
            """根据战利品表 ID 执行权重摇号，返回掉落物品实例列表"""
            dropped_instances = []
            # 战利品表不存在则返回空
            if treasure_id not in TREASURE_DB:
                return dropped_instances
            # 整体掉落概率判定
            if renpy.random.random() > overall_chance:
                return dropped_instances
            
            # 按权重抽取 1~3 件，不重复
            draw_count = renpy.random.randint(1, 3)
            available = dict(TREASURE_DB[treasure_id])  # {item_id: weight}
            
            for _ in range(min(draw_count, len(available))):
                if not available:
                    break
                total = sum(available.values())
                roll = renpy.random.random() * total
                cumulative = 0
                chosen_id = None
                for item_id, weight in available.items():
                    cumulative += weight
                    if roll <= cumulative:
                        chosen_id = item_id
                        break
                if chosen_id is not None:
                    dropped_instances.append(
                        create_item_instance(chosen_id, random_durability=True)
                    )
                    del available[chosen_id]
            
            return dropped_instances

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
        if renpy.random.random() > SEARCH_SUCCESS_CHANCE:
            return []  # 什么都没找到

        # 权重抽奖，抽取 1~3 件，不重复
        draw_count = renpy.random.randint(SEARCH_DROP_MIN, SEARCH_DROP_MAX)
        total_weight = sum(candidate_items.values())
        if total_weight <= 0:
            return []

        dropped = []
        available = dict(candidate_items)

        for _ in range(min(draw_count, len(available))):
            if not available:
                break
            total = sum(available.values())
            roll = renpy.random.random() * total
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
        LOOT_SMALL_CREATURE: {
            141: 60,   # 不明生肉
            115: 20,   # 破布
            105: 15,   # 零件
        },

        # ── 犬科生物（野狗） ──
        LOOT_CANINE: {
            141: 80,   # 不明生肉
            115: 30,   # 破布
            105: 10,   # 零件
        },

        # ── 虫类生物（蟑螂、吸血虫、蜈蚣、蝎尾蝇） ──
        LOOT_INSECT: {
            141: 60,   # 不明生肉
            115: 30,   # 破布
            105: 25,   # 零件
            116: 15,   # 玻璃瓶
        },

        # ── 感染者（枯萎者、寄生体） ──
        LOOT_INFECTED: {
            141: 60,   # 不明生肉
            115: 55,   # 破布
            113: 15,   # 绷带
            112: 8,    # 抗生素
            139: 25,   # 干蘑菇
        },

        # ── 精英感染者（枯萎兽） ──
        LOOT_INFECTED_ELITE: {
            141: 60,   # 不明生肉
            115: 40,   # 破布
            113: 30,   # 绷带
            112: 20,   # 抗生素
            139: 30,   # 干蘑菇
            105: 20,   # 零件
        },

        # ── 人类（普通：流浪者、拾荒帮众） ──
        LOOT_HUMAN_COMMON: {
            115: 40,   # 破布
            114: 25,   # 压缩饼干
            143: 20,   # 雨水收集瓶
            105: 20,   # 零件
        },

        # ── 人类（武装：掠夺者） ──
        LOOT_HUMAN_ARMED: {
            130: 100,  # 砍刀
            114: 35,   # 压缩饼干
            113: 30,   # 绷带
            201: 10,   # 纯净水
        },

        # ── 人类（精锐：军械残兵） ──
        LOOT_HUMAN_ELITE: {
            104: 100,  # 破旧手枪
            142: 35,   # 军用口粮
            113: 30,   # 绷带
            127: 5,    # 防弹背心
        },

        SEARCH_POINT_PLACEHOLDER: {
            115: 30,
            116: 20,
        },
    }

    def roll_and_collect_search_point(search_point, mode=SEARCH_MODE_NORMAL):
        """对搜刮点执行掉落并放入地面容器，返回是否触发遭遇战"""
        if search_point.searched:
            return False
        
        # ★ 出生保护区内搜刮不会遇敌
        if is_in_birth_protection_zone(player_hex_x, player_hex_y):
            # 执行搜刮但不触发战斗
            mode_cfg = SEARCH_MODE_CONFIG[mode]
            dropped = roll_search_point_loot_with_mode(search_point, mode_cfg)
            search_point.searched = True
            tile = get_current_tile()
            if tile and dropped:
                for item in dropped:
                    tile.ground_container.add_item(item)
                item_names = "、".join(item.config.name for item in dropped)
                adventure_log.append(f"你在{search_point.name}中翻找，找到了：{item_names}")
            else:
                adventure_log.append(f"你翻遍了{search_point.name}，一无所获。")
            return False  # 不触发战斗
        
        # 根据模式获取掉落配置
        mode_cfg = SEARCH_MODE_CONFIG[mode]
        
        # 执行掉落摇号（使用模式参数）
        dropped = roll_search_point_loot_with_mode(search_point, mode_cfg)
        search_point.searched = True
        
        tile = get_current_tile()
        if tile and dropped:
            for item in dropped:
                tile.ground_container.add_item(item)
            item_names = "、".join(item.config.name for item in dropped)
            adventure_log.append(f"你在{search_point.name}中翻找，找到了：{item_names}")
        else:
            adventure_log.append(f"你翻遍了{search_point.name}，一无所获。")
        
        # 根据地形和模式决定遭遇概率
        tile = get_current_tile()
        terrain = tile.terrain_type if tile else "plains"
        encounter_chance = SEARCH_ENCOUNTER_CHANCES.get(terrain, SEARCH_ENCOUNTER_FALLBACK)
        encounter_chance += mode_cfg["encounter_bonus"]  # 加上模式加成
        
        if renpy.random.random() < encounter_chance:
            return True
        return False

    def roll_search_point_loot_with_mode(search_point, mode_cfg):
        """根据搜刮模式执行掉落摇号"""
        if search_point.searched:
            return []
        
        # 先执行普通掉落
        dropped = roll_search_point_loot_new(search_point)
        
        # 如果有保底要求，检查是否满足
        guarantee = mode_cfg.get("guarantee")
        if guarantee and dropped:
            # 检查掉落中是否有≥保底稀有度的物品
            has_guaranteed = False
            for item in dropped:
                item_id = item.id
                for rarity in ["common", "rare", "precious"]:
                    if item_id in LOOT_RARITY[rarity]["items"]:
                        if rarity == guarantee or \
                            (guarantee == "common" and rarity in ("common", "rare", "precious")) or \
                            (guarantee == "rare" and rarity in ("rare", "precious")):
                            has_guaranteed = True
                            break
                if has_guaranteed:
                    break
            
            # 如果没有保底物品，额外补一件
            if not has_guaranteed:
                # 从保底稀有度及以上抽取一件
                candidates = []
                for rarity in ["common", "rare", "precious"]:
                    if rarity == guarantee or \
                        (guarantee == "common" and rarity in ("common", "rare", "precious")) or \
                        (guarantee == "rare" and rarity in ("rare", "precious")):
                        for item_id in LOOT_RARITY[rarity]["items"]:
                            candidates.append(item_id)
                if candidates:
                    extra_id = renpy.random.choice(candidates)
                    dropped.append(create_item_instance(extra_id, random_durability=True))
        
        return dropped