// Imported-asset renderer evidence; this is not a human multiplayer playthrough.
const fs=require('node:fs'),vm=require('node:vm'),{createCanvas,Image,loadImage}=require('@napi-rs/canvas');
const pending=[];let now=0;
class LocalImage extends Image{set src(url){pending.push(new Promise((resolve,reject)=>{const callback=this.onload;this.onload=()=>{callback?.();resolve();};this.onerror=reject;}));super.src=fs.readFileSync('static/'+url.replace(/^\//,''));}}
const box={Image:LocalImage,window:{matchMedia:()=>({matches:false})},document:{createElement:()=>createCanvas(1,1)},performance:{now:()=>now}};
vm.runInNewContext(fs.readFileSync('static/world-scenery.js','utf8'),box);
(async()=>{
 await Promise.all(pending);const api=box.window.GauntletWorldScenery;
 const images=await Promise.all(['druid-idle','world-scenery-v2','village-woodland-buildings-v2','dungeon-props-v1','archer-idle','troll-idle','firewolf-idle','icebear-idle'].map(n=>loadImage('static/sprites/'+n+'.png')));
 const [hero,scenery,roof,portal,friend,enemy,wolf,bear]=images;
 const cases=[['Tree',scenery,0,0,160,1.2],['Fallen log',scenery,480,0,160,1.3],['Shale rock',scenery,480,320,160,1.2],['Roof',roof,0,0,80,2.1],['Portal shrine',portal,480,320,160,1],['Teammate',friend,0,68,68,1.6,true],['Enemy',enemy,0,68,68,1.8,true],['Fire wolf',wolf,0,68,68,1.6,true],['Ice bear · camera offset',bear,0,68,68,2.3,true]];
 const out=createCanvas(960,810),g=out.getContext('2d');g.fillStyle='#162b2e';g.fillRect(0,0,960,810);
 for(const [i,[name,img,sx,sy,cell,scale,actor]]of cases.entries()){
  const c=createCanvas(320,225),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;
  const hb=api.spriteBounds(hero,0,68,68,68,116,83,68,68),pb=api.spriteBounds(img,sx,sy,cell,cell,160-cell*scale/2,168-cell*scale,cell*scale,cell*scale);
  const entries=[{depth:130,player:{local:true},bounds:hb,draw:x=>x.drawImage(hero,0,68,68,68,116,83,68,68)},
    {key:'audit-'+i,depth:168,actor:!!actor,occluder:true,bounds:pb,draw:x=>x.drawImage(img,sx,sy,cell,cell,160-cell*scale/2,168-cell*scale,cell*scale,cell*scale),after:x=>{x.fillStyle='#f6d68d';x.fillRect(155,177,10,3);}}];
  for(const t of [0,400]){now=t;ctx.fillStyle='#35503c';ctx.fillRect(0,0,320,225);ctx.save();if(i===8)ctx.translate(8,-5);api.renderDepth(ctx,entries);ctx.restore();}
  const col=i%3,row=Math.floor(i/3);g.drawImage(c,col*320,row*270+35);g.fillStyle='#f5e4b9';g.font='15px sans-serif';g.fillText(name,col*320+12,row*270+21);
 }
 fs.writeFileSync('reports/overlap-audit-2026-10-15.png',out.toBuffer('image/png'));
 console.log('Nine imported-asset overlap cases rendered; actors opaque, complete props fade, markers above.');
})().catch(e=>{console.error(e);process.exitCode=1;});
