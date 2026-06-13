# =============================================================================
# travel.rpy — 大地图主循环
# 功能：定义大地图探索循环、移动/搜刮/交易/扎营指令分发
# 职责：接收 scr_map 的 Return 值，分发至各系统标签处理
# =============================================================================
image bg bg_travel = "images/bg_travel.png"
image bg_travel_darken = Solid("#00000022")

# ── 大地图主循环 ──
label travel_on_wasteland_loop:
    scene bg_travel
    show bg_travel_darken
    # 使用游戏内时间控制音乐冷却
    if not renpy.music.get_playing(channel="music"):
        $ _music_cooldown_passed = True
        # 检查上次播放时间
        if hasattr(store, '_last_explore_music_hour') and _last_explore_music_hour >= 0:
            $ _hours_passed = (game_time['day'] - _last_explore_music_day) * 24 + (game_time['hour'] - _last_explore_music_hour)
            $ _music_cooldown_passed = _hours_passed * 60 >= EXPLORE_MUSIC_COOLDOWN_MINUTES
        if _music_cooldown_passed:
            play music "audio/bgm_explore.mp3" noloop fadein 1.0
            $ _last_explore_music_hour = game_time['hour']
            $ _last_explore_music_day = game_time['day']
        else:
            pass

    $ renpy.show_screen("scr_hud")
    window hide

    # 死亡检查
    if player_stats.b_dead:
        jump game_over_death

    # 战斗后疲劳昏阙检测（fatigue ≥ 100 → 随机走1-3格后强制睡觉）
    if player_stats.fatigue >= 100.0:
        python:
            steps = renpy.random.randint(1, 3)
            for i in range(steps):
                player_hex_x, player_hex_y = get_random_valid_hex_neighbor(player_hex_x, player_hex_y)
        jump event_faint_collapse

    # 呼叫大地图 UI，等待玩家操作后 Return
    call screen scr_map
    
    $ action_result = _return
    if action_result == "moved":
        $ auto_save_game(force=True)

    # ── 指令分发器 ──
    if action_result == "moved":
        $ current_tile = world_map.grid.get((player_hex_x, player_hex_y))
        # 死亡/昏阙检查
        if player_stats.b_dead:
            jump game_over_death
        $ fainted = check_and_trigger_faint_travel(player_stats)
        if fainted:
            python:
                steps = renpy.random.randint(1, 3)
                for i in range(steps):
                    player_hex_x, player_hex_y = get_random_valid_hex_neighbor(player_hex_x, player_hex_y)
            jump event_faint_collapse
        # 特殊地块事件
        elif current_tile and current_tile.special_feature == "merchant":
            jump travel_on_wasteland_loop
        elif last_map_event_code and last_map_event_code in EVENT_LABEL_MAP:
            jump expression EVENT_LABEL_MAP[last_map_event_code]
        else:
            jump travel_on_wasteland_loop

    elif action_result == "inspect":
        $ current_tile = get_current_tile()
        # 不再特殊处理湖泊，统一走搜刮点系统
        $ _was_inspected = getattr(current_tile, "inspected", False) if current_tile else False
        python:
            tile = get_current_tile()
            if tile is None:
                _inspect_success = False
                _event_code = None
            elif not getattr(tile, "inspected", False):
                _result = inspect_current_tile()
                _inspect_success = _result[0]
                _event_code = _result[1]
            elif has_unsearched_points(tile):
                _inspect_success = True
                _event_code = None
            else:
                _inspect_success = False
                _event_code = None

        if _inspect_success:
            if player_stats.b_dead:
                jump game_over_death
            # 使用之前保存的状态来判断
            if not _was_inspected:
                "你停下脚步，仔细观察着周围的环境..."
            else:
                "你继续翻找着之前发现的线索..."
            $ fainted = check_and_trigger_faint_travel(player_stats)
            if fainted:
                jump event_faint_collapse
            $ auto_save_game(force=True)
            $ _points = get_current_tile().search_points if hasattr(get_current_tile(), 'search_points') else []
            if _points:
                call screen scr_search_points(_points)
            else:
                "你仔细搜索了周围，但什么也没发现。"

            # 处理搜刮点返回值
            $ _search_result = _return
            if isinstance(_search_result, (list, tuple)) and len(_search_result) >= 2:
                if _search_result[0] == "event":
                    $ _clicked_point = _search_result[1]
                    $ auto_save_game(force=True)
                    jump expression _clicked_point.event_label
                    
                elif _search_result[0] == "execute_search":       # ← 直接处理，不再经过 select_mode
                    $ _point = _search_result[1]
                    $ _mode = _search_result[2]
                    
                    python:
                        # 获取模式配置
                        _mode_cfg = SEARCH_MODE_CONFIG[_mode]
                        # 获取地形消耗
                        _tile = get_current_tile()
                        _terrain_cost = SCAVENGE_COSTS.get(
                            _tile.terrain_type if _tile else "plains",
                            SCAVENGE_COSTS["plains"]
                        )
                        # 计算实际耗时
                        _base_minutes = _terrain_cost["minutes"]
                        _actual_minutes = int(_base_minutes * _mode_cfg["time_multiplier"])
                        
                        # 推进时间
                        advance_game_time(_actual_minutes)
                        
                        # 应用三维消耗
                        _hunger_cost = _terrain_cost["hunger"] * _mode_cfg["time_multiplier"]
                        _thirst_cost = _terrain_cost["thirst"] * _mode_cfg["time_multiplier"]
                        _fatigue_cost = _terrain_cost["fatigue"] * _mode_cfg["time_multiplier"]
                        player_stats.hunger = min(100.0, player_stats.hunger + _hunger_cost)
                        player_stats.thirst = min(100.0, player_stats.thirst + _thirst_cost)
                        player_stats.fatigue = min(100.0, player_stats.fatigue + _fatigue_cost)
                        tick_minutes(player_stats, _actual_minutes)
                        
                        # 获取动作描述文本
                        _action_text, _end_text = get_search_action_text(_mode, has_loot=True)
                    
                    "[_action_text]"
                    
                    python:
                        # 执行搜刮（传入模式）
                        _encounter_triggered = roll_and_collect_search_point(_point, _mode)
                    
                    if player_stats.b_dead:
                        jump game_over_death
                    
                    if _encounter_triggered:
                        python:
                            _enemy = create_weighted_enemy_for_current_terrain()
                            # 获取遇敌描述
                            _encounter_desc = get_encounter_description(_enemy, _mode)
                        
                        python:
                            for _text in _encounter_desc:
                                renpy.say(None, _text)
                        
                        $ _current_combat_instance = CombatSystem(player_stats, _enemy)
                        $ _current_combat_instance.combat_log = [(f"战斗开始！你遭遇了【{_enemy.name}】", "system")]
                        call screen scr_combat(_current_combat_instance)
                        $ _return_value = _return
                        $ _current_combat_instance.restore_music()
                        $ _current_combat_instance = None
                        $ encounter_result = _return_value
                        $ winner = None
                        python:
                            if encounter_result and isinstance(encounter_result, (list, tuple)) and encounter_result[0] == "combat_end_trigger":
                                winner = encounter_result[1]
                        if winner == player_stats:
                            "你从战斗中幸存下来，身上的伤痕提醒你这片废土依然凶险。"
                        elif winner == "player_escaped":
                            "你成功甩开了敌人，安全地离开了战场。"
                        elif winner is None:
                            "敌人仓皇逃窜，消失在了荒野之中。"
                        else:
                            jump combat_death
                        $ auto_save_game(force=True)
                    else:
                        # 无遇敌，显示结束描述
                        python:
                            # 检查地面容器是否有新物品
                            _tile = get_current_tile()
                            _has_loot = False
                            if _tile:
                                _tile.ground_container._ensure_grid_state()
                                _has_loot = bool(_tile.ground_container.grid_items)
                            _action_text, _end_text = get_search_action_text(_mode, has_loot=_has_loot)
                        "[_end_text]"
                        $ auto_save_game(force=True)

            if _event_code and _event_code in EVENT_LABEL_MAP:
                $ renpy.jump(EVENT_LABEL_MAP[_event_code])
        else:
            "这里已经没有什么值得探索的了。"
        jump travel_on_wasteland_loop

    elif action_result == "merchant_trade":
        # 获取当前地块的商人配置与库存
        python:
            current_tile = world_map.grid.get((player_hex_x, player_hex_y))
            merchant_cfg = MERCHANT_DB.get(current_tile.merchant_id, MERCHANT_WASTELAND_TRADER)
            merchant_inv = get_merchant_inventory(merchant_cfg)

        "商人上下打量了你一眼，将手里攥着的防身刀往怀里收了收。"
        # 打开交易界面
        call screen scr_unified_inventory(
            equipment_slots=player_inventory.slots,
            player_inv=player_inventory,
            secondary_inv=merchant_inv,
            screen_title="背包 / 交易",
            secondary_title="商人货架",
            mode="shop",
            close_mode="return",
            merchant_name=merchant_cfg.name,
            merchant_avatar=merchant_cfg.avatar_path,
            merchant_description=merchant_cfg.description,
            shop_type=merchant_cfg.shop_type,
            barter_rate=1.0
        )
        "交易完毕，你清点了一下背包，整理好行囊，准备继续踏上废土之旅。"
        $ auto_save_game(force=True)
        jump travel_on_wasteland_loop

    elif action_result == "camp":
        jump event_camp

    else:
        # 兜底：未知指令则重新进入循环
        jump travel_on_wasteland_loop
