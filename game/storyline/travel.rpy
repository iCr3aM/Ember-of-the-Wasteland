# =============================================================================
# travel.rpy — 大地图主循环
# 功能：定义大地图探索循环、移动/搜刮/交易/扎营指令分发
# 职责：接收 scr_map 的 Return 值，分发至各系统标签处理
# =============================================================================
image bg bg_travel = "images/bg_travel.png"

# ── 探索音乐冷却控制 ──
init python:
    import time
    last_explore_music_time = 0.0       # 上次播放探索音乐的现实时间戳
    EXPLORE_MUSIC_COOLDOWN = 1800.0     # 冷却时间：1800秒（30分钟）

# ── 大地图主循环 ──
label travel_on_wasteland_loop:
    scene bg bg_travel
    # 冷却已过且无播放时启动探索音乐（仅播放一次）
    if not renpy.music.get_playing():
        if time.time() - last_explore_music_time >= EXPLORE_MUSIC_COOLDOWN:
            play music "audio/bgm_explore.mp3" fadein 1.0  # 移除 loop 参数，只播放一次
            $ last_explore_music_time = time.time()
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
            import random
            steps = random.randint(1, 3)
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
            for _ in range(steps):
                dx, dy = random.choice(directions)
                new_x = player_hex_x + dx
                new_y = player_hex_y + dy
                if 0 <= new_x < map_width and 0 <= new_y < map_height:
                    player_hex_x = new_x
                    player_hex_y = new_y
        jump event_faint_collapse

    # 呼叫大地图 UI，等待玩家操作后 Return
    call screen scr_map
    
    $ action_result = _return

    # ── 指令分发器 ──
    if action_result == "moved":
        $ current_tile = world_map.grid.get((player_hex_x, player_hex_y))
        # 死亡/昏阙检查
        if player_stats.b_dead:
            jump game_over_death
        $ fainted = check_and_trigger_faint_travel(player_stats)
        if fainted:
            python:
                import random
                steps = random.randint(1, 3)
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                for _ in range(steps):
                    dx, dy = random.choice(directions)
                    new_x = player_hex_x + dx
                    new_y = player_hex_y + dy
                    if 0 <= new_x < map_width and 0 <= new_y < map_height:
                        player_hex_x = new_x
                        player_hex_y = new_y
            jump event_faint_collapse
        # 特殊地块事件
        elif current_tile and current_tile.special_feature == "merchant":
            "你来到了一个商人的摊点前。"
            jump travel_on_wasteland_loop
        elif last_map_event_code and last_map_event_code in EVENT_LABEL_MAP:
            jump expression EVENT_LABEL_MAP[last_map_event_code]
        elif current_tile and current_tile.special_feature == "lake_water":
            "你来到了一片湖边，浑浊的水面泛着诡异的油彩光泽。"
            jump travel_on_wasteland_loop
        else:
            "你继续前进到邻近的废土格子。"
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
            $ _points = get_current_tile().search_points if hasattr(get_current_tile(), 'search_points') else []
            if _points:
                call screen scr_search_points(_points)
            else:
                "你仔细搜索了周围，但什么也没发现。"

            # 处理搜刮点返回值
            $ _search_result = _return
            if isinstance(_search_result, (list, tuple)) and len(_search_result) >= 2:
                if _search_result[0] == "event":
                    jump expression _search_result[1]
                elif _search_result[0] == "loot":
                    $ _clicked_point = _search_result[1]
                    $ _encounter_triggered = False
                    python:
                        _encounter_triggered = roll_and_collect_search_point(_clicked_point)
                    if _encounter_triggered:
                        jump event_encounter_default
                # ★ 新增：新手礼包分支
                elif _search_result[0] == "starter_pack":
                    $ _clicked_point = _search_result[1]
                    python:
                        starter_items = roll_starter_pack()
                        tile = get_current_tile()
                        if tile and starter_items:
                            for item in starter_items:
                                tile.ground_container.add_item(item)
                            item_names = "、".join(item.config.name for item in starter_items)
                            adventure_log.append(f"你打开了物资箱，找到了：{item_names}")
                        _clicked_point.searched = True

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
        call screen scr_shop(
            player_inv=player_inventory,
            merchant_inv=merchant_inv,
            shop_type=merchant_cfg.shop_type,
            barter_rate=1.0,
            merchant_avatar=merchant_cfg.avatar_path,
            merchant_name=merchant_cfg.name
        )
        "交易完毕，你清点了一下背包，整理好行囊，准备继续踏上废土之旅。"
        jump travel_on_wasteland_loop

    elif action_result == "camp":
        jump event_camp

    else:
        # 兜底：未知指令则重新进入循环
        jump travel_on_wasteland_loop