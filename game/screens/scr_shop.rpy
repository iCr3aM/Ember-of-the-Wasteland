# =============================================================================
# scr_shop.rpy — 兼容壳
# 功能：将旧交易入口转发到新的统一背包界面
# =============================================================================

screen scr_shop(player_inv, merchant_inv, shop_type="wasteland_trader", barter_rate=1.0, merchant_avatar=None, merchant_name="流浪商人", merchant_description=""):
    use scr_unified_inventory(
        equipment_slots=player_inv.slots,
        player_inv=player_inv,
        secondary_inv=merchant_inv,
        screen_title="背包 / 交易",
        secondary_title="商人货架",
        mode="shop",
        close_mode="return",
        merchant_name=merchant_name,
        merchant_avatar=merchant_avatar,
        merchant_description=merchant_description,
        shop_type=shop_type,
        barter_rate=barter_rate
    )
