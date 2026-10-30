"""Run story, hunter training and physical inn checkpoints."""
import copy
import feedback
import math
import random
import secrets

SKILLS = {
    "vitality": {"name": "Vitality", "description": "+4% base maximum HP per rank", "maxRank": 3, "bonus": .04},
    "power": {"name": "Power", "description": "+3% base attack damage per rank", "maxRank": 3, "bonus": .03},
    "focus": {"name": "Focus", "description": "+5% mana regeneration per rank", "maxRank": 3, "bonus": .05},
}
PAGES = {
    "wounded": ("Wounded Hunter", [
        "Keep your voices low. The dragon struck our hunting party. I escaped, but these burns will not let me travel farther.",
        "It is still out there, beyond the Gauntlet. Will you find the dragon and finish what we could not?",
        "Then take the hunter's road. Find and kill the dragon. The inns reward hunters who survive the journey."]),
    "welcome": ("Village Runner", [
        "Are you hunters? I saw you coming from the Gauntlet! Our inn rewards those brave enough to face the dragon.",
        "Speak to the innkeeper before leaving. They will teach you hunter training. Beds upstairs let your whole party set a checkpoint."]),
    "training": ("Innkeeper", [
        "Welcome, hunters. Your first visit earns one training point. Defeat each of the first two great bosses to earn another. Each reward can be earned once per run.",
        "Vitality raises your base maximum health by 4% per rank. Power raises base attack damage by 3%. Focus raises mana regeneration by 5%. Each branch has three ranks.",
        "Spend one point for one rank. Talk to an innkeeper to train. Your upgrades stay with you if the Guild changes your class; their percentages use your new hero's base stats.",
        "Training belongs to this run. Go upstairs, find an unlocked guest room, and use its bed to rest and set your party's checkpoint. Some locked rooms are occupied. Talking to me does not save your run."]),
}
PAGES['adventure_caretaker']=('Mara · Cottage recovery',['I can restore your health and mana for 5 shared ordinary Runes. If both are already full, there is no charge. This is treatment, not an inn checkpoint.'])
PAGES['adventure_runner']=('Village Runner',['We have work for willing hunters. Review the available assignment, report your findings, or ask about the region. You may postpone without losing evidence.'])
PAGES['adventure_contact']=('Village contact',['What have you found?'])
REPLIES = {
    'adventure_caretaker':['Could you treat my injuries?'],'adventure_runner':['What needs doing?'],'adventure_contact':['What can we do?'],
    "wounded": ["What happened to you?", "We will find the dragon.", "We accept your quest."],
    "welcome": ["Yes, we are hunters.", "We will speak to the innkeeper."],
    "training": ["What do hunters earn here?", "Show me the training branches.", "Our training follows our class?", "I understand. Let us begin."],
}
PRESENTATIONS = {key:dict(type='npc',portrait=portrait) for key,portrait in {
    'adventure_contact':'Villager03','adventure_runner':'Villager02','adventure_caretaker':'Innkeeper','wounded':'Villager04','welcome':'Villager02','training':'Innkeeper',
    'adventure_hunter':'Villager04','adventure_recovered':'Villager04','adventure_welcome':'Villager02',
    'adventure_training':'Innkeeper','adventure_complete':'Villager02','caravan_aftermath':'Villager02'}.items()}


def inspect(player,title,text,kind='inspection'):
    start_dialogue(player,'inspection')
    player['dialogue'].update(title=title,text=text,presentation=kind)


def defaults(room, legacy=False):
    room.setdefault('challengeMode','classic');room.setdefault('challengeSeed',0)
    room.setdefault("story", {"afterStage": random.choice((1, 2)), "encountered": legacy,
                              "quest": "active" if legacy else "not_started"})
    room.setdefault("townInstance", "legacy-"+str(room.get("townSeed", 0)))
    room.setdefault("innRooms", rooms())
    for p in room["players"].values():
        p.setdefault("skillRanks", {key: 0 for key in SKILLS})
        p.setdefault("skillPoints", 0)
        p.setdefault("skillRewards", [])
        p.setdefault("trainingKnown", legacy)
        p.setdefault("questAccepted", legacy or p.get("bot", False))
        p.setdefault("innFloor", 1)
        p.setdefault("dialogue", None)


def rooms():
    occupied = set(random.sample(range(3), random.choice((1, 2))))
    return [{"id": "guest_"+str(i+1), "name": "Room "+str(i+1), "x": 260+i*220,
             "y": 190, "doorY": 330, "locked": i in occupied} for i in range(3)]


