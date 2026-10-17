"""Inventory implemented content/art from source without opening a game world."""
import ast
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/visual-quality-v3'


def tree(file):return ast.parse((ROOT/file).read_text(encoding='utf-8-sig'))
def defined(file,name):return next(n.value for n in tree(file).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
def literal(file,name):return ast.literal_eval(defined(file,name))
def keys(file,name):return [ast.literal_eval(k) for k in defined(file,name).keys]


def main():
    rows=[]
    def add(id,where,art,status='final',states='static',dimensions='64×64',priority='P3',reason='Dedicated runtime artwork',fallback='Native drawing while art loads'):
        if art and status=='final' and not all((ROOT/p).is_file() for p in art.split(';')):status='missing';priority='P0';reason='Runtime artwork file absent'
        rows.append(dict(id=id,appears=where,currentArt=art,status=status,requiredStates=states,dimensions=dimensions,priority=priority,reason=reason,fallback=fallback))
    for hero in keys('game.py','CLASSES'):
        add('hero:'+hero,'Both modes; character renderer','static/sprites/'+hero.lower()+'-idle.png;static/sprites/'+hero.lower()+'-abilities-v1.png',states='8 directions; idle, move, basic, cast, ultimate',dimensions='64px body / 96px casts')
        base='static/sprites/ascended-'+hero.lower()
        code=(ROOT/'static/ascended-sprites.js').read_text() if (ROOT/'static/ascended-sprites.js').is_file() else ''
        done=bool(code) and all((ROOT/(base+s)).is_file() for s in ('-body-v1.png','-actions-v1.png','-v1.json'))
        add('ascended:'+hero,'Adventure; purchased Ascension',base+'-body-v1.png;'+base+'-actions-v1.png;'+base+'-v1.json' if done else 'Base hero plus generic gold ring','final' if done else 'placeholder','8 directions; idle3, move3, basic3, cast3, signature3, hit, downed, transformation','96px cell','P0' if not done else 'P3','Transformed model integrated' if done else 'No transformed model currently connected')
    for name in ['lightningbird','firewolf','icebear','naturegolem']:add('summon:'+name,'Druid summons','static/sprites/'+name+'-idle.png',states='8 directions; idle, move, attack',dimensions='64px display; source metadata')
    for kind in ['serpent','minotaur','troll','spider','wolf','draco','chimera','shrine-guardian']:
        add('enemy:'+kind,'Waves, bosses and authored Adventure encounters','static/sprites/'+kind+'-idle.png;static/sprites/'+kind+'-windup-v1.png',states='8 directions; idle/move/release and heavy/ranged/charge windups',dimensions='64px display; atlas metadata')
    add('enemy:adult-dragon','Gauntlet finale; Last Caravan distant sequence','static/sprites/dragon-adult-idle-v2.png;static/sprites/dragon-adult-windup-v2.png',states='8 directions; idle/move/attack/windup',dimensions='128px display')
    for key in keys('game.py','ITEMS')+keys('tactical_rules.py','BUILD_ITEMS'):add('item:'+key,'Pouch, equipment, shops, loot','static/sprites/item-'+key+'-v1.png')
    for row in literal('game.py','CURSES'):add('curse:'+row['effect'],'Curse slot and inspection','static/sprites/curse-'+row['effect']+'-v1.png')
    for hero,abilities in literal('game.py','ABILITY_SETS').items():
        for a in abilities:add('ability:'+a[0],hero+' base attack choices','static/sprites/ability-'+a[0]+'-v1.png',states='Icon; class action motion; matching gameplay effect',dimensions='64px icon; 96px animation')
    for call in ast.walk(tree('hero_skills.py')):
        if isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='define' and len(call.args)>3:
            hero=ast.literal_eval(call.args[0])
            for a in ast.literal_eval(call.args[3]):
                add('skill:'+a[0],hero+' Adventure skill tree','static/sprites/ability-'+a[-1]+'-v1.png','intentionally reused','Icon; '+a[3]+' motion/effect','64px icon / server footprint','P1','Existing icon is aliased; audit motion and mechanics separately')
    for name in ['merchant','guildmaster','alchemist','innkeeper']+['villager'+str(i).zfill(2) for i in range(1,9)]:add('npc:'+name,'Oakvale/Dunmere services and villagers','static/sprites/'+name+'-idle.png',states='8 directions; idle, walk, gesture',dimensions='64px display')
    integration=(ROOT/'static/region-sprites.js').read_text() if (ROOT/'static/region-sprites.js').is_file() else ''
    for area,features in literal('region_content.py','FEATURES').items():
        for id,name,x,y,kind in features:
            if kind in ('talk','witness'):add('feature:'+id,area,'static/sprites/adventure-npcs-v1.png','intentionally reused','Idle / gesture','256px atlas cell, scaled','P3','Intentional same runner/worker NPC identity');continue
            if id in ('dry_spring','east_landmark','ridge_barrier'):
                add('feature:'+id,area,'static/sprites/adventure-discoveries-v1.png' if id=='dry_spring' else 'static/sprites/adventure-signals-v1.png','intentionally reused','Closed/open casket' if id=='dry_spring' else 'Readable signpost','256px atlas cell','P3','Existing spring casket / authored wooden marker matches the object identity');continue
            connected=id in integration and (ROOT/'static/sprites/region-props-v1.png').is_file()
            add('feature:'+id,area,'static/sprites/region-props-v1.png' if connected else 'Generic woodland_sign / workbench / seal / cache','final' if connected else 'placeholder','Readable prop; mechanism before/after state if supported','160px atlas cell','P3' if connected else 'P0','Dedicated interactive object' if connected else 'Several mechanically distinct new objects share a sign/workbench')
    add('boss:blighted-overseer','Dunmere sealed cellar','static/sprites/troll-idle.png;static/sprites/troll-windup-v1.png','intentionally reused',states='8 directions; idle, move, release, windup',dimensions='Existing enemy layout',priority='P3',reason='Authoritative Nature troll boss: same species and attack kit; blight effects, boss scale/name/health distinguish the encounter. No substitute species or missing animation.')
    for shrine in ('brook','deepwood','watch'):add('shrine:'+shrine,'Woodland travel waystones','static/sprites/travel-shrines-v2.png',states='Inactive / attuned; finite portal channel / arrival',dimensions='160px cell, 2 columns × 3 rows')
    for name in ['cave','tower']:
        add('map:'+name,'Discovered dungeon maps','static/sprites/dungeon-map-'+name+'-v1.png',dimensions='960×540',states='Discovered fog / cleared / sealed overlays')
    cellar=(ROOT/'static/dungeon-sprites.js').read_text()
    add('map:mill_cellar','Dunmere cellar map','static/sprites/dungeon-map-cellar-v1.png' if 'dungeon-map-cellar-v1.png' in cellar else 'Native rectangles / labels','final' if 'dungeon-map-cellar-v1.png' in cellar else 'placeholder',states='Discovered / party / sealed / cleared',dimensions='960×540',priority='P1')
    for region in ['woodland','ruins','cavern','frost']:
        add('scenery:'+region,'Current region palette; intentional reuse for Dunmere','static/sprites/world-ground-'+region+'-v2.png;static/sprites/world-scenery-v2.png',states='Floor / trees / low detail / occlusion',dimensions='512px floor / 160px props')
        add('village:'+region,'Oakvale and Dunmere; same cultural building kit','static/sprites/village-'+region+'-buildings-v2.png;static/sprites/village-'+region+'-interiors-v2.png;static/sprites/village-'+region+'-upstairs-v2.png',states='6 buildings / interiors / upstairs / roof variants',dimensions='80px buildings, 480×270 interiors')
    for key in ['dungeon-props','portal-effects','flight-missiles','flight-spells','flight-enemy','terrain-effects','hazard-effects','impact-effects','magic-effects','puzzle-objects','objective-ward','objective-rift']:
        add('pack:'+key,'Shared renderer; intentional mechanical-family reuse','static/sprites/'+key+'-v1.png',states='Atlas rows; effects4frames; authoritative warning boundaries',dimensions='Per-pack metadata')
    counts={s:sum(r['status']==s for r in rows) for s in ['final','intentionally reused','placeholder','missing','broken']}
    result=dict(scope='Implemented content only; no private worlds imported; actual mechanics reviewed in separate effect inventory',counts=counts,assets=rows)
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/'asset-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (OUT/'asset-audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(counts))


if __name__=='__main__':main()
