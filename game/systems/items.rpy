# =============================================================================
# # 物品、武器、装备、药品、垃圾数据库
# # 定义：静态物品原型数据库（`ITEMS_DB`，含重量、基础价值、最大耐久、每小时腐烂率、装备槽位要求）。
# # 实现：生成具体的物品实例（`ItemInstance`），支持物品因时间流逝而腐烂变质（如肉块变质）、因使用而磨损（如衣服变烂）。
# =============================================================================
init python:
    class ItemType:
        """对应 itemtypes.xml 的静态数据类"""
        def __init__(self, id, name, desc, weight, value, max_durability=1.0, degrade_per_hour=0.0, equip_slots=None):
            self.id = id
            self.name = name
            self.desc = desc
            self.weight = weight
            self.value = value
            self.max_durability = max_durability
            self.degrade_per_hour = degrade_per_hour
            self.equip_slots = equip_slots or [] # 可装备的身体槽位编号

# 将 degrade 方法移入 ItemInstance 类，以便每个物品实例独立管理自己的耐久度。
init python:
    class ItemInstance:
        """在背包及大地图世界中真实流转的动态实例"""
        def __init__(self, item_id, durability=1.0):
            self.id = item_id
            self.config = ITEMS_DB[item_id]
            self.durability = durability # 0.0 - 1.0 独立耐久度

        @property
        def icon_path(self):
            # 通过全局解耦工具动态获取 game/images/ 内部图标路径
            return get_item_icon_path(self.id)

        def degrade(self, hours=1.0):
            """耐久度因磨损或时间流逝产生降级"""
            if self.config.degrade_per_hour > 0:
                self.durability -= self.config.degrade_per_hour * hours
                if self.durability < 0:
                    self.durability = 0.0

    def create_item_instance(item_id, durability=None):
        """工厂函数：基于 item_id 生成动态物品实例。"""
        if item_id not in ITEMS_DB:
            raise KeyError(f"Unknown item_id: {item_id}")
        default_durability = ITEMS_DB[item_id].max_durability
        return ItemInstance(item_id, durability if durability is not None else default_durability)

