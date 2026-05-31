# =============================================================================
# game/storyline/travel.rpy
# 大地图主循环
# =============================================================================
image bg bg_travel = "images/bg_travel.png"

init python:
    import time
    # 记录上次播放探索音乐的现实时间（时间戳）
    last_explore_music_time = 0.0
    # 冷却时间：1800秒 = 30分钟
    EXPLORE_MUSIC_COOLDOWN = 1800.0

label travel_on_wasteland_loop:
    scene bg bg_travel
    # 进入大地图开始播放探索音乐（仅在未播放且冷却已过时启动）
    if not renpy.music.get_playing():
        if time.time() - last_explore_music_time >= EXPLORE_MUSIC_COOLDOWN:
            play music "audio/bgm_explore.mp3" fadein 1.0  # 移除 loop 参数，只播放一次
            $ last_explore_music_time = time.time()
        else:
            # 冷却期内，不播放音乐（但也不显示提示，保持安静即可）
            pass

    $ renpy.show_screen("scr_hud")
    window hide
    
    if player_stats.b_dead:
        jump game_over_death

    # 呼叫（call）大地图 UI，游戏会在此暂停，直到玩家在界面上点击了带有 Return() 的按钮
    call screen scr_map
    
    $ action_result = _return

    # -------------------------------------------------------------------------
    # 【指令分发器】严格调用 systems 内核处理数值，此处只负责文本反馈
    # -------------------------------------------------------------------------
    if action_result == "moved":
        $ current_tile = world_map.grid.get((player_hex_x, player_hex_y))
        if player_stats.b_dead:
            jump game_over_death
        $ fainted = check_and_trigger_faint_travel(player_stats)
        if fainted:
            jump event_faint_collapse
        elif current_tile and current_tile.special_feature == "merchant":
            "你来到了一个商人的摊点前。"
            jump travel_on_wasteland_loop
        elif last_map_event_code and last_map_event_code in EVENT_LABEL_MAP:
            # 优先判定遇敌
            jump expression EVENT_LABEL_MAP[last_map_event_code]
        elif current_tile and current_tile.special_feature == "lake_water":
            # 仅在无遇敌时显示湖水文本
            "你来到了一片湖边，浑浊的水面泛着诡异的油彩光泽。"
            jump travel_on_wasteland_loop
        else:
            "你继续前进到邻近的废土格子。"
            jump travel_on_wasteland_loop

    elif action_result == "scavenge":
        $ current_tile = get_current_tile()
        if current_tile and current_tile.special_feature == "lake_water":
            jump encounter_lake_water          # 湖泊搜刮触发事件
        else:
            python:
                tile = get_current_tile()
                if tile is not None and not getattr(tile, "scavenged", False):
                    scavenge_success, event_code = scavenge_current_tile()
                else:
                    scavenge_success, event_code = False, None

            if scavenge_success:
                if player_stats.b_dead:
                    jump game_over_death
                "你趴在废墟中，仔细翻找着任何有价值的旧世界遗留物..."
                # 搜刮后也检查昏阙
                $ fainted = check_and_trigger_faint_travel(player_stats)
                if fainted:
                    jump event_faint_collapse
                if event_code in EVENT_LABEL_MAP:
                    python:
                        renpy.jump(EVENT_LABEL_MAP[event_code])
            else:
                "你已经搜刮过这里了。"
            jump travel_on_wasteland_loop

    elif action_result == "merchant_trade":
        # 获取当前地块的商人配置
        python:
            current_tile = world_map.grid.get((player_hex_x, player_hex_y))
            merchant_cfg = MERCHANT_DB.get(current_tile.merchant_id, MERCHANT_WASTELAND_TRADER)
            merchant_inv = get_merchant_inventory(merchant_cfg)

        "商人上下打量了你一眼，将手里攥着的防身刀往怀里收了收。"
            
        call screen scr_shop(
            player_inv=player_inventory,
            merchant_inv=merchant_inv,
            shop_type=merchant_cfg.shop_type,
            barter_rate=1.0,
            merchant_avatar=merchant_cfg.avatar_path,
            merchant_name=merchant_cfg.name
        )
        "交易完毕，你清点了一下背包。"
        "你整理好行囊，准备继续踏上废土之旅。"
        jump travel_on_wasteland_loop

    elif action_result == "camp":
        jump event_camp

    else:
        # 兜底防御，防止未知指令导致死循环报错
        jump travel_on_wasteland_loop