"""Local-only isolated browser QA server. Never reads private player saves.

Fixtures are explicitly helper-completed content and do not prove balance.
"""
import argparse
import os
import sys
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'tests')]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--storage',type=Path,required=True);parser.add_argument('--port',type=int,default=8090)
parser.add_argument('--fixture',choices=['fresh','dunmere','ascension'],default='fresh')
args=parser.parse_args();root=Path(__file__).resolve().parents[1]
try:args.storage.resolve().relative_to(root/'data')
except ValueError:pass
else:parser.error('QA storage must be outside private data/.')
import run_storage
original=run_storage.RunStorage.__init__
with patch.object(run_storage.RunStorage,'__init__',lambda self,_path:original(self,args.storage)):import game
import server
if args.fixture!='fresh' and not game.WORLD.rooms:
    import adventure,region_content,magic_runes,chapter_flow
    from test_expansion import report_chain
    from test_adventure import finish
    w=game.WORLD;c,h=w.create_room('Offline fixture keeper');r=w.rooms[c]
    w.action(c,h,dict(action='class',**{'class':'Healer'}));w.action(c,h,dict(action='runOptions',mode='adventure'));r['_skipOpening']=True;w.action(c,h,dict(action='start'));p=r['players'][h];finish(w,r,p)
    report_chain(w,r,p,'chapter_outcome' if args.fixture=='ascension' else 'border')
    r['adventure']['quests']={k:'complete' for k in adventure.QUESTS};r['adventure'].update(bridge=True,bossComplete=True)
    if args.fixture=='ascension':region_content.ensure(r).update(cellarComplete=True,cellarAttempt=False)
    r['adventure']['travelShrines']=dict(version=1,active=['brook','deepwood','watch'])
    adventure.reveal(r,'brook','hollow','watch','border','dunmere','fields','mill','cellar')
    for key in ('brook','hollow','watch'):r['adventure']['areas'][key]=adventure.build_area(w,r,key);r['adventure']['areas'][key]['enemies']=[]
    adventure.enter(w,r,'dunmere','north');p['connected']=False;adventure.save(w,r)
    print('HELPER-completed fixture, not earned gameplay; join code '+c,flush=True)
os.environ.update(HOST='127.0.0.1',PORT=str(args.port));server.main()
