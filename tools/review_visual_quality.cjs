// Fresh, disposable browser review. QA URL must point at an isolated preview server.
const fs=require('node:fs'),path=require('node:path'),{chromium}=require('playwright');
const out=path.join(__dirname,'../art/visual-quality-v3/review');fs.mkdirSync(out,{recursive:true});
const base=process.env.GAUNTLET_QA_URL||'http://127.0.0.1:8015';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.GAUNTLET_ART_BROWSER_PATH?{executablePath:process.env.GAUNTLET_ART_BROWSER_PATH}:{channel:'msedge'})});
 const context=await browser.newContext({viewport:{width:1366,height:768}}),page=await context.newPage(),messages=[],requests=[];
 page.on('pageerror',e=>messages.push(e.stack||e.message));page.on('response',r=>{if(r.status()>=400)messages.push(r.status()+' '+r.url());requests.push({url:r.url().replace(base,''),status:r.status()});});
 // Source delivery for a preview process started before a new static route was added.
 await context.route('**/*.js',route=>{const file=path.basename(new URL(route.request().url()).pathname),local=path.join(__dirname,'../static',file);return fs.existsSync(local)?route.fulfill({path:local,contentType:'text/javascript'}):route.continue();});
 const shot=async name=>{await page.screenshot({path:path.join(out,name+'.png'),fullPage:!await page.evaluate(()=>document.body.classList.contains('is-playing'))});};
 try{
  await page.goto(base);await page.addStyleTag({content:'@media(min-width:901px){body.is-playing .arena-controls{display:none!important}}'});await page.waitForTimeout(1000);await page.evaluate(()=>document.fonts.ready);await shot('menu-desktop');
  await page.locator('#newAdventure').click();await page.locator('#newHero').selectOption('Healer');await page.locator('#newName').fill('Art review');await page.locator('#newWorldName').fill('Woodland art review');await page.locator('#skipIntro').check();await shot('setup-desktop');
  await page.locator('#newRunSubmit').click();await page.waitForFunction(()=>document.body.classList.contains('adventure-playing'));await page.waitForTimeout(800);
  if(await page.locator('#storyDialog[open]').count())await page.getByRole('button',{name:'Understood',exact:true}).click();await page.waitForTimeout(200);await shot('hud-desktop');
  await page.locator('#heroSkillsButton').click();await page.waitForTimeout(150);await shot('skills-desktop');
  await page.locator('#magicProgression summary').click();await shot('magic-runes-desktop');await page.locator('[data-close="heroSkillsDialog"]').click();
  await page.locator('#adventureJournalButton').click();await shot('journal-desktop');await page.locator('[data-close="adventureJournalDialog"]').click();
  await page.locator('#adventureMapButton').click();await shot('map-desktop');await page.locator('[data-close="adventureMapDialog"]').click();
  await page.setViewportSize({width:844,height:390});await page.waitForTimeout(200);await shot('hud-landscape');
  await page.locator('#heroSkillsButton').click();await page.waitForTimeout(100);await shot('skills-landscape');await page.locator('[data-close="heroSkillsDialog"]').click();
  await page.evaluate(()=>returnToMainMenu(true));await page.waitForTimeout(500);await shot('saved-worlds-landscape');
  await page.setViewportSize({width:1366,height:768});await shot('saved-worlds-desktop');
  // Keep ordinary gameplay untouched; a separate page supplies renderer-only model fixtures.
  const model=await context.newPage();model.on('pageerror',e=>messages.push(e.stack||e.message));
  await model.route('**/ascended-sprites.js',route=>route.fulfill({path:path.join(__dirname,'../static/ascended-sprites.js'),contentType:'text/javascript'}));
  await model.goto(base);await model.waitForTimeout(500);
  await model.evaluate(()=>{
   const canvas=document.querySelector('#world');document.body.replaceChildren(canvas);document.body.classList.add('is-playing');Object.assign(canvas.style,{width:'960px',height:'540px',position:'relative',display:'block'});
   window.ascendedArtRoom={code:'model-fixture',you:'a',phase:'combat',mode:'adventure',stage:4,region:'cavern',areaSize:[960,540],classes:{},players:[{id:'a',name:'Sovereign Guardian',class:'Knight',ascended:true,x:360,y:300,hp:150,maxHp:150,status:'alive',facingX:0,facingY:1,connected:true},{id:'b',name:'Seraphic Keeper',class:'Healer',ascended:true,x:600,y:300,hp:110,maxHp:110,status:'alive',facingX:0,facingY:1,connected:true}],summons:[],enemies:[],effects:[],projectiles:[],hazards:[],pings:[],environment:{obstacles:[],zones:[],barriers:[]},adventure:{area:'cave_entry',dungeon:{type:'underground'},features:[],exits:[]}};
   GauntletAscendedSprites.observe(ascendedArtRoom);GauntletCombatEnvironment.observe(ascendedArtRoom);GauntletProjectiles.observe(ascendedArtRoom);
  });
  await model.waitForTimeout(800);
  for(const region of ['cavern','woodland'])for(const state of ['idle','move','basic','signature']){
   await model.evaluate(({region,state})=>{
    const r=ascendedArtRoom;r.region=region;r.adventure=region==='cavern'?{area:'cave_entry',dungeon:{type:'underground'},features:[],exits:[]}:{area:'road',features:[],exits:[]};
    for(const p of r.players){p.moving=state==='move';p.abilityAnimation=['basic','signature'].includes(state)?{id:p.id+state,heroClass:p.class,stage:4,abilityId:state==='basic'?'basic':'signature',kind:state==='basic'?'damage':'ascend_'+p.class.toLowerCase(),attackType:state==='basic'?'light':'special',elapsed:state==='basic'?.05:.63,releaseAt:state==='basic'?0:.6,duration:1,remaining:.5,facingX:0,facingY:1}:null;}
    GauntletAbilityAnimations.observe(r);GauntletAscendedSprites.observe(r);drawWorld(r);
   },{region,state});
   await model.locator('#world').screenshot({path:path.join(out,'prototype-'+region+'-'+state+'.png')});
  }
  fs.writeFileSync(path.join(out,'review.json'),JSON.stringify({scope:'Ordinary disposable UI game plus explicitly separate renderer model fixtures',messages,requests},null,2));
  console.log('Saved UI and two-form prototype views; diagnostics '+messages.length);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
