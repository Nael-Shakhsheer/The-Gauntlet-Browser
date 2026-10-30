/* Original score playback. One current track + one fading track, bounded cache. */
(() => {
 'use strict';
 const now=()=>performance.now(),MAX_BYTES=32*1024*1024;
 function create(host){
  let room=null,lastAt=0,engageUntil=0,nearbySince=0,activitySince=0,lastActivity=0,victoryUntil=0,manifest=null,manifestPromise=null;
  let current=null,fading=null,loading=null,wanted='menu',previewUntil=0,previewKey=null,disabled=false;
  const cache=new Map(),failed=new Set(),positions=new Map();
  const stats={starts:0,transitions:0,failures:0,maxLoops:0,maxDecodedBytes:0};
  function bytes(){return [...cache.values()].reduce((a,b)=>a+(b.length||0)*(b.numberOfChannels||2)*4,0);}
  function trim(){for(const key of cache.keys())if(cache.size>2||bytes()>MAX_BYTES){if(key!==current?.key&&key!==fading?.key)cache.delete(key);}}
  function remember(track){if(!track)return;const elapsed=Math.max(0,host.context().currentTime-track.started)+track.offset;positions.set(track.key,elapsed);}
  function end(track,fade=.07){if(!track)return;if(!track.stopping){remember(track);track.stopping=true;}try{track.level.gain.setTargetAtTime(0,host.context().currentTime,Math.max(.001,fade/3));track.source.stop(host.context().currentTime+fade);}catch{}}
  function stop(){end(current);end(fading);current=fading=null;previewUntil=0;trim();}
  async function catalog(){
   if(manifest)return manifest;
   if(!manifestPromise)manifestPromise=fetch('music/manifest.json').then(r=>{if(!r.ok)throw Error('Missing score manifest');return r.json();}).then(data=>{
    if(data.version!==1||!data.tracks||Object.keys(data.tracks).length>16)throw Error('Invalid score manifest');manifest=data.tracks;return manifest;
   }).catch(()=>{stats.failures++;disabled=true;return null;});
   return manifestPromise;
  }
  function base(){
   if(!room||room.phase==='lobby')return 'menu';
   const t=now(),a=room.adventure||{},area=a.area||'';
   if(room.opening||a.opening?.phase||area==='caravan'||area==='last_caravan'||room.encounterType==='opening')return 'caravan';
   if(room.enemies?.some(e=>e.boss)||a.campaignExtension?.objective?.type==='boss'||a.locked&&/boss/.test(room.encounterType||''))return 'boss';
   if(a.campaignExtension?.objective?.type==='defense')return 'combat';
   if(t<victoryUntil||room.phase==='cleared')return positions.get('victory')>=((manifest?.victory?.seconds)||12)?'oakvale':'victory';
   const listener=room.players?.find(p=>p.id===room.you);
   const nearby=room.enemies?.some(e=>listener&&Math.hypot(e.x-listener.x,e.y-listener.y)<340&&(e.bossAttack||e.roleAttack||e.charging||e.hp<e.maxHp));
   if(nearby){if(!nearbySince)nearbySince=t;if(t-nearbySince>900)engageUntil=Math.max(engageUntil,t+5000);}else nearbySince=0;
   if(t<engageUntil&&room.phase==='combat')return 'combat';
   if(room.phase==='town'||room.phase==='peace'||['home','dunmere'].includes(area))return area==='dunmere'?'dunmere':'oakvale';
   if(a.dungeon||/cave_|tower_|cellar/.test(area)||room.region==='cavern'||room.phase==='puzzle')return 'dungeon';
   if(['fields','mill'].includes(area)||a.campaignExtension?.region==='cinder'||area.startsWith('cinder_'))return 'dryfields';
   return 'woodland';
  }
  function note(e){
   const p=room?.players?.find(p=>p.id===room.you);
   const close=!p||!Number.isFinite(e.x)||Math.hypot(e.x-p.x,e.y-p.y)<600;
   if(close&&['hit','hurt','projectile_launch','windup','release','ascended_release'].includes(e.kind)){
    const t=now();if(!activitySince||t-lastActivity>1000)activitySince=t;lastActivity=t;
    if(t-activitySince>=600)engageUntil=t+5000;
   }
   if(e.kind==='complete'&&e.major||e.kind==='enemy_defeat'&&e.boss||e.kind==='quest_report'&&e.objective==='chapter_outcome'){
    if(now()>=victoryUntil)positions.delete('victory');
    victoryUntil=now()+10500;engageUntil=nearbySince=activitySince=lastActivity=0;
   }
  }
  function enabled(){const c=host.context(),s=host.settings();return c&&c.state==='running'&&!document.hidden&&!s.muted&&s.master>0&&s.music>0&&!disabled&&room?.phase!=='defeat'&&(!room||now()-lastAt<1600);}
  async function update(){
   wanted=now()<previewUntil?previewKey:base();
   if(!enabled()){stop();return;}
   if(current?.key===wanted)return;
   if(loading)return;
   const key=wanted;loading=key;
   try{
    const tracks=await catalog(),spec=tracks?.[key];if(!spec||failed.has(key))return;
    if(!/^[a-z-]+\.wav$/.test(spec.file)||!(spec.seconds>0&&spec.seconds<=65))throw Error('Invalid score');
    let buffer=cache.get(key);
    if(!buffer){
     // Stop the oldest fade before allocating a third decoded score.
     end(fading,0);fading=null;
     for(const old of cache.keys())if(old!==current?.key)cache.delete(old);
     const r=await fetch('music/'+spec.file);if(!r.ok)throw Error('Missing track');
     buffer=await host.context().decodeAudioData(await r.arrayBuffer());
     const size=(buffer.length||0)*(buffer.numberOfChannels||2)*4;
     if(size>16*1024*1024||buffer.duration>65)throw Error('Oversized track');
     cache.set(key,buffer);trim();stats.maxDecodedBytes=Math.max(stats.maxDecodedBytes,bytes());
    }
    // A decode may finish after travel, mute, hidden tab or a newer desired state.
    if(key!==wanted||!enabled())return;
    const c=host.context(),source=c.createBufferSource(),level=c.createGain();
    source.buffer=buffer;source.loop=Boolean(spec.loop);source.loopStart=spec.loopStart||0;source.loopEnd=spec.loopEnd||spec.seconds;
    let offset=positions.get(key)||0;
    const openingPhase=room?.adventure?.opening?.phase||room?.opening?.phase;
    if(key==='caravan'&&!positions.has(key)&&openingPhase&&openingPhase!=='arrival')offset=spec.loopStart||0;
    if(spec.loop&&offset>=source.loopEnd)offset=source.loopStart+(offset-source.loopStart)%(source.loopEnd-source.loopStart);
    if(!spec.loop&&offset>=spec.seconds-.1){if(key==='victory')return;offset=0;}
    source.connect(level);level.connect(host.bus());level.gain.value=0;level.gain.setTargetAtTime(.8,c.currentTime,.55);
    end(fading,0);fading=current;end(fading,1.6);
    const record={key,source,level,started:c.currentTime,offset};current=record;
    source.onended=()=>{if(!spec.loop&&!record.stopping)positions.set(key,spec.seconds);source.disconnect();level.disconnect();if(fading===record)fading=null;if(current===record)current=null;trim();};
    source.start(c.currentTime,offset);stats.starts++;stats.transitions++;stats.maxLoops=Math.max(stats.maxLoops,(current?1:0)+(fading?1:0));
   }catch{failed.add(key);stats.failures++;}finally{loading=null;trim();host.changed?.();}
  }
  function observe(r){
   if(r&&room){
    if(r.code!==room.code||r.you!==room.you){stop();positions.delete('caravan');positions.delete('victory');}
    if(r.code!==room.code||r.you!==room.you||r.adventure?.area!==room.adventure?.area||r.feedback?.epoch!==room.feedback?.epoch)engageUntil=nearbySince=activitySince=lastActivity=victoryUntil=0;
   }
   room=r;lastAt=now();update();
  }
  function reset(){stop();positions.delete('caravan');positions.delete('victory');room=null;engageUntil=nearbySince=activitySince=lastActivity=victoryUntil=0;lastAt=now();previewUntil=0;update();}
  function preview(key='oakvale'){previewKey=key;previewUntil=now()+8000;positions.delete(key);update();}
  window.setInterval?.(()=>{if(host.context())update();},400);
  return {observe,note,update,stop,reset,preview,diagnostics:()=>({...stats,state:wanted,track:current?.key||null,loops:(current?1:0)+(fading?1:0),decodedBytes:bytes(),cachedTracks:cache.size,failed:[...failed]})};
 }
 window.GauntletMusic={create};
})();
