# =============================================================================
# # 攻击方式
# # 定义：攻击/战斗行为数据库（`ATTACK_MODES_DB`，如撕咬、射击、冲锋、绊倒，伤害、附带状态ID）。 
# # 实现：根据当前武器状态或生物类型，动态把可用攻击方式喂给战斗系统，并计算攻击造成的伤口转化。
# =============================================================================
init -190 python:
    
    ATTACK_MODES_DB = {}

    WEAPON_TYPE_RULES = [
        ((1, 2, 3, 9, 10, 11, 12),          "melee"),
        ((4, 8, 104, 105, 107, 109, 110),   "throw"),
        ((5,),                              "pistol"),
        ((6, 199),                          "rifle"),
        ((101, 102, 103, 106, 108, 111),    "natural"),
    ]

    class AttackMode:
        """对应 attackmodes.xml 结构"""
        def __init__(self, id, name, desc, range, damage, hunger_cost=0, thirst_cost=0, fatigue_cost=0,attacker_conditions=None, condition_chance=0.5):
            self.id = id
            self.name = name
            self.desc = desc
            self.range = range
            self.damage = damage
            self.hunger_cost = hunger_cost
            self.thirst_cost = thirst_cost
            self.fatigue_cost = fatigue_cost
            self.attacker_conditions = attacker_conditions or [] # 击中后附带给受击者的状态ID列表
            self.condition_chance = condition_chance  # 附加状态触发概率

# ========================玩家与NPC通用=========================
    ATTACK_MODES_DB[1] = AttackMode(1, "徒手攻击", "用拳头和肘部近身搏击。最基础的攻击手段。", 2, 12.0,hunger_cost=2, thirst_cost=3, fatigue_cost=4, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[2] = AttackMode(2, "强力重击", "蓄满力气，用钝器砸向对手。伤害高，但消耗也大。", 3, 32.0,hunger_cost=5, thirst_cost=5, fatigue_cost=8, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[3] = AttackMode(3, "砍刀挥砍", "握紧你的刀，斜劈而下。废土上最可靠的近战手段。", 4, 24.0,hunger_cost=3, thirst_cost=4, fatigue_cost=6, attacker_conditions=[COND_BLEED], condition_chance=0.4)
    ATTACK_MODES_DB[4] = AttackMode(4, "投掷杂物", "捡起手边的碎石或废铁，用力砸向对方。", 10, 10.0,hunger_cost=1, thirst_cost=1, fatigue_cost=3, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[5] = AttackMode(5, "手枪射击", "举枪瞄准，扣下扳机。中距离的可靠伙伴。", 16, 20.0,hunger_cost=3, thirst_cost=4, fatigue_cost=5, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[6] = AttackMode(6, "步枪射击", "屏住呼吸，准星套住目标。远距离的致命一击。", 20, 38.0,hunger_cost=4, thirst_cost=5, fatigue_cost=7, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[7] = AttackMode(7, "匕首捅刺", "刀刃太短，挥砍不如捅刺。适合快速、低消耗的近身攻击。", 2, 18.0, hunger_cost=2, thirst_cost=2, fatigue_cost=3, attacker_conditions=[COND_BLEED], condition_chance=0.6)
    ATTACK_MODES_DB[8] = AttackMode(8, "碎石投掷", "捡起混凝土块用力掷出。", 8, 12.0, hunger_cost=1, thirst_cost=1, fatigue_cost=2, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[9] = AttackMode(9, "指虎连击", "套上金属指虎，快速连续出拳。轻便、隐蔽、致命。", 1, 15.0, hunger_cost=1, thirst_cost=1, fatigue_cost=2, attacker_conditions=[COND_STAGGER], condition_chance=0.3)
    ATTACK_MODES_DB[10] = AttackMode(10, "钢管挥击", "抡起镀锌钢管，全力横扫。势大力沉，中者筋骨欲裂。", 3, 28.0, hunger_cost=3, thirst_cost=3, fatigue_cost=5, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[11] = AttackMode(11, "棒球棍猛击", "双手握紧棒球棍，像打本垒打一样全力挥出。", 3, 26.0, hunger_cost=3, thirst_cost=3, fatigue_cost=5, attacker_conditions=[COND_STAGGER], condition_chance=0.4)
    ATTACK_MODES_DB[12] = AttackMode(12, "撬棍猛击", "用撬棍的弯头狠狠砸下，既能破门也能破颅。", 3, 25.0, hunger_cost=3, thirst_cost=4, fatigue_cost=5, attacker_conditions=[COND_BLEED], condition_chance=0.3)

# ========================NPC专属============================
    ATTACK_MODES_DB[101] = AttackMode(101, "撕咬", "用残缺的牙齿狠狠咬向猎物的皮肉。", 2, 8.0,hunger_cost=1, thirst_cost=2, fatigue_cost=3, attacker_conditions=[COND_BLEED], condition_chance=0.4)
    ATTACK_MODES_DB[102] = AttackMode(102, "爪击", "挥舞尖锐的利爪撕裂对手。", 3, 18.0,hunger_cost=2, thirst_cost=3, fatigue_cost=4, attacker_conditions=[COND_BLEED], condition_chance=0.4)
    ATTACK_MODES_DB[103] = AttackMode(103, "冲撞", "低下肩膀全力冲刺，将对手撞翻在地。", 4, 22.0,hunger_cost=3, thirst_cost=4, fatigue_cost=5, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[104] = AttackMode(104, "酸液喷射", "从腹腔喷出一股腐蚀性酸液，灼烧沿途的一切。", 8, 12.0,hunger_cost=2, thirst_cost=3, fatigue_cost=4, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[105] = AttackMode(105, "毒刺穿刺", "尾部的毒刺如针管般刺出，注入麻痹毒素。", 6, 8.0,hunger_cost=1, thirst_cost=2, fatigue_cost=3, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[106] = AttackMode(106, "藤蔓抽打", "寄生在骨骼上的藤蔓猛然甩出，鞭笞靠近的活物。", 6, 10.0,hunger_cost=2, thirst_cost=3, fatigue_cost=4, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[107] = AttackMode(107, "蛛网喷射", "喷出一张粘稠的蛛网，束缚猎物的行动。", 8, 5.0,hunger_cost=1, thirst_cost=2, fatigue_cost=3, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[108] = AttackMode(108, "啃咬（小型）", "细小的牙齿快速啃噬。", 1, 3.0, hunger_cost=1, thirst_cost=1, fatigue_cost=1, attacker_conditions=[COND_BLEED], condition_chance=0.3)
    ATTACK_MODES_DB[109] = AttackMode(109, "燃烧瓶", "点燃布条，将自制的玻璃瓶燃烧弹掷向目标。", 12, 22.0,hunger_cost=3, thirst_cost=4, fatigue_cost=5, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[110] = AttackMode(110, "破片手雷", "拔掉保险，将手雷投向掩体后的敌人。", 15, 25.0,hunger_cost=4, thirst_cost=5, fatigue_cost=7, attacker_conditions=[], condition_chance=0)
    ATTACK_MODES_DB[111] = AttackMode(111, "甩尾", "用粗壮的尾巴横扫对手下盘。", 4, 14.0, hunger_cost=2, thirst_cost=2, fatigue_cost=3, attacker_conditions=[COND_STAGGER], condition_chance=0.5)
    ATTACK_MODES_DB[199] = AttackMode(199, "压制射击", "连续扣动扳机，用弹雨封锁敌人的移动路线。", 20, 30.0,hunger_cost=4, thirst_cost=5, fatigue_cost=7, attacker_conditions=[], condition_chance=0)
    