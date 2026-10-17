// Local client art fixtures. No user rooms, gameplay actions, identities or save records.
const fs=require('node:fs'),path=require('node:path'),{chromium}=require('playwright');
const out=path.join(__dirname,'../art/dungeon-portal');
const walls={cave_entry:[[250,35,90,145],[250,360,90,145],[650,35,75,120],[650,385,75,120]],cave_gallery:[[335,110,80,80],[335,350,80,155],[560,35,75,155],[560,355,75,150]],cave_cache:[[170,140,75,200],[710,140,75,200]],cave_heart:[[270,105,65,75],[610,355,65,75]],tower_1:[[260,155,60,60],[640,325,60,60]],tower_2:[[245,205,75,100],[640,205,75,100]],tower_3:[[225,140,70,80],[665,335,70,80]]};
const names={cave_entry:'Entrance chamber',cave_gallery:'Split gallery',cave_cache:'Surveyor alcove',cave_heart:'Troll den',tower_1:'Floor 1',tower_2:'Floor 2',tower_3:'Floor 3'};
const edges={cave_entry:[['road','west'],['cave_gallery','east']],cave_gallery:[['cave_entry','west'],['cave_cache','north'],['cave_heart','east']],cave_cache:[['cave_gallery','south']],cave_heart:[['cave_gallery','west'],['clearing','east']],tower_1:[['camp','west'],['tower_2','north']],tower_2:[['tower_1','south'],['tower_3','north']],tower_3:[['tower_2','south'],['bridge','west']]};
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.GAUNTLET_ART_BROWSER_PATH?{executablePath:process.env.GAUNTLET_ART_BROWSER_PATH}:{channel:'msedge'})});
 const page=await browser.newPage({viewport:{width:960,height:540}}),diagnostics=[],views=[];
 page.on('pageerror',e=>diagnostics.push(e.stack||e.message));page.on('response',r=>{if(r.status()>=400)diagnostics.push(r.status()+' '+r.url());});
 try{
  await page.goto('http://127.0.0.1:8000/');await page.waitForTimeout(1800);await page.evaluate(()=>document.fonts.ready);
  await page.evaluate(()=>{
   const c=document.querySelector('#world');document.body.replaceChildren(c);document.body.classList.add('is-playing');
   Object.assign(c.style,{width:'960px',height:'540px',position:'relative',inset:'auto',display:'block'});
   Object.assign(document.body.style,{margin:'0',padding:'0',width:'960px',height:'540px',overflow:'hidden'});
   const players=['Druid','Archer','Wizard','Knight'].map((className,i)=>({id:'art-'+i,name:className,class:className,x:410+i*46,y:300,facingX:0,facingY:1,hp:100,maxHp:100,status:'alive',connected:true,color:'#b0c5b5'}));
   window.dungeonArtRoom={code:'dungeon-art-fixture',mode:'adventure',you:players[0].id,phase:'combat',stage:4,region:'cavern',classes:{},areaSize:[960,540],players,enemies:[],summons:[],environment:{obstacles:[],zones:[],barriers:[]},projectiles:[],effects:[],hazards:[],pings:[],adventure:{area:'cave_entry',features:[],exits:[],dungeon:{id:'cave',type:'underground'}}};
  });
  for(const area of Object.keys(walls)){
   await page.evaluate(({area,walls,edges,names})=>{
    const r=dungeonArtRoom,tower=area.startsWith('tower_');r.region=tower?'ruins':'cavern';
    r.adventure={area,name:names[area],features:[],exits:edges[area].map(([id,edge])=>({id,name:names[id]||id,edge,x:edge==='west'?35:edge==='east'?925:480,y:edge==='north'?35:edge==='south'?505:270,locked:area==='tower_2'&&edge==='north'})),dungeon:{id:tower?'tower':'cave',type:tower?'tower':'underground'}};
    const f=tower?{id:'dungeon_begin',kind:'dungeon_begin',name:'Ring the watch bell',x:480,y:430}:area==='cave_entry'?{id:'cave_supplies',kind:'dungeon_treasure',name:'Abandoned supply crate',x:450,y:390}:area==='cave_gallery'?{id:'survey_marks',kind:'dungeon_story',name:'Surveyor’s trail marks',x:475,y:180}:area==='cave_cache'?{id:'cave_survey',kind:'dungeon_treasure',name:'Surveyor’s hidden cache',x:510,y:350}:{id:'dungeon_begin',kind:'dungeon_begin',name:'Awaken the cave troll',x:380,y:400};
    r.adventure.features=[f];r.environment={obstacles:[],zones:area==='tower_2'?[{id:'art-trap',kind:'trap',x:410,y:270,radius:32}]:[],barriers:walls[area].map(([x,y,width,height],i)=>({id:'wall-'+i,x,y,width,height,material:'stone'}))};
    GauntletCombatEnvironment.observe(r);GauntletProjectiles.observe(r);GauntletDungeonSprites.observe(r);drawWorld(r);
   },{area,walls,edges,names});
   await page.waitForTimeout(100);await page.evaluate(()=>drawWorld(dungeonArtRoom));
   const file='room-'+area+'.png';await page.locator('#world').screenshot({path:path.join(out,file)});views.push(file);
  }
  await page.evaluate(()=>{dungeonArtRoom.adventure.area='cave_cache';dungeonArtRoom.adventure.features=[];drawWorld(dungeonArtRoom);});
  await page.locator('#world').screenshot({path:path.join(out,'cache-spent.png')});views.push('cache-spent.png');
  const portal=[['charge',2.4],['channel',1.4],['depart',.28]];
  for(const [kind,remaining]of portal){
   await page.evaluate(remaining=>{const r=dungeonArtRoom;r.adventure.area='cave_gallery';r.adventure.dungeon={id:'cave',type:'underground'};r.adventure.features=[];r.adventure.exits=[];r.environment={obstacles:[],zones:[],barriers:[]};r.adventure.portals={channel:{id:'art-channel',remaining,duration:3,anchor:[410,300],participants:r.players.map(p=>p.id)}};GauntletDungeonSprites.observe(r);drawWorld(r);},remaining);
   const file='portal-'+kind+'.png';await page.locator('#world').screenshot({path:path.join(out,file)});views.push(file);
  }
  await page.evaluate(()=>{dungeonArtRoom.adventure.portals.channel=null;GauntletDungeonSprites.observe(dungeonArtRoom);drawWorld(dungeonArtRoom);});
  await page.locator('#world').screenshot({path:path.join(out,'portal-cancel.png')});views.push('portal-cancel.png');
  await page.evaluate(()=>{const r=dungeonArtRoom;r.adventure.area='clearing';r.adventure.dungeon=null;r.feedback={epoch:'arrival-art',cursor:1,events:[{id:1,kind:'portal_arrive',age:.43,participants:r.players.map(p=>({ownerId:p.id,x:p.x,y:p.y}))}]};GauntletDungeonSprites.observe(r);drawWorld(r);});
  await page.locator('#world').screenshot({path:path.join(out,'portal-arrive.png')});views.push('portal-arrive.png');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.evaluate(()=>{const r=dungeonArtRoom;r.adventure.portals.channel={remaining:1.2,duration:3,anchor:[410,300],participants:r.players.map(p=>p.id)};GauntletDungeonSprites.observe(r);drawWorld(r);});
  await page.locator('#world').screenshot({path:path.join(out,'portal-reduced-motion.png')});views.push('portal-reduced-motion.png');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto('http://127.0.0.1:8000/');await page.waitForTimeout(1000);
  for(const id of ['cave','tower'])for(const state of ['full','partial','cleared']){
   await page.evaluate(({id,state,names})=>{
    const all=Object.entries(names).filter(([key])=>key.startsWith(id+'_')),chosen=state==='partial'?all.slice(0,1):all;
    const d={id,name:id==='cave'?'Rootwater passage':'Briarwatch tower',type:id==='cave'?'underground':'tower',danger:4,description:'Finite chambers · retreat through open passages.',complete:state==='cleared',routeOpen:state==='cleared',entrances:[id==='cave'?'road':'camp'],floors:state==='cleared'?[1,2,3]:[],treasure:state==='cleared'?2:0,objective:'Explore the charted passage.',current:true,nodes:chosen.map(([key,name],i)=>({id:key,name:'Dungeon · '+name,current:i===0,visited:true,cleared:state==='cleared',position:[0,0]})),links:[]};
    if(state!=='partial')d.links=id==='cave'?[['cave_entry','cave_gallery'],['cave_gallery','cave_cache'],['cave_gallery','cave_heart']].map(([fromId,toId])=>({fromId,toId,locked:false})):[['tower_1','tower_2'],['tower_2','tower_3']].map(([fromId,toId],i)=>({fromId,toId,locked:state!=='cleared'&&i===1}));
    renderDungeonPanels({dungeons:[d],locations:[],tracked:{id},saveInfo:{worldId:'art-world'}});showAtlasInteriors(true);document.querySelector('#adventureMapDialog').showModal();
   },{id,state,names});
   await page.waitForTimeout(200);
   const file='map-'+id+'-'+state+'.png';await page.locator('#adventureMapDialog').screenshot({path:path.join(out,file)});views.push(file);
   await page.evaluate(()=>document.querySelector('#adventureMapDialog').close());
  }
  await page.setViewportSize({width:844,height:390});
  await page.evaluate(()=>{document.querySelector('#adventureMapDialog').showModal();});await page.waitForTimeout(250);
  await page.screenshot({path:path.join(out,'map-landscape.png')});views.push('map-landscape.png');
  fs.writeFileSync(path.join(out,'render-notes.json'),JSON.stringify({purpose:'Actual client artwork fixtures; no personal room actions or saves',views,diagnostics},null,2)+'\n');console.log('Rendered '+views.length+' art views. Browser diagnostics: '+diagnostics.length);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
