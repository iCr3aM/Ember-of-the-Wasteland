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
    COND_SHELTER = 491              # 闪避状态（非疾病，但与生理状态相关，放在此处）

    # 疲劳状态
    COND_FATIGUE = 401
    COND_SEVERE_FATIGUE = 402
    COND_FAINT = 403

    # 口渴状态元组（用于批量清除）
    CONDITIONAL_THIRST_IDS = (COND_THIRST, COND_DEHYDRATED, COND_EXTREME_DEHYDRATED)
    
    # 口渴阈值：大于60为口渴、大于80为脱水、大于90为极度脱水
    THIRST_THRESHOLDS = {
        'thirst': 60.0,
        'dehydrated': 80.0,
        'extreme_dehydrated': 90.0,
    }

    # 地图移动消耗（每步）
    TRAVEL_COSTS = {
        'hunger_per_step': 2.0,
        'thirst_per_step': 3.0,
        'fatigue_per_step': 2.5,
    }

    # 每小时基础代谢（用于 tick）
    METABOLISM_PER_HOUR = {
        'hunger': 2.0,
        'thirst': 3.0,
        'fatigue': 1.5,
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
    'min_fatigue_to_camp': 40.0,        # 最低疲劳值才能扎营
    'fatigue_recovery_per_hour': 10.0,   # 每小时恢复的疲劳值
    'min_sleep_hours': 6,                # 最少睡眠时间
    'max_sleep_hours': 8,                # 最大睡眠时间
    'thirst_rate_multiplier': 0.5,       # 睡眠期间口渴值增加倍率
}