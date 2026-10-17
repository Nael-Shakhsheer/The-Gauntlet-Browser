// Local authoring preview plus the requested focused ability readiness check.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');const base=path.join(__dirname,'..');
const stripBom=s=>s.replace(/^\uFEFF/,'');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.GAUNTLET_ART_BROWSER || 'msedge'});const page=await browser.newPage({viewport:{width:1100,height:1600}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try {
  for(const [folder,file,output] of [['adventure-sprites','preview.html','preview.png'],['adventure-sprites','regional-preview.html','regional-preview.png'],['projectile-animations','preview.html','preview.png']]){
   await page.goto('file:///'+path.join(base,'art',folder,file).replaceAll('\\','/'));
   await page.waitForTimeout(1300);
   if(errors.length)throw new Error('Artwork preview: '+errors.join('; '));
   await page.locator('canvas').screenshot({path:path.join(base,'art',folder,output)});
   if(folder==='adventure-sprites'&&file==='preview.html'){await page.locator('button').click();await page.waitForTimeout(300);await page.locator('canvas').screenshot({path:path.join(base,'art',folder,'preview-complete.png')});}
  }
  if(process.argv.includes('--art-only')){console.log('Local artwork previews saved. No game rooms or saves were opened.');return;}
  const app=stripBom(fs.readFileSync(path.join(base,'static/app.js'),'utf8'));
  const functions=app.slice(app.indexOf('function renderAbilityBar('),app.indexOf('function renderClasses('));
  const icon=app.slice(app.indexOf('function createAbilityIcon('),app.indexOf('function decorateAbilityChoice(')).replace('image.src="/sprites/ability-"+ability.id+"-v1.png"','image.src=window.GauntletReadinessArt[ability.id]');
  const images=Object.fromEntries(['piercing_volley','snare_shot','deadeye'].map(id=>[id,'data:image/png;base64,'+fs.readFileSync(path.join(base,'static/sprites/ability-'+id+'-v1.png')).toString('base64')]));
  const css=stripBom(fs.readFileSync(path.join(base,'static/style.css'),'utf8'));
  await page.setContent('<style>'+css+'</style><body class="is-playing"><div class="ability-center"><div class="hud-actions"><button id="attackButton"></button></div><div id="abilityButtons" class="ability-buttons"></div></div></body>');
  await page.evaluate(({functions,icon,images})=>{
   window.GauntletReadinessArt=images;
   window.$=s=>document.querySelector(s);window.lastAbilityBarSignature='';window.abilityRingRecords=new Map();window.keyBindings={special:'q',ultimate:'x'};
   window.ABILITY_SPRITE_KEYS=new Set(['piercing_volley','snare_shot','deadeye']);eval(icon);window.createAbilityIcon=createAbilityIcon;
   eval(functions);window.renderAbilityBar=renderAbilityBar;
   window.fixture={code:'css',you:'hero',phase:'combat',mana:100,players:[{id:'hero',status:'alive'}],abilitySlots:['light','special','ultimate'].map((attackType,i)=>({id:['piercing_volley','snare_shot','deadeye'][i],attackType,name:attackType,description:'Fixture',manaCost:i*10,cooldown:15,cooldownRemaining:0}))};
   renderAbilityBar(fixture);
  },{functions,icon,images});
  async function styles(){return page.locator('.ability-icon-button').evaluateAll(buttons=>buttons.map(b=>({state:b.dataset.charge,color:getComputedStyle(b).getPropertyValue('--ring-color').trim(),stroke:getComputedStyle(b.querySelector('.ability-ring-fill')).stroke,outline:getComputedStyle(b.querySelector('.ability-orb')).outlineColor,filter:getComputedStyle(b.querySelector('.ability-sprite')).filter})));}
  for(const width of [1280,390]){await page.setViewportSize({width,height:844});const found=await styles();assert.equal(found.length,3);for(const b of found){assert.equal(b.state,'ready');assert.equal(b.color,'#70f09b');assert.equal(b.stroke,'rgb(112, 240, 155)');assert.equal(b.outline,'rgb(112, 240, 155)');assert.ok(b.filter.includes('112, 240, 155'));}}
  await page.evaluate(()=>{fixture.abilitySlots.forEach(a=>a.cooldownRemaining=4);renderAbilityBar(fixture);});
  for(const b of await styles()){assert.equal(b.state,'charging');assert.equal(b.stroke,'rgb(255, 87, 87)');assert.equal(b.filter,'none');}
  await page.evaluate(()=>{fixture.abilitySlots.forEach(a=>a.cooldownRemaining=0);fixture.mana=0;renderAbilityBar(fixture);});
  assert.deepEqual((await styles()).map(b=>b.state),['ready','charging','charging']);
  await page.evaluate(()=>{fixture.mana=100;fixture.abilitySlots[1].summonAlive=true;renderAbilityBar(fixture);});assert.equal((await styles())[1].state,'active');
  await page.evaluate(()=>{fixture.players[0].status='downed';renderAbilityBar(fixture);});assert.ok((await styles()).every(b=>b.state!=='ready'));
  console.log('Readiness CSS checks passed for Light/Special/Ultimate at desktop and narrow width; cooldown, mana, active summon and downed guards. Artwork previews saved.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
