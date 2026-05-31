# Constants and tunables for the game systems
init -200 python:  #优先级

    # 战斗状态
    COND_BLEED = 201                # 流血
    COND_POISON = 202               # 中毒
    COND_STAGGER = 203              # 失衡
    COND_ENTANGLED = 204            # 被缠绕
    COND_FRACTURE = 205             # 骨折
    COND_INTERNAL_INJURY = 206      # 内伤
    COND_DEFENSE = 207              # 全力防御

    # 疾病状态
    COND_THIRST = 301               # 口渴
    COND_HUNGER = 302               # 饥饿
    COND_DEHYDRATED = 303           # 脱水
    COND_EXTREME_DEHYDRATED = 304   # 极度脱水
    COND_ORGAN_FAILURE = 305        # 器官衰竭
    COND_SEVERE_HUNGER = 306       # 重度饥饿
    COND_EXTREME_HUNGER = 307      # 极度饥饿
    COND_MALNUTRITION = 308        # 营养不良

    COND_SHELTER = 491              # 闪避状态（非疾病，但与生理状态相关，放在此处）

    # 疲劳状态
    COND_FATIGUE = 401
    COND_SEVERE_FATIGUE = 402
    COND_FAINT = 403

    # 脚部状态
    COND_BARE_FOOT = 501       # 赤脚
    COND_CUT_FOOT = 502        # 脚底割伤

    # 口渴状态元组（用于批量清除）
    CONDITIONAL_THIRST_IDS = (COND_THIRST, COND_DEHYDRATED, COND_EXTREME_DEHYDRATED, COND_ORGAN_FAILURE)
    CONDITIONAL_HUNGER_IDS = (COND_HUNGER, COND_SEVERE_HUNGER, COND_EXTREME_HUNGER, COND_MALNUTRITION)
    
    # 口渴阈值
    THIRST_THRESHOLDS = {
        'thirst': 51.0,
        'dehydrated': 81.0,
        'extreme_dehydrated': 96.0,
        'organ_failure': 100.0,
    }

    # 饥饿阈值
    HUNGER_THRESHOLDS = {
        'hunger': 51.0,
        'severe_hunger': 81.0,
        'extreme_hunger': 96.0,
        'malnutrition': 100.0,
    }

    # 地图移动消耗表（每步）
    TERRAIN_TRAVEL_COSTS = {
        "plains":     {"minutes": 15, "hunger": 1.8, "thirst": 2.0, "fatigue": 2.5},
        "beach":      {"minutes": 20, "hunger": 2.2, "thirst": 2.5, "fatigue": 3.0},
        "forest":     {"minutes": 25, "hunger": 2.2, "thirst": 2.5, "fatigue": 3.0},
        "city_ruins": {"minutes": 30, "hunger": 3.5, "thirst": 4.0, "fatigue": 5.0},
        "lake":       {"minutes": 25, "hunger": 2.8, "thirst": 3.2, "fatigue": 4.0},
        "ocean":      None,  # 不可穿越
        "road":       {"minutes": 10, "hunger": 1.5, "thirst": 1.8, "fatigue": 1.5}, 
        "farmland":   {"minutes": 20, "hunger": 2.5, "thirst": 2.0, "fatigue": 2.5}, 
        "swamp":      {"minutes": 35, "hunger": 4.0, "thirst": 4.5, "fatigue": 5.0},
        "other":      {"minutes": 30, "hunger": 3.5, "thirst": 4.0, "fatigue": 5.0},
    }

    # 每五分钟基础代谢（用于 tick）
    METABOLISM_PER_5MIN = {
        'hunger': 0.05,
        'thirst': 0.1,
        'fatigue': 0.05,
    }

    # 疲劳阈值
    FATIGUE_THRESHOLDS = {
        'fatigue': 60.0,
        'severe_fatigue': 80.0,
        'faint': 100.0,
    }

    # 搜刮消耗定义
    SCAVENGE_COSTS = {
        'hunger': 5.0,
        'thirst': 8.0,
        'fatigue': 6.0,
    }

    # 扎营休息配置
    CAMP_CONFIG = {
    'min_fatigue_to_camp': 40.0,             # 最低疲劳值才能扎营（不变）
    'fatigue_recovery_per_5min': 10.0 / 12,  # 约0.8333（原每小时10.0，÷12）
    'hp_recovery_per_5min': 5.0 / 12,        # ← 新增：约0.4167（等效每小时5 HP）
    'min_sleep_minutes': 360,                # 最少睡眠6小时 → 360分钟
    'max_sleep_minutes': 480,                # 最大睡眠8小时 → 480分钟
    'thirst_rate_multiplier': 0.5,           # 睡眠期间口渴增加倍率（不变，但计算方式修正）
}