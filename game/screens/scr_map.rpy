# =============================================================================
# game/screens/scr_map.rpy
# 大地图网格与探索指令面板
# =============================================================================
# =============================================================================
# # 定义：大地图视觉渲染界面，以及周边环境搜索小面板。
# # 实现：高亮显示玩家所在格子和可移动范围，处理点击格子后的移动动画；点击搜索按钮时展示搜索风险与进度条。 
# =============================================================================
init python:
    import math

    MAP_VIEW_WIDTH = 7    # 横向显示 7 格
    MAP_VIEW_HEIGHT = 5   # 纵向显示 5 格
    MAP_OVERFLOW_TILES = 3
    MAP_HEX_WIDTH = 188
    MAP_HEX_HEIGHT = 100
    MAP_HEX_GAP = 4
    MAP_HEX_BEVEL = MAP_HEX_WIDTH // 4
    MAP_HEX_SIDE_LENGTH = math.sqrt(MAP_HEX_BEVEL * MAP_HEX_BEVEL + (MAP_HEX_HEIGHT / 2.0) ** 2)
    MAP_HEX_X_GAP = int(round(MAP_HEX_GAP * MAP_HEX_SIDE_LENGTH / (MAP_HEX_HEIGHT / 2.0)))
    MAP_HEX_X_STEP = MAP_HEX_WIDTH - MAP_HEX_BEVEL + MAP_HEX_X_GAP
    MAP_HEX_Y_STEP = MAP_HEX_HEIGHT + MAP_HEX_GAP
    MAP_HEX_COL_OFFSET = MAP_HEX_Y_STEP // 2
    MAP_FRAME_WIDTH = 1212
    MAP_FRAME_HEIGHT = (MAP_VIEW_HEIGHT - 1) * MAP_HEX_Y_STEP + MAP_HEX_HEIGHT + MAP_HEX_COL_OFFSET

    def _hex_color_to_rgba(color, alpha=255):
        if isinstance(color, tuple):
            return color
        value = color.lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        if len(value) == 6:
            return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)
        if len(value) == 8:
            return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), int(value[6:8], 16))
        return (68, 68, 68, alpha)

    def _tint_hex_color(color, amount=24):
        r, g, b, a = _hex_color_to_rgba(color)
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        return "#{:02x}{:02x}{:02x}{:02x}".format(r, g, b, a)

    def _flat_hex_points(width, height):
        bevel = int(width * 0.25)
        return [
            (bevel, 0),
            (width - bevel, 0),
            (width - 1, height // 2),
            (width - bevel, height - 1),
            (bevel, height - 1),
            (0, height // 2),
        ]

    class FlatHexTileBackground(renpy.Displayable):
        def __init__(self, fill_color, outline_color="#222222", line_width=2, **properties):
            super(FlatHexTileBackground, self).__init__(**properties)
            self.fill_color = fill_color
            self.outline_color = outline_color
            self.line_width = line_width

        def render(self, width, height, st, at):
            width = int(width or MAP_HEX_WIDTH)
            height = int(height or MAP_HEX_HEIGHT)
            render = renpy.Render(width, height)
            canvas = render.canvas()
            points = _flat_hex_points(width, height)
            canvas.polygon(_hex_color_to_rgba(self.fill_color), points, 0)
            if self.outline_color and self.line_width > 0:
                canvas.polygon(_hex_color_to_rgba(self.outline_color), points, self.line_width)
            return render
    
screen scr_map():
    zorder 90
    modal True

    key "K_F12" action Show("debug_dev_menu")
    key "i" action Show(
        "scr_unified_inventory",
        equipment_slots=player_inventory.slots,
        player_inv=player_inventory,
        secondary_inv=get_current_ground_container() if get_current_ground_container() is not None else Inventory(max_slots=0),
        screen_title="背包 / 地面",
        secondary_title="地面",
        mode="ground",
        close_mode="hide"
    )
    timer 0.2 action Function(debug_enforce_hp_lock) repeat True
    
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
            spacing 10
            align (0.5, 0.5)

            frame:
                xsize 1250
                ysize 900
                background Solid("#111111")
                padding (15, 15)

                vbox:
                    spacing 6
                    text "大地图" size 28 color "#ffee88" xalign 0.0
                    $ current_tile = world_map.grid.get((player_hex_x, player_hex_y)) if world_map else None
                    $ current_terrain = get_map_tile_label(current_tile.terrain_type) if current_tile else "未知"
                    $ has_map = (player_inventory.slots.get("left_hand") is not None and player_inventory.slots["left_hand"].id == 154)
                    if has_map:
                        text f"你当前的位置: ({player_hex_x}, {player_hex_y}) - {current_terrain}" size 18 color "#88ccff"
                    else:
                        text f"你当前的位置: (?, ?) - {current_terrain}" size 18 color "#666666"
                    null height 4

                    # ★ 计算视图窗口：玩家居中，7×5；实际绘制范围向外溢出 3 格供 viewport 裁剪 ★
                    $ view_cols = MAP_VIEW_WIDTH
                    $ view_rows = MAP_VIEW_HEIGHT
                    $ draw_cols = view_cols + MAP_OVERFLOW_TILES * 2
                    $ draw_rows = view_rows + MAP_OVERFLOW_TILES * 2
                    $ start_x = player_hex_x - view_cols // 2 - MAP_OVERFLOW_TILES
                    $ start_y = player_hex_y - view_rows // 2 - MAP_OVERFLOW_TILES
                    $ map_canvas_width = (draw_cols - 1) * MAP_HEX_X_STEP + MAP_HEX_WIDTH
                    $ map_canvas_height = (draw_rows - 1) * MAP_HEX_Y_STEP + MAP_HEX_HEIGHT + MAP_HEX_COL_OFFSET
                    $ player_local_x = (player_hex_x - start_x) * MAP_HEX_X_STEP + MAP_HEX_WIDTH // 2
                    $ player_local_y = (player_hex_y - start_y) * MAP_HEX_Y_STEP + (MAP_HEX_COL_OFFSET if player_hex_x % 2 else 0) + MAP_HEX_HEIGHT // 2
                    $ map_scroll_x = int(player_local_x - MAP_FRAME_WIDTH // 2)
                    $ map_scroll_y = int(player_local_y - MAP_FRAME_HEIGHT // 2)
                    $ map_outer_width = MAP_FRAME_WIDTH + 8
                    $ map_outer_height = MAP_FRAME_HEIGHT + 8

                    frame:
                        xsize map_outer_width
                        ysize map_outer_height
                        background Solid("#3a3320")
                        padding (4, 4)
                        viewport:
                            xsize MAP_FRAME_WIDTH
                            ysize MAP_FRAME_HEIGHT
                            child_size (map_canvas_width, map_canvas_height)
                            xinitial map_scroll_x
                            yinitial map_scroll_y
                            draggable False
                            mousewheel False
                            fixed:
                                xsize map_canvas_width
                                ysize map_canvas_height
                                for y in range(start_y, start_y + draw_rows):
                                    for x in range(start_x, start_x + draw_cols):
                                        $ tile = world_map.grid.get((x, y))
                                        $ tile_color = get_map_tile_color(tile.terrain_type) if tile else "#111111"
                                        $ is_current = (x == player_hex_x and y == player_hex_y)
                                        $ is_adjacent = is_hex_adjacent(player_hex_x, player_hex_y, x, y)
                                        $ row_index = y - start_y
                                        $ col_index = x - start_x
                                        $ tile_xpos = col_index * MAP_HEX_X_STEP
                                        $ tile_ypos = row_index * MAP_HEX_Y_STEP + (MAP_HEX_COL_OFFSET if x % 2 else 0)
                                        $ outline_color = "#ffee88" if is_current else None
                                        button:
                                            xpos tile_xpos
                                            ypos tile_ypos
                                            xsize MAP_HEX_WIDTH
                                            ysize MAP_HEX_HEIGHT
                                            padding (0, 0)
                                            background FlatHexTileBackground(tile_color, outline_color)
                                            hover_background FlatHexTileBackground(_tint_hex_color(tile_color), outline_color)
                                            insensitive_background FlatHexTileBackground(tile_color, outline_color)
                                            focus_mask True
                                            sensitive tile is not None and (is_adjacent or is_current)
                                            activate_sound "audio/map_footstep.mp3"
                                            action If(tile is not None and is_adjacent, [Function(move_player_hex, x, y), Return("moved")], NullAction())

                                            if tile:
                                                if tile.special_feature == "merchant":
                                                    text "商人" size 16 color "#ffd700" xalign 0.5 yalign 0.2

                                            if is_current:
                                                text "你" size 22 color "#000000" xalign 0.5 yalign 0.5
                                                if tile and has_ground_items(tile):
                                                    text "有物品" size 12 color "#ffcc00" xalign 0.12 yalign 0.18
                                                if getattr(tile, "inspected", False):
                                                    if has_unsearched_points(tile):
                                                        text "已探索" size 12 color "#ffffff" xalign 0.88 yalign 0.82
                                                    else:
                                                        text "已搜刮" size 12 color "#aaaaaa" xalign 0.88 yalign 0.82
                                            else:
                                                if tile:
                                                    text get_map_tile_label(tile.terrain_type) size 14 color "#ffffff" xalign 0.5 yalign 0.5
                                                if tile and has_ground_items(tile):
                                                    text "有物品" size 12 color "#ffcc00" xalign 0.12 yalign 0.18
                                                if tile and getattr(tile, "inspected", False):
                                                    if has_unsearched_points(tile):
                                                        text "已探索" size 12 color "#ffffff" xalign 0.88 yalign 0.82
                                                    else:
                                                        text "已搜刮" size 12 color "#aaaaaa" xalign 0.88 yalign 0.82
                    # 冒险日志
                    null height 10
                    frame:
                        xsize 600
                        ysize 200
                        background Solid("#0a0a0a")
                        padding (8, 8)
                        vbox:
                            text "------------------------冒险日志------------------------" size 20 color "#ffaa00" xalign 0.5
                            viewport:
                                yinitial 0.0
                                scrollbars "vertical"
                                mousewheel True
                                xfill True
                                yfill True
                                vbox:
                                    spacing 2
                                    for entry in reversed(adventure_log[-8:]):
                                        text "[entry]" size 16 color "#aaaaaa"
            frame:
                xsize 190
                ysize 900
                background Solid("#000000cc")
                padding (20, 20)

                vbox:
                    spacing 15
                    text "行动指令" size 28 color "#ffaa00" xalign 0.5
                    $ current_tile = world_map.grid.get((player_hex_x, player_hex_y)) if world_map else None
                    $ _can_inspect = current_tile is not None and not getattr(current_tile, "inspected", False)
                    $ _has_unsearched = current_tile is not None and has_unsearched_points(current_tile)
                    $ _inspect_label = "探索区域" if _can_inspect else "继续搜刮" if _has_unsearched else "探索完毕"

                    textbutton "[_inspect_label]" :
                        xfill True
                        sensitive current_tile is not None and (_can_inspect or _has_unsearched)
                        action Return("inspect")
                    textbutton "装备拾取":
                        xfill True
                        action Show(
                            "scr_unified_inventory",
                            equipment_slots=player_inventory.slots,
                            player_inv=player_inventory,
                            secondary_inv=current_tile.ground_container if current_tile is not None else Inventory(max_slots=0),
                            screen_title="背包/地面",
                            secondary_title="地面",
                            mode="ground",
                            close_mode="hide"
                        )
                    textbutton "扎营休息" action Return("camp") xfill True
                    
                    # 如果当前位置是商人地块，显示“进行交易”按钮
                    if current_tile is not None and current_tile.special_feature == "merchant":
                        textbutton "进行交易" :
                            xfill True
                            action Return("merchant_trade")

                    null height 20
                    text "点击邻近格子即可移动。" size 16 color "#cccccc"
                    text "移动会消耗饥饿、增加口渴与疲劳。" size 16 color "#cccccc"
