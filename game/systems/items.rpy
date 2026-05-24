# =============================================================================
# # 物品、武器、装备、药品、垃圾数据库
# # 定义：静态物品原型数据库（`ITEMS_DB`，含重量、基础价值、最大耐久、每小时腐烂率、装备槽位要求）。
# # 实现：生成具体的物品实例（`ItemInstance`），支持物品因时间流逝而腐烂变质（如肉块变质）、因使用而磨损（如衣服变烂）。
# =============================================================================
init python:
    class ItemType:
        """对应 itemtypes.xml 的静态数据类"""
        def __init__(self, id, name, weight, value, max_durability=1.0, degrade_per_hour=0.0, equip_slots=None):
            self.id = id
            self.name = name
            self.weight = weight
            self.value = value
            self.max_durability = max_durability
            self.degrade_per_hour = degrade_per_hour
            self.equip_slots = equip_slots or [] # 可装备的身体槽位编号

# 将 degrade 方法移入 ItemInstance 类，以便每个物品实例独立管理自己的耐久度。
init python:
    class ItemInstance:
        """在背包及大地图世界中真实流转的动态实例"""
        def __init__(self, item_id, durability=1.0):
            self.id = item_id
            self.config = ITEMS_DB[item_id]
            self.durability = durability # 0.0 - 1.0 独立耐久度

        @property
        def icon_path(self):
            # 通过全局解耦工具动态获取 game/images/ 内部图标路径
            return get_item_icon_path(self.id)

        def degrade(self, hours=1.0):
            """耐久度因磨损或时间流逝产生降级"""
            if self.config.degrade_per_hour > 0:
                self.durability -= self.config.degrade_per_hour * hours
                if self.durability < 0:
                    self.durability = 0.0

    def create_item_instance(item_id, durability=None):
        """工厂函数：基于 item_id 生成动态物品实例。"""
        if item_id not in ITEMS_DB:
            raise KeyError(f"Unknown item_id: {item_id}")
        default_durability = ITEMS_DB[item_id].max_durability
        return ItemInstance(item_id, durability if durability is not None else default_durability)

# =============================================================================
# 物品用途数据库：定义哪些物品可以直接从背包"使用"
# =============================================================================
init python:
    # 用途效果处理函数
    def use_purified_water(actor):
        """使用纯净水：-50 口渴值"""
        actor.thirst = max(0.0, actor.thirst - 50.0)
        update_thirst_condition(actor)
        renpy.notify("口渴值减少了 50 点")
        return True

    def use_compressed_biscuit(actor):
        """使用压缩饼干：-30 饥饿值"""
        actor.hunger = max(0.0, actor.hunger - 30.0)
        renpy.notify("饥饿值减少了 30 点")
        return True

    def use_antibiotic(actor):
        """使用抗生素：去除中毒状态"""
        removed = remove_condition_by_id(actor, COND_POISON)
        if removed:
            renpy.notify("抗生素生效，中毒状态已解除！")
        else:
            renpy.notify("你并未中毒。")
        return removed  # 即使没中毒也返回 True 以消耗物品（可选）

    def use_bandage(actor):
        """使用绷带：去除流血状态"""
        removed = remove_condition_by_id(actor, COND_BLEED)
        if removed:
            renpy.notify("伤口已被包扎，流血止住了。")
        else:
            renpy.notify("你并没有流血。")
        return removed

    def use_first_aid_kit(actor):
        """使用急救包：恢复 30 HP"""
        actor.hp = min(actor.max_hp, actor.hp + 30.0)
        renpy.notify(f"你的生命值恢复了 30 点（当前 {int(actor.hp)}/{int(actor.max_hp)}）")
        return True

    # 物品用途映射表：item_id -> (use_label_or_none, effect_function_or_none)
    # 如果 use_function 不为 None，则可以在背包界面点击"使用"
    ITEM_USE_FUNCTIONS = {
        201: use_purified_water,   # 纯净水 - 减少口渴值
        114: use_compressed_biscuit, # 压缩饼干 - 减少饥饿值
        112: use_antibiotic,       # 抗生素 - 去除中毒
        113: use_bandage,          # 绷带 - 止血（去流血）
        103: use_first_aid_kit,    # 急救包 - 恢复生命
        # 后续可以添加更多：
        # 103: use_first_aid_kit,  # 急救包
    }

