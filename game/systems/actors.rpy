# =============================================================================
# # 玩家与 NPC 属性、数值
# # 定义：静态生物模板数据库（`CREATURES_DB`，含血量、每回合移动力、挂载的宝藏ID）。 
# # 实现：动态生成玩家（Player）和敌人（NPC/Creature）的动态实例；计算属性修正，处理 AI 战斗意图（战或逃）。
# =============================================================================
init python:
    class ActorInstance:
        """动态生物/NPC/玩家运行时类，彻底连接属性、状态、攻击与掉落"""
        def __init__(self, creature_id, is_player=False):
            self.id = creature_id
            self.is_player = is_player
            
            # 若是玩家，初始化默认白板属性；若是NPC则拉取数据
            if is_player:
                self.name = "拾荒者"
                self.max_hp = 100.0
                self.hp = 100.0
                self.moves_per_turn = 4
                self.treasure_id = 0
                self.corpse_id = 0
                self.attack_mode_ids = [1, 4] # 默认攻击模式
                self.morale = 1.0
                self.cigarettes = 0.0
            else:
                cfg = CREATURES_DB[creature_id]
                self.name = cfg["strName"]
                self.max_hp = cfg.get("fMaxHP", 50.0)
                self.hp = self.max_hp  # 修复：直接使用 max_hp，而不是未初始化的 self.hp
                self.moves_per_turn = cfg["nMovesPerTurn"]
                self.treasure_id = cfg["nTreasureID"]
                self.corpse_id = cfg["nCorpseID"]
                self.attack_mode_ids = cfg["vAttackModes"]
                self.morale = 1.0
                self.cigarettes = 0.0
            
            # 生物基础内呼吸三维
            self.hunger = 0.0   # 0-100, 100为极限饿死
            self.thirst = 0.0   # 0-100, 100为极限渴死
            self.fatigue = 0.0  # 0-100, 100为极度疲劳
            self.b_dead = False
            self.skills = []    # 静态持有的特长/技能ID列表
            self.active_conditions = [] # 动态 ActiveCondition 挂载实例列表
            
        def get_actor_avatar_path(creature_id):
            """
            根据生物 ID 返回头像图片路径。
            玩家 ID 为 0，敌人从 1 开始编号。
            """
            if creature_id == 0:  # 玩家
                return "images/avatar_player.png"
            else:
                return f"images/avatar_creature_{creature_id}.png"
        
        # 备用：如果图片不存在，返回默认占位
        def get_actor_avatar_path_safe(creature_id):
            """带默认降级的头像路径获取函数"""
            import os
            path = get_actor_avatar_path(creature_id)
            if os.path.exists(path):
                return path
            return "images/avatar_default.png"    

        @property
        def avatar(self):
            # 完全与静态图像解耦，运行时基于 ID 映射路径
            return get_actor_avatar_path(self.id)

        def get_modifier_multiplier(self, modifier_key):
            """计算当前挂载的所有状态对某项属性的倍率累加"""
            multiplier = 1.0
            for ac in self.active_conditions:
                if modifier_key in ac.config.modifiers:
                    multiplier += ac.config.modifiers[modifier_key]
            return max(0.0, multiplier)

        def get_available_attack_modes(self, current_range=None):
            """返回所有攻击模式（不根据距离过滤）"""
            modes = [ATTACK_MODES_DB[am_id] for am_id in self.attack_mode_ids if am_id in ATTACK_MODES_DB]
            if current_range is None:
                return modes
            # 修复：武器射程必须大于或等于当前距离才能攻击
            return [am for am in modes if am.range >= current_range]

        def get_available_battle_moves(self, target, current_range):
            """获取战斗中所有合法战术动作"""
            return [bm for bm in BATTLE_MOVES_DB.values() if bm.is_usable(self, target, current_range)]

        def add_condition(self, condition_id):
            """挂载状态与疾病"""
            if condition_id in CONDITIONS_DB:
                # 检查是否可叠加
                if not CONDITIONS_DB[condition_id].b_stackable:
                    for ac in self.active_conditions:
                        if ac.id == condition_id: return
                self.active_conditions.append(ActiveCondition(condition_id))

    CREATURES_DB[1] = {
        "strName": "野狗",
        "fMaxHP": 30.0,
        "nMovesPerTurn": 3,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 102],  # 撕咬、爪击
    }
    CREATURES_DB[2] = {
        "strName": "流浪者",
        "fMaxHP": 50.0,
        "nMovesPerTurn": 4,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [1, 2],  # 徒手、钝器重击
    }
    CREATURES_DB[3] = {
        "strName": "普通枯萎兽",
        "fMaxHP": 30.0,
        "nMovesPerTurn": 2,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101],  # 撕咬
    }
    CREATURES_DB[4] = {
        "strName": "巨大枯萎兽",
        "fMaxHP": 90.0,
        "nMovesPerTurn": 3,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 102, 103],  # 撕咬、爪击、冲撞
    }
    CREATURES_DB[5] = {
        "strName": "肿胀兽",
        "fMaxHP": 40.0,
        "nMovesPerTurn": 2,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 103, 108],  # 撕咬、冲撞、自爆
    }
    CREATURES_DB[6] = {
        "strName": "幼芽寄生体",
        "fMaxHP": 25.0,
        "nMovesPerTurn": 1,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [106],  # 藤蔓抽打
    }
    CREATURES_DB[7] = {
        "strName": "辐射蟑螂",
        "fMaxHP": 20.0,
        "nMovesPerTurn": 2,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 104],  # 撕咬、酸液喷射
    }
    CREATURES_DB[8] = {
        "strName": "变异吸血虫",
        "fMaxHP": 30.0,
        "nMovesPerTurn": 2,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [105],  # 毒刺穿刺
    }
    CREATURES_DB[9] = {
        "strName": "普通掠夺者",
        "fMaxHP": 60.0,
        "nMovesPerTurn": 3,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [1, 2, 3, 5],  # 徒手、钝器重击、砍刀、手枪
    }
    CREATURES_DB[10] = {
        "strName": "疯狂掠夺者",
        "fMaxHP": 50.0,
        "nMovesPerTurn": 4,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [1, 2, 3, 108, 109],  # 徒手、钝器、砍刀、自爆、燃烧瓶
    }
    CREATURES_DB[11] = {
        "strName": "军械残兵",
        "fMaxHP": 80.0,
        "nMovesPerTurn": 4,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [6, 199, 110],  # 步枪、压制射击、破片手雷
    }