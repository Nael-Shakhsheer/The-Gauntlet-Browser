// Owner-aware cosmetic variants. Never mutate live summon state or gameplay values.
(() => {
 const species=new Set(['lightning_bird','fire_wolf','ice_bear','nature_golem']),packs=new Map(),actors=new Map();
 let room=null,scene='',last=0,epoch='',cursor=0,ends=[];
 const reduced=()=>Boolean(window.GauntletAudio?.visualSettings().reduced||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
 const direction=s=>(Math.round((Math.PI/2-Math.atan2(s.facingY??1,s.facingX??0))/(Math.PI/4))+8)%8;
 function isAscended(s){
  if(s.presentationVersion>=1)return s.ownerAscended===true&&s.appearanceKey==='druid.'+s.abilityId+'.ascended';
  // Compatibility with a local server awaiting its cosmetic packet restart.
  const owner=room?.players?.find(p=>p.id===s.ownerId);return Boolean(owner?.class==='Druid'&&owner.ascended);
 }
 function ensure(id,normal=false){if(!species.has(id))return null;const key=(normal?'normal:':'ascended:')+id;if(!packs.has(key)){const image=new Image(),p={image,error:false};image.onerror=()=>p.error=true;image.src=normal?'/sprites/normal-summon-'+id+'-reactions-v5.png':'/sprites/ascended-summon-'+id+'-v1.png';packs.set(key,p);}return packs.get(key);}
 function reset(){actors.clear();ends=[];room=null;scene='';last=0;epoch='';cursor=0;}
 function observe(r){const now=performance.now(),key=[r.code,r.you,r.stage,r.adventure?.area,r.townInterior].join('|');
  if(key!==scene||now-last>1400||document.hidden)reset();scene=key;last=now;room=r;const live=new Set();
  for(const s of(r.summons||[]).slice(0,32)){live.add(s.id);const old=actors.get(s.id),asc=isAscended(s);ensure(s.abilityId,!asc);const record=old||{hitAt:-Infinity,transformAt:-Infinity};
   if(old&&(s.damageTaken||0)>record.damageTaken)record.hitAt=now;
   if(old&&!record.ascended&&asc)record.transformAt=now;
   Object.assign(record,{...s,damageTaken:s.damageTaken||0,ascended:asc});actors.set(s.id,record);
  }
  const feedback=r.feedback;if(feedback){const fresh=feedback.epoch!==epoch;
   if(!fresh)for(const event of feedback.events||[])if(event.kind==='summon_end'&&event.id>cursor&&event.age<.8&&['druid.'+event.abilityId+'.ascended','druid.'+event.abilityId+'.normal'].includes(event.appearanceKey)){
    const previous=actors.get(event.targetId),normal=event.appearanceKey.endsWith('.normal');ensure(event.abilityId,normal);ends.push({entity:{...previous,...event},normal,at:now-event.age*1000,died:event.died});
   }
   epoch=feedback.epoch;cursor=feedback.cursor;
  }
  for(const id of actors.keys())if(!live.has(id))actors.delete(id);
  ends=ends.filter(e=>now-e.at<700).slice(-12);
 }
 function pose(s){const old=actors.get(s.id),now=performance.now();if(s.hp<=0||s.status==='fallen')return 11;
  if(now-(old?.hitAt??-Infinity)<140)return 10;
  if(now-(old?.transformAt??-Infinity)<300)return 8;
  const attack=s.animationUntil*1000-Date.now();if(attack>0)return attack>210?4:attack>100?5:6;
  if(s.emergeRemaining>.1)return s.emergeRemaining>.75?7:s.emergeRemaining>.35?8:9;
  if(s.moving)return 2+(reduced()?0:Math.floor(now/(s.kind==='golem'?240:150))%2);
  return reduced()?0:Math.floor(now/410)%2;
 }
 function stamp(g,s,x,y,frame,normal=false){const p=ensure(s.abilityId,normal);if(!p)return false;if(!p.image.complete||!p.image.naturalWidth){if(normal)return false;g.save();g.fillStyle='#b4b8a7';g.fillRect(x-2,y-10,4,4);g.restore();return true;}
  const d=direction(s);g.save();g.imageSmoothingEnabled=false;g.drawImage(p.image,frame*96,d*96,96,96,Math.round(x-48),Math.round(y-72),96,96);g.restore();return true;
 }
 function draw(g,s,x,y){return isAscended(s)?stamp(g,s,x,y,pose(s)):performance.now()-(actors.get(s.id)?.hitAt??-Infinity)<140?stamp(g,s,x,y,0,true):false;}
 function ownsEndImpact(effect){return effect.type==='impact'&&!effect.text&&ends.some(e=>performance.now()-e.at<450&&Math.hypot(effect.x-e.entity.x,effect.y-e.entity.y)<2&&effect.color===e.entity.color);}
 function corpseEntries(){return ends.map(e=>({actor:true,depth:e.entity.y+15,draw:g=>{const s=e.entity,scale=s.abilityId==='nature_golem'?2.5:s.abilityId==='ice_bear'?2.15:s.abilityId==='fire_wolf'?1.15:1;g.save();g.globalAlpha=Math.min(1,(700-performance.now()+e.at)/220);g.translate(s.x,s.y);g.scale(scale,scale);if(e.normal&&!e.died&&typeof drawImportedHero==='function')drawImportedHero(g,{...s,status:'alive'},0,0,({lightning_bird:'LightningBird',fire_wolf:'FireWolf',ice_bear:'IceBear',nature_golem:'NatureGolem'})[s.abilityId]);else stamp(g,s,0,0,e.normal?1:e.died?11:9,e.normal);g.restore();}}));}
 document.addEventListener('visibilitychange',()=>{if(document.hidden)reset();});
 window.GauntletAscendedSummons={observe,draw,pose,reset,isAscended,ownsEndImpact,corpseEntries,diagnostics:()=>({packs:packs.size,actors:actors.size,ends:ends.length,decodedBytes:[...packs.values()].reduce((n,p)=>n+(p.image.naturalWidth||0)*(p.image.naturalHeight||0)*4,0),errors:[...packs].filter(([,p])=>p.error).map(([id])=>id)})};
})();
