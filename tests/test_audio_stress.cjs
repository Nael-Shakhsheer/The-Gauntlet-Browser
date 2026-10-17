/* A three-minute synthetic authoritative-event trace; not a balance/listening test. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const preamble=fs.readFileSync(path.join(__dirname,'test_audio.cjs'),'utf8').split('(async()=>{')[0];
const harness=Function('require','__dirname',preamble+'\nreturn harness;')(require,__dirname);
(async()=>{
 const h=harness(),a=h.audio;await a.unlock();
 const bank=JSON.parse(fs.readFileSync('art/audio/sounds.json'));for(const name of Object.keys(bank.sounds))await a.ensure(name);
 const heroes=['Knight','Archer','Druid','Healer'],players=heroes.map((hero,i)=>({id:'p'+i,class:hero,x:100+i*60,y:100,hp:100,status:'alive'}));
 let id=0,room={code:'stress',you:'p0',phase:'combat',players,enemies:[],feedback:{version:1,epoch:'stress',cursor:0,events:[]}};a.observe(room);
 let sent=0;
 for(let tick=1;tick<=1800;tick++){
  h.advance(100);const events=[];
  const add=e=>events.push({id:++id,age:.03,x:160,y:100,ownerId:'p0',heroClass:'Knight',...e});
  if(tick%5===0)for(let i=0;i<4;i++){
   const abilityId='stress-'+i;add({kind:'ability',attackType:'light',abilityId,ownerId:'p'+i,heroClass:heroes[i],ascended:tick>800});
   if(i)add({kind:'projectile_launch',family:['blade','arrow','nature','sacred'][i],side:'hero',abilityId,ownerId:'p'+i,heroClass:heroes[i],ascended:tick>800});
   for(let target=0;target<6;target++)add({kind:'hit',material:'flesh',targetId:'e'+target,ownerId:'p'+i,heroClass:heroes[i]});
  }
  if(tick%3===0){add({kind:'hurt'});add({kind:'hit',summon:true});add({kind:'projectile_launch',summon:true,family:'lightning',side:'hero',ownerId:'p2',heroClass:'Druid'});}
  if(tick%80===0)add({kind:'windup',boss:true,targetId:'p0'});
  if(tick%600===0)add({kind:'down'});if(tick%600===20&&tick>600)add({kind:'revive'});
  if(tick===800)add({kind:'ascension',personal:true});
  room={...room,feedback:{...room.feedback,cursor:id,events}};a.observe(room);sent+=events.length;
  assert.ok(a.diagnostics().voices<=10);assert.ok(a.diagnostics().decodedBytes<=8*1024*1024);
 }
 const summary={seconds:180,actors:4,events:sent,...a.diagnostics(),note:'Synthetic event/mixer stress with timed mocked sources; no acoustic or physical-device judgment.'};
 fs.writeFileSync('reports/AUDIO_STRESS_2026-10-16.json',JSON.stringify(summary,null,2)+'\n');
 assert.ok(summary.played>100);assert.equal(h.played.filter(n=>n==='audio/down.wav').length,3);
 console.log('180s four-player/summon/AOE/DOT stress: '+summary.events+' events, '+summary.played+' voices started, peak '+summary.maxVoices+' voices; exactly-once down cues and bounded decoded cache.');
})().catch(e=>{console.error(e);process.exitCode=1;});
