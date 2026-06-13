# =============================================================================
# items.rpy — 物品、武器、装备、药品、垃圾数据库
# 功能：定义静态物品原型（ItemType）与动态物品实例（ItemInstance）
# 职责：管理物品属性、耐久度衰减、堆叠上限、用途效果、图标路径
# =============================================================================
# ── 物品原型类（ItemType） ──
init python:
    class ItemType:
        """对应 itemtypes.xml 的静态数据类"""
        def __init__(self, id, name, desc, weight, value,
                    max_durability=1.0, degrade_per_hour=0.0,
                    equip_slots=None, max_stack=1,
                    grid_size=(1,1), grid_w=1, grid_h=1,
                    container_grid_size=None):
            self.id = id
            self.name = name
            self.desc = desc
            self.weight = weight
            self.value = value
            self.max_durability = max_durability
            self.degrade_per_hour = degrade_per_hour
            self.equip_slots = equip_slots or [] # 可装备的身体槽位
            self.max_stack = max_stack
            self.grid_w = max(int(grid_w), 1)
            self.grid_h = max(int(grid_h), 1)
            self.grid_size = (self.grid_w, self.grid_h)

            if container_grid_size is None:
                container_grid_size = grid_size
            self.container_grid_size = container_grid_size

    ITEM_GRID_SIZE_MAP = {
        # 穿戴物与小配件
        101: (2, 2), 102: (2, 1), 106: (1, 2), 107: (1, 2), 108: (2, 1),
        118: (1, 1), 119: (2, 1), 120: (2, 1), 121: (1, 1), 122: (1, 1),
        123: (1, 1), 124: (1, 1), 125: (1, 1), 126: (1, 2), 127: (2, 2),
        128: (1, 2), 133: (1, 1), 134: (1, 2), 135: (1, 2), 136: (1, 1),
        137: (1, 1), 154: (1, 1),

        # 武器与工具
        103: (2, 1), 104: (1, 1), 109: (1, 1), 110: (2, 1), 111: (2, 1),
        130: (2, 1), 131: (1, 1), 132: (2, 1), 217: (1, 1),

        # 材料与杂物
        105: (1, 1), 115: (1, 1), 116: (1, 2), 117: (1, 1), 148: (1, 1),
        149: (1, 1), 150: (1, 1), 151: (1, 1), 152: (1, 1), 153: (1, 1),

        # 消耗品
        112: (1, 1), 113: (1, 1), 114: (1, 1), 138: (1, 1), 139: (1, 1),
        140: (1, 1), 141: (1, 1), 142: (1, 2), 143: (1, 2), 144: (1, 2),
        145: (1, 2), 146: (1, 1), 147: (1, 1), 201: (1, 2),
        202: (1, 1), 203: (1, 1), 204: (1, 1), 205: (1, 1), 206: (1, 1),
        207: (1, 1), 208: (1, 1), 209: (1, 1), 210: (1, 1), 211: (1, 1),
        212: (1, 1), 213: (1, 1), 214: (1, 1), 215: (1, 1), 216: (1, 1),

        # 背包与腰带装备自身占格
        160: (1, 2), 161: (2, 2), 162: (2, 1), 163: (2, 1), 164: (3, 1),
        165: (2, 1), 166: (2, 1), 167: (2, 3), 168: (2, 3), 169: (3, 2),
        170: (2, 3), 171: (3, 3), 172: (3, 3),
    }

    ITEM_CONTAINER_GRID_SIZE_MAP = {
        # 腰带打开后的容量，上限由 inventory.rpy 控制为 5x1。
        160: (2, 1),
        162: (3, 1),
        163: (4, 1),
        164: (5, 1),

        # 背包打开后的容量，上限由 inventory.rpy 控制为 5x6。
        161: (2, 2),
        165: (3, 2),
        166: (4, 2),
        167: (3, 3),
        168: (5, 3),
        169: (4, 4),
        170: (5, 4),
        171: (5, 5),
        172: (5, 6),
    }

    DEFAULT_ITEM_GRID_SIZE = (1, 1)

    def apply_item_grid_sizes():
        """为所有物品配置占格尺寸。未命中的物品默认 1x1。"""
        for item_id, item_type in ITEMS_DB.items():
            grid_w, grid_h = ITEM_GRID_SIZE_MAP.get(item_id, DEFAULT_ITEM_GRID_SIZE)
            item_type.grid_w = max(int(grid_w), 1)
            item_type.grid_h = max(int(grid_h), 1)
            item_type.grid_size = (item_type.grid_w, item_type.grid_h)
            if item_id in ITEM_CONTAINER_GRID_SIZE_MAP:
                item_type.container_grid_size = ITEM_CONTAINER_GRID_SIZE_MAP[item_id]

