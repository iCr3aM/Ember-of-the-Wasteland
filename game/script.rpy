# =============================================================================
# script.rpy — 游戏全局入口与开发调试菜单
# 功能：定义 label start 入口、splashscreen 启动画面、调试工具菜单
# 职责：调用各系统初始化流程，重定向至序幕逻辑；提供开发阶段测试工具
# =============================================================================
# ── 调试子页面按钮样式 ──
style debug_sub_button is button:
    size_group "debug_sub"
style debug_sub_button_text is button_text:
    size 18
define config.end_splash_transition = dissolve
# ── 调试工具函数集 ──
init python:

    # CRT显示
    def append_boot(text):
        store.boot_log += text + "\n"
        renpy.restart_interaction()

    def append_status(status):
        store.boot_log = store.boot_log.rstrip("\n")
        store.boot_log += status + "\n"
        renpy.restart_interaction()

    # 移除原本映射到游戏菜单的按键（默认包含 'mouseup_3' 即右键）
    config.keymap['game_menu'].remove('mouseup_3')

    # ── HP 锁定开关 ──
    _debug_hp_locked = False

    def debug_toggle_hp_lock():
        """切换 HP 锁定状态，锁定后每帧将 HP 重置为 max_hp"""
        global _debug_hp_locked
        _debug_hp_locked = not _debug_hp_locked
        if _debug_hp_locked:
            player_stats.hp = player_stats.max_hp
            renpy.notify("HP 锁定已开启")
        else:
            renpy.notify("HP 锁定已关闭")

    def debug_enforce_hp_lock():
        """由 screen 定时器每帧调用，维持 HP 锁定（同时锁定三维，防止昏阙/死亡）"""
        if _debug_hp_locked and player_stats is not None:
            player_stats.hp = player_stats.max_hp
            player_stats.b_dead = False
            # 锁定三维，防止触发昏阙/死亡状态
            player_stats.hunger = min(player_stats.hunger, 50.0)
            player_stats.thirst = min(player_stats.thirst, 50.0)
            player_stats.fatigue = min(player_stats.fatigue, 50.0)

    # ── 装备辅助函数 ──
    def debug_equip_item(item_id):
        """创建物品并装备到对应槽位，旧装备自动卸下到背包或地面"""
        global player_inventory

        # 创建物品实例
        new_item = create_item_instance(item_id, durability=1.0)
        if new_item is None:
            renpy.notify("物品创建失败！")
            return

        slots = new_item.config.equip_slots
        if not slots:
            renpy.notify("该物品不可装备！")
            return

        slot_name = slots[0]  # 取第一个装备槽

        # 如果该槽已有装备，先卸下
        if player_inventory.slots.get(slot_name) is not None:
            old_item = player_inventory.slots[slot_name]
            # 尝试放入背包
            if not player_inventory.add_item(old_item):
                # 背包满 → 放入地面
                container = get_current_ground_container()
                if container is not None:
                    container.add_item(old_item)
                    renpy.notify(f"{old_item.config.name} 已掉落到地上。")
                else:
                    renpy.notify(f"{old_item.config.name} 丢失了！")
            player_inventory.slots[slot_name] = None

        # 装备新物品
        player_inventory.slots[slot_name] = new_item

        # 如果是背包/腰带，刷新网格
        if slot_name in ("backpack", "waist"):
            player_inventory.refresh_backpack_grid()

        renpy.notify(f"已装备：{new_item.config.name}")

    # ── 状态辅助函数 ──
    def debug_add_condition(cond_id):
        """给玩家添加指定状态"""
        if player_stats is not None:
            player_stats.add_condition(cond_id)
            cond_name = CONDITIONS_DB[cond_id].name
            renpy.notify(f"已添加状态：{cond_name}")

    def debug_remove_condition(cond_id):
        """移除玩家指定状态"""
        if player_stats is not None:
            remove_condition_by_id(player_stats, cond_id)
            cond_name = CONDITIONS_DB[cond_id].name
            renpy.notify(f"已移除状态：{cond_name}")

    def debug_set_hp_100():
        """将玩家生命值设为100（满血）。"""
        player_stats.hp = 100.0
        renpy.notify("生命值已恢复至 100")

    def debug_clear_hunger():
        """将饥饿值清0。"""
        player_stats.hunger = 0.0
        renpy.notify("饥饿值已清空")

    def debug_clear_thirst():
        """将口渴值清0。"""
        player_stats.thirst = 0.0
        renpy.notify("口渴值已清空")

    def debug_clear_fatigue():
        """将疲劳值清0。"""
        player_stats.fatigue = 0.0
        renpy.notify("疲劳值已清空")

    def debug_add_cigarettes():
        """添加67支香烟到玩家背包。"""
        player_stats.cigarettes += 67
        renpy.notify("已添加 67 支香烟")

    def debug_advance_hours(hours):
        """推进游戏时间 N 小时，并对玩家应用代谢"""
        minutes = hours * 60
        # 推进时间
        advance_game_time(minutes)
        # 应用代谢
        tick_minutes(player_stats, minutes)
        renpy.notify(f"已推进 {hours} 小时")

