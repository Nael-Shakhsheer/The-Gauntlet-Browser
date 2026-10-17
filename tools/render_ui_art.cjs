// Artwork authoring views through the actual client, in a fresh browser context.
// Uses local fixture data only: no room, action, save or personal profile APIs.
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
const out=path.join(__dirname,'../art/pixel-ui');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.GAUNTLET_ART_BROWSER_PATH?{executablePath:process.env.GAUNTLET_ART_BROWSER_PATH}:{channel:process.env.GAUNTLET_ART_BROWSER||'msedge'})});
 const page=await browser.newPage({viewport:{width:1280,height:800}}),messages=[];
 page.on('pageerror',e=>messages.push(e.message));
 page.on('console',e=>{if(e.type()==='error'||/font|OTS/i.test(e.text()))messages.push(e.text());});
 try{
  await page.goto('http://127.0.0.1:8000/');await page.waitForTimeout(1400);await page.evaluate(()=>document.fonts.ready);
  await page.screenshot({path:path.join(out,'entry-desktop.png'),fullPage:true});
  await page.evaluate(()=>{
   const roles=['Frontline fighter','Arcane spellcaster','Ranged marksman','Holy protector','Agile skirmisher','Nature summoner','Musical support','Party healer'];
   const colors=['#d1c3a1','#aa86db','#8db779','#d5b988','#ad91ba','#7fac89','#c9a069','#82b8b2'];
   const classes=Object.fromEntries(['Knight','Wizard','Archer','Cleric','Rogue','Druid','Bard','Healer'].map((n,i)=>[n,{color:colors[i],role:roles[i]}]));
   const abilities=[{id:'piercing_volley',name:'Piercing volley',attackType:'light',cooldown:.65,manaCost:0,description:'A piercing arrow cuts through enemies on its flight.'},
    {id:'snare_shot',name:'Snare shot',attackType:'special',cooldown:7,manaCost:14,description:'Fire a thorn-bound arrow to slow a dangerous target.'},
    {id:'deadeye',name:'Deadeye',attackType:'ultimate',cooldown:15,manaCost:30,description:'Wind up a massive golden arrow that pierces the battlefield.'}];
   const players=[{id:'art-archer',name:'Rowan',class:'Archer',color:colors[2],abilityCount:3,x:980,y:650,facingX:0,facingY:1,hp:84,maxHp:100,status:'alive',connected:true},
    {id:'art-wizard',name:'Mira',class:'Wizard',color:colors[1],abilityCount:3,x:1030,y:615,facingX:0,facingY:1,hp:76,maxHp:100,status:'alive',connected:true},
    {id:'art-knight',name:'Kai',class:'Knight',color:colors[0],abilityCount:3,x:930,y:685,facingX:0,facingY:1,hp:112,maxHp:140,status:'alive',connected:true}];
   const item=(key,name,slot,kind,rarity,description)=>({id:'art-'+key,key,name,slot,kind,rarity,description,sell:12,price:45,power:8});
   const inventory=[item('healing_draught','Healing draught','utility','heal','common','Restores health when the party needs it.'),
    item('mana_draught','Mana draught','utility','mana','common','Restores mana for your next spell.'),
    item('arcane_conductor','Arcane Conductor','tool','weapon','epic','An arcane relic recovered from the woodland shrine.'),
    item('wind_bow','Wind bow','tool','weapon','rare','A carefully carved bow, light and quick to draw.')];
   const raw=[['home','Oakvale',[0,0]],['road','Southern road',[0,1]],['crossroads','Woodland crossroads',[1,1]],['clearing',"Hunter's clearing",[2,1]],['camp','Abandoned camp',[1,2]],['shrine','Overgrown shrine',[2,2]],['bridge','Broken bridge',[0,2]],['ruins','Old ruins',[0,3]]];
   const locations=raw.map(([id,name,position])=>({id,name,position,visited:id!=='ruins',current:id==='crossroads',tracked:id==='shrine',objective:({clearing:'Quest: The missing hunter',camp:'Quest: Repair the bridge',bridge:'Quest: Repair the bridge',shrine:'Quest: Restore the shrine',ruins:'Quest: Secure the woodland'})[id]}));
   const connections=[['home','road','south','north'],['road','crossroads','east','west'],['road','bridge','south','north'],['crossroads','camp','south','north'],['crossroads','clearing','east','west'],['crossroads','shrine','south','north'],['camp','bridge','west','east'],['clearing','shrine','south','north'],['bridge','ruins','south','north']].map(([fromId,toId,fromEdge,toEdge])=>({fromId,toId,fromEdge,toEdge,locked:fromId==='bridge'||fromId==='road'&&toId==='bridge'}));
   const journal=[['hunter','The missing hunter','Escort the hunter from the clearing to Oakvale.'],['bridge','Repair the bridge','Find a repair kit in the camp and restore the crossing.'],['shrine','Restore the shrine','Solve the shrine runes and defeat its stone guardian.'],['region','Secure the woodland','Finish the woodland objectives, then enter the old ruins.']].map(([id,title,objective])=>({id,title,objective,status:'active',visibility:'active'}));
   const adventure={area:'crossroads',name:'Woodland crossroads',locations,connections,journal,tracked:{id:'shrine',title:'Restore the shrine',area:'shrine',nextStep:'Take the southern trail to the overgrown shrine.',complete:false},discoveries:[{title:'Moss-covered cache',text:'A small supply cache hidden beside the old trail.'}],undiscoveredCount:1,rewards:[],persistence:true,checkpointBed:true,bridge:false,shrineRestored:false,
    danger:2,locked:false,features:[{id:'sign',name:'Woodland signpost',kind:'signpost',x:980,y:550}],exits:[{id:'road',name:'Southern road',edge:'west',x:48,y:540},{id:'camp',name:'Abandoned camp',edge:'south',x:614,y:1032},{id:'clearing',name:'Hunter clearing',edge:'east',x:1872,y:540},{id:'shrine',name:'Overgrown shrine',edge:'south',x:1382,y:1032}],travelMembers:[]};
   window.uiArtRoom={code:'ui-art-fixture',you:players[0].id,host:players[0].id,phase:'lobby',mode:'adventure',players,classes,abilityOptions:{Archer:abilities},selectedAbilities:abilities.map(a=>a.id),abilitySlots:abilities.map((a,i)=>({...a,cooldownRemaining:i===1?3:0})),
    inventory,toolSlots:[inventory[3],null],utilitySlots:[inventory[0],inventory[1],null],pouchCapacity:10,runes:142,mana:78,maxMana:100,region:'woodland',stage:2,areaSize:[1920,1080],adventure,
    enemies:[],summons:[],environment:{obstacles:[],zones:[]},projectiles:[],effects:[],hazards:[],pings:[],town:'Oakvale',shopStock:inventory.slice(0,2),chat:[]};
   document.querySelector('#entry').classList.add('hidden');document.querySelector('#lobby').classList.remove('hidden');
   renderClasses(uiArtRoom);renderPlayers(uiArtRoom);
   document.querySelector('#roomCodeDisplay').textContent='PARTY';
   document.querySelector('#chatMessages').innerHTML='<div class="chat-line"><b>Mira</b><span>Meet at the crossroads. I found the shrine trail.</span></div><div class="chat-line"><b>Rowan</b><span>On my way. Let’s gather before we head south.</span></div>';
  });
  await page.waitForTimeout(250);await page.screenshot({path:path.join(out,'lobby-desktop.png'),fullPage:true});
  await page.evaluate(()=>{
   uiArtRoom.phase='combat';document.body.classList.add('is-playing');
   document.querySelector('#classPanel').classList.add('hidden');document.querySelector('.room-bar').classList.add('hidden');document.querySelector('#arenaPanel').classList.remove('hidden');
   document.querySelector('#hpLabel').textContent='HP 84 / 100';document.querySelector('#hpFill').style.width='84%';document.querySelector('#manaLabel').textContent='MANA 78 / 100';document.querySelector('#manaFill').style.width='78%';
   document.querySelector('#runeCount').textContent='142 RUNES';document.querySelector('#dashButton').classList.remove('hidden');
   renderAbilityBar(uiArtRoom);renderQuickPouch(uiArtRoom);renderToolHotbar(uiArtRoom);renderUtilityHotbar(uiArtRoom);renderCoordination(uiArtRoom);renderAdventure(uiArtRoom);
   window.GauntletCombatEnvironment.observe(uiArtRoom);window.GauntletProjectiles.observe(uiArtRoom);
   window.uiArtTimer=setInterval(()=>drawWorld(uiArtRoom),16);
  });
  await page.waitForTimeout(200);await page.screenshot({path:path.join(out,'hud-desktop.png')});
  await page.evaluate(()=>document.querySelector('#adventureMapDialog').showModal());await page.waitForTimeout(200);
  await page.screenshot({path:path.join(out,'map-desktop.png')});
  await page.evaluate(()=>{uiArtRoom.adventure.bridge=true;uiArtRoom.adventure.shrineRestored=true;uiArtRoom.adventure.locations.find(n=>n.id==='bridge').name='Restored bridge';uiArtRoom.adventure.locations.find(n=>n.id==='shrine').name='Restored shrine';uiArtRoom.adventure.connections.forEach(l=>l.locked=false);renderAdventure(uiArtRoom);});
  await page.screenshot({path:path.join(out,'map-restored.png')});
  await page.evaluate(()=>{window.fullAtlas=uiArtRoom.adventure;uiArtRoom.adventure={...fullAtlas,locations:fullAtlas.locations.filter(n=>['home','road','crossroads'].includes(n.id)),connections:fullAtlas.connections.filter(l=>['home','road','crossroads'].includes(l.fromId)&&['home','road','crossroads'].includes(l.toId))};renderAdventure(uiArtRoom);});
  await page.screenshot({path:path.join(out,'map-exploring.png')});
  await page.evaluate(()=>{uiArtRoom.adventure=fullAtlas;renderAdventure(uiArtRoom);});
  await page.setViewportSize({width:844,height:390});await page.waitForTimeout(150);await page.evaluate(()=>{setAtlasZoom(2);focusAtlasNode('crossroads');});await page.screenshot({path:path.join(out,'map-phone.png')});
  await page.setViewportSize({width:667,height:375});await page.waitForTimeout(150);await page.evaluate(()=>focusAtlasNode('crossroads'));await page.screenshot({path:path.join(out,'map-small-phone.png')});
  await page.evaluate(()=>document.querySelector('#adventureMapDialog').close());await page.screenshot({path:path.join(out,'hud-small-phone.png')});
  await page.setViewportSize({width:1280,height:800});
  await page.evaluate(()=>{document.querySelector('#pouchPanel').classList.add('hud-open','pouch-expanded');});
  await page.screenshot({path:path.join(out,'pouch-desktop.png')});
  await page.evaluate(()=>{document.querySelector('#pouchPanel').classList.remove('hud-open');document.querySelector('#adventureJournalDialog').showModal();});
  await page.screenshot({path:path.join(out,'journal-desktop.png')});
  await page.evaluate(()=>{document.querySelector('#adventureJournalDialog').close();uiArtRoom.phase='town';renderTown(uiArtRoom);document.querySelector('#townPanel').classList.remove('hidden');});
  await page.screenshot({path:path.join(out,'shop-desktop.png')});
  await page.evaluate(()=>{document.querySelector('#townPanel').classList.add('hidden');document.querySelector('#audioDialog').showModal();});
  await page.screenshot({path:path.join(out,'settings-desktop.png')});
  await page.evaluate(()=>clearInterval(uiArtTimer));
  fs.writeFileSync(path.join(out,'render-notes.json'),JSON.stringify({purpose:'Visual authoring screenshots from client fixtures; no game rooms or saves',messages},null,2)+'\n');
  console.log('Pixel UI / atlas artwork views saved. '+messages.length+' browser diagnostic messages.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
