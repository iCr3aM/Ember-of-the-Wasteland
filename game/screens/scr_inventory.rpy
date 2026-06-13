# =============================================================================
# scr_inventory.rpy — 兼容壳
# 功能：将旧背包入口转发到新的统一背包界面
# =============================================================================

screen scr_inventory(inv_instance=player_inventory):
    use scr_unified_inventory(
        equipment_slots=inv_instance.slots,
        player_inv=inv_instance,
        secondary_inv=get_current_ground_container() if get_current_ground_container() is not None else Inventory(max_slots=0),
        screen_title="背包 / 地面",
        secondary_title="地面",
        mode="ground",
        close_mode="hide",
        close_screen_name="scr_inventory"
    )
