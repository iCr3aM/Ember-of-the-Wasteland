# =============================================================================
# # 定义：大地图探索时触发的“文本遭遇事件数据库”及选项响应链。
# # 实现：解析玩家当前所拥有的技能（如“囤积狂”）或装备（如“撬棍”），动态显示或隐藏选项；处理选项后的跳转（如：走向战斗、获得宝藏、触发伤病、或跳向另一个 Encounter ID）。
# =============================================================================
# 事件编号统一管理
init -190 python:   #优先级
    EVENT_ENCOUNTER_DEFAULT = 2001
    #EVENT_ENCOUNTER_ = 2002
    TEST_ENEMY_IDS = [1, 3, 4, 7, 9, 11] 


    EVENT_CONFIG = {
        EVENT_ENCOUNTER_DEFAULT: {
            "label": "event_encounter_default",
            "name": "丛林低吼",
            "type": "combat",
        #},
        #EVENT_ENCOUNTER_: {
            #"label": "event_",
            #"name": "",
            #"type": "",
        },
    }

    EVENT_LABEL_MAP = {event_id: data["label"] for event_id, data in EVENT_CONFIG.items()}

# ==========================================================
# 事件标签
# ==========================================================
label encounter_lake_water:

    "你蹲在浑浊的湖边，水面泛着诡异的油彩光泽。"
    "水波之下，隐约可见发白的死鱼翻着肚皮，一股铁锈与腐败混合的气味钻进鼻腔。"
    "但这一切，都无法掩盖你喉咙里那火烧火燎的干渴。"

    if player_stats.thirst < 30:

        "你目前还能忍受这种干渴，理智告诉你这水碰不得。"
        "你站起身，从湖边离开。"

        jump travel_on_wasteland_loop      

    menu:
        "你盯着这片致命的水光，喉结滚动了一下："
        "趴下去，喝个痛快！":
            $ drank_lake_water = True

            "理智在这一刻被本能的渴望彻底击溃。"
            "你双膝跪地，双手撑在泥泞里，像野兽一样把脸埋进水中，大口大口地吞咽。"
            "水是温热的，带着浓重的金属腥味，但顺着喉咙流下去的那一刻，你感觉自己仿佛重获新生。"

            call drink_lake_water_consequence from _call_drink_lake_water_consequence

            jump travel_on_wasteland_loop

        "死死忍住，别上头……":
            $ drank_lake_water = False

            "你用仅存的意志力对抗着身体的哀嚎。"
            "指甲深深掐进掌心，疼痛让你短暂分神。你咬紧牙关，强迫自己转过身，背对着那片诱惑。"
            "不能喝。喝了可能会死得更快。"

            jump travel_on_wasteland_loop

label drink_lake_water_consequence:
    # 立即解除或缓解口渴
    $ player_stats.thirst = max(0, player_stats.thirst - 40)  # 大量补水
    $ update_thirst_condition(player_stats)  # 自动维护口渴状态（会自动移除脱水等状态）
    $ import random
    if random.randint(1, 100) <= 50:
        # ----- 中招 -----
        $ player_stats.hp = max(0, player_stats.hp - 15) 
        $ player_stats.thirst += 20
        $ player_stats.add_condition(COND_POISON)

        $ check_player_death(player_stats)

        "最初的畅快只持续了几秒。很快，你的胃部开始剧烈痉挛，仿佛有什么东西在里面蠕动。"
        "你的身体开始排斥刚刚喝下的毒水——剧烈的呕吐、腹痛，让你在地上蜷成一团。"
        "你跪在地上干呕不止，胆汁都吐了出来。喝下去的水变成了更深的诅咒。"

        $ check_player_death(player_stats)

    else:
        # ----- 侥幸逃脱 -----
        "你打了一个寒颤，等待着那可怕的腹痛到来……但什么都没有发生。"
        "也许是你运气好，没喝到最要命的那些病菌；也许是你早已千疮百孔的免疫系统还在勉力支撑。"
        "无论如何，这一次你赌赢了。但下一次呢？"
        "不过，肚子里隐隐的抽动还是让你有些不安。"
    return

label event_encounter_default:

    python:
        import random
        # 从测试敌人列表中随机选择一个
        creature_id = random.choice(TEST_ENEMY_IDS)
        enemy = ActorInstance(creature_id=creature_id, is_player=False)
        combat_instance = CombatSystem(player_stats, enemy)
        # 在战斗日志中显示敌人名称
        combat_instance.combat_log = [f"你遇到了一个敌人：{enemy.name}！"]
    
    # 根据敌人类型显示不同的遭遇文本
    if enemy.id == 1:  # 野狗
        "一阵低沉的咆哮从灌木丛后响起，一只皮包骨的野狗正龇牙咧嘴地盯着你。"
    elif enemy.id in [3, 4]:  # 枯萎兽系列
        "浓密的植被中传来低沉的嘶吼声，一个扭曲的身影从阴影中缓缓显现……"
    elif enemy.id == 7:  # 辐射蟑螂
        "地面传来窸窸窣窣的声响，一只巨大的甲壳生物从碎石堆中钻了出来。"
    elif enemy.id in [9, 11]:  # 人类敌人
        "前方传来了人声——但这片废土上，陌生人往往比野兽更危险。"
    
    $ _current_combat_instance = combat_instance
    call screen scr_combat(combat_instance)
    $ _return_value = _return
    $ _current_combat_instance = None
    $ encounter_result = _return_value
    $ winner = None

    # 更安全的类型检查 - 使用 python 块处理
    python:
        if encounter_result and isinstance(encounter_result, (list, tuple)) and encounter_result[0] == "combat_end_trigger":
            winner = encounter_result[1]

    # 根据结果分支
    if winner == player_stats:
        # 玩家击杀敌人
        "你从战斗中幸存下来，身上的伤痕提醒你这片废土依然凶险。"
    elif winner == "player_escaped":
        # 玩家主动逃离
        "你成功甩开了敌人，安全地离开了战场。"
    elif winner is None:
        # 敌人逃跑
        "敌人仓皇逃窜，消失在了荒野之中。"
    else:
        # 玩家失败
        "你倒在了荒野之中，视野渐渐模糊。"
        return
    jump travel_on_wasteland_loop

# ==========================================================
# 死亡标签
# ==========================================================
label game_over_dehydration:
    $ player_stats.b_dead = False

    "你因极度脱水倒下，四周的景象渐渐模糊成一片白光。"
    "这一切都在饥渴与疲惫之中终结。"

    $ renpy.full_restart()

label event_merchant_encounter_menu:
    menu:
        "没什么兴趣，继续赶路":
            window hide
            jump travel_on_wasteland_loop

# ============================================================
# 扎营休息标签
# ============================================================
label event_camp:
    # 防御性检查
    $ check_player_death(player_stats)
    
    # 检查疲劳值是否 >= 40
    if player_stats.fatigue < 40:
        "你还不算太累，现在扎营为时过早。"
        jump travel_on_wasteland_loop
    
    # 随机确定睡眠时长：6-8 小时
    $ import random
    $ camp_sleep_hours = random.randint(6, 8)
    $ camp_sleeped_hours = 0
    
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
        $ camp_sleeped_hours += 1
        
        # 推进60分钟
        $ game_time['minute'] += 60
        $ _overflow = game_time['minute'] // 60
        $ game_time['hour'] += _overflow
        $ game_time['minute'] = game_time['minute'] % 60
        if game_time['hour'] >= 24:
            $ game_time['hour'] = 0
            $ game_time['day'] += 1
        
        # 调用 tick_minutes 模拟时间流逝（会增加饥饿、口渴、疲劳）
        $ tick_minutes(player_stats, 60)
        
        # 睡眠恢复疲劳
        $ player_stats.fatigue = max(0.0, player_stats.fatigue - 10.0)
        
        # 睡眠期间口渴值减少
        $ player_stats.thirst = max(0.0, player_stats.thirst - 0.5 * METABOLISM_PER_5MIN['thirst'] * 12)
        
        # 检查是否在睡眠中死亡
        $ check_player_death(player_stats)
        
        # 继续下一小时
        jump _event_camp_loop
    
    label _event_camp_wake_up:
        # 更新疲劳状态
        $ update_fatigue_condition(player_stats)
        
        "你醒了过来，感觉精神恢复了不少。"
        
        $ sleep_hours = camp_sleeped_hours
        if sleep_hours == 1:
            "你只睡了 1 个小时。"
        else:
            "你总共睡了 [sleep_hours] 个小时。"
        
        "现在时间是第 [game_time['day']] 天的 [game_time['hour']]:00。"
        
        if player_stats.fatigue <= 0:
            "你精神饱满，又可以继续前进了。"
        
        $ renpy.restart_interaction()
        
        jump travel_on_wasteland_loop

# ====================昏阙事件标签=====================
label event_faint_collapse:
    "你的身体终于到达了极限。"
    "眼前的景象开始模糊，双膝不受控制地弯曲，世界在你的意识中缓慢地倾斜——"
    "你失去了知觉。"
    
    # 睡眠恢复逻辑：一次睡满 8 小时
    $ player_stats.fatigue = max(0.0, player_stats.fatigue - 80.0)
    $ update_fatigue_condition(player_stats)
    
    # 睡眠期间消耗代谢（口渴、饥饿值继续增加）
    $ tick_minutes(player_stats, minutes=480)  # 8小时 = 480分钟
    
    # 如果睡眠后因口渴死亡
    if player_stats.b_dead:
        jump game_over_dehydration
    
    "……不知过了多久，你在一阵刺骨的寒冷中醒来。"
    "阳光已经移动了位置——你睡了很久。"
    
    # 回到大地图
    jump travel_on_wasteland_loop