# ── 调试菜单界面 ──
screen debug_dev_menu():
    modal True
    tag debug_menu
    zorder 999
    frame:
        background Solid("#111111cc")
        xysize (460, 420)
        align (0.5, 0.5)
        padding (25, 25)

        vbox:
            spacing 6
            # ── 标题 ──
            text "调试工具菜单" size 22 color "#fdd835" xalign 0.5
            text "在大地图页面按下 F12 可随时打开本界面" size 16 color "#ffffff" xalign 0.5

            null height 20

            # ── 功能按钮 ──
            hbox:
                spacing 6
                xfill True

                # 左列
                vbox:
                    xsize 220
                    spacing 4
                    textbutton "装备修改器 →":
                        xfill True
                        text_size 16
                        action Show("debug_equip_menu")
                    textbutton "HP 锁定 [('ON' if _debug_hp_locked else 'OFF')]":
                        xfill True
                        text_size 16
                        action Function(debug_toggle_hp_lock)
                    textbutton "禁用遭遇战 [('已禁用' if disable_encounters else '已启用')]":
                        xfill True
                        text_size 16
                        action ToggleVariable("disable_encounters")
                    textbutton "推进 6 小时":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_advance_hours, 6)]
                    textbutton "添加 67 支香烟":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_add_cigarettes)]

                # 右列
                vbox:
                    xsize 220
                    spacing 4
                    textbutton "状态修改器 →":
                        xfill True
                        text_size 16
                        action Show("debug_condition_menu")
                    textbutton "生命值恢复至 100":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_set_hp_100)]
                    textbutton "饥饿值清0":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_clear_hunger)]
                    textbutton "口渴值清0":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_clear_thirst)]
                    textbutton "疲劳值清0":
                        xfill True
                        text_size 16
                        action [Hide("debug_dev_menu"), Function(debug_clear_fatigue)]

            null height 20

            # ── 底部关闭按钮 ──
            textbutton "关闭调试菜单":
                xalign 0.5
                text_size 22
                action Hide("debug_dev_menu")
            key "K_ESCAPE" action Hide("debug_dev_menu")
            key "K_F12" action Hide("debug_dev_menu")


