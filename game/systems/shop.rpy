# =============================================================================
# 商城/交易系统后台逻辑（价格计算、货币扣除）
# 定义：黑市、废土商人、NPC 交易的静态公式。
# 实现：计算物品的最终成交价；执行货币（香烟）扣除逻辑。
# =============================================================================
init python:
    # 商店类型常量
    SHOP_TYPE_BLACK_MARKET = "black_market"      # 黑市：高卖低买
    SHOP_TYPE_WASTELAND_TRADER = "wasteland_trader"  # 废土商人：中等汇率
    SHOP_TYPE_NPC = "npc"                        # NPC：平价交易
    
    # 价格倍率映射 [买入倍率, 卖出倍率]
    SHOP_PRICE_MODIFIERS = {
        SHOP_TYPE_BLACK_MARKET: {"buy_multiplier": 2.0, "sell_multiplier": 0.5},
        SHOP_TYPE_WASTELAND_TRADER: {"buy_multiplier": 1.5, "sell_multiplier": 0.6},
        SHOP_TYPE_NPC: {"buy_multiplier": 1.2, "sell_multiplier": 0.8},
    }
    # 临时变量，用于传递当前交易商人配置给独立标签
    _current_trade_trader_config = None

    # 商人配置数据结构
    class MerchantConfig:
        def __init__(self, merchant_id, name, shop_type, avatar_path=None, 
                    description="", region=None, items_pool=None):
            self.merchant_id = merchant_id
            self.name = name
            self.shop_type = shop_type
            self.avatar_path = avatar_path
            self.description = description
            self.region = region
            self.items_pool = items_pool or []
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
            
        return round(price, 1)  # 保留1位小数
    
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
    
    def shop_execute_purchase(player_inv, merchant_inv, item_instance, shop_type=SHOP_TYPE_WASTELAND_TRADER, barter_rate=1.0):
        """
        执行一次购买交易：玩家从商人处买入物品。
        
        流程:
            1. 计算价格
            2. 检查玩家香烟是否足够
            3. 扣除香烟
            4. 从商人背包移除物品
            5. 添加到玩家背包
        """
        global player_stats
        
        price = get_shop_price(item_instance, shop_type, buy=True, barter_rate=barter_rate)
        
        if not shop_can_afford(player_stats, price):
            renpy.notify(f"香烟不足！需要 {price} 支，当前只有 {player_stats.cigarettes:.0f} 支。")
            return False
        
        shop_apply_payment(player_stats, price)
        merchant_inv.remove_item(item_instance)
        player_inv.add_item(item_instance)
        renpy.notify(f"购入 {item_instance.config.name}，花费 {price:.0f} 支香烟。")
        renpy.restart_interaction()  
        return True
    
    def shop_execute_sell(player_inv, merchant_inv, item_instance, shop_type=SHOP_TYPE_WASTELAND_TRADER, barter_rate=1.0):
        """
        执行一次卖出交易：玩家将物品卖给商人。
        
        流程:
            1. 计算价格
            2. 从玩家背包移除物品
            3. 添加到商人背包
            4. 支付香烟给玩家
        """
        global player_stats
        
        price = get_shop_price(item_instance, shop_type, buy=False, barter_rate=barter_rate)
        
        player_inv.remove_item(item_instance)
        merchant_inv.add_item(item_instance)
        shop_apply_income(player_stats, price)
        renpy.notify(f"卖出 {item_instance.config.name}，获得 {price:.0f} 支香烟。")
        renpy.restart_interaction()  
        return True

        # 不同地区的商人定义
    MERCHANT_WASTELAND_TRADER = MerchantConfig(
        merchant_id="wasteland_trader_01",
        name="流动商人",
        shop_type=SHOP_TYPE_WASTELAND_TRADER,
        avatar_path="images/merchant_wasteland.png",
        description="一个风尘仆仆的废土商人，他的骆驼背上驮着满满的货箱。",
        region="wasteland",
        items_pool=[101, 102, 201, 104, 105]
    )

    MERCHANT_CITY_TRADER = MerchantConfig(
        merchant_id="city_trader_01",
        name="城市商人",
        shop_type=SHOP_TYPE_NPC,
        avatar_path="images/merchant_city.png",
        description="一个精明的城市商人，他的店铺里摆满了各种废土上的稀缺物资。",
        region="city",
        items_pool=[103, 112, 113, 114, 201]
    )

    MERCHANT_BLACK_MARKET = MerchantConfig(
        merchant_id="black_market_01",
        name="地下黑市商人",
        shop_type=SHOP_TYPE_BLACK_MARKET,
        avatar_path="images/merchant_blackmarket.png",
        description="一个躲在阴影中的神秘人物，他的货物来源不明但品质上乘。",
        region="city_underground",
        items_pool=[101, 109, 110, 111, 103]
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
        """根据商人配置创建其物品库存"""
        inv = Inventory()
        if merchant_config.items_pool:
            import random
            for item_id in merchant_config.items_pool:
                if random.random() < 0.7:  # 70%概率携带
                    inv.add_item_by_id(item_id)
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