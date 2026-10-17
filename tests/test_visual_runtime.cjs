const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let now=1000,hidden=false,reduced=false;const listeners={},requests=[];
class Image{constructor(){this.complete=true;this.naturalWidth=864;}set src(p){assert.ok(fs.existsSync('static'+p));requests.push(p);}}
const box={Image,fetch:async p=>({ok:true,json:async()=>JSON.parse(fs.readFileSync('static'+p,'utf8').replace(/^\uFEFF/,''))}),performance:{now:()=>now},window:{matchMedia:()=>({matches:false}),GauntletAudio:{sceneKey:r=>r.code,visualSettings:()=>({reduced})}},document:{currentScript:null,get hidden(){return hidden;},addEventListener:(k,f)=>{(listeners[k]??=[]).push(f);},createElement:()=>({})}};
vm.createContext(box);for(const file of ['ability-animations','ascended-sprites','combat-visuals','region-sprites'])vm.runInContext(fs.readFileSync('static/'+file+'.js','utf8'),box);
const {GauntletAscendedSprites:a,GauntletAbilityAnimations:m,GauntletCombatVisuals:v,GauntletRegionSprites:r}=box.window;
assert.equal(requests.length,0,'All new form and region sheets are demand loaded');
const hero={id:'h',class:'Wizard',ascended:true,status:'alive',x:200,y:200,connected:true,moving:true,facingX:1,facingY:0};
const room={code:'QA',you:'h',stage:1,phase:'combat',adventure:{area:'road'},players:[hero],effects:[]};
a.observe(room);assert.equal(a.pose(hero).frame<3,true,'Floating Wizard never uses footfalls');
for(let i=0;i<20;i++){hero.x+=3;now+=80;a.observe(room);}assert.ok(a.diagnostics().trails<=4);
hero.x+=500;a.observe(room);assert.equal(a.diagnostics().trails,0,'No trail across a correction');
const c={id:'cast',heroClass:'Wizard',stage:1,kind:'ascend_wizard',attackType:'special',duration:1.1,elapsed:.7,releaseAt:.6,released:false,visual:{family:'lightning',shape:'circle'}};hero.abilityAnimation=c;m.observe(room);assert.equal(a.pose(hero).frame,6,'Wait for authoritative release');
c.released=true;m.observe(room);assert.equal(a.pose(hero).frame,7);c.cancelled=true;m.observe(room);assert.equal(a.pose(hero).frame,8,'Cancellation has no attack release');
room.effects=Array.from({length:100},(_,i)=>({...c,id:'c'+i,type:'ability_cast',elapsed:0,ownerId:'h'}));v.observe(room);assert.ok(v.diagnostics().casts<=32);
assert.equal(r.select({id:'channel_west'},{chapter:[{found:['channel_west']}]}).i,11);assert.equal(r.select({kind:'travel_shrine',shrine:'watch',active:true},{}).i,5);
hidden=true;for(const f of listeners.visibilitychange)f();assert.equal(a.diagnostics().trails,0);assert.equal(v.diagnostics().casts,0);
const app=fs.readFileSync('static/app.js','utf8');assert.ok(app.indexOf('GauntletCombatVisuals?.front')<app.lastIndexOf('GauntletCombatEnvironment.warnings'));
console.log('Visual runtime: lazy assets, float poses, confirmed/cancelled release, bounded trails/casts, stateful props, hidden cleanup and warning order pass.');
