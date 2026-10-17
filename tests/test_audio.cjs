const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/audio.js'),'utf8');
function harness({saved=null,missing=false,unavailable=false,denied=false,slowName=null}={}){
 let now=1000,hidden=false,played=[],stored,levels=[],listeners={};const live=new Set();
 const metrics=JSON.parse(fs.readFileSync(path.join(__dirname,'../art/audio/metrics.json')));
 const param=()=>({value:0,setTargetAtTime(v){this.value=v;}});
 class Context{
  constructor(){this.state='suspended';this.currentTime=1;this.sampleRate=44100;this.destination={};}
  async resume(){if(denied)throw Error('autoplay');this.state='running';}
  createGain(){const n={gain:param(),connect(){},disconnect(){}};levels.push(n);return n;}
  createDynamicsCompressor(){return {threshold:param(),knee:param(),ratio:param(),attack:param(),release:param(),connect(){}};}
  createStereoPanner(){return {pan:param(),connect(){},disconnect(){}};}
  createBiquadFilter(){return {frequency:param(),Q:param(),connect(){},disconnect(){}};}
  createBuffer(c,n,r){return {getChannelData(){return new Float32Array(n);}};}
  createBufferSource(){return {playbackRate:param(),connect(){},disconnect(){},start(){if(typeof this.buffer==='string')played.push(this.buffer);const key=typeof this.buffer==='string'?this.buffer.split('/').at(-1).replace('.wav',''):'';this.end=this.loop?Infinity:now+(metrics[key]?.seconds||.2)*1000;live.add(this);},stop(){live.delete(this);this.onended?.();}};}
  async decodeAudioData(data){return data;}
 }
 const document={get hidden(){return hidden;},querySelectorAll(){return [];},addEventListener(t,f){listeners[t]=f;}};
 const window={...(unavailable?{}:{AudioContext:Context}),matchMedia:()=>({matches:false}),addEventListener(t,f){listeners[t]=f;}};
 let release;const gate=new Promise(resolve=>{release=resolve;});
 const sandbox={document,window,localStorage:{getItem(){return saved;},setItem(k,v){stored=JSON.parse(v);}},performance:{now:()=>now},fetch:async url=>{if(slowName&&url.endsWith('/'+slowName+'.wav'))await gate;return {ok:!missing,arrayBuffer:async()=>url};}};
 vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/audio-routing.js'),'utf8'),sandbox);vm.runInContext(source,sandbox);
 return {audio:window.GauntletAudio,played,levels,listeners,release,get stored(){return stored;},advance(ms=120){now+=ms;for(const source of [...live])if(source.end<=now){live.delete(source);source.onended?.();}},hide(v){hidden=v;listeners.visibilitychange();}};
}
(async()=>{
 const h=harness(),a=h.audio,hero={id:'me',class:'Knight',x:1000,y:800,hp:150,status:'alive'};
 let cursor=0,room={code:'QA',you:'me',mode:'adventure',stage:1,phase:'combat',adventure:{area:'road'},players:[hero],enemies:[],feedback:{version:1,epoch:'one',cursor:0,events:[]}};
 const observe=(events=[],changes={})=>{h.advance();const f={...room.feedback,events:events.map(e=>({id:++cursor,age:.05,x:1000,y:800,ownerId:'me',heroClass:'Knight',...e})),cursor};room={...room,...changes,feedback:{...f,...changes.feedback}};a.observe(room);};
 observe([{kind:'ability',attackType:'light'}]);assert.equal(h.played.length,0);
 await a.unlock();observe();assert.equal(h.played.length,0,'activation cannot replay');
 observe([{kind:'ability',attackType:'light'}]);assert.ok(h.played.at(-1).includes('knight-light'));
 const n=h.played.length;h.advance();a.observe(room);assert.equal(h.played.length,n,'stable IDs exactly once');
 observe([], {players:[{...hero,animationUntil:999}]});assert.equal(h.played.length,n,'no input/pose-derived cast');
 await a.ensure('wizard-special');observe([{kind:'ability',attackType:'special',heroClass:'Wizard'}]);assert.ok(h.played.at(-1).includes('wizard-special'));
 observe([{kind:'hurt'},{kind:'down'},{kind:'revive'}]);for(const cue of ['hurt','down','revive'])assert.ok(h.played.includes('audio/'+cue+'.wav'));
 h.advance(1000);const before=h.played.length;observe([{kind:'ability',attackType:'ultimate'}]);assert.equal(h.played.length,before,'reconnect baseline');
 h.hide(true);observe([{kind:'down'}]);h.hide(false);observe();assert.equal(h.played.length,before,'hidden events discarded');
 observe([{kind:'ability',attackType:'ultimate'}],{adventure:{area:'tower_1',dungeon:{id:'tower',type:'tower',floor:1}},feedback:{epoch:'two'}});assert.equal(h.played.length,before,'travel drops combat');
 assert.equal(a.diagnostics().ambience,'tower');
 observe([],{adventure:{area:'tower_2',dungeon:{id:'tower',type:'tower',floor:2}},feedback:{epoch:'three'}});
 assert.equal(a.diagnostics().ambience,'tower');
 assert.equal(a.spatial(1800,800).gain,0);assert.ok(a.spatial(1400,800).gain<.3);assert.equal(a.spatial(1000,800).gain,1);assert.ok(Math.abs(a.spatial(1400,800).pan)<=.65);
 const input=(selector,extra)=>h.listeners.input({target:{matches:s=>s===selector,...extra}});
 input('[data-audio-mute]',{checked:true});const muted=h.played.length;observe([{kind:'down'}]);assert.equal(h.played.length,muted);
 assert.ok(a.drainVisuals().some(e=>e.kind==='down'),'muted events remain visual');
 assert.equal(a.diagnostics().ambience,null);input('[data-audio-mute]',{checked:false});observe();assert.equal(h.played.length,muted);
 input('[data-reduced-effects]',{checked:true});input('[data-screen-shake]',{value:'off'});assert.equal(a.visualSettings().reduced,true);assert.equal(a.visualSettings().shake,'off');
 assert.equal(h.stored.version,3);
 a.reset();for(let i=0;i<50;i++)a.play('knight-light',{priority:0,group:'spam',owner:String(i),interval:0});
 assert.equal(a.diagnostics().voices,6,'decoration ceiling');
 assert.equal(a.play('down',{priority:6,interval:0}),true);assert.ok(a.diagnostics().voices<=10);
 for(let i=0;i<30;i++)a.play('down',{priority:6,owner:String(i),interval:0});assert.equal(a.diagnostics().voices,10);
 const migrated=harness({saved:'{"volume":0.3,"muted":true}'});await migrated.audio.unlock();assert.equal(migrated.audio.diagnostics().settings.effects,.3);assert.equal(migrated.audio.play('loot'),false);
 for(const options of [{unavailable:true},{missing:true},{denied:true}]){const bad=harness(options);await bad.audio.unlock();assert.equal(bad.audio.play('loot'),false);}
 for(const invalidation of ['none','travel','hide','mute','timeout']){
  const cold=harness({slowName:'quest-accept'});await cold.audio.unlock();
  const base={...room,feedback:{version:1,epoch:'cold',cursor:0,events:[]}};cold.audio.observe(base);cold.advance(100);
  const event={kind:'quest_accept',id:1,age:.05,ownerId:'me',personal:true,x:1000,y:800};
  const accepted={...base,feedback:{version:1,epoch:'cold',cursor:1,events:[event]}};cold.audio.observe(accepted);
  assert.equal(cold.audio.diagnostics().pending,1,'cold accepted outcome waits briefly');
  if(invalidation==='travel')cold.audio.observe({...base,adventure:{area:'other'},feedback:{epoch:'new',cursor:0,events:[]}});
  if(invalidation==='hide')cold.hide(true);
  if(invalidation==='mute')cold.listeners.input({target:{matches:s=>s==='[data-audio-mute]',checked:true}});
  if(invalidation==='timeout')cold.advance(251);
  cold.release();for(let i=0;i<20;i++)await Promise.resolve();
  assert.equal(cold.played.filter(n=>n.endsWith('/quest-accept.wav')).length,invalidation==='none'?1:0,'cold cue '+invalidation);
  cold.audio.observe(accepted);for(let i=0;i<10;i++)await Promise.resolve();
  assert.equal(cold.played.filter(n=>n.endsWith('/quest-accept.wav')).length,invalidation==='none'?1:0,'no deferred replay '+invalidation);
  assert.equal(cold.audio.diagnostics().pending,0);
 }
 const bank=JSON.parse(fs.readFileSync(path.join(__dirname,'../art/audio/sounds.json')));
 for(const name of Object.keys(bank.sounds)){const wav=fs.readFileSync(path.join(__dirname,'../static/audio',name+'.wav'));assert.equal(wav.toString('ascii',0,4),'RIFF');assert.equal(wav.readUInt32LE(24),44100);assert.equal(wav.readUInt32LE(40),wav.length-44);assert.equal(wav.readInt16LE(44),0);assert.equal(wav.readInt16LE(wav.length-2),0);}
 console.log('Audio: authoritative exactly-once events, silent baselines, dungeon scenes, world-distance mix, priorities/caps, mute, visuals, migration, autoplay/failures and '+Object.keys(bank.sounds).length+' WAVs passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});

