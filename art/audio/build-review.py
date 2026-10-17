"""Listening references at conservative default bus gains; not live recordings."""
import json,wave,math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];RATE=22050
OUT=HERE/'review-clips';OUT.mkdir(exist_ok=True)
settings=dict(master=1,music=.16,effects=.4,ambience=.12,ui=.3)
tracklist=json.loads((ROOT/'static/music/manifest.json').read_text())['tracks']
references={}

def load(path):
    with wave.open(str(path)) as w:
        channels=w.getnchannels();rate=w.getframerate();data=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float).reshape(-1,channels)/32768
    if channels==1:data=np.repeat(data,2,axis=1)
    if rate!=RATE:
        positions=np.arange(round(len(data)*RATE/rate))*rate/RATE
        data=np.column_stack([np.interp(positions,np.arange(len(data)),data[:,i]) for i in range(2)])
    return data

def reference(key,seconds,music,events):
    result=np.zeros((round(seconds*RATE),2));track=load(ROOT/'static/music'/f'{music}.wav')
    for start in range(0,len(result),len(track)):
        count=min(len(track),len(result)-start);result[start:start+count]+=track[:count]*settings['music']*.8
    for e in events:
        sound=load(ROOT/'static/audio'/(e['name']+'.wav'));start=round(e['at']*RATE);count=min(len(sound),len(result)-start)
        if count>0:result[start:start+count]+=sound[:count]*e['gain']*settings[e.get('bus','effects')]
    result[:220]*=np.linspace(0,1,220)[:,None];result[-11025:]*=np.linspace(1,0,11025)[:,None]
    peak=float(np.max(np.abs(result)));assert peak<.85,'Reference needs safer balance'
    pcm=np.round(result*32767).astype('<i2')
    with wave.open(str(OUT/(key+'.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(pcm.tobytes())
    references[key]=dict(seconds=seconds,music=music,peak=round(peak,6),rms=round(float(np.sqrt(np.mean(result**2))),6),bytes=(OUT/(key+'.wav')).stat().st_size,events=events)

town=[dict(at=2,name='conversation-open',bus='ui',gain=.16),dict(at=6,name='conversation-close',bus='ui',gain=.16),dict(at=9,name='purchase',bus='ui',gain=.16),dict(at=12,name='equip',bus='ui',gain=.16),dict(at=15,name='rune-gain',bus='ui',gain=.32),dict(at=19,name='quest-report',bus='ui',gain=.32),dict(at=23,name='door',bus='ui',gain=.16),dict(at=25,name='amb-tools',bus='ambience',gain=.1)]
reference('town',30,'oakvale',town)
explore=[dict(at=3,name='amb-leaves',bus='ambience',gain=.1),dict(at=10,name='amb-wildlife',bus='ambience',gain=.1),dict(at=15,name='inspect',bus='ui',gain=.16),dict(at=20,name='amb-water',bus='ambience',gain=.07),dict(at=25,name='shrine-activate',bus='ui',gain=.32),dict(at=31,name='portal-travel',gain=.25)]
reference('exploration',40,'woodland',explore)
combat=[]
for at in np.arange(1,56,.7):
    for offset,name,gain in ((0,'knight-light',.21),(.04,'arrow-launch',.12),(.12,'nature-launch',.1),(.2,'hit-flesh-1',.105),(.24,'sacred-launch',.1)):
        combat.append(dict(at=round(float(at+offset),3),name=name,gain=gain))
for at in range(5,54,8):combat.extend([dict(at=at,name='boss-warning',gain=.4),dict(at=at+.8,name='enemy-fire-launch',gain=.12),dict(at=at+1.1,name='hurt',gain=.22),dict(at=at+2,name='heal',gain=.3)])
combat.extend([dict(at=3,name='summon-fire',gain=.25),dict(at=18,name='wizard-special',gain=.4),dict(at=30,name='down',gain=.65),dict(at=32,name='revive',gain=.48),dict(at=42,name='ascend-knight',gain=.48),dict(at=44,name='ascended-knight',gain=.4),dict(at=57,name='boss-complete',gain=.5)])
reference('combat',60,'combat',combat)
(HERE/'review-metrics.json').write_text(json.dumps(dict(version=1,settings=settings,note='Authored references, not recordings or proof of actual listening. Bus gains are applied; live spatial attenuation/compression and game timing differ.',references=references),indent=2)+'\n')
tracks=''.join('<label>'+t['title']+'<audio class="music" controls preload="none" src="../../static/music/'+t['file']+'"></audio></label>' for t in tracklist.values())
clips=''.join('<label>'+name.title()+' · '+str(r['seconds'])+' seconds<audio controls preload="none" src="review-clips/'+name+'.wav"></audio></label>' for name,r in references.items())
cues=['arrow-launch','fire-impact','frost-launch','lightning-launch','hit-flesh','hit-metal','hit-wood','hit-stone','hit-barrier','hit-magic','rune-gain','rune-spend','shrine-activate','ascend-knight','ascend-healer','boss-warning','revive']
fx=''.join('<label>'+n+'<audio class="effect" controls preload="none" src="../../static/audio/'+n+'.wav"></audio></label>' for n in cues)
(HERE/'review.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>The Gauntlet · Audio review</title><style>body{background:#172b35;color:#e3e7d8;font:16px system-ui;max-width:1100px;margin:auto;padding:20px}h1{font-size:26px}h2{font-size:20px;margin-top:30px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}label{display:block;padding:14px;background:#243a46}audio{display:block;width:100%;margin-top:8px}p{max-width:80ch;line-height:1.5}</style><h1>The Gauntlet · Audio review</h1><p>Original synthesized score, retained Bxfr effects, quieter impacts and distinct interaction cues. Start at a comfortable device volume. No autoplay. Headphone/speaker judgment is still required: the agent cannot hear these files.</p><h2>Mixed references</h2><p>Conservative default bus gains are baked into these authored references. They are not live gameplay recordings. Repeat the combat clip to assess fatigue; the live game additionally applies voice limits, attenuation and compression.</p><div class="grid">'+clips+'</div><h2>Original musical arrangements</h2><p>Ten related arrangements share the refuge motif. The Last Caravan moves from road tension into the Oakvale theme; its refuge section loops in the game without repeating the opening. Plucked-string and airy textures are synthesized, not acoustic recordings. This score uses no third-party samples.</p><div class="grid">'+tracks+'</div><h2>Representative source cues</h2><p>Music controls start at the default music bus gain. Individual effect controls start at a quiet reference level; the runtime settings panel previews every category at its configured level.</p><div class="grid">'+fx+'</div><script>document.querySelectorAll("audio.music").forEach(a=>a.volume=.128);document.querySelectorAll("audio.effect").forEach(a=>a.volume=.16);document.querySelectorAll("audio").forEach(a=>a.addEventListener("play",()=>document.querySelectorAll("audio").forEach(b=>{if(a!==b)b.pause();})));document.addEventListener("visibilitychange",()=>{if(document.hidden)document.querySelectorAll("audio").forEach(a=>a.pause());});</script></html>',encoding='utf-8')
print(json.dumps({key:{k:v for k,v in r.items() if k!='events'} for key,r in references.items()}))
