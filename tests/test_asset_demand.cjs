// Demand loading must preserve dynamic paths and reuse pending/loaded resources.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const requests=[];class Image{constructor(){this.complete=true;this.naturalWidth=612;}set src(url){assert.ok(fs.existsSync('static/'+url.replace(/^\//,'')),url);requests.push(url);}}
const source=fs.readFileSync('static/app.js','utf8');
const app={Image,fetch:async url=>({ok:true,json:async()=>JSON.parse(fs.readFileSync('static/'+url.replace(/^\//,'')))}),fieldArt:{},forkArt:{},fieldArtRevision:0,forkArtRevision:0,terrainKey:'',forkTerrainKey:''};vm.createContext(app);
vm.runInContext(source.slice(source.indexOf('function regionalImage('),source.indexOf('const glowLayers')),app);
vm.runInContext(source.slice(source.indexOf('const heroSprites = {}'),source.indexOf('function drawImportedHero(')),app);
assert.equal(requests.length,0,'No hero/enemy or fallback region sheets on menu');
for(const role of ['Knight','Dragon','Druid','IceBear','ShrineGuardian']){
 app.role=role;vm.runInContext('importedSprite(role);importedSprite(role)',app);
}
assert.equal(requests.length,5,'Each encountered role requests once');
for(const region of ['woodland','ruins','cavern','frost']){
 app.region=region;for(const kind of ['field','fork']){app.kind=kind;vm.runInContext('regionalImage(region,kind);regionalImage(region,kind)',app);}
}
assert.equal(requests.length,13);assert.equal(vm.runInContext('importedSprite("Unknown")',app),null);
let combatRequests=0;const box={Image:class extends Image{set src(url){combatRequests++;super.src=url;}},window:{},document:{createElement:()=>({})},performance:{now:()=>0}};
vm.runInNewContext(fs.readFileSync('static/combat-environment.js','utf8'),box);assert.equal(combatRequests,0,'No enemy attack/cover atlases before play');
const metadata=Object.fromEntries(['landmarks','props','signals','npcs','discoveries'].map(k=>[k,JSON.parse(fs.readFileSync('static/sprites/adventure-'+k+'-v1.json'))]));
let adventureRequests=0;const a={Image:class extends Image{set src(url){adventureRequests++;super.src=url;}},window:{GauntletAdventureSpriteMetadata:metadata},document:{currentScript:null,createElement:()=>({})},performance:{now:()=>0}};
vm.runInNewContext(fs.readFileSync('static/adventure-sprites.js','utf8'),a);assert.equal(adventureRequests,0,'No Adventure terrain/prop sheets on menu');
const ctx={save(){},restore(){},drawImage(){}};a.window.GauntletAdventureSprites.stamp(ctx,'camp_tent',0,0);a.window.GauntletAdventureSprites.stamp(ctx,'camp_tent',0,0);assert.equal(adventureRequests,1);
console.log('Demand loading: current heroes, enemies, regional fallbacks and Adventure packs only; valid paths and no duplicate requests.');
