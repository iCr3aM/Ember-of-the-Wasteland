# =============================================================================
# prologue.rpy — 游戏序幕：开场演出与世界观介绍
# 功能：播放开场 CG、介绍枯萎流感与核战背景、移交大地图
# 职责：渲染序幕剧情文本，完成后切入大地图探索循环
# =============================================================================
# ── 序幕背景图声明 ──
image bg lore_blight = "images/lore_blight.png"
image bg lore_war = "images/lore_war.png"
image bg quarantine_room = "images/quarantine_room.png"
image bg blight_radio = "images/blight_radio.png"

label prologue_start:
    # ── 世界观 ──
    scene bg blight_radio with fade

    "起初，人们叫它“枯萎病”。"
    "一种通过空气传播的病原体。潜伏期长，致死率极高，基因组极不稳定——它变异的速度，永远快过疫苗研发的进度。"

    scene bg lore_blight with fade

    "恐慌像第二场瘟疫，从一座城市蔓延到另一座城市。国境线关闭了，航班取消了，港口里停满了锈蚀的货轮——那些曾经连接世界的动脉，一根接一根地凝固、坏死。"
    "超市货架是最先空掉的。接着是医院的床位。接着，是整个人类社会赖以运转的东西：信任。"

    scene bg lore_war with fade

    "当最后一处安全区被标记在地图上——最后一座疫苗工厂、最后一片无土栽培农场、最后一处未受污染的地下水源——残存的秩序崩解了。"
    "没有全面战争。没有宣战声明。只有冷静的、外科手术式的精确打击。几十枚战术核弹头，足够摧毁对方的希望，也足够让放射性同位素飘进全世界的天空。"
    "战争在几周内结束，因为已经没什么值得继续争夺的了。"

    # ── 醒来 ──
    scene bg quarantine_room with fade

    #play sound "audio/"

    "雨水敲打着生锈的铁皮屋顶。"
    "你睁开眼睛，霉烂与消毒剂的气味扑面而来。——气窗漏下的天光照亮满地骸骨，白大褂蜷缩在墙角。直到最后也没等来救援。"
    "这里曾是一间防疫隔离点的地下急救室，一个本该拯救生命的地方。"
    "你撑起上半身，身体只反馈了两件事：剧烈的口渴，喉咙像被砂纸打磨过。"
    "以及，你还活着。"
    
    # ── 移交大地图 ──
    show screen scr_hud

    # 移交控制权至大地图探索循环
    call travel_on_wasteland_loop from _call_travel_on_wasteland_loop