# =============================================================================
# 物品用途数据库：定义哪些物品可以直接从背包"使用"
# =============================================================================
init python:
    # ──── 饮品（减少口渴值）────
    def use_purified_water(actor):
        """使用纯净水：-40 口渴值"""
        actor.thirst = max(0.0, actor.thirst - 40.0)
        update_thirst_condition(actor)
        renpy.notify("你拧开瓶盖，清凉的纯净水滑过喉咙，整个人都活了过来。")
        return True

    def use_rainwater(actor):
        """使用雨水收集瓶：-15 口渴值"""
        actor.thirst = max(0.0, actor.thirst - 15.0)
        update_thirst_condition(actor)
        renpy.notify("你拧开瓶盖，浑浊的雨水带着一股铁锈味滑过喉咙。")
        return True

    def use_cola(actor):
        """使用瓶装可乐：-20 口渴值"""
        actor.thirst = max(0.0, actor.thirst - 20.0)
        update_thirst_condition(actor)
        renpy.notify("你撬开瓶盖，糖浆般甜腻的液体让你短暂地忘记了干渴。")
        return True

    def use_alcohol(actor):
        """使用酒精饮料：-10 口渴值"""
        actor.thirst = max(0.0, actor.thirst - 10.0)
        update_thirst_condition(actor)
        renpy.notify("你灌下一口烈酒，灼烧感从喉咙一直蔓延到胃里。")
        return True

    # ──── 食物（减少饥饿值）────
    def use_compressed_biscuit(actor):
        """使用压缩饼干：-25 饥饿值"""
        actor.hunger = max(0.0, actor.hunger - 25.0)
        renpy.notify("你啃了一口硬邦邦的压缩饼干，满嘴都是麦粉味。")
        return True

    def use_meat_can(actor):
        """使用肉罐头：-30 饥饿值"""
        actor.hunger = max(0.0, actor.hunger - 30.0)
        renpy.notify("你撬开铁皮罐头，油脂凝固的肉块散发着咸香。")
        return True

    def use_dried_mushroom(actor):
        """使用干蘑菇：-10 饥饿值"""
        actor.hunger = max(0.0, actor.hunger - 10.0)
        renpy.notify("你嚼着干硬的蘑菇，一股泥土味在嘴里散开。")
        return True

    def use_energy_bar(actor):
        """使用能量棒：-20 饥饿值"""
        actor.hunger = max(0.0, actor.hunger - 20.0)
        renpy.notify("你咬了一口能量棒，甜得发腻的糖浆黏住了牙齿。")
        return True

    def use_raw_meat(actor):
        """使用不明生肉：-15 饥饿值，20%概率中毒"""
        actor.hunger = max(0.0, actor.hunger - 15.0)
        if random.random() < 0.2:
            actor.add_condition(COND_POISON)
            renpy.notify("你吞下生肉，胃里立刻翻涌起一阵恶心——肉变质了。")
        else:
            renpy.notify("你皱着眉头咽下生肉，腥味在舌尖久久不散。")
        return True

    def use_military_ration(actor):
        """使用军用口粮：-45 饥饿值"""
        actor.hunger = max(0.0, actor.hunger - 45.0)
        renpy.notify("你拆开迷彩包装，主菜、饼干、速溶饮料——这简直是国王的盛宴。")
        return True

    def use_antibiotic(actor):
        """使用抗生素：去除中毒状态"""
        removed = remove_condition_by_id(actor, COND_POISON)
        if removed:
            renpy.notify("药片滑入喉咙，高烧和冷汗终于开始退去。")
        else:
            renpy.notify("你吞下药片，但身体并无反应。浪费了一支珍贵的抗生素。")
        return True

    def use_bandage(actor):
        """使用绷带：去除流血状态和脚底割伤"""
        removed_bleed = remove_condition_by_id(actor, COND_BLEED)
        removed_cut = remove_condition_by_id(actor, COND_CUT_FOOT)
        if removed_bleed:
            renpy.notify("伤口已被包扎，流血止住了。")
        if removed_cut:
            renpy.notify("脚底的伤口已被包扎。")
        if not removed_bleed and not removed_cut:
            renpy.notify("你并没有需要包扎的伤口。")
        return removed_bleed or removed_cut

    def use_first_aid_kit(actor):
        """使用急救包：恢复 30 HP"""
        actor.hp = min(actor.max_hp, actor.hp + 30.0)
        renpy.notify(f"你的生命值恢复了。")
        return True

    # 物品用途映射表：item_id -> (use_label_or_none, effect_function_or_none)
    # 如果 use_function 不为 None，则可以在背包界面点击"使用"
    ITEM_USE_FUNCTIONS = {
        201: use_purified_water,      # 纯净水 -40口渴
        143: use_rainwater,           # 雨水收集瓶 -15口渴
        144: use_cola,                # 瓶装可乐 -20口渴
        145: use_alcohol,             # 酒精饮料 -10口渴
        114: use_compressed_biscuit,  # 压缩饼干 -25饥饿
        138: use_meat_can,            # 肉罐头 -30饥饿
        139: use_dried_mushroom,      # 干蘑菇 -10饥饿
        140: use_energy_bar,          # 能量棒 -20饥饿
        141: use_raw_meat,            # 不明生肉 -15饥饿(20%中毒)
        142: use_military_ration,     # 军用口粮 -45饥饿
        112: use_antibiotic,          # 抗生素
        113: use_bandage,             # 绷带
    }
    WEAPON_ATTACK_MAP = {
        109: [7],        # 水果刀 → 匕首捅刺
        110: [2],        # 工具锤 → 强力重击
        129: [10],       # 钢管 → 钢管挥击
        130: [3],        # 砍刀 → 砍刀挥砍
        132: [11],       # 棒球棍 → 棒球棍猛击
        131: [9],        # 指虎 → 指虎连击
        111: [12],       # 撬棍 → 撬棍猛击
        104: [5],        # 破旧手枪 → 手枪射击
    }

