# =============================================================================
# inventory.rpy - grid inventory backend
# =============================================================================
init python:
    INVENTORY_AREA_MAIN = "main"
    INVENTORY_AREA_BACKPACK = "backpack"
    INVENTORY_AREA_WAIST = "waist"

    PLAYER_BACKPACK_MAX_COLS = 5
    PLAYER_BACKPACK_MAX_ROWS = 6
    PLAYER_WAIST_MAX_COLS = 5
    PLAYER_WAIST_MAX_ROWS = 1

    class Inventory:
        def __init__(self, max_slots=0, grid_cols=None, grid_rows=None):
            self.slots = {
                "hat": None, "neck": None, "torso": None,
                "left_hand": None, "left_wrist": None,
                "right_hand": None, "right_wrist": None,
                "legs": None, "left_foot": None,
                "right_foot": None, "left_ankle": None, "right_ankle": None,
                "backpack": None, "waist": None,
            }
            self.max_slots = max_slots
            self.backpack_slots = [None] * self.max_slots
            self.default_storage_area = INVENTORY_AREA_MAIN
            self.grid_storage_mode = "grid"
            self.grid_areas = {}

            if grid_cols is None or grid_rows is None:
                guessed_cols, guessed_rows = self._guess_grid_dimensions(self.max_slots)
                if grid_cols is None:
                    grid_cols = guessed_cols
                if grid_rows is None:
                    grid_rows = guessed_rows

            self._set_grid_area(INVENTORY_AREA_MAIN, grid_cols or 0, grid_rows or 0)
            self._refresh_grid_aliases()

        def _guess_grid_dimensions(self, cell_count):
            if cell_count <= 0:
                return (0, 0)

            cols = int(cell_count ** 0.5)
            if cols <= 0:
                cols = 1

            while cols > 1 and (cell_count % cols) != 0:
                cols -= 1

            rows = (cell_count + cols - 1) // cols
            return cols, rows

        def _set_grid_area(self, area, cols, rows):
            cols = max(int(cols or 0), 0)
            rows = max(int(rows or 0), 0)
            self.grid_areas[area] = {
                "cols": cols,
                "rows": rows,
                "cells": [None] * (cols * rows),
                "items": {},
            }

        def _copy_grid_areas(self):
            copied = {}
            for area, data in self.grid_areas.items():
                copied[area] = {
                    "cols": data["cols"],
                    "rows": data["rows"],
                    "cells": list(data["cells"]),
                    "items": dict((item, dict(entry)) for item, entry in data["items"].items()),
                }
            return copied

        def _restore_grid_areas(self, areas):
            self.grid_areas = areas
            self._refresh_grid_aliases()

        def _normalize_area(self, area=None):
            if area is not None:
                return area
            if not getattr(self, "default_storage_area", None):
                self.default_storage_area = INVENTORY_AREA_MAIN
            return self.default_storage_area

        def _is_split_player_storage(self):
            return (
                INVENTORY_AREA_BACKPACK in self.grid_areas
                or INVENTORY_AREA_WAIST in self.grid_areas
            )

        def _area_order(self):
            result = []
            for area in (INVENTORY_AREA_BACKPACK, INVENTORY_AREA_WAIST, INVENTORY_AREA_MAIN):
                if area in self.grid_areas:
                    result.append(area)
            for area in self.grid_areas.keys():
                if area not in result:
                    result.append(area)
            return result

        def _search_areas(self, area=None):
            if area is not None:
                return [area]
            if self._is_split_player_storage():
                return [
                    area for area in (INVENTORY_AREA_BACKPACK, INVENTORY_AREA_WAIST)
                    if area in self.grid_areas
                ]
            return [self._normalize_area()]

        def _refresh_grid_aliases(self):
            if not hasattr(self, "grid_areas") or not self.grid_areas:
                self.grid_areas = {}
                self._set_grid_area(INVENTORY_AREA_MAIN, 0, 0)

            if self.default_storage_area not in self.grid_areas:
                if INVENTORY_AREA_BACKPACK in self.grid_areas:
                    self.default_storage_area = INVENTORY_AREA_BACKPACK
                elif INVENTORY_AREA_MAIN in self.grid_areas:
                    self.default_storage_area = INVENTORY_AREA_MAIN
                else:
                    self.default_storage_area = next(iter(self.grid_areas.keys()))

            current = self.grid_areas[self.default_storage_area]
            self.grid_cols = current["cols"]
            self.grid_rows = current["rows"]
            self.grid_cells = current["cells"]

            aggregate = {}
            for area in self._area_order():
                for item, entry in self.grid_areas[area]["items"].items():
                    entry["area"] = area
                    aggregate[item] = entry
            self.grid_items = aggregate
            self.max_slots = sum(data["cols"] * data["rows"] for data in self.grid_areas.values())

        def _ensure_grid_state(self):
            if not hasattr(self, "slots"):
                self.slots = {}
            if not hasattr(self, "backpack_slots"):
                self.backpack_slots = [None] * getattr(self, "max_slots", 0)
            if not hasattr(self, "grid_storage_mode"):
                self.grid_storage_mode = "grid"
            if not hasattr(self, "default_storage_area"):
                self.default_storage_area = INVENTORY_AREA_MAIN

            if not hasattr(self, "grid_areas") or not self.grid_areas:
                cols = getattr(self, "grid_cols", 0)
                rows = getattr(self, "grid_rows", 0)
                if cols == 0 and rows == 0 and getattr(self, "max_slots", 0) > 0:
                    cols, rows = self._guess_grid_dimensions(self.max_slots)
                self.grid_areas = {}
                self._set_grid_area(self.default_storage_area, cols, rows)

            for area, data in self.grid_areas.items():
                expected_cells = max(data["cols"] * data["rows"], 0)
                if len(data["cells"]) != expected_cells:
                    data["cells"] = [None] * expected_cells
                for item, entry in data["items"].items():
                    entry["area"] = area

            self._refresh_grid_aliases()

        def _init_grid_storage(self):
            self._ensure_grid_state()
            self._set_grid_area(self.default_storage_area, self.grid_cols, self.grid_rows)
            self._refresh_grid_aliases()

        def configure_grid(self, cols, rows, preserve_items=True, area=None):
            self._ensure_grid_state()
            target_area = self._normalize_area(area)
            old_areas = self._copy_grid_areas()
            old_entries = []

            if preserve_items and target_area in self.grid_areas:
                old_entries = sorted(
                    [dict(entry) for entry in self.grid_areas[target_area]["items"].values()],
                    key=lambda entry: (entry["row"], entry["col"], entry["item"].id)
                )

            self._set_grid_area(target_area, cols, rows)
            self._refresh_grid_aliases()

            if preserve_items:
                for entry in old_entries:
                    if not self.place_item_at(entry["item"], entry["col"], entry["row"], stack=entry["stack"], area=target_area):
                        anchor = self.find_space_for_item(entry["item"], area=target_area)
                        if anchor is None:
                            self._restore_grid_areas(old_areas)
                            self.sync_legacy_slots_from_grid()
                            return False
                        if not self.place_item_at(entry["item"], anchor[0], anchor[1], stack=entry["stack"], area=target_area):
                            self._restore_grid_areas(old_areas)
                            self.sync_legacy_slots_from_grid()
                            return False

            self.sync_legacy_slots_from_grid()
            return True

        def configure_storage_areas(self, area_sizes, preserve_items=True):
            self._ensure_grid_state()
            old_areas = self._copy_grid_areas()
            old_entries = []

            if preserve_items:
                old_entries = sorted(
                    [dict(entry) for entry in self.grid_items.values()],
                    key=lambda entry: (self._area_order().index(entry.get("area", self.default_storage_area)) if entry.get("area", self.default_storage_area) in self._area_order() else 99, entry["row"], entry["col"], entry["item"].id)
                )

            self.grid_areas = {}
            for area, size in area_sizes.items():
                self._set_grid_area(area, size[0], size[1])
            self.default_storage_area = INVENTORY_AREA_BACKPACK if INVENTORY_AREA_BACKPACK in self.grid_areas else next(iter(self.grid_areas.keys()), INVENTORY_AREA_MAIN)
            self._refresh_grid_aliases()

            if preserve_items:
                for entry in old_entries:
                    preferred_area = entry.get("area", self.default_storage_area)
                    anchor = None
                    if preferred_area in self.grid_areas:
                        anchor = self.find_space_for_item(entry["item"], area=preferred_area, return_area=True)
                    if anchor is None:
                        anchor = self.find_space_for_item(entry["item"], return_area=True)
                    if anchor is None:
                        self._restore_grid_areas(old_areas)
                        self.sync_legacy_slots_from_grid()
                        return False
                    if not self.place_item_at(entry["item"], anchor[1], anchor[2], stack=entry["stack"], area=anchor[0]):
                        self._restore_grid_areas(old_areas)
                        self.sync_legacy_slots_from_grid()
                        return False

            self.sync_legacy_slots_from_grid()
            return True

        def get_grid_size(self, area=None):
            self._ensure_grid_state()
            area = self._normalize_area(area)
            data = self.grid_areas.get(area)
            if data is None:
                return (0, 0)
            return data["cols"], data["rows"]

        def get_grid_capacity(self, area=None, all_areas=False):
            self._ensure_grid_state()
            if all_areas:
                return sum(data["cols"] * data["rows"] for data in self.grid_areas.values())
            cols, rows = self.get_grid_size(area)
            return cols * rows

        def get_grid_index(self, col, row, area=None):
            self._ensure_grid_state()
            area = self._normalize_area(area)
            data = self.grid_areas.get(area)
            if data is None:
                return None
            if col < 0 or row < 0 or col >= data["cols"] or row >= data["rows"]:
                return None
            return row * data["cols"] + col

        def is_valid_grid_position(self, col, row, area=None):
            return self.get_grid_index(col, row, area=area) is not None

        def iter_grid_positions(self, area=None):
            self._ensure_grid_state()
            for area_name in self._search_areas(area):
                cols, rows = self.get_grid_size(area_name)
                for row in range(rows):
                    for col in range(cols):
                        yield area_name, col, row

        def iter_grid_items(self, area=None):
            self._ensure_grid_state()
            if area is not None:
                data = self.grid_areas.get(area)
                if data is None:
                    return []
                return list(data["items"].items())
            return list(self.grid_items.items())

        def get_item_footprint(self, item_instance):
            config = getattr(item_instance, "config", None)
            if config is None:
                return (1, 1)

            grid_w = getattr(config, "grid_w", None)
            grid_h = getattr(config, "grid_h", None)
            if grid_w is not None and grid_h is not None:
                return max(int(grid_w), 1), max(int(grid_h), 1)

            legacy_size = getattr(config, "grid_size", (1, 1))
            if isinstance(legacy_size, (list, tuple)) and len(legacy_size) >= 2:
                return max(int(legacy_size[0]), 1), max(int(legacy_size[1]), 1)

            return (1, 1)

        def get_item_anchor(self, item_instance):
            self._ensure_grid_state()
            return self.grid_items.get(item_instance)

        def get_item_at(self, col, row, area=None):
            self._ensure_grid_state()
            area = self._normalize_area(area)
            data = self.grid_areas.get(area)
            if data is None:
                return None
            idx = self.get_grid_index(col, row, area=area)
            if idx is None:
                return None
            return data["cells"][idx]

        def _erase_item_from_grid(self, item_instance):
            self._ensure_grid_state()
            entry = self.grid_items.get(item_instance)
            if entry is None:
                return None

            area = entry.get("area", self.default_storage_area)
            data = self.grid_areas.get(area)
            if data is None:
                return None

            data["items"].pop(item_instance, None)
            grid_w, grid_h = self.get_item_footprint(item_instance)
            for row in range(entry["row"], entry["row"] + grid_h):
                for col in range(entry["col"], entry["col"] + grid_w):
                    idx = self.get_grid_index(col, row, area=area)
                    if idx is not None and data["cells"][idx] is item_instance:
                        data["cells"][idx] = None

            self._refresh_grid_aliases()
            return entry

        def can_place_item_at(self, item_instance, col, row, area=None):
            self._ensure_grid_state()
            area = self._normalize_area(area)
            data = self.grid_areas.get(area)
            if data is None:
                return False

            grid_w, grid_h = self.get_item_footprint(item_instance)
            if grid_w <= 0 or grid_h <= 0:
                return False
            if self.get_grid_index(col, row, area=area) is None:
                return False
            if (col + grid_w) > data["cols"] or (row + grid_h) > data["rows"]:
                return False

            for current_row in range(row, row + grid_h):
                for current_col in range(col, col + grid_w):
                    occupied = self.get_item_at(current_col, current_row, area=area)
                    if occupied is not None and occupied is not item_instance:
                        return False
            return True

        def find_space_for_item(self, item_instance, area=None, return_area=False):
            self._ensure_grid_state()
            grid_w, grid_h = self.get_item_footprint(item_instance)

            for area_name in self._search_areas(area):
                data = self.grid_areas.get(area_name)
                if data is None or grid_w > data["cols"] or grid_h > data["rows"]:
                    continue

                max_col = data["cols"] - grid_w
                max_row = data["rows"] - grid_h
                for row in range(max_row + 1):
                    for col in range(max_col + 1):
                        if self.can_place_item_at(item_instance, col, row, area=area_name):
                            if return_area:
                                return (area_name, col, row)
                            return (col, row)
            return None

        def place_item_at(self, item_instance, col, row, allow_swap=False, stack=1, allow_repack=False, area=None):
            self._ensure_grid_state()
            requested_area = area
            target_area = self._normalize_area(area)

            if not self.can_place_item_at(item_instance, col, row, area=target_area):
                if not allow_repack:
                    return False
                anchor = self.find_space_for_item(item_instance, area=requested_area, return_area=True)
                if anchor is None:
                    return False
                target_area, col, row = anchor

            self._erase_item_from_grid(item_instance)
            data = self.grid_areas.get(target_area)
            if data is None:
                return False

            grid_w, grid_h = self.get_item_footprint(item_instance)
            for current_row in range(row, row + grid_h):
                for current_col in range(col, col + grid_w):
                    idx = self.get_grid_index(current_col, current_row, area=target_area)
                    if idx is None:
                        return False
                    data["cells"][idx] = item_instance

            data["items"][item_instance] = {
                "item": item_instance,
                "stack": max(int(stack), 1),
                "col": col,
                "row": row,
                "area": target_area,
            }
            self._refresh_grid_aliases()
            self.sync_legacy_slots_from_grid()
            return True

        def remove_item_at(self, col, row, area=None):
            self._ensure_grid_state()
            item_instance = self.get_item_at(col, row, area=area)
            if item_instance is None:
                return None
            self._erase_item_from_grid(item_instance)
            self.sync_legacy_slots_from_grid()
            return item_instance

        def move_item_within_grid(self, from_col, from_row, to_col, to_row, allow_swap=False, from_area=None, to_area=None):
            self._ensure_grid_state()
            source_area = self._normalize_area(from_area)
            target_area = self._normalize_area(to_area if to_area is not None else source_area)
            item_instance = self.get_item_at(from_col, from_row, area=source_area)
            if item_instance is None:
                return False

            entry = self.grid_items.get(item_instance)
            if entry is None:
                return False

            old_col, old_row = entry["col"], entry["row"]
            old_area = entry.get("area", source_area)
            old_stack = entry["stack"]
            target_item = self.get_item_at(to_col, to_row, area=target_area)

            if (
                target_item is not None
                and target_item is not item_instance
                and self.can_merge_stack_into_item(item_instance, target_item, old_stack)
            ):
                self.grid_items[target_item]["stack"] += old_stack
                self._erase_item_from_grid(item_instance)
                self.sync_legacy_slots_from_grid()
                return True

            self._erase_item_from_grid(item_instance)
            if not self.can_place_item_at(item_instance, to_col, to_row, area=target_area):
                self.place_item_at(item_instance, old_col, old_row, stack=old_stack, area=old_area, allow_repack=True)
                return False

            return self.place_item_at(item_instance, to_col, to_row, stack=old_stack, area=target_area)

        def can_merge_stack_into_item(self, source_item, target_item, incoming_stack=1):
            self._ensure_grid_state()
            if source_item is None or target_item is None or source_item is target_item:
                return False
            if source_item.id != target_item.id:
                return False

            target_entry = self.grid_items.get(target_item)
            if target_entry is None:
                return False

            max_stack = getattr(target_item.config, "max_stack", 1)
            if max_stack <= 1:
                return False

            return (target_entry["stack"] + max(int(incoming_stack), 1)) <= max_stack

        def find_merge_target_for_item(self, item_instance, incoming_stack=1, preferred_col=None, preferred_row=None, preferred_area=None):
            self._ensure_grid_state()

            if preferred_col is not None and preferred_row is not None:
                preferred_item = self.get_item_at(preferred_col, preferred_row, area=preferred_area)
                if self.can_merge_stack_into_item(item_instance, preferred_item, incoming_stack):
                    return preferred_item

            for area_name in self._search_areas(preferred_area):
                data = self.grid_areas.get(area_name)
                if data is None:
                    continue
                for existing_item, entry in data["items"].items():
                    if self.can_merge_stack_into_item(item_instance, existing_item, incoming_stack):
                        return existing_item
            return None

        def move_item_to_container(self, item_instance, target_container, target_col=None, target_row=None, target_area=None):
            self._ensure_grid_state()
            if target_container is None:
                return False
            target_container._ensure_grid_state()

            entry = self.grid_items.get(item_instance)
            if entry is None:
                return False

            source_stack = entry["stack"]
            merge_target = target_container.find_merge_target_for_item(
                item_instance,
                incoming_stack=source_stack,
                preferred_col=target_col,
                preferred_row=target_row,
                preferred_area=target_area,
            )
            if merge_target is not None:
                target_container.grid_items[merge_target]["stack"] += source_stack
                target_container.sync_legacy_slots_from_grid()
                self._erase_item_from_grid(item_instance)
                self.sync_legacy_slots_from_grid()
                return True

            if target_col is not None and target_row is not None and target_container.can_place_item_at(item_instance, target_col, target_row, area=target_area):
                anchor = (target_area or target_container.default_storage_area, target_col, target_row)
            else:
                anchor = target_container.find_space_for_item(item_instance, area=target_area, return_area=True)
                if anchor is None:
                    return False

            if not target_container.place_item_at(item_instance, anchor[1], anchor[2], stack=source_stack, allow_repack=True, area=anchor[0]):
                return False

            self._erase_item_from_grid(item_instance)
            self.sync_legacy_slots_from_grid()
            return True

        def sync_grid_from_legacy_slots(self):
            self._ensure_grid_state()
            for area in list(self.grid_areas.keys()):
                self._set_grid_area(area, self.grid_areas[area]["cols"], self.grid_areas[area]["rows"])
            self._refresh_grid_aliases()

            for slot in self.backpack_slots:
                if slot is None:
                    continue
                item_instance = slot.get("item")
                stack = slot.get("stack", 1)
                if item_instance is None or item_instance in self.grid_items:
                    continue

                anchor = self.find_space_for_item(item_instance, return_area=True)
                if anchor is None:
                    return False
                self.place_item_at(item_instance, anchor[1], anchor[2], stack=stack, area=anchor[0])

            self.sync_legacy_slots_from_grid()
            return True

        def sync_legacy_slots_from_grid(self):
            if not hasattr(self, "grid_areas"):
                return True

            self._refresh_grid_aliases()
            self.backpack_slots = [None] * self.max_slots
            cursor = 0
            for area in self._area_order():
                entries = sorted(
                    self.grid_areas[area]["items"].values(),
                    key=lambda entry: (entry["row"], entry["col"], entry["item"].id)
                )
                for entry in entries:
                    if cursor >= len(self.backpack_slots):
                        break
                    self.backpack_slots[cursor] = {
                        "item": entry["item"],
                        "stack": entry["stack"],
                    }
                    cursor += 1
            return True

        def is_barefoot(self):
            left_shod = self.slots.get("left_foot") is not None
            right_shod = self.slots.get("right_foot") is not None
            return not (left_shod and right_shod)

        def _container_size_for_slot(self, slot_name):
            item = self.slots.get(slot_name)
            if item is None:
                return (0, 0)

            raw_w, raw_h = getattr(item.config, "container_grid_size", (0, 0))
            capacity = max(int(raw_w or 0), 0) * max(int(raw_h or 0), 0)
            if capacity <= 0:
                return (0, 0)

            if slot_name == INVENTORY_AREA_WAIST:
                cols = min(capacity, PLAYER_WAIST_MAX_COLS)
                return (cols, PLAYER_WAIST_MAX_ROWS)

            cols = min(max(int(raw_w or 1), 1), PLAYER_BACKPACK_MAX_COLS)
            rows = min(max((capacity + cols - 1) // cols, 1), PLAYER_BACKPACK_MAX_ROWS)
            return (cols, rows)

        def calculate_backpack_dimensions(self):
            return self._container_size_for_slot(INVENTORY_AREA_BACKPACK)

        def calculate_waist_dimensions(self):
            return self._container_size_for_slot(INVENTORY_AREA_WAIST)

        def refresh_backpack_grid(self):
            self._ensure_grid_state()
            backpack_size = self.calculate_backpack_dimensions()
            waist_size = self.calculate_waist_dimensions()
            if not self.configure_storage_areas({
                INVENTORY_AREA_BACKPACK: backpack_size,
                INVENTORY_AREA_WAIST: waist_size,
            }):
                renpy.notify("当前容器空间不足，无法更换该装备。")
                return False
            return True

        def add_item(self, item_instance, area=None):
            self._ensure_grid_state()
            max_stack = item_instance.config.max_stack

            if max_stack > 1:
                for entry in self.grid_items.values():
                    if entry["item"].id == item_instance.id and entry["stack"] < max_stack:
                        entry["stack"] += 1
                        self.sync_legacy_slots_from_grid()
                        return True

            anchor = self.find_space_for_item(item_instance, area=area, return_area=True)
            if anchor is None:
                return False

            return self.place_item_at(item_instance, anchor[1], anchor[2], stack=1, area=anchor[0])

        def remove_item(self, item_instance):
            self._ensure_grid_state()
            entry = self.grid_items.get(item_instance)
            if entry is not None:
                entry["stack"] -= 1
                if entry["stack"] <= 0:
                    self._erase_item_from_grid(item_instance)
                self.sync_legacy_slots_from_grid()
                return True
            for slot_name, inst in list(self.slots.items()):
                if inst is item_instance:
                    self.slots[slot_name] = None
                    return True
            return False

        def extract_item_for_transfer(self, item_instance):
            self._ensure_grid_state()
            entry = self.grid_items.get(item_instance)
            if entry is not None:
                if entry["stack"] > 1:
                    entry["stack"] -= 1
                    self.sync_legacy_slots_from_grid()
                    return create_item_instance(
                        item_instance.id,
                        durability=getattr(item_instance, "durability", None)
                    )

                self._erase_item_from_grid(item_instance)
                self.sync_legacy_slots_from_grid()
                return item_instance

            for slot_name, inst in list(self.slots.items()):
                if inst is item_instance:
                    self.slots[slot_name] = None
                    return item_instance

            return None

        def remove_item_stack(self, item_instance):
            self._ensure_grid_state()
            if item_instance in self.grid_items:
                self._erase_item_from_grid(item_instance)
                self.sync_legacy_slots_from_grid()
                return True
            return False

        def remove_one_random_item(self):
            self._ensure_grid_state()
            if not self.grid_items:
                return False

            item_instance = renpy.random.choice(list(self.grid_items.keys()))
            entry = self.grid_items[item_instance]
            entry["stack"] -= 1
            if entry["stack"] <= 0:
                self._erase_item_from_grid(item_instance)
            self.sync_legacy_slots_from_grid()
            return True

        def add_item_by_id(self, item_id, durability=None):
            item_instance = create_item_instance(item_id, durability)
            self.add_item(item_instance)
            return item_instance

        def _try_drop_unequipped_item_to_ground(self, item_instance):
            current_container = get_current_ground_container()
            if current_container is None:
                return False

            if current_container.add_item(item_instance):
                renpy.notify(f"{item_instance.config.name} 已放到地面。")
                return True

            return False

        def _after_unequip_item(self, slot_name):
            if slot_name == "right_hand":
                self.update_player_attack_modes()

            if slot_name in ("left_foot", "right_foot"):
                if self.is_barefoot():
                    player_stats.add_condition(COND_BARE_FOOT)
                else:
                    player_stats.remove_condition(COND_BARE_FOOT)

        def check_item_count(self, item_id):
            self._ensure_grid_state()
            count = 0
            for entry in self.grid_items.values():
                if entry["item"].id == item_id:
                    count += entry["stack"]
            for slot_name, item in self.slots.items():
                if item and item.id == item_id:
                    count += 1
            return count

        @property
        def backpack_grid(self):
            self._ensure_grid_state()
            result = []
            for entry in self.grid_items.values():
                for i in range(entry["stack"]):
                    result.append(entry["item"])
            return result

        def unequip_item(self, slot_name, target_col=None, target_row=None, target_area=None):
            self._ensure_grid_state()
            item = self.slots[slot_name]
            if item is None:
                return False

            if slot_name in (INVENTORY_AREA_BACKPACK, INVENTORY_AREA_WAIST):
                if self.grid_areas.get(slot_name, {}).get("items"):
                    renpy.notify("请先清空该容器，才能卸下这件装备。")
                    return False

                self.slots[slot_name] = None
                if not self.refresh_backpack_grid():
                    self.slots[slot_name] = item
                    self.refresh_backpack_grid()
                    renpy.notify("背包没有足够的空间，无法卸下该装备！")
                    return False

                if self.get_grid_capacity(all_areas=True) <= 0:
                    if self._try_drop_unequipped_item_to_ground(item):
                        self._after_unequip_item(slot_name)
                        return True
                    self.slots[slot_name] = item
                    self.refresh_backpack_grid()
                    renpy.notify("背包、腰带和地面都没有足够的空位，无法卸下装备。")
                    return False
            else:
                self.slots[slot_name] = None

            if target_col is not None and target_row is not None and self.can_place_item_at(item, target_col, target_row, area=target_area):
                anchor = (target_area or self.default_storage_area, target_col, target_row)
            else:
                anchor = self.find_space_for_item(item, area=target_area, return_area=True)

            if anchor is None:
                if target_area is None and self._try_drop_unequipped_item_to_ground(item):
                    self._after_unequip_item(slot_name)
                    return True

                self.slots[slot_name] = item
                if slot_name in (INVENTORY_AREA_BACKPACK, INVENTORY_AREA_WAIST):
                    self.refresh_backpack_grid()
                renpy.notify("背包没有足够的空位，无法卸下装备！")
                return False

            if not self.place_item_at(item, anchor[1], anchor[2], stack=1, area=anchor[0]):
                self.slots[slot_name] = item
                if slot_name in (INVENTORY_AREA_BACKPACK, INVENTORY_AREA_WAIST):
                    self.refresh_backpack_grid()
                renpy.notify("移动失败。")
                return False

            self._after_unequip_item(slot_name)

            return True

        def update_player_attack_modes(self):
            base_modes = [1, 4]
            weapon_item = self.slots.get("right_hand")
            if weapon_item and weapon_item.id in WEAPON_ATTACK_MAP:
                base_modes.extend(WEAPON_ATTACK_MAP[weapon_item.id])
            player_stats.attack_mode_ids = list(set(base_modes))
