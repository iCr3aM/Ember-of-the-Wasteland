# game/systems/utils.rpy
init python:
    def get_actor_avatar_path(actor_id):
        if actor_id == 0:
            return "images/avatar_player.png"
        path = f"images/avatar_enemy_{actor_id}.png"
        return path if renpy.loadable(path) else None

    def clamp_hp(actor, min_hp=0.0):
        """统一处理 HP 下限保护，并返回是否触发死亡"""
        if actor.hp < min_hp:
            actor.hp = min_hp
        return actor.hp <= 0

    def is_in_active_combat():
        """检查当前是否处于活跃战斗中（安全访问全局变量）"""
        try:
            return _current_combat_instance is not None and not _current_combat_instance.is_finished
        except NameError:
            return False

    def is_player_turn_available():
        """检查玩家当前是否可以操作背包/进行行动"""
        if not is_in_active_combat():
            return True
        try:
            return not _current_combat_instance.player_turn_disabled_by_inventory
        except NameError:
            return True