const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let now=1000;const calls=[];
class Image {constructor(){this.complete=true;}set src(v){this.srcPath=v;const png=fs.readFileSync('static'+v);this.naturalWidth=png.readUInt32BE(16);}}
const s={Image,window:{},performance:{now:()=>now},Date,document:{createElement(){return {getContext(){return ctx;}}}}};
const ctx=new Proxy({}, {get:(_t,k)=>(...args)=>calls.push([k,...args]),set:()=>true});
vm.runInNewContext(fs.readFileSync('static/combat-environment.js','utf8'),s);
const api=s.window.GauntletCombatEnvironment;
for(const [kind,asset,cell] of [['serpent','serpent',68],['minotaur','minotaur',68],['troll','troll',68],['wolf','wolf',68],['spider','spider',68],['draco','draco',68],['monster','chimera',68],['dragon','dragon-adult',116],['troll','shrine-guardian',96]]){
  const version=asset==='dragon-adult'?'v2':'v1';
  for(const mode of ['idle','windup']){
    const file=asset+'-'+mode+(mode==='idle'&&asset!=='dragon-adult'?'':'-'+version);
    const m=JSON.parse(fs.readFileSync('static/sprites/'+file+'.json','utf8').replace(/^\uFEFF/,''));
    assert.equal(m.spritesheet.cell_size.width,cell);assert.equal(m.spritesheet.rows.filter(r=>r.type==='animation').length,8);
  }
  for(const [attack,offset] of [['charge',0],['slam',3],['ranged',6],['draco_projectile',6],['draco_melee',3]]){
    const e={id:asset==='shrine-guardian'?'shrine-guardian':'mob',kind,x:400,y:200,hp:50,moving:false,facingX:1,facingY:0,roleAttack:{kind:attack,startedAt:5,x:500,y:200,progress:.5,remaining:.5}};
    api.observe({code:asset,stage:1,enemies:[e]});calls.length=0;assert.equal(api.enemy(ctx,e,400,200),true);
    let draw=calls.find(c=>c[0]==='drawImage');assert.ok(draw[1].srcPath.includes(asset+'-windup'));assert.equal(draw[2],(offset+1)*cell);
    now+=50;delete e.roleAttack;e.recovering=true;e.animationUntil=Date.now()/1000+.4;
    api.observe({code:asset,stage:1,enemies:[e]});calls.length=0;api.enemy(ctx,e,400,200);draw=calls.find(c=>c[0]==='drawImage');
    assert.ok(draw[1].srcPath.includes(asset+'-idle'));assert.equal(draw[2],6*cell,'Release uses the imported monster attack sequence');
  }
}
console.log('Nine monster assets: directional dimensions, charge/heavy/channel windups and attack releases verified.');
