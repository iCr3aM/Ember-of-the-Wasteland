# =============================================================================
# 荒原余烬 Ember of the Wasteland 世界观沉浸展示与初始技能配置
# =============================================================================
# =============================================================================
# # 定义：游戏的序幕文本、开场 CG 演出、背景世界观介绍（枯萎流感爆发与核战）。
# # 实现：玩家捏人（选择初始特长）的剧情化包装，完成后赋予玩家初始属性并切入大地图。
# =============================================================================
# 声明序幕所需的视觉资产背景图占位（颜色占位符）
image bg lore_blight = Solid("#503020")
image bg lore_ragnarok = Solid("#403050")
image bg quarantine_zone = Solid("#204050")

label prologue_start:
    # 常驻显示基础 HUD 界面以监控实时生理状态变化
    show screen scr_hud

    # -------------------------------------------------------------------------
    # 【第一阶段：世界观历史宏叙事】
    # -------------------------------------------------------------------------
    scene bg lore_blight with dissolve
    
    "第一波：无声的枯萎"
    
    "起初，人们叫它“枯萎病”。它由空气传播，潜伏期漫长，致死率极高，且基因组似乎永不停歇地重组。"
    "疫苗研发的速度，永远追不上它变异的脚步。恐慌像第二场瘟疫般蔓延。"
    "国境线关闭，城市封锁，全球化的血管——那些横跨大洋的货轮与航班——一根根凝固、坏死。"
    "超市货架变得空空荡荡，接着是医院，接着是整个社会赖以运转的信任。"

    scene bg lore_ragnarok with fade
    
    "第二波：诸神的黄昏"
    
    "为了争夺地球上仅存的几处安全区——最后的疫苗工厂、地下的无土栽培农场、未受污染的水源地——残存的秩序迅速瓦解。"
    "不是全面核战争，而是冷酷、务实的“外科手术式”打击。"
    "几十枚战术核弹头，足够精准地摧毁对方的希望，也足够向全世界的天空播撒致命的同位素。"
    "战争在几周内结束，因为它已没有继续的必要。"

    # -------------------------------------------------------------------------
    # 【第二阶段：互动捏人与特长注入】
    # -------------------------------------------------------------------------
    "在文明坠入无底深渊前，你在旧时代里所依赖的生存本领是什么？"

    menu:
        "【野外追踪者】精通资源搜索与环境规避":
            python:
                player_stats.skills.append("Scavenging")
                # 搜刮特长赋予极微小的代谢优化优势
                player_stats.moves_per_turn = 5 
            "你掌握了旧世界的废墟分布。基础移动能力提升。"

        "【前战地军医】精通创伤缝合与病症识别":
            python:
                player_stats.skills.append("Medic")
                player_stats.max_hp = 120.0
                player_stats.hp = 120.0
            "你对各种病症的抗性更强。基础最大生命值提升。"

        "【避难所打手】精通徒手搏击与简易器械":
            python:
                player_stats.skills.append("Melee")
                # 为突击队形态追加额外攻击手段ID（假设 2 为强力一击）
                player_stats.attack_mode_ids.append(2)
            "你适应了近身血斗。解锁了更高级别的近战体征指令。"

    # -------------------------------------------------------------------------
    # 【第三阶段：隔离区冷开场】
    # -------------------------------------------------------------------------
    scene bg quarantine_zone with fade
    
    "【冷开场】"
    "你在一个废弃的前政府防疫隔离点（Quarantine Zone）的地下室醒来。"
    "四周是腐烂的防化服、失效的医疗器械和满地的骷髅。外面正传来狂暴的雷鸣与大雨声。"

    # 初始化生理绝境危机数据（极度渴死、饥饿临界边缘，强逼玩家通过交互脱困）
    python:
        player_stats.thirst = 85.0
        player_stats.hunger = 45.0
        update_thirst_condition(player_stats)
        player_stats.add_condition(302)

    "寒冷与致命的脱水感正在撕裂你的意识。你必须在离开前搜刮到两样东西："
    "1. 【防毒面具滤毒罐】——确保在外面的辐射暴雨中存活。"
    "2. 【纯净水】——解决目前的极度口渴。"

# 循环检查任务目标的局部状态机
label quarantine_exploration_loop:
    # 检查任务物品是否皆已安全存入背包
    $ has_filter = player_inventory.check_item_count(101) > 0
    $ has_water = player_inventory.check_item_count(201) > 0

    if has_filter and has_water:
        jump prologue_escape_success

    menu:
        "【搜刮】翻找倾倒的医疗急救箱" if not has_filter or not has_water:
            "你强忍着恶臭撬开了锈蚀的救护箱。在层层碎玻璃和霉变的绷带下，你找到了急需的补给物资。"
            python:
                # 严禁直接写代码创建裸字典，必须严格遵循 items.rpy 的设计进行动态实例派发
                if not has_filter:
                    filter_instance = ItemInstance(item_id=101)
                    player_inventory.add_item(filter_instance)
                if not has_water:
                    water_instance = ItemInstance(item_id=201)
                    player_inventory.add_item(water_instance)
            "获得：[ITEMS_DB[101].name] ×1，[ITEMS_DB[201].name] ×1"
            jump quarantine_exploration_loop

        "【调查】尝试启动墙角闪烁的废弃电脑终端":
            "电脑屏幕上残存着由上个纪元防疫指挥部留下的加密日志残片："
            "“...变异速度完全失控... 基因测序显示第4组链条出现了非自然重组... 隔离区已于昨日宣告破裂... 愿上帝宽恕那些被留在地表的人...”"
            jump quarantine_exploration_loop

        "【查看】凝视墙上干涸的油漆涂鸦":
            "水泥墙壁上，有人在死前用黑色油漆疯狂地涂抹下了一行醒目的粗体大字："
            "【不是枯萎病杀死了我们，是那些为了抢夺疫苗而扔下核弹的疯子。】"
            jump quarantine_exploration_loop

# -------------------------------------------------------------------------
# 【第四阶段：破局与世界线交错】
# -------------------------------------------------------------------------
label prologue_escape_success:
    "你颤抖着拧开了那瓶[ITEMS_DB[201].name]，冰冷甘甜的液体滋润了你冒烟的喉咙。"
    
    python:
        # 扣除消耗品，更新物理内呼吸系统健康数值
        player_stats.thirst = 0.0
        update_thirst_condition(player_stats)
        # 扫描并移除背包中已消耗的纯净水实例
        for item in list(player_inventory.backpack_grid):
            if item.id == 201:
                player_inventory.backpack_grid.remove(item)
                break

    "随后，你将全新的[ITEMS_DB[101].name]卡死在防毒面具的面罩气孔上。橡胶的冰冷触感让你重新恢复了理智。"
    "你推开了地下室沉重的铅封铁门。狂暴的酸雨瞬间砸在你的面罩上，远方是一望无际的废土死寂地平线。"
    
    "序幕结束。你已正式踏入残酷的荒野。"
    show screen scr_hud  # 确保 HUD 可见

    # 彻底平滑过渡，将控制权整体移交至大地图探索网络（systems/map.rpy 与 screens/scr_map.rpy）
    call travel_on_wasteland_loop from _call_travel_on_wasteland_loop