init python:
    UNIFIED_EQUIP_LAYOUT = {
        "hat": (0.44, 0.06),
        "neck": (0.44, 0.18),
        "torso": (0.44, 0.32),
        "left_hand": (0.14, 0.32),
        "left_wrist": (0.14, 0.46),
        "right_hand": (0.74, 0.32),
        "right_wrist": (0.74, 0.46),
        "legs": (0.44, 0.54),
        "left_foot": (0.22, 0.68),
        "right_foot": (0.66, 0.68),
        "left_ankle": (0.14, 0.82),
        "right_ankle": (0.74, 0.82),
        "backpack": (0.74, 0.12),
        "waist": (0.74, 0.56),
    }

    UNIFIED_EQUIP_LABELS = {
        "hat": "头部",
        "neck": "颈部",
        "torso": "躯干",
        "left_hand": "左手",
        "left_wrist": "左腕",
        "right_hand": "右手",
        "right_wrist": "右腕",
        "legs": "腿部",
        "left_foot": "左脚",
        "right_foot": "右脚",
        "left_ankle": "左踝",
        "right_ankle": "右踝",
        "backpack": "背包",
        "waist": "腰部",
    }

    def unified_inventory_prepare(inv):
        if inv is None:
            return
        ensure_grid = getattr(inv, "_ensure_grid_state", None)
        if ensure_grid is not None:
            ensure_grid()

    def unified_prepare_secondary_inventory(inv, mode):
        unified_inventory_prepare(inv)
        if inv is None:
            return

        if mode == "shop":
            if not ("MERCHANT_GRID_COLS" in globals() and "MERCHANT_GRID_ROWS" in globals()):
                return
            target_cols = MERCHANT_GRID_COLS
            target_rows = MERCHANT_GRID_ROWS
        elif mode == "ground":
            if not ("GROUND_CONTAINER_GRID_COLS" in globals() and "GROUND_CONTAINER_GRID_ROWS" in globals()):
                return
            target_cols = GROUND_CONTAINER_GRID_COLS
            target_rows = GROUND_CONTAINER_GRID_ROWS
        else:
            return

        cols, rows = inv.get_grid_size()
        if cols != target_cols or rows != target_rows:
            inv.configure_grid(target_cols, target_rows, preserve_items=True)

    def unified_item_label_text(name, max_chars=7):
        if not name:
            return ""
        if len(name) <= max_chars:
            return name
        return name[:max_chars] + "..."

    def unified_item_tooltip_text(item):
        if item is None:
            return ""
        name = getattr(item.config, "name", "")
        desc = getattr(item.config, "desc", "")
        if name and desc:
            return name + "\n\n" + desc
        return name or desc

    def unified_inventory_entries(inv, area=None):
        if inv is None:
            return []
        unified_inventory_prepare(inv)
        if area is not None:
            entries = [entry for item, entry in inv.iter_grid_items(area=area)]
        else:
            entries = list(getattr(inv, "grid_items", {}).values())
        return sorted(entries, key=lambda entry: (entry["row"], entry["col"], entry["item"].id))

    def unified_inventory_grid_pixels(inv, cell_size, spacing, area=None):
        if inv is None:
            return (0, 0)
        unified_inventory_prepare(inv)
        cols, rows = inv.get_grid_size(area=area)
        if cols <= 0 or rows <= 0:
            return (0, 0)
        return (
            cols * cell_size + max(cols - 1, 0) * spacing,
            rows * cell_size + max(rows - 1, 0) * spacing,
        )

    def unified_get_item_by_anchor(inv, anchor, area=None):
        if inv is None or anchor is None:
            return None
        unified_inventory_prepare(inv)
        cols, rows = inv.get_grid_size(area=area)
        if cols <= 0:
            return None
        return inv.get_item_at(anchor % cols, anchor // cols, area=area)

    def unified_try_move_between_containers(source_inv, source_idx, target_inv, target_idx, source_area=None, target_area=None):
        if source_inv is None or target_inv is None or source_idx is None or target_idx is None:
            return False

        unified_inventory_prepare(source_inv)
        unified_inventory_prepare(target_inv)

        source_cols, source_rows = source_inv.get_grid_size(area=source_area)
        target_cols, target_rows = target_inv.get_grid_size(area=target_area)
        if source_cols <= 0 or target_cols <= 0:
            return False

        source_item = source_inv.get_item_at(source_idx % source_cols, source_idx // source_cols, area=source_area)
        if source_item is None:
            return False

        target_col = target_idx % target_cols
        target_row = target_idx // target_cols
        if source_inv.move_item_to_container(source_item, target_inv, target_col, target_row, target_area=target_area):
            return True

        renpy.notify("移动失败。")
        return False

    def unified_try_move_within_container(inv, source_idx, target_idx, source_area=None, target_area=None):
        if inv is None or source_idx is None or target_idx is None:
            return False

        unified_inventory_prepare(inv)
        source_cols, source_rows = inv.get_grid_size(area=source_area)
        target_cols, target_rows = inv.get_grid_size(area=target_area)
        if source_cols <= 0 or target_cols <= 0:
            return False

        src_col = source_idx % source_cols
        src_row = source_idx // source_cols
        dst_col = target_idx % target_cols
        dst_row = target_idx // target_cols

        if inv.move_item_within_grid(src_col, src_row, dst_col, dst_row, from_area=source_area, to_area=target_area):
            return True

        renpy.notify("目标区域放不下该物品。")
        return False

    def unified_try_unequip_to_inventory(slot_name, inv, target_idx, target_area=None):
        if inv is None or slot_name is None or target_idx is None:
            return False

        unified_inventory_prepare(inv)
        if inv.slots.get(slot_name) is None:
            return False

        cols, rows = inv.get_grid_size(area=target_area)
        if cols <= 0:
            return False
        return inv.unequip_item(slot_name, target_col=target_idx % cols, target_row=target_idx // cols, target_area=target_area)

    def unified_try_unequip_auto(slot_name, inv):
        if inv is None or slot_name is None:
            return False

        unified_inventory_prepare(inv)
        if inv.slots.get(slot_name) is None:
            return False

        return inv.unequip_item(slot_name)

    def unified_try_equip_from_inventory(inv, source_idx, slot_name, source_area=None):
        if inv is None or source_idx is None or slot_name is None:
            return False

        unified_inventory_prepare(inv)
        cols, rows = inv.get_grid_size(area=source_area)
        if cols <= 0:
            return False

        src_col = source_idx % cols
        src_row = source_idx // cols
        item = inv.get_item_at(src_col, src_row, area=source_area)
        if item is None:
            return False

        if slot_name not in item.config.equip_slots:
            renpy.notify(f"{item.config.name} 不能装备到该槽位。")
            return False

        old_item = inv.slots.get(slot_name)
        old_entry = inv.grid_items.get(item)
        old_stack = old_entry["stack"] if old_entry is not None else 1

        inv._erase_item_from_grid(item)
        inv.slots[slot_name] = item

        if slot_name in ("backpack", "waist"):
            if not inv.refresh_backpack_grid():
                inv.slots[slot_name] = old_item
                inv.place_item_at(item, src_col, src_row, stack=old_stack, area=source_area, allow_repack=True)
                renpy.notify("背包空间不足，无法装备该物品。")
                return False

        if old_item is not None:
            anchor = inv.find_space_for_item(old_item, return_area=True)
            if anchor is None:
                inv.slots[slot_name] = old_item
                if slot_name in ("backpack", "waist"):
                    inv.refresh_backpack_grid()
                inv.place_item_at(item, src_col, src_row, stack=old_stack, area=source_area, allow_repack=True)
                renpy.notify("背包空间不足，无法交换该装备。")
                return False
            inv.place_item_at(old_item, anchor[1], anchor[2], area=anchor[0], allow_repack=True)

        inv.sync_legacy_slots_from_grid()

        if slot_name == "right_hand":
            inv.update_player_attack_modes()

        if slot_name in ("left_foot", "right_foot"):
            if inv.is_barefoot():
                player_stats.add_condition(COND_BARE_FOOT)
            else:
                player_stats.remove_condition(COND_BARE_FOOT)

        return True

    def unified_item_can_equip(item):
        return item is not None and bool(getattr(item.config, "equip_slots", []))

    def unified_try_equip_player_item(inv, item):
        if inv is None or item is None:
            return False

        unified_inventory_prepare(inv)
        source_entry = getattr(inv, "grid_items", {}).get(item)
        if source_entry is None:
            return False

        equip_slots = [slot for slot in getattr(item.config, "equip_slots", []) if slot in inv.slots]
        if not equip_slots:
            renpy.notify(f"{item.config.name} 不能装备。")
            return False

        slot_name = None
        for candidate in equip_slots:
            if inv.slots.get(candidate) is None:
                slot_name = candidate
                break
        if slot_name is None:
            slot_name = equip_slots[0]

        source_area = source_entry.get("area", inv.default_storage_area)
        source_idx = inv.get_grid_index(source_entry["col"], source_entry["row"], area=source_area)
        return unified_try_equip_from_inventory(inv, source_idx, slot_name, source_area)

    def unified_try_equip_from_ground(source_inv, source_item, target_inv):
        if source_inv is None or source_item is None or target_inv is None:
            return False

        unified_inventory_prepare(source_inv)
        unified_inventory_prepare(target_inv)

        source_entry = getattr(source_inv, "grid_items", {}).get(source_item)
        if source_entry is None:
            return False

        equip_slots = [slot for slot in getattr(source_item.config, "equip_slots", []) if slot in target_inv.slots]
        if not equip_slots:
            renpy.notify(f"{source_item.config.name} 不能装备。")
            return False

        slot_name = None
        for candidate in equip_slots:
            if target_inv.slots.get(candidate) is None:
                slot_name = candidate
                break
        if slot_name is None:
            slot_name = equip_slots[0]

        source_col = source_entry["col"]
        source_row = source_entry["row"]
        source_area = source_entry.get("area", source_inv.default_storage_area)
        source_stack = source_entry["stack"]
        old_item = target_inv.slots.get(slot_name)

        source_inv._erase_item_from_grid(source_item)
        source_inv.sync_legacy_slots_from_grid()
        target_inv.slots[slot_name] = source_item

        if slot_name in ("backpack", "waist"):
            if not target_inv.refresh_backpack_grid():
                target_inv.slots[slot_name] = old_item
                target_inv.refresh_backpack_grid()
                source_inv.place_item_at(source_item, source_col, source_row, stack=source_stack, area=source_area, allow_repack=True)
                renpy.notify("背包空间不足，无法装备该物品。")
                return False

        if old_item is not None:
            if slot_name in ("backpack", "waist"):
                if not source_inv.place_item_at(old_item, source_col, source_row, area=source_area, allow_repack=True):
                    target_inv.slots[slot_name] = old_item
                    target_inv.refresh_backpack_grid()
                    source_inv.place_item_at(source_item, source_col, source_row, stack=source_stack, area=source_area, allow_repack=True)
                    renpy.notify("地面空间不足，无法交换该装备。")
                    return False
            else:
                anchor = target_inv.find_space_for_item(old_item, return_area=True)
                if anchor is None:
                    target_inv.slots[slot_name] = old_item
                    source_inv.place_item_at(source_item, source_col, source_row, stack=source_stack, area=source_area, allow_repack=True)
                    renpy.notify("背包空间不足，无法交换该装备。")
                    return False
                target_inv.place_item_at(old_item, anchor[1], anchor[2], area=anchor[0], allow_repack=True)

        target_inv.sync_legacy_slots_from_grid()

        if slot_name == "right_hand":
            target_inv.update_player_attack_modes()

        if slot_name in ("left_foot", "right_foot"):
            if target_inv.is_barefoot():
                player_stats.add_condition(COND_BARE_FOOT)
            else:
                player_stats.remove_condition(COND_BARE_FOOT)

        renpy.notify(f"已装备 {source_item.config.name}。")
        return True

    def unified_run_no_return(func, *args, **kwargs):
        func(*args, **kwargs)
        return None

    def unified_context_menu_pos(menu_w=156, menu_h=132, pad=8):
        x, y = renpy.get_mouse_pos()
        max_x = max(pad, config.screen_width - menu_w - pad)
        max_y = max(pad, config.screen_height - menu_h - pad)
        return (min(max(x, pad), max_x), min(max(y, pad), max_y))

    def unified_item_menu_option_count(item, menu_context="player"):
        can_use_item = item is not None and item.id in ITEM_USE_FUNCTIONS
        can_equip_item = unified_item_can_equip(item)
        if menu_context in ("shop_buy", "shop_sell", "equipment"):
            return 2
        if menu_context == "ground":
            return 2 + (1 if can_use_item else 0) + (1 if can_equip_item else 0)
        return 2 + (1 if can_use_item else 0) + (1 if can_equip_item else 0)

    def unified_item_menu_price_h(menu_context="player"):
        return 30 if menu_context in ("shop_buy", "shop_sell") else 0

    def unified_item_menu_pos(item, menu_context="player", menu_w=132, option_h=36, menu_pad=7, option_gap=5):
        option_count = unified_item_menu_option_count(item, menu_context)
        price_h = unified_item_menu_price_h(menu_context)
        price_gap = option_gap if price_h else 0
        menu_h = option_count * option_h + max(option_count - 1, 0) * option_gap + price_h + price_gap + menu_pad * 2
        return unified_context_menu_pos(menu_w, menu_h)


screen scr_unified_inventory_item_menu(item, inv, actor=None, menu_pos=None, menu_context="player", player_inv=None, shop_inv=None, shop_type=None, barter_rate=1.0, equip_slot=None):
    modal True
    zorder 300

    $ menu_w = 132
    $ option_h = 36
    $ menu_pad = 7
    $ option_gap = 5
    $ menu_option_w = menu_w - menu_pad * 2
    $ can_use_item = item is not None and item.id in ITEM_USE_FUNCTIONS
    $ can_equip_item = unified_item_can_equip(item)
    $ option_count = unified_item_menu_option_count(item, menu_context)
    $ price_h = unified_item_menu_price_h(menu_context)
    $ price_gap = option_gap if price_h else 0
    $ shop_price = get_shop_price(item, shop_type, buy=(menu_context == "shop_buy"), barter_rate=barter_rate) if item is not None and menu_context in ("shop_buy", "shop_sell") else 0
    $ shop_price_label = "买入" if menu_context == "shop_buy" else "卖出"
    $ menu_h = option_count * option_h + max(option_count - 1, 0) * option_gap + price_h + price_gap + menu_pad * 2
    $ menu_x, menu_y = menu_pos if menu_pos is not None else unified_context_menu_pos(menu_w, menu_h)

    button:
        xsize config.screen_width
        ysize config.screen_height
        background None
        action Hide("scr_unified_inventory_item_menu")
        alternate Hide("scr_unified_inventory_item_menu")

    frame:
        xpos menu_x
        ypos menu_y
        xsize menu_w
        ysize menu_h
        background Solid("#191b20ee")
        padding (menu_pad, menu_pad)

        vbox:
            spacing option_gap
            xsize menu_option_w

            if menu_context in ("shop_buy", "shop_sell"):
                frame:
                    xsize menu_option_w
                    ysize price_h
                    background Solid("#111318")
                    padding (6, 3)

                    text "[shop_price_label] [shop_price]":
                        size 18
                        color "#d9d2c2"
                        xalign 0.5
                        yalign 0.5

            if menu_context == "shop_buy":
                textbutton "购买":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, shop_execute_purchase, player_inv, inv, item, shop_type, barter_rate),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            elif menu_context == "shop_sell":
                textbutton "卖出":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, shop_execute_sell, inv, shop_inv, item, shop_type, barter_rate),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            elif menu_context == "equipment":
                textbutton "卸下":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, unified_try_unequip_auto, equip_slot, inv),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            elif menu_context == "ground":
                textbutton "拿取":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, take_item_from_ground_to_player, item, inv, player_inv),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            if menu_context in ("player", "ground") and can_use_item:
                textbutton "使用":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, use_item_and_refresh_screen, item, inv, actor),
                        If(is_in_active_combat(), Function(disable_player_turn_in_combat), NullAction()),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            if menu_context == "player" and can_equip_item:
                textbutton "装备":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, unified_try_equip_player_item, inv, item),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            if menu_context == "ground" and can_equip_item:
                textbutton "装备":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, unified_try_equip_from_ground, inv, item, player_inv),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            if menu_context == "player":
                textbutton "丢弃":
                    xsize menu_option_w
                    ysize option_h
                    background Solid("#252831")
                    hover_background Solid("#3f4754")
                    action [
                        Function(unified_run_no_return, ui_action_drop_item, item, inv),
                        Hide("tooltip_delay_timer"),
                        Hide("floating_tooltip"),
                        Hide("scr_unified_inventory_item_menu")
                    ]
                    text_size 22
                    text_xalign 0.5
                    text_yalign 0.5

            textbutton "取消":
                xsize menu_option_w
                ysize option_h
                background Solid("#252831")
                hover_background Solid("#3f4754")
                action Hide("scr_unified_inventory_item_menu")
                text_size 22
                text_xalign 0.5
                text_yalign 0.5


