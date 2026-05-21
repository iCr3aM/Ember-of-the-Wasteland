# 1. 使用 init offset 统一将当前文件的初始化阶段大幅提前
# 确保所有静态字典在游戏启动的第一时间被注册，防止其他系统调用时报 Key 错误
# =============================================================================
# # 初始化各系统实例（如 inventory = Inventory()）
# # 定义：全局动态运行时实例的集中声明（如 inventory、player_stats、active_quests）。
# # 实现：游戏存档/读档（Save/Load）时的序列化安全保障。作为中央注册表，提供跨文件的数据互调中间件。
# =============================================================================
init -100:
    
    # 1. 初始化所有静态数据库注册表
    define ITEMS_DB = {}
    define CONDITIONS_DB = {}
    define ATTACK_MODES_DB = {}
    define BATTLE_MOVES_DB = {}
    define CREATURES_DB = {}
    define TREASURE_DB = {}
    define MAPS_DB = {}
    define EVENTS_DB = {}
    define QUESTS_DB = {}

# 2. 声明动态运行时全局单例实例（纳入 Ren'Py 存档系统）
default player_stats = None
default player_inventory = None
default active_quests = []
default current_map_id = 1
default player_hex_x = 0
default player_hex_y = 0
default game_time = {"month": 1, "day": 1, "hour": 10}
default last_map_event_code = None
# 调试模式开关
default god_mode = False
default disable_encounters = False
default _pending_inventory_removals = []

# 3. 纯 Python 逻辑中枢方法区
init python:
    def get_item_icon_path(item_id):
        # 使用颜色占位符代替实际图标资源
        return Solid("#777777")

    def get_actor_avatar_path(actor_id):
        # 使用颜色占位符代替实际头像资源
        return Solid("#555555")

    def initialize_game_systems():
        global player_stats, player_inventory, active_quests
        if player_stats is None:
            player_stats = ActorInstance(creature_id=0, is_player=True)

        if player_inventory is None:
            player_inventory = Inventory()

        active_quests = []

        player_stats.hunger = 0.0
        player_stats.thirst = 0.0
        player_stats.fatigue = 0.0
        player_stats.b_dead = False
        player_stats.hp = player_stats.max_hp
        player_stats.active_conditions = []