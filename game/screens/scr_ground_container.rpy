init python:
    def move_selected_ground_item_to_backpack(target_idx, selected_ground_idx, container, player_inv):
        if selected_ground_idx is None:
            return False
        if target_idx < 0 or target_idx >= player_inv.max_slots:
            return False
        if selected_ground_idx >= len(container.backpack_slots):
            return False

        src = container.backpack_slots[selected_ground_idx]
        if src is None:
            return False

        dst = player_inv.backpack_slots[target_idx]
        player_inv.backpack_slots[target_idx] = src
        container.backpack_slots[selected_ground_idx] = dst
        return True

    def move_selected_backpack_item_to_ground(target_idx, selected_player_idx, container, player_inv):
        if selected_player_idx is None:
            return False
        if target_idx < 0 or target_idx >= len(container.backpack_slots):
            return False
        if selected_player_idx >= player_inv.max_slots:
            return False

        src = player_inv.backpack_slots[selected_player_idx]
        if src is None:
            return False

        dst = container.backpack_slots[target_idx]
        container.backpack_slots[target_idx] = src
        player_inv.backpack_slots[selected_player_idx] = dst
        return True

    def swap_ground_slots(idx_a, idx_b, container):
        if idx_a == idx_b:
            return False
        if idx_a < 0 or idx_a >= len(container.backpack_slots):
            return False
        if idx_b < 0 or idx_b >= len(container.backpack_slots):
            return False

        container.backpack_slots[idx_a], container.backpack_slots[idx_b] = \
            container.backpack_slots[idx_b], container.backpack_slots[idx_a]
        return True

    def swap_backpack_slots(idx_a, idx_b, player_inv):
        if idx_a == idx_b:
            return False
        if idx_a < 0 or idx_a >= player_inv.max_slots:
            return False
        if idx_b < 0 or idx_b >= player_inv.max_slots:
            return False

        player_inv.backpack_slots[idx_a], player_inv.backpack_slots[idx_b] = \
            player_inv.backpack_slots[idx_b], player_inv.backpack_slots[idx_a]
        return True

    def equip_item_from_backpack_in_ground_ui(backpack_idx, equip_slot, player_inv):
        """在地面容器界面中，将背包内的物品装备到指定槽位"""
        # 安全边界检查
        if backpack_idx < 0 or backpack_idx >= player_inv.max_slots:
            return
        if equip_slot not in player_inv.slots:
            return
        
        src_slot = player_inv.backpack_slots[backpack_idx]
        if src_slot is None:
            return
        
        item = src_slot["item"]
        if equip_slot not in item.config.equip_slots:
            renpy.notify(f"{item.config.name} 不能装备到该槽位！")
            return
        
        # 战斗中禁用
        if is_in_active_combat():
            mark_inventory_action_performed()
        
        # 保存旧物品
        old_item = player_inv.slots[equip_slot]
        
        # 消耗背包堆叠
        src_slot["stack"] -= 1
        if src_slot["stack"] <= 0:
            player_inv.backpack_slots[backpack_idx] = None
        
        # 装备新物品
        player_inv.slots[equip_slot] = item
        
        # 如果是背包/腰袋，刷新网格
        if equip_slot in ("backpack", "waist"):
            if not player_inv.refresh_backpack_grid():
                # 刷新失败 → 回滚
                player_inv.slots[equip_slot] = old_item
                player_inv.backpack_slots[backpack_idx] = {"item": item, "stack": 1}
                renpy.notify("背包内物品太多，无法更换此装备！")
                return
        
        if old_item is not None:
            empty_idx = -1
            for i in range(player_inv.max_slots):
                if player_inv.backpack_slots[i] is None:
                    empty_idx = i
                    break
            if empty_idx != -1:
                player_inv.backpack_slots[empty_idx] = {"item": old_item, "stack": 1}
            else:
                current_container = get_current_ground_container()
                if current_container is not None:
                    current_container.add_item(old_item)
                    renpy.notify(f"背包空间不足，{old_item.config.name} 已掉落到地上。")
                else:
                    renpy.notify(f"背包空间不足，{old_item.config.name} 丢失了！")
        
        # 更新攻击模式
        if equip_slot == "right_hand":
            player_inv.update_player_attack_modes()
        
        # 同步赤脚状态
        if equip_slot in ("left_foot", "right_foot"):
            if player_inv.is_barefoot():
                player_stats.add_condition(COND_BARE_FOOT)
            else:
                player_stats.remove_condition(COND_BARE_FOOT)
        
        renpy.notify(f"已装备 {item.config.name}。")

    def equip_item_from_ground(item_instance, player_inv, ground_idx, container):
        """从地面容器直接装备物品到对应槽位"""
        # 检查物品是否有可装备的槽位
        if not item_instance.config.equip_slots:
            renpy.notify(f"{item_instance.config.name} 不能装备。")
            return
        
        # 取第一个匹配的装备槽
        equip_slot = item_instance.config.equip_slots[0]
        if equip_slot not in player_inv.slots:
            renpy.notify(f"{item_instance.config.name} 不能装备到任何槽位。")
            return
        
        # 检查该槽位是否已有装备
        old_item = player_inv.slots[equip_slot]
        
        # 从地面容器移除物品
        src = container.backpack_slots[ground_idx]
        if src is None:
            return
        container.backpack_slots[ground_idx] = None
        
        # 装备新物品
        player_inv.slots[equip_slot] = item_instance
        
        # 如果是背包/腰袋，刷新网格
        if equip_slot in ("backpack", "waist"):
            if not player_inv.refresh_backpack_grid():
                # 刷新失败 → 回滚
                player_inv.slots[equip_slot] = old_item
                container.backpack_slots[ground_idx] = {"item": item_instance, "stack": 1}
                renpy.notify("背包内物品太多，无法更换此装备！")
                return
        
        # 如果有旧装备，放入地面容器（避免放回同一格）
        if old_item is not None:
            # 先临时占位，防止 add_item 把旧装备放回刚清空的格子
            container.backpack_slots[ground_idx] = {"item": old_item, "stack": 1}
            # 找一个真正的空格子
            empty_idx = -1
            for i in range(len(container.backpack_slots)):
                if container.backpack_slots[i] is None:
                    empty_idx = i
                    break
            # 取消临时占位
            container.backpack_slots[ground_idx] = None
            if empty_idx != -1:
                container.backpack_slots[empty_idx] = {"item": old_item, "stack": 1}
            else:
                container.add_item(old_item)
            renpy.notify(f"已装备 {item_instance.config.name}，旧装备已放入地面。")
        else:
            renpy.notify(f"已装备 {item_instance.config.name}。")
        
        # 更新攻击模式（如果是武器）
        if equip_slot == "right_hand":
            player_inv.update_player_attack_modes()
        
        # 同步赤脚状态
        if equip_slot in ("left_foot", "right_foot"):
            if player_inv.is_barefoot():
                player_stats.add_condition(COND_BARE_FOOT)
            else:
                player_stats.remove_condition(COND_BARE_FOOT)