# ── 装备修改器子页面 ──
screen debug_equip_menu():
    modal True
    zorder 1000
    frame:
        background Solid("#111111cc")
        xysize (620, 620)
        align (0.5, 0.5)
        padding (20, 20)

        vbox:
            xalign 0.5
            spacing 6
            text "装备修改器" size 22 color "#fdd835" xalign 0.5
            text "点击装备，旧装备自动卸下到背包或地面" size 14 color "#aaaaaa" xalign 0.5

            null height 4

            # ── 背包类 ──
            text "【背包】" size 16 color "#66ff66"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "杂物袋(2×2)" action [Function(debug_equip_item, 161), Hide("debug_equip_menu")]
                textbutton "简易挎包(3×2)" action [Function(debug_equip_item, 165), Hide("debug_equip_menu")]
                textbutton "褡裢(4×2)" action [Function(debug_equip_item, 166), Hide("debug_equip_menu")]
                textbutton "登山包(3×3)" action [Function(debug_equip_item, 167), Hide("debug_equip_menu")]
                textbutton "帆布背包(5×3)" action [Function(debug_equip_item, 168), Hide("debug_equip_menu")]
                textbutton "猎人背架(4×4)" action [Function(debug_equip_item, 169), Hide("debug_equip_menu")]
                textbutton "军用突击包(5×4)" action [Function(debug_equip_item, 170), Hide("debug_equip_menu")]
                textbutton "流浪者大背囊(5×5)" action [Function(debug_equip_item, 171), Hide("debug_equip_menu")]
                textbutton "商队驮包(5×6)" action [Function(debug_equip_item, 172), Hide("debug_equip_menu")]

            null height 4

            # ── 腰带类 ──
            text "【腰带】" size 16 color "#66ff66"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "破布条(1×2)" action [Function(debug_equip_item, 160), Hide("debug_equip_menu")]
                textbutton "简易腰包(1×3)" action [Function(debug_equip_item, 162), Hide("debug_equip_menu")]
                textbutton "战术腰封(1×4)" action [Function(debug_equip_item, 163), Hide("debug_equip_menu")]
                textbutton "拾荒者工具带(1×5)" action [Function(debug_equip_item, 164), Hide("debug_equip_menu")]

            null height 4

            # ── 武器类 ──
            text "【武器】" size 16 color "#66ff66"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "破旧手枪" action [Function(debug_equip_item, 104), Hide("debug_equip_menu")]
                textbutton "水果刀" action [Function(debug_equip_item, 109), Hide("debug_equip_menu")]
                textbutton "工具锤" action [Function(debug_equip_item, 110), Hide("debug_equip_menu")]
                textbutton "撬棍" action [Function(debug_equip_item, 111), Hide("debug_equip_menu")]

            null height 4

            # ── 鞋子类 ──
            text "【鞋子】" size 16 color "#66ff66"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "破旧军靴(左)" action [Function(debug_equip_item, 102), Hide("debug_equip_menu")]
                textbutton "破旧军靴(右)" action [Function(debug_equip_item, 119), Hide("debug_equip_menu")]
                textbutton "肮脏运动鞋(左)" action [Function(debug_equip_item, 108), Hide("debug_equip_menu")]

            null height 4

            # ── 返回按钮 ──
            textbutton "← 返回上级菜单":
                xalign 0.5
                text_size 20
                action [Hide("debug_equip_menu")]
            key "K_ESCAPE" action Hide("debug_equip_menu")
            key "K_F12" action Hide("debug_equip_menu")

