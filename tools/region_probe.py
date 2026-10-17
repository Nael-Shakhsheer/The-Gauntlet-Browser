"""Normal-stat encounter probes in authored expansion locations.

Ordinary shop kit, legacy three-ability benchmark, no boosted HP/damage; automated
controller, not human playtesting or an earned campaign. Boss setup is labelled.
"""
import json
import argparse
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'tools')]
import run_storage
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--temp-root',type=Path,default=Path(__file__).resolve().parents[1]/'.test-tmp');args=parser.parse_args();args.temp_root.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(dir=args.temp_root) as temp:
    original=run_storage.RunStorage.__init__
    with patch.object(run_storage.RunStorage,'__init__',lambda self,_path:original(self,Path(temp)/'singleton')):import game
import chapter_probe,adventure,region_content,chapter_flow
rows=[]
for location,heroes,companion in [('brook',('Knight',),False),('hollow',('Druid',),False),('watch',('Knight','Healer'),False),('fields',('Knight','Archer','Healer'),False),('mill',('Knight','Wizard','Druid','Healer'),False),('fields',('Healer',),True)]:
    row=chapter_probe.probe(location,heroes,companion=companion,limit=240);rows.append(row)
base_enter=adventure.enter

def boss_enter(world,room,area,*args,**kwargs):
    base_enter(world,room,area,*args,**kwargs)
    if area=='cellar':
        room['enemies']=[] # The approach is pre-cleared ONLY in this boss fixture.
        chapter_flow.ensure(room)['stages']['mill_cellar']='accepted';region_content.begin_cellar(world,room)

for heroes in [('Knight',),('Knight','Healer'),('Knight','Wizard','Druid','Healer')]:
    with patch.object(adventure,'enter',side_effect=boss_enter):row=chapter_probe.probe('cellar',heroes,limit=240)
    row['setup']='Pre-cleared approach and accepted assignment for ordinary-stat boss observation; not earned chapter progress.';rows.append(row)
result=dict(label='Automated normal-stat encounter probes; not human playtesting or an earned campaign',kit='Class weapon, Oakguard, one heal/mana/ward; legacy three abilities; no stat upgrades or Ascension; opening Ultimate recharge 15s',observations=rows)
Path('reports/EXPANSION_ORDINARY_PROBES_2026-10-14.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for row in rows:print(row['location'],row['classes'],row['outcome'],round(row['duration'],2),row['downings'],flush=True)
