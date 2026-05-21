# =============================================================================
# # 攻击方式
# # 定义：攻击/战斗行为数据库（`ATTACK_MODES_DB`，如撕咬、射击、冲锋、绊倒，含射程、钝击/斩击伤害、附带状态ID）。 
# # 实现：根据当前武器状态或生物类型，动态把可用攻击方式喂给战斗系统，并计算攻击造成的伤口转化。
# =============================================================================
init python:
    class AttackMode:
        """对应 attackmodes.xml 结构"""
        def __init__(self, id, name, range, damage, attacker_conditions=None):
            self.id = id
            self.name = name
            self.range = range
            self.damage = damage
            self.attacker_conditions = attacker_conditions or [] # 击中后附带给受击者的状态ID列表

# ========================玩家与NPC通用=========================
    ATTACK_MODES_DB[1] = AttackMode(1, "徒手攻击", 2, 20.0)
    ATTACK_MODES_DB[2] = AttackMode(2, "强力重击", 4, 45.0)
    ATTACK_MODES_DB[3] = AttackMode(3, "砍刀挥砍", 4, 35.0)
    ATTACK_MODES_DB[4] = AttackMode(4, "投掷杂物", 16, 17.5)
    ATTACK_MODES_DB[5] = AttackMode(5, "手枪射击", 16, 30.0)
    ATTACK_MODES_DB[6] = AttackMode(6, "步枪射击", 16, 52.5)

# ========================NPC专属============================
    ATTACK_MODES_DB[101] = AttackMode(101, "撕咬", 2, 10.0)
    ATTACK_MODES_DB[102] = AttackMode(102, "爪击", 2, 27.5)
    ATTACK_MODES_DB[103] = AttackMode(103, "冲撞", 4, 35.0)
    ATTACK_MODES_DB[104] = AttackMode(104, "酸液喷射", 8, 15.0)
    ATTACK_MODES_DB[105] = AttackMode(105, "毒刺穿刺", 8, 10.0)
    ATTACK_MODES_DB[106] = AttackMode(106, "藤蔓抽打", 12, 15.0)
    ATTACK_MODES_DB[107] = AttackMode(107, "蛛网喷射", 10, 12.5)
    ATTACK_MODES_DB[108] = AttackMode(108, "自爆", 1, 20.0)
    ATTACK_MODES_DB[109] = AttackMode(109, "燃烧瓶", 16, 30.0)
    ATTACK_MODES_DB[110] = AttackMode(110, "破片手雷", 16, 30.0)
    ATTACK_MODES_DB[199] = AttackMode(199, "压制射击", 16, 45.0)