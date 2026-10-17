const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const manifest=JSON.parse(fs.readFileSync('static/music/manifest.json'));
function harness(missing=false){
 let ms=1000,hidden=false,setting={master:1,music:.16,muted:false},active=new Set(),sources=[],requests=[];
 const c={state:'running',currentTime:1,sampleRate:48000,createGain(){return {gain:{value:0,setTargetAtTime(){}},connect(){},disconnect(){}};},
  createBufferSource(){const s={loop:false,connect(){},disconnect(){},start(at,offset){this.offset=offset;active.add(this);},stop(at=0){this.stopAt=at;}};sources.push(s);return s;},
  async decodeAudioData(file){const key=file.split('/').at(-1).replace('.wav',''),t=manifest.tracks[key];return {length:Math.round(t.seconds*48000),duration:t.seconds,numberOfChannels:2};}};
 const s={window:{},document:{get hidden(){return hidden;}},performance:{now:()=>ms},fetch:async url=>{requests.push(url);return {ok:!missing,json:async()=>manifest,arrayBuffer:async()=>url};}};
 vm.createContext(s);vm.runInContext(fs.readFileSync('static/music.js','utf8'),s);
 const music=s.window.GauntletMusic.create({context:()=>c,bus:()=>({}),settings:()=>setting});
 function advance(n=500){ms+=n;c.currentTime=ms/1000;for(const source of [...active])if(source.stopAt<=c.currentTime){active.delete(source);source.onended?.();}}
 return {music,setting,requests,active,sources,advance,hide(v){hidden=v;}};
}
const flush=async()=>{for(let i=0;i<15;i++)await Promise.resolve();};
(async()=>{
 const h=harness(),m=h.music;
 m.observe(null);await flush();assert.equal(m.diagnostics().track,'menu');
 const initial=m.diagnostics().starts;for(let i=0;i<10;i++){h.advance(100);m.observe(null);await flush();}assert.equal(m.diagnostics().starts,initial,'polls do not restart music');
 const room={code:'A',phase:'town',players:[{id:'p',x:0,y:0}],you:'p',adventure:{area:'home'},enemies:[]};
 m.observe(room);await flush();assert.equal(m.diagnostics().track,'oakvale');assert.ok(m.diagnostics().loops<=2);
 h.advance(1800);m.observe({...room,phase:'combat',adventure:{area:'road'}});await flush();assert.equal(m.diagnostics().track,'woodland','nearby idle monsters do not imply combat');
 m.note({kind:'hit',x:10,y:0});h.advance(800);m.note({kind:'hit',x:10,y:0});m.observe({...room,phase:'combat',adventure:{area:'road'}});await flush();assert.equal(m.diagnostics().track,'combat');
 for(let i=0;i<6;i++){h.advance(600);m.observe({...room,phase:'combat',adventure:{area:'road'}});await flush();}assert.equal(m.diagnostics().track,'combat','post-combat hold avoids flutter');
 m.observe({...room,phase:'combat',adventure:{area:'cellar'},enemies:[{boss:true}]});await flush();assert.equal(m.diagnostics().track,'boss');
 h.advance(2000);m.observe({...room,phase:'combat',adventure:{area:'tower_2',dungeon:{type:'tower'}},enemies:[]});await flush();assert.equal(m.diagnostics().track,'dungeon');
 m.observe({...room,adventure:{area:'dunmere'}});await flush();assert.equal(m.diagnostics().track,'dunmere');
 m.observe({...room,phase:'combat',adventure:{area:'road',opening:{phase:'first'}}});await flush();assert.equal(m.diagnostics().track,'caravan');
 h.advance(700);h.hide(true);m.stop();h.advance(100);assert.equal(h.active.size,0,'hidden stops loops');h.hide(false);m.observe({...room,phase:'combat',adventure:{area:'road',opening:{phase:'second'}}});await flush();assert.ok(h.sources.at(-1).offset>0,'intro resumes rather than restarting');
 h.setting.muted=true;await m.update();h.advance(100);assert.equal(h.active.size,0,'master mute stops current and fading sources');
 h.setting.muted=false;m.observe(room);await flush();
 for(const area of ['road','cellar','fields','home','dunmere']){h.advance(2000);m.observe({...room,phase:area==='home'||area==='dunmere'?'town':'combat',adventure:{area}});await flush();assert.ok(m.diagnostics().cachedTracks<=2);assert.ok(m.diagnostics().decodedBytes<=32*1024*1024);}
 const bad=harness(true);bad.music.observe(null);await flush();assert.equal(bad.music.diagnostics().track,null);assert.ok(bad.music.diagnostics().failures>0);
 for(const [key,t] of Object.entries(manifest.tracks)){
  const wav=fs.readFileSync('static/music/'+t.file);assert.equal(wav.readUInt16LE(22),2);assert.equal(wav.readUInt32LE(24),22050);assert.equal(wav.length,t.bytes);assert.ok(t.peak<=.31);assert.equal(t.clippedSamples,0);if(t.loop)assert.ok(t.boundaryDelta<.001,key+' seamless boundary');
 }
 console.log('Music: meaningful engagement/hold, menu/town/regions/dungeon/boss/Caravan states, stable playback, crossfades, hidden/mute/resume, missing assets, two-track/32MiB cache and '+Object.keys(manifest.tracks).length+' original exports passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
