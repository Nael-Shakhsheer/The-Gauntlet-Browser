"""Catalog actual definitions and sprite exports without starting a game world."""
import ast
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/dungeon-portal'


def definition(file,name):
    tree=ast.parse((ROOT/file).read_text(encoding='utf-8'))
    return next(n.value for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))


def dict_keys(node):
    return [ast.literal_eval(k) for k in node.keys]


def file_record(file):
    path=ROOT/file
    record=dict(path=file,present=path.is_file())
    if path.is_file():
        record.update(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if path.suffix=='.png':
            with Image.open(path) as im:record.update(size=list(im.size),mode=im.mode)
    return record


def main():
    items=dict_keys(definition('game.py','ITEMS'))+dict_keys(definition('tactical_rules.py','BUILD_ITEMS'))
    heroes=dict_keys(definition('game.py','CLASSES'))
    abilities=[ast.literal_eval(n.elts[0]) for n in ast.walk(definition('game.py','ABILITY_SETS')) if isinstance(n,ast.Tuple)]
    curses=[ast.literal_eval(n.values[i]) for n in ast.walk(definition('game.py','CURSES'))
            if isinstance(n,ast.Dict) for i,k in enumerate(n.keys) if isinstance(k,ast.Constant) and k.value=='effect']
    groups={
        'items':['static/sprites/item-'+key+'-v1.png' for key in items],
        'ability_icons':['static/sprites/ability-'+key+'-v1.png' for key in abilities],
        'curses':['static/sprites/curse-'+key+'-v1.png' for key in curses],
        'heroes_and_summons':['static/sprites/'+key.lower()+'-idle.png' for key in heroes+['LightningBird','FireWolf','IceBear','NatureGolem']],
        'enemy_models':['static/sprites/'+key+'-idle.png' for key in ['serpent','minotaur','troll','spider','wolf','draco','chimera','shrine-guardian']]+['static/sprites/dragon-adult-idle-v2.png'],
        'town_characters':['static/sprites/'+key+'-idle.png' for key in ['merchant','guildmaster','alchemist','innkeeper']+['villager'+str(i).zfill(2) for i in range(1,9)]],
        'combat_and_puzzle':['static/sprites/'+key+'-v1.png' for key in ['terrain-effects','hazard-effects','impact-effects','magic-effects','objective-rift','objective-ward','puzzle-objects','fork-signposts','flight-missiles','flight-spells','flight-enemy']+['cover-'+r for r in ['woodland','ruins','cavern','frost']]],
        'new_dungeon_portal':['static/sprites/'+key+'-v1.png' for key in ['dungeon-map-cave','dungeon-map-tower','dungeon-materials','dungeon-props','dungeon-entrance-cave','dungeon-entrance-tower','portal-effects','dungeon-floor-cave','dungeon-floor-tower']],
    }
    catalog={key:[file_record(p) for p in paths] for key,paths in groups.items()}
    inventory=dict(scope='Definition and asset inventory; no game rooms, saves or regression suites',counts={k:len(v) for k,v in catalog.items()},missing=[r['path'] for rows in catalog.values() for r in rows if not r['present']],groups=catalog,
                   sources=[file_record(p.relative_to(ROOT).as_posix()) for p in sorted((OUT/'source').glob('*.png'))])
    (OUT/'asset-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(counts=inventory['counts'],missing=inventory['missing'])))


if __name__=='__main__':main()
