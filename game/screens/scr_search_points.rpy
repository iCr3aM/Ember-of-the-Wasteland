# =============================================================================
# scr_search_points.rpy — 搜刮点选择界面
# 功能：展示当前区域发现的搜刮点，玩家选择后执行搜刮
# =============================================================================
screen scr_search_points(search_points):
    modal True
    zorder 100
    tag search_points

    # 当前选中的搜刮点（None=未选中）
    default selected_point = None

    frame:
        xalign 0.5 yalign 0.5
        xsize 700
        ysize 650
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
                ysize 300

                vbox:
                    spacing 8
                    for point in search_points:
                        if point.event_label:
                            button:
                                xfill True
                                background Solid("#2a5a2a")
                                hover_background Solid("#3a7a3a")
                                padding (10, 10)
                                action Return(("event", point))

                                hbox:
                                    spacing 10
                                    add get_search_point_icon_display(point) yalign 0.5
                                    vbox:
                                        text point.name size 20 color "#66ff66"
                                        text point.desc size 16 color "#aaaaaa"

                        elif point.searched:
                            frame:
                                background Solid("#333333")
                                padding (10, 10)
                                xfill True
                                hbox:
                                    spacing 10
                                    add get_search_point_icon_display(point) yalign 0.5
                                    vbox:
                                        text point.name size 20 color "#888888"
                                        text point.desc size 16 color "#666666"
                        else:
                            $ is_this_selected = (selected_point == point)
                            button:
                                xfill True
                                background Solid("#4a4a1a" if is_this_selected else "#2a2a2a")
                                hover_background Solid("#5a5a2a" if is_this_selected else "#3a3a3a")
                                padding (10, 10)
                                activate_sound "audio/searching_click.mp3"
                                action If(is_this_selected, SetScreenVariable("selected_point", None), SetScreenVariable("selected_point", point))

                                hbox:
                                    spacing 10
                                    add get_search_point_icon_display(point) yalign 0.5
                                    vbox:
                                        text point.name size 20 color ("#ffff88" if is_this_selected else "#ffcc66")
                                        text point.desc size 16 color ("#cccccc" if is_this_selected else "#aaaaaa")

            # ── 模式选择区域 ──
            null height 5
            frame:
                xfill True
                background Solid("#1a1a2a")
                padding (10, 10)
                vbox:
                    spacing 6
                    text "选择搜刮方式" size 18 color "#b0bec5" xalign 0.5
                    
                    if selected_point is not None:
                        text "当前选中：[selected_point.name]" size 18 color "#ffff88" xalign 0.5
                    else:
                        text "请先在上方点击选择一个搜刮点" size 18 color "#666666" xalign 0.5

                    $ available_modes = get_available_search_modes()
                    $ mode_rows = max(1, (len(available_modes) + 3) // 4)
                    grid 4 mode_rows:
                        spacing 8
                        xfill True
                        yfill False
                        for mode_id in available_modes:
                            $ cfg = SEARCH_MODE_CONFIG[mode_id]
                            $ crowbar_ready = (mode_id != SEARCH_MODE_CROWBAR) or is_crowbar_equipped()
                            $ can_click = selected_point is not None and crowbar_ready
                            
                            button:
                                xsize 100 ysize 40
                                background Solid("#222222" if not can_click else "#334455")
                                hover_background Solid("#556677")
                                hovered Show("tooltip_delay_timer", text=cfg["desc"])
                                unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                                action [
                                    Hide("tooltip_delay_timer"),
                                    Hide("floating_tooltip"),
                                    If(can_click, Return(("execute_search", selected_point, mode_id)), NullAction())
                                ]

                                text cfg["name"] size 18 xalign 0.5 yalign 0.5 color ("#555555" if not can_click else "#ffffff")

            # ── 离开按钮 ──
            null height 5
            textbutton "离开" :
                xalign 0.5
                action Return("leave")