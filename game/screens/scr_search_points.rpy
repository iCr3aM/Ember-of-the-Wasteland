# =============================================================================
# scr_search_points.rpy — 搜刮点选择界面
# 功能：展示当前区域发现的搜刮点，玩家选择后执行搜刮
# =============================================================================
screen scr_search_points(search_points):
    modal True
    zorder 100
    tag search_points

    frame:
        xalign 0.5 yalign 0.5
        xsize 600
        ysize 500
        background Solid("#111111")
        padding (20, 20)

        vbox:
            spacing 10
            text "你发现了以下可搜刮的地点：" size 24 color "#ffee88" xalign 0.5

            viewport:
                yinitial 0.0
                scrollbars "vertical"
                mousewheel True
                xfill True
                ysize 350

                vbox:
                    spacing 8
                    for point in search_points:
                        if point.event_label:
                            # ★ 事件型搜刮点（如湖水）：始终可点击，永不标记已搜刮
                            button:
                                xfill True
                                background Solid("#2a5a2a")          # 绿色背景，与普通点区分
                                hover_background Solid("#3a7a3a")
                                padding (10, 10)
                                action Return(click_search_point(point))

                                vbox:
                                    text point.name size 20 color "#66ff66"
                                    text point.desc size 16 color "#aaaaaa"

                        elif point.searched:
                            # 普通搜刮点已搜刮：灰色不可用
                            frame:
                                background Solid("#333333")
                                padding (10, 10)
                                xfill True
                                vbox:
                                    text point.name size 20 color "#888888"
                                    text point.desc size 16 color "#666666"
                        else:
                            # 普通搜刮点未搜刮：可点击
                            button:
                                xfill True
                                background Solid("#2a2a2a")
                                hover_background Solid("#3a3a3a")
                                padding (10, 10)
                                action Return(click_search_point(point))

                                vbox:
                                    text point.name size 20 color "#ffcc66"
                                    text point.desc size 16 color "#aaaaaa"

            textbutton "离开" :
                xalign 0.5
                action Return("leave")