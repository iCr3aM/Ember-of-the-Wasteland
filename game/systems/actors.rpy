# =============================================================================
# actors.rpy — 玩家与 NPC 属性、数值
# 功能：定义生物模板数据库（CREATURES_DB）与动态角色实例（ActorInstance）
# 职责：管理角色属性初始化、状态挂载/移除、攻击/战术动作获取、属性修正计算
# =============================================================================
# ── 动态角色实例类 ──
init python:
    import random

    # ── NPC 词条稀有度权重表（类似 LOOT_RARITY） ──
    TRAIT_RARITY = {
        "trash":       {"weight": 30, "traits": [TRAIT_WEAK, TRAIT_FRAIL, TRAIT_SLUGGISH, TRAIT_DECAYING]},
        "common":      {"weight": 20, "traits": [TRAIT_FOCUSED, TRAIT_DROUGHT_RESISTANT, TRAIT_ENERGETIC]},
        "rare":        {"weight": 10, "traits": [TRAIT_TOUGH, TRAIT_FEROCIOUS]},
        "precious":    {"weight": 5,  "traits": []},
        "easter_egg":  {"weight": 1,  "traits": [TRAIT_EASTER_EGG]},
    }

    def roll_npc_trait():
        """基于稀有度权重抽取 NPC 词条，返回 trait_id 或 None"""
        candidates = {}  # trait_id -> weight
        
        # 无词条：基础权重 100，始终参与
        none_weight = 100
        
        # 收集所有词条及其权重
        for rarity, data in TRAIT_RARITY.items():
            for trait_id in data["traits"]:
                candidates[trait_id] = data["weight"]
        
        # 计算总权重（含无词条）
        total = none_weight + sum(candidates.values())
        roll = random.random() * total
        
        # 先判断是否无词条
        if roll < none_weight:
            return None
        
        # 在词条中按权重抽取
        cumulative = none_weight
        for trait_id, weight in candidates.items():
            cumulative += weight
            if roll <= cumulative:
                return trait_id
        
        return None

    class ActorInstance:
        """动态角色运行时实例：连接属性、状态、攻击模式与掉落"""
        def __init__(self, creature_id, is_player=False):
            self.id = creature_id
            self.is_player = is_player
            
            # 玩家初始化为白板属性，NPC 从数据库拉取
            if is_player:
                self.name = "你"
                self.max_hp = 100.0
                self.hp = 100.0
                self.treasure_id = 0
                self.corpse_id = 0
                self.attack_mode_ids = [1, 4]  # 默认攻击模式：徒手、投掷
                self.morale = 1.0
                self.cigarettes = 0
                self.trait_id = None
            else:
                cfg = CREATURES_DB[creature_id]
                self.name = cfg["strName"]
                self.max_hp = cfg.get("fMaxHP", 50.0)
                self.hp = self.max_hp  # 满血生成
                self.treasure_id = cfg["nTreasureID"]
                self.corpse_id = cfg["nCorpseID"]
                self.attack_mode_ids = cfg["vAttackModes"]
                self.morale = 1.0
                self.cigarettes = 0
                self.is_human = cfg.get("is_human", False)
                self.escape_rate = cfg.get("escape_rate", 0.0)
                
                # 敌人初始疲劳值（配置指定或随机 0~30）
                fatigue_on_spawn = cfg.get("fFatigueOnSpawn", None)
                if fatigue_on_spawn is not None:
                    self.fatigue = float(int(fatigue_on_spawn))
                else:
                    self.fatigue = random.randint(0, 30)
            
            # 基础代谢三维初始化
            self.hunger = random.randint(10, 30) if not is_player else 0.0
            self.thirst = random.randint(10, 30) if not is_player else 0.0
            self.b_dead = False
            self.skills = []              # 静态持有的特长/技能 ID 列表
            self.active_conditions = []   # 动态状态实例列表

            # ── NPC 词条抽取（仅 NPC，玩家不抽取） ──
            if not is_player:
                self.trait_id = roll_npc_trait()
                if self.trait_id is not None:
                    self.add_condition(self.trait_id)
                    # 从状态修饰符中读取 HP 倍率并应用
                    trait_config = CONDITIONS_DB[self.trait_id]
                    if "fMaxHpMultiplier" in trait_config.modifiers:
                        hp_mult = 1.0 + trait_config.modifiers["fMaxHpMultiplier"]
                        self.max_hp *= hp_mult
                        self.hp = self.max_hp

            if not is_player:
                update_fatigue_condition(self)

        @property
        def avatar(self):
            """返回角色头像路径，由全局工具函数动态解析"""
            return get_actor_avatar_path(self.id)

        def get_modifier_multiplier(self, modifier_key):
            """计算当前挂载的所有状态对某项属性的倍率累加"""
            multiplier = 1.0
            for ac in self.active_conditions:
                if modifier_key in ac.config.modifiers:
                    multiplier += ac.config.modifiers[modifier_key]
            return max(0.0, multiplier)

        def get_available_attack_modes(self, current_range=None):
            modes = [ATTACK_MODES_DB[am_id] for am_id in self.attack_mode_ids if am_id in ATTACK_MODES_DB]
            # 骨折状态下只能使用徒手攻击（ID 1）
            if any(ac.id == COND_FRACTURE for ac in self.active_conditions):
                modes = [am for am in modes if am.id == 1]
            if current_range is None:
                return modes
            return [am for am in modes if am.min_range <= current_range <= am.max_range]

        def get_available_battle_moves(self, target, current_range):
            """获取战斗中所有合法战术动作"""
            return [bm for bm in BATTLE_MOVES_DB.values() if bm.is_usable(self, target, current_range)]

        def add_condition(self, condition_id):
            """挂载状态实例（不可堆叠状态去重，玩家首次获得写入日志）"""
            if condition_id in CONDITIONS_DB:
                # 不可堆叠状态 → 已存在则跳过
                if not CONDITIONS_DB[condition_id].b_stackable:
                    for ac in self.active_conditions:
                        if ac.id == condition_id: return
                self.active_conditions.append(ActiveCondition(condition_id))
                # 玩家首次获得该状态时写入冒险日志
                if self.is_player:
                    if not hasattr(self, '_logged_conditions'):
                        self._logged_conditions = set()
                    if condition_id not in self._logged_conditions:
                        self._logged_conditions.add(condition_id)
                        try:
                            adventure_log.append(f"你获得了状态：{CONDITIONS_DB[condition_id].name}")
                        except NameError:
                            pass
        
        def remove_condition(self, condition_id):
            """移除指定状态，同时清除日志记录以便将来可重新记录"""
            self.active_conditions = [ac for ac in self.active_conditions if ac.id != condition_id]
            # 清除日志记录，允许将来重新获得时再次写入
            if self.is_player and hasattr(self, '_logged_conditions'):
                self._logged_conditions.discard(condition_id)

    # ── 生物模板数据库 ──
    CREATURES_DB[1] = {
        "strName": "野狗",
        "fMaxHP": 30.0,
        "nTreasureID": 3002,
        "nCorpseID": 0,
        "vAttackModes": [101, 102],  # 撕咬、爪击
        "is_human": False,
        "escape_rate": 0.2
    }
    CREATURES_DB[2] = {
        "strName": "流浪者",
        "fMaxHP": 50.0,
        "nTreasureID": 3004,
        "nCorpseID": 0,
        "vAttackModes": [1, 4],  # 徒手攻击、投掷杂物
        "is_human": True,
        "escape_rate": 0.6,
    }
    CREATURES_DB[3] = {
        "strName": "枯萎者",
        "fMaxHP": 35.0,
        "nTreasureID": 3003,
        "nCorpseID": 0,
        "vAttackModes": [101],  # 撕咬
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[4] = {
        "strName": "枯萎兽",
        "fMaxHP": 90.0,
        "nTreasureID": 3003,
        "nCorpseID": 0,
        "vAttackModes": [101, 102, 103],  # 撕咬、爪击、冲撞
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[5] = {
        "strName": "辐射鼠",
        "fMaxHP": 8.0,
        "nTreasureID": 3001,
        "nCorpseID": 0,
        "vAttackModes": [108],  # 啃咬
        "is_human": False,
        "escape_rate": 0.8,
    }
    CREATURES_DB[6] = {
        "strName": "幼芽寄生体",
        "fMaxHP": 25.0,
        "nTreasureID": 3003,
        "nCorpseID": 0,
        "vAttackModes": [106],  # 藤蔓抽打
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[7] = {
        "strName": "辐射蟑螂",
        "fMaxHP": 20.0,
        "nTreasureID": 3002,
        "nCorpseID": 0,
        "vAttackModes": [101, 104],  # 撕咬、酸液喷射
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[8] = {
        "strName": "变异吸血虫",
        "fMaxHP": 25.0,
        "nTreasureID": 3002,
        "nCorpseID": 0,
        "vAttackModes": [105],  # 毒刺穿刺
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[9] = {
        "strName": "掠夺者",
        "fMaxHP": 80.0,
        "nTreasureID": 0,
        "nCorpseID": 0,
        "vAttackModes": [1, 2, 5],  # 徒手、钝器重击、手枪
        "is_human": True,
        "escape_rate": 0.3,
    }
    CREATURES_DB[10] = {
        "strName": "变异蜈蚣",
        "fMaxHP": 15.0,
        "nTreasureID": 3002,
        "nCorpseID": 0,
        "vAttackModes": [101, 105],  # 撕咬、毒刺穿刺
        "is_human": False,
        "escape_rate": 0.3,
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
    CREATURES_DB[12] = {
        "strName": "蝎尾蝇",
        "fMaxHP": 35.0,
        "nTreasureID": 3002,
        "nCorpseID": 0,
        "vAttackModes": [105, 111],  # 毒刺穿刺、甩尾
        "is_human": False,
        "escape_rate": 0.0,
    }
    CREATURES_DB[13] = {
        "strName": "拾荒帮众",
        "fMaxHP": 45.0,
        "nTreasureID": 3004,
        "nCorpseID": 0,
        "vAttackModes": [1, 3],  # 徒手、砍刀挥砍
        "is_human": True,
        "escape_rate": 0.5,
    }