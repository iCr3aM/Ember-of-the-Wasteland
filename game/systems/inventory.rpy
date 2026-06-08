# =============================================================================
# inventory.rpy — 背包后台逻辑（固定网格版）
# 功能：定义背包网格数据模型、点击选中/移动/装备/卸下交互逻辑
# 职责：管理全局选中状态、背包与装备槽的增删改查、战斗禁用联动
# =============================================================================
# ── 全局交互状态与背包操作函数 ──
init python:
    # ── 全局选中状态 ──
    _selected_type = None   # "backpack" 或 "equip"
    _selected_id = None     # int（背包网格索引）或 str（装备槽名）
    inventory_action_performed = False  # 战斗中是否执行过背包操作

    def mark_inventory_action_performed():
        """标记本回合已执行背包操作（战斗中禁用玩家行动）"""
        global inventory_action_performed
        inventory_action_performed = True

    def reset_inventory_action_performed():
        """重置背包操作标记（新回合开始时调用）"""
        global inventory_action_performed
        inventory_action_performed = False

    def clear_selection():
        """清除选中高亮状态"""
        global _selected_type, _selected_id
        _selected_type = None
        _selected_id = None

    def click_backpack_slot(idx):
        """处理点击背包内指定格子的逻辑"""
        global _selected_type, _selected_id
        
        # 安全边界检查
        if idx < 0 or idx >= player_inventory.max_slots:
            return
            
        target_slot = player_inventory.backpack_slots[idx]

        if _selected_type == "backpack":
            src_idx = _selected_id
            if src_idx == idx:
                # 再次点击同一背包物品 → 取消选中
                clear_selection()
            elif target_slot is None:
                # 选中物品 → 点击空格子 → 移动过去
                if player_inventory.backpack_slots[src_idx] is not None:
                    player_inventory.backpack_slots[idx] = player_inventory.backpack_slots[src_idx]
                    player_inventory.backpack_slots[src_idx] = None
                clear_selection()
            else:
                # 点击另一个有物品的格子 → 切换选中目标
                _selected_id = idx

        elif _selected_type == "equip":
            src_slot = _selected_id
            if target_slot is None:
                # 装备选中 → 点击背包空格子 → 卸下到该格子
                item = player_inventory.slots.get(src_slot)
                if item:
                    # 同步特殊装备状态
                    if src_slot in ("left_foot", "right_foot"):
                        if player_inventory.is_barefoot():
                            player_stats.add_condition(COND_BARE_FOOT)
                        else:
                            player_stats.remove_condition(COND_BARE_FOOT)
                    
                    if src_slot in ("backpack", "waist"):
                        player_inventory.slots[src_slot] = None
                        new_w, new_h = player_inventory.calculate_backpack_dimensions()
                        new_max = new_w * new_h
                        player_inventory.slots[src_slot] = item

                        if new_max == 0:
                            # 卸下最后一个背包/腰带，没有格子可放 → 丢到地面
                            player_inventory.slots[src_slot] = None
                            current_container = get_current_ground_container()
                            if current_container is not None:
                                current_container.add_item(item)
                                renpy.notify(f"{item.config.name} 已掉落到地上。")
                            else:
                                renpy.notify(f"{item.config.name} 丢失了！")
                            player_inventory.refresh_backpack_grid()
                            clear_selection()
                            return

                        if idx >= new_max:
                            renpy.notify("无法在此位置卸下该装备！")
                            clear_selection()
                            return

                        # 放入格子，清空装备槽，刷新网格
                        player_inventory.backpack_slots[idx] = {"item": item, "stack": 1}
                        player_inventory.slots[src_slot] = None
                        player_inventory.refresh_backpack_grid()
                    else:
                        player_inventory.backpack_slots[idx] = {"item": item, "stack": 1}
                        player_inventory.slots[src_slot] = None
                    
                    if src_slot == "right_hand":
                        player_inventory.update_player_attack_modes()
                    
                    # 战斗中卸下装备则禁用本回合行动
                    if is_in_active_combat():
                        disable_player_turn_in_combat()

                clear_selection()
            else:
                # 装备选中 → 点击有物品的背包格子 → 切换为选中该背包物品
                _selected_type = "backpack"
                _selected_id = idx
                
        else:
            # 无选中 → 点击有物品的格子则选中
            if target_slot is not None:
                _selected_type = "backpack"
                _selected_id = idx

    def click_equip_slot(slot_name):
        """处理点击身体纸娃娃装备槽的逻辑"""
        global _selected_type, _selected_id
        current_item = player_inventory.slots.get(slot_name)

        if _selected_type == "backpack":
            src_idx = _selected_id
            if src_idx is not None and player_inventory.backpack_slots[src_idx] is not None:
                item = player_inventory.backpack_slots[src_idx]["item"]
                
                # 背包选中 → 点击对应装备槽 → 装备
                if slot_name in item.config.equip_slots:
                    if is_in_active_combat():
                        mark_inventory_action_performed()
                    
                    # 先装备新物品，再处理旧物品的卸下
                    old_item = player_inventory.slots[slot_name]
                    
                    # 消耗背包格子内的堆叠
                    player_inventory.backpack_slots[src_idx]["stack"] -= 1
                    if player_inventory.backpack_slots[src_idx]["stack"] <= 0:
                        player_inventory.backpack_slots[src_idx] = None
                    
                    # 先装备新物品
                    player_inventory.slots[slot_name] = item

                    # 如果是背包/腰袋，尝试刷新网格
                    if slot_name in ("backpack", "waist"):
                        if not player_inventory.refresh_backpack_grid():
                            # 刷新失败 → 恢复原状
                            player_inventory.slots[slot_name] = old_item
                            # 把新物品放回背包格子
                            player_inventory.backpack_slots[src_idx] = {"item": item, "stack": 1}
                            renpy.notify("背包内物品太多，无法更换此装备！")
                            clear_selection()
                            return
                    
                    # 再处理旧物品的卸下
                    if old_item is not None:
                        # 尝试将旧物品放入背包空位
                        empty_idx = -1
                        for i in range(player_inventory.max_slots):
                            if player_inventory.backpack_slots[i] is None:
                                empty_idx = i
                                break
                        if empty_idx != -1:
                            # 有空位 → 正常放入
                            player_inventory.backpack_slots[empty_idx] = {"item": old_item, "stack": 1}
                            # 注意：unequip_item 会再次调用 refresh_backpack_grid，但此时新旧背包已交换
                            # 直接手动处理，避免二次刷新
                        else:
                            # 没有空位 → 丢弃到地面
                            current_container = get_current_ground_container()
                            if current_container is not None:
                                current_container.add_item(old_item)
                                renpy.notify(f"背包空间不足，{old_item.config.name} 已掉落到地上。")
                            else:
                                renpy.notify(f"背包空间不足，{old_item.config.name} 丢失了！")
                    
                    if slot_name == "right_hand":
                        player_inventory.update_player_attack_modes()
                    
                    if slot_name in ("left_foot", "right_foot"):
                        if player_inventory.is_barefoot():
                            player_stats.add_condition(COND_BARE_FOOT)
                        else:
                            player_stats.remove_condition(COND_BARE_FOOT)
                    clear_selection()  # 清除选中状态
                else:
                    renpy.notify(f"{item.config.name} 不能装备在该槽位！")

        elif _selected_type == "equip":
            if _selected_id == slot_name:
                # 再次点击同一已装备物品 → 取消选中
                clear_selection()
            else:
                # 切换选中的装备槽
                if current_item is not None:
                    _selected_id = slot_name
                else:
                    clear_selection()
        else:
            # 没有任何选中 -> 直接选中此装备槽内物品
            if current_item is not None:
                _selected_type = "equip"
                _selected_id = slot_name

    def split_item_stack(item, inv_instance, slot_idx):
        """分离堆叠物品：从堆叠中分出1个到最近的空格子"""
        # 安全边界检查
        if slot_idx < 0 or slot_idx >= inv_instance.max_slots:
            return
        slot = inv_instance.backpack_slots[slot_idx]
        if slot is None or slot["stack"] <= 1:
            return
        
        # 找空格子
        for i in range(inv_instance.max_slots):
            if inv_instance.backpack_slots[i] is None:
                # 当前格子减1
                inv_instance.backpack_slots[slot_idx]["stack"] -= 1
                # 新格子放1个
                inv_instance.backpack_slots[i] = {"item": item, "stack": 1}
                renpy.notify(f"已分离出1个{item.config.name}")
                return
        
        renpy.notify("背包已满，无法分离！")

    def merge_item_stack(inv_instance, src_idx, dst_idx):
        """合并堆叠物品：将源格子的物品合并到目标格子"""
        # 安全边界检查
        if src_idx < 0 or src_idx >= inv_instance.max_slots:
            return
        if dst_idx < 0 or dst_idx >= inv_instance.max_slots:
            return
        src = inv_instance.backpack_slots[src_idx]
        dst = inv_instance.backpack_slots[dst_idx]
        if src is None or dst is None:
            return
        if src["item"].id != dst["item"].id:
            return
        
        max_stack = src["item"].config.max_stack
        space = max_stack - dst["stack"]
        if space <= 0:
            renpy.notify("目标格子已满，无法合并！")
            return
        
        move_count = min(src["stack"], space)
        dst["stack"] += move_count
        src["stack"] -= move_count
        if src["stack"] <= 0:
            inv_instance.backpack_slots[src_idx] = None
        
        renpy.notify(f"已合并{move_count}个物品")

    # ── 背包网格数据模型 ──
    class Inventory:
        def __init__(self, max_slots=0):
            self.slots = {
                "hat": None, "neck": None, "torso": None,
                "left_hand": None, "left_wrist": None,
                "right_hand": None, "right_wrist": None,
                "legs": None, "left_foot": None,
                "right_foot": None, "left_ankle": None, "right_ankle": None,
                "backpack": None, "waist": None,
            }
            self.default_backpack_grid = (0, 0)
            self.backpack_width, self.backpack_height = self.default_backpack_grid
            self.max_slots = max_slots
            self.backpack_slots = [None] * self.max_slots

        def is_barefoot(self):
            """只要有一只脚没穿鞋就算赤脚"""
            left_shod = self.slots.get("left_foot") is not None
            right_shod = self.slots.get("right_foot") is not None
            return not (left_shod and right_shod)

        def calculate_backpack_dimensions(self):
            backpack_item = self.slots.get("backpack")
            waist_item = self.slots.get("waist")

            if backpack_item is None and waist_item is None:
                return (0, 0)

            total_slots = 0
            widths = []

            if backpack_item is not None:
                bh, bw = backpack_item.config.grid_size
                total_slots += bw * bh
                widths.append(bw)

            if waist_item is not None:
                wh, ww = waist_item.config.grid_size
                total_slots += ww * wh
                widths.append(ww)

            MAX_GRID_WIDTH = 6    # 宽最大为6
            MAX_GRID_HEIGHT = 5   # 长最大为5

            grid_width = min(max(widths), MAX_GRID_WIDTH)
            grid_height = (total_slots + grid_width - 1) // grid_width
            grid_height = min(grid_height, MAX_GRID_HEIGHT)
            return grid_width, grid_height

        def refresh_backpack_grid(self):
            """装备/卸下背包或腰袋后刷新背包格子数量和宽高。"""
            new_width, new_height = self.calculate_backpack_dimensions()
            new_max_slots = new_width * new_height

            if new_max_slots == self.max_slots:
                self.backpack_width, self.backpack_height = new_width, new_height
                return True

            if new_max_slots < self.max_slots:
                if any(slot is not None for slot in self.backpack_slots[new_max_slots:]):
                    renpy.notify("当前背包内物品太多，无法卸下该装备。")
                    return False
                self.backpack_slots = self.backpack_slots[:new_max_slots]
            else:
                self.backpack_slots.extend([None] * (new_max_slots - self.max_slots))

            self.max_slots = new_max_slots
            self.backpack_width, self.backpack_height = new_width, new_height
            return True

        def add_item(self, item_instance):
            """往背包网格添加一件物品（完美兼容固定长度的 20/60 槽位）"""
            max_stack = item_instance.config.max_stack
            
            # 可堆叠物品（max_stack > 1）→ 先找未满的同类格子
            if max_stack > 1:
                for slot in self.backpack_slots:
                    if slot is not None and slot["item"].id == item_instance.id:
                        if slot["stack"] < max_stack:
                            slot["stack"] += 1
                            return True
            
            # 寻找列表中第一个真正的 None 空位
            for i in range(len(self.backpack_slots)):
                if self.backpack_slots[i] is None:
                    self.backpack_slots[i] = {"item": item_instance, "stack": 1}
                    return True
            
            # 兜底：列表长度意外小于 max_slots 且无 None 时才 append
            if len(self.backpack_slots) < self.max_slots:
                self.backpack_slots.append({"item": item_instance, "stack": 1})
                return True
                
            return False

        def remove_item(self, item_instance):
            """全面移除：搜寻特定网格格子或装备槽"""
            for i in range(self.max_slots):
                slot = self.backpack_slots[i]
                if slot is not None and slot["item"] is item_instance:
                    slot["stack"] -= 1
                    if slot["stack"] <= 0:
                        self.backpack_slots[i] = None
                    return True
            for slot_name, inst in list(self.slots.items()):
                if inst is item_instance:
                    self.slots[slot_name] = None
                    return True
            return False

        def remove_one_random_item(self):
            """随机移除一个背包物品（堆叠减1，归零则清空格子）"""
            indices = [i for i, slot in enumerate(self.backpack_slots) if slot is not None]
            if not indices:
                return False
            idx = renpy.random.choice(indices)
            slot = self.backpack_slots[idx]
            slot["stack"] -= 1
            if slot["stack"] <= 0:
                self.backpack_slots[idx] = None
            return True

        def add_item_by_id(self, item_id, durability=None):
            """通过物品 ID 创建并添加一个物品实例（支持堆叠）。"""
            item_instance = create_item_instance(item_id, durability)
            self.add_item(item_instance)
            return item_instance

        def check_item_count(self, item_id):
            """统计指定物品的总堆叠数量（背包 + 装备槽）。"""
            count = 0
            for slot in self.backpack_slots:
                if slot is not None and slot["item"].id == item_id:
                    count += slot["stack"]
            for slot_name, item in self.slots.items():
                if item and item.id == item_id:
                    count += 1
            return count

        @property
        def backpack_grid(self):
            """扁平化返回所有物品实例列表（兼容旧代码）。"""
            result = []
            for slot in self.backpack_slots:
                if slot is not None:
                    for _ in range(slot["stack"]):
                        result.append(slot["item"])
            return result

        def unequip_item(self, slot_name):
            item = self.slots[slot_name]
            if item is None:
                return

            if slot_name in ("backpack", "waist"):
                self.slots[slot_name] = None
                new_w, new_h = self.calculate_backpack_dimensions()
                new_max = new_w * new_h
                self.slots[slot_name] = item

                if new_max == 0:
                    # 卸下最后一个背包/腰带，没有格子可放 → 丢到地面
                    self.slots[slot_name] = None
                    current_container = get_current_ground_container()
                    if current_container is not None:
                        current_container.add_item(item)
                        renpy.notify(f"{item.config.name} 已掉落到地上。")
                    else:
                        renpy.notify(f"{item.config.name} 丢失了！")
                    self.refresh_backpack_grid()
                    return

                empty_idx = -1
                for i in range(new_max):
                    if self.backpack_slots[i] is None:
                        empty_idx = i
                        break
                if empty_idx == -1:
                    renpy.notify("背包没有足够的空位，无法卸下该装备！")
                    return

                # 放入空位，清空装备槽，刷新网格
                self.backpack_slots[empty_idx] = {"item": item, "stack": 1}
                self.slots[slot_name] = None
                self.refresh_backpack_grid()
            else:
                # 非背包/腰带装备：在旧尺寸范围内找空位
                empty_idx = -1
                for i in range(self.max_slots):
                    if self.backpack_slots[i] is None:
                        empty_idx = i
                        break
                if empty_idx != -1:
                    self.backpack_slots[empty_idx] = {"item": item, "stack": 1}
                    self.slots[slot_name] = None
                else:
                    renpy.notify("背包没有足够的空位，无法卸下装备！")

        def update_player_attack_modes(self):
            """根据当前装备的武器更新玩家的攻击模式列表"""
            base_modes = [1, 4]
            weapon_item = self.slots.get("right_hand")
            if weapon_item and weapon_item.id in WEAPON_ATTACK_MAP:
                base_modes.extend(WEAPON_ATTACK_MAP[weapon_item.id])
            player_stats.attack_mode_ids = list(set(base_modes))