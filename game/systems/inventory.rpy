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

            self.backpack_slots = []  # 每个元素: {"item": ItemInstance, "stack": int}
            self.max_slots = 20       # 5×5 = 20 格

        STACKABLE_ITEMS = {103, 112, 113, 114, 201, 104, 105, 115, 116, 117}  # 消耗品/垃圾

        def add_item(self, item_instance, count=1):
            """添加物品（支持堆叠）
            如果 item_instance 是可堆叠物品，尝试合并到已有堆叠槽；
            否则创建新槽位。
            返回 True 成功，False 背包已满。
            """
            # 检查是否可堆叠
            if item_instance.id in self.STACKABLE_ITEMS:
                for slot in self.backpack_slots:
                    if slot["item"].id == item_instance.id and slot["stack"] < 10:
                        add_count = min(count, 10 - slot["stack"])
                        slot["stack"] += add_count
                        count -= add_count
                        if count <= 0:
                            return True

            # 需要新槽位
            while count > 0:
                if len(self.backpack_slots) >= self.max_slots:
                    return False  # 背包已满
                add_count = min(count, 10)
                # 创建新的物品实例（避免引用同一个实例）
                new_item = create_item_instance(item_instance.id)
                self.backpack_slots.append({"item": new_item, "stack": add_count})
                count -= add_count
            return True

        # ──────── 统一的 add_item_by_id 方法 ────────
        def add_item_by_id(self, item_id, durability=None):
            """通过物品 ID 创建并添加一个物品实例（支持堆叠）。"""
            item_instance = create_item_instance(item_id, durability)
            self.add_item(item_instance)
            return item_instance

        # ──────── 统一的 equip_item 方法 ────────
        def equip_item(self, item_instance, slot_name):
            """将物品装配到指定槽位，触发联动逻辑"""
            if slot_name in self.slots:
                self.slots[slot_name] = item_instance
                # 触发物品卸下/换装导致的身体防御值或状态变动（在此留空，后续在主属性动态计算中关联）

        # ──────── 统一的 remove_item 方法 ────────
        def remove_item(self, item_instance):
            """
            移除物品（减少堆叠计数）。
            如果堆叠减少到 0，移除该槽位。
            """
            # 检查背包槽位
            for slot in list(self.backpack_slots):  # 使用 list() 副本以便安全删除
                if slot["item"] is item_instance:
                    slot["stack"] -= 1
                    if slot["stack"] <= 0:
                        self.backpack_slots.remove(slot)
                    return True

            # 检查装备槽
            for slot_name, inst in list(self.slots.items()):
                if inst is item_instance:
                    self.slots[slot_name] = None
                    return True
            return False

        # ──────── 统一的 remove_item_by_id 方法 ────────
        def remove_item_by_id(self, item_id, count=1):
            """从背包中移除指定数量的物品（减少堆叠计数）。"""
            removed = []
            for slot in list(self.backpack_slots):
                if slot["item"].id == item_id and len(removed) < count:
                    # 从该槽位移除
                    remove_count = min(count - len(removed), slot["stack"])
                    slot["stack"] -= remove_count
                    for _ in range(remove_count):
                        removed.append(slot["item"])
                    if slot["stack"] <= 0:
                        self.backpack_slots.remove(slot)
                    if len(removed) >= count:
                        break
            return removed

        # ──────── 统一的 check_item_count 方法 ────────
        def check_item_count(self, item_id):
            """统计指定物品的总堆叠数量（背包 + 装备槽）。"""
            count = 0
            for slot in self.backpack_slots:
                if slot["item"].id == item_id:
                    count += slot["stack"]
            for slot, item in self.slots.items():
                if item and item.id == item_id:
                    count += 1
            return count

        # ──────── 向后兼容属性：backpack_grid ────────
        @property
        def backpack_grid(self):
            """
            扁平化返回所有物品实例的列表（每个堆叠展开多次）。
            用于兼容旧代码（如 UI 渲染、脚本中的迭代）。
            """
            result = []
            for slot in self.backpack_slots:
                for _ in range(slot["stack"]):
                    result.append(slot["item"])
            return result

        # ──────── 卸下指定装备槽的物品，将其放回背包 ────────
        def unequip_item(self, slot_name, notify_on_fail=True):
            """
            卸下指定装备槽的物品，将其放回背包。
            如果背包已满，则取消卸下。
            返回 True 表示成功，False 表示失败。
            """
            item = self.slots.get(slot_name)
            if item is None:
                return False
            
            # 放回背包
            success = self.add_item(item)
            if not success:
                if notify_on_fail:
                    renpy.notify("背包已满，无法卸下装备！")
                return False
            
            # 清空装备槽
            self.slots[slot_name] = None
            return True 

        def move_to_equip(self, item_instance, slot_name):
            """从背包中移除物品并装备到指定槽位。如果装备槽已有物品，先卸下。"""
            # 如果目标槽位已有物品，先卸下到背包
            if self.slots[slot_name] is not None:
                self.unequip_item(slot_name)  # 放回背包

            # 从背包中移除物品
            for slot in list(self.backpack_slots):
                if slot["item"] is item_instance:
                    slot["stack"] -= 1
                    if slot["stack"] <= 0:
                        self.backpack_slots.remove(slot)
                    break
            
            # 装备到槽位
            self.slots[slot_name] = item_instance