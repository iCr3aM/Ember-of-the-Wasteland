# =============================================================================
# # 定义：游戏全局入口、初始标签（label start）、开发调试菜单（Dev Menu）。
# # 实现：调用各个系统的初始化流程，重定向至序幕（prologue）；提供一键刷物品/怪物的测试工具。
# =============================================================================

init python:
    def debug_add_test_items():
        """将测试物品加入玩家背包。"""
        player_inventory.add_item_by_id(110)
        player_inventory.add_item_by_id(111)
        player_inventory.add_item_by_id(112)
        player_inventory.add_item_by_id(113)
        player_inventory.add_item_by_id(114)
        player_inventory.add_item_by_id(201)
        player_stats.cigarettes = 9999
        renpy.notify("已添加测试物品")

    def debug_open_shop_screen():
        # 直接 Show scr_shop，不经过 trade_flow
        merchant_cfg = MERCHANT_WASTELAND_TRADER
        merchant_inv = get_merchant_inventory(merchant_cfg)
        renpy.show_screen("scr_shop",
            player_inv=player_inventory,
            merchant_inv=merchant_inv,
            shop_type=merchant_cfg.shop_type,
            barter_rate=1.0,
            merchant_avatar=merchant_cfg.avatar_path,
            merchant_name=merchant_cfg.name)

    def debug_skip_to_map():
        global player_hex_x, player_hex_y, last_map_event_code
        import random
        player_hex_x, player_hex_y = random.choice(BIRTH_ZONE)  # ← 引用全局变量
        last_map_event_code = None
        player_stats.b_dead = False
        player_stats.hp = player_stats.max_hp
        player_stats.hunger = 0.0
        player_stats.thirst = 0.0
        player_stats.fatigue = 0.0
        renpy.jump("travel_on_wasteland_loop")

        # 四个独立调试函数
    def debug_set_hp_999():
        """将玩家生命值设为999。"""
        player_stats.hp = 999.0
        renpy.notify("生命值已设定为 999")

    def debug_clear_hunger():
        """将饥饿值清0。"""
        player_stats.hunger = 0.0
        renpy.notify("饥饿值已清空")

    def debug_clear_thirst():
        """将口渴值清0。"""
        player_stats.thirst = 0.0
        renpy.notify("口渴值已清空")

    def debug_clear_fatigue():
        """将疲劳值清0。"""
        player_stats.fatigue = 0.0
        renpy.notify("疲劳值已清空")


define splash_title_size = 90   # 工作室名更大
define splash_text_size  = 50   # 声明也更大

style splash_title:
    size 70
    color "#ffffff"
    bold True

style splash_text:
    size 32
    color "#ffffff"
    line_spacing 8

label splashscreen:

    # 提前播放主菜单音乐（循环播放，淡入1秒）
    play music "bgm_menu.mp3" fadein 1.0

    # 先清空画面，设为黑色背景
    scene black
    with Pause(0.5)

    # --- 工作室名称（大号字，居中） ---
    show text "{size=[splash_title_size]}Cr3aM Studio{/size}" at truecenter with dissolve
    $ renpy.pause(2.0, hard=True)
    hide text with dissolve
    with Pause(0.5)

    # --- 游戏声明（稍小但依然清晰，居中） ---
    show text "{size=[splash_text_size]}\n本游戏可能含有恐怖、惊悚元素。\n本游戏基于Ren'Py引擎制作，采用AI生成图像与音乐素材。\n本游戏为单机游戏，不收集任何个人信息。\n\n本游戏所有内容纯属虚构。\n如有雷同，纯属巧合。{/size}" at truecenter with dissolve
    $ renpy.pause(4.0, hard=True)
    hide text with dissolve
    with Pause(0.5)

    # 回到纯黑色背景
    scene black
    with Pause(0.2)
    
    return

screen debug_dev_menu():
    modal True
    tag debug_menu
    zorder 999
    frame:
        background Solid("#111111cc")
        xysize (520, 480)
        align (0.5, 0.3)
        padding (25, 25)

        vbox:
            spacing 8
            # ── 标题（全宽） ──
            text "调试工具菜单" size 22 color "#fdd835" xalign 0.5
            text "按下 F12 可随时打开本界面" size 16 color "#ffffff" xalign 0.5
            
            null height 8

            # ── 功能按钮：两列 ──
            hbox:
                spacing 12
                xfill True
                
                # 左列：场景/状态类
                vbox:
                    xsize 220
                    spacing 6
                    textbutton "跳过开头，进入大地图":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_skip_to_map)]
                    textbutton "添加测试物品到背包":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_add_test_items)]
                    textbutton "生命值设定为 999":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_set_hp_999)]
                    textbutton "疲劳值清0":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_clear_fatigue)]
                
                # 右列：系统/属性类
                vbox:
                    xsize 220
                    spacing 6
                    textbutton "打开商城交易界面":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_open_shop_screen)]
                    textbutton "饥饿值清0":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_clear_hunger)]
                    textbutton "口渴值清0":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_clear_thirst)]
                    textbutton "禁用遭遇战 [('开' if disable_encounters else '关')]":
                        xfill True
                        text_size 16
                        action ToggleVariable("disable_encounters")
            
            null height 10

            # ── 底部按钮 ──
            textbutton "关闭调试菜单":
                xalign 0.5
                text_size 22
                action Hide("debug_dev_menu")
            key "K_ESCAPE" action Hide("debug_dev_menu")

screen debug_listener():
    key "K_F12" action Show("debug_dev_menu")


label start:
    # 主题曲淡出（1.5秒）
    stop music fadeout 1.5
    
    # 等待淡出完成（可选：如果希望淡出完毕后文字才开始显示）
    $ renpy.pause(1.0, hard=True)

    # 如果此时音乐未在播放（从 splashscreen 进入时已在播，从其他地方进入可能没有）
    if not renpy.music.is_playing():
        play music "bgm_menu.mp3" fadein 1.0
    
    python:
        # 激活内核单例
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