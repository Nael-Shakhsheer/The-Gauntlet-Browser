"""Read-only size inventory and isolated, reproducible CPU/payload/save benchmarks.

Never opens player save contents. Files under data/ are counted as metadata only.
Benchmark rooms have ordinary stats; their story setup is helper-created, not an
earned campaign or human balance playtest.
"""
import argparse
import ast
import collections
import cProfile
import hashlib
import io
import json
from pathlib import Path
import pstats
import random
import struct
import sys
import tempfile
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests'),str(ROOT/'tools')]


def stats(values):
    a=sorted(values)
    return dict(count=len(a),mean=round(sum(a)/len(a),4),p50=round(a[len(a)//2],4),
                p95=round(a[min(len(a)-1,int(len(a)*.95))],4),maximum=round(a[-1],4))


def inventory():
    from package_game import source_files
    groups=collections.Counter();count=0;images={};duplicates=collections.defaultdict(list)
    for p in ROOT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(ROOT);size=p.stat().st_size;groups[rel.parts[0] if len(rel.parts)>1 else '(root files)']+=size;count+=1
        if rel.parts[0]=='static':
            raw=p.read_bytes();duplicates[hashlib.sha256(raw).hexdigest()].append(rel.as_posix())
            if raw.startswith(b'\x89PNG\r\n\x1a\n'):
                w,h=struct.unpack('>II',raw[16:24]);images['/'+rel.relative_to('static').as_posix()]=dict(bytes=size,width=w,height=h,rgbaBytes=w*h*4)
    packages={}
    for label,runtime in [('portable_source',False),('runtime_candidate',True)]:
        files=source_files(ROOT,runtime_only=runtime)
        packages[label]=dict(files=len(files),bytes=sum(p.stat().st_size for _,p in files),
            groups=dict(collections.Counter({k:sum(p.stat().st_size for n,p in files if n.split('/')[0]==k) for k in sorted({n.split('/')[0] for n,p in files})})))
    # Compare filters on exactly the same current files, even if another artwork
    # edit arrives between inventories. No file is deleted or rewritten.
    old_runtime=[(n,p) for n,p in source_files(ROOT) if not (n.startswith('art/') and not n.startswith('art/audio/')) and not (n.startswith('reports/') and p.suffix.lower() in ('.png','.jpg','.jpeg'))]
    packages['runtime_candidate']['previousFilterBytesOnSameFiles']=sum(p.stat().st_size for _,p in old_runtime)
    scripts={p.name:dict(bytes=p.stat().st_size,dynamicPaths=[line.strip() for line in p.read_text(encoding='utf-8').splitlines() if ('.src' in line or 'fetch(' in line) and len(line)<550]) for p in (ROOT/'static').glob('*.js')}
    return dict(projectFiles=count,projectBytes=sum(groups.values()),groups=dict(groups),packages=packages,
        dependencies=dependencies(),
        staticImages=images,identicalStaticFiles=[v for v in duplicates.values() if len(v)>1],loadDependencies=scripts,
        caveat='Uncompressed candidates, not a measurement of the remote Render deployment. RGBA is a lower-bound decoded-image estimate; GPU copies/canvases/audio are separate. Private data metadata only.')


def dependencies():
    """Code dependency inventory; never imports game or opens configuration secrets."""
    local={p.stem for p in ROOT.glob('*.py')};modules={};external=set()
    for path in ROOT.glob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        names=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names.update(a.name.split('.')[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:names.add(node.module.split('.')[0])
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='__import__' and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):names.add(node.args[0].value.split('.')[0])
        modules[path.name]=dict(local=sorted(names&local),standardLibrary=sorted(names&sys.stdlib_module_names),other=sorted(names-local-sys.stdlib_module_names-{'__future__'}))
        external.update(modules[path.name]['other'])
    return dict(python=modules,nonStandardImports=sorted(external),runtime='Python standard library authoritative HTTP/threaded server; plain browser JS/Canvas/WebAudio; optional cloud adapter uses server-side HTTP.',
                authoring='Node is needed for test/render/audio rebuild tooling, not the playable server. Existing @napi-rs/canvas and vendored Bfxr/sfxr sources/licenses retained.')


def benchmark(temp_root):
    import run_storage
    with tempfile.TemporaryDirectory(prefix='audit-',dir=temp_root) as directory:
        original=run_storage.RunStorage.__init__
        with patch.object(run_storage.RunStorage,'__init__',lambda self,_:original(self,Path(directory)/'singleton')):import game
        import adventure,magic_runes
        from test_expansion import start
        rows=[]
        for area,count,ascended in [('brook',1,False),('hollow',4,False),('dunmere',4,True),('cellar',4,True)]:
            random.seed(41);w,r,players=start(('Knight','Wizard','Druid','Healer')[:count],directory=Path(directory)/area)
            if ascended:
                for p in players:
                    for key in magic_runes.SOURCES:magic_runes.claim(p,key)
                    p['magicRunes'].update(ascended=True,balance=1);magic_runes.refresh(p)
            adventure.enter(w,r,area,'south');p=players[0]
            cpu=[];encode=[];length=[];profile=cProfile.Profile();profile.enable()
            for _ in range(200):
                began=time.perf_counter();s=w.state(r['code'],p['id']);cpu.append((time.perf_counter()-began)*1000)
                began=time.perf_counter();raw=json.dumps(s).encode();encode.append((time.perf_counter()-began)*1000);length.append(len(raw))
            profile.disable();out=io.StringIO();pstats.Stats(profile,stream=out).strip_dirs().sort_stats('cumtime').print_stats(12)
            compact=[];compact_cpu=[]
            if 'include_catalog' in __import__('inspect').signature(w.state).parameters:
                skill_revision=s.get('heroSkillsRevision');compact_profile=cProfile.Profile();compact_profile.enable()
                for _ in range(200):
                    began=time.perf_counter();s=w.state(r['code'],p['id'],include_catalog=False,known_skill_revision=skill_revision);compact_cpu.append((time.perf_counter()-began)*1000);compact.append(len(json.dumps(s).encode()))
                compact_profile.disable()
            tick=[]
            for _ in range(100):
                began=time.perf_counter();w.tick();tick.append((time.perf_counter()-began)*1000)
            save=[]
            for _ in range(8):
                began=time.perf_counter();adventure.save(w,r);save.append((time.perf_counter()-began)*1000)
            rows.append(dict(area=area,party=count,ascended=ascended,stateMs=stats(cpu),encodeMs=stats(encode),stateBytes=stats(length),
                steadyStateBytes=stats(compact) if compact else None,steadyStateMs=stats(compact_cpu) if compact_cpu else None,
                tickMs=stats(tick),saveMs=stats(save),lockAndDisk=w.metrics.view(),profile=out.getvalue()))
        return dict(label='Same seeded helper setup, ordinary stats, 200 profiled full polls +200 optional compact polls,100 ticks,8 durable saves/location. Not network latency or human balance.',rows=rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True);parser.add_argument('--temp-root',type=Path,required=True);args=parser.parse_args()
    try:args.temp_root.resolve().relative_to((ROOT/'data').resolve())
    except ValueError:pass
    else:parser.error('Use disposable storage outside private data/.')
    args.temp_root.mkdir(parents=True,exist_ok=True)
    result=dict(inventory=inventory(),server=benchmark(args.temp_root))
    target=ROOT/'reports'/('COMPLETION_PERFORMANCE_'+args.label+'.json');target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(target.name)
    print(json.dumps(dict(projectBytes=result['inventory']['projectBytes'],packages={k:v['bytes'] for k,v in result['inventory']['packages'].items()},server=[{k:r[k] for k in ('area','stateMs','stateBytes','steadyStateBytes','tickMs','saveMs')} for r in result['server']['rows']]),indent=2))
