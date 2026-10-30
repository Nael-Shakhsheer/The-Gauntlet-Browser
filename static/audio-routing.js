/* Presentation policy shared by live playback and the review harness. */
(() => {
 const families=['arrow','blade','fire','frost','lightning','arcane','sacred','nature','mixture','tonal','shadow','stone'];
 const materials=['flesh','metal','wood','stone','barrier','magic'];
 const extra=['ui-nav','ui-confirm','ui-reject','conversation-open','conversation-close','inspect','door','stairs','mechanism','skill-learn','rune-gain','rune-spend','shrine-activate','quest-accept','quest-progress','quest-report','portal-travel','portal-charge','defeat-soft','hit-significant','amb-leaves','amb-wildlife','amb-tools','amb-droplet','amb-creak','amb-dry',
  ...families.flatMap(f=>[f+'-launch','enemy-'+f+'-launch',f+'-impact']),...materials.flatMap(m=>['hit-'+m,'hit-'+m+'-1','hit-'+m+'-2']),
  ...['knight','rogue','wizard','druid','archer','cleric','bard','healer'].flatMap(h=>['ascend-'+h,'ascended-'+h,'ascended-'+h+'-light'])];
 const interactions={conversation_open:'conversation-open',conversation_close:'conversation-close',inspect:'inspect',door:'door',stairs:'stairs',mechanism:'mechanism',skill_learn:'skill-learn',loadout:'equip',equip:'equip',purchase:'purchase',sell:'purchase',rune_gain:'rune-gain',rune_spend:'rune-spend',shrine_activate:'shrine-activate',quest_accept:'quest-accept',quest_progress:'quest-progress',quest_report:'quest-report'};
 function route(e,r){
  const owner=e.ownerId===r?.you,local=owner||e.personal,hero=String(e.heroClass||'wizard').toLowerCase();
  const base={local:Boolean(local),x:e.x,y:e.y,owner:e.ownerId||'',gain:.16,priority:2,group:e.kind,interval:180,bus:'effects'};
  if(interactions[e.kind])return {...base,name:interactions[e.kind],local:e.kind==='shrine_activate'?owner:true,bus:e.kind==='shrine_activate'?'effects':'ui',gain:['rune_gain','quest_report','shrine_activate'].includes(e.kind)?.32:.16,priority:['quest_report','shrine_activate'].includes(e.kind)?4:2,group:'interaction',interval:160};
  switch(e.kind){
   case 'magic_acquired':return owner?{...base,name:'rune-gain',local:true,bus:'ui',gain:.32,priority:4,group:'magic-acquired',interval:500,duck:'rune'}:false;
   case 'portal_arrive':return {...base,name:'portal-travel',local:true,gain:.25,priority:3,interval:1000};
   case 'portal_charge':return {...base,name:'portal-charge',local:true,bus:'ui',gain:.17,priority:2,interval:1000};
   case 'ability':
    if(e.silentLaunch)return false;
    return {...base,name:e.ascended&&e.attackType==='light'?'ascended-'+hero+'-light':e.abilityId==='frost_lance'?'frost-launch':hero+'-'+(e.attackType||'light')+(e.attackType==='light'&&e.id%3?'-'+e.id%3:''),
     gain:e.attackType==='light'?(owner?.21:.11):String(e.abilityKind).startsWith('ascend_')?.16:owner?.40:.23,priority:e.attackType==='light'?(owner?2:1):owner?4:3,group:e.attackType==='light'?'light':'major',interval:e.attackType==='light'?220:200};
   case 'projectile_launch':return {...base,name:e.ascended?'ascended-'+hero+'-light':(e.side==='enemy'?'enemy-':'')+(families.includes(e.family)?e.family:'arcane')+'-launch',gain:e.summon?.055:owner?.20:.12,priority:e.summon?0:e.side==='enemy'?3:2,group:e.summon?'summon':'projectile',owner:e.summon?'':e.ownerId,interval:e.summon?450:180};
   case 'projectile_impact':
    if(e.side==='enemy'&&e.targetId)return false; // local hurt already conveys the hit
    return {...base,local:false,name:e.material&&(['arrow','blade','stone'].includes(e.family)||!e.targetId)?'hit-'+(e.material==='crate'?'wood':materials.includes(e.material)?e.material:'stone'):(families.includes(e.family)?e.family:'arcane')+'-impact',gain:e.summon?.05:e.significant?.18:.11,priority:e.summon?0:e.significant?3:1,group:e.summon?'summon-impact':'impact',owner:e.summon?'':e.ownerId,interval:e.summon?450:190};
   case 'hit':{
    if(e.silentImpact)return false;
    const material=e.element? e.element==='Ice'?'frost':e.element==='Fire'?'fire':e.element==='Storm'?'lightning':e.element==='Nature'?'nature':'arcane':null;
    const variant=e.id%3;
    return {...base,local:false,name:e.significant?'hit-significant':material?material+'-impact':'hit-'+(materials.includes(e.material)?e.material:'flesh')+(variant?'-'+variant:''),gain:e.summon||e.periodic?.05:e.significant?.19:.105,priority:e.significant?3:0,group:e.periodic?'periodic':e.summon?'summon-impact':'impact',owner:e.summon||e.periodic?'':e.ownerId,interval:e.periodic?500:e.summon?450:200,pitch:1+((e.id%3)-1)*.008};
   }
   case 'material':return {...base,local:false,name:'hit-'+(e.material==='crate'?'wood':'stone'),gain:.09,priority:0,group:'impact',owner:'',interval:230};
   case 'hurt':return {...base,name:e.warded?'hit-barrier':'hurt',gain:owner?(e.heavy?.32:.22):.08,priority:owner?(e.heavy?5:3):1,group:'hurt',interval:450};
   case 'blocked':return {...base,name:'hit-barrier',gain:owner?.16:.07,priority:2,interval:350};
   case 'enemy_defeat':return e.boss?false:{...base,local:false,name:'defeat-soft',gain:.12,priority:2,group:'defeat',owner:'',interval:320};
   case 'summon_attack':return false; // actual launch or hit already conveys the attack
   case 'ascension':return {...base,name:'ascend-'+hero,local:owner,gain:owner?.48:.27,priority:owner?4:3,group:'transformation',interval:1000};
   case 'ascended_release':return {...base,name:'ascended-'+hero,gain:owner?.4:.22,priority:4,interval:350};
   default:return null;
  }
 }
 window.GauntletAudioRouting={route,extra,families,materials};
})();
