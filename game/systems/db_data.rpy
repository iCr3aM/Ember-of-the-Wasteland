# =============================================================================
# db_data.rpy — 全局数据注册表与运行时实例声明
# 功能：集中声明所有静态数据库字典及动态运行时全局单例实例
# 职责：作为中央注册表，提供跨文件的数据互调中间件，确保存档/读档序列化安全
# =============================================================================
# ── 静态数据库注册表（init -100 确保最早加载） ──
init -100 python:
    
    # 初始化所有静态数据库注册表
    ITEMS_DB = {}
    CONDITIONS_DB = {}
    BATTLE_MOVES_DB = {}
    CREATURES_DB = {}
    TREASURE_DB = {}
    MAPS_DB = {}
    EVENTS_DB = {}
    QUESTS_DB = {}

# ── 动态运行时全局单例实例（纳入 Ren'Py 存档系统） ──
default player_stats = None
default player_inventory = None
default active_quests = []
default current_map_id = 1
default player_hex_x = 0
default player_hex_y = 0
default game_time = {"month": 1, "day": 1, "hour": 10, "minute": 0}
default last_map_event_code = None
default adventure_log = []                 # 冒险日志
default god_mode = False                   # 调试：上帝模式
default disable_encounters = False         # 调试：禁用遭遇战
default _pending_inventory_removals = []   # 待处理的背包移除队列
default cigarettes_smoked = 0            # 累计吸烟支数
default last_cigarette_hour = -1         # 上次吸烟的游戏小时数（-1 表示从未吸烟）
default last_cigarette_day = -1 
default _last_explore_music_hour = -1
default _last_explore_music_day = -1
default steps_taken = 0                # 累计移动格数
default enemies_killed = 0             # 累计击杀敌人数
default times_camped = 0               # 累计扎营次数
default total_damage_taken = 0         # 累计承受伤害

# ── 工具函数：图标/头像路径解析 ──
init python:
    def get_item_icon_path(item_id):
        """根据物品ID返回图标路径，如果实际图像文件存在则返回路径字符串，否则返回显示物品名称和ID的文本显示对象。"""
        path = f"images/items_icon/icon_{item_id}.png"
        if renpy.loadable(path):
            return path
        # 图标缺失时，返回文本显示对象（名称 + ID）
        config = ITEMS_DB.get(item_id)
        display_name = config.name if config else f"未知(ID:{item_id})"
        return Fixed(
            Text(
                f"ID:{item_id}\n{display_name}",
                size=18,
                color="#888888",
                text_align=0.5,
                xalign=0.5,
                yalign=0.5,
                outlines=[(1, "#000000")]
            ),
            xysize=(80, 80)
        )

    def get_actor_avatar_path(actor_id):
        """根据角色ID返回头像路径，如果实际图像文件存在则返回路径字符串，否则返回颜色占位符。"""
        path = "images/avatar/avatar_player.png" if actor_id == 0 else f"images/avatar/avatar_enemy_{actor_id}.png"
        if renpy.loadable(path):
            return path
        return Solid("#555555")
    
# ── 游戏系统初始化 ──
init python:
    BIRTH_ZONE = [(40, 20), (40, 21), (41, 20), (41, 21)]

    def initialize_game_systems():
        global player_stats, player_inventory, active_quests, player_hex_x, player_hex_y
        
        # 只在第一次初始化时随机出生点
        if player_stats is None:
            player_stats = ActorInstance(creature_id=0, is_player=True)
            player_hex_x, player_hex_y = renpy.random.choice(BIRTH_ZONE)

        if player_inventory is None:
            player_inventory = Inventory()

        active_quests = []

        player_stats.hunger = 0.0
        player_stats.thirst = 0.0
        player_stats.fatigue = 0.0
        player_stats.b_dead = False
        player_stats.hp = player_stats.max_hp
        player_stats.active_conditions = []
