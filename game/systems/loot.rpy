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
        def roll_loot(treasure_id, overall_chance=1.0):
            """
            输入 TreasureID，丢骰子随机实例化一揽子物品。
            overall_chance: 整体掉落概率（0.0-1.0），默认100%必定触发掉落。
            """
            dropped_instances = []
            if treasure_id not in TREASURE_DB:
                return dropped_instances
            
            # ★ 先判定整体掉落概率 ★
            if random.random() > overall_chance:
                return dropped_instances  # 什么都没掉

            # 然后按原有概率生成具体物品
            for entry in TREASURE_DB[treasure_id]:
                if random.random() <= entry["chance"]:
                    new_item = ItemInstance(item_id=entry["item_id"])
                    dropped_instances.append(new_item)
            return dropped_instances


    TREASURE_SCRAP = 1001  # 废墟搜刮通用表

    # 战利品表定义
    TREASURE_DB = {
        TREASURE_SCRAP: [
            {"item_id": 101, "chance": 0.10},  # 破旧头盔 10% (原30%)
            {"item_id": 102, "chance": 0.10},  # 破旧军靴 10% (原30%)
            {"item_id": 103, "chance": 0.08},  # 急救包 8% (原25%)
            {"item_id": 106, "chance": 0.13},  # 破旧的白衬衫 13% (原40%)
            {"item_id": 107, "chance": 0.12},  # 破旧的工装裤 12% (原35%)
            {"item_id": 108, "chance": 0.13},  # 肮脏的运动鞋 13% (原40%)
            {"item_id": 111, "chance": 0.05},  # 撬棍 5% (原15%)
            {"item_id": 112, "chance": 0.07},  # 抗生素 7% (原20%)
            {"item_id": 113, "chance": 0.10},  # 绷带 10% (原30%)
            {"item_id": 114, "chance": 0.12},  # 压缩饼干 12% (原35%)
            {"item_id": 201, "chance": 0.10},  # 纯净水 10% (原30%)
        ]
    }

    def loot_random_scavenge(player_inventory=None):
        """
        大地图搜刮函数：从 TREASURE_SCRAP 表随机生成战利品。
        返回掉落物品列表。
        如果传入 inventory，自动添加进去。
        """
        dropped = LootTable.roll_loot(TREASURE_SCRAP, overall_chance=0.5)  # 只有50%概率搜到东西
        if player_inventory is not None and dropped:
            for item in dropped:
                player_inventory.add_item(item)
        return dropped