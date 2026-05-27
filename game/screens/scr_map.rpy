# =============================================================================
# game/screens/scr_map.rpy
# 大地图网格与探索指令面板
# =============================================================================
# =============================================================================
# # 定义：大地图视觉渲染界面，以及周边环境搜索小面板。
# # 实现：高亮显示玩家所在格子和可移动范围，处理点击格子后的移动动画；点击搜索按钮时展示搜索风险与进度条。 
# =============================================================================
screen scr_map():
    modal True

    # 安全检查 - 使用 screen 语法中的条件显示
    if world_map is None:
        frame:
            background Solid("#440000")
            xsize 400
            ysize 200
            align (0.5, 0.5)
            text "错误：世界地图数据未加载" size 24 color "#ff6666" xalign 0.5 yalign 0.5
    else:
        hbox:
            spacing 20
            align (0.5, 0.5)

            frame:
                xsize 1400
                ysize 800
                background Solid("#111111")
                padding (15, 15)

                vbox:
                    spacing 10
                    text "大地图" size 28 color "#ffee88" xalign 0.0
                    $ current_tile = world_map.grid.get((player_hex_x, player_hex_y)) if world_map else None
                    $ current_terrain = get_map_tile_label(current_tile.terrain_type) if current_tile else "未知"
                    text f"你当前的位置: ({player_hex_x}, {player_hex_y}) - {current_terrain}" size 18 color "#cccccc"
                    null height 10

                    vbox:
                        spacing 4
                        for y in range(map_height):
                            hbox:
                                spacing 4
                                for x in range(map_width):
                                    $ tile = world_map.grid.get((x, y))
                                    $ tile_color = get_map_tile_color(tile.terrain_type) if tile else "#111111"
                                    $ is_adjacent = abs(x - player_hex_x) + abs(y - player_hex_y) == 1
                                    button:
                                        xsize 60
                                        ysize 60
                                        background Solid(tile_color)
                                        sensitive is_adjacent or (x == player_hex_x and y == player_hex_y)
                                        action If(is_adjacent, [Function(move_player_hex, x, y), Return("moved")], NullAction())

                                        if tile:
                                            if tile.special_feature == "merchant":
                                                text "商人" size 16 color "#ffd700" xalign 0.5 yalign 0.2

                                        if x == player_hex_x and y == player_hex_y:
                                            text "你" size 22 color "#000000" xalign 0.5 yalign 0.5
                                            if getattr(tile, "scavenged", False):
                                                text "已搜刮" size 12 color "#ffffff" xalign 0.9 yalign 0.9
                                        else:
                                            text get_map_tile_label(tile.terrain_type) size 14 color "#ffffff" xalign 0.5 yalign 0.5
                                            if tile and getattr(tile, "scavenged", False):
                                                text "已搜刮" size 12 color "#ffffff" xalign 0.9 yalign 0.9

            frame:
                xsize 200
                ysize 800
                background Solid("#000000cc")
                padding (20, 20)

                vbox:
                    spacing 15
                    text "行动指令" size 28 color "#ffaa00" xalign 0.5
                    $ current_tile = world_map.grid.get((player_hex_x, player_hex_y)) if world_map else None
                    textbutton "原地搜刮" :
                        xfill True
                        # 如果当前位置已搜刮过，按钮不可用
                        sensitive current_tile is not None and not getattr(current_tile, "scavenged", False)
                        action Return("scavenge")
                    textbutton "打开背包" action Show("scr_inventory", inv_instance=player_inventory) xfill True
                    textbutton "扎营休息" action Return("camp") xfill True
                    
                    # 如果当前位置是商人地块，显示“进行交易”按钮
                    if current_tile is not None and current_tile.special_feature == "merchant":
                        textbutton "进行交易" :
                            xfill True
                            action Return("merchant_trade")

                    null height 20
                    text "点击邻近格子即可移动。" size 14 color "#cccccc"
                    text "移动会消耗饥饿、增加口渴与疲劳。" size 14 color "#cccccc"