init python:
    def use_item_from_inventory(item_instance, actor=None):
        """
        通用物品使用函数。只执行物品的用途效果，不操作 UI。
        返回 (success, item_instance) 元组。
        """
        item_id = item_instance.id
        
        if item_id not in ITEM_USE_FUNCTIONS:
            return (False, item_instance)
        
        # 执行用途效果
        use_function = ITEM_USE_FUNCTIONS[item_id]
        if actor is None:
            # 如果未传入 actor，尝试获取全局 player_stats
            try:
                actor = player_stats
            except NameError:
                return (False, item_instance)
        success = use_function(player_stats)
        
        return (success, item_instance)

init python:
    def use_item_and_refresh_screen(item_instance, inv_instance, actor=None):
        success, item = use_item_from_inventory(item_instance, actor=actor)
        if success:
            inv_instance.remove_item(item)
            if is_in_active_combat():
                disable_player_turn_in_combat()

    def get_item_icon_path(item_id):
        """
        返回物品 ID 对应的图标路径。
        如果图标文件不存在，返回默认占位图。
        图标文件命名规则：icon_{item_id}.png
        """
        import os
        # 构造图标文件路径
        icon_filename = f"icon_{item_id}.png"
        icon_path = f"images/{icon_filename}"
        
        # 检查文件是否存在（在 Ren'Py 中，文件路径相对于 game/ 目录）
        # 使用 renpy.loadable() 检查资源文件是否存在
        if renpy.loadable(icon_path):
            return icon_path
        else:
            # 如果没有对应图标，返回一个默认的占位图
            # 或者直接返回 None（UI 中处理缺失图标的情况）
            return None

