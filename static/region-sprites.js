// Playable-region clues and mechanisms, driven exclusively by public quest facts.
(() => {
 const root=document.currentScript?.dataset.spriteRoot||'/sprites/',images={};
 const rows={brook_outlet:0,mill_wheel:1,watch_register:2,network_seal:3,pumping_register:4,dry_ditch:5,rooted_crop:6,empty_granary:7,field_restored:8,additive_ledger:9,channel_west:10,channel_east:10,sluice_open:12,cellar_begin:14};
 Object.assign(rows,{upstream_sample:0,farm_record:4,steward_account:9,valve_west:10,valve_east:10,intake_restored:12,warden_begin:14});
 const campaignRows={letter_road:0,letter_brook:0,letter_yard:0,seed_supply:1,shelter_lit:2,root_sump_begin:3};
 function image(key){if(!images[key]){const i=images[key]=new Image();i.src=root+key+'.png';}return images[key];}
 function select(f,a){
  const facts=new Set((a.chapter||[]).flatMap(q=>q.found||[]));
  if(f.event)return{key:'campaign-props-v1',i:f.event==='caravan'?1:0,columns:2,scale:.65};
  if(f.kind==='travel_shrine')return{key:'travel-shrines-v2',i:Math.max(0,['brook','deepwood','watch'].indexOf(f.shrine))*2+Number(Boolean(f.active)),columns:2};
  if(campaignRows[f.id]!==undefined)return{key:f.id==='shelter_lit'&&!a.campaign?.shelter&&!facts.has('shelter_lit')?'campaign-props-unlit-v1':'campaign-props-v1',i:campaignRows[f.id],columns:2,scale:f.id.startsWith('letter_')?.5:f.id==='root_sump_begin'?1:.78};
  let i=rows[f.id];if(i===undefined)return null;
  if(f.id==='cellar_begin'&&f.open)i=15;
  if(['channel_west','channel_east','sluice_open','valve_west','valve_east','intake_restored'].includes(f.id)&&facts.has(f.id))i++;
  return{key:'region-props-v1',i,columns:4};
 }
 function feature(ctx,f,a){if(f.event==='caravan')return Boolean(window.GauntletAdventureSprites?.stamp(ctx,'road_wagon',f.x,f.y,{scale:.72}));const q=select(f,a);if(!q)return false;const img=image(q.key);if(!img.complete||!img.naturalWidth)return false;
  const scale=q.scale||1;ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(img,q.i%q.columns*160,Math.floor(q.i/q.columns)*160,160,160,Math.round(f.x-80*scale),Math.round(f.y+18-144*scale),160*scale,160*scale);
  const reduced=window.GauntletAudio?.visualSettings?.()?.reduced||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if(f.id==='shelter_lit'&&q.key==='campaign-props-v1'&&!reduced){ctx.globalAlpha*=.16+.08*Math.sin(performance.now()/190);ctx.fillStyle='#ffe59a';ctx.fillRect(Math.round(f.x-10*scale),Math.round(f.y+18-75*scale),2,5);}
  ctx.restore();return true;
 }
 function bounds(f,a){if(f.event==='caravan')return{x:f.x-65,y:f.y-85,width:130,height:100};const q=select(f,a);if(!q)return null;const img=image(q.key);if(!img.naturalWidth)return null;
  const scale=q.scale||1;return window.GauntletWorldScenery?.spriteBounds(img,q.i%q.columns*160,Math.floor(q.i/q.columns)*160,160,160,Math.round(f.x-80*scale),Math.round(f.y+18-144*scale),160*scale,160*scale)||null;
 }
 function scenery(ctx,room){const a=room.adventure;if(!a||!['watch','network','mill_trail','cellar'].includes(a.area))return;
  for(const b of room.environment?.barriers||[])if(b.material==='stone')window.GauntletDungeonSprites?.barrier(ctx,b,false);
  if(a.area==='cellar'&&a.dungeon?.complete)feature(ctx,{id:'cellar_begin',x:570,y:290,open:true},a);
 }
 function barrier(ctx,b,area){
  if(area!=='farmstead'||b.material!=='wood')return false;
  const img=image('region-props-v1');if(!img.complete||!img.naturalWidth)return false;
  // Reuse the finished granary artwork: its base stays on the actual solid
  // footprint; the roof may extend upward like every other world building.
  const sx=480,sy=160,cut=window.GauntletWorldScenery?.spriteBounds(img,sx,sy,160,160,0,0,160,160);
  if(!cut?.width||!cut.height)return false;
  const height=b.width*cut.height/cut.width;
  ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(img,sx+cut.x,sy+cut.y,cut.width,cut.height,Math.round(b.x),Math.round(b.y+b.height-height),b.width,height);ctx.restore();return true;
 }
 window.GauntletRegionSprites={feature,bounds,scenery,select,barrier};
})();
