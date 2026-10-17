const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const base=path.join(__dirname,'..');let now=0;const loaded=[],calls=[];
class Image{constructor(){this.complete=true;this.naturalWidth=384;}set src(v){this.path=v;loaded.push(v);}}
const sandbox={Image,performance:{now:()=>now},document:{currentScript:null},window:{}};
vm.runInNewContext(fs.readFileSync(path.join(base,'static/projectile-animations.js'),'utf8'),sandbox);
const api=sandbox.window.GauntletProjectiles;
const ctx=new Proxy({}, {get:(_,k)=> (...args)=>calls.push([k,...args]),set:()=>true});
const styles={piercing_volley:'quick_arrow',snare_shot:'snare_arrow',deadeye:'deadeye_arrow',arc_burst:'arc_bolt',frost_lance:'frost_lance',radiant_flask:'radiant_flask',sanctified_throw:'sanctified_vial',briar_burst:'briar_pod',thornshot:'thorn_spike',quickstring:'quickstring_note',life_spark:'life_spark'};
for(const [abilityId,expected] of Object.entries(styles))assert.equal(api.style({side:'hero',abilityId}),expected);
for(const [affinity,expected] of Object.entries({Fire:'fireball',Ice:'ice_comet',Dark:'dark_orb',Arcane:'arcane_orb',Storm:'storm_bolt',Poison:'venom_glob',Nature:'nature_seed'}))assert.equal(api.style({side:'enemy',ownerId:'owner'},{enemies:[{id:'owner',affinity}]}),expected);
assert.equal(api.style({effectKind:'rock'}),'tumbling_rock');assert.equal(api.style({effectKind:'lightning'}),'bird_lightning');
assert.equal(api.style({side:'enemy',class:'Archer',ownerKind:'serpent',affinity:'Nature'}),'nature_seed','Enemy kit cannot replace its elemental attack with a hero arrow');
assert.equal(api.style({side:'enemy',class:'Wizard',ownerKind:'draco',affinity:'Fire'}),'fireball','Element survives owner removal');
assert.equal(loaded.length,0,'No flight sheets download before a projectile needs them');
const catalogue=[];
for(const pack of ['missiles','spells','enemy']){
 const metadata=JSON.parse(fs.readFileSync(path.join(base,'static/sprites/flight-'+pack+'-v1.json'),'utf8').replace(/^\uFEFF/,''));
 const png=fs.readFileSync(path.join(base,'static/sprites/flight-'+pack+'-v1.png'));
 assert.equal(png.readUInt32BE(16),384);assert.equal(png.readUInt32BE(20),metadata.rows.length*96);
 for(const row of metadata.rows){catalogue.push(row.id);for(let frame=0;frame<4;frame++){
  calls.length=0;api.variant(ctx,row.id,10,20,Math.PI/2,frame*(pack==='missiles'?110:80));
  const draw=calls.find(c=>c[0]==='drawImage');assert.equal(draw[2],frame*96);assert.equal(draw[3],row.row*96);assert.equal(draw[6],-row.anchor[0]);
  assert.ok(calls.some(c=>c[0]==='rotate'&&c[1]===Math.PI/2));
 }}
}
assert.equal(catalogue.length,23);
assert.ok(loaded.every(p=>p.startsWith('/sprites/flight-')));assert.equal(loaded.length,3,'Each used flight bank loads once');
const shot={id:'arrow',side:'hero',abilityId:'deadeye',x:55,y:80,vx:0,vy:240};
const room={code:'art',stage:3,phase:'combat',adventure:{area:'clearing'},projectiles:[shot],hazards:[]};
api.observe(room);now=120;calls.length=0;api.draw(ctx,shot);
assert.equal(calls.find(c=>c[0]==='drawImage')[2],96);
api.observe(room);now=240;calls.length=0;api.draw(ctx,shot);
assert.equal(calls.find(c=>c[0]==='drawImage')[2],192,'polling must preserve animation age');
assert.ok(calls.some(c=>c[0]==='rotate'&&c[1]===Math.PI/2),'vertical flight uses zero vx correctly');
room.adventure.area='camp';api.observe(room);calls.length=0;api.draw(ctx,shot);assert.equal(calls.find(c=>c[0]==='drawImage')[2],0,'area change clears flight clocks');
const hazard={id:'rain',side:'hero',kind:'arrow_rain',x:400,y:200,radius:110,active:false,windupLeft:.25};
room.hazards=[hazard];api.observe(room);calls.length=0;api.rain(ctx,room);
assert.ok(calls.some(c=>c[0]==='drawImage'&&c[3]===288),'Rain of Arrows draws the actual arrow row');
assert.ok(!calls.some(c=>c[0]==='fillRect'),'no impact sparks before server activation');
const metadata=JSON.parse(fs.readFileSync(path.join(base,'static/sprites/flight-missiles-v1.json'),'utf8').replace(/^\uFEFF/,''));
const deadeye=metadata.rows.find(p=>p.id==='deadeye_arrow'),quick=metadata.rows.find(p=>p.id==='quick_arrow');assert.ok(deadeye.nativeLength>=quick.nativeLength*2);
// Authoring sources are optional on a fresh checkout; runtime coverage above is portable.
const manifestPath=path.join(base,'art/projectile-animations/manifest.json');
if(fs.existsSync(manifestPath)){
 const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8').replace(/^\uFEFF/,''));assert.equal(manifest.length,92);
 for(const id of ['radiant_flask','sanctified_vial'])assert.ok(manifest.filter(p=>p.id===id).every(p=>p.source==='overrides'));
}
console.log('Projectile checks passed: 23 designs, 92 frames, real arrows/ultimates, rotation, persistent clocks and elemental mapping.');
