# =============================================================================
# constants.rpy — 游戏全局常量与可调参数
# 功能：集中定义状态ID、阈值、地形消耗、扎营配置等所有数值常量
# 职责：作为中央数值配置表，供各系统统一引用，避免硬编码
# =============================================================================
# ── 全局常量定义（init -200 确保最早加载） ──
init -200 python:

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
    LOOT_OVERALL_CHANCE = 0.6      # 敌人战利品整体掉落概率
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
    AUTO_HP_RECOVERY_PER_5MIN = 1.0 / 12          # 每5分钟恢复量（等效每小时1.0HP）

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

    # ── 每5分钟基础代谢（用于 tick） ──
    METABOLISM_PER_5MIN = {
        'hunger': 0.05,
        'thirst': 0.1,
        'fatigue': 0.05,
    }

    # ── 搜刮消耗定义（按地形） ──
    SCAVENGE_COSTS = {
        "road": {
            "minutes": 8,
            "hunger": 0.2,
            "thirst": 0.3,
            "fatigue": 0.4,
        },
        "plains": {
            "minutes": 10,
            "hunger": 0.3,
            "thirst": 0.4,
            "fatigue": 0.6,
        },
        "beach": {
            "minutes": 12,
            "hunger": 0.4,
            "thirst": 0.5,
            "fatigue": 0.8,
        },
        "farmland": {
            "minutes": 15,
            "hunger": 0.5,
            "thirst": 0.6,
            "fatigue": 1.0,
        },
        "forest": {
            "minutes": 15,
            "hunger": 0.5,
            "thirst": 0.6,
            "fatigue": 1.0,
        },
        "city_ruins": {
            "minutes": 20,
            "hunger": 0.7,
            "thirst": 0.8,
            "fatigue": 1.7,
        },
        "lake": {
            "minutes": 12,
            "hunger": 0.4,
            "thirst": 0.4,
            "fatigue": 0.6,
        },
        "swamp": {
            "minutes": 25,
            "hunger": 0.8,
            "thirst": 1.0,
            "fatigue": 2.2,
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