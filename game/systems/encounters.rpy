# =============================================================================
# # 定义：大地图探索时触发的“文本遭遇事件数据库”及选项响应链。
# # 实现：解析玩家当前所拥有的技能（如“囤积狂”）或装备（如“撬棍”），动态显示或隐藏选项；处理选项后的跳转（如：走向战斗、获得宝藏、触发伤病、或跳向另一个 Encounter ID）。
# =============================================================================

# 事件编号统一管理
init -190 python:   #优先级
    EVENT_ENCOUNTER_DEFAULT = 2001
    EVENT_ENCOUNTER_AMBUSH = 2002

    EVENT_CONFIG = {
        EVENT_ENCOUNTER_DEFAULT: {
            "label": "event_encounter_default",
            "name": "丛林低吼",
            "type": "combat",
        },
        EVENT_ENCOUNTER_AMBUSH: {
            "label": "event_encounter_ambush",
            "name": "废弃检查站",
            "type": "exploration",
        },
    }

    EVENT_LABEL_MAP = {event_id: data["label"] for event_id, data in EVENT_CONFIG.items()}

label event_encounter_default:
    "丛林深处传来了低沉的嗥叫，空气中弥漫着危险的气息。"
    python:
        enemy = ActorInstance(creature_id=1, is_player=False)
        combat_instance = CombatSystem(player_stats, enemy)
    call screen scr_combat(combat_instance)
    $ encounter_result = _return
    if encounter_result and encounter_result[0] == "combat_end_trigger":
        if encounter_result[1] == player_stats:
            "你从战斗中幸存下来，身上的伤痕提醒你这片废土依然凶险。"
        else:
            "你倒在了荒野之中，视野渐渐模糊。"
            return
    jump travel_on_wasteland_loop

label event_encounter_ambush:
    "你发现了一个废弃检查站，残余的弹药和破碎的装备散落一地。"
    "没有敌人立即出现，但这里的沉寂本身就是警告。"
    jump travel_on_wasteland_loop

# ============================================================
# 死亡标签
# ==========================================================
label game_over_dehydration:
    $ player_stats.b_dead = False
    "你因极度脱水倒下，四周的景象渐渐模糊成一片白光。"
    "这一切都在饥渴与疲惫之中终结。"
    $ renpy.full_restart()

label event_city_arrival:
    "你抵达了（城市名称）。这座由废墟重建的聚居地虽然简陋，但充满了生机。"
    # 在这里可以：接取任务，休息，交易等。
    window hide
    call event_city_arrival_menu from _call_event_city_arrival_menu  # ← 调用子标签，包含循环 menu
label event_city_arrival_menu:
    menu:
        "进入交易区":
            # 创建并显示商人界面
            $ merchant_inv = Inventory()
            $ merchant_inv.add_item_by_id(103)
            $ merchant_inv.add_item_by_id(104)
            $ merchant_inv.add_item_by_id(105)
            window hide  # 隐藏对话栏
            call screen scr_shop(player_inventory, merchant_inv)
            window show # 交易结束后恢复对话栏
            "交易完毕，你清点了一下背包。"
            "你整理好物资，回到了街道上。"
            jump event_city_arrival_menu  # ← 循环回到 menu，不会显示入场文字
        "离开这里，继续旅程":
            window hide
            jump travel_on_wasteland_loop

label event_merchant_encounter:
    "一个风尘仆仆的废土商人正在树荫下歇脚，他的骆驼背上驮着满满的货箱。"
    window hide
    call event_merchant_encounter_menu from _call_event_merchant_encounter_menu  # ← 调用子标签
label event_merchant_encounter_menu:    
    menu:
        "看看他卖些什么":
            $ merchant_inv = Inventory()
            $ merchant_inv.add_item_by_id(101)
            $ merchant_inv.add_item_by_id(102)
            $ merchant_inv.add_item_by_id(201)
            window hide  # 隐藏对话栏
            call screen scr_shop(player_inventory, merchant_inv)
            window show # 交易结束后恢复对话栏
            "交易完毕，你清点了一下背包。"
            "你整理好行囊，准备继续踏上废土之旅。"
            jump event_merchant_encounter_menu
        "没什么兴趣，继续赶路":
            window hide
            jump travel_on_wasteland_loop
# ============================================================
# 扎营休息标签
# ============================================================
label event_camp:
    # 防御性检查
    if player_stats.b_dead:
        jump game_over_dehydration
    
    # 检查疲劳值是否 >= 40
    if player_stats.fatigue < 40:
        "你还不算太累，现在扎营为时过早。继续前进吧。"
        jump travel_on_wasteland_loop
    
    # 随机确定睡眠时长：6-8 小时
    $ camp_sleep_hours = renpy.random.randint(6, 8)
    
    "你找了一个相对避风的角落，开始整理物资并休息。"
    "你躺了下来，很快便进入了梦乡……"
    
    # 循环模拟每一小时
    label _event_camp_loop:
        # 如果疲劳值已降为0，提前醒来
        if player_stats.fatigue <= 0:
            $ player_stats.fatigue = 0.0
            "你的疲劳已经完全恢复，提前醒了过来。"
            jump _event_camp_wake_up
        
        # 如果睡眠时长已到，自然醒来
        if camp_sleep_hours <= 0:
            jump _event_camp_wake_up
        
        # 睡眠 1 小时
        $ camp_sleep_hours -= 1
        
        # 调用 tick_hour 模拟时间流逝（会增加疲劳、口渴等代谢）
        $ tick_hour(player_stats, 1)
        
        # 睡眠期间强制恢复疲劳：每小时减少 10 疲劳
        $ player_stats.fatigue = max(0.0, player_stats.fatigue - 10.0)
        
        # 睡眠期间口渴值只按正常消耗的一半增加
        # tick_hour 已经加了 METABOLISM_PER_HOUR['thirst']，这里减去一半
        $ player_stats.thirst = max(0.0, player_stats.thirst - 0.5 * METABOLISM_PER_HOUR['thirst'])
        
        # 更新疲劳状态
        $ update_fatigue_condition(player_stats)
        
        # 检查是否在睡眠中死亡
        if player_stats.b_dead or player_stats.thirst >= 100 or player_stats.hp <= 0:
            jump game_over_dehydration
        
        # 继续下一小时
        jump _event_camp_loop
    
    label _event_camp_wake_up:
        # 更新疲劳状态
        $ update_fatigue_condition(player_stats)
        
        "你醒了过来，感觉精神恢复了不少。"
        
        if player_stats.fatigue <= 0:
            "你精神饱满，又可以继续前进了。"
        
        $ renpy.restart_interaction()
        
        jump travel_on_wasteland_loop
