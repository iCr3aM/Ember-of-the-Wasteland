# =============================================================================
# search_points.rpy — 搜刮点生成系统
# 功能：定义搜刮点数据模型、地形→搜刮点池映射、动态生成逻辑
# 职责：管理搜刮点的生成、显示、独立掉落
# =============================================================================
init python:
    import random

    class SearchPoint:
        """一个具体的搜刮点实例"""
        def __init__(self, point_id, name, desc, loot_table_id=None, event_label=None):
            self.point_id = point_id          # 对应 TREASURE_DB 中的 ID
            self.name = name
            self.desc = desc
            self.loot_table_id = loot_table_id   # 普通搜刮点：对应 TREASURE_DB 的 ID
            self.event_label = event_label       # 事件搜刮点：对应 Ren'Py label 名
            self.searched = False             # 是否已被搜刮

    # ── 搜刮点显示信息 ──
    SEARCH_POINT_INFO = {
        # ── 新手礼包 ──
        SEARCH_POINT_STARTER_PACK: {
            "name": "旧世界的物资箱",
            "desc": "一个布满灰尘的旧世界物资箱，里面似乎装满了物资。",
        },

        # ── 平原 ──
        SEARCH_POINT_ABANDONED_CAMP: {
            "name": "废弃营地",
            "desc": "一个被遗弃的临时营地，帐篷已经坍塌，但也许还留下了一些有用的东西。",
        },
        SEARCH_POINT_DEAD_TREE_HOLLOW: {
            "name": "枯树洞",
            "desc": "一棵巨大的枯树，树干上有一个空洞，里面似乎藏着什么东西。",
        },
        SEARCH_POINT_ABANDONED_CELLAR: {
            "name": "废弃地窖",
            "desc": "一扇斜开在地面上的铁门，台阶长满青苔。这曾是一户人家的储藏室，厚重的土墙让里面的东西保存得比外面好。",
        },
        SEARCH_POINT_OLD_SIGNAL_TOWER: {
            "name": "古老的信号塔",
            "desc": "一座锈迹斑斑的钢架信号塔，底部机房里散落着被遗弃的设备和几本受潮的工作日志。",
        },
        SEARCH_POINT_DRIED_RIVERBED: {
            "name": "干涸的河床",
            "desc": "曾经的小溪早已断流，碎石间嵌着被冲刷而来的零碎物品。几只变异蜥蜴在阴影里窥视着你。",
        },


        # ── 森林 ──
        SEARCH_POINT_HUNTER_TREE_STAND: {
            "name": "猎人的树架",
            "desc": "树干上钉着的简易木架，猎人曾蹲在上面等待猎物。",
        },
        SEARCH_POINT_FALLEN_TREE_ROOT: {
            "name": "倒木根区",
            "desc": "被风暴掀翻的巨树，根部翘起形成天然浅坑。",
        },
        SEARCH_POINT_DENSE_FOREST_CLEARING: {
            "name": "密林空地",
            "desc": "灌木围住的空地，几块被苔藓覆盖的石头适合藏东西。",
        },
        SEARCH_POINT_RANGER_POST: {
            "name": "护林员哨站",
            "desc": "一座架在几棵粗壮树干之间的木屋，屋顶塌了一半，但柜子里可能还锁着护林员的装备。",
        },
        SEARCH_POINT_ABANDONED_SAWMILL: {
            "name": "废弃锯木场",
            "desc": "生锈的电锯、堆成小山的木屑、半截埋在土里的圆木。机器早就停了，但工具还在。",
        },
        SEARCH_POINT_ANIMAL_DEN: {
            "name": "兽穴",
            "desc": "一个被荆棘半遮住的土洞，洞口散落着嚼碎的骨头。某种大型生物曾住在这里，现在里面也许还藏着它拖回来的战利品。",
        },

        # ── 废墟 ──
        SEARCH_POINT_ABANDONED_STORE: {
            "name": "废弃商店",
            "desc": "铁皮卷帘门被撬开一半，货架歪倒在地，但仓库里也许还有存货。",
        },
        SEARCH_POINT_ABANDONED_OFFICE: {
            "name": "废弃办公楼",
            "desc": "玻璃碎了一地，抽屉全被拉开，但总有人漏掉最下面那层。",
        },
        SEARCH_POINT_ABANDONED_PHARMACY: {
            "name": "废弃药房",
            "desc": "门上的红十字掉了一半，几个锁着的柜子还没被撬开。",
        },
        SEARCH_POINT_ABANDONED_APARTMENT: {
            "name": "废弃公寓",
            "desc": "住户的门半开半掩，衣柜、床底、厨房橱柜——能翻的地方很多。",
        },
        SEARCH_POINT_UNDERGROUND_GARAGE: {
            "name": "地下车库",
            "desc": "斜坡入口的钢筋裸露在外，角落里堆着废弃车胎和铁桶。",
        },
        SEARCH_POINT_ABANDONED_FIRE_STATION: {
            "name": "废弃消防站",
            "desc": "车库里还停着一辆轮胎瘪了的消防车，墙上挂着生锈的消防斧。二楼的生活区被翻得乱七八糟。",
        },
        SEARCH_POINT_ABANDONED_SCHOOL: {
            "name": "废弃学校",
            "desc": "课桌椅歪倒一地，黑板上有人用粉笔写着潦草的求救信息。医务室和食堂也许还有东西没被搬空。",
        },
        SEARCH_POINT_ABANDONED_LIBRARY: {
            "name": "废弃图书馆",
            "desc": "书架像多米诺骨牌一样倒在地上，纸页发黄发脆。大部分书被拿去生火了，但厚重的档案室铁门还锁着。",
        },
        SEARCH_POINT_SEWER_ENTRANCE: {
            "name": "废弃下水道入口",
            "desc": "一个敞开的检修井，铁梯子锈得嘎吱作响。地下管道里偶尔有风灌上来，带着霉味和某种生物的味道。",
        },

        # ── 湖泊 ──
        SEARCH_POINT_ABANDONED_FISHING_BOAT: {
            "name": "废弃渔船",
            "desc": "锈迹斑斑的铁皮渔船搁浅在岸边，甲板下的储物舱可能还封着。",
        },
        SEARCH_POINT_LAKESIDE_CAMP: {
            "name": "湖边营地",
            "desc": "用芦苇杆和塑料布搭成的窝棚，主人不知去向。",
        },
        SEARCH_POINT_SHORE_DEBRIS: {
            "name": "浅滩杂物堆",
            "desc": "湖水冲上来的一堆杂物：树枝、塑料瓶、被泡烂的布料。",
        },
        SEARCH_POINT_LAKE_DRINK: {
            "name": "湖水",
            "desc": "浑浊的湖水泛着诡异的油彩光泽。",
            "event_label": "encounter_lake_water",   # 指向已有的事件标签
        },
        SEARCH_POINT_ABANDONED_BOATHOUSE: {
            "name": "废弃船屋",
            "desc": "一座半塌的木板房歪在湖面上，靠几根快烂透的木桩撑着。门口系着一艘底朝天的划艇。",
        },
        SEARCH_POINT_FISHING_PIER: {
            "name": "钓鱼栈桥",
            "desc": "一条伸向湖心的木栈道，栏杆断了几处。尽头有一个铁皮工具箱，锁早被人砸了，但里面似乎还有东西。",
        },
        SEARCH_POINT_LAKESIDE_REEDS: {
            "name": "湖畔芦苇丛",
            "desc": "比人还高的芦苇密密匝匝地长在水边，风过时沙沙作响。里面藏着鸟巢和被冲上来的浮木杂物。",
        },

        # ── 沙滩 ──
        SEARCH_POINT_ABANDONED_LIFEGUARD_TOWER: {
            "name": "废弃救生塔",
            "desc": "歪斜的木制瞭望塔，底层的储藏室里锁着救生设备。",
        },
        SEARCH_POINT_SHIPWRECK: {
            "name": "废船残骸",
            "desc": "被风暴拍碎在礁石上的货船，货舱裸露在外。",
        },
        SEARCH_POINT_TIDE_CAVE: {
            "name": "潮汐洞穴",
            "desc": "退潮后露出一个低矮的岩洞口，往里看一片漆黑。涨潮时这里会被海水淹没，所以没人敢住，但偶尔有人把东西藏进来。",
        },
        SEARCH_POINT_ABANDONED_BATHING_BEACH: {
            "name": "废弃海滨浴场",
            "desc": "褪色的遮阳伞歪在沙子里，售票亭的玻璃碎了，后面有几个锈得不成样子的储物柜。",
        },
        SEARCH_POINT_FISHERMAN_SHACK: {
            "name": "渔民小屋",
            "desc": "一间用漂流木和铁皮搭成的小棚子，墙上挂着渔网浮标和晒干的鱼线。住在这里的人早就走了，或者被什么东西拖走了。",
        },

        # ── 公路 ──
        SEARCH_POINT_ABANDONED_GAS_STATION: {
            "name": "废弃加油站",
            "desc": "顶棚塌了半边，便利店里的货架东倒西歪，但冰柜也许还有存货。",
        },
        SEARCH_POINT_ABANDONED_VEHICLE: {
            "name": "废弃车辆",
            "desc": "一辆轿车侧翻在路边，后备箱半开着。",
        },
        SEARCH_POINT_ROAD_SIGN_SERVICE: {
            "name": "路牌服务站",
            "desc": "砖砌的小休息站，墙上贴着褪色的旧公路地图。",
        },
        SEARCH_POINT_ABANDONED_TOLL_BOOTH: {
            "name": "废弃收费站",
            "desc": "一个逼仄的水泥亭子，玻璃窗被砸碎，收费机的抽屉半开，里面的硬币早被人掏空。但墙角还有被忽略的杂物。",
        },
        SEARCH_POINT_OVERTURNED_TRUCK: {
            "name": "翻倒的货运卡车",
            "desc": "一辆侧翻在路基下的重型卡车，货柜上的锁还挂着。司机室里散落着私人物品，货柜里堆着早已腐烂的货箱。",
        },
        SEARCH_POINT_BRIDGE_CAMP: {
            "name": "桥洞下的营地",
            "desc": "公路桥的阴影里，有人用硬纸板和塑料布搭过一个临时窝。篝火的余烬早已冰冷，几件东西被匆匆遗落在角落里。",
        },

        # ── 农田 ──
        SEARCH_POINT_ABANDONED_FARMHOUSE: {
            "name": "废弃农舍",
            "desc": "木门歪在门框上，灶台下的铁锅还盖着。",
        },
        SEARCH_POINT_ABANDONED_BARN: {
            "name": "废弃谷仓",
            "desc": "堆着发霉干草和锈蚀农具的谷仓，角落里立着一把镰刀。",
        },
        SEARCH_POINT_ABANDONED_TRACTOR: {
            "name": "废弃拖拉机",
            "desc": "轮胎瘪了的旧拖拉机，驾驶室玻璃全碎，工具箱锁在座位下。",
        },
        SEARCH_POINT_ABANDONED_MILL: {
            "name": "废弃磨坊",
            "desc": "一座石砌的老磨坊，风车叶片断了两根。底层还堆着几袋发霉的谷物，齿轮间卡着破布和工具。",
        },
        SEARCH_POINT_ABANDONED_GREENHOUSE: {
            "name": "废弃温室",
            "desc": "玻璃顶棚碎了大半，里面种的东西早就死光了。花盆和培养槽间散落着园艺工具和几袋干结的肥料。",
        },
        SEARCH_POINT_ABANDONED_WELL: {
            "name": "废弃水井",
            "desc": "一口石砌的老井，井口盖着半块木板。探头往下看，一股凉气扑面而来。井壁上曾经有人藏过东西——用绳子吊下去的那种。",
        },

        # ── 沼泽 ──
        SEARCH_POINT_SWAMP_SHACK: {
            "name": "沼泽窝棚",
            "desc": "架在木桩上的破棚子，里面堆满了捡来的破烂。",
        },
        SEARCH_POINT_ABANDONED_TREEHOUSE: {
            "name": "废弃树屋",
            "desc": "搭在老树上的小木屋，绳索梯子断了一半。",
        },
        SEARCH_POINT_SWAMP_SHIPWRECK: {
            "name": "沼泽沉船",
            "desc": "被沼泽吞没了一半的平底船，密闭的铁箱可能还干燥。",
        },
        SEARCH_POINT_COLLAPSED_HUNTING_STAND: {
            "name": "倒塌的狩猎高台",
            "desc": "一座歪在泥水里的木制高台，猎人曾蹲在上面等鹿。梯子断了，但平台上可能还留着装备。",
        },
        SEARCH_POINT_ABANDONED_PUMP_STATION: {
            "name": "废弃泵站",
            "desc": "一座被藤蔓吞没的砖砌泵站，巨大的铁管从泥地里伸出，像死去的巨兽骸骨。里面回荡着滴水的声音。",
        },

        # ── 其他地形占位符 ──
        SEARCH_POINT_PLACEHOLDER: {
            "name": "可疑地点",
            "desc": "一个看起来值得翻找的地方。",
        },
    }

    # ── 地形 → 搜刮点池映射 ──
    TERRAIN_SEARCH_POINT_POOLS = {
        "plains": {
            "pool": [SEARCH_POINT_ABANDONED_CAMP, SEARCH_POINT_DEAD_TREE_HOLLOW,
                    SEARCH_POINT_ABANDONED_CELLAR, SEARCH_POINT_OLD_SIGNAL_TOWER,
                    SEARCH_POINT_DRIED_RIVERBED],
            "min_count": 1,
            "max_count": 3,
        },
        "forest": {
            "pool": [SEARCH_POINT_HUNTER_TREE_STAND, SEARCH_POINT_FALLEN_TREE_ROOT,
                    SEARCH_POINT_DENSE_FOREST_CLEARING, SEARCH_POINT_RANGER_POST,
                    SEARCH_POINT_ABANDONED_SAWMILL, SEARCH_POINT_ANIMAL_DEN],
            "min_count": 1,
            "max_count": 3,
        },
        "city_ruins": {
            "pool": [SEARCH_POINT_ABANDONED_STORE, SEARCH_POINT_ABANDONED_OFFICE,
                    SEARCH_POINT_ABANDONED_PHARMACY, SEARCH_POINT_ABANDONED_APARTMENT,
                    SEARCH_POINT_UNDERGROUND_GARAGE, SEARCH_POINT_ABANDONED_FIRE_STATION,
                    SEARCH_POINT_ABANDONED_SCHOOL, SEARCH_POINT_ABANDONED_LIBRARY,
                    SEARCH_POINT_SEWER_ENTRANCE],
            "min_count": 2,
            "max_count": 4,
        },
        "lake": {
            "pool": [SEARCH_POINT_LAKE_DRINK, SEARCH_POINT_ABANDONED_FISHING_BOAT,
                    SEARCH_POINT_LAKESIDE_CAMP, SEARCH_POINT_SHORE_DEBRIS,
                    SEARCH_POINT_ABANDONED_BOATHOUSE, SEARCH_POINT_FISHING_PIER,
                    SEARCH_POINT_LAKESIDE_REEDS],
            "min_count": 1,
            "max_count": 3,
        },
        "beach": {
            "pool": [SEARCH_POINT_ABANDONED_LIFEGUARD_TOWER, SEARCH_POINT_SHIPWRECK,
                    SEARCH_POINT_TIDE_CAVE, SEARCH_POINT_ABANDONED_BATHING_BEACH,
                    SEARCH_POINT_FISHERMAN_SHACK],
            "min_count": 1,
            "max_count": 2,
        },
        "road": {
            "pool": [SEARCH_POINT_ABANDONED_GAS_STATION, SEARCH_POINT_ABANDONED_VEHICLE,
                    SEARCH_POINT_ROAD_SIGN_SERVICE, SEARCH_POINT_ABANDONED_TOLL_BOOTH,
                    SEARCH_POINT_OVERTURNED_TRUCK, SEARCH_POINT_BRIDGE_CAMP],
            "min_count": 1,
            "max_count": 2,
        },
        "farmland": {
            "pool": [SEARCH_POINT_ABANDONED_FARMHOUSE, SEARCH_POINT_ABANDONED_BARN,
                    SEARCH_POINT_ABANDONED_TRACTOR, SEARCH_POINT_ABANDONED_MILL,
                    SEARCH_POINT_ABANDONED_GREENHOUSE, SEARCH_POINT_ABANDONED_WELL],
            "min_count": 1,
            "max_count": 3,
        },
        "swamp": {
            "pool": [SEARCH_POINT_SWAMP_SHACK, SEARCH_POINT_ABANDONED_TREEHOUSE,
                    SEARCH_POINT_SWAMP_SHIPWRECK, SEARCH_POINT_COLLAPSED_HUNTING_STAND,
                    SEARCH_POINT_ABANDONED_PUMP_STATION],
            "min_count": 1,
            "max_count": 2,
        },
        "other": {
            "pool": [SEARCH_POINT_PLACEHOLDER],
            "min_count": 1,
            "max_count": 2,
        },
    }

    STARTER_ITEMS = [201, 113, 138, 160, 161]

    def roll_starter_pack():
        """生成新手礼包物品列表（只生效一次）"""
        global _starter_loot_claimed
        if _starter_loot_claimed:
            return []
        _starter_loot_claimed = True
        items = []
        for item_id in STARTER_ITEMS:
            items.append(create_item_instance(item_id, random_durability=True))
        return items

    def generate_search_points(terrain_type):
        """根据地形类型随机生成搜刮点列表（60%概率出现搜刮点）"""
        # 40% 概率该区域没有任何搜刮点
        if random.random() > 0.60:
            return []
        
        pool_config = TERRAIN_SEARCH_POINT_POOLS.get(terrain_type, TERRAIN_SEARCH_POINT_POOLS["other"])
        count = random.randint(pool_config["min_count"], pool_config["max_count"])
        
        selected = random.sample(pool_config["pool"], min(count, len(pool_config["pool"])))
        
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

    def click_search_point(point):
        """点击搜刮点：事件型返回标签，新手礼包特殊处理，普通型执行掉落"""
        if point.event_label:
            return ("event", point.event_label)
        elif point.point_id == SEARCH_POINT_STARTER_PACK:
            return ("starter_pack", point)   # ★ 新手礼包走特殊分支
        else:
            return ("loot", point)