def start_dialogue(player, kind):
    player["dialogue"] = {"id": secrets.token_hex(5), "kind": kind, "page": 0}
    player.update(dx=0, dy=0, attacking=False, reviving=None)


def dialogue(player):
    d = player.get("dialogue")
    if not d:
        return None
    if d['kind']=='inspection':return {**d,'total':1,'reply':'What happened here?' if d['presentation']=='npc' else None,'button':'Close','presentation':d['presentation'],'portrait':d.get('portrait') if d['presentation']=='npc' else None}
    title, pages = PAGES[d["kind"]]
    presentation=PRESENTATIONS.get(d['kind'],dict(type='inspection',portrait=None))
    return __import__("dialogue_choices").decorate(player,{**d, "title": title, "text": pages[d["page"]], "total": len(pages),
            "presentation":presentation['type'],"portrait":presentation['portrait'],
            "reply": REPLIES[d["kind"]][d["page"]] if presentation['type']=='npc' else None,
            "button": "Accept quest" if d["kind"] == "wounded" and d["page"] == len(pages)-1 else
                      "Continue" if d["page"] < len(pages)-1 else "Understood"})


def advance(world, room, player, payload):
    d = player.get("dialogue")
    if not d or payload.get("id") != d["id"] or payload.get("page") != d["page"]:
        raise ValueError("This dialogue has changed. Continue the current page.")
    if d['kind']=='inspection':player['dialogue']=None;return
    if d["page"] < len(PAGES[d["kind"]][1])-1:
        d["page"] += 1
        return
    kind = d["kind"]
    player["dialogue"] = None
    if kind.startswith('adventure_'):
        import adventure
        adventure.advance(world, room, player, kind)
        return
    if kind == "wounded":
        player["questAccepted"] = True
        room["story"]["quest"] = "active"
        world._say(room, "system", "Wounded Hunter", player["name"]+" accepted the quest: Find and kill the dragon.")
    elif kind == "welcome":
        room["townWelcome"].setdefault("acknowledged", []).append(player["id"])
    elif kind == "training":
        player["trainingKnown"] = True
        reward(player, "first_inn")
        player["townInteraction"] = "innkeeper"
        for bot in room["players"].values():
            if bot.get("bot"):
                bot["trainingKnown"] = True
                reward(bot, "first_inn")


def reward(player, milestone):
    if milestone not in player.setdefault("skillRewards", []):
        player["skillRewards"].append(milestone)
        player["skillPoints"] = player.get("skillPoints", 0)+1


def boss_reward(room):
    number = room["bossesDefeated"]
    if number < 3:
        for p in room["players"].values():
            reward(p, "boss_"+str(number))
    else:
        room["story"]["quest"] = "complete"


def max_hp(player, classes):
    if 'magicRunes' in player:return __import__('magic_runes').maxima(player)[0]
    return (classes[player["class"]]["hp"]*(100+4*player.get("skillRanks", {}).get("vitality", 0))+99)//100


def train(world, room, player, branch, classes):
    npc = world._nearby_npc(room, player) if room["phase"] == "town" else None
    if not player.get("trainingKnown") or player.get("dialogue") or not npc or npc["id"] != "innkeeper":
        raise ValueError("Finish the innkeeper's tutorial and talk to them to train.")
    if not isinstance(branch, str) or branch not in SKILLS:
        raise ValueError("Choose Vitality, Power or Focus.")
    rank = player["skillRanks"].get(branch, 0)
    if rank >= 3 or player["skillPoints"] < 1:
        raise ValueError("You need a training point and an unfinished branch.")
    player["skillRanks"][branch] = rank+1
    player["skillPoints"] -= 1
    if branch == "vitality":
        previous = player["maxHp"]
        player["maxHp"] = max_hp(player, classes)
        player["hp"] = min(player["maxHp"], player["hp"]+player["maxHp"]-previous)
    world._say(room, "system", "Innkeeper", player["name"]+" trained "+SKILLS[branch]["name"]+" to rank "+str(rank+1)+".")


def locked(room, player):
    return bool(room.get('_campaignCinematic') or player.get("dialogue") or (room.get("townWelcome") and not room["townWelcome"].get("done")))


def enter_peace(world, room):
    room["phase"] = "peace"
    room["story"]["encountered"] = True
    room.update(projectiles=[], hazards=[], enemies=[])
    world._dismiss_summons(room)
    for i, p in enumerate(room["players"].values()):
        p.update(x=440+i*42, y=440, dx=0, dy=0, attacking=False, reviving=None, dialogue=None)
        p["questAccepted"] = bool(p.get("bot"))
    world._say(room, "system", "The Gauntlet", "A peaceful clearing. A wounded hunter rests beside the road. Speak to him.")