# ── 状态修改器子页面 ──
screen debug_condition_menu():
    modal True
    zorder 1000
    frame:
        background Solid("#111111cc")
        xysize (700, 720)
        align (0.5, 0.5)
        padding (20, 20)

        vbox:
            xalign 0.5
            spacing 4
            text "状态修改器" size 22 color "#fdd835" xalign 0.5
            text "点击添加状态到玩家身上，右键/ESC 返回" size 14 color "#aaaaaa" xalign 0.5

            null height 4

            # ── 伤害/减益状态 ──
            text "【伤害/减益】" size 16 color "#ff8844"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "流血" action [Function(debug_add_condition, COND_BLEED), Hide("debug_condition_menu")]
                textbutton "中毒" action [Function(debug_add_condition, COND_POISON), Hide("debug_condition_menu")]
                textbutton "失衡" action [Function(debug_add_condition, COND_STAGGER), Hide("debug_condition_menu")]
                textbutton "被缠绕" action [Function(debug_add_condition, COND_ENTANGLED), Hide("debug_condition_menu")]
                textbutton "骨折" action [Function(debug_add_condition, COND_FRACTURE), Hide("debug_condition_menu")]
                textbutton "内伤" action [Function(debug_add_condition, COND_INTERNAL_INJURY), Hide("debug_condition_menu")]

            null height 4

            # ── 生存状态 ──
            text "【生存状态】" size 16 color "#ffcc66"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "口渴" action [Function(debug_add_condition, COND_THIRST), Hide("debug_condition_menu")]
                textbutton "脱水" action [Function(debug_add_condition, COND_DEHYDRATED), Hide("debug_condition_menu")]
                textbutton "极度脱水" action [Function(debug_add_condition, COND_EXTREME_DEHYDRATED), Hide("debug_condition_menu")]
                textbutton "器官衰竭" action [Function(debug_add_condition, COND_ORGAN_FAILURE), Hide("debug_condition_menu")]
                textbutton "饥饿" action [Function(debug_add_condition, COND_HUNGER), Hide("debug_condition_menu")]
                textbutton "重度饥饿" action [Function(debug_add_condition, COND_SEVERE_HUNGER), Hide("debug_condition_menu")]
                textbutton "极度饥饿" action [Function(debug_add_condition, COND_EXTREME_HUNGER), Hide("debug_condition_menu")]
                textbutton "营养不良" action [Function(debug_add_condition, COND_MALNUTRITION), Hide("debug_condition_menu")]

            null height 4

            # ── 疲劳状态 ──
            text "【疲劳】" size 16 color "#ffcc66"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "疲劳" action [Function(debug_add_condition, COND_FATIGUE), Hide("debug_condition_menu")]
                textbutton "重度疲劳" action [Function(debug_add_condition, COND_SEVERE_FATIGUE), Hide("debug_condition_menu")]
                textbutton "睡觉中" action [Function(debug_add_condition, COND_FAINT), Hide("debug_condition_menu")]

            null height 4

            # ── 战斗/脚部状态 ──
            text "【战斗/脚部】" size 16 color "#ff8844"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "进入掩体" action [Function(debug_add_condition, COND_SHELTER), Hide("debug_condition_menu")]
                textbutton "摔倒" action [Function(debug_add_condition, COND_PRONE), Hide("debug_condition_menu")]
                textbutton "濒死" action [Function(debug_add_condition, COND_MORIBUND), Hide("debug_condition_menu")]
                textbutton "赤脚" action [Function(debug_add_condition, COND_BARE_FOOT), Hide("debug_condition_menu")]
                textbutton "脚底割伤" action [Function(debug_add_condition, COND_CUT_FOOT), Hide("debug_condition_menu")]

            null height 4

            # ── 成瘾状态 ──
            text "【成瘾】" size 16 color "#aa66cc"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "尼古丁初瘾" action [Function(debug_add_condition, COND_NICOTINE_MILD), Hide("debug_condition_menu")]
                textbutton "尼古丁成瘾" action [Function(debug_add_condition, COND_NICOTINE_MODERATE), Hide("debug_condition_menu")]
                textbutton "尼古丁重瘾" action [Function(debug_add_condition, COND_NICOTINE_SEVERE), Hide("debug_condition_menu")]
            null height 4

            # ── 敌人词条 ──
            text "【敌人词条】" size 16 color "#66ff66"
            hbox:
                style_prefix "debug_sub"
                spacing 6
                box_wrap True
                textbutton "虚弱" action [Function(debug_add_condition, TRAIT_WEAK), Hide("debug_condition_menu")]
                textbutton "孱弱" action [Function(debug_add_condition, TRAIT_FRAIL), Hide("debug_condition_menu")]
                textbutton "迟缓" action [Function(debug_add_condition, TRAIT_SLUGGISH), Hide("debug_condition_menu")]
                textbutton "衰竭" action [Function(debug_add_condition, TRAIT_DECAYING), Hide("debug_condition_menu")]
                textbutton "专注" action [Function(debug_add_condition, TRAIT_FOCUSED), Hide("debug_condition_menu")]
                textbutton "耐渴" action [Function(debug_add_condition, TRAIT_DROUGHT_RESISTANT), Hide("debug_condition_menu")]
                textbutton "精力充沛" action [Function(debug_add_condition, TRAIT_ENERGETIC), Hide("debug_condition_menu")]
                textbutton "强硬" action [Function(debug_add_condition, TRAIT_TOUGH), Hide("debug_condition_menu")]
                textbutton "凶猛" action [Function(debug_add_condition, TRAIT_FEROCIOUS), Hide("debug_condition_menu")]
                textbutton "彩蛋" action [Function(debug_add_condition, TRAIT_EASTER_EGG), Hide("debug_condition_menu")]

            null height 4

            # ── 清除所有状态 ──
            textbutton "清除玩家所有状态":
                xalign 0.5
                text_size 16
                action [Function(lambda: player_stats.active_conditions.clear() if player_stats else None), Hide("debug_condition_menu")]

            null height 4

            # ── 返回按钮 ──
            textbutton "← 返回上级菜单":
                xalign 0.5
                text_size 20
                action Hide("debug_condition_menu")
            key "K_ESCAPE" action Hide("debug_condition_menu")
            key "K_F12" action Hide("debug_condition_menu")

