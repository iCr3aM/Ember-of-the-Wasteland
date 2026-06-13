# =============================================================================
# constants.rpy — 游戏全局常量与可调参数
# 功能：集中定义状态ID、阈值、地形消耗、扎营配置等所有数值常量
# 职责：作为中央数值配置表，供各系统统一引用，避免硬编码
# =============================================================================
# ── 全局常量定义（init -200 确保最早加载） ──
init -200 python:
    # ═══════════════════════════════════════════
    # 音乐播放冷却（游戏内分钟数）
    # ═══════════════════════════════════════════
    EXPLORE_MUSIC_COOLDOWN_MINUTES = 30  # 30分钟游戏内时间冷却
    # 战斗状态
    COND_BLEED = 201                # 流血
    COND_POISON = 202               # 中毒
    COND_STAGGER = 203              # 失衡
    COND_ENTANGLED = 204            # 被缠绕
    COND_FRACTURE = 205             # 骨折
    COND_INTERNAL_INJURY = 206      # 内伤

    # 疾病状态
    COND_THIRST = 301               # 口渴
    COND_HUNGER = 302               # 饥饿
    COND_DEHYDRATED = 303           # 脱水
    COND_EXTREME_DEHYDRATED = 304   # 极度脱水
    COND_ORGAN_FAILURE = 305        # 器官衰竭
    COND_SEVERE_HUNGER = 306        # 重度饥饿
    COND_EXTREME_HUNGER = 307       # 极度饥饿
    COND_MALNUTRITION = 308         # 营养不良

    # 疲劳状态
    COND_FATIGUE = 401              # 疲劳
    COND_SEVERE_FATIGUE = 402       # 重度疲劳
    COND_FAINT = 403                # 昏阙

    # ── 尼古丁成瘾状态 ──
    COND_NICOTINE_MILD = 701         # 尼古丁初瘾（轻度依赖）
    COND_NICOTINE_MODERATE = 702     # 尼古丁成瘾（中度依赖）
    COND_NICOTINE_SEVERE = 703       # 尼古丁重瘾（重度依赖）

    COND_SHELTER = 491              # 闪避状态
    COND_PRONE = 492                # 摔倒/倒地
    COND_MORIBUND = 493             # 濒死（HP < 30%）
    COND_DEAD = 494                 # 死亡（HP = 0）

    # 脚部状态
    COND_BARE_FOOT = 501       # 赤脚
    COND_CUT_FOOT = 502        # 脚底割伤

    # ── NPC 词条 ID ──
    TRAIT_WEAK = 601                # 虚弱（Trash）
    TRAIT_FRAIL = 602               # 孱弱（Trash）
    TRAIT_SLUGGISH = 603            # 迟缓（Trash）
    TRAIT_DECAYING = 604            # 衰竭（Trash）
    TRAIT_FOCUSED = 605             # 专注（Common）
    TRAIT_DROUGHT_RESISTANT = 606   # 耐渴（Common）
    TRAIT_ENERGETIC = 607           # 精力充沛（Common）
    TRAIT_TOUGH = 608               # 强硬（Rare）
    TRAIT_FEROCIOUS = 609           # 凶猛（Rare）
    TRAIT_EASTER_EGG = 610          # 彩蛋（Easter Egg）

    # ── 状态批量清除元组 ──
    CONDITIONAL_THIRST_IDS = (COND_THIRST, COND_DEHYDRATED, COND_EXTREME_DEHYDRATED, COND_ORGAN_FAILURE)
    CONDITIONAL_HUNGER_IDS = (COND_HUNGER, COND_SEVERE_HUNGER, COND_EXTREME_HUNGER, COND_MALNUTRITION)
    
    # ── 口渴阈值 ──
    THIRST_THRESHOLDS = {
        'thirst': 51.0,                # 口渴
        'dehydrated': 81.0,            # 脱水
        'extreme_dehydrated': 96.0,    # 极度脱水
        'organ_failure': 100.0,        # 器官衰竭
    }

    # ── 饥饿阈值 ──
    HUNGER_THRESHOLDS = {
        'hunger': 51.0,                # 饥饿
        'severe_hunger': 81.0,         # 重度饥饿
        'extreme_hunger': 96.0,        # 极度饥饿
        'malnutrition': 100.0,         # 营养不良
    }

    # ── 疲劳阈值 ──
    FATIGUE_THRESHOLDS = {
        'fatigue': 60.0,             # 疲劳
        'severe_fatigue': 80.0,      # 重度疲劳
        'faint': 100.0,              # 昏阙
    }

    # ═══════════════════════════════════════════
    # 战斗数值常量（集中配置）
    # ═══════════════════════════════════════════

    # ── 命中率边界 ──
    HIT_CHANCE_MIN = 0.05          # 命中率下限 5%
    HIT_CHANCE_MAX = 0.99          # 命中率上限 99%
    RANGE_MOD_FALLBACK = 0.5       # 超出射程范围时的回退修正系数

    # ── 掩体击破概率 ──
    SHELTER_BREAK_MELEE = 0.80     # 近战/天然武器击破掩体概率 80%
    SHELTER_BREAK_RANGED = 0.20    # 远程武器击破掩体概率 20%

    # ── 逃离战斗 ──
    ESCAPE_HP_LOW = 0.30           # 低血量阈值（≤30% 自动脱离）
    ESCAPE_HP_MID = 0.60           # 中血量阈值（≤60% 拉开距离）
    ESCAPE_TRIP_CHANCE = 0.05      # 逃离时摔倒概率 5%

    # ── 伤害浮动 ──
    ENEMY_DAMAGE_MIN = 0.60        # 敌人伤害浮动下限
    ENEMY_DAMAGE_MAX = 0.80        # 敌人伤害浮动上限

    # ── 战利品/搜刮 ──
    LOOT_OVERALL_CHANCE = 0.80      # 敌人战利品整体掉落概率
    SEARCH_SUCCESS_CHANCE = 0.60   # 搜刮点搜到东西的基础概率
    SEARCH_DROP_MIN = 1            # 搜刮最少物品数
    SEARCH_DROP_MAX = 3            # 搜刮最多物品数

    # ═══════════════════════════════════════════
    # 战斗距离阈值
    # ═══════════════════════════════════════════
    COMBAT_RANGE_MELEE_MAX = 6      # 近战最大距离（≤6 消耗三维）
    COMBAT_RANGE_MELEE_ADVANCE = 4  # 近战AI前进阈值（>4 则前进）
    COMBAT_RANGE_RANGED_MIN = 8     # 远程最小距离（<8 则后退 / ≥8 视为远程）
    COMBAT_RANGE_ESCAPE = 20        # 脱离战斗距离（≥20 脱离）
    COMBAT_RANGE_CLOSE_PENALTY = 3  # 逃离近身惩罚距离（≤3 惩罚）
    COMBAT_RANGE_ENTANGLED_ATTACK = 2  # 缠绕时远程攻击距离（>2 可用）

    # ═══════════════════════════════════════════
    # 逃离战斗数值
    # ═══════════════════════════════════════════
    ESCAPE_CLOSE_PENALTY_VALUE = 2  # 近身逃离惩罚值
    ESCAPE_BASE_FLEE = 8            # 逃离基础距离（敌人犹豫追击）
    ESCAPE_BASE_CHASE = 4           # 逃离基础距离（敌人全力追击）

    # ═══════════════════════════════════════════
    # 命中率相关（从 combat.rpy 迁移）
    # ═══════════════════════════════════════════
    BASE_HIT_CHANCE = 0.85                    # 基础命中率 85%
    PLAYER_DAMAGE_MULTIPLIER = (0.80, 1.20)   # 玩家伤害浮动范围
    PLAYER_HIT_MULTIPLIER = (0.90, 1.10)      # 玩家命中率浮动范围
    BASE_DODGE_CHANCE = 0.10                  # 基础闪避率 10%

    RANGE_HIT_MODIFIERS = {
        "point_blank": (1, 2, 1.0),
        "close":       (3, 5, 0.9),
        "medium":      (6, 10, 0.75),
        "long":        (11, 15, 0.55),
        "extreme":     (16, 20, 0.40),
    }

    WEAPON_HIT_BASE = {
        "melee":   0.95,
        "pistol":  0.80,
        "rifle":   0.75,
        "throw":   0.60,
        "natural": 0.85,
    }

    # ═══════════════════════════════════════════
    # 冲撞/掩体/缠绕数值
    # ═══════════════════════════════════════════
    CHARGE_RANGE_REDUCE = 3         # 冲撞拉近距离
    SHELTER_COOLDOWN_TURNS = 4      # 退出掩体后冷却回合数
    ENTANGLE_COOLDOWN_TURNS = 4     # 缠绕冷却回合数
    ENTANGLE_COOLDOWN_KEY = "entangle"  # 缠绕冷却字典键
    SHELTER_ENTER_CHANCE_HUMAN = 0.6   # 人类敌人进入掩体的概率（60%）

    # ── 尼古丁成瘾阈值 ──
    NICOTINE_MILD_THRESHOLD = 20       # 轻度依赖：≥20 支
    NICOTINE_MODERATE_THRESHOLD = 50   # 中度依赖：≥50 支
    NICOTINE_SEVERE_THRESHOLD = 100    # 重度依赖：≥100 支
    NICOTINE_MILD_HOURS = 24           # 轻度戒断：24小时
    NICOTINE_MODERATE_HOURS = 12       # 中度戒断：12小时
    NICOTINE_SEVERE_HOURS = 6          # 重度戒断：6小时

    # ── 濒死阈值 ──
    MORIBUND_HP_THRESHOLD = 0.30   # 濒死触发阈值（HP < 30%）

    # ── 自动生命恢复（无口渴/饥饿状态时） ──
    AUTO_HP_RECOVERY_PER_5MIN = 5.0 / 12          # 每5分钟恢复量（等效每小时5.0HP）

    # ── 地形移动消耗表（每步） ──
    TERRAIN_TRAVEL_COSTS = {
        "plains":     {"minutes": 15, "hunger": 1.8, "thirst": 2.0, "fatigue": 2.5},
        "beach":      {"minutes": 20, "hunger": 2.2, "thirst": 2.5, "fatigue": 3.0},
        "forest":     {"minutes": 25, "hunger": 2.2, "thirst": 2.5, "fatigue": 3.0},
        "city_ruins": {"minutes": 30, "hunger": 3.5, "thirst": 4.0, "fatigue": 5.0},
        "lake":       {"minutes": 25, "hunger": 2.8, "thirst": 3.2, "fatigue": 4.0},
        "ocean":      None,                                            # 不可穿越
        "road":       {"minutes": 10, "hunger": 1.5, "thirst": 1.8, "fatigue": 1.5}, 
        "farmland":   {"minutes": 20, "hunger": 2.5, "thirst": 2.0, "fatigue": 2.5}, 
        "swamp":      {"minutes": 35, "hunger": 4.0, "thirst": 4.5, "fatigue": 5.0},
        "other":      {"minutes": 30, "hunger": 3.5, "thirst": 4.0, "fatigue": 5.0},
    }

    # ═══════════════════════════════════════════
    # 事件系统（从 encounters.rpy 迁移）
    # ═══════════════════════════════════════════
    EVENT_ENCOUNTER_DEFAULT = 2001

    TERRAIN_ENEMY_MAP = {
        "road":       [13, 2],
        "plains":     [1, 2],
        "farmland":   [5, 13],
        "forest":     [6, 10],
        "beach":      [5, 8],
        "city_ruins": [3, 4, 7],
        "lake":       [1, 8],
        "swamp":      [12, 4, 7],
        "ocean":      [],
    }

    # 兜底敌人池
    FALLBACK_ENEMY_POOL = [1, 2, 3, 5, 6, 7, 8, 10, 12, 13]

    EVENT_CONFIG = {
        EVENT_ENCOUNTER_DEFAULT: {
            "label": "event_encounter_default",
            "name": "丛林低吼",
            "type": "combat",
        },
    }

    EVENT_LABEL_MAP = {event_id: data["label"] for event_id, data in EVENT_CONFIG.items()}

    # ═══════════════════════════════════════════
    # 湖泊饮水事件数值
    # ═══════════════════════════════════════════
    LAKE_WATER_POISON_CHANCE = 0.5    # 中毒概率 50%
    LAKE_WATER_HP_DAMAGE = 15.0       # 中毒时 HP 损失
    LAKE_WATER_THIRST_PENALTY = 20.0  # 中毒时口渴增加
    LAKE_WATER_THIRST_RELIEF = 40.0   # 饮水解渴量

    # ── 每5分钟基础代谢（用于 tick） ──
    METABOLISM_PER_5MIN = {
        'hunger': 0.05,
        'thirst': 0.1,
        'fatigue': 0.05,
    }

    # ── 探索消耗定义（按地形） ──
    SCAVENGE_COSTS = {
        "road": {
            "minutes": 4,
            "hunger": 0.1,
            "thirst": 0.15,
            "fatigue": 0.2,
        },
        "plains": {
            "minutes": 5,
            "hunger": 0.15,
            "thirst": 0.2,
            "fatigue": 0.3,
        },
        "beach": {
            "minutes": 6,
            "hunger": 0.2,
            "thirst": 0.25,
            "fatigue": 0.4,
        },
        "farmland": {
            "minutes": 7,
            "hunger": 0.25,
            "thirst": 0.3,
            "fatigue": 0.5,
        },
        "forest": {
            "minutes": 7,
            "hunger": 0.25,
            "thirst": 0.3,
            "fatigue": 0.5,
        },
        "city_ruins": {
            "minutes": 10,
            "hunger": 0.35,
            "thirst": 0.4,
            "fatigue": 0.85,
        },
        "lake": {
            "minutes": 6,
            "hunger": 0.2,
            "thirst": 0.2,
            "fatigue": 0.3,
        },
        "swamp": {
            "minutes": 12,
            "hunger": 0.4,
            "thirst": 0.5,
            "fatigue": 1.1,
        },
    }

    # ── 扎营休息配置 ──
    CAMP_CONFIG = {
        'min_fatigue_to_camp': 40.0,             # 最低疲劳值才能扎营
        'fatigue_recovery_per_5min': 10.0 / 12,  # 每5分钟疲劳恢复量（等效每小时10.0）
        'hp_recovery_per_5min': 12.0 / 12,        # 每5分钟生命恢复量（等效每小时12.0）
        'min_sleep_minutes': 360,                # 最少睡眠分钟数（6小时）
        'max_sleep_minutes': 480,                # 最大睡眠分钟数（8小时）
        'thirst_rate_multiplier': 0.5,           # 睡眠期间口渴增加倍率
    }

    # ═══════════════════════════════════════════
    # 搜刮点遇敌概率（按地形）
    # ═══════════════════════════════════════════
    SEARCH_ENCOUNTER_CHANCES = {
        "city_ruins": 0.55,  # 废墟：55%
        "swamp":      0.50,  # 沼泽：50%
        "forest":     0.45,  # 森林：45%
        "road":       0.40,  # 公路：40%
        "farmland":   0.40,  # 农田：40%
        "plains":     0.35,  # 平原：35%
        "lake":       0.35,  # 湖泊：35%
        "beach":      0.30,  # 沙滩：30%
    }
    SEARCH_ENCOUNTER_FALLBACK = 0.30  # 未知地形兜底概率

    # ═══════════════════════════════════════════
    # 敌人稀有度权重（类似 LOOT_RARITY）
    # ═══════════════════════════════════════════
    ENEMY_RARITY = {
        "trash":    {"weight": 100, "enemies": [1, 3, 5, 6, 7, 8, 10]},
        "common":   {"weight": 60,  "enemies": [2, 12, 13]},
        "rare":     {"weight": 20,  "enemies": [4, 9, 11]},
        "precious": {"weight": 5,   "enemies": []},
    }

    # ═══════════════════════════════════════════
    # 战利品表 ID
    # ═══════════════════════════════════════════
    LOOT_SMALL_CREATURE = 3001    # 小型生物
    LOOT_INFECTED = 3003          # 感染者
    LOOT_HUMAN_COMMON = 3004      # 人类（普通）
    LOOT_HUMAN_ARMED = 3005       # 人类（武装）
    LOOT_HUMAN_ELITE = 3006       # 人类（精锐）
    LOOT_CANINE = 3007            # 犬科生物
    LOOT_INSECT = 3008            # 虫类生物
    LOOT_INFECTED_ELITE = 3009    # 精英感染者
    LOOT_PARASITE = 3010          # 植物寄生体

    # ═══════════════════════════════════════════
    # 商店类型常量（从 shop.rpy 迁移）
    # ═══════════════════════════════════════════
    SHOP_TYPE_BLACK_MARKET = "black_market"
    SHOP_TYPE_WASTELAND_TRADER = "wasteland_trader"
    SHOP_TYPE_NPC = "npc"

    SHOP_PRICE_MODIFIERS = {
        SHOP_TYPE_BLACK_MARKET:      {"buy_multiplier": 2.0, "sell_multiplier": 0.5},
        SHOP_TYPE_WASTELAND_TRADER:  {"buy_multiplier": 1.5, "sell_multiplier": 0.6},
        SHOP_TYPE_NPC:               {"buy_multiplier": 1.2, "sell_multiplier": 0.8},
    }

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

    # ── 搜刮点显示信息 ──
    SEARCH_POINT_INFO = {
        # ── 平原 ──
        SEARCH_POINT_ABANDONED_CAMP: {
            "name": "营地",
            "desc": "一个被遗弃的临时营地，帐篷已经坍塌，但也许还留下了一些有用的东西。",
            "icon": "images/search_icons/plains/ABANDONED_CAMP.png",
        },
        SEARCH_POINT_DEAD_TREE_HOLLOW: {
            "name": "枯树洞",
            "desc": "一棵巨大的枯树，树干上有一个空洞，里面似乎藏着什么东西。",
            "icon": "images/search_icons/plains/DEAD_TREE_HOLLOW.png",
        },
        SEARCH_POINT_ABANDONED_CELLAR: {
            "name": "地窖",
            "desc": "一扇斜开在地面上的铁门，台阶长满青苔。这曾是一户人家的储藏室，厚重的土墙让里面的东西保存得比外面好。",
            "icon": "images/search_icons/plains/ABANDONED_CELLAR.png",
        },
        SEARCH_POINT_OLD_SIGNAL_TOWER: {
            "name": "古老信号塔",
            "desc": "一座锈迹斑斑的钢架信号塔，底部机房里散落着被遗弃的设备和几本受潮的工作日志。",
            "icon": "images/search_icons/plains/OLD_SIGNAL_TOWER.png",
        },
        SEARCH_POINT_DRIED_RIVERBED: {
            "name": "干涸河床",
            "desc": "曾经的小溪早已断流，碎石间嵌着被冲刷而来的零碎物品。几只变异蜥蜴在阴影里窥视着你。",
            "icon": "images/search_icons/plains/DRIED_RIVERBED.png",
        },

        # ── 森林 ──
        SEARCH_POINT_HUNTER_TREE_STAND: {
            "name": "猎人树架",
            "desc": "树干上钉着的简易木架，猎人曾蹲在上面等待猎物。",
            "icon": "images/search_icons/forest/HUNTER_TREE_STAND.png",
        },
        SEARCH_POINT_FALLEN_TREE_ROOT: {
            "name": "倒木根区",
            "desc": "被风暴掀翻的巨树，根部翘起形成天然浅坑。",
            "icon": "images/search_icons/forest/FALLEN_TREE_ROOT.png",
        },
        SEARCH_POINT_DENSE_FOREST_CLEARING: {
            "name": "密林空地",
            "desc": "灌木围住的空地，几块被苔藓覆盖的石头适合藏东西。",
            "icon": "images/search_icons/forest/DENSE_FOREST_CLEARING.png",
        },
        SEARCH_POINT_RANGER_POST: {
            "name": "护林员哨站",
            "desc": "一座架在几棵粗壮树干之间的木屋，屋顶塌了一半，但柜子里可能还锁着护林员的装备。",
            "icon": "images/search_icons/forest/RANGER_POST.png",
        },
        SEARCH_POINT_ABANDONED_SAWMILL: {
            "name": "锯木场",
            "desc": "生锈的电锯、堆成小山的木屑、半截埋在土里的圆木。机器早就停了，但工具还在。",
            "icon": "images/search_icons/forest/ABANDONED_SAWMILL.png",
        },
        SEARCH_POINT_ANIMAL_DEN: {
            "name": "兽穴",
            "desc": "一个被荆棘半遮住的土洞，洞口散落着嚼碎的骨头。某种大型生物曾住在这里，现在里面也许还藏着它拖回来的战利品。",
            "icon": "images/search_icons/forest/ANIMAL_DEN.png",
        },

        # ── 废墟 ──
        SEARCH_POINT_ABANDONED_STORE: {
            "name": "商店",
            "desc": "铁皮卷帘门被撬开一半，货架歪倒在地，但仓库里也许还有存货。",
            "icon": "images/search_icons/city_ruins/ABANDONED_STORE.png",
        },
        SEARCH_POINT_ABANDONED_OFFICE: {
            "name": "办公楼",
            "desc": "玻璃碎了一地，抽屉全被拉开，但总有人漏掉最下面那层。",
            "icon": "images/search_icons/city_ruins/ABANDONED_OFFICE.png",
        },
        SEARCH_POINT_ABANDONED_PHARMACY: {
            "name": "药房",
            "desc": "门上的红十字掉了一半，几个锁着的柜子还没被撬开。",
            "icon": "images/search_icons/city_ruins/ABANDONED_PHARMACY.png",
        },
        SEARCH_POINT_ABANDONED_APARTMENT: {
            "name": "公寓",
            "desc": "住户的门半开半掩，衣柜、床底、厨房橱柜——能翻的地方很多。",
            "icon": "images/search_icons/city_ruins/ABANDONED_APARTMENT.png",
        },
        SEARCH_POINT_UNDERGROUND_GARAGE: {
            "name": "地下车库",
            "desc": "斜坡入口的钢筋裸露在外，角落里堆着废弃车胎和铁桶。",
            "icon": "images/search_icons/city_ruins/UNDERGROUND_GARAGE.png",
        },
        SEARCH_POINT_ABANDONED_FIRE_STATION: {
            "name": "消防站",
            "desc": "车库里还停着一辆轮胎瘪了的消防车，墙上挂着生锈的消防斧。二楼的生活区被翻得乱七八糟。",
            "icon": "images/search_icons/city_ruins/ABANDONED_FIRE_STATION.png",
        },
        SEARCH_POINT_ABANDONED_SCHOOL: {
            "name": "学校",
            "desc": "课桌椅歪倒一地，黑板上有人用粉笔写着潦草的求救信息。医务室和食堂也许还有东西没被搬空。",
            "icon": "images/search_icons/city_ruins/ABANDONED_SCHOOL.png",
        },
        SEARCH_POINT_ABANDONED_LIBRARY: {
            "name": "图书馆",
            "desc": "书架像多米诺骨牌一样倒在地上，纸页发黄发脆。大部分书被拿去生火了，但厚重的档案室铁门还锁着。",
            "icon": "images/search_icons/city_ruins/ABANDONED_LIBRARY.png",
        },
        SEARCH_POINT_SEWER_ENTRANCE: {
            "name": "下水道入口",
            "desc": "一个敞开的检修井，铁梯子锈得嘎吱作响。地下管道里偶尔有风灌上来，带着霉味和某种生物的味道。",
            "icon": "images/search_icons/city_ruins/SEWER_ENTRANCE.png",
        },

        # ── 湖泊 ──
        SEARCH_POINT_ABANDONED_FISHING_BOAT: {
            "name": "渔船",
            "desc": "锈迹斑斑的铁皮渔船搁浅在岸边，甲板下的储物舱可能还封着。",
            "icon": "images/search_icons/lake/ABANDONED_FISHING_BOAT.png",
        },
        SEARCH_POINT_LAKESIDE_CAMP: {
            "name": "湖边营地",
            "desc": "用芦苇杆和塑料布搭成的窝棚，主人不知去向。",
            "icon": "images/search_icons/lake/LAKESIDE_CAMP.png",
        },
        SEARCH_POINT_SHORE_DEBRIS: {
            "name": "浅滩杂物堆",
            "desc": "湖水冲上来的一堆杂物：树枝、塑料瓶、被泡烂的布料。",
            "icon": "images/search_icons/lake/SHORE_DEBRIS.png",
        },
        SEARCH_POINT_LAKE_DRINK: {
            "name": "湖水",
            "desc": "浑浊的湖水泛着诡异的油彩光泽。",
            "event_label": "encounter_lake_water",   # 指向已有的事件标签
            "icon": "images/search_icons/lake/LAKE_DRINK.png",
        },
        SEARCH_POINT_ABANDONED_BOATHOUSE: {
            "name": "船屋",
            "desc": "一座半塌的木板房歪在湖面上，靠几根快烂透的木桩撑着。门口系着一艘底朝天的划艇。",
            "icon": "images/search_icons/lake/ABANDONED_BOATHOUSE.png",
        },
        SEARCH_POINT_FISHING_PIER: {
            "name": "钓鱼栈桥",
            "desc": "一条伸向湖心的木栈道，栏杆断了几处。尽头有一个铁皮工具箱，锁早被人砸了，但里面似乎还有东西。",
            "icon": "images/search_icons/lake/FISHING_PIER.png",
        },
        SEARCH_POINT_LAKESIDE_REEDS: {
            "name": "湖畔芦苇丛",
            "desc": "比人还高的芦苇密密匝匝地长在水边，风过时沙沙作响。里面藏着鸟巢和被冲上来的浮木杂物。",
            "icon": "images/search_icons/lake/LAKESIDE_REEDS.png",
        },

        # ── 沙滩 ──
        SEARCH_POINT_ABANDONED_LIFEGUARD_TOWER: {
            "name": "救生塔",
            "desc": "歪斜的木制瞭望塔，底层的储藏室里锁着救生设备。",
            "icon": "images/search_icons/beach/ABANDONED_LIFEGUARD_TOWER.png",
        },
        SEARCH_POINT_SHIPWRECK: {
            "name": "货船残骸",
            "desc": "被风暴拍碎在礁石上的货船，货舱裸露在外。",
            "icon": "images/search_icons/beach/SHIPWRECK.png",
        },
        SEARCH_POINT_TIDE_CAVE: {
            "name": "潮汐洞穴",
            "desc": "退潮后露出一个低矮的岩洞口，往里看一片漆黑。涨潮时这里会被海水淹没，所以没人敢住，但偶尔有人把东西藏进来。",
            "icon": "images/search_icons/beach/TIDE_CAVE.png",
        },
        SEARCH_POINT_ABANDONED_BATHING_BEACH: {
            "name": "海滨浴场",
            "desc": "褪色的遮阳伞歪在沙子里，售票亭的玻璃碎了，后面有几个锈得不成样子的储物柜。",
            "icon": "images/search_icons/beach/ABANDONED_BATHING_BEACH.png",
        },
        SEARCH_POINT_FISHERMAN_SHACK: {
            "name": "渔民小屋",
            "desc": "一间用漂流木和铁皮搭成的小棚子，墙上挂着渔网浮标和晒干的鱼线。",
            "icon": "images/search_icons/beach/FISHERMAN_SHACK.png",
        },

        # ── 公路 ──
        SEARCH_POINT_ABANDONED_GAS_STATION: {
            "name": "加油站",
            "desc": "顶棚塌了半边，便利店里的货架东倒西歪，但冰柜也许还有存货。",
            "icon": "images/search_icons/road/ABANDONED_GAS_STATION.png",
        },
        SEARCH_POINT_ABANDONED_VEHICLE: {
            "name": "车辆",
            "desc": "一辆轿车侧翻在路边，后备箱半开着。",
            "icon": "images/search_icons/road/ABANDONED_VEHICLE.png",
        },
        SEARCH_POINT_ROAD_SIGN_SERVICE: {
            "name": "路牌服务站",
            "desc": "砖砌的小休息站，墙上贴着褪色的旧公路地图。",
            "icon": "images/search_icons/road/ROAD_SIGN_SERVICE.png",
        },
        SEARCH_POINT_ABANDONED_TOLL_BOOTH: {
            "name": "收费站",
            "desc": "一个逼仄的水泥亭子，玻璃窗被砸碎，收费机的抽屉半开，里面的硬币早被人掏空。但墙角还有被忽略的杂物。",
            "icon": "images/search_icons/road/ABANDONED_TOLL_BOOTH.png",
        },
        SEARCH_POINT_OVERTURNED_TRUCK: {
            "name": "侧翻卡车",
            "desc": "一辆侧翻在路基下的重型卡车，货柜上的锁还挂着。司机室里散落着私人物品，货柜里堆着早已腐烂的货箱。",
            "icon": "images/search_icons/road/OVERTURNED_TRUCK.png",
        },
        SEARCH_POINT_BRIDGE_CAMP: {
            "name": "桥洞下营地",
            "desc": "公路桥的阴影里，有人用硬纸板和塑料布搭过一个临时窝。篝火的余烬早已冰冷，几件东西被匆匆遗落在角落里。",
            "icon": "images/search_icons/road/BRIDGE_CAMP.png",
        },

        # ── 农田 ──
        SEARCH_POINT_ABANDONED_FARMHOUSE: {
            "name": "农舍",
            "desc": "木门歪在门框上，灶台下的铁锅还盖着。",
            "icon": "images/search_icons/farmland/ABANDONED_FARMHOUSE.png",
        },
        SEARCH_POINT_ABANDONED_BARN: {
            "name": "谷仓",
            "desc": "堆着发霉干草和锈蚀农具的谷仓，角落里立着一把镰刀。",
            "icon": "images/search_icons/farmland/ABANDONED_BARN.png",
        },
        SEARCH_POINT_ABANDONED_TRACTOR: {
            "name": "拖拉机",
            "desc": "轮胎瘪了的旧拖拉机，驾驶室玻璃全碎，工具箱锁在座位下。",
            "icon": "images/search_icons/farmland/ABANDONED_TRACTOR.png",
        },
        SEARCH_POINT_ABANDONED_MILL: {
            "name": "磨坊",
            "desc": "一座石砌的老磨坊，风车叶片断了两根。底层还堆着几袋发霉的谷物，齿轮间卡着破布和工具。",
            "icon": "images/search_icons/farmland/ABANDONED_MILL.png",
        },
        SEARCH_POINT_ABANDONED_GREENHOUSE: {
            "name": "温室",
            "desc": "玻璃顶棚碎了大半，里面种的东西早就死光了。花盆和培养槽间散落着园艺工具和几袋干结的肥料。",
            "icon": "images/search_icons/farmland/ABANDONED_GREENHOUSE.png",
        },
        SEARCH_POINT_ABANDONED_WELL: {
            "name": "水井",
            "desc": "一口石砌的老井，井口盖着半块木板。井壁上曾经有人藏过东西——用绳子吊下去的那种。",
            "icon": "images/search_icons/farmland/ABANDONED_WELL.png",
        },

        # ── 沼泽 ──
        SEARCH_POINT_SWAMP_SHACK: {
            "name": "沼泽窝棚",
            "desc": "架在木桩上的破棚子，里面堆满了捡来的破烂。",
            "icon": "images/search_icons/swamp/SWAMP_SHACK.png",
        },
        SEARCH_POINT_ABANDONED_TREEHOUSE: {
            "name": "树屋",
            "desc": "搭在老树上的小木屋，绳索梯子断了一半。",
            "icon": "images/search_icons/swamp/ABANDONED_TREEHOUSE.png",
        },
        SEARCH_POINT_SWAMP_SHIPWRECK: {
            "name": "沼泽沉船",
            "desc": "被沼泽吞没了一半的平底船，密闭的铁箱可能还干燥。",
            "icon": "images/search_icons/swamp/SWAMP_SHIPWRECK.png",
        },
        SEARCH_POINT_COLLAPSED_HUNTING_STAND: {
            "name": "倒塌狩猎高台",
            "desc": "一座歪在泥水里的木制高台，猎人曾蹲在上面等鹿。梯子断了，但平台上可能还留着装备。",
            "icon": "images/search_icons/swamp/COLLAPSED_HUNTING_STAND.png",
        },
        SEARCH_POINT_ABANDONED_PUMP_STATION: {
            "name": "水泵站",
            "desc": "一座被藤蔓吞没的砖砌泵站，巨大的铁管从泥地里伸出，里面回荡着滴水的声音。",
            "icon": "images/search_icons/swamp/ABANDONED_PUMP_STATION.png",
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

    # ═══════════════════════════════════════════
    # 搜刮模式配置
    # ═══════════════════════════════════════════
    SEARCH_MODE_NORMAL = "normal"
    SEARCH_MODE_THOROUGH = "thorough"
    SEARCH_MODE_CROWBAR = "crowbar"

    SEARCH_MODE_CONFIG = {
        SEARCH_MODE_NORMAL: {
            "name": "普通搜刮",
            "desc": "标准耗时，正常风险。运气决定一切。",
            "time_multiplier": 1.0,
            "encounter_bonus": 0.0,
            "drop_min": 1,
            "drop_max": 3,
            "guarantee": None,          # 保底稀有度
        },
        SEARCH_MODE_THOROUGH: {
            "name": "仔细搜索",
            "desc": "双倍耗时，遇敌风险+25%。不放过任何角落。",
            "time_multiplier": 2.0,
            "encounter_bonus": 0.25,
            "drop_min": 3,
            "drop_max": 5,
            "guarantee": "common",      # 保底1件≥Common
        },
        SEARCH_MODE_CROWBAR: {
            "name": "撬棍搜刮",
            "desc": "标准耗时，正常风险。利用撬棍快速破开锁具，安静高效。",
            "time_multiplier": 1.0,
            "encounter_bonus": 0.0,
            "drop_min": 3,
            "drop_max": 5,
            "guarantee": "rare",        # 保底1件≥Rare
            "required_item": 111,       # 需要撬棍
        },
    }
