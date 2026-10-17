"""Render an original small score. Editable notes + instrument formulas; no samples/Bfxr.

Requires numpy for authoring only. Runtime consumes ordinary PCM WAV assets.
"""
import hashlib,json,math,wave,sys,time,shutil
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RATE=22050
MOTIF=[(0,62,1),(1.5,66,.5),(2,69,1),(3,67,.75),(4,66,1),(5.5,64,.5),(6,62,1.5)]
TRACKS={
 'menu':dict(title='A Road to Refuge',bpm=72,bars=8,style='menu',roots=[50,47,43,45],motif='refuge'),
 'oakvale':dict(title='Oakvale · Lanterns at Home',bpm=80,bars=8,style='town',roots=[50,47,43,45],motif='refuge'),
 'dunmere':dict(title='Dunmere · The Empty Mill',bpm=64,bars=8,style='dry',roots=[50,46,43,45],motif='worn refuge'),
 'dryfields':dict(title='Fields Without Grain',bpm=68,bars=8,style='dry',roots=[50,48,46,45],motif='sparse refuge variation'),
 'woodland':dict(title='Between the Leaves',bpm=72,bars=8,style='woods',roots=[50,48,46,45],motif='refuge in minor'),
 'dungeon':dict(title='Under the Old Stones',bpm=80,bars=8,style='dungeon',roots=[38,41,43,45],motif='low refuge fragments'),
 'combat':dict(title='Hold the Crossing',bpm=112,bars=16,style='combat',roots=[50,46,43,45],motif='refuge rhythm'),
 'boss':dict(title='The Broken Watch',bpm=120,bars=16,style='boss',roots=[38,46,43,45],motif='developed refuge'),
 'victory':dict(title='A Light Remains',bpm=80,bars=4,style='victory',roots=[43,45,50,50],motif='refuge resolution',once=True),
 'caravan':dict(title='The Last Caravan · Road to Oakvale',bpm=96,bars=16,style='caravan',roots=[50,46,43,45],motif='dramatic road → refuge',introBars=8)
}

def instrument(note,duration,kind,seed):
    count=max(32,int((duration+1.1)*RATE));t=np.arange(count)/RATE
    f=440*2**((note-69)/12);rng=np.random.default_rng(seed)
    if kind=='drum':
        return (np.sin(2*np.pi*(80*t+24*(1-np.exp(-t*15))))*np.exp(-t*17)+rng.normal(0,.08,count)*np.exp(-t*35))*.6
    if kind=='brush':
        noise=rng.normal(0,1,count);return np.convolve(noise,np.ones(9)/9,mode='same')*np.exp(-t*23)*.12
    if kind=='pluck':
        signal=sum(np.sin(2*np.pi*f*h*t+.11*h)/h**1.7*np.exp(-t*(2.2+h*.36)) for h in range(1,9))
        return signal*np.minimum(1,t/.006)
    if kind=='bass':return (np.sin(2*np.pi*f*t)+.12*np.sin(2*np.pi*f*2*t))*np.minimum(1,t/.025)*np.exp(-t*2.1)
    signal=np.sin(2*np.pi*f*t+.008*np.sin(2*np.pi*4*t))+.14*np.sin(2*np.pi*f*2*t)
    return signal*np.minimum(1,t/.09)*np.minimum(1,np.maximum(0,(duration+.7-t)/.7))*np.exp(-t*.4)

def compose(spec):
    notes=[];style=spec['style'];bpm=spec['bpm'];beat=60/bpm
    def add(at,n,d=1,g=.12,k='pluck',pan=0):notes.append(dict(beat=round(at,4),note=n,duration=d,gain=g,instrument=k,pan=pan))
    for bar in range(spec['bars']):
        safe=style in ('menu','town','victory') or style=='caravan' and bar>=8
        dry=style=='dry';root=([50,47,43,45] if safe else spec['roots'])[bar%4]
        rhythm=style in ('combat','boss','caravan') and not safe
        third=4 if safe else 3
        add(bar*4,max(38,root-12),2,.08 if rhythm else .045,'bass')
        chord=[root,root+third,root+7,root+12]
        if style not in ('dry','dungeon') or bar%2==0:
            for i,n in enumerate(chord):add(bar*4+i*.055,n,2.5,.065 if safe else .04,'pluck',(-1 if i%2 else 1)*.3)
        if rhythm or safe:
            for i in range(4):add(bar*4+i+.5,chord[i%4]+12,.6,.03 if safe else .055,'pluck',.2)
        if rhythm:
            for b in (0,2):add(bar*4+b,36,.2,.085 if style=='boss' else .06,'drum')
            for b in (1,3):add(bar*4+b,0,.15,.09,'brush',-.15)
        elif style=='dungeon':
            for b in (0,2):add(bar*4+b,root,.5,.04,'pluck',-.2)
        # An eight-beat motif, varied by harmony and region, never an endless tone.
        if bar%2==0 and (not dry or bar in (0,4)):
            for at,n,d in MOTIF:
                if not safe and n==66:n=65
                if dry and at in (1.5,5.5):continue
                octave=-12 if style=='dungeon' else 0
                add(bar*4+at,n+octave,d,.09 if safe else .065,'air' if style in ('woods','dry') else 'pluck',-.15)
    return notes