# ── 物品实例类（ItemInstance）与工厂函数 ──
init python:
    class ItemInstance:
        """在背包及大地图世界中真实流转的动态实例"""
        def __init__(self, item_id, durability=1.0):
            self.id = item_id
            self.config = ITEMS_DB[item_id]
            self.durability = durability # 0.0~1.0

        @property
        def icon_path(self):
            """返回物品图标路径，由全局工具函数动态解析"""
            return get_item_icon_path(self.id)

        def degrade(self, hours=1.0):
            """耐久度因磨损或时间流逝产生降级"""
            if self.config.degrade_per_hour > 0:
                self.durability -= self.config.degrade_per_hour * hours
                if self.durability < 0:
                    self.durability = 0.0

# ── 物品实例工厂与地面交互函数 ──
    def create_item_instance(item_id, durability=None, random_durability=False):
        """工厂函数：基于 item_id 生成动态物品实例。
        
        参数:
            item_id: 物品 ID
            durability: 指定耐久度（None 则使用默认值）
            random_durability: 如果为 True，对可降解物品在 0.3~1.0 范围随机耐久度
        """
        if item_id not in ITEMS_DB:
            raise KeyError(f"Unknown item_id: {item_id}")
        
        item_config = ITEMS_DB[item_id]
        
        if durability is not None:
            final_durability = durability
        elif random_durability and item_config.degrade_per_hour > 0:
            final_durability = renpy.random.uniform(0.6, 1.0) * item_config.max_durability
        else:
            final_durability = item_config.max_durability
        
        return ItemInstance(item_id, final_durability)

    def drop_item_to_current_tile(item_instance, inv_instance):
        """将物品从背包丢弃到当前地面容器"""
        current_container = get_current_ground_container()
        if current_container is None:
            renpy.notify("当前地形没有可用的空位，无法丢弃。")
            return False

        moved_item = inv_instance.extract_item_for_transfer(item_instance)
        if moved_item is None:
            return False

        if not current_container.add_item(moved_item):
            inv_instance.add_item(moved_item)
            renpy.notify("地上的东西满了，无法丢弃。")
            return False

        renpy.notify(f"{item_instance.config.name} 已丢弃到地面。")
        return True

    def ui_action_drop_item(item_instance, inv_instance):
        """UI丢弃函数：拦截返回值，防止触发 Ren'Py 强制 Return"""
        drop_item_to_current_tile(item_instance, inv_instance)
        # 没有任何 return 语句，Python 默认返回 None

    def take_item_from_ground_to_player(item_instance, ground_container, player_inv):
        """从地面容器拾取物品到玩家背包"""
        moved_item = ground_container.extract_item_for_transfer(item_instance)
        if moved_item is None:
            return False

        if player_inv.add_item(moved_item):
            renpy.notify(f"{item_instance.config.name} 已放入背包。")
            return True
        else:
            ground_container.add_item(moved_item)
            renpy.notify("背包已满，无法取回。")
            return False

