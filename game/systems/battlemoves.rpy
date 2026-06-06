# =============================================================================
# battlemoves.rpy — 战术动作/移动数据库
# 功能：定义非直接伤害的战术动作（BATTLE_MOVES_DB，如冲锋、掩体、逃离）
# 职责：管理动作的前置条件判定与效果（距离变更、姿态切换）
# =============================================================================
# ── 战术动作类定义 ──
init python:
    class BattleMove:
        """战术动作静态原型：定义距离范围、消耗、前置条件、效果"""
        def __init__(self, id, name, desc, min_range, max_range, hunger_cost=0, thirst_cost=0, fatigue_cost=0, cooldown=0, us_pre_conds=None, them_pre_conds=None, success_effects=None):
            self.id = id
            self.name = name
            self.desc = desc
            self.min_range = min_range
            self.max_range = max_range
            self.hunger_cost = hunger_cost
            self.thirst_cost = thirst_cost
            self.fatigue_cost = fatigue_cost
            self.us_pre_conds = us_pre_conds or []       # 自身前置条件（正=必须有，负=不能有）
            self.them_pre_conds = them_pre_conds or []   # 目标前置条件（正=必须有，负=不能有）
            self.success_effects = success_effects or {} # 成功效果，如 {"range_change": -2, "set_pose": "cover"}
            self.cooldown = cooldown  # 使用后冷却回合数（0=无冷却）

        def is_usable(self, user, target, current_range):
            """检查战术动作是否满足所有前置条件"""
            if not (self.min_range <= current_range <= self.max_range):
                return False
            
            # 校验自身状态前置条件
            user_cond_ids = [c.id for c in user.active_conditions]
            for cond in self.us_pre_conds:
                if cond > 0 and cond not in user_cond_ids:
                    return False  # 缺少必须状态
                if cond < 0 and abs(cond) in user_cond_ids:
                    return False  # 挂载了禁忌状态
                
            # 校验目标状态前置条件
            target_cond_ids = [c.id for c in target.active_conditions]
            for cond in self.them_pre_conds:
                if cond > 0 and cond not in target_cond_ids:
                    return False  # 目标缺少必须状态
                if cond < 0 and abs(cond) in target_cond_ids:
                    return False  # 目标挂载了禁忌状态
                
            return True

    # ── 通用基础移动（玩家与大多数NPC皆可使用） ──
    BATTLE_MOVES_DB[1] = BattleMove(1, "前进", "谨慎地向敌人靠近两步，保持战斗姿态。", 1, 14, hunger_cost=0.3, thirst_cost=0.3, fatigue_cost=0.5, success_effects={"range_change": -2})
    BATTLE_MOVES_DB[2] = BattleMove(2, "后退", "向后撤退两步，与敌人拉开距离。", 1, 14, hunger_cost=0.3, thirst_cost=0.3, fatigue_cost=0.5, success_effects={"range_change": 2})
    BATTLE_MOVES_DB[3] = BattleMove(3, "冲锋", "爆发性地向前冲刺，大幅拉近与敌人的距离。", 4, 20, hunger_cost=0.8, thirst_cost=0.8, fatigue_cost=1.5, cooldown=0, us_pre_conds=[-COND_FRACTURE], success_effects={"range_change": -4})
    BATTLE_MOVES_DB[4] = BattleMove(4, "进入掩体", "找到掩体并进入，降低受到的攻击伤害。", 4, 14, hunger_cost=1.0, thirst_cost=1.0, fatigue_cost=1.5, us_pre_conds=[-COND_SHELTER], success_effects={"set_pose": "cover"})
    #BATTLE_MOVES_DB[5] = BattleMove(5, "防御", 1, 6, hunger_cost=2, thirst_cost=2, fatigue_cost=2, success_effects={"set_pose": "defend"})
    BATTLE_MOVES_DB[6] = BattleMove(6, "逃离战斗", "不顾一切地向远处奔逃，尝试脱离战场。", 8, 12, hunger_cost=1.5, thirst_cost=1.5, fatigue_cost=3.0, cooldown=6, us_pre_conds=[-COND_FRACTURE], success_effects={"range_change": 8})
    #BATTLE_MOVES_DB[7] = BattleMove(7, "原地等待", 1, 16, hunger_cost=0, thirst_cost=0, fatigue_cost=0, success_effects={"range_change": 0})
    BATTLE_MOVES_DB[8] = BattleMove(8, "向前走", "稳步向前迈进一步，节省体力。", 1, 20, hunger_cost=0.2, thirst_cost=0.2, fatigue_cost=0.3, success_effects={"range_change": -1})
    BATTLE_MOVES_DB[9] = BattleMove(9, "掩体前移", "在掩体中向前移动一格。", 1, 20, hunger_cost=0.4, thirst_cost=0.4, fatigue_cost=0.6, us_pre_conds=[COND_SHELTER], success_effects={"range_change": -1})
    BATTLE_MOVES_DB[10] = BattleMove(10, "掩体后退", "在掩体中向后撤退一格。", 1, 20, hunger_cost=0.4, thirst_cost=0.4, fatigue_cost=0.6, us_pre_conds=[COND_SHELTER], success_effects={"range_change": 1})
    BATTLE_MOVES_DB[11] = BattleMove(11, "退出掩体", "放弃掩体，回到普通战斗姿态。", 1, 20, hunger_cost=0.2, thirst_cost=0.2, fatigue_cost=0.5, us_pre_conds=[COND_SHELTER], success_effects={"unset_pose": "cover"})
    BATTLE_MOVES_DB[12] = BattleMove(12, "起身", "从地上爬起来，重新站稳脚跟。", 1, 20, hunger_cost=0.5, thirst_cost=0.5, fatigue_cost=1.0, us_pre_conds=[COND_PRONE], success_effects={"unset_pose": "prone"})