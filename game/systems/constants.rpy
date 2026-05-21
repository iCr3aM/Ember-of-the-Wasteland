# Constants and tunables for the game systems
init -200 python:  #优先级
    
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

    # 战斗动作消耗
    COMBAT_ACTION_COSTS = {
        'battle_move': {'hunger': 4.0, 'thirst': 6.0, 'fatigue': 5.0},
        'attack': {'hunger': 6.0, 'thirst': 8.0, 'fatigue': 7.0},
    }

    # 每小时基础代谢（用于 tick）
    METABOLISM_PER_HOUR = {
        'hunger': 4.0,
        'thirst': 6.0,
        'fatigue': 3.0,
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