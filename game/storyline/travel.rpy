# =============================================================================
# game/storyline/travel.rpy
# 大地图主循环
# =============================================================================
label travel_on_wasteland_loop:
    window hide
    
    if player_stats.b_dead:
        jump game_over_dehydration

    # 呼叫（call）大地图 UI，游戏会在此暂停，直到玩家在界面上点击了带有 Return() 的按钮
    call screen scr_map
    
    $ action_result = _return

    # -------------------------------------------------------------------------
    # 【指令分发器】严格调用 systems 内核处理数值，此处只负责文本反馈
    # -------------------------------------------------------------------------
    if action_result == "moved":
        # 使用纯 Ren'Py 控制流，避免 Python 块中的 renpy.jump 导致的问题
        $ current_tile = world_map.grid.get((player_hex_x, player_hex_y))
        
        if current_tile and current_tile.special_feature == "merchant":
            # 直接跳转到商人事件
            jump event_merchant_encounter
        elif current_tile and current_tile.special_feature == "city":
            # 直接跳转到城市事件
            jump event_city_arrival
        elif last_map_event_code and last_map_event_code in EVENT_LABEL_MAP:
            # 有随机遭遇战
            jump expression EVENT_LABEL_MAP[last_map_event_code]
        else:
            # 普通移动
            "你继续推进到邻近的废土格子。"
            jump travel_on_wasteland_loop

    elif action_result == "scavenge":
        python:
            tile = get_current_tile()
            if tile is not None and not getattr(tile, "scavenged", False):
                scavenge_success, event_code = scavenge_current_tile()
            else:
                scavenge_success, event_code = False, None

        if scavenge_success:
            "你趴在废墟中，仔细翻找着任何有价值的旧世界遗留物...（消耗了饥饿、口渴和疲劳）"
            if event_code in EVENT_LABEL_MAP:
                python:
                    renpy.jump(EVENT_LABEL_MAP[event_code])
        else:
            "你已经搜刮过这里了（不再消耗饥饿值、口渴值、疲劳值）"
        jump travel_on_wasteland_loop

    elif action_result == "camp":
        "你找了一个相对避风的角落，开始整理物资并休息。"
        jump event_camp

    else:
        # 兜底防御，防止未知指令导致死循环报错
        jump travel_on_wasteland_loop