def tick(world, room, now):
    welcome = room.get("townWelcome")
    if room["phase"] == "town" and welcome and not welcome.get("done"):
        dt = min(.1, max(0, now-welcome["lastTick"]))
        welcome["lastTick"] = now
        welcome["y"] = min(405, welcome["y"]+150*dt)
        humans = [p for p in world._active_players(room) if not p.get("bot")]
        if welcome["y"] >= 405:
            for p in humans:
                if p["id"] not in welcome["acknowledged"] and not p.get("dialogue"):
                    start_dialogue(p, "welcome")
            if humans and all(p["id"] in welcome["acknowledged"] for p in humans):
                welcome["done"] = True
        for p in room["players"].values():
            p.update(dx=0, dy=0, attacking=False, lastMove=now)
    if room["phase"] == "peace":
        active = world._voting_players(room)
        if active and all(p.get("questAccepted") and world._at_stage_exit(p) for p in active):
            room["phase"] = "stage_exit"


def npcs(room, player):
    if player.get("innFloor", 1) == 2:
        result = {"stairs_down": {"x": 710, "y": 430}}
        for r in room["innRooms"]:
            result[("locked_" if r["locked"] else "bed_")+r["id"]] = {
                "x": r["x"], "y": r["doorY"] if r["locked"] else r["y"]}
        return result
    return {"innkeeper": {"x": 480, "y": 220}, "stairs_up": {"x": 710, "y": 350}}


def interior_walkable(room, player, x, y):
    if player.get("innFloor", 1) != 2:
        return True
    if y >= 340:
        return True
    return any(not r["locked"] and abs(x-r["x"]) < (25 if y >= 310 else 68) and y >= 130
               for r in room["innRooms"])


def checkpoint(world, room, player, bed_id):
    if room.get('mode') == 'adventure':
        import adventure
        adventure.rest(world, room, player, bed_id)
        return
    if not player.get("trainingKnown"):
        raise ValueError("Speak to the innkeeper to discover hunter training before resting.")
    bed = next((r for r in room["innRooms"] if "bed_"+r["id"] == bed_id and not r["locked"]), None)
    if player.get("innFloor") != 2 or not bed:
        raise ValueError("Find a bed in an unlocked upstairs room.")
    for p in room["players"].values():
        p.update(hp=p["maxHp"], mana=p["maxMana"])
    keys = ("bossesDefeated", "miniBossesSinceBoss", "miniBossesRequired", "regularWavesSinceMiniBoss",
            "regularWavesRequired", "bossSequence", "stageWave", "stageWaves", "miniBossStages", "bossStages",
            "puzzlesRequired", "puzzlesCompleted", "puzzleStages", "townsTarget", "townsVisited", "townStages",
            "townLayout", "townSeed", "townPaths", "townVillagers", "townDecor", "townPortal", "townDesignVersion", "difficulty", "totalStages",
            "townInstance", "innRooms")
    for key,default in (('objectiveStages',{}),('townPressureStages',[]),('lengthChosen',False)):
        room.setdefault(key,copy.deepcopy(default))
    keys+=('objectiveStages','townPressureStages','lengthChosen')
    room.setdefault('challengeMode','classic');room.setdefault('challengeSeed',0);keys+=('challengeMode','challengeSeed')
    room["checkpoint"] = {"stage": room["stage"], "wave": room["wave"], "town": room["town"],
        "region": room["region"], "bed": bed["id"],
        "shopStock": {pid: copy.deepcopy(p["shopStock"]) for pid,p in room["players"].items()},
        **{k: copy.deepcopy(room[k]) for k in keys}}
    for pid in room["players"]:
        room.setdefault("privateNotices", {})[pid] = "Party restored. Checkpoint set at the upstairs bed in "+bed["name"]+"."
    world._save_checkpoint(room)
    feedback.emit(room, 'rest', actor=player)
    world._say(room, "system", "The Gauntlet", player["name"]+" rested in "+bed["name"]+". The party's bed checkpoint is set.")


def place_at_checkpoint(room, player):
    checkpoint = room.get("checkpoint") or {}
    bed = next((r for r in room.get("innRooms", []) if r["id"] == checkpoint.get("bed")), None)
    inn = next((h for h in room.get("townLayout", []) if h.get("service") == "innkeeper"), None)
    player.update(dialogue=None, innFloor=2 if bed and inn else 1)
    if bed and inn:
        player.update(townInterior=inn["id"], townReturn=[inn["x"], inn["y"]+60], x=bed["x"], y=bed["y"]+65)
