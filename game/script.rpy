# =============================================================================
# # 定义：游戏全局入口、初始标签（label start）、开发调试菜单（Dev Menu）。
# # 实现：调用各个系统的初始化流程，重定向至序幕（prologue）；提供一键刷物品/怪物的测试工具。
# =============================================================================

init python:
    def debug_add_test_items():
        """将测试物品加入玩家背包。"""
        player_inventory.add_item_by_id(101)
        player_inventory.add_item_by_id(102)
        player_inventory.add_item_by_id(103)
        player_inventory.add_item_by_id(104)
        player_inventory.add_item_by_id(105)
        player_inventory.add_item_by_id(201)
        player_stats.cigarettes = 9999
        renpy.notify("已添加测试物品")

    def debug_open_shop_screen():
        """打开测试用商城交易界面。"""
        merchant_inv = Inventory()
        merchant_inv.add_item_by_id(101)
        merchant_inv.add_item_by_id(103)
        merchant_inv.add_item_by_id(105)
        renpy.show_screen("scr_shop", player_inventory, merchant_inv, barter_rate=1.0)

    def debug_skip_to_map():
        """跳过开头直接进入大地图主循环。"""
        global player_hex_x, player_hex_y, last_map_event_code
        player_hex_x = 0
        player_hex_y = 0
        last_map_event_code = None
        player_stats.b_dead = False
        player_stats.hp = player_stats.max_hp
        player_stats.hunger = 0.0
        player_stats.thirst = 0.0
        player_stats.fatigue = 0.0
        renpy.jump("travel_on_wasteland_loop")

screen debug_dev_menu():
    modal True
    tag debug_menu
    zorder 999
    frame:
        background Solid("#111111cc")
        xysize (600, 400)
        align (0.5, 0.5)
        padding (30, 30)

        vbox:
            spacing 15
            text "调试工具菜单" size 30 color "#fdd835" xalign 0.5
            text "按下 F12 可随时打开本界面。" size 14 color "#ffffff" xalign 0.5
            textbutton "跳过开头，进入大地图":
                xfill True
                action [Hide("debug_dev_menu"), Function(debug_skip_to_map)]
            textbutton "添加测试物品到背包":
                xfill True
                action [Hide("debug_dev_menu"), Function(debug_add_test_items)]
            textbutton "打开商城交易界面":
                xfill True
                action [Hide("debug_dev_menu"), Function(debug_open_shop_screen)]
            null height 20
            textbutton "无敌模式 [('✓' if god_mode else '✗')]":
                xfill True
                action ToggleVariable("god_mode")
            textbutton "禁用遭遇战 [('✓' if disable_encounters else '✗')]":
                xfill True
                action ToggleVariable("disable_encounters")
            textbutton "关闭调试菜单":
                xfill True
                action Hide("debug_dev_menu")
            key "K_ESCAPE" action Hide("debug_dev_menu")

screen debug_listener():
    key "K_F12" action Show("debug_dev_menu")


label start:
    python:
        # 激活内核单例（多带带在 systems 内部实现的各种类初始化）
        initialize_game_systems()

    show screen debug_listener

    # 平滑跨文件转移至序幕逻辑
    jump prologue_start

label cleanup_pending_removals:
    python:
        while _pending_inventory_removals:
            item = _pending_inventory_removals.pop()
            if item in player_inventory.backpack_grid:
                player_inventory.remove_item(item)
    return