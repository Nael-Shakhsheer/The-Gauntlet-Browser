"""Disposable solo/four-player audio QA. No production data or fixture endpoint."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8013)
    parser.add_argument('--players',type=int,choices=(1,4),default=4)
    parser.add_argument('--touch-controls',action='store_true')
    parser.add_argument('--scene',choices=('cave','town','woods','boss','caravan','dunmere','ascension'),default='cave')
    args=parser.parse_args()
    task_root=Path(__file__).resolve().parents[1]/'.test-tmp';task_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gauntlet-audio-qa-',dir=task_root) as directory:
        # Isolate the imported singleton as well as the explicit fixture world.
        import run_storage
        original=run_storage.RunStorage.__init__
        with patch.object(run_storage.RunStorage,'__init__',lambda self,_path:original(self,Path(directory)/'bootstrap')):
            import server
            from test_adventure import party,travel
        heroes=('Knight','Wizard','Druid','Healer') if args.players==4 else ('Knight',)
        world,room,players=party(heroes) # Audio QA is deliberately memory-only.
        if args.scene in ('cave','woods','boss'):
            travel(world,room,'road')
            if args.scene!='woods':travel(world,room,'cave_entry')
        if args.scene=='boss':
            travel(world,room,'cave_gallery');travel(world,room,'cave_heart')
            from test_dungeons import begin
            begin(world,room,players)
        if args.scene=='caravan':
            from test_opening import new
            world,room,players=new(heroes)
        if args.scene in ('dunmere','ascension'):
            import adventure,magic_runes
            adventure.enter(world,room,'dunmere' if args.scene=='dunmere' else 'home','south')
            if args.scene=='ascension':
                for p in players:
                    for key in magic_runes.SOURCES:
                        if key!='cache:dry_spring':magic_runes.claim(p,key)
        for i,p in enumerate(players):
            if args.scene in ('cave','woods'):p.update(x=440 if i==0 else 330+i*30,y=290 if i==0 else 250+i*35,hp=p['maxHp']-20)
            p['connected']=False
        ready=threading.Event()
        server.WORLD=world
        session=json.dumps(server.recovery().session(room['code'],players[0]['id']))
        class Handler(server.Handler):
            def do_GET(self):
                path=self.path.split('?')[0]
                if path=='/audio-review':
                    html=(server.ROOT/'art/audio/review.html').read_text(encoding='utf-8').replace('../../static/','/').replace('review-clips/','/audio-review-clips/')
                    return self._send(200,html,'text/html; charset=utf-8')
                if path.startswith('/audio-review-clips/'):
                    name=path.removeprefix('/audio-review-clips/')
                    if name not in ('town.wav','exploration.wav','combat.wav'):return self._error('Not found.',404)
                    return self._send(200,(server.ROOT/'art/audio/review-clips'/name).read_bytes(),'audio/wav')
                return super().do_GET()
            def _file(self,name,mime):
                if name=='index.html':
                    ready.set()
                    html=(server.STATIC/name).read_text(encoding='utf-8')
                    html=html.replace('<head>','<head><script>localStorage.setItem("gauntlet-session",'+json.dumps(session)+');</script>')
                    if args.touch_controls:html=html.replace('</head>','<script>document.documentElement.dataset.touchPreview="true";</script><style>body.is-playing .arena-controls{display:flex!important}</style></head>')
                    html=html.replace('</body>','<aside id="audioQa" style="position:fixed;bottom:0;left:0;font:10px monospace;background:#102431;color:white;pointer-events:none;z-index:9999">Disposable QA</aside><script>let frames=0,frameAt=performance.now(),fps=0;function countFrames(){frames++;const now=performance.now();if(now-frameAt>1000){fps=Math.round(frames*1000/(now-frameAt));frames=0;frameAt=now;}requestAnimationFrame(countFrames);}countFrames();setInterval(()=>{const a=window.GauntletAudio?.diagnostics();document.getElementById("audioQa").textContent=JSON.stringify({fps,audio:a,visual:window.GauntletFeedback?.diagnostics()});},500);</script></body>')
                    return self._send(200,html,mime)
                super()._file(name,mime)
        stop=threading.Event()
        def actions():
            started=None;last={}
            while not stop.wait(.2):
                if not ready.is_set():continue
                if started is None:started=time.monotonic()
                with world.lock:
                    now=time.monotonic()
                    # Existing accepted abilities and ordinary keepalive only. Rules unchanged.
                    for p in players:
                        world.state(room['code'],p['id'])
                        if args.players==1 or args.scene in ('town','dunmere','ascension'):continue
                        elapsed=now-started
                        slot=2 if int(elapsed)%8==2 else 3 if int(elapsed)%17==5 else 1
                        if now-last.get((p['id'],slot),0)<(2 if slot==1 else 8):continue
                        last[p['id'],slot]=now
                        try:world.action(room['code'],p['id'],dict(action='ability',slot=slot))
                        except ValueError:pass
        simulation=threading.Thread(target=server._simulation_loop,args=(stop,),daemon=True)
        control=threading.Thread(target=actions,daemon=True)
        listener=server.ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
        simulation.start();control.start()
        print(f'Disposable {args.players}-player QA: http://127.0.0.1:{args.port} (ordinary stats, memory-only fixture)',flush=True)
        try:listener.serve_forever()
        except KeyboardInterrupt:pass
        finally:stop.set();listener.server_close();simulation.join(2);control.join(2)
        if world._tick_errors:raise RuntimeError('Simulation error during QA')


if __name__=='__main__':main()
