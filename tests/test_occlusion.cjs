const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {createCanvas}=require('@napi-rs/canvas');
let now=0,reduced=false;
const sandbox={window:{matchMedia:()=>({matches:reduced})},Image:class{},document:{createElement:()=>createCanvas(1,1)},performance:{now:()=>now}};
vm.runInNewContext(fs.readFileSync('static/world-scenery.js','utf8'),sandbox);
const {renderDepth}=sandbox.window.GauntletWorldScenery;
function hero(x=40,depth=50){return {depth,player:{local:true},bounds:{x,y:30,width:20,height:30},draw(ctx){ctx.fillStyle='#ff0000';ctx.fillRect(x,30,20,30);}};}
function prop(depth=70){return {depth,occluder:true,bounds:{x:20,y:10,width:80,height:80},draw(ctx){ctx.fillStyle='#00ff00';ctx.fillRect(20,10,80,80);}};}
function scene(entries,scale=1){const canvas=createCanvas(120*scale,100*scale),ctx=canvas.getContext('2d');ctx.scale(scale,scale);
const frame=(at,items=entries)=>{now=at;ctx.clearRect(0,0,120,100);renderDepth(ctx,items);};frame(0);frame(60);frame(300);return {ctx,frame,pixel:(x,y)=>Array.from(ctx.getImageData(x*scale,y*scale,1,1).data)};}
let s=scene([prop(),hero()]);
const under=s.pixel(50,45);assert.ok(under[0]>175 && under[1]<80,'Hero remains visible through foreground scenery');
assert.ok(s.pixel(80,45)[3]<90,'The WHOLE overlapping object fades, including outside hero bounds; no rectangular cutback');
s.frame(340,[hero(-30),prop()]);assert.ok(s.pixel(80,45)[3]<90,'Exit hysteresis prevents transparency flicker');
s.frame(700,[hero(-30),prop()]);s.frame(1000,[hero(-30),prop()]);assert.deepEqual(s.pixel(80,45),[0,255,0,255],'The whole prop returns to opacity after leaving');
s=scene([hero(40,90),prop()]);assert.deepEqual(s.pixel(50,45),[255,0,0,255],'A hero in front needs no scenery cutback');
s=scene([hero(0),prop()]);assert.deepEqual(s.pixel(50,45),[0,255,0,255],'Non-overlapping scenery stays opaque');
s=scene([hero(40),{...hero(48),player:{local:false}},prop()]);
assert.deepEqual(s.pixel(53,45),under,'Overlapping heroes trigger one fade, without double blending');
s=scene([hero(),prop()],2);assert.deepEqual(s.pixel(50,45),under,'Cutback matches world coordinates under a scrolling/zoomed camera');
s.ctx.fillStyle='#ffff00';s.ctx.fillRect(50,40,4,4);assert.deepEqual(s.pixel(51,41),[255,255,0,255],'Combat warnings drawn above scenery remain fully readable');
const local=hero(40,90);local.occluder=true;
s=scene([{...hero(40,50),player:{local:false}},local]);assert.deepEqual(s.pixel(50,45),[255,0,0,255],'Local hero is never faded by a teammate behind them');
const decorated=prop();decorated.draw=ctx=>{ctx.fillStyle='#00ff00';ctx.fillRect(20,10,90,80);};
s=scene([hero(),decorated]);assert.ok(s.pixel(105,45)[3]>65&&s.pixel(105,45)[3]<90,'Whole object edges fade smoothly without cropping');
s=scene([hero(),{...prop(),actor:true}]);assert.deepEqual(s.pixel(50,45),[0,255,0,255],'Actors and their combat information remain opaque');
reduced=true;s=scene([hero(),prop()]);assert.deepEqual(s.pixel(50,45),under,'Reduced motion keeps the same settled visibility without a tween');
console.log('Whole-object fade, smooth transitions/hysteresis, actor opacity, local hero, camera and warnings: OK');