# ── 启动画面样式常量 ──
define splash_title_size = 90   # 工作室名尺寸
define splash_text_size  = 50   # 声明文字尺寸

# ── 启动画面样式定义 ──
style splash_title:
    size 70
    color "#ffffff"
    bold True

style splash_text:
    size 32
    color "#ffffff"
    line_spacing 8

# ── 启动画面（splashscreen） ──
label splashscreen:
    # ── 禁用 ESC 菜单（保存原键位，临时清空） ──
    python:
        _saved_game_menu_keys = list(config.keymap['game_menu'])
        config.keymap['game_menu'] = []
        renpy.clear_keymap_cache()  # ← 刷新键位缓存，使修改立即生效

    show screen crt_overlay

    scene flash_white
    with Dissolve(0.02)

    scene black
    with Dissolve(0.03)

    show screen boot_terminal

    $ boot_log = ""

    $ append_boot("===================================")
    $ append_boot("         WASTELAND TERMINAL")
    $ append_boot("          BIOS VERSION 2.4")
    $ append_boot("       COPYRIGHT (C) UNKNOWN")
    $ append_boot("===================================")

    $ renpy.pause(0.8, hard=True)

    $ append_boot("")
    $ append_boot("      BOOT SEQUENCE INITIATED")

    $ renpy.pause(0.5, hard=True)

    $ append_boot("")
    $ append_boot("CPU MODULE.....................")

    $ renpy.pause(0.2, hard=True)

    $ append_status("ONLINE")
    $ renpy.play("audio/splashscreen_beep.mp3") 

    $ renpy.pause(0.3, hard=True)

    $ append_boot("MEMORY BANK.....................")

    $ renpy.pause(0.2, hard=True)

    $ append_status("64 KB")

    $ renpy.pause(0.3, hard=True)

    $ append_boot("CACHE BUFFER....................")

    $ renpy.pause(0.2, hard=True)

    $ append_status("16 KB")

    $ renpy.pause(0.3, hard=True)

    $ append_boot("SELF TEST........................")

    $ renpy.pause(0.3, hard=True)

    $ append_status("PASS")
    $ renpy.play("audio/splashscreen_beep.mp3") 

    $ renpy.pause(0.3, hard=True)

    $ append_boot("STORAGE DEVICE..................")

    $ renpy.pause(0.3, hard=True)

    $ append_status("FOUND")
    $ renpy.play("audio/splashscreen_beep.mp3") 

    $ renpy.pause(0.3, hard=True)

    $ append_boot("ARCHIVE DATABASE................")

    $ renpy.pause(0.3, hard=True)

    $ append_status("READY")
    $ renpy.play("audio/splashscreen_beep.mp3") 

    $ renpy.pause(0.3, hard=True)

    $ append_boot("")

    $ append_boot("      BOOT SEQUENCE COMPLETE")

    $ renpy.pause(1.2, hard=True)

    hide screen boot_terminal

    scene flash_white
    with Dissolve(0.02)
    $ renpy.play("audio/terminal_off.mp3") 
    scene black
    with Dissolve(0.03)

    hide screen crt_overlay

    $ renpy.pause(0.5, hard=True)

    play music "bgm_menu.mp3" fadein 1.0

    # ── 工作室名称（大号字，居中） ──
    show text "{size=[splash_title_size]}Cr3aM Studio{/size}" at truecenter with dissolve
    $ renpy.pause(2.0, hard=True)
    hide text with dissolve
    with Pause(0.5)

    # ── 游戏声明 ──
    show text "{size=[splash_text_size]}\n本游戏可能含有恐怖、惊悚元素。\n游戏基于Ren'Py引擎制作，采用AI生成图像与音乐素材。\n本作为单机游戏，不收集任何个人信息。\n\n所有内容纯属虚构。\n如有雷同，纯属巧合。{/size}" at truecenter with dissolve
    $ renpy.pause(3.0, hard=True)
    hide text with dissolve
    with Pause(0.5)

    # 回到纯黑色背景
    scene black

    with Pause(0.2)

    # ── 恢复 ESC 菜单键位 ──
    python:
        config.keymap['game_menu'] = _saved_game_menu_keys
        renpy.clear_keymap_cache()  # ← 刷新键位缓存
        del _saved_game_menu_keys
    
    return


