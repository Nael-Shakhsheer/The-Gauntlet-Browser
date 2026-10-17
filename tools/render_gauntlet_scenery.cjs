// Real imported assets, cosmetic generator and eight palette/purpose fixtures.
// This contact sheet is a renderer fixture, not a human multiplayer playthrough.
const fs=require('node:fs'),vm=require('node:vm'),{createCanvas,Image,loadImage}=require('@napi-rs/canvas');
const pending=[];class LocalImage extends Image{set src(url){const done=this.onload;pending.push(new Promise((resolve,reject)=>{this.onload=()=>{done?.();resolve();};this.onerror=reject;}));super.src=fs.readFileSync('static/'+url);}}
const box={window:{matchMedia:()=>({matches:false})},Image:LocalImage,performance:{now:()=>1000},document:{createElement:()=>createCanvas(1,1)}};
vm.runInNewContext(fs.readFileSync('static/world-scenery.js','utf8'),box);
(async()=>{
 await Promise.all(pending);const world=box.window.GauntletWorldScenery,heroes=await Promise.all(['knight','wizard','archer','druid'].map(h=>loadImage('static/sprites/'+h+'-idle.png')));
 const c=createCanvas(1200,1480),g=c.getContext('2d');g.imageSmoothingEnabled=false;g.fillStyle='#15262d';g.fillRect(0,0,c.width,c.height);
 const report=[];for(const [row,region]of ['woodland','ruins','cavern','frost'].entries())for(let column=0;column<2;column++){
  const room={code:'visual-'+region,phase:'combat',region,stage:column?10:9,encounterType:column?'large_boss':'regular',enemies:column?[{boss:true}]:[],environment:{obstacles:[{id:'retained-tactical-cover',x:280,y:310}]}};
  g.save();g.translate(column*600,row*370+35);g.scale(.625,.625);g.beginPath();g.rect(0,0,960,540);g.clip();world.floor(g,room,960,540);
  const objects=world.objects(room,960,540);world.renderDepth(g,objects);
  // The same ordinary four-hero visual footprint, not a player-stat fixture.
  for(const [i,img]of heroes.entries()){const size=Math.min(img.width,img.height/8),x=395+(i%2)*145,y=255+Math.floor(i/2)*145;const b=world.spriteBounds(img,0,size,size,size,0,0,size,size),scale=62/Math.max(1,b.height);g.drawImage(img,b.x,size+b.y,b.width,b.height,x-b.width*scale/2,y-b.height*scale,b.width*scale,b.height*scale);}
  g.restore();g.fillStyle='#f6e6bd';g.font='18px sans-serif';g.fillText(region+' · '+world.profile(room).id+' · '+objects.length+' decorative objects',column*600+20,row*370+25);
  report.push({region,purpose:world.profile(room).id,objects:objects.length,tacticalCoverRetained:room.environment.obstacles.length});
 }
 fs.writeFileSync('reports/gauntlet-palettes-2026-10-15.png',c.toBuffer('image/png'));fs.writeFileSync('reports/GAUNTLET_SCENERY_2026-10-15.json',JSON.stringify(report,null,2));console.log(report);
})().catch(e=>{console.error(e);process.exitCode=1;});
