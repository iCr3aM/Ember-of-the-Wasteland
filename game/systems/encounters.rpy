# =============================================================================
# # 定义：大地图探索时触发的“文本遭遇事件数据库”及选项响应链。
# # 实现：解析玩家当前所拥有的技能或装备（如“撬棍”），动态显示或隐藏选项；处理选项后的跳转（如：走向战斗、获得宝藏、触发伤病、或跳向另一个 Encounter ID）。
# =============================================================================
# 事件编号统一管理
init -190 python:   #优先级
    EVENT_ENCOUNTER_DEFAULT = 2001
    #EVENT_ENCOUNTER_ = 2002
    TEST_ENEMY_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13]

    TERRAIN_ENEMY_MAP = {
        "road":       [13, 2],       # 拾荒帮众、流浪者
        "plains":     [1, 2],        # 野狗、流浪者
        "farmland":   [5, 13],       # 辐射鼠、拾荒帮众
        "forest":     [6, 10],       # 幼芽寄生体、变异蜈蚣
        "beach":      [5, 8],        # 辐射鼠、变异吸血虫
        "city_ruins": [3, 4],        # 枯萎者、枯萎兽
        "lake":       [1, 8],        # 野狗、变异吸血虫
        "swamp":      [12, 4],       # 蝎尾蝇、枯萎兽
        "ocean":      [],            # 无
    }

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
        # 根据当前地形选择敌人
        _tile = world_map.grid.get((player_hex_x, player_hex_y))
        _terrain = _tile.terrain_type if _tile else "plains"
        _enemy_pool = TERRAIN_ENEMY_MAP.get(_terrain, TEST_ENEMY_IDS)
        if not _enemy_pool:
            _enemy_pool = TEST_ENEMY_IDS  # 兜底（ocean 不会触发事件，但以防万一）
        creature_id = random.choice(_enemy_pool)
        enemy = ActorInstance(creature_id=creature_id, is_player=False)
        combat_instance = CombatSystem(player_stats, enemy)
        # 在战斗日志中显示敌人名称
        combat_instance.combat_log = [f"你遇到了一个敌人：{enemy.name}！"]
    
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
label game_over_death:
    $ player_stats.b_dead = False

    "你感受到自己的意识逐渐模糊……"
    "身体像被抽空了一样，四肢再也无法支撑你的重量……"

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
    
    # 使用CAMP_CONFIG检查疲劳值
    if player_stats.fatigue < CAMP_CONFIG['min_fatigue_to_camp']:
        "你还不算太累，现在扎营为时过早。"
        jump travel_on_wasteland_loop
    
    # 随机确定睡眠时长（分钟）
    $ import random
    $ camp_sleep_minutes = random.randint(
        CAMP_CONFIG['min_sleep_minutes'],
        CAMP_CONFIG['max_sleep_minutes']
    )
    $ remaining_minutes = camp_sleep_minutes
    
    "你找了一个相对避风的角落，开始整理物资并休息。"
    "你躺了下来，很快便进入了梦乡……"
    
    # 每5分钟步进一次（与tick_minutes保持相同粒度）
    label _event_camp_loop:
        # 条件检查：疲劳已恢复或睡眠时长用完
        if player_stats.fatigue <= 0:
            $ player_stats.fatigue = 0.0
            "你的疲劳已经完全恢复，提前醒了过来。"
            jump _event_camp_wake_up
        
        if remaining_minutes <= 0:
            jump _event_camp_wake_up
        
        # 步进5分钟
        $ step = min(5, remaining_minutes)
        $ game_time['minute'] += step
        $ _overflow = game_time['minute'] // 60
        $ game_time['hour'] += _overflow
        $ game_time['minute'] = game_time['minute'] % 60
        if game_time['hour'] >= 24:
            $ game_time['hour'] = 0
            $ game_time['day'] += 1
        
        # 调用基础代谢（增加饥饿、口渴、疲劳）
        $ tick_minutes(player_stats, step, thirst_multiplier=CAMP_CONFIG['thirst_rate_multiplier'])
        
        # 睡眠恢复疲劳（按5分钟粒度）
        $ recovery_this_step = CAMP_CONFIG['fatigue_recovery_per_5min'] * (step / 5.0)
        $ player_stats.fatigue = max(0.0, player_stats.fatigue - recovery_this_step)

        # 睡眠恢复生命值（按5分钟粒度，受 fHealingRate 修正）
        $ hp_recovery_base = CAMP_CONFIG['hp_recovery_per_5min'] * (step / 5.0)
        $ hp_recovery_mult = player_stats.get_modifier_multiplier("fHealingRate")
        $ player_stats.hp = min(player_stats.max_hp, player_stats.hp + hp_recovery_base * hp_recovery_mult)
        
        # 检查是否在睡眠中死亡
        $ check_player_death(player_stats)
        
        $ remaining_minutes -= step
        jump _event_camp_loop
    
    label _event_camp_wake_up:
        # 更新疲劳状态
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
        
        $ renpy.restart_interaction()
        
        jump travel_on_wasteland_loop

# ====================昏阙事件标签=====================
label event_faint_collapse:
    "你的身体终于到达了极限。"
    "眼前的景象开始模糊，双膝不受控制地弯曲，世界在你的意识中缓慢地倾斜——"
    "你失去了知觉。"
    
    # 一次性恢复所有疲劳（昏阙后强制睡满最大时间）
    $ player_stats.fatigue = 0.0
    $ update_fatigue_condition(player_stats)
    
    # 睡眠期间代谢消耗（8小时=480分钟）
    $ faint_sleep_minutes = CAMP_CONFIG['max_sleep_minutes']  # 480
    
    # 调用tick_minutes模拟8小时代谢（但按倍率减少口渴增加）
    $ tick_minutes(player_stats, faint_sleep_minutes, thirst_multiplier=CAMP_CONFIG['thirst_rate_multiplier'])

    # 昏阙期间按睡眠时长恢复生命值（与扎营使用相同速率）
    $ faint_hp_recovery = CAMP_CONFIG['hp_recovery_per_5min'] * (faint_sleep_minutes / 5.0)
    $ faint_hp_mult = player_stats.get_modifier_multiplier("fHealingRate")
    $ player_stats.hp = min(player_stats.max_hp, player_stats.hp + faint_hp_recovery * faint_hp_mult)

    # 同时推进时间
    $ game_time['minute'] += faint_sleep_minutes
    $ _overflow = game_time['minute'] // 60
    $ game_time['hour'] += _overflow
    $ game_time['minute'] = game_time['minute'] % 60
    if game_time['hour'] >= 24:
        $ game_time['hour'] = 0
        $ game_time['day'] += 1
    
    # 如果睡眠后死亡
    if player_stats.b_dead:
        jump game_over_death
    
    "……不知过了多久，你在一阵刺骨的寒冷中醒来。"
    "阳光已经移动了位置——你睡了很久。"
    
    # 回到大地图
    jump travel_on_wasteland_loop