# ── 游戏主入口 ──
label start:
    # 主题曲淡出（1.5秒）
    stop music fadeout 1.5
    
    # 等待淡出完成（可选：如果希望淡出完毕后文字才开始显示）
    $ renpy.pause(0.5, hard=True)

    scene black with dissolve
    $ renpy.pause(0.3, hard=True)

    # 如果此时音乐未在播放（从 splashscreen 进入时已在播，从其他地方进入可能没有）
    if not renpy.music.is_playing():
        play music "bgm_menu.mp3" fadein 1.0
    
    python:
        # 激活内核单例
        initialize_game_systems()

    # 平滑跨文件转移至序幕逻辑
    jump prologue_start

# ── 清理待移除物品 ──
label cleanup_pending_removals:
    python:
        while _pending_inventory_removals:
            item = _pending_inventory_removals.pop()
            if item in player_inventory.backpack_grid:
                player_inventory.remove_item(item)
    return

# ── CRT显示效果 ──
default boot_log = ""
image flash_white = Solid("#CCFFCC")
image flash_black = Solid("#000000")

transform crt_flicker:

    alpha 1.0
    linear 0.08 alpha 0.95
    linear 0.06 alpha 1.0
    repeat

screen crt_overlay():
    zorder 999
    add "gui/crt_scanline.png" at crt_flicker

screen boot_terminal():

    zorder 100
    add "#000000"

    text boot_log:
        xpos 300
        ypos 80
        color "#66ff66"
        size 32
        font "fusion-pixel-12px-monospaced-zh_hans.ttf"   # 等宽字体
        text_align 0.0

    # 右上角带边框的状态面板（强制使用等宽字体）
    text "╔═════════╗\n║ POWER:   STABLE  ║\n║ RAD:     0.12µSv ║\n║ CPU:     23°C    ║\n║ UPTIME:  247d    ║\n║ LINK:    REMOTE  ║\n╚═════════╝":
        xpos 1720
        ypos 80
        xanchor 1.0
        xoffset -80                         # 距离右边80像素，与左侧对称
        color "#66ff66"
        size 32
        font "fusion-pixel-12px-monospaced-zh_hans.ttf"
        text_align 0.5                     # 框内文字居中（也可以 0.0 左对齐）

    # 底部功能键提示（也建议使用等宽字体，保证对齐）
    text "[[F1] HELP   [[F2] LOAD   [[F11] SETTINGS   [[F12] QUIT   | BIOS v2.4   | (C) UNKNOWN":
        xalign 0.5
        yalign 1.0
        yoffset -30
        color "#66ff66"
        size 32
        font "fusion-pixel-12px-monospaced-zh_hans.ttf"