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
        padding (20, 10)
        
        vbox:
            spacing 5
            
            hbox:            # 时间显示
                $ has_watch = (player_inventory.slots.get("left_wrist") is not None and player_inventory.slots["left_wrist"].id == 118)
                if has_watch:
                    text "时间: [get_time_period_str(game_time['hour'])] ([game_time['hour']]:[game_time['minute']:0>2])" size 20 color "#ffffff"
                else:
                    text "时间: [get_time_period_str(game_time['hour'])]" size 20 color "#ffffff"
            
            hbox:            # 状态条
                spacing 30
                hbox:
                    spacing 5
                    text "生命值:" size 16 color "#ff4d4d"
                    bar value player_stats.hp range player_stats.max_hp xsize 120 ysize 16 left_bar "#ff4d4d" right_bar "#551a1a"
                    text f"{player_stats.hp:.0f}" size 16
                hbox:
                    spacing 5
                    text "饥饿值:" size 16 color "#ffa500"
                    bar value player_stats.hunger range 100.0 xsize 100 ysize 16 left_bar "#ffa500" right_bar "#4d3200"
                    text f"{player_stats.hunger:.0f}/100" size 16 color "#ffa500"
                hbox:
                    spacing 5
                    text "口渴值:" size 16 color "#3399ff"
                    bar value player_stats.thirst range 100.0 xsize 100 ysize 16 left_bar "#3399ff" right_bar "#0f2d4d"
                    text f"{player_stats.thirst:.0f}/100" size 16 color "#3399ff"
                hbox:
                    spacing 5
                    text "疲劳值:" size 16 color "#aa66cc"
                    bar value player_stats.fatigue range 100.0 xsize 100 ysize 16 left_bar "#aa66cc" right_bar "#331133"
                    text f"{player_stats.fatigue:.0f}/100" size 16 color "#aa66cc"

    # 右侧负面状态指示（保持独立，但调整位置避免与主框架重叠）
    vbox:
        xalign 0.02
        yalign 0.15
        spacing 8
        for ac in player_stats.active_conditions:
            if ac.id == COND_FAINT:
                # "昏阙"状态特殊显示 - 绿色背景
                button:
                    background Solid("#225522")
                    padding (4, 4)
                    action NullAction()
                    hovered Show("tooltip_delay_timer", text=ac.config.desc)
                    unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                    text ac.config.name size 18 color "#88ff88"

            elif ac.id == COND_SEVERE_FATIGUE:
                # 重度疲劳 - 红色背景
                button:
                    background Solid("#552222")
                    padding (5, 5)
                    action NullAction()
                    hovered Show("tooltip_delay_timer", text=ac.config.desc)
                    unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                    hbox:
                        spacing 5
                        text f"{ac.config.name}" size 18 color "#ff6666"

            elif ac.id == COND_FATIGUE:
                # 普通疲劳 - 暗紫色背景
                button:
                    background Solid("#332244")
                    padding (5, 5)
                    action NullAction()
                    hovered Show("tooltip_delay_timer", text=ac.config.desc)
                    unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                    hbox:
                        spacing 5
                        text f"{ac.config.name}" size 18 color "#cc88ff"

            elif ac.id not in (COND_FATIGUE, COND_SEVERE_FATIGUE):
                button:
                    background Solid("#222222")
                    padding (5, 5)
                    action NullAction()
                    # 悬停时显示描述
                    hovered Show("tooltip_delay_timer", text=ac.config.desc)
                    unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                    
                    hbox:
                        spacing 5
                        text f"{ac.config.name}" size 18 color "#ff3333"
