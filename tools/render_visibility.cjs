// Imported-sprite appearance evidence; no game rooms or private saves.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {createCanvas,Image,loadImage}=require('@napi-rs/canvas');
const pending=[];let now=0;
class LocalImage extends Image{set src(url){const done=this.onload;pending.push(new Promise((resolve,reject)=>{this.onload=()=>{done?.();resolve();};this.onerror=reject;}));super.src=fs.readFileSync(path.join('static',url));}}
const box={window:{matchMedia:()=>({matches:false})},Image:LocalImage,performance:{now:()=>now},document:{createElement:()=>createCanvas(1,1)}};
vm.runInNewContext(fs.readFileSync('static/world-scenery.js','utf8'),box);
(async()=>{await Promise.all(pending);const druid=await loadImage('static/sprites/druid-idle.png'),world=box.window.GauntletWorldScenery;
 const c=createCanvas(760,350),g=c.getContext('2d');g.fillStyle='#304c37';g.fillRect(0,0,760,350);
 for(let i=0;i<2;i++){g.save();g.translate(i*380-300+(i?25:0),-10-(i?15:0));const tree={x:480,y:300,row:0,variant:0,scale:1};
  const hero={depth:280,player:{local:true},bounds:{x:456,y:218,width:48,height:64},draw:ctx=>{ctx.drawImage(druid,0,68,68,68,448,218,64,64);}};
  const prop={key:'proof-'+i,depth:300,occluder:true,bounds:world.bounds(tree),draw:ctx=>world.drawObject(ctx,tree)};
  now=0;world.renderDepth(g,[hero,prop]);g.fillStyle='#304c37';g.fillRect(300,10,380,350);now=400;world.renderDepth(g,[hero,prop]);g.restore();
  g.fillStyle='#fff1c4';g.font='16px sans-serif';g.fillText(i?'Camera offset + imported sprites':'Imported tree + Druid',i*380+20,30);
 }
 const out=process.argv[2]||'reports/overlap-review.png';fs.writeFileSync(out,c.toBuffer('image/png'));console.log(out);
})().catch(e=>{console.error(e);process.exitCode=1;});