screen scr_unified_inventory(
    equipment_slots,
    player_inv,
    secondary_inv,
    screen_title="背包/地面",
    secondary_title="地面",
    mode="ground",
    close_mode="hide",
    close_screen_name="scr_unified_inventory",
    merchant_name=None,
    merchant_avatar=None,
    merchant_description="",
    shop_type=None,
    barter_rate=1.0,
    show_secondary=True
):
    tag unified_inventory
    modal True
    zorder 100
    key "game_menu" action If(is_in_active_combat(), NullAction(), ShowMenu("history"))

    default hovered_player_area = None
    default hovered_player_anchor = None
    default hovered_secondary_anchor = None
    default hovered_equip_slot = None
    default selected_player_area = None
    default selected_player_anchor = None
    default selected_secondary_anchor = None
    default selected_equip_slot = None

    $ unified_inventory_prepare(player_inv)
    $ unified_prepare_secondary_inventory(secondary_inv, mode)
    $ backpack_area = INVENTORY_AREA_BACKPACK
    $ waist_area = INVENTORY_AREA_WAIST
    $ backpack_cols, backpack_rows = player_inv.get_grid_size(area=backpack_area)
    $ waist_cols, waist_rows = player_inv.get_grid_size(area=waist_area)
    $ secondary_cols, secondary_rows = secondary_inv.get_grid_size() if show_secondary and secondary_inv is not None else (0, 0)
    $ player_cell_size = 100
    $ waist_cell_size = 100
    $ secondary_cell_size = 100
    $ grid_spacing = 3
    $ equip_slot_size = 108
    $ backpack_grid_w, backpack_grid_h = unified_inventory_grid_pixels(player_inv, player_cell_size, grid_spacing, area=backpack_area)
    $ waist_grid_w, waist_grid_h = unified_inventory_grid_pixels(player_inv, waist_cell_size, grid_spacing, area=waist_area)
    $ secondary_grid_w, secondary_grid_h = unified_inventory_grid_pixels(secondary_inv, secondary_cell_size, grid_spacing)
    $ backpack_entries = unified_inventory_entries(player_inv, area=backpack_area)
    $ waist_entries = unified_inventory_entries(player_inv, area=waist_area)
    $ secondary_entries = unified_inventory_entries(secondary_inv) if show_secondary else []
    $ selected_player_item = unified_get_item_by_anchor(player_inv, selected_player_anchor, selected_player_area)
    $ selected_secondary_item = unified_get_item_by_anchor(secondary_inv, selected_secondary_anchor)
    $ unified_is_shop = mode == "shop"
    $ unified_outer_padding = 18
    $ unified_button_strip_h = 38
    $ unified_column_gap = 14
    $ unified_panel_pad = 14
    $ unified_grid_pad = 8
    $ backpack_display_w = max(backpack_grid_w, PLAYER_BACKPACK_MAX_COLS * player_cell_size + max(PLAYER_BACKPACK_MAX_COLS - 1, 0) * grid_spacing)
    $ backpack_display_h = max(backpack_grid_h, PLAYER_BACKPACK_MAX_ROWS * player_cell_size + max(PLAYER_BACKPACK_MAX_ROWS - 1, 0) * grid_spacing)
    $ waist_display_w = max(waist_grid_w, PLAYER_WAIST_MAX_COLS * waist_cell_size + max(PLAYER_WAIST_MAX_COLS - 1, 0) * grid_spacing)
    $ waist_display_h = max(waist_grid_h, PLAYER_WAIST_MAX_ROWS * waist_cell_size + max(PLAYER_WAIST_MAX_ROWS - 1, 0) * grid_spacing)
    $ player_panel_w = max(backpack_display_w, waist_display_w) + unified_panel_pad * 2 + unified_grid_pad * 2 + 22
    $ secondary_panel_w = secondary_grid_w + unified_panel_pad * 2 + unified_grid_pad * 2 + 22 if show_secondary else 0
    $ equipment_panel_w = 500
    $ content_panel_w = player_panel_w + (unified_column_gap + secondary_panel_w if show_secondary else 0)
    $ outer_panel_w = content_panel_w + unified_outer_padding * 2 if unified_is_shop else equipment_panel_w + unified_column_gap + content_panel_w + unified_outer_padding * 2
    $ backpack_panel_h = backpack_display_h + 48
    $ waist_panel_h = waist_display_h + 82
    $ unified_outer_h = int(config.screen_height * 0.88)
    $ unified_content_h = unified_outer_h - 14 - unified_button_strip_h
    $ unified_outer_w = min(int(config.screen_width * 0.98), outer_panel_w)
    $ unified_inner_w = unified_outer_w - unified_outer_padding * 2
    $ unified_inner_h = unified_outer_h - 28
    $ unified_main_w = content_panel_w if unified_is_shop else equipment_panel_w + unified_column_gap + content_panel_w
    $ unified_main_h = unified_content_h
    $ equipment_panel_inner_w = equipment_panel_w - 36
    $ equipment_panel_inner_h = unified_main_h - 36
    $ equipment_header_h = 34
    $ equipment_slots_h = max(0, equipment_panel_inner_h - equipment_header_h - 14)
    $ player_panel_inner_w = player_panel_w - unified_panel_pad * 2
    $ player_panel_inner_h = unified_main_h - unified_panel_pad * 2
    $ player_action_h = 0
    $ player_inventory_sections_h = player_panel_inner_h
    $ inventory_title_h = 34
    $ inventory_title_gap = 12
    $ backpack_frame_w = backpack_display_w + unified_grid_pad * 2
    $ backpack_frame_h = backpack_display_h + unified_grid_pad * 2
    $ waist_frame_w = waist_display_w + unified_grid_pad * 2
    $ waist_frame_h = waist_display_h + 36
    $ backpack_frame_x = max(0, int((player_panel_inner_w - backpack_frame_w) / 2))
    $ waist_frame_x = max(0, int((player_panel_inner_w - waist_frame_w) / 2))
    $ backpack_frame_y = inventory_title_h + inventory_title_gap
    $ waist_frame_y = max(0, player_inventory_sections_h - waist_frame_h)
    $ waist_title_y = max(0, waist_frame_y - inventory_title_gap - inventory_title_h)
    $ secondary_panel_inner_w = secondary_panel_w - unified_panel_pad * 2
    $ secondary_panel_inner_h = unified_main_h - unified_panel_pad * 2
    $ secondary_header_h = inventory_title_h
    $ secondary_merchant_h = 84 if unified_is_shop and merchant_name else 0
    $ secondary_trade_h = 0
    $ secondary_child_count = 2 + (1 if secondary_merchant_h else 0) + (1 if secondary_trade_h else 0)
    $ secondary_grid_panel_w = secondary_panel_inner_w
    $ secondary_grid_panel_h = max(0, secondary_panel_inner_h - secondary_header_h - secondary_merchant_h - secondary_trade_h - inventory_title_gap * (secondary_child_count - 1))
    $ secondary_viewport_w = secondary_grid_panel_w - unified_grid_pad * 2
    $ secondary_viewport_h = max(0, secondary_grid_panel_h - unified_grid_pad * 2)

    if unified_is_shop and renpy.loadable("images/bg_shop_screen.png"):
        add "images/bg_shop_screen.png":
            xsize config.screen_width
            ysize config.screen_height
            fit "cover"
        add Solid("#00000088") xsize config.screen_width ysize config.screen_height

    else:
        add Solid("#0d0d0f") xsize config.screen_width ysize config.screen_height

    frame:
        xalign 0.5
        yalign 0.5
        xsize unified_outer_w
        ysize unified_outer_h
        background Solid("#151619ee")
        padding (unified_outer_padding, 14)

        fixed:
            xsize unified_inner_w
            ysize unified_inner_h

            hbox:
                spacing unified_column_gap
                xsize unified_main_w
                ysize unified_main_h

                if not unified_is_shop:
                    frame:
                        xsize equipment_panel_w
                        ysize unified_main_h
                        background Solid("#1d1e22")
                        padding (18, 18)

                        vbox:
                            spacing 14
                            xsize equipment_panel_inner_w
                            ysize equipment_panel_inner_h

                            text "装备栏":
                                size 28
                                color "#f0f0f0"
                                xsize equipment_panel_inner_w
                                xalign 0.5
                                textalign 0.5

                            fixed:
                                xsize equipment_panel_inner_w
                                ysize equipment_slots_h

                                for slot_name, pos in UNIFIED_EQUIP_LAYOUT.items():
                                    $ current_item = equipment_slots.get(slot_name) if equipment_slots is not None else None
                                    $ is_hovered = hovered_equip_slot == slot_name
                                    $ is_selected = selected_equip_slot == slot_name
                                    $ frame_color = "#72c37b" if is_selected else "#ececec" if is_hovered else "#2b2d33"

                                    frame:
                                        xpos int(pos[0] * 420)
                                        ypos int(pos[1] * 720)
                                        xsize equip_slot_size
                                        ysize equip_slot_size
                                        background Solid(frame_color)
                                        xpadding 2
                                        ypadding 2

                                        frame:
                                            xsize 1.0
                                            ysize 1.0
                                            background Solid("#17181c")

                                            button:
                                                xsize 1.0
                                                ysize 1.0
                                                background None
                                                if selected_player_anchor is not None:
                                                    action [
                                                        Function(unified_run_no_return, unified_try_equip_from_inventory, player_inv, selected_player_anchor, slot_name, selected_player_area),
                                                        SetScreenVariable("selected_player_anchor", None),
                                                        SetScreenVariable("selected_player_area", None),
                                                        SetScreenVariable("selected_secondary_anchor", None),
                                                        SetScreenVariable("selected_equip_slot", None)
                                                    ]
                                                else:
                                                    action [
                                                        SetScreenVariable("selected_equip_slot", slot_name),
                                                        SetScreenVariable("selected_player_anchor", None),
                                                        SetScreenVariable("selected_player_area", None),
                                                        SetScreenVariable("selected_secondary_anchor", None)
                                                    ]
                                                if current_item:
                                                    alternate [
                                                        SetScreenVariable("selected_equip_slot", slot_name),
                                                        SetScreenVariable("selected_player_anchor", None),
                                                        SetScreenVariable("selected_player_area", None),
                                                        SetScreenVariable("selected_secondary_anchor", None),
                                                        Hide("tooltip_delay_timer"),
                                                        Hide("floating_tooltip"),
                                                        Show("scr_unified_inventory_item_menu", item=current_item, inv=player_inv, menu_pos=unified_item_menu_pos(current_item, "equipment"), menu_context="equipment", equip_slot=slot_name)
                                                    ]
                                                hovered [
                                                    SetScreenVariable("hovered_equip_slot", slot_name),
                                                    Show("tooltip_delay_timer", text=unified_item_tooltip_text(current_item) if current_item else UNIFIED_EQUIP_LABELS.get(slot_name, slot_name))
                                                ]
                                                unhovered [
                                                    SetScreenVariable("hovered_equip_slot", None),
                                                    Hide("tooltip_delay_timer"),
                                                    Hide("floating_tooltip")
                                                ]

                                                if current_item:
                                                    fixed:
                                                        if current_item.icon_path:
                                                            add current_item.icon_path:
                                                                fit "contain"
                                                                xysize (70, 70)
                                                                xpos 0.5
                                                                ypos 0.48
                                                                xanchor 0.5
                                                                yanchor 0.5
                                                        else:
                                                            add Solid("#5a5d66") xysize (70, 70) xpos 0.5 ypos 0.48 xanchor 0.5 yanchor 0.5

                                                        if getattr(current_item, "durability", 1.0) < 1.0:
                                                            text "[current_item.durability * 100:.0f]%":
                                                                size 12
                                                                color "#8ce08d"
                                                                xpos 0.04
                                                                ypos 0.04
                                                                outlines [(1, "#000000")]
                                                else:
                                                    text UNIFIED_EQUIP_LABELS.get(slot_name, slot_name):
                                                        size 12
                                                        color "#6c7280"
                                                        align (0.5, 0.5)

                hbox:
                    spacing unified_column_gap
                    xsize content_panel_w
                    ysize unified_main_h
    
                    frame:
                        xsize player_panel_w
                        ysize unified_main_h
                        background Solid("#1d1e22")
                        padding (unified_panel_pad, unified_panel_pad)
    
                        vbox:
                            spacing 10
                            xsize player_panel_inner_w
                            ysize player_panel_inner_h
    
                            fixed:
                                xsize player_panel_inner_w
                                ysize player_inventory_sections_h
    
                                text "背包":
                                    size 23
                                    color "#f0f0f0"
                                    xpos backpack_frame_x
                                    ypos 0
                                    ysize inventory_title_h

                                frame:
                                    xpos backpack_frame_x
                                    ypos backpack_frame_y
                                    xsize backpack_frame_w
                                    ysize backpack_frame_h
                                    background Solid("#131419")
                                    padding (8, 8)
    
                                    if backpack_cols > 0 and backpack_rows > 0:
                                        fixed:
                                            xsize backpack_grid_w
                                            ysize backpack_grid_h
    
                                            for row in range(backpack_rows):
                                                for col in range(backpack_cols):
                                                    $ cell_idx = player_inv.get_grid_index(col, row, area=backpack_area)
                                                    $ is_hovered = hovered_player_area == backpack_area and hovered_player_anchor == cell_idx
                                                    $ cell_color = "#f4f4f4" if is_hovered else "#24262d"
    
                                                    frame:
                                                        xpos col * (player_cell_size + grid_spacing)
                                                        ypos row * (player_cell_size + grid_spacing)
                                                        xsize player_cell_size
                                                        ysize player_cell_size
                                                        background Solid(cell_color)
                                                        xpadding 1
                                                        ypadding 1
    
                                                        frame:
                                                            xsize 1.0
                                                            ysize 1.0
                                                            background Solid("#0f1014")
    
                                                            button:
                                                                xsize 1.0
                                                                ysize 1.0
                                                                background None
                                                                if unified_is_shop:
                                                                    action [
                                                                        SetScreenVariable("selected_player_anchor", cell_idx),
                                                                        SetScreenVariable("selected_player_area", backpack_area),
                                                                        SetScreenVariable("selected_secondary_anchor", None),
                                                                        SetScreenVariable("selected_equip_slot", None)
                                                                    ]
                                                                elif mode == "ground" and selected_secondary_anchor is not None:
                                                                    action [
                                                                        Function(unified_run_no_return, unified_try_move_between_containers, secondary_inv, selected_secondary_anchor, player_inv, cell_idx, None, backpack_area),
                                                                        SetScreenVariable("selected_secondary_anchor", None),
                                                                        SetScreenVariable("selected_equip_slot", None)
                                                                    ]
                                                                elif selected_equip_slot is not None:
                                                                    action [
                                                                        Function(unified_run_no_return, unified_try_unequip_to_inventory, selected_equip_slot, player_inv, cell_idx, backpack_area),
                                                                        SetScreenVariable("selected_equip_slot", None),
                                                                        SetScreenVariable("selected_secondary_anchor", None)
                                                                    ]
                                                                elif selected_player_anchor is not None:
                                                                    action [
                                                                        Function(unified_run_no_return, unified_try_move_within_container, player_inv, selected_player_anchor, cell_idx, selected_player_area, backpack_area),
                                                                        SetScreenVariable("selected_player_anchor", None),
                                                                        SetScreenVariable("selected_player_area", None),
                                                                        SetScreenVariable("selected_secondary_anchor", None),
                                                                        SetScreenVariable("selected_equip_slot", None)
                                                                    ]
                                                                else:
                                                                    action [
                                                                        SetScreenVariable("selected_player_anchor", cell_idx),
                                                                        SetScreenVariable("selected_player_area", backpack_area),
                                                                        SetScreenVariable("selected_secondary_anchor", None),
                                                                        SetScreenVariable("selected_equip_slot", None)
                                                                    ]
                                                                hovered [SetScreenVariable("hovered_player_area", backpack_area), SetScreenVariable("hovered_player_anchor", cell_idx)]
                                                                unhovered [SetScreenVariable("hovered_player_area", None), SetScreenVariable("hovered_player_anchor", None)]
    
                                            for entry in backpack_entries:
                                                $ item = entry["item"]
                                                $ stack = entry["stack"]
                                                $ item_w, item_h = player_inv.get_item_footprint(item)
                                                $ item_px_w = item_w * player_cell_size + max(item_w - 1, 0) * grid_spacing
                                                $ item_px_h = item_h * player_cell_size + max(item_h - 1, 0) * grid_spacing
                                                $ anchor_idx = player_inv.get_grid_index(entry["col"], entry["row"], area=backpack_area)
                                                $ is_hovered = hovered_player_area == backpack_area and hovered_player_anchor == anchor_idx
                                                $ is_selected = selected_player_area == backpack_area and selected_player_anchor == anchor_idx
                                                $ item_border = "#72c37b" if is_selected else "#ececec" if is_hovered else "#3a3d46"
    
                                                frame:
                                                    xpos entry["col"] * (player_cell_size + grid_spacing)
                                                    ypos entry["row"] * (player_cell_size + grid_spacing)
                                                    xsize item_px_w
                                                    ysize item_px_h
                                                    background Solid(item_border)
                                                    xpadding 2
                                                    ypadding 2
    
                                                    frame:
                                                        xsize 1.0
                                                        ysize 1.0
                                                        background Solid("#1a1c22")
    
                                                        button:
                                                            xsize 1.0
                                                            ysize 1.0
                                                            background None
                                                            if unified_is_shop:
                                                                action [
                                                                    SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_area", backpack_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            elif mode == "ground" and selected_secondary_anchor is not None:
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_move_between_containers, secondary_inv, selected_secondary_anchor, player_inv, anchor_idx, None, backpack_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            elif selected_equip_slot is not None:
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_unequip_to_inventory, selected_equip_slot, player_inv, anchor_idx, backpack_area),
                                                                    SetScreenVariable("selected_equip_slot", None),
                                                                    SetScreenVariable("selected_secondary_anchor", None)
                                                                ]
                                                            elif selected_player_anchor is not None and not (selected_player_area == backpack_area and selected_player_anchor == anchor_idx):
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_move_within_container, player_inv, selected_player_anchor, anchor_idx, selected_player_area, backpack_area),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            else:
                                                                action [
                                                                    SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_area", backpack_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            if unified_is_shop:
                                                                alternate [
                                                                    SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_area", backpack_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None),
                                                                    Hide("tooltip_delay_timer"),
                                                                    Hide("floating_tooltip"),
                                                                    Show("scr_unified_inventory_item_menu", item=item, inv=player_inv, menu_pos=unified_item_menu_pos(item, "shop_sell"), menu_context="shop_sell", shop_inv=secondary_inv, shop_type=shop_type, barter_rate=barter_rate)
                                                                ]
                                                            else:
                                                                alternate [
                                                                    SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_area", backpack_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None),
                                                                    Hide("tooltip_delay_timer"),
                                                                    Hide("floating_tooltip"),
                                                                    Show("scr_unified_inventory_item_menu", item=item, inv=player_inv, actor=_current_combat_instance.player if is_in_active_combat() else None, menu_pos=unified_item_menu_pos(item))
                                                                ]
                                                            hovered [
                                                                SetScreenVariable("hovered_player_area", backpack_area),
                                                                SetScreenVariable("hovered_player_anchor", anchor_idx),
                                                                Show("tooltip_delay_timer", text=unified_item_tooltip_text(item))
                                                            ]
                                                            unhovered [
                                                                SetScreenVariable("hovered_player_area", None),
                                                                SetScreenVariable("hovered_player_anchor", None),
                                                                Hide("tooltip_delay_timer"),
                                                                Hide("floating_tooltip")
                                                            ]
    
                                                            fixed:
                                                                if item.icon_path:
                                                                    add item.icon_path:
                                                                        fit "contain"
                                                                        xysize (min(item_px_w - 16, 92), min(item_px_h - 28, 92))
                                                                        xpos 0.5
                                                                        ypos 0.48
                                                                        xanchor 0.5
                                                                        yanchor 0.5
                                                                else:
                                                                    add Solid("#5a5d66") xysize (min(item_px_w - 16, 92), min(item_px_h - 28, 92)) xpos 0.5 ypos 0.48 xanchor 0.5 yanchor 0.5

                                                                if getattr(item, "durability", 1.0) < 1.0:
                                                                    text "[item.durability * 100:.0f]%" size 12 color "#8ce08d" xpos 5 ypos 4 outlines [(1, "#000000")]
                                                                if stack > 1:
                                                                    text "x[stack]" size 12 color "#ffdd6c" xalign 1.0 yalign 1.0 xoffset -5 yoffset -5 outlines [(1, "#000000")]

                                text "腰带":
                                    size 23
                                    color "#f0f0f0"
                                    xpos waist_frame_x
                                    ypos waist_title_y
                                    ysize inventory_title_h

                                frame:
                                    xpos waist_frame_x
                                    ypos waist_frame_y
                                    xsize waist_frame_w
                                    ysize waist_frame_h
                                    background Solid("#131419")
                                    padding (unified_grid_pad, unified_grid_pad)
    
                                    fixed:
                                        xsize waist_grid_w
                                        ysize waist_grid_h
    
                                        for row in range(waist_rows):
                                            for col in range(waist_cols):
                                                $ cell_idx = player_inv.get_grid_index(col, row, area=waist_area)
                                                $ is_hovered = hovered_player_area == waist_area and hovered_player_anchor == cell_idx
                                                $ cell_color = "#f4f4f4" if is_hovered else "#24262d"
    
                                                frame:
                                                    xpos col * (waist_cell_size + grid_spacing)
                                                    ypos row * (waist_cell_size + grid_spacing)
                                                    xsize waist_cell_size
                                                    ysize waist_cell_size
                                                    background Solid(cell_color)
                                                    xpadding 1
                                                    ypadding 1
    
                                                    frame:
                                                        xsize 1.0
                                                        ysize 1.0
                                                        background Solid("#0f1014")
    
                                                        button:
                                                            xsize 1.0
                                                            ysize 1.0
                                                            background None
                                                            if unified_is_shop:
                                                                action [
                                                                    SetScreenVariable("selected_player_anchor", cell_idx),
                                                                    SetScreenVariable("selected_player_area", waist_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            elif mode == "ground" and selected_secondary_anchor is not None:
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_move_between_containers, secondary_inv, selected_secondary_anchor, player_inv, cell_idx, None, waist_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            elif selected_equip_slot is not None:
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_unequip_to_inventory, selected_equip_slot, player_inv, cell_idx, waist_area),
                                                                    SetScreenVariable("selected_equip_slot", None),
                                                                    SetScreenVariable("selected_secondary_anchor", None)
                                                                ]
                                                            elif selected_player_anchor is not None:
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_move_within_container, player_inv, selected_player_anchor, cell_idx, selected_player_area, waist_area),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            else:
                                                                action [
                                                                    SetScreenVariable("selected_player_anchor", cell_idx),
                                                                    SetScreenVariable("selected_player_area", waist_area),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            hovered [SetScreenVariable("hovered_player_area", waist_area), SetScreenVariable("hovered_player_anchor", cell_idx)]
                                                            unhovered [SetScreenVariable("hovered_player_area", None), SetScreenVariable("hovered_player_anchor", None)]

                                        for entry in waist_entries:
                                            $ item = entry["item"]
                                            $ stack = entry["stack"]
                                            $ item_w, item_h = player_inv.get_item_footprint(item)
                                            $ item_px_w = item_w * waist_cell_size + max(item_w - 1, 0) * grid_spacing
                                            $ item_px_h = item_h * waist_cell_size + max(item_h - 1, 0) * grid_spacing
                                            $ anchor_idx = player_inv.get_grid_index(entry["col"], entry["row"], area=waist_area)
                                            $ is_hovered = hovered_player_area == waist_area and hovered_player_anchor == anchor_idx
                                            $ is_selected = selected_player_area == waist_area and selected_player_anchor == anchor_idx
                                            $ item_border = "#72c37b" if is_selected else "#ececec" if is_hovered else "#3a3d46"
    
                                            frame:
                                                xpos entry["col"] * (waist_cell_size + grid_spacing)
                                                ypos entry["row"] * (waist_cell_size + grid_spacing)
                                                xsize item_px_w
                                                ysize item_px_h
                                                background Solid(item_border)
                                                xpadding 2
                                                ypadding 2
    
                                                frame:
                                                    xsize 1.0
                                                    ysize 1.0
                                                    background Solid("#1a1c22")
    
                                                    button:
                                                        xsize 1.0
                                                        ysize 1.0
                                                        background None
                                                        if unified_is_shop:
                                                            action [
                                                                SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                SetScreenVariable("selected_player_area", waist_area),
                                                                SetScreenVariable("selected_secondary_anchor", None),
                                                                SetScreenVariable("selected_equip_slot", None)
                                                            ]
                                                        elif mode == "ground" and selected_secondary_anchor is not None:
                                                            action [
                                                                Function(unified_run_no_return, unified_try_move_between_containers, secondary_inv, selected_secondary_anchor, player_inv, anchor_idx, None, waist_area),
                                                                SetScreenVariable("selected_secondary_anchor", None),
                                                                SetScreenVariable("selected_player_anchor", None),
                                                                SetScreenVariable("selected_player_area", None),
                                                                SetScreenVariable("selected_equip_slot", None)
                                                            ]
                                                        elif selected_equip_slot is not None:
                                                            action [
                                                                Function(unified_run_no_return, unified_try_unequip_to_inventory, selected_equip_slot, player_inv, anchor_idx, waist_area),
                                                                SetScreenVariable("selected_equip_slot", None),
                                                                SetScreenVariable("selected_secondary_anchor", None)
                                                            ]
                                                        elif selected_player_anchor is not None and not (selected_player_area == waist_area and selected_player_anchor == anchor_idx):
                                                            action [
                                                                Function(unified_run_no_return, unified_try_move_within_container, player_inv, selected_player_anchor, anchor_idx, selected_player_area, waist_area),
                                                                SetScreenVariable("selected_player_anchor", None),
                                                                SetScreenVariable("selected_player_area", None),
                                                                SetScreenVariable("selected_secondary_anchor", None),
                                                                SetScreenVariable("selected_equip_slot", None)
                                                            ]
                                                        else:
                                                            action [
                                                                SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                SetScreenVariable("selected_player_area", waist_area),
                                                                SetScreenVariable("selected_secondary_anchor", None),
                                                                SetScreenVariable("selected_equip_slot", None)
                                                            ]
                                                        if unified_is_shop:
                                                            alternate [
                                                                SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                SetScreenVariable("selected_player_area", waist_area),
                                                                SetScreenVariable("selected_secondary_anchor", None),
                                                                SetScreenVariable("selected_equip_slot", None),
                                                                Hide("tooltip_delay_timer"),
                                                                Hide("floating_tooltip"),
                                                                Show("scr_unified_inventory_item_menu", item=item, inv=player_inv, menu_pos=unified_item_menu_pos(item, "shop_sell"), menu_context="shop_sell", shop_inv=secondary_inv, shop_type=shop_type, barter_rate=barter_rate)
                                                            ]
                                                        else:
                                                            alternate [
                                                                SetScreenVariable("selected_player_anchor", anchor_idx),
                                                                SetScreenVariable("selected_player_area", waist_area),
                                                                SetScreenVariable("selected_secondary_anchor", None),
                                                                SetScreenVariable("selected_equip_slot", None),
                                                                Hide("tooltip_delay_timer"),
                                                                Hide("floating_tooltip"),
                                                                Show("scr_unified_inventory_item_menu", item=item, inv=player_inv, actor=_current_combat_instance.player if is_in_active_combat() else None, menu_pos=unified_item_menu_pos(item))
                                                            ]
                                                        hovered [
                                                            SetScreenVariable("hovered_player_area", waist_area),
                                                            SetScreenVariable("hovered_player_anchor", anchor_idx),
                                                            Show("tooltip_delay_timer", text=unified_item_tooltip_text(item))
                                                        ]
                                                        unhovered [
                                                            SetScreenVariable("hovered_player_area", None),
                                                            SetScreenVariable("hovered_player_anchor", None),
                                                            Hide("tooltip_delay_timer"),
                                                            Hide("floating_tooltip")
                                                        ]
    
                                                        fixed:
                                                            if item.icon_path:
                                                                add item.icon_path:
                                                                    fit "contain"
                                                                    xysize (min(item_px_w - 16, 92), min(item_px_h - 28, 92))
                                                                    xpos 0.5
                                                                    ypos 0.5
                                                                    xanchor 0.5
                                                                    yanchor 0.5
                                                            else:
                                                                add Solid("#5a5d66") xysize (min(item_px_w - 16, 92), min(item_px_h - 28, 92)) xpos 0.5 ypos 0.5 xanchor 0.5 yanchor 0.5
                                                            if getattr(item, "durability", 1.0) < 1.0:
                                                                text "[item.durability * 100:.0f]%" size 12 color "#8ce08d" xpos 5 ypos 4 outlines [(1, "#000000")]
                                                            if stack > 1:
                                                                text "x[stack]" size 12 color "#ffdd6c" xalign 1.0 yalign 1.0 xoffset -5 yoffset -5 outlines [(1, "#000000")]
    
                    if show_secondary:
                        frame:
                            xsize secondary_panel_w
                            ysize unified_main_h
                            background Solid("#1d1e22")
                            padding (unified_panel_pad, unified_panel_pad)
    
                            vbox:
                                spacing 12
                                xsize secondary_panel_inner_w
                                ysize secondary_panel_inner_h
    
                                hbox:
                                    xsize secondary_panel_inner_w
                                    ysize secondary_header_h
    
                                    text secondary_title size 23 color "#f0f0f0"
    
                                if mode == "shop" and merchant_name:
                                    frame:
                                        xsize secondary_panel_inner_w
                                        ysize 84
                                        background Solid("#17181c")
                                        padding (12, 10)
    
                                        hbox:
                                            spacing 14
                                            yalign 0.5
    
                                            frame:
                                                xysize (64, 64)
                                                background Solid("#262932")
                                                if merchant_avatar:
                                                    add merchant_avatar:
                                                        fit "cover"
                                                        xysize (64, 64)
                                                else:
                                                    text "?" size 28 color "#8c8f98" align (0.5, 0.5)
    
                                            vbox:
                                                spacing 4
                                                yalign 0.5
                                                text merchant_name size 22 color "#ffca79"
                                                text merchant_description or "商人货架":
                                                    size 14
                                                    color "#9fa4ad"
                                                    xmaximum secondary_panel_inner_w - 104
    
                                frame:
                                    xsize secondary_grid_panel_w
                                    ysize secondary_grid_panel_h
                                    background Solid("#131419")
                                    padding (8, 8)
    
                                    viewport:
                                        scrollbars "vertical"
                                        mousewheel True
                                        draggable True
                                        xsize secondary_viewport_w
                                        ysize secondary_viewport_h
                                        child_size (secondary_grid_w, secondary_grid_h)
    
                                        fixed:
                                            xsize secondary_grid_w
                                            ysize secondary_grid_h
    
                                            for row in range(secondary_rows):
                                                for col in range(secondary_cols):
                                                    $ cell_idx = secondary_inv.get_grid_index(col, row)
                                                    $ is_hovered = hovered_secondary_anchor == cell_idx
                                                    $ cell_color = "#f4f4f4" if is_hovered else "#24262d"
    
                                                    frame:
                                                        xpos col * (secondary_cell_size + grid_spacing)
                                                        ypos row * (secondary_cell_size + grid_spacing)
                                                        xsize secondary_cell_size
                                                        ysize secondary_cell_size
                                                        background Solid(cell_color)
                                                        xpadding 1
                                                        ypadding 1
    
                                                        frame:
                                                            xsize 1.0
                                                            ysize 1.0
                                                            background Solid("#0f1014")
    
                                                            button:
                                                                xsize 1.0
                                                                ysize 1.0
                                                                background None
                                                                if unified_is_shop:
                                                                    action [
                                                                        SetScreenVariable("selected_secondary_anchor", cell_idx),
                                                                        SetScreenVariable("selected_player_anchor", None),
                                                                        SetScreenVariable("selected_player_area", None),
                                                                        SetScreenVariable("selected_equip_slot", None)
                                                                    ]
                                                                elif mode == "ground" and selected_player_anchor is not None:
                                                                    action [
                                                                        Function(unified_run_no_return, unified_try_move_between_containers, player_inv, selected_player_anchor, secondary_inv, cell_idx, selected_player_area, None),
                                                                        SetScreenVariable("selected_player_anchor", None),
                                                                        SetScreenVariable("selected_player_area", None),
                                                                        SetScreenVariable("selected_equip_slot", None)
                                                                    ]
                                                                elif selected_secondary_anchor is not None and selected_secondary_anchor != cell_idx:
                                                                    action [
                                                                        Function(unified_run_no_return, unified_try_move_within_container, secondary_inv, selected_secondary_anchor, cell_idx),
                                                                        SetScreenVariable("selected_secondary_anchor", None),
                                                                        SetScreenVariable("selected_player_anchor", None),
                                                                        SetScreenVariable("selected_player_area", None)
                                                                    ]
                                                                else:
                                                                    action [
                                                                        SetScreenVariable("selected_secondary_anchor", cell_idx),
                                                                        SetScreenVariable("selected_player_anchor", None),
                                                                        SetScreenVariable("selected_player_area", None),
                                                                        SetScreenVariable("selected_equip_slot", None)
                                                                    ]
                                                                hovered SetScreenVariable("hovered_secondary_anchor", cell_idx)
                                                                unhovered SetScreenVariable("hovered_secondary_anchor", None)
    
                                            for entry in secondary_entries:
                                                $ item = entry["item"]
                                                $ stack = entry["stack"]
                                                $ item_w, item_h = secondary_inv.get_item_footprint(item)
                                                $ item_px_w = item_w * secondary_cell_size + max(item_w - 1, 0) * grid_spacing
                                                $ item_px_h = item_h * secondary_cell_size + max(item_h - 1, 0) * grid_spacing
                                                $ anchor_idx = secondary_inv.get_grid_index(entry["col"], entry["row"])
                                                $ is_hovered = hovered_secondary_anchor == anchor_idx
                                                $ is_selected = selected_secondary_anchor == anchor_idx
                                                $ item_border = "#72c37b" if is_selected else "#ececec" if is_hovered else "#3a3d46"
    
                                                frame:
                                                    xpos entry["col"] * (secondary_cell_size + grid_spacing)
                                                    ypos entry["row"] * (secondary_cell_size + grid_spacing)
                                                    xsize item_px_w
                                                    ysize item_px_h
                                                    background Solid(item_border)
                                                    xpadding 2
                                                    ypadding 2
    
                                                    frame:
                                                        xsize 1.0
                                                        ysize 1.0
                                                        background Solid("#1a1c22")
    
                                                        button:
                                                            xsize 1.0
                                                            ysize 1.0
                                                            background None
                                                            if unified_is_shop:
                                                                action [
                                                                    SetScreenVariable("selected_secondary_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                                alternate [
                                                                    SetScreenVariable("selected_secondary_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_equip_slot", None),
                                                                    Hide("tooltip_delay_timer"),
                                                                    Hide("floating_tooltip"),
                                                                    Show("scr_unified_inventory_item_menu", item=item, inv=secondary_inv, menu_pos=unified_item_menu_pos(item, "shop_buy"), menu_context="shop_buy", player_inv=player_inv, shop_type=shop_type, barter_rate=barter_rate)
                                                                ]
                                                            elif mode == "ground" and selected_player_anchor is not None:
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_move_between_containers, player_inv, selected_player_anchor, secondary_inv, anchor_idx, selected_player_area, None),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            elif selected_secondary_anchor is not None and selected_secondary_anchor != anchor_idx:
                                                                action [
                                                                    Function(unified_run_no_return, unified_try_move_within_container, secondary_inv, selected_secondary_anchor, anchor_idx),
                                                                    SetScreenVariable("selected_secondary_anchor", None),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            else:
                                                                action [
                                                                    SetScreenVariable("selected_secondary_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_equip_slot", None)
                                                                ]
                                                            if mode == "ground":
                                                                alternate [
                                                                    SetScreenVariable("selected_secondary_anchor", anchor_idx),
                                                                    SetScreenVariable("selected_player_anchor", None),
                                                                    SetScreenVariable("selected_player_area", None),
                                                                    SetScreenVariable("selected_equip_slot", None),
                                                                    Hide("tooltip_delay_timer"),
                                                                    Hide("floating_tooltip"),
                                                                    Show("scr_unified_inventory_item_menu", item=item, inv=secondary_inv, actor=_current_combat_instance.player if is_in_active_combat() else None, menu_pos=unified_item_menu_pos(item, "ground"), menu_context="ground", player_inv=player_inv)
                                                                ]
                                                            hovered [
                                                                SetScreenVariable("hovered_secondary_anchor", anchor_idx),
                                                                Show("tooltip_delay_timer", text=unified_item_tooltip_text(item))
                                                            ]
                                                            unhovered [
                                                                SetScreenVariable("hovered_secondary_anchor", None),
                                                                Hide("tooltip_delay_timer"),
                                                                Hide("floating_tooltip")
                                                            ]
    
                                                            fixed:
                                                                if item.icon_path:
                                                                    add item.icon_path:
                                                                        fit "contain"
                                                                        xysize (min(item_px_w - 16, 92), min(item_px_h - 28, 92))
                                                                        xpos 0.5
                                                                        ypos 0.48
                                                                        xanchor 0.5
                                                                        yanchor 0.5
                                                                else:
                                                                    add Solid("#5a5d66") xysize (min(item_px_w - 16, 92), min(item_px_h - 28, 92)) xpos 0.5 ypos 0.48 xanchor 0.5 yanchor 0.5

                                                                if getattr(item, "durability", 1.0) < 1.0:
                                                                    text "[item.durability * 100:.0f]%" size 12 color "#8ce08d" xpos 5 ypos 4 outlines [(1, "#000000")]
                                                                if stack > 1:
                                                                    text "x[stack]" size 12 color "#ffdd6c" xalign 1.0 yalign 1.0 xoffset -5 yoffset -5 outlines [(1, "#000000")]
    
                textbutton "关闭":
                    xpos 0.5
                    ypos 1.0
                    yoffset 12
                    xanchor 0.5
                    yanchor 1.0
                    if close_mode == "return":
                        action [Hide("tooltip_delay_timer"), Hide("floating_tooltip"), Return()]
                    else:
                        action [Hide("tooltip_delay_timer"), Hide("floating_tooltip"), Hide(close_screen_name)]
                    text_size 23

