# =============================================================================
# scr_inventory.rpy — 背包与纸娃娃装备界面
# 功能：渲染 5×4 固定网格背包 + 12 槽位人体装备栏
# 交互：点击选择 + 悬停高亮，支持物品移动、装备/卸下、使用/丢弃
# =============================================================================
screen scr_inventory(inv_instance=player_inventory):
    tag inventory
    zorder 100
    modal True
    
    # ── 悬停状态（屏幕级变量，每次打开自动重置） ──
    default hovered_bp_idx = None
    default hovered_eq_slot = None
    default inventory_context_menu_slot = None
    default inventory_context_menu_pos = (0, 0)

    add Solid("#202020") xsize 1920 ysize 1080 

    # ── 战斗状态提示 ──
    $ in_combat = is_in_active_combat()

    $ can_interact = is_player_turn_available()
    if not can_interact and in_combat and _current_combat_instance.player_turn_disabled_by_inventory:
        text "你本回合已因操作背包而无法行动，请关闭背包结束回合" xalign 0.5 yalign 0.10 size 20 color "#ffcc00"
    
    text "你的背包和装备" xalign 0.5 yalign 0.15 size 28 color "#d1c4e9"
    
    # ── 装备栏（人体结构布局） ──
    $ slot_positions = {
        "hat": (0.15, 0.10), "neck": (0.15, 0.22), "torso": (0.15, 0.34),
        "left_hand": (0.08, 0.34), "left_wrist": (0.08, 0.46),
        "right_hand": (0.22, 0.34), "right_wrist": (0.22, 0.46),
        "legs": (0.15, 0.56), "left_foot": (0.08, 0.62),
        "right_foot": (0.22, 0.62), "left_ankle": (0.08, 0.74), "right_ankle": (0.22, 0.74),
        "backpack": (0.32, 0.34), "waist": (0.32, 0.46),
    }

    # ── 装备栏位中文显示名 ──
    $ slot_names_cn = {
        "hat": "头部", "neck": "颈部", "torso": "躯干",
        "left_hand": "左手", "left_wrist": "左手腕",
        "right_hand": "右手", "right_wrist": "右手腕",
        "legs": "腿部", "left_foot": "左脚",
        "right_foot": "右脚", "left_ankle": "左脚踝", "right_ankle": "右脚踝",
        "backpack": "背包", "waist": "腰部",
    }

    for slot_name, pos in slot_positions.items():
        $ current_item = inv_instance.slots.get(slot_name)
        $ is_self_selected = (_selected_type == "equip" and _selected_id == slot_name)
    
        # 检查选中的背包物品是否能装备到此槽位
        $ is_compatible = False
        if _selected_type == "backpack" and _selected_id is not None:
            $ sel_slot = inv_instance.backpack_slots[_selected_id]
            if sel_slot is not None:
                $ is_compatible = slot_name in sel_slot["item"].config.equip_slots

        # 高亮条件：自身被选中，或鼠标悬停在可装备的槽位上
        $ show_eq_highlight = is_self_selected or (is_compatible and hovered_eq_slot == slot_name)
        $ eq_bg = "#4caf50" if show_eq_highlight else "#303030"

        frame:
            xpos pos[0] ypos pos[1]
            xsize 120 ysize 120
            background Solid(eq_bg)
            xpadding 3 ypadding 3 # 固定边距，使内部按钮尺寸恒定不变
            
            frame:
                background Solid("#303030")
                xfill True yfill True
                
                button:
                    xfill True yfill True
                    background None
                    # 如果不能交互（已经执行过动作），则不赋予任何 action，按钮会自动变成不可点击的禁用状态
                    if can_interact:
                        action [
                            Function(click_equip_slot, slot_name),
                            # 判定：如果是从背包装备进来的动作，在战斗中则立即禁用后续操作
                            If(_selected_type == "backpack" and in_combat, Function(disable_player_turn_in_combat), NullAction())
                        ]
                    else:
                        action None
                        
                    # 有物品时显示描述提示，无物品时只更新悬停状态
                    if current_item:
                        hovered [SetScreenVariable("hovered_eq_slot", slot_name), Show("tooltip_delay_timer", text=current_item.config.desc)]
                    else:
                        hovered SetScreenVariable("hovered_eq_slot", slot_name)
                        
                    unhovered [SetScreenVariable("hovered_eq_slot", None), Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                    
                    if current_item:
                        fixed: # 用 fixed 包裹，方便进行局部的绝对定位
                            vbox:
                                align (0.5, 0.5)
                                if current_item.icon_path:
                                    add current_item.icon_path size (80, 80)
                                else:
                                    text "?" size 40 color "#888888"
                                text current_item.config.name size 12 xalign 0.5
                            
                            # 【保持】当装备栏耐久度不满 100% 时，在格子「左上角」显示耐久
                            if current_item.durability < 1.0:
                                text f"{current_item.durability*100:.0f}%" size 11 color "#4caf50" xpos 0.0 ypos 0.0 xanchor 0.0 yanchor 0.0 outlines [(1, "#000000")]
                    else:
                        if is_compatible:
                            text "可装备" align (0.5, 0.5) size 14 color "#aaffaa"
                        else:
                            text slot_names_cn.get(slot_name, slot_name) align (0.5, 0.5) size 12 color "#555555"

    # ── 背包网格 ──
    frame:
        xpos 0.50 ypos 0.25
        xsize 700 ysize 600
        background Solid("#181818")
        padding (15, 15)

        grid inv_instance.backpack_width inv_instance.backpack_height:
            spacing 3
            for i in range(inv_instance.max_slots):
                $ slot = inv_instance.backpack_slots[i]
                $ item = slot["item"] if slot is not None else None
                $ stack = slot["stack"] if slot is not None else 0
            
                # ── 状态判断 ──
                $ is_self_selected = (_selected_type == "backpack" and _selected_id == i)
                $ is_hovered = (hovered_bp_idx == i) # 鼠标当前是否悬停在此格
                
                # ── 动态方框高亮逻辑 ──
                if is_hovered:
                    $ bp_border_color = "#ffffff"     # 鼠标悬停：亮白色高亮方框
                elif is_self_selected:
                    $ bp_border_color = "#66bb6a"     # 点击选中：绿色高亮方框
                else:
                    $ bp_border_color = "#282828"     # 默认状态：暗色无高亮

                frame:
                    xsize 110 ysize 110
                    background Solid(bp_border_color) # 应用高亮方框颜色
                    xpadding 2
                    ypadding 2

                    frame:
                        xfill True
                        yfill True
                        background Solid("#1a1a1a")

                        button:
                            xfill True
                            yfill True
                            background None
                            # 如果无法交互，背包格子也不能被点击选中/移动
                            if can_interact:
                                action Function(click_backpack_slot, i)
                            else:
                                action None
                        
                            # 右键菜单触发（同样受到交互限制保护）
                            if item is not None and can_interact:
                                alternate [
                                    SetScreenVariable("inventory_context_menu_slot", i),
                                    SetScreenVariable("inventory_context_menu_pos", renpy.get_mouse_pos()),
                                    Hide("tooltip_delay_timer"),
                                    Hide("floating_tooltip")
                                ]
                        
                            # 悬停状态更新
                            if item is not None:
                                hovered [SetScreenVariable("hovered_bp_idx", i), Show("tooltip_delay_timer", text=item.config.desc)]
                            else:
                                hovered SetScreenVariable("hovered_bp_idx", i)
                                
                            unhovered [SetScreenVariable("hovered_bp_idx", None), Hide("tooltip_delay_timer"), Hide("floating_tooltip")]

                            if slot is not None:
                                fixed:
                                    if item.icon_path:
                                        add item.icon_path size (80, 80) xpos 0.5 ypos 0.5 xanchor 0.5 yanchor 0.5
                                    else:
                                        add Solid("#444444") size (80, 80) xpos 0.5 ypos 0.5 xanchor 0.5 yanchor 0.5

                                    text item.config.name size 12 color "#ffffff" xpos 0.5 ypos 0.5 xanchor 0.0 yanchor 0.0 xoffset -40 yoffset -40 outlines [(1, "#000000")]
                                    if stack > 1:
                                        text f"×{stack}" size 12 color "#ffcc00" xpos 0.5 ypos 0.5 xanchor 1.0 yanchor 1.0 xoffset 40 yoffset 40 outlines [(1, "#000000")]
                                    
                                    # 背包内依然保持在「左下角」显示耐久度百分比
                                    if getattr(item, "durability", 1.0) < 1.0:
                                        text f"{item.durability*100:.0f}%" size 11 color "#4caf50" xpos 0.0 ypos 1.0 xanchor 0.0 yanchor 1.0 outlines [(1, "#000000")]
                            else:
                                null

    # ── 右键菜单模块 ──
    if inventory_context_menu_slot is not None:
  
        # 全屏透明遮罩按钮
        button:
            background None
            xfill True
            yfill True
            action SetScreenVariable("inventory_context_menu_slot", None)

        $ slot = inv_instance.backpack_slots[inventory_context_menu_slot]
        if slot is not None:
            $ item = slot["item"]
            $ stack = slot["stack"]

            # 真正的菜单渲染
            frame:
                xsize 140  
                background Solid("#222222")
                xpadding 10
                ypadding 10
                xpos inventory_context_menu_pos[0]
                ypos inventory_context_menu_pos[1]

                vbox:
                    spacing 8  

                    text item.config.name size 16 color "#ffffff" xalign 0.5  

                    if item.id in ITEM_USE_FUNCTIONS:
                        textbutton _("使用"):
                            text_size 14
                            xfill True
                            text_xalign 0.5             
                            ypadding 6                  
                            background Solid("#333333")       
                            hover_background Solid("#555555") 
                            # 当使用物品时，如果在战斗中，立刻给战斗实例打上禁用标记
                            action [
                                Function(use_item_and_refresh_screen, item, inv_instance, actor=_current_combat_instance.player if in_combat else None),
                                If(in_combat, Function(disable_player_turn_in_combat), NullAction()),
                                SetScreenVariable("inventory_context_menu_slot", None),
                                Show("scr_inventory", inv_instance=inv_instance)
                            ]

                    if stack > 1:
                        textbutton _("分离"):
                            text_size 14
                            xfill True
                            text_xalign 0.5
                            ypadding 6
                            background Solid("#333333")
                            hover_background Solid("#555555")
                            action [
                                Function(split_item_stack, item, inv_instance, inventory_context_menu_slot),
                                SetScreenVariable("inventory_context_menu_slot", None),
                                Show("scr_inventory", inv_instance=inv_instance)
                            ]

                    textbutton _("丢弃"):
                        text_size 14
                        xfill True
                        text_xalign 0.5                 
                        ypadding 6                      
                        background Solid("#333333")       
                        hover_background Solid("#555555") 
                        action [
                            # 已移除 If(in_combat, ...) 的禁用回合逻辑，丢弃现在是“自由动作”
                            # 替换为安全的 ui_action_drop_item，不再返回 True/False 导致屏幕崩溃
                            Function(ui_action_drop_item, item, inv_instance),
                            SetScreenVariable("inventory_context_menu_slot", None),
                            Show("scr_inventory", inv_instance=inv_instance)
                        ]
                    
                    # 检查是否有可合并的同类物品（当前格子未满才显示合并）
                    $ merge_found = False
                    $ merge_target_idx = -1
                    if stack < item.config.max_stack:
                        python:
                            for j in range(inv_instance.max_slots):
                                if j != inventory_context_menu_slot:
                                    s = inv_instance.backpack_slots[j]
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
                                Function(merge_item_stack, inv_instance, inventory_context_menu_slot, merge_target_idx),
                                SetScreenVariable("inventory_context_menu_slot", None),
                                Show("scr_inventory", inv_instance=inv_instance)
                            ]

                    textbutton _("取消"):
                        text_size 14
                        xfill True
                        text_xalign 0.5                 
                        ypadding 6                      
                        background Solid("#333333")       
                        hover_background Solid("#555555") 
                        action SetScreenVariable("inventory_context_menu_slot", None)

    # ── 关闭按钮 ──
    textbutton "关闭背包":
        xalign 0.5 ypos 0.93
        # 【修改】关闭背包时，如果是战斗中且已经触发了背包锁死标记，返回后会自动执行战斗大后方的回合推进。
        action [
            Hide("scr_inventory"), 
            Hide("tooltip_delay_timer"), 
            Hide("floating_tooltip")
        ] 
        style "button"