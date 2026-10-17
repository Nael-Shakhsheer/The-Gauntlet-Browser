"""Isolated browser QA server. Saves are temporary, never the real data folder.

No fixture endpoint is added to the actual game. --scene prepares authored test
data before the server starts. Default is the ordinary menu/start flow.
"""
import argparse
from contextlib import nullcontext
import json
import logging
from pathlib import Path
import sys
import tempfile
import threading
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
import adventure
import game
import server
from test_adventure import party,travel,interact,kill,shrine,finish,read_sign


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8002)
    parser.add_argument('--temp-root',type=Path,default=Path(__file__).resolve().parents[1]/'.test-tmp',help='Writable fixture directory, separate from private data/.')
    parser.add_argument('--storage-dir',type=Path,help='Optional restartable disposable storage. Must be a child of --temp-root; never private data/.')
    parser.add_argument('--scene',choices=('menu','portal','road','sign','camp','cache','watch','bridge','bridge-broken','complete','shrine','cave','tower','dungeons-complete'),default='menu')
    parser.add_argument('--fast-combat',action='store_true',help='Disposable browser QA only: high HP and damage to verify complete encounter flows quickly, not balance.')
    parser.add_argument('--ordinary-kit',action='store_true',help='Ordinary shop kit: class weapon, Oakguard, heal/mana/ward; no stat boosts or ranks. Useful for repeatable dungeon reviews.')
    parser.add_argument('--touch-controls',action='store_true',help='Show the existing coarse-pointer movement pad for narrow-viewport QA; not hardware touch emulation.')
    parser.add_argument('--observations',help='Write anonymous ordinary-stat browser observations at shutdown; accelerated scenes are explicitly labelled.')
    args=parser.parse_args()
    try:args.temp_root.resolve().relative_to(Path(__file__).resolve().parents[1]/'data')
    except ValueError:pass
    else:parser.error('QA storage must be outside private data/.')
    args.temp_root.mkdir(parents=True,exist_ok=True)
    if args.storage_dir:
        try:args.storage_dir.resolve().relative_to(args.temp_root.resolve())
        except ValueError:parser.error('--storage-dir must be under the disposable --temp-root.')
        if args.storage_dir.resolve()==args.temp_root.resolve():parser.error('Choose a separate disposable child directory.')
        args.storage_dir.mkdir(parents=True,exist_ok=True)
    with (nullcontext(str(args.storage_dir)) if args.storage_dir else tempfile.TemporaryDirectory(prefix='gauntlet-adventure-qa-',dir=args.temp_root)) as directory:
        world=game.GameWorld(storage_dir=directory,disconnect_timeout=15)
        session=None
        if args.scene=='portal':
            world,room,ps=party(storage_dir=directory);p=ps[0]
            p.update(x=480,y=260)
            session={'room':room['code'],'player':p['id']}
        if args.scene=='road':
            world,room,ps=party(storage_dir=directory);p=ps[0]
            travel(world,room,'road');p.update(x=1100,y=650)
            session={'room':room['code'],'player':p['id']}
        if args.scene=='cache':
            world,room,ps=party(storage_dir=directory);p=ps[0];travel(world,room,'road')
            x,y=adventure.point(room,250,340);p.update(x=x,y=y)
            session={'room':room['code'],'player':p['id']}
        if args.scene in ('cave','tower'):
            world,room,ps=party(storage_dir=directory);p=ps[0];travel(world,room,'road')
            if args.scene=='tower':travel(world,room,'crossroads');travel(world,room,'camp')
            destination='cave_entry' if args.scene=='cave' else 'tower_1'
            e=next(e for e in adventure.exits(room) if e['id']==destination);p.update(x=e['x']-55,y=e['y'])
            session={'room':room['code'],'player':p['id']}
        if args.scene=='dungeons-complete':
            from test_dungeons import begin,clear_floor
            world,room,ps=party(storage_dir=directory);p=ps[0]
            adventure.enter(world,room,'cave_entry','west');interact(world,room,p,'cave_supplies');kill(world,room,p)
            travel(world,room,'cave_gallery');kill(world,room,p);travel(world,room,'cave_cache')
            interact(world,room,p,'cave_survey');kill(world,room,p);travel(world,room,'cave_gallery');travel(world,room,'cave_heart')
            begin(world,room,ps);kill(world,room,p);adventure.enter(world,room,'tower_1','west')
            for floor in (1,2,3):
                clear_floor(world,room,ps)
                if floor<3:travel(world,room,'tower_'+str(floor+1))
            adventure.enter(world,room,'cave_heart','west');p.update(x=480,y=400)
            session={'room':room['code'],'player':p['id']}
        if args.scene not in ('menu','portal','road','cache','cave','tower','dungeons-complete'):
            world,room,ps=party(storage_dir=directory);p=ps[0]
            travel(world,room,'road');interact(world,room,p,'tracks');travel(world,room,'crossroads');read_sign(world,room,p)
            if args.scene=='camp':
                travel(world,room,'camp');kill(world,room,p);p.update(x=400,y=350)
            elif args.scene=='watch':
                travel(world,room,'clearing');kill(world,room,p)
                x,y=adventure.point(room,635,365);p.update(x=x,y=y)
            elif args.scene=='bridge-broken':
                travel(world,room,'camp');kill(world,room,p);interact(world,room,p,'kit');travel(world,room,'bridge')
                kill(world,room,p);p.update(x=680,y=260)
            elif args.scene!='sign':
                travel(world,room,'clearing');kill(world,room,p);interact(world,room,p,'hunter')
                travel(world,room,'shrine')
                if args.scene!='shrine':
                    shrine(world,room,p);travel(world,room,'crossroads');travel(world,room,'camp')
                    kill(world,room,p);interact(world,room,p,'kit');travel(world,room,'bridge');interact(world,room,p,'repair')
                    if args.scene=='complete':
                        travel(world,room,'ruins');interact(world,room,p,'seal');kill(world,room,p);finish(world,room,p)
                        travel(world,room,'bridge');travel(world,room,'road');travel(world,room,'home')
            session={'room':room['code'],'player':p['id']}
        if args.fast_combat and session:
            p=world.rooms[session['room']]['players'][session['player']]
            p.update(maxHp=5000,hp=5000,damageBoost=20,damageBoostUntil=time.monotonic()+3600)
        if args.ordinary_kit and session:
            for p in world.rooms[session['room']]['players'].values():
                p['toolSlots']=[world._make_item(game.CLASS_WEAPONS[p['class']]),world._make_item('oakguard_vest')]
                p['utilitySlots']=[world._make_item(k) for k in ('healing_draught','mana_draught','warding_tonic')]
        server.WORLD=world
        server.RECOVERY=__import__('adventure_recovery').Recovery(world)
        if session:
            session=server.RECOVERY.session(session['room'],session['player'])
            if args.observations:__import__('chapter_observations').enable(world.rooms[session['room']],'accelerated functional fixture' if args.fast_combat else 'ordinary stats browser review')
        class PreviewHandler(server.Handler):
            def _file(self,name,mime):
                if name=='index.html' and (session or args.touch_controls):
                    html=(server.STATIC/name).read_text(encoding='utf-8')
                    if session:
                        auth=json.dumps(session)
                        html=html.replace('<head>','<head><script>localStorage.setItem("gauntlet-session",'+json.dumps(auth)+');</script>')
                    if args.touch_controls:
                        html=html.replace('</head>','<script>document.documentElement.dataset.touchPreview="true";</script><style>body.is-playing .arena-controls {display:flex !important;}</style></head>')
                    return self._send(200,html,mime)
                super()._file(name,mime)
        listener=server.ThreadingHTTPServer(('127.0.0.1',args.port),PreviewHandler)
        stop=threading.Event()
        simulation=threading.Thread(target=server._simulation_loop,args=(stop,),daemon=True);simulation.start()
        print(f'Isolated {args.scene} QA at http://127.0.0.1:{args.port}',flush=True)
        try:listener.serve_forever()
        except KeyboardInterrupt:pass
        finally:
            stop.set();listener.server_close();simulation.join(2)
            if args.observations and session:
                report=__import__('chapter_observations').finish(world.rooms[session['room']],'review ended')
                Path(args.observations).write_text(json.dumps(report,indent=2),encoding='utf-8')
        if world._tick_errors:raise RuntimeError('Simulation errors during browser QA')


if __name__=='__main__':main()