# =============================================================================
# 初始化基础 ITEM 类型数据表
# =============================================================================
init python:
    ITEMS_DB[101] = ItemType(
        101,
        "破旧头盔",
        "一顶布满划痕的二战头盔，内衬海绵早已塌陷，但至少还能护住你的脑袋。",
        weight=1.2,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["hat"]
    )

    ITEMS_DB[102] = ItemType(
        102,
        "破旧军靴（左）",
        "一只饱经风霜的军用皮靴。鞋底磨得差不多了，但比赤脚踩在碎玻璃上好。",
        weight=1.2,
        value=8.0,
        max_durability=0.8,
        degrade_per_hour=0.0,
        equip_slots=["left_foot"]
    )

    ITEMS_DB[103] = ItemType(
        103,
        "急救包",
        "一个印着褪色红十字的防水包。里面塞着缝合针、消毒酒精和几片救命药。",
        weight=1.0,
        value=15.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[104] = ItemType(
        104,
        "破旧手枪",
        "一把膛线快磨平的半自动手枪。卡壳是家常便饭，但没人敢对着枪口赌它今天哑火。",
        weight=0.3,
        value=12.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[105] = ItemType(
        105,
        "零件",
        "一堆混杂在一起的螺丝、弹簧和金属片。修东西全靠它们。",
        weight=0.8,
        value=4.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[106] = ItemType(
        106,
        "破旧白衬衫",
        "一件发黄的旧衬衫。穿上它，至少让你感觉自己还是个人。",
        weight=0.3,
        value=2.0,
        max_durability=0.6,
        degrade_per_hour=0.0,
        equip_slots=["torso"]
    )

    ITEMS_DB[107] = ItemType(
        107,
        "破旧工装裤",
        "一条满是污渍的帆布工装裤。膝盖处的布料已经磨穿，但口袋多，能装。",
        weight=0.6,
        value=3.0,
        max_durability=0.7,
        degrade_per_hour=0.0,
        equip_slots=["legs"]
    )

    ITEMS_DB[108] = ItemType(
        108,
        "肮脏运动鞋（左）",
        "一只看不出原本颜色的运动鞋。鞋底开胶了，走路时会灌进沙子和碎石。",
        weight=0.9,
        value=2.0,
        max_durability=0.5,
        degrade_per_hour=0.0,
        equip_slots=["left_foot"]
    )

    ITEMS_DB[109] = ItemType(
        109,
        "水果刀",
        "一把厨房用的水果刀，刀柄缠着防滑胶带。切东西还行，捅人也凑合。",
        weight=0.3,
        value=3.0,
        max_durability=0.6,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[110] = ItemType(
        110,
        "工具锤",
        "一把结实的羊角锤。锤头有些锈迹，但钉钉子、砸颅骨都同样顺手。",
        weight=1.5,
        value=8.0,
        max_durability=0.9,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[111] = ItemType(
        111,
        "撬棍",
        "一根淬过火的钢材撬棍。除了撬开锁死的门，也能让不长眼的掠夺者安静下来。",
        weight=2.0,
        value=10.0,
        max_durability=0.95,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[112] = ItemType(
        112,
        "抗生素",
        "一瓶自制的广谱抗生素。在这年头，这小小的药片比黄金还珍贵。",
        weight=0.1,
        value=20.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[113] = ItemType(
        113,
        "绷带",
        "一卷医用纱布绷带。干净、柔韧，能把裂开的伤口紧紧裹住。",
        weight=0.1,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[114] = ItemType(
        114,
        "压缩饼干",
        "一包已经破损的军用压缩饼干。硬得像砖头，但一小口就能撑半天。",
        weight=0.2,
        value=6.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[115] = ItemType(
        115,
        "破布",
        "几块从旧衣服上撕下来的布料。擦血、生火、堵门缝——破布永远不会嫌多。",
        weight=0.2,
        value=1.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[116] = ItemType(
        116,
        "玻璃瓶",
        "一个空玻璃瓶，标签早已脱落。装水、储存零碎、或者砸碎当武器都行。",
        weight=0.4,
        value=1.5,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[117] = ItemType(
        117,
        "废电池",
        "漏液的旧电池。电量所剩无几，但在懂行的人手里，也许还能榨出最后一点用处。",
        weight=0.3,
        value=2.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[118] = ItemType(
        118,
        "破旧电子表",
        "一块靠太阳能驱动的电子表。屏幕裂了一条缝，但数字还在跳动。它记得时间，也许也记得末日前的某一天。",
        weight=0.1,
        value=5.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["left_wrist"] 
    )

    ITEMS_DB[119] = ItemType(
        119,
        "破旧军靴（右）",
        "一只饱经风霜的军用皮靴。和左脚那只凑成一对，总算能好好走路了。",
        weight=1.2,
        value=8.0,
        max_durability=0.8,
        degrade_per_hour=0.0,
        equip_slots=["right_foot"]
    )

    ITEMS_DB[120] = ItemType(
        120,
        "肮脏运动鞋（右）",
        "一只看不出原本颜色的运动鞋。和左脚那只凑成一对，至少能跑。",
        weight=0.9,
        value=2.0,
        max_durability=0.5,
        degrade_per_hour=0.0,
        equip_slots=["right_foot"]
    )

    ITEMS_DB[121] = ItemType(
        121,
        "人字拖（左）",
        "一只破旧的人字拖，塑料夹脚带已经断过一次，用铁丝重新拧上了。聊胜于无。",
        weight=0.3,
        value=1.0,
        max_durability=0.3,
        degrade_per_hour=0.0,
        equip_slots=["left_foot"]
    )

    ITEMS_DB[122] = ItemType(
        122,
        "人字拖（右）",
        "一只破旧的人字拖，鞋底磨得比纸还薄，但至少脚底不用直接踩在滚烫的沙地上。",
        weight=0.3,
        value=1.0,
        max_durability=0.3,
        degrade_per_hour=0.0,
        equip_slots=["right_foot"]
    )
    ITEMS_DB[123] = ItemType(
        123, 
        "破旧兜帽",
        "一件连帽衫上撕下来的兜帽。挡不住子弹，但能遮住你的脸，让掠夺者第一眼认不出你的底细。",
        weight=0.2, 
        value=2.0, 
        max_durability=0.4, 
        degrade_per_hour=0.0,
        equip_slots=["hat"]
    )
    ITEMS_DB[124] = ItemType(
        124, 
        "狗牌项链",
        "一串军用识别牌，上面刻着一个陌生的名字。也许它的主人还在某处，也许早已化为白骨。",
        weight=0.1, 
        value=3.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=["neck"]
    )

    ITEMS_DB[125] = ItemType(
        125, 
        "破围巾",
        "一条手织的羊毛围巾，已经看不出原本的颜色。裹住脖子能抵御风寒和沙尘。",
        weight=0.3, 
        value=2.0, 
        max_durability=0.5, 
        degrade_per_hour=0.0,
        equip_slots=["neck"]
    )

    ITEMS_DB[126] = ItemType(
        126, 
        "皮夹克",
        "一件硬邦邦的旧皮衣，散发着烟味和汗味。比衬衫结实，还能挡一挡撕咬。",
        weight=2.0, 
        value=12.0, 
        max_durability=0.8, 
        degrade_per_hour=0.0,
        equip_slots=["torso"]
    )

    ITEMS_DB[127] = ItemType(
        127, 
        "防弹背心",
        "一件没有陶瓷插板的空防弹衣。挡不住步枪弹，但刀子和手枪弹头还能扛一扛。",
        weight=3.5, 
        value=30.0, 
        max_durability=0.85, 
        degrade_per_hour=0.0,
        equip_slots=["torso"]
    )

    ITEMS_DB[128] = ItemType(
        128, 
        "雨衣",
        "一件黄色的塑料雨衣，折叠起来只有拳头大。",
        weight=0.5, 
        value=5.0, 
        max_durability=0.6, 
        degrade_per_hour=0.0,
        equip_slots=["torso"]
    )

    ITEMS_DB[129] = ItemType(
        129, 
        "钢管",
        "一根从水管上拆下来的镀锌钢管。握在手里沉甸甸的，挥舞起来虎虎生风。",
        weight=1.8, 
        value=5.0, 
        max_durability=0.9, 
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[130] = ItemType(
        130, 
        "砍刀",
        "一把刃口卷刃的砍刀，木柄上缠着防滑胶带。",
        weight=1.2, 
        value=12.0, 
        max_durability=0.85, 
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[131] = ItemType(
        131, 
        "指虎",
        "一块铸造的金属指套，套在手指上能把普通的拳头变成凶器。轻便、隐蔽。",
        weight=0.2, 
        value=6.0, 
        max_durability=0.95, 
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[132] = ItemType(
        132, 
        "棒球棍",
        "一根木制棒球棍，棍身上刻着褪色的球队标志。挥起来顺手，砸下去扎实。",
        weight=1.4, 
        value=4.0, 
        max_durability=0.7, 
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[133] = ItemType(
        133, 
        "幸运手链",
        "一串用旧弹壳和彩色塑料片串成的手链。据说戴上它的人能多活几天。也许只是巧合。",
        weight=0.05, 
        value=2.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=["right_wrist"]
    )

    ITEMS_DB[134] = ItemType(
        134, 
        "牛仔裤",
        "一条褪色的蓝色牛仔裤，膝盖处磨出了洞。比工装裤薄，但活动更灵活。",
        weight=0.7, 
        value=3.0, 
        max_durability=0.6, 
        degrade_per_hour=0.0,
        equip_slots=["legs"]
    )

    ITEMS_DB[135] = ItemType(
        135, 
        "战术裤",
        "一条多口袋的军用战术裤。结实、耐磨，大腿两侧的口袋能塞下弹匣和绷带。",
        weight=1.0, 
        value=10.0, 
        max_durability=0.85, 
        degrade_per_hour=0.0,
        equip_slots=["legs"]
    )

    ITEMS_DB[136] = ItemType(
        136, 
        "护踝（左）",
        "一块用皮带固定在脚踝上的硬塑料片，防止崴脚。",
        weight=0.4, 
        value=4.0, 
        max_durability=0.7, 
        degrade_per_hour=0.0,
        equip_slots=["left_ankle"]
    )

    ITEMS_DB[137] = ItemType(
        137, 
        "护踝（右）",
        "一块用皮带固定在脚踝上的硬塑料片，和左脚配对的护踝。",
        weight=0.4, 
        value=4.0, 
        max_durability=0.7, 
        degrade_per_hour=0.0,
        equip_slots=["right_ankle"]
    )

    ITEMS_DB[138] = ItemType(
        138, 
        "肉罐头",
        "一罐没有标签的铁皮罐头。摇晃起来里面有液体晃动的声音。可能是午餐肉，也可能是狗粮。",
        weight=0.4, 
        value=5.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[139] = ItemType(
        139, 
        "干蘑菇",
        "一串用绳子穿起来的干瘪蘑菇，闻起来有一股泥土味。",
        weight=0.1, 
        value=3.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[140] = ItemType(
        140, 
        "能量棒",
        "一根包装完好的能量棒。末日前的产物，保质期长得离谱。咬一口，甜得发腻。",
        weight=0.1, 
        value=4.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[141] = ItemType(
        141, 
        "不明生肉",
        "一块从变异生物身上割下来的肉，还带着血。也许能吃，但最好烤熟了再碰。",
        weight=0.5, 
        value=2.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[142] = ItemType(
        142, 
        "军用口粮",
        "一包未拆封的军用即食口粮，迷彩包装完好无损。里面有主菜、饼干、速溶饮料——简直是国王的盛宴。",
        weight=0.6, 
        value=15.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[143] = ItemType(
        143, 
        "雨水收集瓶",
        "一瓶用塑料布收集到的雨水。水质浑浊，带着一股铁锈味，但至少是水。",
        weight=0.5, 
        value=2.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[144] = ItemType(
        144, 
        "瓶装可乐",
        "一瓶末日前的可乐，玻璃瓶还带着褪色的红色商标。气泡早已消散，但糖分还在。",
        weight=0.5, 
        value=4.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[145] = ItemType(
        145, 
        "酒精饮料",
        "一瓶来路不明的烈酒，标签被撕掉了。喝一口能暖胃，喝两口能暂时忘记自己身在废土。",
        weight=0.6, 
        value=6.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[146] = ItemType(
        146, 
        "净水药片",
        "一小瓶含氯净水药片。扔一颗进脏水里，等半小时，大部分细菌就死透了。",
        weight=0.05, 
        value=8.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[147] = ItemType(
        147, 
        "止痛药",
        "几片白色药片，包装上的字已经模糊不清。吞一片，疼痛会暂时退到角落。治不了病，但能让你再撑一会儿。",
        weight=0.05, 
        value=10.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[148] = ItemType(
        148, 
        "情报纸条",
        "一张写着坐标和潦草注记的纸条。可能是某个隐藏物资点，也可能是一个陷阱。",
        weight=0.01, 
        value=5.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[149] = ItemType(
        149, 
        "铜线",
        "一卷从废弃变压器上拆下来的铜线，导电性好。",
        weight=0.4, 
        value=3.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[150] = ItemType(
        150, 
        "塑料袋",
        "一个还算完整的塑料袋。装东西、套在头上——用途多得离谱。",
        weight=0.05, 
        value=0.5, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[151] = ItemType(
        151, 
        "胶带",
        "一卷银色的布基胶带。",
        weight=0.3, 
        value=4.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[152] = ItemType(
        152, 
        "弹簧",
        "一根从旧沙发或车座里拆出来的金属弹簧，弹性十足。",
        weight=0.3, 
        value=2.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[153] = ItemType(
        153, 
        "打火机",
        "一个塑料打火机，摇晃起来还能听到液体晃动的声音。",
        weight=0.05, 
        value=3.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[]
    )

    ITEMS_DB[154] = ItemType(
        154,
        "破旧地图",
        "一张泛黄的废土地图，上面用红笔标注了几个可疑的位置。虽然残缺不全，但至少能让你知道自己身在何处。",
        weight=0.1,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["left_hand"]
    )    

    ITEMS_DB[201] = ItemType(
        201,
        "纯净水",
        "一瓶未开封的瓶装水。透明、无味、没有辐射尘——废土上最奢侈的东西。",
        weight=0.5,
        value=5.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[]
    )
    