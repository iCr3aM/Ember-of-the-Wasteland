# =============================================================================
# 交易界面（左侧玩家背包，右侧商人背包，顶部显示当前香烟数量）
# 实现：调用 shop_execute_purchase() / shop_execute_sell() 进行货币结算
# =============================================================================
screen scr_shop(player_inv, merchant_inv, shop_type="wasteland_trader", barter_rate=1.0, merchant_avatar=None, merchant_name="流浪商人"):
    modal True
    zorder 200 
    # 全屏覆盖层，确保不透过任何底层内容
    frame:
        xsize config.screen_width
        ysize config.screen_height
        background Solid("#0f0f0f")
        
    add Solid("#0f0f0f")

    # 顶部信息栏 - 显示玩家香烟
    frame:
        xpos 20 ypos 20
        xsize 400
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
                xsize 750 ysize 650   
                background Solid("#202020")
                padding (15, 15)   
                
                grid 5 4:
                    spacing 10     
                    for i in range(20):
                        if i < len(player_inv.backpack_slots):
                            $ slot = player_inv.backpack_slots[i]
                            $ item = slot["item"]
                            $ stack = slot["stack"]
                            frame:
                                xsize 130 ysize 145  
                                background Solid("#282828")
                                if item.config.max_durability > 0 and item.durability < 1.0:
                                    $ durability_pct = item.durability * 100
                                    text f"耐久:{durability_pct:.0f}%" size 12 color "#4caf50" xpos 1.0 ypos 0.0 xanchor 1.0 yanchor 0.0
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
                                            text "×[stack]" size 14 color "#ffcc00"

                                # 底部：卖出价格 + "卖出"文字按钮
                                hbox:
                                    xfill True
                                    ypos 1.0 yanchor 1.0
                                    spacing 4
                                    hbox:
                                        xalign 0.0
                                        $ sell_price = get_shop_price(item, shop_type, buy=False, barter_rate=barter_rate)
                                        text "价值:[sell_price:.0f]支烟" size 12 color "#ffd54f"
                                    hbox:
                                        xalign 1.0
                                        textbutton "卖出":
                                            text_size 12
                                            xpadding 6 ypadding 3
                                            action Function(shop_execute_sell, player_inv, merchant_inv, item, shop_type, barter_rate)
                        else:
                            # 空格子
                            frame:
                                xsize 130 ysize 145
                                background Solid("#1a1a1a")
                                text "空" align (0.5, 0.5) size 12 color "#444444"

        # ========== 右侧：商人栏（含头像） ==========
        vbox:
            spacing 10
            xsize 750
            
            # 商人头像和名称区域
            frame:
                xsize 750 ysize 140
                background Solid("#2a2a2a")
                padding (15, 15)
                hbox:
                    spacing 20
                    # 头像
                    frame:
                        xysize (110, 110)
                        background Solid("#333")
                        if merchant_avatar:
                            add merchant_avatar size (110, 110)
                        else:
                            text "?" size 44 color "#888" align (0.5, 0.5)

                    vbox:
                        spacing 5
                        # ★ 只显示商人名称 ★
                        text "[merchant_name]" size 24 color "#ffb74d"
            
            text "商人的物品" size 18 color "#e57373" xalign 0.5
            
            frame:
                xsize 750 ysize 650
                background Solid("#202020")
                padding (15, 15)

                grid 5 4:
                    spacing 10
                    for i in range(20):
                        if i < len(merchant_inv.backpack_slots):
                            $ slot = merchant_inv.backpack_slots[i]
                            $ item = slot["item"]
                            $ stack = slot["stack"]
                            frame:
                                xsize 130 ysize 145
                                background Solid("#282828")
                                fixed:
                                    # ★ 耐久度 - 右上角 ★
                                    if item.config.max_durability > 0 and item.durability < 1.0:
                                        $ durability_pct = item.durability * 100
                                        text f"耐久:{durability_pct:.0f}%" size 12 color "#4caf50" xpos 1.0 ypos 0.0 xanchor 1.0 yanchor 0.0

                                    # 居中内容
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
                                                text "×[stack]" size 14 color "#ffcc00"

                                    # 底部：买入价格 + "买入"文字按钮（有敏感状态）
                                    hbox:
                                        xfill True
                                        ypos 1.0 yanchor 1.0
                                        spacing 4
                                        hbox:
                                            xalign 0.0
                                            $ buy_price = get_shop_price(item, shop_type, buy=True, barter_rate=barter_rate)
                                            $ can_buy = shop_can_afford(player_stats, buy_price)
                                            text "价格:[buy_price:.0f]支烟" size 12 color "#ffd54f"
                                        hbox:
                                            xalign 1.0
                                            textbutton "买入":
                                                text_size 12
                                                xpadding 6 ypadding 3
                                                sensitive can_buy
                                                action Function(shop_execute_purchase, player_inv, merchant_inv, item, shop_type, barter_rate)
                        else:
                            # 空格子
                            frame:
                                xsize 130 ysize 145
                                background Solid("#1a1a1a")
                                text "空" align (0.5, 0.5) size 12 color "#444444"

    # 底部退出按钮
    textbutton "打包物资安全离开":
        xalign 0.5 ypos 0.88
        action Return() 
        style "button"
        text_size 20