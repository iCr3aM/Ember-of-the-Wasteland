# =============================================================================
# # 战利品/资源生成系统
# # 定义：战利品/资源生成表（`TREASURE_DB`，包含多概率档位的物品组合）。 
# # 实现：当 NPC 死亡、玩家搜索废墟、或者遭遇战获胜时，负责“摇号/丢骰子”生成一堆具体的物品实例。
# =============================================================================
init python:
    import random

    class LootTable:
        """战利品与资源刷新池引擎"""
        @staticmethod
        def roll_loot(treasure_id):
            """输入 TreasureID，丢骰子随机实例化一揽子物品"""
            dropped_instances = []
            if treasure_id not in TREASURE_DB:
                return dropped_instances

            # 结构格式：TREASURE_DB[id] = [{"item_id": 501, "chance": 0.4}, ...]
            for entry in TREASURE_DB[treasure_id]:
                if random.random() <= entry["chance"]:
                    # 生成独立动态物品对象
                    new_item = ItemInstance(item_id=entry["item_id"])
                    dropped_instances.append(new_item)
            return dropped_instances