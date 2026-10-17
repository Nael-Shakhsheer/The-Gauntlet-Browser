// Playable-region clues and mechanisms, driven exclusively by public quest facts.
(() => {
 const root=document.currentScript?.dataset.spriteRoot||'/sprites/',images={};
 const rows={brook_outlet:0,mill_wheel:1,watch_register:2,network_seal:3,pumping_register:4,dry_ditch:5,rooted_crop:6,empty_granary:7,field_restored:8,additive_ledger:9,channel_west:10,channel_east:10,sluice_open:12,cellar_begin:14};
 function image(key){if(!images[key]){const i=images[key]=new Image();i.src=root+key+'.png';}return images[key];}
 function select(f,a){
  const facts=new Set((a.chapter||[]).flatMap(q=>q.found||[]));
  if(f.kind==='travel_shrine')return{key:'travel-shrines-v2',i:Math.max(0,['brook','deepwood','watch'].indexOf(f.shrine))*2+Number(Boolean(f.active)),columns:2};
  let i=rows[f.id];if(i===undefined)return null;
  if(f.id==='cellar_begin'&&f.open)i=15;
  if(['channel_west','channel_east','sluice_open'].includes(f.id)&&facts.has(f.id))i++;
  return{key:'region-props-v1',i,columns:4};
 }
 function feature(ctx,f,a){const q=select(f,a);if(!q)return false;const img=image(q.key);if(!img.complete||!img.naturalWidth)return false;
  ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(img,q.i%q.columns*160,Math.floor(q.i/q.columns)*160,160,160,Math.round(f.x-80),Math.round(f.y+18-144),160,160);ctx.restore();return true;
 }
 function bounds(f,a){const q=select(f,a);if(!q)return null;const img=image(q.key);if(!img.naturalWidth)return null;
  return window.GauntletWorldScenery?.spriteBounds(img,q.i%q.columns*160,Math.floor(q.i/q.columns)*160,160,160,Math.round(f.x-80),Math.round(f.y+18-144),160,160)||null;
 }
 function scenery(ctx,room){const a=room.adventure;if(!a||!['watch','network','mill_trail','cellar'].includes(a.area))return;
  for(const b of room.environment?.barriers||[])if(b.material==='stone')window.GauntletDungeonSprites?.barrier(ctx,b,false);
  if(a.area==='cellar'&&a.dungeon?.complete)feature(ctx,{id:'cellar_begin',x:570,y:290,open:true},a);
 }
 window.GauntletRegionSprites={feature,bounds,scenery,select};
})();
