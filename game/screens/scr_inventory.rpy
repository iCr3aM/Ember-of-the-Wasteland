# =============================================================================
# # 定义：背包交互界面、装备纸娃娃系统界面。
# # 实现：渲染槽位和格子，支持玩家用鼠标拖拽物品（换装、丢弃）、点击右键弹出“搜索尸体”的上下文菜单。
# =============================================================================
# 修改背包屏幕的声明头部，赋予其默认单例
screen scr_inventory(inv_instance=player_inventory):
    modal True
    # ... 你的网格化渲染背包逻辑 ...
    add Solid("#202020") xsize 1280 ysize 720 # 全屏背包控制底图
    
    # 标题
    text "你的背包和装备" xalign 0.5 yalign 0.05 size 28 color "#d1c4e9"
    
    # 左侧：身体装备纸娃娃插槽区
    grid 2 3:
        xpos 0.1 ypos 0.2
        spacing 20
        for slot_name in ["head", "torso", "legs", "feet", "left_hand", "right_hand"]:
            $ current_item = inv_instance.slots[slot_name]
            frame:
                xsize 130 ysize 130
                # 动态分配特定纸娃娃插槽背景阴影图
                background Solid("#303030")
                
                if current_item:
                    vbox:
                        align (0.5, 0.5)
                        add current_item.icon_path size (90, 90)
                        text current_item.config.name size 12 text_align 0.5
                        text f"耐:{current_item.durability*100:.0f}%" size 10 color "#4caf50"
                        # 右键/点击解除装备
                        button:
                            style "button"
                            action [Function(inv_instance.add_item, current_item), SetDict(inv_instance.slots, slot_name, None)]
                            text "卸下" size 12
                else:
                    text slot_name.upper() align (0.5, 0.5) size 14 color "#555555"

    # 右侧：传统网格化自由流转背包层
    frame:
        xpos 0.5 ypos 0.2
        xsize 550 ysize 500
        background Solid("#181818")
        padding (15, 15)
        
        vpgrid:
            cols 4
            spacing 15
            scrollbars "vertical"
            mousewheel True
            
            for item in inv_instance.backpack_grid:
                frame:
                    xsize 110 ysize 130
                    background Solid("#282828")
                    vbox:
                        align (0.5, 0.5)
                        add item.icon_path size (80, 80)
                        text item.config.name size 12 xalign 0.5
                        
                        # 点击展开交互上下文菜单菜单
                        hbox:
                            xalign 0.5
                            spacing 5
                            # 如果物品有定义用途效果，显示"使用"按钮
                            if item.id in ITEM_USE_FUNCTIONS:
                                textbutton "使用":
                                    text_size 11
                                    action Function(use_item_and_refresh_screen, item, inv_instance)
                            if item.config.equip_slots:
                                textbutton "装配":
                                    text_size 11
                                    action [Function(inv_instance.equip_item, item, item.config.equip_slots[0]), Function(inv_instance.backpack_grid.remove, item)]
                            textbutton "丢弃":
                                text_size 11
                                action Function(inv_instance.backpack_grid.remove, item)

    # 关闭按钮
    textbutton "关闭面板":
        xalign 0.5 ypos 0.88
        action Hide("scr_inventory")
        style "button"