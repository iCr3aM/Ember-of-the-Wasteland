# =============================================================================
# # 背包后台逻辑（添加、删除、检查物品、装备系统）
# # 定义：背包、容器（纸箱、背包、口袋）与身体装备槽位（左手、右手、头部、躯干等）的空间物理逻辑。
# # 实现：添加/删除物品、检查任务所需物品；装备穿戴/卸下时的属性及状态联动（如穿鞋免疫碎玻璃割伤）。
# =============================================================================
init python:
    class Inventory:
        """背包物理空间与纸娃娃装备插槽复合后台系统"""
        def __init__(self):
            # 身体固定装备槽定义
            self.slots = {
                "head": None,
                "torso": None,
                "legs": None,
                "feet": None,
                "left_hand": None,
                "right_hand": None
            }
            self.backpack_grid = [] # 存储无槽位、存放在包裹网格内的 ItemInstance 实例

        def equip_item(self, item_instance, slot_name):
            """将物品装配到指定槽位，触发联动逻辑"""
            if slot_name in self.slots:
                self.slots[slot_name] = item_instance
                # 触发物品卸下/换装导致的身体防御值或状态变动（在此留空，后续在主属性动态计算中关联）

        def remove_item(self, item_instance):
            """从全局库存中安全剥离某物品"""
            if item_instance in self.backpack_grid:
                self.backpack_grid.remove(item_instance)
                return True
            for slot, inst in self.slots.items():
                if inst == item_instance:
                    self.slots[slot] = None
                    return True
            return False

        def add_item(self, item_instance):
            """添加物品至基础空间网格"""
            self.backpack_grid.append(item_instance)

        def add_item_by_id(self, item_id, durability=None):
            """通过物品 ID 创建并添加一个物品实例。"""
            item_instance = create_item_instance(item_id, durability)
            self.add_item(item_instance)
            return item_instance

        def remove_item_by_id(self, item_id, count=1):
            """从背包中移除指定数量的物品实例。"""
            removed = []
            for item in list(self.backpack_grid):
                if item.id == item_id and len(removed) < count:
                    self.backpack_grid.remove(item)
                    removed.append(item)
            return removed
        
        def safe_remove_item(self, item_instance):
            """安全地从背包中移除物品，不触发迭代器异常"""
            if item_instance in self.backpack_grid:
                # 创建新的列表，排除要移除的物品
                self.backpack_grid = [item for item in self.backpack_grid if item is not item_instance]
                return True
            for slot, inst in self.slots.items():
                if inst == item_instance:
                    self.slots[slot] = None
                    return True
            return False        

        def check_item_count(self, item_id):
            """扫描检索任务及合成所需的物品数量"""
            count = 0
            for item in self.backpack_grid:
                if item.id == item_id: count += 1
            for slot, item in self.slots.items():
                if item and item.id == item_id: count += 1
            return count