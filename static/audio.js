/* Bfxr feedback mixer. Presentation only: no gameplay actions or combat rules. */
(() => {
  'use strict';
  const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
  const reducedMedia=window.matchMedia?.('(prefers-reduced-motion: reduce)');
  let settings={version:3,master:1,music:.16,effects:.4,ambience:.12,ui:.3,muted:false,shake:'reduced',reducedEffects:false};
  try {
    const saved=JSON.parse(localStorage.getItem('gauntlet-audio') || 'null');
    if(saved) {
      settings.effects=clamp(Number.isFinite(saved.effects)?saved.effects:Number.isFinite(saved.volume)?saved.volume:.45);
      settings.ambience=clamp(Number.isFinite(saved.ambience)?saved.ambience:.16);
      for(const key of ['master','music','ui'])if(Number.isFinite(saved[key]))settings[key]=clamp(saved[key]);
      settings.muted=saved.muted===true;settings.reducedEffects=saved.reducedEffects===true;
      if(['off','reduced','normal'].includes(saved.shake))settings.shake=saved.shake;
    }
  } catch {}
  const classes=['knight','rogue','archer','wizard','druid','cleric','bard','healer'];
  const names=['dash','hurt','down','revive','heal','loot','clear','curse','select','interact',
    'ward','metal-impact','wood-impact','stone-impact','enemy-windup','enemy-release','boss-warning','boss-complete',
    'repair','restore','discovery','equip','purchase','ice-cast','ice-impact',
    ...['fire','ice','storm','nature'].map(x=>'summon-'+x),
    ...['village','woodland','chamber','tower','boss','fire','water','landmark'].map(x=>'amb-'+x),
    ...classes.flatMap(c=>['light','light-1','light-2','special','ultimate','impact'].map(t=>c+'-'+t))];
  let context=null,master=null,effectsBus=null,ambienceBus=null,uiBus=null,musicBus=null,loading=null,attempted=false,failures=0;
  let musicDuck=null,ambienceDuck=null,routineDuck=null,duckStarted=0,duckUntil=0,duckRestUntil=0;
  function clearDucking(){
    duckStarted=duckUntil=duckRestUntil=0;
    if(context)for(const bus of [musicDuck,ambienceDuck,routineDuck])if(bus){bus.gain.cancelScheduledValues?.(context.currentTime);bus.gain.setTargetAtTime(1,context.currentTime,.025);}
  }
  function runeDucking(){
    const now=performance.now();
    if(now>=duckUntil){if(now<duckRestUntil)return;duckStarted=now;duckUntil=now+1100;duckRestUntil=now+3200;}
    else duckUntil=Math.min(duckStarted+2200,now+1100);
    // Separate multipliers preserve changes to the user's actual volume sliders.
    // Boss warnings, rescues, major casts and the UI fanfare bypass routineDuck.
    for(const [bus,factor]of [[musicDuck,.62],[ambienceDuck,.65],[routineDuck,.8]])if(bus){
      bus.gain.cancelScheduledValues?.(context.currentTime);bus.gain.setTargetAtTime(factor,context.currentTime,.035);
      bus.gain.setTargetAtTime(1,context.currentTime+(duckUntil-now)/1000,.16);
    }
  }
  const buffers=new Map(),voices=new Map(),rates=new Map(),stats={played:0,dropped:0,events:0,maxVoices:0};
  const inflight=new Map(),failed=new Set(),used=new Map();
  const music=window.GauntletMusic?.create({context:()=>context,bus:()=>musicBus,settings:()=>settings,changed:()=>controls()});
  const extraNames=window.GauntletAudioRouting?.extra||[];
  const allowedNames=new Set([...names,...extraNames]);
  const coreNames=['hurt','down','revive','heal','ward','boss-warning','enemy-windup','enemy-release','clear','boss-complete','ui-nav','ui-confirm','ui-reject','hit-flesh','hit-flesh-1','hit-flesh-2','hit-barrier','hit-significant','defeat-soft','conversation-open','conversation-close','inspect','rune-gain','rune-spend','shrine-activate','quest-report','skill-learn','equip','purchase','loot','restore'];
  let generation=0;const pending=new Map();
  function decodedBytes(){return [...buffers.values()].reduce((n,b)=>n+(b.length||0)*(b.numberOfChannels||1)*4,0);}
  function trimBuffers(){
    for(const [key] of [...used].sort((a,b)=>a[1]-b[1])){
      if(decodedBytes()<=8*1024*1024)break;
      if([...voices.values()].some(v=>v.name===key))continue;
      buffers.delete(key);used.delete(key);
    }
  }
  async function ensure(name,urgent=false){
    if(buffers.has(name))return buffers.get(name);
    if(!context||!allowedNames.has(name)||failed.has(name))return;
    if(inflight.has(name))return inflight.get(name);
    if(inflight.size>=(urgent?6:4))return;
    const task=(async()=>{
      try{const response=await fetch('audio/'+name+'.wav');if(!response.ok)throw Error('Missing cue');
        const b=await context.decodeAudioData(await response.arrayBuffer());if(b.duration>2.05)throw Error('Oversized effect');
        buffers.set(name,b);used.set(name,performance.now());trimBuffers();return b;
      }catch{failed.add(name);failures++;}finally{inflight.delete(name);controls();}
    })();inflight.set(name,task);return task;
  }
  async function warm(list){for(let i=0;i<list.length;i+=4)await Promise.all(list.slice(i,i+4).map(ensure));}
  let roster='';
  function warmRoom(){const heroes=[...new Set((room?.players||[]).map(p=>p.class?.toLowerCase()).filter(c=>classes.includes(c)))];
    const key=heroes.join('|');if(context&&key!==roster){roster=key;return warm(heroes.flatMap(h=>[...['light','light-1','light-2','special','ultimate'].map(t=>h+'-'+t),'ascend-'+h,'ascended-'+h,'ascended-'+h+'-light']));}}
  let room=null,scene='',epoch='',cursor=0,at=0,baseline=true,serial=0,ambience=null,accentAt=0;
  let fallbackSeen=new Set();
  const visualQueue=[];
  const fadingAmbience=new Set();
  let resumeAt=0;
  function sceneKey(r) {
    const d=r.dungeon || r.adventure?.dungeon || r.adventure?.dungeons?.find(d=>d.current) || {};
    return [r.code,r.you,r.mode,r.adventure?.area,typeof d==='string'?d:d.id,d.floor ?? r.dungeonFloor,r.stage,r.townInterior,r.innFloor,r.puzzle?.id,r.feedback?.epoch].join('|');
  }
  function visualSettings(){return {reduced:settings.reducedEffects || Boolean(reducedMedia?.matches),shake:reducedMedia?.matches?'off':settings.shake};}
  function status(){return !window.AudioContext&&!window.webkitAudioContext?'Audio unavailable; visual warnings remain active.':
    settings.muted?'All audio muted.':!context||context.state!=='running'?'Click, tap or press a key to activate audio.':
    loading?'Loading Bfxr cues…':failures||music?.diagnostics().failures?'Some cues or tracks are unavailable; gameplay continues. Refresh to retry.':'Audio ready.';}
  function controls(){
    const set=(selector,fn)=>document.querySelectorAll(selector).forEach(fn);
    set('[data-audio-volume]',e=>{e.value=String(Math.round(settings.effects*100));});
    set('[data-audio-value]',e=>{e.textContent=Math.round(settings.effects*100)+'%';});
    set('[data-ambience-volume]',e=>{e.value=String(Math.round(settings.ambience*100));});
    set('[data-ambience-value]',e=>{e.textContent=Math.round(settings.ambience*100)+'%';});
    set('[data-audio-mute]',e=>{e.checked=settings.muted;});
    set('[data-reduced-effects]',e=>{e.checked=settings.reducedEffects;});
    set('[data-screen-shake]',e=>{e.value=settings.shake;});
    set('[data-audio-status]',e=>{e.textContent=status();});
    for(const key of ['master','music','ui']){set('[data-'+key+'-volume]',e=>{e.value=String(Math.round(settings[key]*100));});set('[data-'+key+'-value]',e=>{e.textContent=Math.round(settings[key]*100)+'%';});}
  }
  function apply(){
    try{localStorage.setItem('gauntlet-audio',JSON.stringify({...settings,volume:settings.effects}));}catch{}
    if(context){master.gain.setTargetAtTime(settings.muted?0:settings.master,context.currentTime,.025);
      effectsBus.gain.setTargetAtTime(settings.effects,context.currentTime,.04);
      ambienceBus.gain.setTargetAtTime(settings.ambience,context.currentTime,.15);
      uiBus.gain.setTargetAtTime(settings.ui,context.currentTime,.04);musicBus.gain.setTargetAtTime(settings.music,context.currentTime,.3);}
    if(settings.muted||!settings.master){generation++;pending.clear();clearDucking();stopVoices();stopAmbience();music?.stop();}music?.update();controls();
  }
  async function unlock(){
    if(document.hidden)return;
    try{
      const C=window.AudioContext || window.webkitAudioContext;
      if(!C){controls();return;}
      if(!context){
        try{context=new C({sampleRate:44100,latencyHint:'interactive'});}catch{context=new C();}
        master=context.createGain();effectsBus=context.createGain();ambienceBus=context.createGain();uiBus=context.createGain();musicBus=context.createGain();
        musicDuck=context.createGain();ambienceDuck=context.createGain();routineDuck=context.createGain();
        for(const bus of [musicDuck,ambienceDuck,routineDuck])bus.gain.value=1;
        const compressor=context.createDynamicsCompressor();compressor.threshold.value=-10;compressor.knee.value=10;compressor.ratio.value=4;
        if(compressor.attack)compressor.attack.value=.004;if(compressor.release)compressor.release.value=.15;
        routineDuck.connect(effectsBus);effectsBus.connect(compressor);compressor.connect(master);ambienceBus.connect(ambienceDuck);ambienceDuck.connect(master);uiBus.connect(master);musicBus.connect(musicDuck);musicDuck.connect(master);
        const ceiling=context.createWaveShaper?.();
        if(ceiling){const curve=new Float32Array(4097);for(let i=0;i<curve.length;i++){const x=i/2048-1,a=Math.abs(x);curve[i]=Math.sign(x)*(a<=.85?a:.85+.13*(1-Math.exp(-(a-.85)/.13)));}ceiling.curve=curve;ceiling.oversample='2x';master.connect(ceiling);ceiling.connect(context.destination);}else master.connect(context.destination);
        master.gain.value=settings.muted?0:settings.master;effectsBus.gain.value=settings.effects;ambienceBus.gain.value=settings.ambience;uiBus.gain.value=settings.ui;musicBus.gain.value=settings.music;
        context.onstatechange=()=>{if(context.state!=='running'){baseline=true;clearDucking();stopVoices();stopAmbience();music?.stop();}controls();};
      }
      if(context.state!=='running')await context.resume();
      if(!attempted){attempted=true;loading=warm(coreNames.filter(n=>allowedNames.has(n)).concat(classes.map(h=>h+'-light')));}
      if(loading){await loading;loading=null;}
      await warmRoom();updateAmbience();music?.observe(room);
    }catch{/* A failed resume or unavailable device cannot interrupt input or polling. */}
    controls();
  }
  function retire(source,fade=.025){
    const voice=voices.get(source);if(!voice)return;
    voices.delete(source);
    resumeAt=Math.max(resumeAt,context.currentTime+fade);
    try{voice.level.gain.setTargetAtTime(0,context.currentTime,.008);source.stop(context.currentTime+fade);}catch{}
  }
  function stopVoices(){for(const source of [...voices.keys()])retire(source);rates.clear();}
  function spatial(x,y,local=false){
    const listener=room?.players?.find(p=>p.id===room.you);
    if(local||!listener||!Number.isFinite(x)||!Number.isFinite(y))return {gain:1,pan:0};
    const distance=Math.hypot(x-listener.x,y-listener.y);
    return {gain:distance>=800?0:Math.pow(1-distance/800,2),pan:clamp((x-listener.x)/500,-.65,.65)};
  }
  function play(name,{gain=.35,x,y,local=false,priority=2,group=name,owner='',pitch=1,bus='effects',interval=90,duck=null}={}){
    if(settings.muted||!settings.master||document.hidden||!context||context.state!=='running'||!(settings[bus]??settings.effects))return false;
    if(!buffers.has(name)){ensure(name);return false;}
    const position=spatial(x,y,local);gain*=position.gain;if(gain<.008)return false;
    // Reserve auditory space around boss warnings and completed rescues.
    // This changes presentation only; every essential visual warning remains.
    // Comfortable source balance and concurrency caps do the work; no repeated heavy ducking.
    const now=performance.now(),key=group+':'+owner;
    if(now-(rates.get(key)??-Infinity)<interval){stats.dropped++;return false;}
    const family=group.startsWith('summon')?'summon':group==='impact'?'impact':group==='light'||group==='projectile'?'ordinary':bus==='ui'?'ui':group;
    const limit=family==='impact'?2:family==='summon'||family==='periodic'||family==='preview'?1:family==='ordinary'?3:family==='ui'?2:10;
    if([...voices.values()].filter(v=>v.family===family).length>=limit&&priority<5){
      const remote=[...voices].find(([,v])=>v.family===family&&!v.local&&v.priority<priority);
      if(local&&remote)retire(remote[0]);else{stats.dropped++;return false;}
    }
    const capacity=priority>=5?10:priority>=3?8:6;
    if(voices.size>=capacity){
      const victim=[...voices].filter(([,v])=>v.priority<priority).sort((a,b)=>a[1].priority-b[1].priority)[0];
      if(!victim){stats.dropped++;return false;}retire(victim[0]);
    }
    try{
      const source=context.createBufferSource(),level=context.createGain();source.buffer=buffers.get(name);used.set(name,now);
      if(source.playbackRate)source.playbackRate.value=clamp(pitch,.97,1.03);
      level.gain.value=clamp(gain);source.connect(level);
      const panner=context.createStereoPanner?.();
      const destination=bus==='ambience'?ambienceBus:bus==='ui'?uiBus:priority>=4?effectsBus:routineDuck;
      if(panner){panner.pan.value=position.pan;level.connect(panner);panner.connect(destination);}
      else level.connect(destination);
      voices.set(source,{priority,level,name,family,local});rates.set(key,now);if(rates.size>512)rates.delete(rates.keys().next().value);stats.played++;stats.maxVoices=Math.max(stats.maxVoices,voices.size);
      source.onended=()=>{voices.delete(source);source.disconnect();level.disconnect();panner?.disconnect();};source.start(Math.max(context.currentTime,resumeAt));if(duck==='rune')runeDucking();return true;
    }catch{return false;}
  }
  function confirmedPlay(name,options,event){
    if(buffers.has(name))return play(name,options);
    if(!context||context.state!=='running'||settings.muted||!settings.master||document.hidden)return;
    const critical=options.priority>=3||event.personal;
    if(!critical||pending.size>=8){ensure(name);return;}
    const token=generation,started=performance.now(),key=token+':'+event.id+':'+name;
    if(pending.has(key))return;pending.set(key,true);
    ensure(name,true).then(buffer=>{
      if(buffer&&token===generation&&performance.now()-started<=250&&(event.age||0)+(performance.now()-started)/1000<=.75)play(name,options);
    }).finally(()=>pending.delete(key));
  }
  function cue(event){
    if(event.silentReward||event.kind==='release'&&event.silentLaunch)return;
    const route=window.GauntletAudioRouting?.route(event,room);
    if(route===false)return;
    if(route){confirmedPlay(route.name,route,event);return;}
    const hero=String(event.heroClass||'wizard').toLowerCase();
    const family=classes.includes(hero)?hero:'wizard';let local=event.ownerId===room?.you || (event.kind==='windup' && event.targetId===room?.you);
    let name,gain=.28,priority=local?3:1,group=event.kind,interval=110,pitch=1;
    switch(event.kind){
      case 'caravan_creak':name='wood-impact';gain=.17;priority=0;interval=2000;break;
      case 'caravan_impact':name='stone-impact';gain=.42;priority=2;local=true;interval=2000;break;
      case 'caravan_gate':name='interact';gain=.26;priority=2;local=true;break;
      case 'caravan_arrival':name='restore';gain=.24;priority=2;local=true;break;
      case 'ability':{
        const category=event.attackType || 'light';name=family+'-'+category;
        if(category==='light'){const variant=event.id%3;name+=variant?'-'+variant:'';gain=local?.37:.20;group='light';interval=local?150:230;}
        else {gain=local?.5:.3;priority=local?4:2;}
        if(event.abilityId==='frost_lance')name='ice-cast';
        if(event.abilityKind==='summon')gain*=.6;
        break;
      }
      case 'hit':name=family+'-impact';gain=event.summon?.05:local?.11:.07;priority=0;group='impact';interval=220;break;
      case 'hurt':name=event.warded?'metal-impact':'hurt';gain=local?.22:.08;priority=local?3:1;group='danger';interval=450;break;
      case 'down':name='down';gain=local?.65:.4;priority=6;interval=0;break;
      case 'revive':name='revive';gain=.48;priority=5;interval=0;break;
      case 'windup':name=event.boss?'boss-warning':'enemy-windup';gain=event.boss?.4:local?.32:.19;priority=event.boss||local?5:1;group=event.boss?'boss-warning':local?'target-warning':'enemy-pack';interval=event.boss?400:300;break;
      case 'release':name='enemy-release';gain=event.boss?.32:.17;priority=event.boss?3:0;group='enemy-pack-release';interval=200;break;
      case 'boss_phase':name='boss-warning';gain=.55;priority=6;interval=0;break;
      case 'complete':case 'quest':name=event.major?'boss-complete':'clear';gain=.5;priority=5;interval=250;break;
      case 'summon':name='summon-'+({Fire:'fire',Ice:'ice',Storm:'storm',Nature:'nature'}[event.affinity]||'nature');gain=.32;priority=local?3:1;group='summon';interval=220;break;
      case 'summon_attack':name='druid-light';gain=.12;priority=0;group='summon-pack';interval=350;break;
      default:name=({heal:'heal',ward:'ward',dash:'dash',loot:'loot',curse:'curse',equip:'equip',purchase:'purchase',repair:'repair',restore:'restore',discovery:'discovery',wave:'interact',travel:'interact',encounter:'boss-warning',rest:'restore',material:'stone-impact'})[event.kind];
    }
    if(!name)return;
    if(event.kind==='hit'&&event.element==='Ice')name='ice-impact';
    if(event.kind==='loot'&&['epic','legendary'].includes(String(event.rarity).toLowerCase()))name='discovery';
    if(event.kind==='material')name=event.material==='crate'?'wood-impact':'stone-impact';
    if(['hit','summon_attack'].includes(event.kind))pitch=1+((event.id%5)-2)*.006;
    if(['heal','ward'].includes(event.kind)) {priority=local?3:1;gain=local?.3:.16;group='restoration';interval=230;}
    confirmedPlay(name,{gain,x:event.x,y:event.y,local:event.personal||local,priority,group,owner:priority>=3?event.ownerId:'',interval,pitch},event);
  }
  function receive(event){
    stats.events++;music?.note(event);cue(event);
    if(event.age<=.6 || event.age===undefined){visualQueue.push({...event,receivedAt:performance.now()});if(visualQueue.length>48)visualQueue.shift();}
  }
  function fallback(r,old){
    for(const effect of r.effects||[]){
      if(fallbackSeen.has(effect.id))continue;fallbackSeen.add(effect.id);
      if(effect.type==='ability_cast')receive({...effect,id:++serial,kind:'ability'});
      else if(['dash','heal','puzzle_solved','ambush'].includes(effect.type))receive({...effect,id:++serial,kind:{puzzle_solved:'complete',ambush:'boss_phase'}[effect.type]||effect.type});
    }
    if(fallbackSeen.size>256)fallbackSeen=new Set((r.effects||[]).map(e=>e.id));
    if(!old)return;
    for(const p of r.players||[]){const before=old.players?.find(a=>a.id===p.id);if(!before||before.class!==p.class)continue;
      if(p.status!==before.status)receive({...p,ownerId:p.id,id:++serial,kind:p.status==='alive'?'revive':'down'});
      else if(p.hp<before.hp||p.damageTaken>before.damageTaken)receive({...p,ownerId:p.id,id:++serial,kind:'hurt'});
    }
  }
  function atmosphere(r){
    if(!r||r.phase==='lobby'||r.phase==='defeat'||r.phase==='cleared')return null;
    const d=r.dungeon||r.adventure?.dungeon||r.adventure?.dungeons?.find(d=>d.current);
    if(r.enemies?.some(e=>e.boss)||r.adventure?.locked&&!d)return 'boss';
    if(d?.type==='tower')return 'tower';
    if(d||r.region==='cavern'||r.phase==='puzzle'||r.adventure?.area==='cellar')return 'chamber';
    if(['dunmere','fields','mill'].includes(r.adventure?.area)||r.adventure?.campaignExtension?.region==='cinder'||r.adventure?.area?.startsWith('cinder_'))return 'dry';
    if(r.phase==='town'||r.phase==='peace'||r.adventure?.area==='home')return 'village';
    return 'woodland';
  }
  function stopAmbience(){for(const old of [...fadingAmbience,...(ambience?[ambience]:[])]){try{old.source.stop();}catch{}old.level.disconnect();old.filter.disconnect();}fadingAmbience.clear();ambience=null;}
  function updateAmbience(){
    const kind=atmosphere(room);
    if(!context||context.state!=='running'||document.hidden||settings.muted||!settings.master||!settings.ambience||!kind){stopAmbience();return;}
    if(ambience?.kind===kind)return;
    try{
      const source=context.createBufferSource(),level=context.createGain(),filter=context.createBiquadFilter();
      const buffer=context.createBuffer(1,context.sampleRate*3,context.sampleRate),data=buffer.getChannelData(0);
      let seed=31,previous=0;
      for(let i=0;i<data.length;i++){seed=(Math.imul(seed,1664525)+1013904223)|0;previous=previous*.94+((seed>>>0)/4294967296-.5)*.018;data[i]=previous*Math.min(1,i/500,(data.length-1-i)/500);}
      source.buffer=buffer;source.loop=true;filter.type='bandpass';filter.frequency.value={village:480,woodland:680,chamber:280,tower:390,boss:240,dry:340}[kind];filter.Q.value=.5;
      source.connect(filter);filter.connect(level);level.connect(ambienceBus);level.gain.value=0;level.gain.setTargetAtTime(.65,context.currentTime,.5);
      const old=ambience;const created=ambience={source,level,filter,kind};
      source.onended=()=>{source.disconnect();filter.disconnect();level.disconnect();fadingAmbience.delete(created);};source.start();
      for(const fading of fadingAmbience){try{fading.source.stop();}catch{}}fadingAmbience.clear();
      if(old){fadingAmbience.add(old);old.level.gain.setTargetAtTime(0,context.currentTime,.35);old.source.stop(context.currentTime+1.2);}
      accentAt=performance.now()+6000;
      warm([kind==='dry'?'amb-dry':'amb-'+kind,kind==='chamber'?'amb-droplet':kind==='tower'?'amb-creak':'amb-leaves']);
    }catch{stopAmbience();}
  }
  function accents(now){
    if(!ambience||now<accentAt)return;accentAt=now+13000+(serial++%4)*3000;
    if(['combat','boss'].includes(music?.diagnostics().state)||[...voices.values()].some(v=>v.priority>=4))return;
    const accents={village:['amb-village','amb-tools'],woodland:['amb-leaves','amb-woodland','amb-wildlife'],chamber:['amb-chamber','amb-droplet'],tower:['amb-tower','amb-creak'],dry:['amb-dry','amb-creak'],boss:['amb-boss']};
    const choices=accents[ambience.kind]||['amb-woodland'];play(choices[serial%choices.length],{bus:'ambience',gain:.10,priority:0,group:'atmosphere',interval:10000,local:true});
    const listener=room?.players?.find(p=>p.id===room.you);
    if(!listener||room.townInterior)return;
    const feature=(room.adventure?.features||[]).filter(f=>/altar|repair|campfire|hearth|brook|sluice|channel|well|spring|attune_/.test(f.id))
      .sort((a,b)=>Math.hypot(a.x-listener.x,a.y-listener.y)-Math.hypot(b.x-listener.x,b.y-listener.y))[0];
    if(feature)play(/altar|attune_/.test(feature.id)?'amb-landmark':/repair|brook|sluice|channel|well|spring/.test(feature.id)?'amb-water':'amb-fire',{bus:'ambience',gain:.07,x:feature.x,y:feature.y,priority:0,group:'landmark',interval:10000});
  }
  function observe(r){
    const now=performance.now(),key=sceneKey(r),f=r.feedback;
    const liveTravel=!baseline&&room&&key!==scene&&now-at<=750&&!document.hidden;
    const initialize=baseline||!room||key!==scene||f?.epoch!==epoch||now-at>750||document.hidden;
    const old=room;room=r;scene=key;at=now;baseline=document.hidden;epoch=f?.epoch;
    if(initialize){generation++;pending.clear();clearDucking();cursor=f?.cursor||0;fallbackSeen=new Set((r.effects||[]).map(e=>e.id));visualQueue.length=0;stopVoices();
      if(liveTravel){const arrival=f?.events?.find(e=>['caravan_arrival','portal_arrive'].includes(e.kind)&&e.age<=.5);if(arrival)receive(arrival);else {const travel=f?.events?.find(e=>e.kind==='travel'&&e.age<=.5);if(travel)receive(travel);}}}
    else if(f?.version===1){
      const events=(f.events||[]).filter(e=>e.id>cursor&&e.id<=f.cursor).sort((a,b)=>a.id-b.id);
      const launches=new Set(events.filter(e=>e.kind==='projectile_launch'&&!e.summon).map(e=>e.ownerId+':'+e.abilityId));
      const hostileReleases=new Set(events.filter(e=>e.kind==='projectile_launch'&&e.side==='enemy').map(e=>e.ownerId));
      const impacts=new Set(events.filter(e=>e.kind==='projectile_impact').map(e=>e.ownerId+':'+e.targetId));
      const rewards=new Set(events.filter(e=>['rune_gain','quest_report','shrine_activate','ascension'].includes(e.kind)).map(e=>e.causeId).filter(Boolean));
      for(const e of events){if(e.kind==='ability'&&(e.attackType==='light'||e.abilityId==='frost_lance')&&launches.has(e.ownerId+':'+e.abilityId))e.silentLaunch=true;if(e.kind==='hit'&&impacts.has(e.ownerId+':'+e.targetId))e.silentImpact=true;}
      for(const e of events){
        if(e.kind==='release'&&hostileReleases.has(e.ownerId))e.silentLaunch=true;
        if(e.kind==='projectile_impact'){
          // Current packets emit the collision immediately before its damage.
          // Match the following hit, not another attack by the same owner later
          // in this snapshot; summon impact then shares the summon voice bucket.
          const hit=e.targetId&&events.find(h=>h.id>e.id&&h.kind==='hit'&&h.ownerId===e.ownerId&&h.targetId===e.targetId);
          if(hit){e.significant=Boolean(hit.significant);e.summon=Boolean(e.summon||hit.summon);}
        }
        if(['discovery','quest','complete','purchase','equip'].includes(e.kind)&&rewards.has(e.causeId))e.silentReward=true;
        if(e.kind==='material'&&events.some(p=>p.kind==='projectile_impact'&&p.material&&Math.hypot(e.x-p.x,e.y-p.y)<60))e.silentReward=true;
      }
      for(const event of events)if(event.age<=.75){if(['rune_gain','quest_report','shrine_activate'].includes(event.kind)&&events.some(e=>e.kind==='magic_acquired'&&e.ownerId===r.you)&&event.ownerId===r.you)event.silentReward=true;receive(event);}
      cursor=Math.max(cursor,f.cursor);
    }else fallback(r,old);
    warmRoom();music?.observe(r);updateAmbience();accents(now);
  }
  function reset(){generation++;pending.clear();clearDucking();room=null;scene='';epoch='';cursor=0;baseline=true;visualQueue.length=0;stopVoices();stopAmbience();music?.reset();}
  function drainVisuals(){return visualQueue.splice(0);}
  function suspend(){generation++;pending.clear();clearDucking();baseline=true;visualQueue.length=0;stopVoices();stopAmbience();music?.stop();}
  window.GauntletAudio={observe,reset,unlock,play,sceneKey,spatial,visualSettings,drainVisuals,
    ensure,requestOutcome:(accepted)=>{play(accepted?'ui-confirm':'ui-reject',{bus:'ui',gain:accepted?.12:.16,local:true,priority:2,group:'request-outcome',interval:400});},
    diagnostics:()=>({...stats,voices:voices.size,ambience:ambience?.kind||null,settings:{...settings},failures,decodedBytes:decodedBytes(),inflight:inflight.size,pending:pending.size,runeDuckMs:Math.max(0,duckUntil-performance.now()),music:music?.diagnostics()})};
  document.addEventListener('pointerdown',e=>{if(e.isTrusted!==false)unlock();},{capture:true,passive:true});
  document.addEventListener('keydown',e=>{if(!e.repeat&&e.isTrusted!==false)unlock();},{capture:true});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)suspend();});window.addEventListener('blur',suspend);
  document.addEventListener('input',e=>{
    generation++;pending.clear();
    if(e.target.matches('[data-audio-volume]'))settings.effects=clamp(Number(e.target.value)/100);
    if(e.target.matches('[data-ambience-volume]'))settings.ambience=clamp(Number(e.target.value)/100);
    if(e.target.matches('[data-audio-mute]'))settings.muted=e.target.checked;
    if(e.target.matches('[data-reduced-effects]'))settings.reducedEffects=e.target.checked;
    if(e.target.matches('[data-screen-shake]'))settings.shake=e.target.value;
    for(const key of ['master','music','ui'])if(e.target.matches('[data-'+key+'-volume]'))settings[key]=clamp(Number(e.target.value)/100);
    apply();updateAmbience();
  });
  document.addEventListener('click',async e=>{
    if(e.target.closest('[data-audio-open]'))window.openInfo?.('audioDialog');
    const preview=e.target.closest('[data-cue-preview]');
    const score=e.target.closest('[data-music-preview]');
    if(score){await unlock();music?.preview(score.dataset.musicPreview||'oakvale');}
    else if(preview||e.target.closest('[data-audio-test]')){await unlock();const name=preview?.dataset.cuePreview||'loot';if(inflight.size>=6)await Promise.race([...inflight.values()]);await ensure(name,true);play(name,{gain:name==='boss-warning'?.4:name==='revive'?.48:.17,priority:4,group:'preview',interval:250,local:true,bus:name.startsWith('amb-')?'ambience':name.startsWith('ui-')?'ui':'effects'});}
    else if(e.target.closest('[data-close],[data-guide],#openSettings,summary,#frontSettings,#frontPlay,#frontContinue,#adventureMapButton,#adventureJournalButton,#togglePouch,#toggleChat'))play('ui-nav',{gain:.12,bus:'ui',priority:1,local:true,group:'ui-navigation',interval:100});
  });
  controls();
})();
