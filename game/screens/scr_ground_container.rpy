# =============================================================================
# scr_ground_container.rpy — 兼容壳
# 功能：将旧地面容器入口转发到新的统一背包界面
# =============================================================================

screen scr_ground_container(container, player_inv):
    use scr_unified_inventory(
        equipment_slots=player_inv.slots,
        player_inv=player_inv,
        secondary_inv=container,
        screen_title="背包 / 地面",
        secondary_title="地面",
        mode="ground",
        close_mode="hide",
        close_screen_name="scr_ground_container"
    )
