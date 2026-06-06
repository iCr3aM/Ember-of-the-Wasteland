# =============================================================================
# 交易界面（左侧玩家背包，右侧商人背包，顶部显示当前香烟数量）
# 实现：调用 shop_execute_purchase() / shop_execute_sell() 进行货币结算
# =============================================================================
screen scr_shop(player_inv, merchant_inv, shop_type="wasteland_trader", barter_rate=1.0, merchant_avatar=None, merchant_name="流浪商人"):
    modal True
    # ── 悬停/右键状态变量 ──
    default hovered_player_idx = None
    default hovered_merchant_idx = None
    default shop_context_menu_slot = None
    default shop_context_menu_pos = (0, 0)
    default shop_context_is_player = False
    zorder 100
    # 全屏覆盖层，确保不透过任何底层内容
    frame:
        xsize config.screen_width
        ysize config.screen_height
        background Solid("#0f0f0f")
        
    add Solid("#0f0f0f")

    # 顶部信息栏 - 显示玩家香烟
    frame:
        xpos 20 ypos 20
        xsize 200
        background Solid("#1a1a1a")
        padding (15, 10)
        hbox:
            spacing 10
            text "香烟：" size 18 color "#ffffff"
            text "[player_stats.cigarettes:.0f] 支" size 18 color "#ffd54f"
    
    hbox:
        align (0.5, 0.4)
        spacing 40
        
        # ========== 左侧：玩家物品栏 ==========
        vbox:
            spacing 10
            xsize 450
            null height 140

            text "你的物品" size 18 color "#81c784" xalign 0.5
            
            frame:
                xsize 750 ysize 600
                background Solid("#202020")
                padding (15, 15)

                vpgrid:
                    cols player_inv.backpack_width
                    mousewheel True
                    draggable True
                    ysize 620
                    spacing 3
                    for i in range(player_inv.max_slots):
                        $ slot = player_inv.backpack_slots[i] if i < len(player_inv.backpack_slots) else None
                        $ item = slot["item"] if slot is not None else None
                        $ stack = slot["stack"] if slot is not None else 0

                        # ── 动态边框颜色 ──
                        if hovered_player_idx == i:
                            $ player_border_color = "#ffffffa1"
                        else:
                            $ player_border_color = "#282828"

                        if slot is not None:
                            frame:
                                xsize 110 ysize 110
                                background Solid(player_border_color)
                                xpadding 2 ypadding 2

                                frame:
                                    xfill True yfill True
                                    background Solid("#1a1a1a")

                                    fixed:
                                        # ── 居中按钮（图标+名称+堆叠） ──
                                        button:
                                            align (0.5, 0.5)
                                            background None
                                            action NullAction()
                                            hovered [SetScreenVariable("hovered_player_idx", i), Show("tooltip_delay_timer", text=item.config.desc)]
                                            unhovered [SetScreenVariable("hovered_player_idx", None), Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                                            # 右键打开卖出菜单
                                            alternate [
                                                SetScreenVariable("shop_context_menu_slot", i),
                                                SetScreenVariable("shop_context_is_player", True),
                                                SetScreenVariable("shop_context_menu_pos", renpy.get_mouse_pos()),
                                                Hide("tooltip_delay_timer"),
                                                Hide("floating_tooltip")
                                            ]

                                            vbox:
                                                align (0.5, 0.5)
                                                $ icon = item.icon_path
                                                if icon:
                                                    add icon size (80, 80) xalign 0.5
                                                else:
                                                    add Solid("#555555") size (80, 80) xalign 0.5
                                                hbox:
                                                    xalign 0.5
                                                    spacing 5
                                                    text "[item.config.name]" size 12
                                                    if stack > 1:
                                                        text "×[stack]" size 12 color "#ffcc00" outlines [(1, "#000000")]

                                        # ── 耐久度（浮在右上角） ──
                                        if item.config.max_durability > 0 and item.durability < 1.0:
                                            $ durability_pct = item.durability * 100
                                            text f"耐久:{durability_pct:.0f}%" size 12 color "#4caf50" xpos 1.0 ypos 0.0 xanchor 1.0 yanchor 0.0 outlines [(1, "#000000")]
                        else:
                            frame:
                                xsize 110 ysize 110
                                background Solid(player_border_color)
                                xpadding 2 ypadding 2

                                frame:
                                    xfill True yfill True
                                    background Solid("#1a1a1a")

        # ========== 右侧：商人栏（含头像） ==========
        vbox:
            spacing 10
            xsize 750
            
            # 商人头像和名称区域
            frame:
                xsize 280 ysize 140
                background Solid("#2a2a2a")
                padding (15, 15)
                hbox:
                    spacing 20
                    frame:
                        xysize (110, 110)
                        background Solid("#333")
                        if merchant_avatar:
                            add merchant_avatar size (110, 110)
                        else:
                            text "?" size 44 color "#888" align (0.5, 0.5)

                    vbox:
                        spacing 5
                        text "[merchant_name]" size 24 color "#ffb74d"
            
            text "商人的物品" size 18 color "#e57373" xalign 0.5
            
            frame:
                xsize 750 ysize 600
                background Solid("#202020")
                padding (15, 15)

                vpgrid:
                    cols 6
                    scrollbars "vertical"
                    mousewheel True
                    draggable True
                    ysize 560
                    spacing 3
                    for i in range(60):
                        $ slot = merchant_inv.backpack_slots[i] if i < len(merchant_inv.backpack_slots) else None
                        $ item = slot["item"] if slot is not None else None
                        $ stack = slot["stack"] if slot is not None else 0

                        if hovered_merchant_idx == i:
                            $ merchant_border_color = "#ffffffa1"
                        else:
                            $ merchant_border_color = "#282828"

                        if slot is not None:
                            frame:
                                xsize 110 ysize 110
                                background Solid(merchant_border_color)
                                xpadding 2 ypadding 2

                                frame:
                                    xfill True yfill True
                                    background Solid("#1a1a1a")

                                    fixed:
                                        button:
                                            align (0.5, 0.5)
                                            background None
                                            action NullAction()
                                            hovered [SetScreenVariable("hovered_merchant_idx", i), Show("tooltip_delay_timer", text=item.config.desc)]
                                            unhovered [SetScreenVariable("hovered_merchant_idx", None), Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                                            # 右键打开买入菜单
                                            alternate [
                                                SetScreenVariable("shop_context_menu_slot", i),
                                                SetScreenVariable("shop_context_is_player", False),
                                                SetScreenVariable("shop_context_menu_pos", renpy.get_mouse_pos()),
                                                Hide("tooltip_delay_timer"),
                                                Hide("floating_tooltip")
                                            ]

                                            vbox:
                                                align (0.5, 0.5)
                                                $ icon = item.icon_path
                                                if icon:
                                                    add icon size (80, 80) xalign 0.5
                                                else:
                                                    add Solid("#555555") size (80, 80) xalign 0.5
                                                hbox:
                                                    xalign 0.5
                                                    spacing 5
                                                    text "[item.config.name]" size 12
                                                    if stack > 1:
                                                        text "×[stack]" size 12 color "#ffcc00" outlines [(1, "#000000")]

                                        if item.config.max_durability > 0 and item.durability < 1.0:
                                            $ durability_pct = item.durability * 100
                                            text f"耐久:{durability_pct:.0f}%" size 12 color "#4caf50" xpos 1.0 ypos 0.0 xanchor 1.0 yanchor 0.0 outlines [(1, "#000000")]
                        else:
                            frame:
                                xsize 110 ysize 110
                                background Solid(merchant_border_color)
                                xpadding 2 ypadding 2

                                frame:
                                    xfill True yfill True
                                    background Solid("#1a1a1a")

    # ── 右键菜单模块 ──
    if shop_context_menu_slot is not None:
        # 全屏透明遮罩
        button:
            background None
            xfill True
            yfill True
            action SetScreenVariable("shop_context_menu_slot", None)

        $ ctx_slot = player_inv.backpack_slots[shop_context_menu_slot] if shop_context_is_player else merchant_inv.backpack_slots[shop_context_menu_slot]
        if ctx_slot is not None:
            $ ctx_item = ctx_slot["item"]
            $ ctx_stack = ctx_slot["stack"]

            frame:
                xsize 140
                background Solid("#222222")
                xpadding 10
                ypadding 10
                xpos shop_context_menu_pos[0]
                ypos shop_context_menu_pos[1]

                vbox:
                    spacing 8
                    text ctx_item.config.name size 16 color "#ffffff" xalign 0.5

                    if shop_context_is_player:
                        # 玩家物品 → 卖出
                        $ sell_price = get_shop_price(ctx_item, shop_type, buy=False, barter_rate=barter_rate)
                        text f"售价: {sell_price:.0f} 支烟" size 14 color "#ffd54f" xalign 0.5
                        null height 4
                        textbutton _("卖出"):
                            text_size 14
                            xfill True
                            text_xalign 0.5
                            ypadding 6
                            background Solid("#333333")
                            hover_background Solid("#555555")
                            action [
                                Function(shop_execute_sell, player_inv, merchant_inv, ctx_item, shop_type, barter_rate),
                                SetScreenVariable("shop_context_menu_slot", None),
                                Show("scr_shop", player_inv=player_inv, merchant_inv=merchant_inv, shop_type=shop_type, barter_rate=barter_rate, merchant_avatar=merchant_avatar, merchant_name=merchant_name)
                            ]
                    else:
                        # 商人物品 → 买入
                        $ buy_price = get_shop_price(ctx_item, shop_type, buy=True, barter_rate=barter_rate)
                        $ can_buy = shop_can_afford(player_stats, buy_price)
                        text f"价格: {buy_price:.0f} 支烟" size 14 color "#ffd54f" xalign 0.5
                        if not can_buy:
                            text "香烟不足！" size 12 color "#f44336" xalign 0.5
                        null height 4
                        textbutton _("买入"):
                            text_size 14
                            xfill True
                            text_xalign 0.5
                            ypadding 6
                            sensitive can_buy
                            background Solid("#333333")
                            hover_background Solid("#555555")
                            action [
                                Function(shop_execute_purchase, player_inv, merchant_inv, ctx_item, shop_type, barter_rate),
                                SetScreenVariable("shop_context_menu_slot", None),
                                Show("scr_shop", player_inv=player_inv, merchant_inv=merchant_inv, shop_type=shop_type, barter_rate=barter_rate, merchant_avatar=merchant_avatar, merchant_name=merchant_name)
                            ]

                    textbutton _("取消"):
                        text_size 14
                        xfill True
                        text_xalign 0.5
                        ypadding 6
                        background Solid("#333333")
                        hover_background Solid("#555555")
                        action SetScreenVariable("shop_context_menu_slot", None)

    # 底部退出按钮
    textbutton "打包物资安全离开":
        xalign 0.5 ypos 0.88
        action [Hide("tooltip_delay_timer"), Hide("floating_tooltip"), Return()]
        style "button"
        text_size 20