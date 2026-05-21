# =============================================================================
# # 战术动作/移动数据库
# # 定义：非直接伤害的战术动作（`BATTLE_MOVES_DB`，如冲锋、绊倒、寻找掩体、投降）。
# # 实现：判定动作的前置条件（如：必须在距离4以内才能冲锋），计算动作成功率，并改变交战双方的“姿态值”或“距离值”。
# =============================================================================
init python:
    class BattleMove:
        """对应 battlemoves.xml 战术动作结构"""
        def __init__(self, id, name, min_range, max_range, us_pre_conds=None, them_pre_conds=None, success_effects=None):
            self.id = id
            self.name = name
            self.min_range = min_range
            self.max_range = max_range
            self.us_pre_conds = us_pre_conds or []     # 必须满足自身状态ID（正数必须有，负数不能有）
            self.them_pre_conds = them_pre_conds or [] # 必须满足对方状态ID
            self.success_effects = success_effects or {} # 改变姿态或距离的效果，例如 {"range_change": -1, "set_pose": "cover"}

        def is_usable(self, user, target, current_range):
            """执行严苛的战术前置条件判定"""
            if not (self.min_range <= current_range <= self.max_range):
                return False
            
            # 校验自身状态前置条件
            user_cond_ids = [c.id for c in user.active_conditions]
            for cond in self.us_pre_conds:
                if cond > 0 and cond not in user_cond_ids: return False # 缺少必须状态
                if cond < 0 and abs(cond) in user_cond_ids: return False # 挂载了禁忌状态
                
            # 校验目标状态前置条件
            target_cond_ids = [c.id for c in target.active_conditions]
            for cond in self.them_pre_conds:
                if cond > 0 and cond not in target_cond_ids: return False
                if cond < 0 and abs(cond) in target_cond_ids: return False
                
            return True

# ======================== 通用基础移动 (玩家与大多数NPC皆可使用) ==============================
    BATTLE_MOVES_DB[1] = BattleMove(1, "前进", 1, 15, success_effects={"range_change": -2})  # 快速缩短距离
    BATTLE_MOVES_DB[2] = BattleMove(2, "撤退", 1, 15, success_effects={"range_change": 2})  # 快速拉开距离
    BATTLE_MOVES_DB[3] = BattleMove(3, "冲锋", 1, 10, success_effects={"range_change": -4})  # 大幅缩短距离
    