screen scr_ground_container(container, player_inv):
    modal True
    zorder 100
    tag ground_container

    # ── 状态变量 ──
    default selected_ground_idx = None
    default selected_player_idx = None
    default hovered_ground_idx = None  
    default hovered_player_idx = None  
    default ground_context_menu_slot = None
    default ground_context_menu_pos = (0, 0)

    add Solid("#0f0f0f") xsize config.screen_width ysize config.screen_height

    frame:
        xalign 0.5 yalign 0.5
        xsize int(config.screen_width * 0.92)
        ysize int(config.screen_height * 0.88)
        background Solid("#111111")
        padding (24, 24)

        vbox:
            spacing 10
            xfill True
            text "当前地上的物品" size 30 color "#ffee88" xalign 0.5
            text "左侧：取回地上的物品。右侧：背包内物品可点击丢弃到地上。" size 18 color "#cccccc" xalign 0.5

            hbox:
                spacing 16
                xalign 0.5

                # ════════════ 左侧：地面容器 ════════════
                vbox:
                    spacing 8
                    text "地上的物品" size 24 color "#ffee88" xalign 0.0

                    frame:
                        xsize 950
                        ysize 700
                        background Solid("#202020")
                        padding (12, 12)

                        vpgrid:
                            cols 8
                            spacing 2
                            xfill True
                            ysize 670
                            scrollbars "vertical"
                            mousewheel True
                            draggable True

                            for i in range(128):
                                $ slot = container.backpack_slots[i] if i < len(container.backpack_slots) else None
                                $ selected = (selected_ground_idx == i)
                                $ hovered = (hovered_ground_idx == i)
                                
                                # 【优化后的动态颜色逻辑】
                                if hovered:
                                    $ ground_border_color = "#ffffffa1"      # 鼠标悬停：白色
                                elif selected and slot is not None:        # 【修改】只有格子内有物品被选中时才变绿
                                    $ ground_border_color = "#66bb6a"      # 点击选中：绿色
                                else:
                                    $ ground_border_color = "#282828"      # 默认/空格子选中：暗色

                                if slot is not None:
                                    $ item = slot["item"]

                                    frame:
                                        xsize 110 ysize 110
                                        background Solid(ground_border_color) 
                                        xpadding 2 ypadding 2

                                        frame:
                                            xfill True yfill True
                                            background Solid("#1a1a1a")

                                            button:
                                                xfill True yfill True
                                                background None
                                                action If(
                                                    selected_player_idx is not None,
                                                    [
                                                        Function(move_selected_backpack_item_to_ground, i, selected_player_idx, container, player_inv),
                                                        SetScreenVariable("selected_ground_idx", None),
                                                        SetScreenVariable("selected_player_idx", None)
                                                    ],
                                                    If(
                                                        selected_ground_idx == i,
                                                        SetScreenVariable("selected_ground_idx", None),
                                                        If(
                                                            selected_ground_idx is not None,
                                                            [
                                                                Function(swap_ground_slots, i, selected_ground_idx, container),
                                                                SetScreenVariable("selected_ground_idx", None)
                                                            ],
                                                            [SetScreenVariable("selected_ground_idx", i), SetScreenVariable("selected_player_idx", None)]
                                                        )
                                                    )
                                                )
                                                # 右键菜单触发（有物品时右键打开菜单）
                                                if slot is not None:
                                                    alternate [
                                                        SetScreenVariable("ground_context_menu_slot", 1000 + i),  # 地面容器索引偏移
                                                        SetScreenVariable("ground_context_menu_pos", renpy.get_mouse_pos()),
                                                        Hide("tooltip_delay_timer"),
                                                        Hide("floating_tooltip")
                                                    ]
                                                if slot is not None:
                                                    hovered [SetScreenVariable("hovered_ground_idx", i), Show("tooltip_delay_timer", text=item.config.desc)]
                                                else:
                                                    hovered SetScreenVariable("hovered_ground_idx", i)
                                                    
                                                unhovered [SetScreenVariable("hovered_ground_idx", None), Hide("tooltip_delay_timer"), Hide("floating_tooltip")]

                                                fixed:
                                                    if item.icon_path:
                                                        add item.icon_path size (80, 80) xpos 0.5 ypos 0.5 xanchor 0.5 yanchor 0.5
                                                    else:
                                                        add Solid("#444444") size (80, 80) xpos 0.5 ypos 0.5 xanchor 0.5 yanchor 0.5

                                                    text item.config.name size 12 color "#ffffff" xpos 0.5 ypos 0.5 xanchor 0.0 yanchor 0.0 xoffset -40 yoffset -40 outlines [(1, "#000000")]
                                                    if slot["stack"] > 1:
                                                        text f"×{slot['stack']}" size 12 color "#ffcc00" xpos 0.5 ypos 0.5 xanchor 1.0 yanchor 1.0 xoffset 40 yoffset 40 outlines [(1, "#000000")]
                                else:
                                    frame:
                                        xsize 110 ysize 110
                                        background Solid(ground_border_color) 
                                        xpadding 2 ypadding 2

                                        frame:
                                            xfill True yfill True
                                            background Solid("#1a1a1a")

                                            button:
                                                xfill True yfill True
                                                background None
                                                action If(
                                                    selected_player_idx is not None,
                                                    [
                                                        Function(move_selected_backpack_item_to_ground, i, selected_player_idx, container, player_inv),
                                                        SetScreenVariable("selected_ground_idx", None),
                                                        SetScreenVariable("selected_player_idx", None)
                                                    ],
                                                    If(
                                                        selected_ground_idx is not None,
                                                        [
                                                            Function(swap_ground_slots, i, selected_ground_idx, container),
                                                            SetScreenVariable("selected_ground_idx", None)
                                                        ],
                                                        SetScreenVariable("selected_ground_idx", i)
                                                    )
                                                )
                                                hovered SetScreenVariable("hovered_ground_idx", i)
                                                unhovered SetScreenVariable("hovered_ground_idx", None)

                # ════════════ 右侧：你的背包 ════════════
                vbox:
                    spacing 8
                    text "你的背包" size 24 color "#88ccff" xalign 1.0
                    frame:
                        xsize 700
                        ysize 580
                        background Solid("#202020")
                        padding (12, 12)

                        grid player_inv.backpack_width player_inv.backpack_height:
                            spacing 2
                            for i in range(player_inv.max_slots):
                                $ slot = player_inv.backpack_slots[i]  # 【调整位置】先获取 slot 实例
                                $ selected = (selected_player_idx == i)
                                $ hovered = (hovered_player_idx == i)
                                
                                # 【优化后的动态颜色逻辑】
                                if hovered:
                                    $ player_border_color = "#ffffffa1"     # 鼠标悬停：白色
                                elif selected and slot is not None:         # 【修改】只有格子内有物品被选中时才变绿
                                    $ player_border_color = "#66bb6a"       # 点击选中：绿色
                                else:
                                    $ player_border_color = "#282828"       # 默认/空格子选中：暗色

                                if slot is not None:
                                    $ item = slot["item"]

                                    frame:
                                        xsize 110 ysize 110
                                        background Solid(player_border_color) 
                                        xpadding 2 ypadding 2

                                        frame:
                                            xfill True yfill True
                                            background Solid("#1a1a1a")

                                            button:
                                                xfill True yfill True
                                                background None
                                                action If(
                                                    selected_ground_idx is not None,
                                                    [
                                                        Function(move_selected_ground_item_to_backpack, i, selected_ground_idx, container, player_inv),
                                                        SetScreenVariable("selected_ground_idx", None),
                                                        SetScreenVariable("selected_player_idx", None)
                                                    ],
                                                    If(
                                                        selected_player_idx == i,
                                                        SetScreenVariable("selected_player_idx", None),
                                                        [SetScreenVariable("selected_player_idx", i), SetScreenVariable("selected_ground_idx", None)]
                                                    )
                                                )
                                                # 右键菜单触发（有物品时右键打开菜单）
                                                if slot is not None:
                                                    alternate [
                                                        SetScreenVariable("ground_context_menu_slot", i),
                                                        SetScreenVariable("ground_context_menu_pos", renpy.get_mouse_pos()),
                                                        Hide("tooltip_delay_timer"),
                                                        Hide("floating_tooltip")
                                                    ]
                                                if slot is not None:
                                                    hovered [SetScreenVariable("hovered_player_idx", i), Show("tooltip_delay_timer", text=item.config.desc)]
                                                else:
                                                    hovered SetScreenVariable("hovered_player_idx", i)
                                                    
                                                unhovered [SetScreenVariable("hovered_player_idx", None), Hide("tooltip_delay_timer"), Hide("floating_tooltip")]

                                                fixed:
                                                    if item.icon_path:
                                                        add item.icon_path size (80, 80) xpos 0.5 ypos 0.5 xanchor 0.5 yanchor 0.5
                                                    else:
                                                        add Solid("#444444") size (80, 80) xpos 0.5 ypos 0.5 xanchor 0.5 yanchor 0.5

                                                    text item.config.name size 12 color "#ffffff" xpos 0.5 ypos 0.5 xanchor 0.0 yanchor 0.0 xoffset -40 yoffset -40 outlines [(1, "#000000")]
                                                    if slot["stack"] > 1:
                                                        text f"×{slot['stack']}" size 12 color "#ffcc00" xpos 0.5 ypos 0.5 xanchor 1.0 yanchor 1.0 xoffset 40 yoffset 40 outlines [(1, "#000000")]
                                else:
                                    frame:
                                        xsize 110 ysize 110
                                        background Solid(player_border_color) 
                                        xpadding 2 ypadding 2

                                        frame:
                                            xfill True yfill True
                                            background Solid("#1a1a1a")

                                            button:
                                                xfill True yfill True
                                                background None
                                                action If(
                                                    selected_ground_idx is not None,
                                                    [
                                                        Function(move_selected_ground_item_to_backpack, i, selected_ground_idx, container, player_inv),
                                                        SetScreenVariable("selected_ground_idx", None),
                                                        SetScreenVariable("selected_player_idx", None)
                                                    ],
                                                    If(
                                                        selected_player_idx == i,
                                                        SetScreenVariable("selected_player_idx", None),
                                                        If(
                                                            selected_player_idx is not None,
                                                            [
                                                                Function(swap_backpack_slots, i, selected_player_idx, player_inv),
                                                                SetScreenVariable("selected_player_idx", None)
                                                            ],
                                                            [SetScreenVariable("selected_player_idx", i), SetScreenVariable("selected_ground_idx", None)]
                                                        )
                                                    )
                                                )
                                                hovered SetScreenVariable("hovered_player_idx", i)
                                                unhovered SetScreenVariable("hovered_player_idx", None)

            # ── 底部控制 ──
            hbox:
                spacing 16
                xalign 0.5
                textbutton "关闭":
                    action Hide("scr_ground_container")
                    style "button"

    # ── 右键菜单模块（地面/背包物品操作） ──
    if ground_context_menu_slot is not None:
  
        # 全屏透明遮罩按钮（点击空白处关闭菜单）
        button:
            background None
            xfill True
            yfill True
            action SetScreenVariable("ground_context_menu_slot", None)

        # 判断是地面容器还是背包的右键
        $ is_ground_slot = (ground_context_menu_slot >= 1000)
        $ real_idx = ground_context_menu_slot - 1000 if is_ground_slot else ground_context_menu_slot
        $ slot = container.backpack_slots[real_idx] if is_ground_slot else player_inv.backpack_slots[real_idx]
        if slot is not None:
            $ item = slot["item"]
            $ stack = slot["stack"]

            # 菜单浮窗
            frame:
                xsize 140  
                background Solid("#222222")
                xpadding 10
                ypadding 10
                xpos ground_context_menu_pos[0]
                ypos ground_context_menu_pos[1]

                vbox:
                    spacing 8  

                    text item.config.name size 16 color "#ffffff" xalign 0.5  

                    # 装备按钮：检查物品是否能装备到某个槽位
                    $ equip_slot_name = None
                    python:
                        for es in item.config.equip_slots:
                            if es in player_inv.slots:
                                equip_slot_name = es
                                break
                    if equip_slot_name:
                        if is_ground_slot:
                            textbutton _("装备"):
                                text_size 14
                                xfill True
                                text_xalign 0.5
                                ypadding 6
                                background Solid("#333333")
                                hover_background Solid("#555555")
                                action [
                                    Function(equip_item_from_ground, item, player_inv, real_idx, container),
                                    SetScreenVariable("ground_context_menu_slot", None),
                                    Show("scr_ground_container", container=container, player_inv=player_inv)
                                ]
                        else:
                            textbutton _("装备"):
                                text_size 14
                                xfill True
                                text_xalign 0.5
                                ypadding 6
                                background Solid("#333333")
                                hover_background Solid("#555555")
                                action [
                                    Function(equip_item_from_backpack_in_ground_ui, real_idx, equip_slot_name, player_inv),
                                    SetScreenVariable("ground_context_menu_slot", None),
                                    Show("scr_ground_container", container=container, player_inv=player_inv)
                                ]

                    # 分离按钮：堆叠数 > 1 时才显示（仅背包物品可分离）
                    if stack > 1 and not is_ground_slot:
                        textbutton _("分离"):
                            text_size 14
                            xfill True
                            text_xalign 0.5
                            ypadding 6
                            background Solid("#333333")
                            hover_background Solid("#555555")
                            action [
                                Function(split_item_stack, item, player_inv, real_idx),
                                SetScreenVariable("ground_context_menu_slot", None),
                                Show("scr_ground_container", container=container, player_inv=player_inv)
                            ]

                    # 地面物品 → 拿取；背包物品 → 丢弃
                    if is_ground_slot:
                        textbutton _("拿取"):
                            text_size 14
                            xfill True
                            text_xalign 0.5                 
                            ypadding 6                      
                            background Solid("#333333")       
                            hover_background Solid("#555555") 
                            action [
                                Function(take_item_from_ground_to_player, item, container, player_inv),
                                SetScreenVariable("ground_context_menu_slot", None),
                                Show("scr_ground_container", container=container, player_inv=player_inv)
                            ]
                    else:
                        textbutton _("丢弃"):
                            text_size 14
                            xfill True
                            text_xalign 0.5                 
                            ypadding 6                      
                            background Solid("#333333")       
                            hover_background Solid("#555555") 
                            action [
                                Function(ui_action_drop_item, item, player_inv),
                                SetScreenVariable("ground_context_menu_slot", None),
                                Show("scr_ground_container", container=container, player_inv=player_inv)
                            ]
                    
                    # 合并按钮：检查是否有同类未满的格子（仅背包物品可合并）
                    $ merge_found = False
                    $ merge_target_idx = -1
                    if stack < item.config.max_stack and not is_ground_slot:
                        python:
                            for j in range(player_inv.max_slots):
                                if j != real_idx:
                                    s = player_inv.backpack_slots[j]
                                    if s is not None and s["item"].id == item.id and s["stack"] < item.config.max_stack:
                                        merge_found = True
                                        merge_target_idx = j
                                        break
                    if merge_found:
                        textbutton _("合并"):
                            text_size 14
                            xfill True
                            text_xalign 0.5
                            ypadding 6
                            background Solid("#333333")
                            hover_background Solid("#555555")
                            action [
                                Function(merge_item_stack, player_inv, real_idx, merge_target_idx),
                                SetScreenVariable("ground_context_menu_slot", None),
                                Show("scr_ground_container", container=container, player_inv=player_inv)
                            ]

                    # 取消按钮：关闭菜单
                    textbutton _("取消"):
                        text_size 14
                        xfill True
                        text_xalign 0.5                 
                        ypadding 6                      
                        background Solid("#333333")       
                        hover_background Solid("#555555") 
                        action SetScreenVariable("ground_context_menu_slot", None)