# =============================================================================
# 物品用途数据库
# 功能：定义可直接从背包"使用"的物品效果函数
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
        if renpy.random.random() < 0.2:
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
        if actor.hp >= actor.max_hp * MORIBUND_HP_THRESHOLD:
            remove_condition_by_id(actor, COND_MORIBUND)
        renpy.notify(f"你的生命值恢复了。")
        return True

    def use_splint(actor):
        """使用夹板：移除骨折状态"""
        if remove_condition_by_id(actor, COND_FRACTURE):
            return True
        return False

    # ──── 野生食物（森林/荒野）────
    def use_wild_blueberry(actor):
        """野生蓝莓：饥饿-5，口渴-3"""
        actor.hunger = max(0.0, actor.hunger - 5.0)
        actor.thirst = max(0.0, actor.thirst - 3.0)
        renpy.notify("你嚼着酸甜的蓝莓，汁水在嘴里炸开。")
        return True

    def use_wild_onion(actor):
        """野葱：饥饿-4，口渴+3"""
        actor.hunger = max(0.0, actor.hunger - 4.0)
        actor.thirst += 3.0
        renpy.notify("你嚼着辛辣的野葱，胃里暖和了，但嘴里干得冒火。")
        return True

    def use_dandelion_root(actor):
        """蒲公英根：饥饿-6"""
        actor.hunger = max(0.0, actor.hunger - 6.0)
        renpy.notify("你嚼着略带苦味的蒲公英根，泥土的腥甜在舌尖化开。")
        return True

    def use_wild_oat(actor):
        """野燕麦穗：饥饿-8，口渴+4"""
        actor.hunger = max(0.0, actor.hunger - 8.0)
        actor.thirst += 4.0
        renpy.notify("你搓掉谷壳，硬咽下粗糙的燕麦粒，嗓子眼发干。")
        return True

    def use_shepherd_purse(actor):
        """荠菜：饥饿-5"""
        actor.hunger = max(0.0, actor.hunger - 5.0)
        renpy.notify("你嚼着微甜的荠菜，叶片在齿间渗出清汁。")
        return True

    def use_pine_needle(actor):
        """松针：口渴-10，疲劳-3"""
        actor.thirst = max(0.0, actor.thirst - 10.0)
        actor.fatigue = max(0.0, actor.fatigue - 3.0)
        renpy.notify("你嚼碎了几根松针，苦涩的汁液让你精神一振。")
        return True

    # ──── 水域食物 ────
    def use_cattail_rhizome(actor):
        """香蒲根茎：饥饿-10，口渴+3"""
        actor.hunger = max(0.0, actor.hunger - 10.0)
        actor.thirst += 3.0
        renpy.notify("你啃着白色的香蒲根茎，淀粉的甜味在嘴里化开，但吃完嗓子发干。")
        return True

    def use_lake_algae(actor):
        """湖藻团：饥饿-6，15%中毒"""
        actor.hunger = max(0.0, actor.hunger - 6.0)
        if renpy.random.random() < 0.15:
            actor.add_condition(COND_POISON)
            renpy.notify("你吞下腥苦的湖藻，胃里一阵翻涌——果然不该生吃。")
        else:
            renpy.notify("你皱着眉头咽下晒干的湖藻团，满嘴都是腥味。")
        return True

    # ──── 海岸食物 ────
    def use_sea_asparagus(actor):
        """海芦笋：口渴-8，饥饿-3"""
        actor.thirst = max(0.0, actor.thirst - 8.0)
        actor.hunger = max(0.0, actor.hunger - 3.0)
        renpy.notify("你咬了一口多汁的海芦笋，咸涩的汁水在嘴里迸开。")
        return True

    def use_tide_crab(actor):
        """潮池小蟹：饥饿-8，25%中毒"""
        actor.hunger = max(0.0, actor.hunger - 8.0)
        if renpy.random.random() < 0.25:
            actor.add_condition(COND_POISON)
            renpy.notify("你嚼碎了小螃蟹，壳很脆，但肚子立刻开始抗议。")
        else:
            renpy.notify("你嘎嘣嘎嘣地嚼着小螃蟹，咸腥的味道填满了胃。")
        return True

    # ──── 沼泽食物 ────
    def use_water_vine(actor):
        """水藤：口渴-15，20%中毒"""
        actor.thirst = max(0.0, actor.thirst - 15.0)
        if renpy.random.random() < 0.20:
            actor.add_condition(COND_POISON)
            renpy.notify("你对着藤蔓切口喝了几口清水，但肚子里传来异样的绞痛。")
        else:
            renpy.notify("你对着藤蔓切口喝了几口清水，甘甜得让人想哭。")
        return True

    def use_rush_root(actor):
        """灯芯草根：口渴-6，饥饿-2"""
        actor.thirst = max(0.0, actor.thirst - 6.0)
        actor.hunger = max(0.0, actor.hunger - 2.0)
        renpy.notify("你嚼着纤维状的草根，汁水微甜，渣子吐了一地。")
        return True

    def use_peat_moss(actor):
        """泥炭藓：移除流血"""
        removed = remove_condition_by_id(actor, COND_BLEED)
        if removed:
            renpy.notify("你用泥炭藓紧紧裹住伤口，流血止住了。")
        else:
            renpy.notify("你并没有需要包扎的伤口。")
        return removed

    # ──── 狩猎食物 ────
    def use_bird_egg(actor):
        """鸟蛋：饥饿-5，5%中毒"""
        actor.hunger = max(0.0, actor.hunger - 5.0)
        if renpy.random.random() < 0.05:
            actor.add_condition(COND_POISON)
            renpy.notify("你生吞了鸟蛋，蛋液腥得呛喉，胃里一阵翻涌。")
        else:
            renpy.notify("你生吞了鸟蛋，温热的蛋液滑过喉咙，补充了一点体力。")
        return True

    def use_honeycomb(actor):
        """蜂蜜巢碎片：饥饿-4，口渴-2"""
        actor.hunger = max(0.0, actor.hunger - 4.0)
        actor.thirst = max(0.0, actor.thirst - 2.0)
        renpy.notify("你咬下一块蜂巢，浓稠的蜂蜜在舌尖化开——废土上最奢侈的甜味。")
        return True

    # ── 物品用途映射表 ──
    ITEM_USE_FUNCTIONS = {
        112: use_antibiotic,          # 抗生素
        113: use_bandage,             # 绷带
        114: use_compressed_biscuit,  # 压缩饼干 -25饥饿
        138: use_meat_can,            # 肉罐头 -30饥饿
        139: use_dried_mushroom,      # 干蘑菇 -10饥饿
        140: use_energy_bar,          # 能量棒 -20饥饿
        141: use_raw_meat,            # 不明生肉 -15饥饿(20%中毒)
        142: use_military_ration,     # 军用口粮 -45饥饿
        143: use_rainwater,           # 雨水收集瓶 -15口渴
        144: use_cola,                # 瓶装可乐 -20口渴
        145: use_alcohol,             # 酒精饮料 -10口渴
        201: use_purified_water,      # 纯净水 -40口渴
        # ── 野生食物 ──
        202: use_wild_blueberry,
        203: use_wild_onion,
        204: use_dandelion_root,
        205: use_wild_oat,
        206: use_shepherd_purse,
        207: use_pine_needle,
        # ── 水域 ──
        208: use_cattail_rhizome,
        209: use_lake_algae,
        # ── 海岸 ──
        210: use_sea_asparagus,
        211: use_tide_crab,
        # ── 沼泽 ──
        212: use_water_vine,
        213: use_rush_root,
        214: use_peat_moss,
        # ── 狩猎 ──
        215: use_bird_egg,
        216: use_honeycomb,
    }

    # ── 物品用途映射表 ──
    WEAPON_ATTACK_MAP = {
        109: [7],        # 水果刀 → 匕首捅刺
        110: [2],        # 工具锤 → 强力重击
        130: [3],        # 砍刀 → 砍刀挥砍
        132: [11],       # 棒球棍 → 棒球棍猛击
        131: [9],        # 指虎 → 指虎连击
        111: [12],       # 撬棍 → 撬棍猛击
        104: [5],        # 破旧手枪 → 手枪射击
    }

