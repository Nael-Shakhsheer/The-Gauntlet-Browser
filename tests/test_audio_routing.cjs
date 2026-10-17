const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const s={window:{}};vm.createContext(s);vm.runInContext(fs.readFileSync('static/audio-routing.js','utf8'),s);
const routing=s.window.GauntletAudioRouting,room={you:'me'};
const route=e=>routing.route({id:10,heroClass:'Knight',ownerId:'me',...e},room);
assert.ok(route({kind:'hit'}).gain<.12);assert.ok(route({kind:'hit'}).priority<route({kind:'ability',attackType:'light'}).priority);
assert.ok(route({kind:'hurt'}).interval>=450);assert.equal(route({kind:'summon_attack'}),false);
for(const family of routing.families){assert.equal(route({kind:'projectile_launch',family,side:'hero'}).name,family+'-launch');assert.equal(route({kind:'projectile_launch',family,side:'enemy'}).name,'enemy-'+family+'-launch');}
assert.equal(route({kind:'projectile_impact',family:'arrow',material:'wood',side:'hero'}).name,'hit-wood');
assert.equal(route({kind:'projectile_impact',family:'fire',material:'flesh',targetId:'e',side:'hero'}).name,'fire-impact');
assert.equal(route({kind:'projectile_impact',side:'enemy',targetId:'me'}),false);
for(const hero of ['Knight','Rogue','Wizard','Druid','Archer','Cleric','Bard','Healer']){
 const e={heroClass:hero,kind:'ascension'};assert.equal(route(e).name,'ascend-'+hero.toLowerCase());assert.equal(route({...e,kind:'ascended_release'}).name,'ascended-'+hero.toLowerCase());
 assert.equal(route({...e,kind:'ability',attackType:'light',ascended:true}).name,'ascended-'+hero.toLowerCase()+'-light');
}
for(const kind of ['conversation_open','conversation_close','inspect','skill_learn','rune_gain','rune_spend','quest_accept','quest_report']){assert.equal(route({kind}).bus,'ui');assert.equal(route({kind}).local,true);}
const bank=JSON.parse(fs.readFileSync('art/audio/sounds.json'));
for(const name of routing.extra)assert.ok(bank.sounds[name],name+' retained editable recipe');
console.log('Routing: quiet material hits, coherent projectile release/impact, hostile identities, all Ascended kits, private UI and editable recipes passed.');
