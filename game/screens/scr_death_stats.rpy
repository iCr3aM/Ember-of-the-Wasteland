# =============================================================================
# scr_death_stats.rpy — 死亡统计页面
# 功能：玩家死亡后展示本次旅程的完整数据统计
# 职责：显示生存天数、移动格数、击杀数、吸烟数等，提供返回主菜单按钮
# =============================================================================
screen scr_death_stats():

    modal True
    zorder 1000
    tag death_stats

    add Solid("#0f0f0f")

    frame:
        xalign 0.5
        yalign 0.5
        xsize 1000
        ysize 800
        background Solid("#111111")
        padding (30, 30)

        vbox:
            spacing 15
            xfill True

            text "旅程终结" size 42 color "#ffee88" xalign 0.5
            text "你的废土生存记录" size 20 color "#999999" xalign 0.5

            add Solid("#aa7733") xysize (940, 2) xalign 0.5

            hbox:
                spacing 20
                xfill True

                # 左侧：死亡总结
                frame:
                    xsize 420
                    yfill True
                    background Solid("#1a1a1a")
                    padding (20, 20)

                    vbox:
                        spacing 12

                        text "生存总结" size 28 color "#80deea"

                        text "生存时间" size 18 color "#888888"
                        text "[game_time['day']]天 [game_time['hour']]小时 [game_time['minute']]分钟" size 26 color "#ffffff"

                        null height 10

                        text "移动步数" size 18 color "#888888"
                        text "[steps_taken] 格" size 24 color "#66bb6a"

                        text "击杀敌人" size 18 color "#888888"
                        text "[enemies_killed] 个" size 24 color "#ef5350"

                        text "累计吸烟" size 18 color "#888888"
                        text "[cigarettes_smoked] 支" size 24 color "#ffa726"

                        text "扎营次数" size 18 color "#888888"
                        text "[times_camped] 次" size 24 color "#42a5f5"

                        text "承受伤害" size 18 color "#888888"
                        text "[total_damage_taken] 点" size 24 color "#ff6b6b"

                # 右侧：统计面板
                frame:
                    xsize 420
                    yfill True
                    background Solid("#151c26")
                    padding (20, 20)

                    vbox:
                        spacing 8

                        text "废土档案" size 28 color "#80deea" xalign 0.5

                        grid 2 6:
                            spacing 10

                            text "生存天数" size 20 color "#b0bec5"
                            text "[game_time['day']] 天" size 20 color "#ffffff"

                            text "总移动距离" size 20 color "#b0bec5"
                            text "[steps_taken] 格" size 20 color "#ffffff"

                            text "敌人击杀" size 20 color "#b0bec5"
                            text "[enemies_killed] 个" size 20 color "#ffffff"

                            text "累计吸烟" size 20 color "#b0bec5"
                            text "[cigarettes_smoked] 支" size 20 color "#ffffff"

                            text "扎营次数" size 20 color "#b0bec5"
                            text "[times_camped] 次" size 20 color "#ffffff"

                            text "承受伤害" size 20 color "#b0bec5"
                            text "[total_damage_taken] 点" size 20 color "#ffffff"

                        null height 60

                        frame:
                            xfill True
                            background Solid("#202020")
                            padding (15, 15)
                            
                            text "没有人能永远活在废土中，但每一步都留下了痕迹。":
                                size 20
                                color "#cccccc"
                                italic True
                                xalign 0.5

            add Solid("#aa7733") xysize (940, 2) xalign 0.5

            button:
                xalign 0.5
                xsize 340
                ysize 60
                background Solid("#556677")
                hover_background Solid("#778899")
                action [
                    Hide("scr_death_stats"),
                    With(dissolve),
                    Function(renpy.full_restart)
                ]

                text "返回主菜单" align (0.5, 0.5) size 24 color "#ffffff"
