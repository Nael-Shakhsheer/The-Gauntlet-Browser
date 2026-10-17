// Real PNG/canvas checks: ambient motion cannot alter fixed silhouettes.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createCanvas,Image}=require('@napi-rs/canvas');
let now=0,reduced=false;
const base=path.join(__dirname,'../static');
const imageLoads=[];
class LocalImage extends Image{set src(url){const callback=this.onload;
 imageLoads.push(new Promise((resolve,reject)=>{this.onload=()=>{callback?.();resolve();};this.onerror=reject;}));
 super.src=fs.readFileSync(path.join(base,url.replace(/^\//,'')));
}}
const metadata=Object.fromEntries(['landmarks','props','signals','npcs','discoveries'].map(k=>[k,JSON.parse(fs.readFileSync(path.join(base,'sprites/adventure-'+k+'-v1.json')))]));
const sandbox={Image:LocalImage,performance:{now:()=>now},window:{GauntletAdventureSpriteMetadata:metadata,matchMedia:()=>({matches:reduced})},document:{currentScript:null,createElement:()=>createCanvas(1,1)}};
vm.runInNewContext(fs.readFileSync(path.join(base,'adventure-sprites.js'),'utf8'),sandbox);
(async()=>{
await Promise.all(imageLoads); // Decoding is asynchronous even when header dimensions are available.
const api=sandbox.window.GauntletAdventureSprites;
function render(room,age){now=age;const canvas=createCanvas(960,540);api.scenery(canvas.getContext('2d'),room);return canvas.getContext('2d').getImageData(0,0,960,540).data;}
function changed(a,b,rect){let n=0;for(let y=rect[1];y<rect[3];y++)for(let x=rect[0];x<rect[2];x++){
 const i=(y*960+x)*4;if(a.slice(i,i+4).some((v,j)=>v!==b[i+j]))n++;
}return n;}
const bridge={areaSize:[960,540],adventure:{area:'bridge',bridge:true,bridgeLayout:{river:{left:568,right:640},crossing:{top:235,bottom:285},sprite:{x:604,y:337},eastPath:740}}};
const a=render(bridge,0),b=render(bridge,730);
assert.equal(changed(a,b,[543,239,663,270]),0,'Repaired timber, posts and ropes remain identical over time');
assert.ok(changed(a,b,[589,300,616,320])>0,'Water has a separate restrained overlay');
assert.equal(changed(a,b,[480,140,567,400]),0,'Stone banks and scenery retain their shape and texture');
const camp={adventure:{area:'camp',features:[{id:'kit'}]}};
const c=render(camp,0),d=render(camp,930);
assert.equal(changed(c,d,[140,40,346,250]),0,'Tent canvas and poles use the stable base');
assert.equal(changed(c,d,[320,315,446,375]),0,'Log bench stays fixed');
assert.equal(changed(c,d,[365,286,435,325]),0,'Campfire stones and logs stay fixed');
assert.ok(changed(c,d,[392,270,407,282])>0,'Only localized flame highlights flicker');
reduced=true;
assert.deepEqual(render(bridge,0),render(bridge,930),'Reduced motion stops decorative water');
assert.deepEqual(render(camp,0),render(camp,930),'Reduced motion stops flame flicker and embers');
const ctx={save(){},restore(){},drawImage(...args){this.frame=args[1];}};
for(const id of ['camp_tent','camp_fire','woodland_sign','trail_open','trail_locked','shrine_corrupt','shrine_restored','ruins_seal_awake','celebration_banner']){
 now=1030;assert.ok(api.stamp(ctx,id,0,0));assert.equal(ctx.frame,0,id+' is static by default');
}
now=250;api.npc(ctx,'runner',0,0,{moving:true});assert.equal(ctx.frame,metadata.npcs.cell,'Character animation remains explicitly enabled even with reduced decorative motion');
const movement={window:{}};vm.runInNewContext(fs.readFileSync(path.join(base,'movement.js'),'utf8'),movement);
const terrain={phase:'combat',environment:{obstacles:[],barriers:[{x:568,y:0,width:72,height:540}]}};
const p={x:680,y:260,slideVx:0,slideVy:0};movement.window.GauntletMovement.move(terrain,p,-1,0,500,1);
assert.ok(p.x>=652,'Browser prediction cannot cross an unrepaired river');
terrain.environment.barriers=[{x:568,y:0,width:72,height:235},{x:568,y:285,width:72,height:255}];
p.x=680;movement.window.GauntletMovement.move(terrain,p,-1,0,180,1);assert.ok(Math.abs(p.x-500)<.001,'Prediction opens the repaired span');
console.log('Stable props, localized water/flames, reduced motion, preserved characters and bridge prediction: OK');
const dungeon={region:'cavern',phase:'combat',areaSize:[960,540],adventure:{area:'cave_entry',dungeon:{id:'cave',type:'underground'}},environment:{obstacles:[],barriers:[{x:250,y:35,width:90,height:145,material:'stone',blocksShots:true}]}};
const wall=render(dungeon,0);assert.deepEqual(wall,render(dungeon,930),'Dungeon stonework remains static');
const alpha=(x,y)=>wall[(y*960+x)*4+3];
assert.equal(alpha(249,110),0);assert.equal(alpha(250,110),255);assert.equal(alpha(339,110),255);assert.equal(alpha(340,110),0,'Wall silhouette matches its authoritative rectangle');
const walker={x:220,y:110,slideVx:0,slideVy:0};movement.window.GauntletMovement.move(dungeon,walker,1,0,500,.5);
assert.ok(walker.x<250,'Prediction stops at the drawn wall, including a long dash');
walker.y=270;movement.window.GauntletMovement.move(dungeon,walker,1,0,300,1);assert.ok(walker.x>500,'Open corridor remains traversable');
vm.runInNewContext(fs.readFileSync(path.join(base,'world-scenery.js'),'utf8'),sandbox);
await Promise.all(imageLoads);
assert.equal(sandbox.window.GauntletWorldScenery.objects(dungeon,960,540).length,0,'Dungeon silhouettes have no cosmetic foreground cover');
// Use the actual woodland tree pixels through the same depth pass as gameplay.
const worldArt=sandbox.window.GauntletWorldScenery,tree={x:480,y:300,row:0,variant:0,scale:1};
const treeOnly=createCanvas(960,540);worldArt.drawObject(treeOnly.getContext('2d'),tree);
const treePixels=treeOnly.getContext('2d').getImageData(0,0,960,540).data;
let sample;
for(let y=250;y<285 && !sample;y++)for(let x=465;x<495;x++){
 const i=(y*960+x)*4;if(treePixels[i+3]===255 && treePixels[i]<150){sample=[x,y,i];break;}
}
assert.ok(sample,'The real tree has an opaque foreground pixel over this hero');
const mixed=createCanvas(960,540),mixedCtx=mixed.getContext('2d');
const entries=[{depth:280,player:{local:true},bounds:{x:465,y:250,width:30,height:40},draw:g=>{g.fillStyle='#ff0000';g.fillRect(465,250,30,40);}},
 {depth:300,occluder:true,bounds:worldArt.bounds(tree),draw:g=>worldArt.drawObject(g,tree)}];
worldArt.renderDepth(mixedCtx,entries);now+=300;mixedCtx.clearRect(0,0,960,540);worldArt.renderDepth(mixedCtx,entries);
const mixedPixels=mixedCtx.getImageData(0,0,960,540).data;
assert.ok(mixedPixels[sample[2]]>treePixels[sample[2]]+70,'Hero color remains readable through the actual imported tree');
const outside=(220*960+450)*4;assert.ok(mixedPixels[outside+3]<treePixels[outside+3],'The entire actual tree fades without a rectangular boundary');
const visible=worldArt.bounds(tree);assert.ok(visible.width<264&&visible.height<264,'Alpha-trimmed sprite bounds exclude transparent atlas margins');
for(const region of ['woodland','ruins','cavern','frost']){
 const r={code:'profile-test',stage:5,region,phase:'combat',environment:{obstacles:[]}},normal=worldArt.layout(r,960,540),boss=worldArt.layout({...r,encounterType:'large_boss'},960,540);
 assert.ok(normal.length<=10&&boss.length<=6);assert.equal(normal.filter(o=>o.x>180&&o.x<780&&o.y>180&&o.y<450).length,0,'Clear fighting/arrival space in '+region);
 assert.deepEqual(JSON.stringify(normal),JSON.stringify(worldArt.layout(r,960,540)),'Deterministic profiles');
}
console.log('Real tree whole-object fade, alpha bounds, deterministic sparse arena/boss profiles: OK');
console.log('Dungeon stable wall footprint, matching prediction, open corridor and unobscured actors: OK');
// Sample the actual imported frame where permanent structural collision lies;
// both the tent's mouth and the ruins archway remain usable in prediction.
const structures={phase:'combat',environment:{obstacles:[],barriers:[{x:202,y:195,width:49,height:25},{x:233,y:182,width:50,height:14},{x:288,y:207,width:13,height:15}]}};
assert.equal(movement.window.GauntletMovement.walkable(structures,227,210),false);
assert.equal(movement.window.GauntletMovement.walkable(structures,267,222),true);
const tentPixels=render(camp,0);assert.equal(tentPixels[(210*960+227)*4+3],255,'Tent side collision corresponds to the imported canvas');
structures.environment.barriers=[{x:437,y:188,width:23,height:79},{x:520,y:182,width:21,height:85}];
assert.equal(movement.window.GauntletMovement.walkable(structures,447,225),false);
assert.equal(movement.window.GauntletMovement.walkable(structures,480,225),true);
const archPixels=render({adventure:{area:'ruins'}},0);assert.equal(archPixels[(225*960+447)*4+3],255,'Column collision corresponds to imported stone');
console.log('Imported tent/column solid footprints and open mouths agree with browser prediction: OK');
})().catch(error=>{console.error(error);process.exitCode=1;});
