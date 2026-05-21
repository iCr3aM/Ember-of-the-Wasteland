# =============================================================================
# # 定义：战术战斗界面（显示敌我距离数值、双方姿态文字、可用战术动作按钮、滚动战斗日志文本框）。
# # 实现：将当前的战斗数据可视化。点击“冲锋”按钮调用 `combat.rpy`，并在日志框刷出“你向前冲锋，拉近了距离”的文本。 
# =============================================================================
# game/screens/scr_combat.rpy
screen scr_combat(combat_instance):
    modal True
    add Solid("#102030")
    
    # 顶部双向敌我属性对比横幅
    hbox:
        align (0.5, 0.1)  # ← 整体定位：水平居中，垂直10%
        spacing 100
        
        # 左侧：玩家（没有HP显示）
        vbox:
            # 尝试加载玩家头像，如果不存在则显示文字
            if renpy.loadable("images/avatar_player.png"):
                add "images/avatar_player.png" xsize 160 ysize 160 xalign 0.5
            else:
                frame:
                    xsize 160 ysize 160
                    background Solid("#4caf50")
                    text "你" size 24 color "#ffffff" align (0.5, 0.5)
            text f"{combat_instance.player.name} (你)" size 20 color "#4caf50" xalign 0.5
        
        # 中间：交战距离
        vbox:
            align (0.5, 0.25)
            text f"距离" size 28 xalign 0.5 ypos 0
            frame:
                xsize 300 ysize 30
                background Solid("#203040")
                text f"----- {combat_instance.range} 米 -----" align (0.5, 0.5) color "#ffeb3b" bold True

        # 右侧：敌人（保留HP，头像移到名字上方）
        vbox:
            $ enemy_img = f"images/avatar_creature_{combat_instance.enemy.id}.png"
            if renpy.loadable(enemy_img):
                add enemy_img xsize 160 ysize 160 xalign 0.5
            else:
                frame:
                    xsize 160 ysize 160
                    background Solid("#f44336")
                    text "敌" size 24 color "#ffffff" align (0.5, 0.5)
            text f"{combat_instance.enemy.name}" size 20 color "#f44336" xalign 0.5
            text f"HP: {combat_instance.enemy.hp:.0f}/{combat_instance.enemy.max_hp:.0f}" size 20 xalign 0.5

    # 左侧：滚动战斗日志（保持不变）
    frame:
        xpos 0.05 ypos 0.3
        xsize 450 ysize 400
        background Solid("#101010")
        padding (15, 15)
        
        viewport:
            scrollbars "vertical"
            mousewheel True
            yinitial 1.0
            vbox:
                spacing 5
                for line in combat_instance.combat_log:
                    text line size 14 color "#e0e0e0" substitute False

    # 右侧：战术动作面板
    frame:
        xpos 0.55 ypos 0.3
        xsize 500 ysize 400
        background Solid("#121824")
        padding (15, 15)
        
        vbox:
            spacing 15
            text "决定当前回合动作" size 18 xalign 0.5 color "#80deea"
            
            # 显示回合状态
            if combat_instance.is_player_turn and not combat_instance.is_finished:
                text "====你的回合====" size 16 xalign 0.5 color "#4caf50"
            elif not combat_instance.is_finished:
                text "====敌人回合====" size 16 xalign 0.5 color "#f44336"
            
            # 玩家回合才显示按钮
            if combat_instance.is_player_turn and not combat_instance.is_finished:
                # 战术动作
                text "战术动作选择" size 14 color "#b0bec5"
                hbox:
                    spacing 10
                    $ current_battle_moves = combat_instance.player.get_available_battle_moves(
                        combat_instance.enemy, combat_instance.range
                    )
                    for bm in current_battle_moves[:4]:
                        button:
                            xsize 105 ysize 60
                            # 已行动则按钮变灰
                            background Solid("#222222" if combat_instance.player_acted_this_turn else "#334455")
                            sensitive not combat_instance.player_acted_this_turn and not combat_instance.is_finished
                            action Function(combat_instance.execute_battle_move, bm, True)
                            text bm.name size 12 align (0.5, 0.5) text_align 0.5

                # 攻击模式 — 显示命中率与距离影响
                text "攻击方式选择" size 14 color "#b0bec5"
                hbox:
                    spacing 10
                    $ current_attacks = combat_instance.player.get_available_attack_modes(
                        current_range=combat_instance.range
                    )
                    for am in current_attacks:
                        $ hit_chance = combat_instance.calculate_hit_chance(am, is_player=True)
                        $ hit_color = "#4caf50" if hit_chance >= 0.7 else "#ffa726" if hit_chance >= 0.4 else "#f44336"

                        button:
                            xsize 130 ysize 95
                            background Solid("#222222" if combat_instance.player_acted_this_turn else "#445566")
                            sensitive not combat_instance.player_acted_this_turn and not combat_instance.is_finished
                            action Function(combat_instance.execute_attack, am, True)
                            vbox:
                                text "[am.name]" size 14 xalign 0.5
                                text "射程: [am.range]米" size 10 xalign 0.5 color "#ffa726"
                                text "伤害: [am.damage]" size 10 xalign 0.5 color "#ff8a80"
                                text "命中率: [hit_chance*100:.0f]%" size 10 xalign 0.5 color hit_color
            
            # 回合控制按钮
            vbox:
                ypos 40
                spacing 15
                xalign 0.5
                
                if not combat_instance.is_finished:
                    if combat_instance.is_player_turn:
                        button:
                            xsize 200 ysize 50
                            background Solid("#556677")
                            hover_background Solid("#778899")
                            action Function(combat_instance.end_turn)
                            text "结束己方回合" align (0.5, 0.5) size 16 color "#ffffff"
                    else:
                        text "敌人正在行动..." size 16 color "#ffa726" xalign 0.5
                
                # 战斗结束界面（保持不变）
                if combat_instance.is_finished:
                    frame:
                        xfill False
                        background Solid("#2a2a3a")
                        padding (15, 10)
                        vbox:
                            spacing 10
                            xalign 0.5
                            
                            if combat_instance.winner == combat_instance.player:
                                text "战斗胜利" size 18 color "#4caf50" xalign 0.5
                                
                                if not combat_instance.corpse_searched:
                                    textbutton "搜刮尸体":
                                        xfill True
                                        xsize 200
                                        ysize 40
                                        background Solid("#556644")
                                        hover_background Solid("#778866")
                                        action Function(combat_instance.search_corpse)
                                    text "搜刮尸体" size 14 color "#ffffff" align (0.5, 0.5)
                                else:
                                    text "尸体已被搜刮。" size 14 color "#aaaaaa" xalign 0.5
                                    null height 5
                            
                            button:
                                xsize 200 ysize 48
                                background Solid("#775555")
                                hover_background Solid("#997777")
                                action Return(["combat_end_trigger", combat_instance.winner])
                                text "脱离战场结算" align (0.5, 0.5) size 16 color "#00ff00"