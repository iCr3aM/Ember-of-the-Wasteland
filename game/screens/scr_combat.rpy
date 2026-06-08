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

    def get_combat_conditions_display(actor):
        """返回 (条件列表, 颜色元组) 用于战斗界面显示"""
        conditions = []
        for ac in actor.active_conditions:
            bg, color = get_condition_display_colors(ac.id)
            conditions.append((ac.config.name, ac.config.desc, bg, color))
        return conditions
    
    def get_combat_attack_info(combat, attack_mode):
        """返回攻击的命中率和颜色"""
        hit_chance = combat.calculate_hit_chance(attack_mode, is_player=True)
        if hit_chance >= 0.7:
            hit_color = "#4caf50"
        elif hit_chance >= 0.4:
            hit_color = "#ffa726"
        else:
            hit_color = "#f44336"
        return hit_chance, hit_color
    
    def is_in_shelter(actor):
        return any(ac.id == COND_SHELTER for ac in actor.active_conditions)
    
    def is_prone(actor):
        return any(ac.id == COND_PRONE for ac in actor.active_conditions)

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
            if renpy.loadable("images/avatar/avatar_player.png"):
                add "images/avatar/avatar_player.png" xsize 200 ysize 200 fit "contain" xalign 0.5
            else:
                frame:
                    xsize 160 ysize 160
                    background Solid("#4caf50")
                    text "你" size 26 color "#ffffff" align (0.5, 0.5)
            text f"{combat_instance.player.name}" size 26 color "#4caf50" xalign 0.5
        
        # 中间：交战距离
        vbox:
            align (0.5, 0.25)
            text f"距离" size 30 xalign 0.5 ypos -0.5
            frame:
                xsize 300 ysize 30
                background Solid("#203040")
                text f"----- {combat_instance.range} 米 -----" align (0.5, 0.5) color "#ffeb3b" bold True

        # 右侧：敌人（头像+名称）
        vbox:
            $ enemy_img = f"images/avatar/avatar_enemy_{combat_instance.enemy.id}.png"
            if renpy.loadable(enemy_img):
                add enemy_img xsize 200 ysize 200 fit "contain" xalign 0.5
            else:
                frame:
                    xsize 160 ysize 160
                    background Solid("#f44336")
                    text "敌" size 26 color "#ffffff" align (0.5, 0.5)
            text f"{combat_instance.enemy.name}" size 26 color "#f44336" xalign 0.5

    # 敌人状态独立面板（锚定在右侧，与敌人头像对齐）
    hbox:
        xpos 0.70
        ypos 0.1
        vbox:
            spacing 4
            text "状态" size 16 color "#b0bec5" xalign 0.5
            $ enemy_conditions = combat_instance.enemy.active_conditions
            if enemy_conditions:
                for ac in enemy_conditions:
                    $ cond_name = ac.config.name
                    $ cond_desc = ac.config.desc
                    python:
                        _bg, _color = get_condition_display_colors(ac.id)
                        cond_bg = _bg
                        cond_color = _color
                    button:
                        background Solid(cond_bg)
                        padding (4, 3)
                        action NullAction()
                        hovered Show("tooltip_delay_timer", text=cond_desc)
                        unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                        text cond_name size 15 color cond_color xalign 0.5

    # 左侧：滚动战斗日志（保持不变）
    frame:
        xpos 0.15 ypos 0.3
        xsize 500 ysize 500
        background Solid("#101010")
        padding (15, 15)
        
        viewport:
            scrollbars "vertical"
            mousewheel True
            yinitial 0.0
            vbox:
                spacing 5
                for entry in reversed(combat_instance.combat_log):
                    $ line_text = entry[0]
                    $ line_owner = entry[1]
                    if line_owner == "player":
                        $ line_color = "#4caf50"
                    elif line_owner == "enemy":
                        $ line_color = "#f44336"
                    else:
                        $ line_color = "#e0e0e0"
                    text line_text size 16 color line_color substitute False

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

            # ===== 战斗进行中：显示回合状态和行动面板 =====
            if not combat_instance.is_finished:
                # 显示回合状态
                if combat_instance.is_player_turn:
                    text "====你的回合====" size 18 xalign 0.5 color "#4caf50"
                else:
                    text "====敌人回合====" size 18 xalign 0.5 color "#f44336"
                
                # 玩家回合才显示按钮
                if combat_instance.is_player_turn:

                    hbox:
                        spacing 20
                        xalign 0.5
                        button:
                            xsize 150 ysize 50
                            background Solid("#886622")
                            hover_background Solid("#aa8844")
                            sensitive combat_instance.can_player_act()
                            action Show("scr_inventory", inv_instance=player_inventory)
                            text "打开背包" align (0.5,0.5) size 18 color "#ffffff"
                    null height 10

                    $ player_in_shelter = is_in_shelter(combat_instance.player)
                    $ player_is_prone = is_prone(combat_instance.player)
                    $ shelter_move_ids = [9, 10, 11]
                    $ prone_move_ids = [12]

                    text "战术动作选择" size 18 color "#b0bec5" xalign 0.5
                    $ current_battle_moves = combat_instance.player.get_available_battle_moves(
                        combat_instance.enemy, combat_instance.range
                    )
                    $ battle_move_rows = max(2, (len(current_battle_moves) + 3) // 4)
                    if player_in_shelter:
                        $ current_battle_moves = [bm for bm in current_battle_moves if bm.id in shelter_move_ids]
                    if player_is_prone:
                        $ current_battle_moves = [bm for bm in current_battle_moves if bm.id in prone_move_ids]

                    grid 4 battle_move_rows:
                        spacing 10
                        xfill True
                        yfill False
                        for bm in current_battle_moves:
                            button:
                                xsize 100 ysize 40
                                background Solid("#222222" if not combat_instance.can_player_act() else "#334455")
                                hover_background Solid("#556677")
                                sensitive combat_instance.can_player_act() and bm.id not in combat_instance.move_cooldowns
                                hovered Show("tooltip_delay_timer", text=bm.desc)
                                unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                                action [
                                    Function(combat_instance.execute_battle_move, bm, True),
                                    Hide("tooltip_delay_timer"),
                                    Hide("floating_tooltip")
                                ]
                                vbox:
                                    xalign 0.5
                                    text "[bm.name]" size 18 xalign 0.5 bold True

                    text "攻击方式选择" size 18 color "#b0bec5" xalign 0.5
                if player_is_prone:
                    text "你摔倒在地，无法发动攻击！" size 16 color "#ff6b6b" xalign 0.5
                elif not player_in_shelter:
                    $ current_attacks = combat_instance.player.get_available_attack_modes(
                        current_range=combat_instance.range
                    )
                    $ attack_rows = max(2, (len(current_attacks) + 3) // 4)

                    grid 4 attack_rows:
                        spacing 10
                        xfill True
                        yfill False
                        for am in current_attacks:
                            $ hit_chance = combat_instance.calculate_hit_chance(am, is_player=True)
                            $ hit_color = "#4caf50" if hit_chance >= 0.7 else "#ffa726" if hit_chance >= 0.4 else "#f44336"

                            button:
                                xsize 100 ysize 40
                                background Solid("#222222" if not combat_instance.can_player_act() else "#445566")
                                sensitive combat_instance.can_player_act()
                                hovered Show("tooltip_delay_timer", text=am.desc)
                                unhovered [Hide("tooltip_delay_timer"), Hide("floating_tooltip")]
                                action [
                                    Function(combat_instance.execute_attack, am, True),
                                    Hide("tooltip_delay_timer"),
                                    Hide("floating_tooltip")
                                ]
                                vbox:
                                    xalign 0.5
                                    text "[am.name]" size 18 xalign 0.5 bold True color hit_color
                else:
                    text "掩体中无法发动普通攻击。" size 16 color "#ffcc00" xalign 0.5

                # ===== 回合按钮 =====
                null height 20
                if combat_instance.is_player_turn:
                    if combat_instance.player_turn_disabled_by_inventory:
                        text "你因操作背包而失去了本回合的行动机会" size 20 color "#ffcc00" xalign 0.5
                    
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
            
            # ===== 战斗结束：只显示结果和结算按钮 =====
            else:
                frame:
                    xalign 0.5
                    xsize 320
                    background Solid("#2a2a3a")
                    padding (15, 10)
                    vbox:
                        spacing 10
                        xalign 0.5
                        
                        if combat_instance.winner == combat_instance.player:
                            text "战斗胜利" size 20 color "#4caf50" xalign 0.5
                            
                            if not combat_instance.corpse_searched:
                                button:
                                    xsize 280
                                    ysize 45
                                    background Solid("#556644")
                                    hover_background Solid("#778866")
                                    action Function(combat_instance.search_corpse)
                                    text "搜刮尸体" align (0.5, 0.5) size 18 color "#ffffff"
                            else:
                                button:
                                    xsize 280 ysize 45
                                    background Solid("#444444")
                                    sensitive False
                                    text "尸体已被搜刮" align (0.5, 0.5) size 18 color "#aaaaaa"
                                    
                        elif combat_instance.winner == "player_escaped":
                            text "你逃离了战场" size 20 color "#ffa726" xalign 0.5
                            
                        elif combat_instance.winner is None:
                            text "敌人逃跑了" size 20 color "#ffa726" xalign 0.5
                            
                        else:
                            text "战斗失败" size 20 color "#f44336" xalign 0.5
                        
                        button:
                            xsize 280 ysize 45
                            background Solid("#775555")
                            hover_background Solid("#997777")
                            action Return(["combat_end_trigger", combat_instance.winner])
                            text "脱离战场结算" align (0.5, 0.5) size 18 color "#00ff00"