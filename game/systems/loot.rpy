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
            
            # 判定整体掉落概率
            if random.random() > overall_chance:
                return dropped_instances  # 什么都没掉

            # 然后按原有概率生成具体物品
            for entry in TREASURE_DB[treasure_id]:
                if random.random() <= entry["chance"]:
                    new_item = ItemInstance(item_id=entry["item_id"])
                    dropped_instances.append(new_item)
            return dropped_instances


    # 地形专属搜刮表 ID
    TREASURE_SCRAP = 1001        # 通用废墟（保留作为兜底）
    TREASURE_CITY_RUINS = 2001   # 城市废墟
    TREASURE_FOREST = 2002       # 森林
    TREASURE_PLAINS = 2003       # 平原
    TREASURE_FARMLAND = 2004     # 农田
    TREASURE_SWAMP = 2005        # 沼泽
    TREASURE_BEACH = 2006        # 沙滩
    TREASURE_ROAD = 2007         # 公路
    TREASURE_LAKE = 2008         # 湖泊

    # 敌人战利品表 ID
    LOOT_SMALL_CREATURE = 3001    # 小型生物
    LOOT_NORMAL_CREATURE = 3002   # 普通生物
    LOOT_INFECTED = 3003          # 感染者
    LOOT_HUMAN_COMMON = 3004      # 人类（普通）
    LOOT_HUMAN_ARMED = 3005       # 人类（武装）
    LOOT_HUMAN_ELITE = 3006       # 人类（精锐）

    # 地形 → 搜刮表 ID 映射
    TERRAIN_TREASURE_MAP = {
        "city_ruins": TREASURE_CITY_RUINS,
        "forest":     TREASURE_FOREST,
        "plains":     TREASURE_PLAINS,
        "farmland":   TREASURE_FARMLAND,
        "swamp":      TREASURE_SWAMP,
        "beach":      TREASURE_BEACH,
        "road":       TREASURE_ROAD,
        "lake":       TREASURE_LAKE,
        "other":      TREASURE_SCRAP,
    }

    # 战利品表定义
    TREASURE_DB = {
    # ── 小型生物（辐射鼠等） ──
    LOOT_SMALL_CREATURE: [
        {"item_id": 141, "chance": 0.60},  # 不明生肉
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 105, "chance": 0.15},  # 零件
    ],

    # ── 普通生物（野狗、蟑螂等） ──
    LOOT_NORMAL_CREATURE: [
        {"item_id": 141, "chance": 0.60},  # 不明生肉
        {"item_id": 105, "chance": 0.25},  # 零件
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 116, "chance": 0.10},  # 玻璃瓶
    ],

    # ── 感染者（枯萎兽、寄生体等） ──
    LOOT_INFECTED: [
        {"item_id": 115, "chance": 0.55},  # 破布
        {"item_id": 113, "chance": 0.15},  # 绷带
        {"item_id": 112, "chance": 0.08},  # 抗生素
        {"item_id": 139, "chance": 0.25},  # 干蘑菇
    ],

    # ── 人类（普通：流浪者、拾荒帮众） ──
    LOOT_HUMAN_COMMON: [
        {"item_id": 115, "chance": 0.40},  # 破布
        {"item_id": 114, "chance": 0.25},  # 压缩饼干
        {"item_id": 143, "chance": 0.20},  # 雨水收集瓶
        {"item_id": 105, "chance": 0.20},  # 零件
    ],

    # ── 人类（武装：掠夺者） ──
    LOOT_HUMAN_ARMED: [
        {"item_id": 114, "chance": 0.35},  # 压缩饼干
        {"item_id": 113, "chance": 0.30},  # 绷带
        {"item_id": 104, "chance": 0.15},  # 破旧手枪
        {"item_id": 130, "chance": 0.08},  # 砍刀
    ],

    # ── 人类（精锐：军械残兵） ──
    LOOT_HUMAN_ELITE: [
        {"item_id": 142, "chance": 0.35},  # 军用口粮
        {"item_id": 113, "chance": 0.30},  # 绷带
        {"item_id": 104, "chance": 0.25},  # 破旧手枪
        {"item_id": 127, "chance": 0.05},  # 防弹背心
    ],

    # ── 通用废墟（兜底） ──
    TREASURE_SCRAP: [
        {"item_id": 115, "chance": 0.30},  # 破布
        {"item_id": 116, "chance": 0.25},  # 玻璃瓶
        {"item_id": 105, "chance": 0.20},  # 零件
        {"item_id": 117, "chance": 0.15},  # 废电池
        {"item_id": 150, "chance": 0.20},  # 塑料袋
        {"item_id": 151, "chance": 0.15},  # 胶带
        {"item_id": 152, "chance": 0.15},  # 弹簧
        {"item_id": 149, "chance": 0.12},  # 铜线
        {"item_id": 153, "chance": 0.10},  # 打火机
        {"item_id": 106, "chance": 0.15},  # 破旧白衬衫
        {"item_id": 107, "chance": 0.12},  # 破旧工装裤
        {"item_id": 134, "chance": 0.10},  # 牛仔裤
        {"item_id": 108, "chance": 0.10},  # 肮脏运动鞋（左）
        {"item_id": 120, "chance": 0.10},  # 肮脏运动鞋（右）
        {"item_id": 121, "chance": 0.12},  # 人字拖（左）
        {"item_id": 122, "chance": 0.12},  # 人字拖（右）
        {"item_id": 102, "chance": 0.08},  # 破旧军靴（左）
        {"item_id": 119, "chance": 0.08},  # 破旧军靴（右）
        {"item_id": 123, "chance": 0.08},  # 破旧兜帽
        {"item_id": 125, "chance": 0.10},  # 破围巾
        {"item_id": 128, "chance": 0.08},  # 雨衣
        {"item_id": 136, "chance": 0.08},  # 护踝（左）
        {"item_id": 137, "chance": 0.08},  # 护踝（右）
        {"item_id": 114, "chance": 0.12},  # 压缩饼干
        {"item_id": 139, "chance": 0.10},  # 干蘑菇
        {"item_id": 140, "chance": 0.08},  # 能量棒
        {"item_id": 141, "chance": 0.06},  # 生肉
        {"item_id": 138, "chance": 0.05},  # 肉罐头
        {"item_id": 142, "chance": 0.03},  # 军用口粮
        {"item_id": 201, "chance": 0.08},  # 纯净水
        {"item_id": 143, "chance": 0.10},  # 雨水收集瓶
        {"item_id": 144, "chance": 0.05},  # 瓶装可乐
        {"item_id": 145, "chance": 0.04},  # 酒精饮料
        {"item_id": 113, "chance": 0.08},  # 绷带
        {"item_id": 112, "chance": 0.05},  # 抗生素
        {"item_id": 103, "chance": 0.05},  # 急救包
        {"item_id": 146, "chance": 0.06},  # 净水药片
        {"item_id": 147, "chance": 0.04},  # 止痛药
        {"item_id": 109, "chance": 0.06},  # 水果刀
        {"item_id": 110, "chance": 0.04},  # 工具锤
        {"item_id": 111, "chance": 0.03},  # 撬棍
        {"item_id": 129, "chance": 0.04},  # 钢管
        {"item_id": 130, "chance": 0.03},  # 砍刀
        {"item_id": 131, "chance": 0.04},  # 指虎
        {"item_id": 132, "chance": 0.03},  # 棒球棍
        {"item_id": 101, "chance": 0.06},  # 破旧头盔
        {"item_id": 104, "chance": 0.02},  # 破旧手枪
        {"item_id": 118, "chance": 0.03},  # 破旧电子表
        {"item_id": 124, "chance": 0.04},  # 狗牌项链
        {"item_id": 126, "chance": 0.03},  # 皮夹克
        {"item_id": 127, "chance": 0.01},  # 防弹背心
        {"item_id": 133, "chance": 0.04},  # 幸运手链
        {"item_id": 135, "chance": 0.03},  # 战术裤
        {"item_id": 148, "chance": 0.03},  # 情报纸条
    ],

    # ── 城市废墟 ──
    TREASURE_CITY_RUINS: [
        {"item_id": 115, "chance": 0.35},  # 破布
        {"item_id": 116, "chance": 0.30},  # 玻璃瓶
        {"item_id": 105, "chance": 0.25},  # 零件
        {"item_id": 117, "chance": 0.20},  # 废电池
        {"item_id": 150, "chance": 0.25},  # 塑料袋
        {"item_id": 151, "chance": 0.20},  # 胶带
        {"item_id": 152, "chance": 0.18},  # 弹簧
        {"item_id": 149, "chance": 0.15},  # 铜线
        {"item_id": 153, "chance": 0.12},  # 打火机
        {"item_id": 148, "chance": 0.08},  # 情报纸条
        {"item_id": 106, "chance": 0.18},  # 破旧白衬衫
        {"item_id": 107, "chance": 0.15},  # 破旧工装裤
        {"item_id": 134, "chance": 0.12},  # 牛仔裤
        {"item_id": 108, "chance": 0.12},  # 肮脏运动鞋（左）
        {"item_id": 120, "chance": 0.12},  # 肮脏运动鞋（右）
        {"item_id": 123, "chance": 0.10},  # 破旧兜帽
        {"item_id": 125, "chance": 0.12},  # 破围巾
        {"item_id": 128, "chance": 0.10},  # 雨衣
        {"item_id": 126, "chance": 0.05},  # 皮夹克
        {"item_id": 127, "chance": 0.02},  # 防弹背心
        {"item_id": 135, "chance": 0.04},  # 战术裤
        {"item_id": 101, "chance": 0.08},  # 破旧头盔
        {"item_id": 102, "chance": 0.10},  # 破旧军靴（左）
        {"item_id": 119, "chance": 0.10},  # 破旧军靴（右）
        {"item_id": 136, "chance": 0.10},  # 护踝（左）
        {"item_id": 137, "chance": 0.10},  # 护踝（右）
        {"item_id": 109, "chance": 0.08},  # 水果刀
        {"item_id": 110, "chance": 0.06},  # 工具锤
        {"item_id": 111, "chance": 0.05},  # 撬棍
        {"item_id": 129, "chance": 0.06},  # 钢管
        {"item_id": 130, "chance": 0.04},  # 砍刀
        {"item_id": 131, "chance": 0.05},  # 指虎
        {"item_id": 132, "chance": 0.04},  # 棒球棍
        {"item_id": 104, "chance": 0.03},  # 破旧手枪
        {"item_id": 118, "chance": 0.04},  # 破旧电子表
        {"item_id": 124, "chance": 0.05},  # 狗牌项链
        {"item_id": 133, "chance": 0.05},  # 幸运手链
        {"item_id": 114, "chance": 0.10},  # 压缩饼干
        {"item_id": 138, "chance": 0.06},  # 肉罐头
        {"item_id": 142, "chance": 0.04},  # 军用口粮
        {"item_id": 201, "chance": 0.08},  # 纯净水
        {"item_id": 144, "chance": 0.06},  # 瓶装可乐
        {"item_id": 145, "chance": 0.05},  # 酒精饮料
        {"item_id": 113, "chance": 0.10},  # 绷带
        {"item_id": 112, "chance": 0.06},  # 抗生素
        {"item_id": 103, "chance": 0.06},  # 急救包
        {"item_id": 147, "chance": 0.05},  # 止痛药
    ],

    # ── 森林 ──
    TREASURE_FOREST: [
        {"item_id": 139, "chance": 0.30},  # 干蘑菇
        {"item_id": 141, "chance": 0.20},  # 生肉
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 116, "chance": 0.15},  # 玻璃瓶
        {"item_id": 150, "chance": 0.15},  # 塑料袋
        {"item_id": 114, "chance": 0.10},  # 压缩饼干
        {"item_id": 140, "chance": 0.08},  # 能量棒
        {"item_id": 201, "chance": 0.06},  # 纯净水
        {"item_id": 143, "chance": 0.08},  # 雨水收集瓶
        {"item_id": 105, "chance": 0.08},  # 零件
        {"item_id": 117, "chance": 0.06},  # 废电池
        {"item_id": 153, "chance": 0.06},  # 打火机
        {"item_id": 109, "chance": 0.04},  # 水果刀
        {"item_id": 110, "chance": 0.03},  # 工具锤
        {"item_id": 113, "chance": 0.05},  # 绷带
        {"item_id": 146, "chance": 0.04},  # 净水药片
    ],

    # ── 平原 ──
    TREASURE_PLAINS: [
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 116, "chance": 0.18},  # 玻璃瓶
        {"item_id": 150, "chance": 0.18},  # 塑料袋
        {"item_id": 105, "chance": 0.12},  # 零件
        {"item_id": 117, "chance": 0.10},  # 废电池
        {"item_id": 114, "chance": 0.10},  # 压缩饼干
        {"item_id": 201, "chance": 0.08},  # 纯净水
        {"item_id": 143, "chance": 0.10},  # 雨水收集瓶
        {"item_id": 140, "chance": 0.06},  # 能量棒
        {"item_id": 139, "chance": 0.08},  # 干蘑菇
        {"item_id": 141, "chance": 0.05},  # 生肉
        {"item_id": 109, "chance": 0.04},  # 水果刀
        {"item_id": 110, "chance": 0.03},  # 工具锤
        {"item_id": 153, "chance": 0.06},  # 打火机
        {"item_id": 113, "chance": 0.04},  # 绷带
    ],

    # ── 农田 ──
    TREASURE_FARMLAND: [
        {"item_id": 139, "chance": 0.25},  # 干蘑菇
        {"item_id": 141, "chance": 0.15},  # 生肉
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 116, "chance": 0.15},  # 玻璃瓶
        {"item_id": 150, "chance": 0.15},  # 塑料袋
        {"item_id": 114, "chance": 0.12},  # 压缩饼干
        {"item_id": 201, "chance": 0.08},  # 纯净水
        {"item_id": 143, "chance": 0.10},  # 雨水收集瓶
        {"item_id": 105, "chance": 0.10},  # 零件
        {"item_id": 110, "chance": 0.05},  # 工具锤
        {"item_id": 109, "chance": 0.04},  # 水果刀
        {"item_id": 151, "chance": 0.10},  # 胶带
        {"item_id": 152, "chance": 0.08},  # 弹簧
        {"item_id": 153, "chance": 0.06},  # 打火机
    ],

    # ── 沼泽 ──
    TREASURE_SWAMP: [
        {"item_id": 139, "chance": 0.20},  # 干蘑菇
        {"item_id": 141, "chance": 0.12},  # 生肉
        {"item_id": 115, "chance": 0.25},  # 破布
        {"item_id": 116, "chance": 0.20},  # 玻璃瓶
        {"item_id": 150, "chance": 0.20},  # 塑料袋
        {"item_id": 105, "chance": 0.08},  # 零件
        {"item_id": 117, "chance": 0.06},  # 废电池
        {"item_id": 114, "chance": 0.06},  # 压缩饼干
        {"item_id": 201, "chance": 0.04},  # 纯净水
        {"item_id": 143, "chance": 0.06},  # 雨水收集瓶
        {"item_id": 112, "chance": 0.04},  # 抗生素
        {"item_id": 113, "chance": 0.05},  # 绷带
        {"item_id": 146, "chance": 0.04},  # 净水药片
        {"item_id": 153, "chance": 0.04},  # 打火机
    ],

    # ── 沙滩 ──
    TREASURE_BEACH: [
        {"item_id": 116, "chance": 0.30},  # 玻璃瓶
        {"item_id": 150, "chance": 0.25},  # 塑料袋
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 201, "chance": 0.10},  # 纯净水
        {"item_id": 143, "chance": 0.12},  # 雨水收集瓶
        {"item_id": 105, "chance": 0.08},  # 零件
        {"item_id": 117, "chance": 0.06},  # 废电池
        {"item_id": 153, "chance": 0.08},  # 打火机
        {"item_id": 109, "chance": 0.04},  # 水果刀
        {"item_id": 121, "chance": 0.10},  # 人字拖（左）
        {"item_id": 122, "chance": 0.10},  # 人字拖（右）
        {"item_id": 106, "chance": 0.08},  # 破旧白衬衫
        {"item_id": 134, "chance": 0.06},  # 牛仔裤
        {"item_id": 128, "chance": 0.06},  # 雨衣
    ],

    # ── 公路 ──
    TREASURE_ROAD: [
        {"item_id": 105, "chance": 0.25},  # 零件
        {"item_id": 115, "chance": 0.20},  # 破布
        {"item_id": 116, "chance": 0.15},  # 玻璃瓶
        {"item_id": 150, "chance": 0.15},  # 塑料袋
        {"item_id": 117, "chance": 0.15},  # 废电池
        {"item_id": 151, "chance": 0.18},  # 胶带
        {"item_id": 152, "chance": 0.15},  # 弹簧
        {"item_id": 149, "chance": 0.12},  # 铜线
        {"item_id": 153, "chance": 0.10},  # 打火机
        {"item_id": 114, "chance": 0.08},  # 压缩饼干
        {"item_id": 201, "chance": 0.06},  # 纯净水
        {"item_id": 144, "chance": 0.04},  # 瓶装可乐
        {"item_id": 140, "chance": 0.06},  # 能量棒
        {"item_id": 110, "chance": 0.05},  # 工具锤
        {"item_id": 111, "chance": 0.03},  # 撬棍
        {"item_id": 109, "chance": 0.04},  # 水果刀
        {"item_id": 113, "chance": 0.05},  # 绷带
        {"item_id": 146, "chance": 0.04},  # 净水药片
    ],

    # ── 湖泊（湖水事件处理，搜刮只出杂物） ──
    TREASURE_LAKE: [
        {"item_id": 116, "chance": 0.20},  # 玻璃瓶
        {"item_id": 150, "chance": 0.15},  # 塑料袋
        {"item_id": 115, "chance": 0.10},  # 破布
        {"item_id": 143, "chance": 0.08},  # 雨水收集瓶
        {"item_id": 201, "chance": 0.04},  # 纯净水
    ],
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