# ── 通用物品使用函数 ──
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
        success = use_function(actor)
        
        return (success, item_instance)

init python:
    def use_item_and_refresh_screen(item_instance, inv_instance, actor=None):
        """使用物品并刷新背包界面。"""
        success, item = use_item_from_inventory(item_instance, actor=actor)
        if success:
            inv_instance.remove_item(item)

# =============================================================================
# 物品数据库注册表
# 功能：向 ITEMS_DB 注册所有物品原型
# =============================================================================
# ── 装备类物品 ──
init python:
    ITEMS_DB[101] = ItemType(
        101,
        "破旧头盔",
        "一顶布满划痕的二战头盔，内衬海绵早已塌陷，但至少还能护住你的脑袋。",
        weight=1.2,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.01,
        equip_slots=["hat"]
    )

    ITEMS_DB[102] = ItemType(
        102,
        "破旧军靴（左）",
        "一只饱经风霜的军用皮靴。鞋底磨得差不多了，但比赤脚踩在碎玻璃上好。",
        weight=1.2,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.02,
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
        equip_slots=[], max_stack=5
    )

    ITEMS_DB[106] = ItemType(
        106,
        "破旧白衬衫",
        "一件发黄的旧衬衫。穿上它，至少让你感觉自己还是个人。",
        weight=0.3,
        value=2.0,
        max_durability=1.0,
        degrade_per_hour=0.01,
        equip_slots=["torso"]
    )

    ITEMS_DB[107] = ItemType(
        107,
        "破旧工装裤",
        "一条满是污渍的帆布工装裤。膝盖处的布料已经磨穿，但口袋多，能装。",
        weight=0.6,
        value=3.0,
        max_durability=1.0,
        degrade_per_hour=0.01,
        equip_slots=["legs"]
    )

    ITEMS_DB[108] = ItemType(
        108,
        "肮脏运动鞋（左）",
        "一只看不出原本颜色的运动鞋。鞋底开胶了，走路时会灌进沙子和碎石。",
        weight=0.9,
        value=2.0,
        max_durability=1.0,
        degrade_per_hour=0.03,
        equip_slots=["left_foot"]
    )

    ITEMS_DB[109] = ItemType(
        109,
        "水果刀",
        "一把厨房用的水果刀，刀柄缠着防滑胶带。切东西还行，捅人也凑合。",
        weight=0.3,
        value=3.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[110] = ItemType(
        110,
        "工具锤",
        "一把结实的羊角锤。锤头有些锈迹，但钉钉子、砸颅骨都同样顺手。",
        weight=1.5,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[111] = ItemType(
        111,
        "撬棍",
        "一根淬过火的钢材撬棍。除了撬开锁死的门，也能让不长眼的掠夺者安静下来。",
        weight=2.0,
        value=10.0,
        max_durability=1.0,
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
        equip_slots=[], max_stack=8
    )

    ITEMS_DB[113] = ItemType(
        113,
        "绷带",
        "一卷医用纱布绷带。干净、柔韧，能把裂开的伤口紧紧裹住。",
        weight=0.1,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=5
    )

    ITEMS_DB[114] = ItemType(
        114,
        "压缩饼干",
        "一包已经破损的军用压缩饼干。硬得像砖头，但一小口就能撑半天。",
        weight=0.2,
        value=6.0,
        max_durability=1.0,
        degrade_per_hour=0.001,
        equip_slots=[], max_stack=4
    )

    ITEMS_DB[115] = ItemType(
        115,
        "破布",
        "几块从旧衣服上撕下来的布料。擦血、生火、堵门缝——破布永远不会嫌多。",
        weight=0.2,
        value=1.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=8
    )

    ITEMS_DB[116] = ItemType(
        116,
        "玻璃瓶",
        "一个空玻璃瓶，标签早已脱落。装水、储存零碎、或者砸碎当武器都行。",
        weight=0.4,
        value=1.5,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[117] = ItemType(
        117,
        "废电池",
        "漏液的旧电池。电量所剩无几，但在懂行的人手里，也许还能榨出最后一点用处。",
        weight=0.3,
        value=2.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=4
    )

    ITEMS_DB[118] = ItemType(
        118,
        "破旧电子表",
        "一块靠太阳能驱动的电子表。屏幕裂了一条缝，但数字还在跳动。它记得时间，也许也记得末日前的某一天。",
        weight=0.1,
        value=5.0,
        max_durability=1.0,
        degrade_per_hour=0.01,
        equip_slots=["left_wrist"] 
    )

    ITEMS_DB[119] = ItemType(
        119,
        "破旧军靴（右）",
        "一只饱经风霜的军用皮靴。和左脚那只凑成一对，总算能好好走路了。",
        weight=1.2,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.02,
        equip_slots=["right_foot"]
    )

    ITEMS_DB[120] = ItemType(
        120,
        "肮脏运动鞋（右）",
        "一只看不出原本颜色的运动鞋。和左脚那只凑成一对，至少能跑。",
        weight=0.9,
        value=2.0,
        max_durability=1.0,
        degrade_per_hour=0.03,
        equip_slots=["right_foot"]
    )

    ITEMS_DB[121] = ItemType(
        121,
        "人字拖（左）",
        "一只破旧的人字拖，塑料夹脚带已经断过一次，用铁丝重新拧上了。聊胜于无。",
        weight=0.3,
        value=1.0,
        max_durability=1.0,
        degrade_per_hour=0.04,
        equip_slots=["left_foot"]
    )

    ITEMS_DB[122] = ItemType(
        122,
        "人字拖（右）",
        "一只破旧的人字拖，鞋底磨得比纸还薄，但至少脚底不用直接踩在滚烫的沙地上。",
        weight=0.3,
        value=1.0,
        max_durability=1.0,
        degrade_per_hour=0.04,
        equip_slots=["right_foot"]
    )
    ITEMS_DB[123] = ItemType(
        123, 
        "破旧兜帽",
        "一件连帽衫上撕下来的兜帽。挡不住子弹，但能遮住你的脸，让掠夺者第一眼认不出你的底细。",
        weight=0.2, 
        value=2.0, 
        max_durability=1.0,
        degrade_per_hour=0.01,
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
        max_durability=1.0,
        degrade_per_hour=0.01,
        equip_slots=["neck"]
    )

    ITEMS_DB[126] = ItemType(
        126, 
        "皮夹克",
        "一件硬邦邦的旧皮衣，散发着烟味和汗味。比衬衫结实，还能挡一挡撕咬。",
        weight=2.0, 
        value=12.0, 
        max_durability=1.0,
        degrade_per_hour=0.02,
        equip_slots=["torso"]
    )

    ITEMS_DB[127] = ItemType(
        127, 
        "防弹背心",
        "一件没有陶瓷插板的空防弹衣。挡不住步枪弹，但刀子和手枪弹头还能扛一扛。",
        weight=3.5, 
        value=30.0, 
        max_durability=1.0,
        degrade_per_hour=0.03,
        equip_slots=["torso"]
    )

    ITEMS_DB[128] = ItemType(
        128, 
        "雨衣",
        "一件黄色的塑料雨衣，折叠起来只有拳头大。",
        weight=0.5, 
        value=5.0, 
        max_durability=1.0,
        degrade_per_hour=0.02,
        equip_slots=["torso"]
    )

    #ITEMS_DB[129] = ItemType(
    #    129, 
    #    "钢管",
    #    "一根从水管上拆下来的镀锌钢管。握在手里沉甸甸的，挥舞起来虎虎生风。",
    #    weight=1.8, 
    #    value=5.0, 
    #    max_durability=0.9, 
    #    degrade_per_hour=0.0,
    #    equip_slots=["right_hand"]
    #)

    ITEMS_DB[130] = ItemType(
        130, 
        "砍刀",
        "一把刃口卷刃的砍刀，木柄上缠着防滑胶带。",
        weight=1.2, 
        value=12.0, 
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[131] = ItemType(
        131, 
        "指虎",
        "一块铸造的金属指套，套在手指上能把普通的拳头变成凶器。轻便、隐蔽。",
        weight=0.2, 
        value=6.0, 
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["right_hand"]
    )

    ITEMS_DB[132] = ItemType(
        132, 
        "棒球棍",
        "一根木制棒球棍，棍身上刻着褪色的球队标志。挥起来顺手，砸下去扎实。",
        weight=1.4, 
        value=4.0, 
        max_durability=1.0,
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
        max_durability=1.0,
        degrade_per_hour=0.01,
        equip_slots=["legs"]
    )

    ITEMS_DB[135] = ItemType(
        135, 
        "战术裤",
        "一条多口袋的军用战术裤。结实、耐磨，大腿两侧的口袋能塞下弹匣和绷带。",
        weight=1.0, 
        value=10.0, 
        max_durability=1.0,
        degrade_per_hour=0.02,
        equip_slots=["legs"]
    )

    ITEMS_DB[136] = ItemType(
        136, 
        "护踝（左）",
        "一块用皮带固定在脚踝上的硬塑料片，防止崴脚。",
        weight=0.4, 
        value=4.0, 
        max_durability=1.0,
        degrade_per_hour=0.02,
        equip_slots=["left_ankle"]
    )

    ITEMS_DB[137] = ItemType(
        137, 
        "护踝（右）",
        "一块用皮带固定在脚踝上的硬塑料片，和左脚配对的护踝。",
        weight=0.4, 
        value=4.0, 
        max_durability=1.0,
        degrade_per_hour=0.02,
        equip_slots=["right_ankle"]
    )

    ITEMS_DB[138] = ItemType(
        138, 
        "肉罐头",
        "一罐没有标签的铁皮罐头。摇晃起来里面有液体晃动的声音。可能是午餐肉，也可能是狗粮。",
        weight=0.4, 
        value=5.0, 
        max_durability=1.0, 
        degrade_per_hour=0.001,
        equip_slots=[], max_stack=3
    )

    ITEMS_DB[139] = ItemType(
        139, 
        "干蘑菇",
        "一串干瘪蘑菇，闻起来有一股泥土味。",
        weight=0.1, 
        value=3.0, 
        max_durability=1.0, 
        degrade_per_hour=0.002,
        equip_slots=[], max_stack=6
    )

    ITEMS_DB[140] = ItemType(
        140, 
        "能量棒",
        "一根包装完好的能量棒。末日前的产物，保质期长得离谱。咬一口，甜得发腻。",
        weight=0.1, 
        value=4.0, 
        max_durability=1.0, 
        degrade_per_hour=0.001,
        equip_slots=[], max_stack=5
    )

    ITEMS_DB[141] = ItemType(
        141, 
        "不明生肉",
        "一块从变异生物身上割下来的肉，还带着血。也许能吃，但最好烤熟了再碰。",
        weight=0.5, 
        value=2.0, 
        max_durability=1.0, 
        degrade_per_hour=0.02,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[142] = ItemType(
        142, 
        "军用口粮",
        "一包未拆封的军用即食口粮，迷彩包装完好无损。里面有主菜、饼干、速溶饮料——简直是国王的盛宴。",
        weight=0.6, 
        value=15.0, 
        max_durability=1.0, 
        degrade_per_hour=0.001,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[143] = ItemType(
        143, 
        "雨水收集瓶",
        "一瓶用塑料布收集到的雨水。水质浑浊，带着一股铁锈味，但至少是水。",
        weight=0.5, 
        value=2.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[144] = ItemType(
        144, 
        "瓶装可乐",
        "一瓶末日前的可乐，玻璃瓶还带着褪色的红色商标。气泡早已消散，但糖分还在。",
        weight=0.5, 
        value=4.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[145] = ItemType(
        145, 
        "酒精饮料",
        "一瓶来路不明的烈酒，标签被撕掉了。喝一口能暖胃，喝两口能暂时忘记自己身在废土，喝三口…",
        weight=0.6, 
        value=6.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[146] = ItemType(
        146, 
        "净水药片",
        "一小瓶含氯净水药片。扔一颗进脏水里，等半小时，大部分细菌就死透了。",
        weight=0.05, 
        value=8.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=12
    )

    ITEMS_DB[147] = ItemType(
        147, 
        "止痛药",
        "几片白色药片，包装上的字已经模糊不清。吞一片，疼痛会暂时退到角落。治不了病，但能让你再撑一会儿。",
        weight=0.05, 
        value=10.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=8
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
        equip_slots=[], max_stack=4
    )

    ITEMS_DB[150] = ItemType(
        150, 
        "塑料袋",
        "一个还算完整的塑料袋。装东西、套在头上——用途多得离谱。",
        weight=0.05, 
        value=0.5, 
        max_durability=1.0, 
        degrade_per_hour=0.01,
        equip_slots=[], max_stack=6
    )

    ITEMS_DB[151] = ItemType(
        151, 
        "胶带",
        "一卷银色的布基胶带。",
        weight=0.3, 
        value=4.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=3
    )

    ITEMS_DB[152] = ItemType(
        152, 
        "弹簧",
        "一根从旧沙发或车座里拆出来的金属弹簧，弹性十足。",
        weight=0.3, 
        value=2.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=3
    )

    ITEMS_DB[153] = ItemType(
        153, 
        "打火机",
        "一个塑料打火机，摇晃起来还能听到液体晃动的声音。",
        weight=0.05, 
        value=3.0, 
        max_durability=1.0, 
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=2
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

    ITEMS_DB[160] = ItemType(
        160,
        "破布条",
        "一根从旧衣服上撕下来的布条，勉强能把几样东西捆在腰上。",
        weight=0.2,
        value=2.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["waist"],
        max_stack=1
    )

    ITEMS_DB[161] = ItemType(
        161,
        "杂物袋",
        "一个脏兮兮的粗麻布袋，袋口用一根绳子收紧。捡垃圾专用。",
        weight=0.8,
        value=3.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[162] = ItemType(
        162,
        "简易腰包",
        "用帆布碎料缝成的小腰包，拉链坏了，用别针扣着。装不了多少，但总比塞裤兜里强。",
        weight=0.2,
        value=8.0,
        max_durability=0.5,
        degrade_per_hour=0.02,
        equip_slots=["waist"],
        max_stack=1
    )

    ITEMS_DB[163] = ItemType(
        163,
        "战术腰封",
        "一条加宽的尼龙腰封，挂满了小口袋和快拔套。",
        weight=0.4,
        value=22.0,
        max_durability=0.8,
        degrade_per_hour=0.01,
        equip_slots=["waist"],
        max_stack=1
    )

    ITEMS_DB[164] = ItemType(
        164,
        "拾荒者工具带",
        "一条加厚皮革腰带，上面挂着各种挂钩和套环。从扳手到手枪，什么都能挂上去。",
        weight=0.6,
        value=55.0,
        max_durability=0.9,
        degrade_per_hour=0.005,
        equip_slots=["waist"],
        max_stack=1
    )

    ITEMS_DB[165] = ItemType(
        165,
        "简易挎包",
        "用破帆布和汽车安全带缝成的斜挎包。背带勒得肩膀生疼，但比空着手强。",
        weight=0.5,
        value=8.0,
        max_durability=0.5,
        degrade_per_hour=0.02,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[166] = ItemType(
        166,
        "褡裢",
        "一条搭在肩上的旧布口袋，前后各一个兜，容量不小。末日前的农民用它装种子，现在的幸存者用它装一切可以换钱的东西。",
        weight=0.6,
        value=12.0,
        max_durability=0.5,
        degrade_per_hour=0.02,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[167] = ItemType(
        167,
        "登山包",
        "旧时代的登山装备，背负系统尚好，背起来比看上去舒服。",
        weight=1.0,
        value=25.0,
        max_durability=0.8,
        degrade_per_hour=0.01,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[168] = ItemType(
        168,
        "帆布背包",
        "一个褪色的旧书包，拉链半坏，底部磨出了洞。学生时代的遗物，如今装的是生存的希望。",
        weight=0.8,
        value=18.0,
        max_durability=0.6,
        degrade_per_hour=0.015,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[169] = ItemType(
        169,
        "猎人背架",
        "一个焊接的金属外框，可以把猎物或任何大件物品捆在上面。看起来很原始，但极其实用。",
        weight=1.5,
        value=28.0,
        max_durability=0.9,
        degrade_per_hour=0.005,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[170] = ItemType(
        170,
        "军用突击背包",
        "完整的军用背包，迷彩布料，快拆扣具完好。",
        weight=1.8,
        value=45.0,
        max_durability=0.9,
        degrade_per_hour=0.005,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[171] = ItemType(
        171,
        "流浪者大背囊",
        "用防水油布和金属支架手工打造的巨大背囊。几乎能装下一个人的全部家当。",
        weight=2.5,
        value=30.0,
        max_durability=0.7,
        degrade_per_hour=0.015,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[172] = ItemType(
        172,
        "商队驮包",
        "原本是双头牛背上的货箱，被幸存者改装成了人用背包。容量大到荒谬。",
        weight=4.0,
        value=65.0,
        max_durability=0.85,
        degrade_per_hour=0.01,
        equip_slots=["backpack"],
        max_stack=1
    )

    ITEMS_DB[201] = ItemType(
        201,
        "纯净水",
        "一瓶未开封的瓶装水。透明、无味、没有辐射尘——废土上最奢侈的东西。",
        weight=0.5,
        value=5.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=2
    )
    # ── 野生食物（森林/荒野） ──
    ITEMS_DB[202] = ItemType(
        202,
        "野生蓝莓",
        "一捧深蓝色的小浆果，表面覆着薄霜般的天然果粉。很甜，汁水会在指尖染上紫色。",
        weight=0.1,
        value=2.0,
        max_durability=0.4,
        degrade_per_hour=0.04,
        equip_slots=[], max_stack=6
    )

    ITEMS_DB[203] = ItemType(
        203,
        "野葱",
        "几根纤细的绿色茎叶，根部带着泥土，闻起来有刺鼻的辛辣味。嚼着吃能提神，但之后会更渴。",
        weight=0.1,
        value=2.0,
        max_durability=0.5,
        degrade_per_hour=0.03,
        equip_slots=[], max_stack=4
    )

    ITEMS_DB[204] = ItemType(
        204,
        "蒲公英根",
        "挖出来的褐色根茎，带着泥土的腥甜。洗净后可以生嚼。",
        weight=0.15,
        value=3.0,
        max_durability=0.6,
        degrade_per_hour=0.02,
        equip_slots=[], max_stack=3
    )

    ITEMS_DB[205] = ItemType(
        205,
        "野燕麦穗",
        "几株垂着头的野生燕麦，谷粒小而硬，外壳带芒。得搓掉壳才能咽下去，吃完嗓子发干。",
        weight=0.2,
        value=1.0,
        max_durability=0.3,
        degrade_per_hour=0.05,
        equip_slots=[], max_stack=5
    )

    ITEMS_DB[206] = ItemType(
        206,
        "荠菜",
        "一丛贴地生长的野菜，叶片呈锯齿状，中心抽出一根细长的花茎。末日前的田间杂草，现在的救命食物。",
        weight=0.12,
        value=2.0,
        max_durability=0.4,
        degrade_per_hour=0.04,
        equip_slots=[], max_stack=4
    )

    ITEMS_DB[207] = ItemType(
        207,
        "松针",
        "一把墨绿色的松树针叶，表面有蜡质光泽。直接嚼又苦又涩。",
        weight=0.08,
        value=1.0,
        max_durability=0.5,
        degrade_per_hour=0.02,
        equip_slots=[], max_stack=8
    )

    # ── 水域 ──
    ITEMS_DB[208] = ItemType(
        208,
        "香蒲根茎",
        "从浅水中拔出的香蒲，根部像一节节白色的藕。可以生吃，淀粉含量很高，顶饿。",
        weight=0.25,
        value=3.0,
        max_durability=0.5,
        degrade_per_hour=0.03,
        equip_slots=[], max_stack=3
    )

    ITEMS_DB[209] = ItemType(
        209,
        "湖藻团",
        "一团被水冲上来的深绿色藻类，摸起来滑腻。晒干后可以当干粮，生吃味道腥苦，还可能闹肚子。",
        weight=0.15,
        value=1.0,
        max_durability=0.3,
        degrade_per_hour=0.06,
        equip_slots=[], max_stack=4
    )

    # ── 海岸 ──
    ITEMS_DB[210] = ItemType(
        210,
        "海芦笋",
        "一丛长在沙滩高处的肉质植物，茎秆像迷你芦笋，咬开是咸的汁水。解渴，但越喝越渴。",
        weight=0.12,
        value=2.0,
        max_durability=0.4,
        degrade_per_hour=0.04,
        equip_slots=[], max_stack=5
    )

    ITEMS_DB[211] = ItemType(
        211,
        "潮池小蟹",
        "几只硬币大小的螃蟹，在退潮后的礁石水坑里爬动。活吃很腥，但能填肚子。",
        weight=0.3,
        value=3.0,
        max_durability=0.3,
        degrade_per_hour=0.08,
        equip_slots=[], max_stack=2
    )

    # ── 沼泽 ──
    ITEMS_DB[212] = ItemType(
        212,
        "水藤",
        "一段拇指粗的藤蔓，两端切口渗出清澈的汁液。砍断后可以直接对着嘴喝，但可能有虫卵。",
        weight=0.3,
        value=2.0,
        max_durability=0.3,
        degrade_per_hour=0.05,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[213] = ItemType(
        213,
        "灯芯草根",
        "白色纤维状的根茎，嚼起来像甘蔗，汁水微甜但纤维很多，嚼完得吐渣。",
        weight=0.18,
        value=1.0,
        max_durability=0.4,
        degrade_per_hour=0.04,
        equip_slots=[], max_stack=4
    )

    ITEMS_DB[214] = ItemType(
        214,
        "泥炭藓",
        "一团从沼泽泥地中扯出的苔藓，吸水性极强，天然抗菌。不能吃，但可以应急当绷带用。",
        weight=0.08,
        value=3.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[], max_stack=3
    )

    # ── 狩猎 ──
    ITEMS_DB[215] = ItemType(
        215,
        "鸟蛋",
        "一枚带着褐色斑点的鸟蛋，壳很薄，握在手心里还能感受到微微的温度。生吞也行，但烤熟了更香。",
        weight=0.06,
        value=4.0,
        max_durability=0.5,
        degrade_per_hour=0.03,
        equip_slots=[], max_stack=2
    )

    ITEMS_DB[216] = ItemType(
        216,
        "蜂蜜巢碎片",
        "一块从树洞或岩缝里掰下来的蜂巢碎片，滴着金黄色的浓稠液体。甜得不像废土上该有的东西。",
        weight=0.2,
        value=6.0,
        max_durability=0.7,
        degrade_per_hour=0.01,
        equip_slots=[], max_stack=1
    )

    ITEMS_DB[217] = ItemType(
        217,
        "夹板",
        "几根木条和绷带组成的简易固定夹板。可以固定骨折部位，缓解疼痛，让伤者恢复行动能力。",
        weight=0.5,
        value=8.0,
        max_durability=1.0,
        degrade_per_hour=0.0,
        equip_slots=[],
        max_stack=3
    )

    apply_item_grid_sizes()
