# =============================================================================
# # 定义：主界面常驻 HUD 面板（屏幕上方或死角的仪表盘）。 
# # 实现：实时用进度条或数字显示玩家的内呼吸指标：系统时间（月/日/时）、HP、饥饿值、口渴值、疲劳值。
# =============================================================================
screen scr_hud():
    zorder 505
    
    # 将 frame 内容正确嵌套
    frame:
        background Solid("#111111")
        xalign 0.5
        yalign 0.0
        ysize 50
        padding (20, 10)
        
        hbox:            # 单行布局：时间 → 生命值 → 饥饿值 → 口渴值 → 疲劳值 → 香烟/抽烟
            spacing 20
            yalign 0.5
            
            # ── 时间显示 ──
            $ has_watch = (player_inventory.slots.get("left_wrist") is not None and player_inventory.slots["left_wrist"].id == 118)
            if has_watch:
                text "时间: [get_time_period_str(game_time['hour'])] ([game_time['hour']]:[game_time['minute']:0>2])" size 16 color "#ffffff" yalign 0.5
            else:
                text "时间: [get_time_period_str(game_time['hour'])]" size 16 color "#ffffff" yalign 0.5
            
            # ── 生命值 ──
            hbox:
                spacing 5
                yalign 0.5
                text "生命值:" size 16 color "#ff4d4d" yalign 0.5
                bar value player_stats.hp range player_stats.max_hp xsize 120 ysize 16 left_bar "#ff4d4d" right_bar "#551a1a" yalign 0.5
                text f"{player_stats.hp:.0f}" size 16 yalign 0.5
            
            # ── 饥饿值 ──
            hbox:
                spacing 5
                yalign 0.5
                text "饥饿值:" size 16 color "#ffa500" yalign 0.5
                bar value player_stats.hunger range 100.0 xsize 100 ysize 16 left_bar "#ffa500" right_bar "#4d3200" yalign 0.5
                text f"{player_stats.hunger:.0f}" size 16 color "#ffa500" yalign 0.5
            
            # ── 口渴值 ──
            hbox:
                spacing 5
                yalign 0.5
                text "口渴值:" size 16 color "#3399ff" yalign 0.5
                bar value player_stats.thirst range 100.0 xsize 100 ysize 16 left_bar "#3399ff" right_bar "#0f2d4d" yalign 0.5
                text f"{player_stats.thirst:.0f}" size 16 color "#3399ff" yalign 0.5
            
            # ── 疲劳值 ──
            hbox:
                spacing 5
                yalign 0.5
                text "疲劳值:" size 16 color "#aa66cc" yalign 0.5
                bar value player_stats.fatigue range 100.0 xsize 100 ysize 16 left_bar "#aa66cc" right_bar "#331133" yalign 0.5
                text f"{player_stats.fatigue:.0f}" size 16 color "#aa66cc" yalign 0.5
            
            # ── 香烟显示 + 抽烟按钮（仅大地图） ──
            if not is_in_active_combat():
                hbox:
                    spacing 5
                    yalign 0.5
                    text "香烟: [player_stats.cigarettes:.0f] 支" size 16 color "#ffd54f" yalign 0.5
                    if player_stats.cigarettes >= 1:
                        button:
                            yalign 0.5
                            background Solid("#554422")
                            hover_background Solid("#776633")
                            padding (8, 4)
                            activate_sound "audio/smoke_click.mp3"
                            action Function(smoke_cigarette)
                            text "抽一只" size 16 color "#ffffff" yalign 0.5

    # 负面状态指示（保持独立，但调整位置避免与主框架重叠）
    vbox:
        xalign 0.02
        yalign 0.15
        spacing 8
        for ac in player_stats.active_conditions:
            $ _bg, _color = get_condition_display_colors(ac.id)
            button:
                background Solid(_bg)
                padding (5, 5)
                action NullAction()
                hovered Show("tooltip_delay_timer", text=ac.config.desc)
                unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                text ac.config.name size 18 color _color