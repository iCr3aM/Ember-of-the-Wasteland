# =============================================================================
# 交易界面（左侧玩家背包，右侧商人背包，顶部显示当前香烟数量）
# 实现：调用 shop_execute_purchase() / shop_execute_sell() 进行货币结算
# =============================================================================
screen scr_shop(player_inv, merchant_inv, shop_type="wasteland_trader", barter_rate=1.0):
    modal True
    zorder 200 
    # 全屏覆盖层，确保不透过任何底层内容
    frame:
        xsize config.screen_width
        ysize config.screen_height
        background Solid("#0f0f0f")
        
    add Solid("#0f0f0f")

    # 左上角显示玩家当前香烟数量
    frame:
        xpos 20 ypos 20
        background Solid("#1a1a1a")
        padding (15, 10)
        hbox:
            spacing 10
            text "香烟：" size 18 color "#ffffff"
            text "[player_stats.cigarettes:.0f] 支" size 18 color "#ffd54f"
    
    text "交易界面" xalign 0.5 ypos 0.15 size 26 color "#ffb74d"
    
    hbox:
        align (0.5, 0.4)
        spacing 40
        
        # 左侧：玩家库存抛售区
        vbox:
            spacing 10
            text "你的物品" size 16 color "#81c784" xalign 0.5
            frame:
                xsize 400 ysize 400
                background Solid("#202020")
                padding (10, 10)
                vpgrid:
                    cols 3 spacing 10 scrollbars "vertical" mousewheel True
                    for item in player_inv.backpack_grid:
                        vbox:
                            add item.icon_path size (64, 64) xalign 0.5
                            text "[item.config.name]" size 11 xalign 0.5
                            $ sell_price = get_shop_price(item, shop_type, buy=False, barter_rate=barter_rate)
                            text "卖出价: [sell_price:.0f]支烟" size 10 color "#ffd54f" xalign 0.5
                            textbutton "出售此物":
                                text_size 11 xalign 0.5
                                # 调用 shop_execute_sell 进行货币结算
                                action [Function(shop_execute_sell, player_inv, merchant_inv, item, shop_type, barter_rate), Return("refresh")]

        # 右侧：流浪商人货架区
        vbox:
            spacing 10
            text "商人的物品" size 16 color "#e57373" xalign 0.5
            frame:
                xsize 400 ysize 400
                background Solid("#202020")
                padding (10, 10)
                vpgrid:
                    cols 3 spacing 10 scrollbars "vertical" mousewheel True
                    for item in merchant_inv.backpack_grid:
                        vbox:
                            add item.icon_path size (64, 64) xalign 0.5
                            text "[item.config.name]" size 11 xalign 0.5
                            $ buy_price = get_shop_price(item, shop_type, buy=True, barter_rate=barter_rate)
                            text "买入价: [buy_price:.0f]支烟" size 10 color "#ffd54f" xalign 0.5
                            $ can_buy = shop_can_afford(player_stats, buy_price)
                            textbutton "购入此物":
                                text_size 11 xalign 0.5
                                sensitive can_buy
                                # 调用 shop_execute_purchase 进行货币结算
                                action Function(shop_execute_purchase, player_inv, merchant_inv, item, shop_type, barter_rate)

    # 底部退出按钮
    textbutton "打包物资安全离开":
        xalign 0.5 ypos 0.88
        action Return("leave")
        style "button"
        text_size 16