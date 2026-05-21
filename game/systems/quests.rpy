# =============================================================================
# # 任务追踪系统逻辑
# # 定义：主线与支线任务的目标结构（`QUESTS_DB`，包含杀怪、寻物、到达某地）。 
# # 实现：任务状态机的追踪（未接取 -> 已接取 -> 目标完成 -> 已交付），给 UI 提供任务日志数据。
# =============================================================================
init python:
    class Quest:
        """任务状态机逻辑数据结构"""
        def __init__(self, id, name, quest_type, target_id, required_count):
            self.id = id
            self.name = name
            self.quest_type = quest_type # "kill" (杀怪) 或 "fetch" (寻物)
            self.target_id = target_id   # 目标怪物ID或物品ID
            self.required_count = required_count
            self.current_progress = 0
            self.status = "active" # active, completed, rewarded

        def update_fetch_progress(self, current_inventory):
            """刷新寻物任务进度"""
            if self.quest_type == "fetch":
                self.current_progress = current_inventory.check_item_count(self.target_id)
                if self.current_progress >= self.required_count:
                    self.status = "completed"