init python:
    def use_item_from_inventory(item_instance, actor=None):
        """
        通用物品使用函数。只执行物品的用途效果，不操作 UI。
        返回 (success, item_instance) 元组。
        """
        item_id = item_instance.id
        
        if item_id not in ITEM_USE_FUNCTIONS:
            return (False, item_instance)
        
        # 执行用途效果
        use_function = ITEM_USE_FUNCTIONS[item_id]
        if actor is None:
            # 如果未传入 actor，尝试获取全局 player_stats
            try:
                actor = player_stats
            except NameError:
                return (False, item_instance)
        success = use_function(player_stats)
        
        return (success, item_instance)

init python:
    def use_item_and_refresh_screen(item_instance, inv_instance, actor=None):
        """使用物品、移除、通知。"""
        success, item = use_item_from_inventory(item_instance, actor=actor)
        if success:
            inv_instance.remove_item(item)
            renpy.notify(f"使用了 {item.config.name} ×1")
        else:
            renpy.notify(f"{item.config.name} 无法直接使用。")

    def get_item_icon_path(item_id):
        """
        返回物品 ID 对应的图标路径。
        如果图标文件不存在，返回默认占位图。
        图标文件命名规则：icon_{item_id}.png
        """
        import os
        # 构造图标文件路径
        icon_filename = f"icon_{item_id}.png"
        icon_path = f"images/{icon_filename}"
        
        # 检查文件是否存在（在 Ren'Py 中，文件路径相对于 game/ 目录）
        # 使用 renpy.loadable() 检查资源文件是否存在
        if renpy.loadable(icon_path):
            return icon_path
        else:
            # 如果没有对应图标，返回一个默认的占位图
            # 或者直接返回 None（UI 中处理缺失图标的情况）
            return None

# =============================================================================
# 初始化基础 ITEM 类型数据表
# =============================================================================
init python:
    ITEMS_DB[101] = ItemType(
        101,
        "破旧头盔",
        weight=1.2,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["head"]
    )

    ITEMS_DB[102] = ItemType(
        102,
        "破旧军靴",
        weight=1.2,
        value=8.0,
        max_durability=0.8,
        degrade_per_hour=0.0,
        equip_slots=["feet"]
    )

    ITEMS_DB[103] = ItemType(
        103,
        "急救包",
        weight=1.0,
        value=15.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[104] = ItemType(
        104,
        "手枪弹匣",
        weight=0.3,
        value=12.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[105] = ItemType(
        105,
        "零件",
        weight=0.8,
        value=4.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[106] = ItemType(
        106,
        "破旧的白衬衫",
        weight=0.3,
        value=2.0,
        max_durability=0.6,
        degrade_per_hour=0.0,
        equip_slots=["torso"]
    )

    ITEMS_DB[107] = ItemType(
        107,
        "破旧的工装裤",
        weight=0.6,
        value=3.0,
        max_durability=0.7,
        degrade_per_hour=0.0,
        equip_slots=["legs"]
    )

    ITEMS_DB[108] = ItemType(
        108,
        "肮脏的运动鞋",
        weight=0.9,
        value=2.0,
        max_durability=0.5,
        degrade_per_hour=0.0,
        equip_slots=["feet"]
    )

    ITEMS_DB[109] = ItemType(
        109,
        "水果刀",
        weight=0.3,
        value=3.0,
        max_durability=0.6,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[110] = ItemType(
        110,
        "工具锤",
        weight=1.5,
        value=8.0,
        max_durability=0.9,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[111] = ItemType(
        111,
        "撬棍",
        weight=2.0,
        value=10.0,
        max_durability=0.95,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[112] = ItemType(
        112,
        "抗生素",
        weight=0.1,
        value=20.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[113] = ItemType(
        113,
        "绷带",
        weight=0.1,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[114] = ItemType(
        114,
        "压缩饼干",
        weight=0.2,
        value=6.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[115] = ItemType(
        115,
        "破布",
        weight=0.2,
        value=1.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[116] = ItemType(
        116,
        "玻璃瓶",
        weight=0.4,
        value=1.5,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[117] = ItemType(
        117,
        "废电池",
        weight=0.3,
        value=2.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[201] = ItemType(
        201,
        "纯净水",
        weight=0.5,
        value=5.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )