# =============================================================================
# encounters.rpy — 大地图遭遇事件与选项响应链
# 功能：定义地形敌人池、战斗遭遇、湖泊饮水事件、扎营休息、昏阙恢复等事件
# 职责：根据玩家位置/状态动态触发事件，处理选项分支与跳转
# =============================================================================
# ── 事件标签 ──
label encounter_lake_water:

    "你蹲在浑浊的湖边，水面泛着诡异的油彩光泽。"
    "水波之下，隐约可见发白的死鱼翻着肚皮，一股铁锈与腐败混合的气味钻进鼻腔。"

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
            "不能喝，喝了可能会死得更快。"

            jump travel_on_wasteland_loop

label drink_lake_water_consequence:
    # 立即解除或缓解口渴
    $ player_stats.thirst = max(0, player_stats.thirst - LAKE_WATER_THIRST_RELIEF)
    $ update_thirst_condition(player_stats)  # 自动维护口渴状态（会自动移除脱水等状态）
    if renpy.random.random() <= LAKE_WATER_POISON_CHANCE:
        # ----- 中招 -----
        $ player_stats.hp = max(0, player_stats.hp - LAKE_WATER_HP_DAMAGE)
        $ player_stats.thirst += LAKE_WATER_THIRST_PENALTY
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
        "不过，肚子里隐隐的抽动还是让你有些不安。"
    return

label event_encounter_default:

    python:
        enemy = create_weighted_enemy_for_current_terrain()
        combat_instance = CombatSystem(player_stats, enemy)
        # 在战斗日志中显示敌人名称
        combat_instance.combat_log = [(f"你遇到了一个敌人：{enemy.name}！", "system")]
    
    # 根据敌人类型显示不同的遭遇文本
    if enemy.id == 1:  # 野狗
        "一阵低沉的咆哮在附近响起，一只皮包骨的野狗正龇牙咧嘴地盯着你。"
    elif enemy.id in [3, 4]:  # 枯萎兽系列
        "你的附近传来了低沉的嘶吼声，一个扭曲的身影从阴影中缓缓显现……"
    elif enemy.is_human:
        "前方传来了人声——但这片废土上，陌生人往往比野兽更危险。"
    else:
        "地面传来窸窸窣窣的声响，一只变异生物从废墟的缝隙中钻了出来。"
    
    $ _current_combat_instance = combat_instance
    call screen scr_combat(combat_instance)
    $ _return_value = _return
    $ combat_instance.restore_music()
    $ _current_combat_instance = None
    $ encounter_result = _return_value
    $ winner = None

    # 安全类型检查：解析战斗结算返回值
    python:
        if encounter_result and isinstance(encounter_result, (list, tuple)) and encounter_result[0] == "combat_end_trigger":
            winner = encounter_result[1]

    # 根据结果分支
    if winner == player_stats:
        # 玩家击杀敌人
        "你从战斗中幸存下来，身上的伤痕提醒你这片废土依然险。"
    elif winner == "player_escaped":
        # 玩家主动逃离
        "你成功甩开了敌人，安全地离开了战场。"
    elif winner is None:
        # 敌人逃跑
        "敌人仓皇逃窜，消失在了荒野之中。"
    else:
        # 玩家失败 — 被敌人杀死
        jump combat_death
    $ auto_save_game(force=True)
    jump travel_on_wasteland_loop

# ── 死亡标签 ──
label game_over_death:
    $ player_stats.b_dead = False
    $ hide_gameplay_overlays()
    scene black with dissolve
    $ renpy.pause(0.3, hard=True)
    $ death_descriptions = [
        "你感受到自己的意识逐渐模糊……\n身体像被抽空了一样，四肢再也无法支撑你的重量……",
        "视野的边缘开始发黑，像墨水在宣纸上缓慢洇开。\n你听见自己的心跳越来越慢，最终归于沉寂。",
        "废土的风吹过你的身体，带走了最后一丝温度。\n你躺在尘土中，和这片荒芜的土地融为一体。",
        "你倒下了。没有人会知道你的名字，没有人会记得你曾在这里挣扎求生。\n废土吞没了一切。",
        "疼痛渐渐远去，取而代之的是一种奇异的平静。\n你终于可以休息了。",
        "你的手指在沙土上无力地划过，留下最后一道痕迹。\n风很快会将它抹去，就像你从未存在过。",
        "你想起了一个早已模糊的画面——蓝色的天空，绿色的树。\n然后一切都暗了下来。",
        "废土上又多了一具无人认领的尸体。\n秃鹫会在天空中盘旋，等待它们的晚餐。",
        "你试图抓住什么，但手指只握住了虚空。\n意识像沙子一样从指缝间流走。",
    ]
    $ renpy.random.shuffle(death_descriptions)
    "[death_descriptions[0]]"
    
    # 淡出到黑屏
    scene black with dissolve
    $ renpy.pause(1.0, hard=True)
    
    # 显示死亡统计页面
    call screen scr_death_stats

    # 淡出返回主菜单
    scene black with dissolve
    $ renpy.pause(0.5, hard=True)
    $ MainMenu(confirm=False, save=False)()

# ── 战斗死亡标签 ──
label combat_death:
    $ combat_death_descriptions = [
        "你倒在了血泊中，视野渐渐模糊。\n敌人的身影在你上方晃动，然后一切都归于黑暗。",
        "最后一击来得又快又狠。你甚至没来得及感觉到疼痛——\n世界就变成了一片空白。",
        "你的膝盖一软，跪倒在地上。\n温热的液体从伤口涌出，染红了身下的沙土。\n敌人站在你面前，冷漠地看着你咽下最后一口气。",
        "你听见自己的骨头碎裂的声音，清脆而遥远，仿佛是从别人身体里传来的。\n然后你什么也听不见了。",
        "你试图爬起来，但四肢已经不再听从使唤。\n敌人给了你最后一击，彻底终结了你的挣扎。",
        "视野开始天旋地转，你分不清哪里是天，哪里是地。\n你倒在废墟中，意识像断线的风筝一样飘远。",
        "敌人的武器贯穿了你的身体。\n你低头看着伤口，觉得那好像不是自己的血。\n然后你倒了下去，再也没有站起来。",
        "你被击倒在地，嘴里满是铁锈味的血腥。\n你望着灰蒙蒙的天空，视线越来越模糊，直到什么都看不见。",
        "你的身体已经到达了极限。\n敌人没有给你任何喘息的机会，最后一击彻底结束了你的旅途。",
        "你倒在废土上，感受着生命从身体里一点点流走。\n风声、脚步声、心跳声——所有的声音都在远去。",
    ]
    $ renpy.random.shuffle(combat_death_descriptions)
    "[combat_death_descriptions[0]]"
    jump game_over_death

# ── 商人遭遇菜单 ──
label event_merchant_encounter_menu:
    menu:
        "没什么兴趣，继续赶路":
            window hide
            jump travel_on_wasteland_loop

# ── 扎营休息标签 ──
label event_camp:
    $ times_camped += 1
    # 防御性死亡检查
    $ check_player_death(player_stats)
    
    # 疲劳值未达扎营阈值则跳过
    if player_stats.fatigue < CAMP_CONFIG['min_fatigue_to_camp']:
        "你还不算太累，现在扎营为时过早。"
        jump travel_on_wasteland_loop
    
    # 随机确定睡眠时长（分钟）
    $ camp_sleep_minutes = renpy.random.randint(
        CAMP_CONFIG['min_sleep_minutes'],
        CAMP_CONFIG['max_sleep_minutes']
    )
    $ remaining_minutes = camp_sleep_minutes
    
    "你找了一个相对避风的角落，开始整理物资并休息。"
    "你躺了下来，很快便进入了梦乡……"
    
    # ── 睡眠循环：每5分钟步进 ──
    label _event_camp_loop:
        # 疲劳已恢复或时长用完则唤醒
        if player_stats.fatigue <= 0:
            $ player_stats.fatigue = 0.0
            "你的疲劳已经完全恢复，提前醒了过来。"
            jump _event_camp_wake_up
        
        if remaining_minutes <= 0:
            jump _event_camp_wake_up
        
        # 步进5分钟并推进游戏时间
        $ step = min(5, remaining_minutes)
        $ advance_game_time(step)
        
        # 应用基础代谢（饥饿、口渴、疲劳增加）
        $ tick_minutes(player_stats, step, thirst_multiplier=CAMP_CONFIG['thirst_rate_multiplier'])
        
        # 睡眠恢复疲劳
        $ recovery_this_step = CAMP_CONFIG['fatigue_recovery_per_5min'] * (step / 5.0)
        $ player_stats.fatigue = max(0.0, player_stats.fatigue - recovery_this_step)

        # 睡眠恢复生命值（受 fHealingRate 修正）
        $ hp_recovery_base = CAMP_CONFIG['hp_recovery_per_5min'] * (step / 5.0)
        $ hp_recovery_mult = player_stats.get_modifier_multiplier("fHealingRate")
        $ player_stats.hp = min(player_stats.max_hp, player_stats.hp + hp_recovery_base * hp_recovery_mult)
        
        # 睡眠中死亡检查
        $ check_player_death(player_stats)
        
        $ remaining_minutes -= step
        jump _event_camp_loop
    
    # ── 唤醒结算 ──
    label _event_camp_wake_up:
        $ update_fatigue_condition(player_stats)
        
        $ sleep_hours = (camp_sleep_minutes - remaining_minutes) // 60
        $ sleep_remain = (camp_sleep_minutes - remaining_minutes) % 60

        $ nap_descriptions = [
            "你打了个盹，被一阵不知名的嚎叫声惊醒。心脏狂跳了好一阵才平复。",
            "你靠在废墟的阴影里，意识在清醒与混沌间游荡了片刻。醒来时脖子僵硬。",
            "浅层的睡眠只持续了一小会儿。你醒来时，甚至不确定自己是否真的睡着过。"
        ]

        $ short_sleep_descriptions = [
            "你梦见了水，清澈的、无穷无尽的水。醒来时嘴唇却依旧是干裂的。",
            "身体下的地面硬得硌人，每一次翻身都伴随着骨骼的抗议。倦意依然沉沉地压着你。",
            "断断续续的睡眠让你恢复了一些体力，但脑袋里像塞了一团废布，昏沉沉的。"
        ]

        $ good_sleep_descriptions = [
            "意识沉入黑暗，像一块石头落入深井。你一度忘记了那些游荡在废墟里的东西。",
            "你在黑暗中沉沉睡去，又在同样的黑暗中醒来。有那么一瞬间，你分不清自己身在何方。",
            "睡眠如同一场短暂而彻底的死亡，将你从废土的现实中暂时解放了出来。"
        ]

        $ long_sleep_descriptions = [
            "这一觉跨越了昼夜的边界。醒来时，头顶的天空已经换了颜色。",
            "你睡了很久，久到身体仿佛被钉在了地面上。那些积压在肌肉深处的疲惫总算被洗去了大半。",
            "你从一个深不见底的睡眠中浮了上来。梦的碎片沉在脑后，你想抓住它们，但它们已经消散了。"
        ]

        if sleep_hours == 0:
            "[renpy.random.choice(nap_descriptions)]"
        elif sleep_hours < 4:
            "[renpy.random.choice(short_sleep_descriptions)]"
        elif sleep_hours < 8:
            "[renpy.random.choice(good_sleep_descriptions)]"
        else:
            "[renpy.random.choice(long_sleep_descriptions)]"
        
        if player_stats.fatigue <= 0:
            "你精神饱满，又可以继续前进了。"
        
        $ auto_save_game(force=True)
        $ renpy.restart_interaction()
        
        jump travel_on_wasteland_loop

# ── 昏阙事件标签 ──
label event_faint_collapse:
    "你的身体终于到达了极限。"
    "眼前的景象开始模糊，双膝不受控制地弯曲，世界在你的意识中缓慢地倾斜——"
    "你失去了知觉。"
    
    # 强制清空疲劳（昏阙后睡满最大时长）
    $ player_stats.fatigue = 0.0
    $ update_fatigue_condition(player_stats)
    
    # 睡眠期间代谢消耗（8小时=480分钟）
    $ faint_sleep_minutes = CAMP_CONFIG['max_sleep_minutes']  # 480
    
    # 模拟8小时代谢（口渴增加按倍率缩减）
    $ tick_minutes(player_stats, faint_sleep_minutes, thirst_multiplier=CAMP_CONFIG['thirst_rate_multiplier'])

    # ★ 如果在睡眠中死亡 → 直接跳转，HP已为0
    if player_stats.b_dead:
        jump game_over_death

    # 昏阙期间恢复生命值（与扎营使用相同速率）
    $ faint_hp_recovery = CAMP_CONFIG['hp_recovery_per_5min'] * (faint_sleep_minutes / 5.0)
    $ faint_hp_mult = player_stats.get_modifier_multiplier("fHealingRate")
    $ player_stats.hp = min(player_stats.max_hp, player_stats.hp + faint_hp_recovery * faint_hp_mult)

    # 同时推进时间
    $ advance_game_time(faint_sleep_minutes)
    
    "……不知过了多久，你在一阵刺骨的寒冷中醒来。"
    "阳光已经移动了位置——你睡了很久。"
    
    # 回到大地图
    $ auto_save_game(force=True)
    jump travel_on_wasteland_loop
