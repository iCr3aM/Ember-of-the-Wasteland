# =============================================================================
# # 玩家与 NPC 属性、数值
# # 定义：静态生物模板数据库（`CREATURES_DB`，含血量、每回合移动力、挂载的宝藏ID）。 
# # 实现：动态生成玩家（Player）和敌人（NPC/Creature）的动态实例；计算属性修正，处理 AI 战斗意图（战或逃）。
# =============================================================================
init python:
    import random
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
                self.treasure_id = 0
                self.corpse_id = 0
                self.attack_mode_ids = [1,2,4] # 默认攻击模式
                self.morale = 1.0
                self.cigarettes = 0.0
            else:
                cfg = CREATURES_DB[creature_id]
                self.name = cfg["strName"]
                self.max_hp = cfg.get("fMaxHP", 50.0)
                self.hp = self.max_hp  # 直接使用 max_hp，而不是未初始化的 self.hp
                self.treasure_id = cfg["nTreasureID"]
                self.corpse_id = cfg["nCorpseID"]
                self.attack_mode_ids = cfg["vAttackModes"]
                self.morale = 1.0
                self.cigarettes = 0.0
                self.is_human = cfg.get("is_human", False)
                self.escape_rate = cfg.get("escape_rate", 0.0)
                
                # 敌人随机初始疲劳值
                fatigue_on_spawn = cfg.get("fFatigueOnSpawn", None)
                if fatigue_on_spawn is not None:
                    self.fatigue = float(fatigue_on_spawn)
                else:
                    self.fatigue = random.uniform(0, 30)
            
            # 生物基础内呼吸三维
            self.hunger = 0.0   # 0-100, 100为极限饿死
            self.thirst = 0.0   # 0-100, 100为极限渴死
            self.fatigue = 0.0  # 0-100, 100为极度疲劳
            self.b_dead = False
            self.skills = []    # 静态持有的特长/技能ID列表
            self.active_conditions = [] # 动态 ActiveCondition 挂载实例列表

            if not is_player:
                update_fatigue_condition(self)

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
        
        def remove_condition(self, condition_id):
            """移除指定的状态"""
            self.active_conditions = [ac for ac in self.active_conditions if ac.id != condition_id]

    CREATURES_DB[1] = {
        "strName": "野狗",
        "fMaxHP": 30.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 102],  # 撕咬、爪击
        "is_human": False,
        "escape_rate": 0.2
    }
    CREATURES_DB[2] = {
        "strName": "流浪者",
        "fMaxHP": 50.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [1, 2],  # 徒手、钝器重击
        "is_human": True,
        "escape_rate": 0.6,
    }
    CREATURES_DB[3] = {
        "strName": "普通枯萎兽",
        "fMaxHP": 35.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101],  # 撕咬
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[4] = {
        "strName": "巨大枯萎兽",
        "fMaxHP": 110.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 102, 103],  # 撕咬、爪击、冲撞
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[5] = {
        "strName": "肿胀兽",
        "fMaxHP": 40.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 103, 108],  # 撕咬、冲撞、自爆
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[6] = {
        "strName": "幼芽寄生体",
        "fMaxHP": 25.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [106],  # 藤蔓抽打
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[7] = {
        "strName": "辐射蟑螂",
        "fMaxHP": 20.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [101, 104],  # 撕咬、酸液喷射
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[8] = {
        "strName": "变异吸血虫",
        "fMaxHP": 25.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [105],  # 毒刺穿刺
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[9] = {
        "strName": "普通掠夺者",
        "fMaxHP": 80.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [1, 2, 3, 5],  # 徒手、钝器重击、砍刀、手枪
        "is_human": True,
        "escape_rate": 0.3,
    }
    CREATURES_DB[10] = {
        "strName": "疯狂掠夺者",
        "fMaxHP": 50.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [1, 2, 3, 108, 109],  # 徒手、钝器、砍刀、自爆、燃烧瓶
        "is_human": True,
        "escape_rate": 0.1,
    }
    CREATURES_DB[11] = {
        "strName": "军械残兵",
        "fMaxHP": 70.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [6, 199, 110],  # 步枪、压制射击、破片手雷
        "is_human": True,
        "escape_rate": 0.1,
    }