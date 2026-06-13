# =============================================================================
# 商城/交易系统后台逻辑（价格计算、货币扣除）
# 定义：黑市、废土商人、NPC 交易的静态公式。
# 实现：计算物品的最终成交价；执行货币（香烟）扣除逻辑。
# =============================================================================
init python:
    MERCHANT_GRID_COLS = 5
    MERCHANT_GRID_ROWS = 12

    # 临时变量，用于传递当前交易商人配置给独立标签
    _current_trade_trader_config = None

    # 商人配置数据结构
    class MerchantConfig:
        def __init__(self, merchant_id, name, shop_type, avatar_path=None, 
                    description="", region=None):
            self.merchant_id = merchant_id
            self.name = name
            self.shop_type = shop_type
            self.avatar_path = avatar_path
            self.description = description
            self.region = region
            # 运行时缓存，用于实现"每天刷新一次库存"
            self._inventory = None      # 当前持有的 Inventory 实例
            self._last_refresh_day = -1  # 上次刷新时的 game_time['day']，-1 表示从未刷新

    
    def get_shop_price(item_instance, shop_type=SHOP_TYPE_WASTELAND_TRADER, buy=True, barter_rate=1.0):
        """
        计算物品在商店中的最终价格。
        
        参数:
            item_instance: 物品实例
            shop_type: 商店类型
            buy: True=玩家从商店买入，False=玩家卖给商店
            barter_rate: 额外汇率倍率（用于特殊NPC或剧情场景）
        
        返回:
            float: 最终价格（香烟数）
        """
        config = SHOP_PRICE_MODIFIERS.get(shop_type, SHOP_PRICE_MODIFIERS[SHOP_TYPE_WASTELAND_TRADER])
        
        if buy:
            # 玩家买入价格 = 基础价值 × 买入倍率 × 汇率
            price = item_instance.config.value * config["buy_multiplier"] * barter_rate
        else:
            # 玩家卖出价格 = 基础价值 × 卖出倍率 × 汇率
            price = item_instance.config.value * config["sell_multiplier"] * barter_rate
            
        return int(round(price))  # 四舍五入到整数
    
    def shop_can_afford(player_stats, amount):
        """检查玩家是否有足够的香烟。"""
        return player_stats.cigarettes >= amount
    
    def shop_apply_payment(player_stats, amount):
        """从玩家扣除香烟。"""
        if player_stats.cigarettes >= amount:
            player_stats.cigarettes -= amount
            return True
        return False
    
    def shop_apply_income(player_stats, amount):
        """向玩家支付香烟（卖出物品所得）。"""
        player_stats.cigarettes += amount
    
    def shop_execute_purchase(player_inv, merchant_inv, item_instance, shop_type, barter_rate=1.0):
        """执行购买逻辑：玩家消耗香烟，获得物品；商人失去物品。"""
        # 计算商品购买价格
        buy_price = get_shop_price(item_instance, shop_type, buy=True, barter_rate=barter_rate)
        
        # 检查玩家资产是否足够
        if not shop_can_afford(player_stats, buy_price):
            renpy.notify("香烟不足，无法购买！")
            return

        # 检查玩家背包是否有足够空间
        can_stack = False
        if item_instance.config.max_stack > 1:
            for entry in player_inv.grid_items.values():
                if entry["item"].id == item_instance.id and entry["stack"] < item_instance.config.max_stack:
                    can_stack = True
                    break

        if not can_stack and player_inv.find_space_for_item(item_instance) is None:
            renpy.notify("你的背包已经满了。")
            return

        moved_item = merchant_inv.extract_item_for_transfer(item_instance)
        if moved_item is None:
            renpy.notify("商品不存在，无法购买。")
            return

        # 扣除资产并转移物品
        player_stats.cigarettes -= buy_price

        if not player_inv.add_item(moved_item):
            merchant_inv.add_item(moved_item)
            player_stats.cigarettes += buy_price
            renpy.notify("你的背包已经满了。")
            return
        
        renpy.notify(f"花费 {buy_price:.0f} 支烟购买了 {item_instance.config.name}")
        renpy.restart_interaction()
    
    def shop_execute_sell(player_inv, merchant_inv, item_instance, shop_type, barter_rate=1.0):
        """执行卖出逻辑：玩家失去物品，获得香烟；商人获得物品。"""
        # 计算商品出售价格
        sell_price = get_shop_price(item_instance, shop_type, buy=False, barter_rate=barter_rate)
        
        can_stack = False
        if item_instance.config.max_stack > 1:
            for entry in merchant_inv.grid_items.values():
                if entry["item"].id == item_instance.id and entry["stack"] < item_instance.config.max_stack:
                    can_stack = True
                    break

        if not can_stack and merchant_inv.find_space_for_item(item_instance) is None:
            renpy.notify("商人的背包已经满了。")
            return

        moved_item = player_inv.extract_item_for_transfer(item_instance)
        if moved_item is None:
            renpy.notify("你没有这件物品。")
            return

        # 扣除玩家物品并结算香烟
        if not merchant_inv.add_item(moved_item):
            player_inv.add_item(moved_item)
            renpy.notify("商人的背包已经满了。")
            return
        player_stats.cigarettes += sell_price
        
        renpy.notify(f"卖出 {item_instance.config.name}，获得 {sell_price:.0f} 支烟")
        renpy.restart_interaction()

    # 不同地区的商人定义
    MERCHANT_WASTELAND_TRADER = MerchantConfig(
        merchant_id="wasteland_trader_01",
        name="流浪商人",
        shop_type=SHOP_TYPE_WASTELAND_TRADER,
        avatar_path="images/merchant_wasteland.png",
        description="一个风尘仆仆的废土商人，他的骆驼背上驮着满满的货箱。",
        region="wasteland",
    )

    MERCHANT_CITY_TRADER = MerchantConfig(
        merchant_id="city_trader_01",
        name="城市商人",
        shop_type=SHOP_TYPE_NPC,
        avatar_path="images/merchant_city.png",
        description="一个精明的城市商人，他的店铺里摆满了各种废土上的稀缺物资。",
        region="city",
    )

    MERCHANT_BLACK_MARKET = MerchantConfig(
        merchant_id="black_market_01",
        name="地下黑市商人",
        shop_type=SHOP_TYPE_BLACK_MARKET,
        avatar_path="images/merchant_blackmarket.png",
        description="一个躲在阴影中的神秘人物，他的货物来源不明但品质上乘。",
        region="city_underground",
    )

    # 商人查找表
    MERCHANT_DB = {
        "wasteland_trader_01": MERCHANT_WASTELAND_TRADER,
        "city_trader_01": MERCHANT_CITY_TRADER,
        "black_market_01": MERCHANT_BLACK_MARKET,
    }

    # 按区域查找商人
    MERCHANTS_BY_REGION = {
        "wasteland": ["wasteland_trader_01"],
        "city": ["city_trader_01", "black_market_01"],
        "city_underground": ["black_market_01"],
    }

    def create_merchant_inventory(merchant_config):
        """根据稀有度权重生成商人库存（最多30件，每稀有度至少2件）"""
        inv = Inventory(
            max_slots=MERCHANT_GRID_COLS * MERCHANT_GRID_ROWS,
            grid_cols=MERCHANT_GRID_COLS,
            grid_rows=MERCHANT_GRID_ROWS,
        )

        MAX_MERCHANT_ITEMS = 30
        selected_ids = []

        # 1. 每个稀有度至少选2件
        for rarity, data in LOOT_RARITY.items():
            pool = list(data["items"])
            renpy.random.shuffle(pool)
            count = min(2, len(pool))
            for i in range(count):
                selected_ids.append(pool[i])

        # 2. 用权重填充剩余名额到30件
        remaining = MAX_MERCHANT_ITEMS - len(selected_ids)
        if remaining > 0:
            weighted_pool = []
            for rarity, data in LOOT_RARITY.items():
                for item_id in data["items"]:
                    weighted_pool.append((item_id, data["weight"]))

            for i in range(remaining):
                if not weighted_pool:
                    break
                total_weight = sum(w for _, w in weighted_pool)
                roll = renpy.random.random() * total_weight
                cumulative = 0
                chosen_id = weighted_pool[0][0]
                for item_id, weight in weighted_pool:
                    cumulative += weight
                    if roll <= cumulative:
                        chosen_id = item_id
                        break
                selected_ids.append(chosen_id)

        # 3. 生成物品实例
        for item_id in selected_ids:
            item_instance = create_item_instance(item_id, random_durability=True)
            inv.add_item(item_instance)

        return inv

    def get_merchant_inventory(merchant_config):
        """
        获取商人的当前库存。
        如果今天是新的游戏日（与上次刷新时的 day 不同），则重新生成库存。
        否则返回缓存的库存。
        """
        current_day = game_time['day']
        
        # 如果缓存为空 或 游戏天数已变化 → 重新生成
        if merchant_config._inventory is None or merchant_config._last_refresh_day != current_day:
            merchant_config._inventory = create_merchant_inventory(merchant_config)
            merchant_config._last_refresh_day = current_day
            # 可选：输出调试信息，确认刷新
            # renpy.notify(f"{merchant_config.name} 的库存已刷新（第{current_day}天）")
        
        return merchant_config._inventory
