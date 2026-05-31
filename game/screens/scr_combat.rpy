# =============================================================================
# # 定义：战术战斗界面（显示敌我距离数值、双方姿态文字、可用战术动作按钮、滚动战斗日志文本框）。
# # 实现：将当前的战斗数据可视化。点击“冲锋”按钮调用 `combat.rpy`，并在日志框刷出“你向前冲锋，拉近了距离”的文本。 
# =============================================================================
# game/screens/scr_combat.rpy

init python:
    def disable_player_turn_in_combat():
        """在背包操作后禁用玩家当前回合（如果正在战斗中）"""
        global _current_combat_instance
        if _current_combat_instance and not _current_combat_instance.is_finished:
            _current_combat_instance.player_turn_disabled_by_inventory = True

    def refresh_combat_display():
        """刷新战斗显示状态"""
        renpy.restart_interaction()

screen scr_combat(combat_instance):
    # 战斗开始时淡出探索音乐（仅首次进入）
    $ music_faded = getattr(combat_instance, '_music_faded', False)
    if not music_faded:
        $ combat_instance.fade_out_music()
        $ setattr(combat_instance, '_music_faded', True)

    modal True
    add Solid("#102030")
    
    # 顶部双向敌我属性对比横幅
    hbox:
        align (0.5, 0.1)  # ← 整体定位：水平居中，垂直10%
        spacing 100
        
        # 左侧：玩家
        vbox:
            # 尝试加载玩家头像，如果不存在则显示文字
            if renpy.loadable("images/avatar_player.png"):
                add "images/avatar_player.png" xsize 160 ysize 160 xalign 0.5
            else:
                frame:
                    xsize 160 ysize 160
                    background Solid("#4caf50")
                    text "你" size 26 color "#ffffff" align (0.5, 0.5)
            text f"{combat_instance.player.name} (你)" size 26 color "#4caf50" xalign 0.5
        
        # 中间：交战距离
        vbox:
            align (0.5, 0.25)
            text f"距离" size 30 xalign 0.5 ypos -0.5
            frame:
                xsize 300 ysize 30
                background Solid("#203040")
                text f"----- {combat_instance.range} 米 -----" align (0.5, 0.5) color "#ffeb3b" bold True

        # 右侧：敌人
        vbox:
            $ enemy_img = f"images/avatar_enemy_{combat_instance.enemy.id}.png"
            if renpy.loadable(enemy_img):
                add enemy_img xsize 160 ysize 160 xalign 0.5
            else:
                frame:
                    xsize 160 ysize 160
                    background Solid("#f44336")
                    text "敌" size 26 color "#ffffff" align (0.5, 0.5)
            text f"{combat_instance.enemy.name}" size 26 color "#f44336" xalign 0.5

    # 左侧：滚动战斗日志（保持不变）
    frame:
        xpos 0.20 ypos 0.3
        xsize 600 ysize 500
        background Solid("#101010")
        padding (15, 15)
        
        viewport:
            scrollbars "vertical"
            mousewheel True
            yinitial 0.0
            vbox:
                spacing 5
                for line in reversed(combat_instance.combat_log):
                    text line size 16 color "#e0e0e0" substitute False

    # 右侧：战术动作面板
    frame:
        xpos 0.55 ypos 0.3
        xsize 500 ysize 500
        background Solid("#121824")
        padding (15, 15)
        
        vbox:
            spacing 5
            xalign 0.5
            text "决定当前回合动作" size 26 xalign 0.5 color "#80deea" bold True
            if any(ac.id == COND_FAINT for ac in combat_instance.player.active_conditions):
                text "你已经昏阙，无法行动！" size 18 color "#ff7043" xalign 0.5
            
            # 显示回合状态
            if combat_instance.is_player_turn and not combat_instance.is_finished:
                text "====你的回合====" size 18 xalign 0.5 color "#4caf50"
            elif not combat_instance.is_finished:
                text "====敌人回合====" size 18 xalign 0.5 color "#f44336"
            
            # 玩家回合才显示按钮
            if combat_instance.is_player_turn and not combat_instance.is_finished:

                hbox:
                    spacing 20
                    xalign 0.5
                    button:
                        xsize 200 ysize 50
                        background Solid("#886622")
                        hover_background Solid("#aa8844")
                        sensitive combat_instance.can_player_act()   # 如果已因背包消耗则不可再次打开
                        # 使用 Show 调用屏幕。因 scr_inventory 有 modal True，
                        # 它会阻塞战斗界面，关闭后自然返回战斗，无需 Refresh 强制重绘。
                        action Show("scr_inventory", inv_instance=player_inventory)
                        text "打开背包" align (0.5,0.5) size 18 color "#ffffff"
                null height 10  # 分隔                

                # === 战术动作（带消耗显示） ===
                text "战术动作选择" size 18 color "#b0bec5" xalign 0.5
                hbox:
                    spacing 20
                    xalign 0
                    $ current_battle_moves = combat_instance.player.get_available_battle_moves(
                        combat_instance.enemy, combat_instance.range
                    )
                    for bm in current_battle_moves[:12]:
                        button:
                            xsize 100 ysize 110
                            # 已行动则按钮变灰
                            background Solid("#222222" if not combat_instance.can_player_act() else "#334455")
                            sensitive combat_instance.can_player_act()
                            action Function(combat_instance.execute_battle_move, bm, True)
                            vbox:
                                xalign 0.5
                                text "[bm.name]" size 18 xalign 0.5 bold True
                                text "饥饿: [bm.hunger_cost]" size 16 xalign 0.5 color "#ffab40"
                                text "口渴: [bm.thirst_cost]" size 16 xalign 0.5 color "#4dd0e1"
                                text "疲劳: [bm.fatigue_cost]" size 16 xalign 0.5 color "#ce93d8"

                # 攻击模式 — 显示命中率与距离影响
                text "攻击方式选择" size 18 color "#b0bec5" xalign 0.5
                hbox:
                    spacing 20
                    $ current_attacks = combat_instance.player.get_available_attack_modes(
                        current_range=combat_instance.range
                    )
                    for am in current_attacks:
                        $ hit_chance = combat_instance.calculate_hit_chance(am, is_player=True)
                        $ hit_color = "#4caf50" if hit_chance >= 0.7 else "#ffa726" if hit_chance >= 0.4 else "#f44336"

                        button:
                            xsize 100 ysize 110
                            background Solid("#222222" if not combat_instance.can_player_act() else "#445566")
                            sensitive combat_instance.can_player_act()
                            action Function(combat_instance.execute_attack, am, True)
                            vbox:
                                xalign 0.5
                                text "[am.name]" size 18 xalign 0.5 bold True
                                text "射程: [am.range]米" size 16 xalign 0.5 color "#ffa726"
                                text "伤害: [am.damage]" size 16 xalign 0.5 color "#ff8a80"
                                text "命中率: [hit_chance*100:.0f]%" size 16 xalign 0.5 color hit_color
            
            # ===== 回合按钮 =====
            null height 20  # 留白
            if not combat_instance.is_finished:
                if combat_instance.is_player_turn:
                    # ★ 修改点1：操作背包后的提示（始终显示，不替代按钮）★
                    if combat_instance.player_turn_disabled_by_inventory:
                        text "你因为操作背包而浪费了本回合的行动机会！" size 20 color "#ffcc00" xalign 0.5
                    
                    # ★ 修改点2：结束回合按钮始终可点击（只要战斗未结束）★
                    button:
                        xalign 0.5
                        xsize 320 ysize 60
                        background Solid("#556677")
                        hover_background Solid("#778899")
                        sensitive not combat_instance.is_finished
                        action Function(combat_instance.end_turn)
                        text "结束己方回合" align (0.5, 0.5) size 20 color "#ffffff"
                else:
                    text "敌人正在行动..." size 20 color "#ffa726" xalign 0.5
            
            # ===== 战斗结束界面 =====
            if combat_instance.is_finished:
                frame:
                    xfill False
                    background Solid("#2a2a3a")
                    padding (15, 10)
                    vbox:
                        spacing 10
                        xalign 0.5
                        
                        if combat_instance.winner == combat_instance.player:
                            text "战斗胜利" size 20 color "#4caf50" xalign 0.5
                            
                            # 搜刮尸体按钮（只有击杀敌人才显示）
                            if not combat_instance.corpse_searched:
                                button:
                                    xsize 240
                                    ysize 45
                                    background Solid("#556644")
                                    hover_background Solid("#778866")
                                    action Function(combat_instance.search_corpse)
                                    text "搜刮尸体" align (0.5, 0.5) size 18 color "#ffffff"
                            else:
                                button:
                                    xsize 240 ysize 45
                                    background Solid("#444444")
                                    sensitive False
                                    text "尸体已被搜刮" align (0.5, 0.5) size 18 color "#aaaaaa"
                                    
                        elif combat_instance.winner == "player_escaped":
                            text "你逃离了战场" size 20 color "#ffa726" xalign 0.5
                            
                        elif combat_instance.winner is None:
                            text "敌人逃跑了" size 20 color "#ffa726" xalign 0.5
                            
                        else:  # 玩家失败
                            text "战斗失败" size 20 color "#f44336" xalign 0.5
                        
                        # 脱离战场结算按钮（总是显示）
                        button:
                            xsize 240 ysize 45
                            background Solid("#775555")
                            hover_background Solid("#997777")
                            action Return(["combat_end_trigger", combat_instance.winner])
                            text "脱离战场结算" align (0.5, 0.5) size 18 color "#00ff00"