def render(key,spec):
    beat=60/spec['bpm'];length=round(spec['bars']*4*beat*RATE);audio=np.zeros((length,2),dtype=np.float64)
    notes=spec.get('notes') or compose(spec);loop=not spec.get('once');intro=round(spec.get('introBars',0)*4*beat*RATE)
    for index,n in enumerate(notes):
        signal=instrument(n['note'],n['duration']*beat,n['instrument'],index+71)*n['gain']
        start=round(n['beat']*beat*RATE);pan=n['pan'];stereo=np.column_stack((signal*math.sqrt((1-pan)/2),signal*math.sqrt((1+pan)/2)))
        # Carry release tails through the loop point. Intro is played only once.
        end=min(len(stereo),length-start);audio[start:start+end]+=stereo[:end]
        if loop and len(stereo)>end:
            tail=stereo[end:];size=min(len(tail),length-intro);audio[intro:intro+size]+=tail[:size]
    # Small, cyclic room reflections rather than external reverb samples.
    for delay,gain in ((.073,.10),(.137,.06)):
        shift=int(delay*RATE)
        if loop:audio+=np.roll(audio,shift,axis=0)*gain
        else:audio[shift:]+=audio[:-shift]*gain
    audio=np.tanh(audio*1.15)
    audio*=.30/max(.30,float(np.max(np.abs(audio))))
    if spec.get('once'):
        fade=min(RATE*2,length);audio[-fade:]*=np.linspace(1,0,fade)[:,None];audio[:220]*=np.linspace(0,1,220)[:,None]
    # A loop-point seam uses the preceding tail's extrapolated sample, not silence.
    endpoint=intro if intro else 0
    if loop:
        for channel in range(2):
            target=audio[endpoint,channel];start=length-96
            audio[start:,channel]+=np.linspace(0,target-audio[-1,channel],96)
    pcm=np.round(np.clip(audio,-.98,.98)*32767).astype('<i2');blob=pcm.tobytes()
    destination=ROOT/'static/music'/f'{key}.wav'
    with wave.open(str(destination),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(blob)
    return dict(title=spec['title'],file=key+'.wav',seconds=length/RATE,loop=loop,loopStart=intro/RATE,loopEnd=length/RATE,
        peak=round(float(np.max(np.abs(audio))),6),rms=round(float(np.sqrt(np.mean(audio**2))),6),bytes=destination.stat().st_size,
        boundaryDelta=round(float(np.max(np.abs(audio[-1]-audio[endpoint]))),7) if loop else 0,
        clippedSamples=int(np.sum(np.abs(pcm)>=32760)),sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
        credit='Original The Gauntlet composition and synthesized instruments; art/audio/music/LICENSE.txt'),notes

def main():
    global MOTIF
    (ROOT/'static/music').mkdir(exist_ok=True);(HERE/'music').mkdir(exist_ok=True)
    source=HERE/'music/composition.json'
    if not source.exists():source.write_text(json.dumps(dict(version=1,motif=MOTIF,arrangements=TRACKS),indent=2)+'\n')
    composition=json.loads(source.read_text());MOTIF=composition['motif'];arrangements=composition['arrangements']
    manifest=ROOT/'static/music/manifest.json';previous=json.loads(manifest.read_text()).get('tracks',{}) if manifest.exists() else {}
    for key,spec in arrangements.items():
        if not key.replace('-','').isalpha() or not 50<=spec['bpm']<=180 or not 1<=spec['bars']<=32 or spec['bars']*4*60/spec['bpm']>65:raise ValueError('Invalid score dimensions')
        target=ROOT/'static/music'/f'{key}.wav'
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=previous.get(key,{}).get('sha256'):
            if '--replace-modified' not in sys.argv:raise ValueError('Modified music export protected: '+key)
            backup=HERE/'music/manual-backups'/str(time.time_ns());backup.mkdir(parents=True);shutil.copy2(target,backup/target.name)
    records={};scores={}
    for key,spec in arrangements.items():records[key],scores[key]=render(key,spec)
    (ROOT/'static/music/manifest.json').write_text(json.dumps(dict(version=1,sampleRate=RATE,tracks=records),indent=2)+'\n')
    (HERE/'music/scores.json').write_text(json.dumps(dict(version=1,motif=MOTIF,arrangements=arrangements,notes=scores),indent=2)+'\n')
    (HERE/'music/metrics.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Rendered '+str(len(records))+' original musical arrangements; '+str(sum(t['bytes'] for t in records.values()))+' bytes; no samples or Bfxr used for music.')

if __name__=='__main__':main()
