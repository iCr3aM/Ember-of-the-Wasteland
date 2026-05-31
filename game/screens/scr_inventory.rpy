# =============================================================================
# # 定义：背包交互界面、装备纸娃娃系统界面。
# # 实现：渲染槽位和格子，支持玩家用鼠标拖拽物品（换装、丢弃）、点击右键弹出“搜索尸体”的上下文菜单。
# =============================================================================
# 修改背包屏幕的声明头部，赋予其默认单例

screen scr_inventory(inv_instance=player_inventory):
    tag inventory
    zorder 100
    modal True
    add Solid("#202020") xsize 1920 ysize 1080 # 全屏背包控制底图

    $ in_combat = is_in_active_combat()
    if in_combat:
        text "提示：所有操作完成后，请点击\"关闭背包\"退出" xalign 0.5 yalign 0.1 size 18 color "#ffeb3b"

    $ can_interact = is_player_turn_available()
    
    if not can_interact and in_combat and _current_combat_instance.player_turn_disabled_by_inventory:
        text "你本回合已因操作背包而无法行动" xalign 0.5 yalign 0.10 size 20 color "#ffcc00"
    
    text "你的背包和装备" xalign 0.5 yalign 0.15 size 28 color "#d1c4e9"
    
    # === 装备栏（人体结构布局） ===
    # 每个槽位的屏幕坐标 (xpos, ypos) 可根据实际分辨率微调
    $ slot_positions = {
        "hat":          (0.15, 0.10),
        "neck":         (0.15, 0.22),
        "torso":        (0.15, 0.34),
        "left_hand":    (0.08, 0.34),
        "left_wrist":   (0.08, 0.46),
        "right_hand":   (0.22, 0.34),
        "right_wrist":  (0.22, 0.46),
        "legs":         (0.15, 0.56),
        "left_foot":    (0.08, 0.62),
        "right_foot":   (0.22, 0.62),
        "left_ankle":   (0.08, 0.74),
        "right_ankle":  (0.22, 0.74),
    }

    for slot_name, pos in slot_positions.items():
        $ current_item = inv_instance.slots.get(slot_name)
        frame:
            xpos pos[0] ypos pos[1]
            xsize 120 ysize 120
            background Solid("#303030")
            
            if current_item:
                # 透明按钮，专门负责监听鼠标悬停并调用当前装备的描述
                button:
                    align (0.5, 0.5)
                    background None
                    action NullAction()
                    hovered Show("tooltip_delay_timer", text=current_item.config.desc)
                    unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                    
                    vbox:
                        align (0.5, 0.5)
                        $ icon = current_item.icon_path
                        if icon:
                            add icon size (80, 80)
                        else:
                            text "?" size 40 color "#888888" align (0.5, 0.5)
                        text current_item.config.name size 12 xalign 0.5
                        
                # 耐久显示
                text f"耐久:{current_item.durability*100:.0f}%" size 12 color "#4caf50" xpos 1.0 ypos 0.0 xanchor 1.0 yanchor 0.0
                # 卸下按钮（条件与之前一致）
                if can_interact:
                    button:
                        style "button"
                        xpadding 4 ypadding 2
                        action [
                            Function(disable_player_turn_in_combat),
                            Function(inv_instance.unequip_item, slot_name),
                            Show("scr_inventory", inv_instance=inv_instance)
                        ]
                        text "卸下" size 12
            else:
                text slot_name.upper() align (0.5, 0.5) size 12 color "#555555"

    # === 背包网格 ===
    frame:
        xpos 0.42 ypos 0.20
        xsize 750 ysize 650
        background Solid("#181818")
        padding (15, 15)
        
        grid 5 4:
            spacing 10
            for i in range(inv_instance.max_slots):  
                if i < len(inv_instance.backpack_slots):
                    $ slot = inv_instance.backpack_slots[i]
                    $ item = slot["item"]
                    $ stack = slot["stack"]
                    frame:
                        xsize 130 ysize 140
                        background Solid("#282828")
                        fixed:
                            # 耐久显示在右上角
                            if item.durability < 1.0 or item.config.max_durability > 0:
                                $ durability_pct = item.durability * 100
                                if durability_pct < 100:
                                    text f"耐久:{durability_pct:.0f}%" size 12 color "#4caf50" xpos 1.0 ypos 0.0 xanchor 1.0 yanchor 0.0
                            
                            # 居中内容
                            # 透明按钮，专门负责监听鼠标悬停并调用背包物品的描述
                            button:
                                align (0.5, 0.5)
                                background None
                                action NullAction()
                                hovered Show("tooltip_delay_timer", text=item.config.desc)
                                unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                                
                                vbox:
                                    align (0.5, 0.5)
                                    $ icon = item.icon_path
                                    if icon:
                                        add icon size (80, 80)
                                    else:
                                        text f"{item.id}" size 28 color "#555555" align (0.5, 0.5)
                                    hbox:
                                        xalign 0.5
                                        spacing 5
                                        text item.config.name size 12
                                        if stack > 1:
                                            text f"×{stack}" size 14 color "#ffcc00"
                            
                            # 操作按钮 - 底部
                            hbox:
                                xfill True
                                ypos 1.0 yanchor 1.0
                                spacing 0
                                # 左侧：使用和装配
                                hbox:
                                    xalign 0.0
                                    spacing 3
                                    if item.id in ITEM_USE_FUNCTIONS:
                                        $ can_use_in_combat = is_player_turn_available()
                                        if can_use_in_combat:
                                            textbutton "使用":
                                                text_size 12
                                                xpadding 4 ypadding 2
                                                action [
                                                    Function(use_item_and_refresh_screen, item, inv_instance, actor=_current_combat_instance.player if in_combat else None),
                                                    Show("scr_inventory", inv_instance=inv_instance)
                                                ]
                                    if item.config.equip_slots and can_interact:
                                        textbutton "装配":
                                            text_size 12
                                            xpadding 4 ypadding 2
                                            action [
                                                Function(disable_player_turn_in_combat),
                                                Function(inv_instance.move_to_equip, item, item.config.equip_slots[0] if item.config.equip_slots else None),
                                                Show("scr_inventory", inv_instance=inv_instance)
                                            ]
                                # 右侧：丢弃
                                if can_interact:
                                    hbox:
                                        xalign 1.0
                                        textbutton "丢弃":
                                            text_size 12
                                            xpadding 4 ypadding 2
                                            action [
                                                Function(disable_player_turn_in_combat),
                                                Function(inv_instance.remove_item, item),
                                                Show("scr_inventory", inv_instance=inv_instance)
                                            ]
                else:
                    # 空格子
                    frame:
                        xsize 130 ysize 140
                        background Solid("#1a1a1a")
                        text "空" align (0.5, 0.5) size 14 color "#444444"

    # === 关闭按钮 ===
    textbutton "关闭背包":
        xalign 0.5 ypos 0.93
        # 关闭背包的同时，强制隐藏可能正在倒计时的计时器以及浮窗
        action [Hide("scr_inventory"), Hide("tooltip_delay_timer"), Hide("floating_tooltip")] 
        style "button"