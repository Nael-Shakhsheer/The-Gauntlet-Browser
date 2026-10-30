/* Server-owned unlocks, loadouts and permanent character purchases. */
(() => {
  let busy=false,signature='',branch='',hero='',section='learn',sectionScroll={},purchasePreview=null,purchaseId=null;
  const add=(box,tag,text,cls='')=>{const el=document.createElement(tag);el.textContent=text;el.className=cls;box.append(el);return el;};
  const milestoneNames={arrival:'Arrive in Oakvale',road:'Explore Southern road',inn:'Meet the innkeeper',hunter:'Recover the hunter',bridge:'Restore the bridge',shrine:'Restore the shrine',alcove:'Find the surveyor cache',cave:'Clear Rootwater',floor1:'Briarwatch floor 1',floor2:'Briarwatch floor 2',tower:'Clear Briarwatch',region:'Secure the woodland'};
  const labels={basic:'Basic',active1:'Active 1',active2:'Active 2',active3:'Active 3',ultimate:'Ultimate'};
  const gateNames={aurelian:'Aurelian’s refuge',verdant:'Rootsong in the Verdant Veil',cinder:'the first Cinder Crown sanctuary'};
  const binding=s=>{const key=keyBindings[s==='active1'?'special':s];return s==='basic'?'Hold':key===' '?'Space':String(key).toUpperCase();};
  async function act(action,data={}){
    if(busy)return;const owner=session;busy=true;signature='';render(latestRoom);notice($('#heroSkillsNotice'),'Applying…');
    try{await sendAction(action,data);if(session===owner)notice($('#heroSkillsNotice'),'Updated.','success');}
    catch(e){if(session===owner)notice($('#heroSkillsNotice'),e.message,'error');}finally{if(session===owner){busy=false;signature='';refresh();render(latestRoom);}}
  }
  function renderMagic(room){
    const m=room.adventure?.magicRunes;if(!m)return;
    let panel=document.getElementById('magicProgression');
    if(!panel){panel=document.createElement('details');panel.id='magicProgression';panel.dataset.focusKey='magic-details';$('#heroAscensionPurchases').append(panel);}
    panel.replaceChildren();panel.open=true;add(panel,'summary',m.ascended?'Ascended · '+m.balance+' Magic Runes':m.balance+' Magic Runes');
    for(const kind of ['health','mana','ascend']){
      const maxed=kind==='health'?m.healthRanks>=5:kind==='mana'?m.manaRanks>=5:m.ascended;
      const text=kind==='health'?'Health '+m.healthBefore+' → '+m.healthAfter+' · 1 rune · '+m.healthRanks+'/5':kind==='mana'?'Mana '+m.manaBefore+' → '+m.manaAfter+' · 1 rune · '+m.manaRanks+'/5':'Preview Ascension · 15 unspent runes';
      const button=add(panel,'button',maxed&&kind==='ascend'?'Ascended':text,'secondary small');button.disabled=busy||maxed;
      window.GauntletUI.control(button,'preview-'+kind);button.dataset.state=maxed?'unlocked':'available';
      button.onclick=()=>{purchasePreview=kind;purchaseId=crypto.randomUUID().replaceAll('-','');signature='';render(latestRoom);};
    }
    if(purchasePreview){
      const kind=purchasePreview,box=add(panel,'section','','magic-preview');panel.open=true;
      add(box,'h3',kind==='ascend'?'Permanent Ascension':'Permanent '+kind+' rank');
      add(box,'p',kind==='ascend'?'15 Magic Runes · Health '+m.healthBefore+' → '+m.ascendHealth+' · Mana '+m.manaBefore+' → '+m.ascendMana+' · Damage +8%. Signature and passives unlock.':'1 Magic Rune · '+(kind==='health'?'Health '+m.healthBefore+' → '+m.healthAfter:'Mana '+m.manaBefore+' → '+m.manaAfter));
      add(box,'small','Permanent purchase. Current resource proportions and recharge stay.');
      const confirm=add(box,'button','Confirm purchase','primary small'),cancel=add(box,'button','Back','secondary small');
      window.GauntletUI.control(confirm,'magic-confirm','primary');window.GauntletUI.control(cancel,'magic-back','navigation');
      confirm.disabled=busy||!m.safe||(kind==='ascend'&&!m.ascensionEligible)||m.balance<(kind==='ascend'?15:1)||(kind==='health'?m.healthRanks>=5:kind==='mana'?m.manaRanks>=5:m.ascended);
      if(kind==='ascend'&&!m.ascensionEligible)add(box,'p','Ascension opens after you report the conclusion of Dunmere’s harvest and water investigation. Ordinary hero skills are available in Oakvale.','subtle');
      if(!m.safe)add(box,'p','Return safely to a village and finish any conversation to commit.','subtle');
      cancel.onclick=()=>{purchasePreview=null;signature='';render(latestRoom);};
      confirm.onclick=async()=>{
        if(busy)return;busy=true;signature='';render(latestRoom);const owner=session;
        try{await sendAction('magicPurchase',{purchase:kind,requestId:purchaseId,expectedRank:kind==='health'?m.healthRanks:m.manaRanks});if(session===owner){purchasePreview=null;notice($('#heroSkillsNotice'),'Purchase confirmed.','success');if(kind==='ascend')window.showAscensionRitual?.(room);}}
        catch(e){if(session===owner)notice($('#heroSkillsNotice'),e.message,'error');}
        finally{if(session===owner){busy=false;signature='';await refresh();render(latestRoom);}}
      };
    }
  }
  function render(room){
    const h=room?.heroSkills;if(!h)return;
    $('#heroSkillsButton').textContent='Skills'+(h.points?' · '+h.points:'');
    if(!$('#heroSkillsDialog').open)return;
    if(hero!==h.hero){hero=h.hero;branch='';section='learn';sectionScroll={};}
    const knownBranches=[...new Set(h.nodes.filter(n=>n.branch!=='Ascension').map(n=>n.branch))];if(!knownBranches.includes(branch))branch=knownBranches[0];
    const liveSummons=(room.abilities||[]).some(a=>a.summonAlive);
    const sig=JSON.stringify([h,room.adventure?.magicRunes,liveSummons,busy,branch,section,purchasePreview,keyBindings]);if(sig===signature)return;signature=sig;
    for(const button of $('#heroSkillSections').querySelectorAll('[data-skill-section]')){const selected=button.dataset.skillSection===section;button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;button.dataset.uiAction='navigation';}
    for(const [key,id]of Object.entries({learn:'skillLearn',loadout:'skillLoadout',ascension:'skillAscension'}))$('#'+id).hidden=section!==key;
    $('#heroSkillsDialog').dataset.safe=String(h.safe);
    $('#heroSkillsTitle').textContent=h.hero+(room.adventure?.magicRunes?.ascended?' · Ascended':'')+' · Skills';$('#heroSkillsPoints').textContent=h.points+' skill points available';$('#heroSkillsPoints').title=h.earned+' earned from milestones';
    $('#heroSkillsSafety').textContent=h.safe?'Learn and equip here. '+h.activeSlots+' active slots open.':'Inspect here; learn and equip in a village or secured sanctuary after closing conversations.';
    window.GauntletUI.preserve($('#heroSkillsContent'),()=>{
    const decisions=$('#heroSkillActions');decisions.replaceChildren();
    const recommended=h.buildAdvice?.options?.map(n=>n.id)||[];
    const available=h.nodes.filter(n=>n.regionReady!==false&&!n.starter&&n.rank<n.maxRank&&!(n.unlocked&&n.type==='ability')&&n.cost<=h.points&&n.requires.every(id=>h.nodes.find(v=>v.id===id)?.unlocked)).sort((x,y)=>Number(recommended.includes(y.id))-Number(recommended.includes(x.id)));
    add(decisions,'strong',available.length?available.length+' affordable upgrades':'No affordable upgrade yet');
    for(const n of available.slice(0,2)){const b=add(decisions,'button',n.name+' · '+n.cost+' SP','secondary small');window.GauntletUI.control(b,'afford-'+n.id,'navigation');b.onclick=()=>{branch=n.branch;signature='';render(latestRoom);};}
    let advice=document.getElementById('heroBuildAdvice');
    if(h.buildAdvice){
      if(!advice){advice=document.createElement('details');advice.id='heroBuildAdvice';advice.dataset.focusKey='build-advice';decisions.after(advice);}
      const wasOpen=advice.open;advice.replaceChildren();advice.open=wasOpen;
      add(advice,'summary','Solo and party builds');add(advice,'p',h.buildAdvice.text,'subtle');
      for(const option of h.buildAdvice.options){const b=add(advice,'button','Inspect '+option.name+' · '+option.cost+' SP','secondary small');window.GauntletUI.control(b,'advice-'+option.id,'navigation');b.onclick=()=>{branch=option.branch;signature='';render(latestRoom);};}
    }else if(advice)advice.remove();
    renderMagic(room);
    const cat=h.nodes.filter(n=>n.type==='ability'),load=$('#heroLoadout');load.replaceChildren();
    for(const s of Object.keys(labels)){
      const index=s.startsWith('active')?Number(s.at(-1))-1:null,locked=index!==null&&index>=h.activeSlots;
      const aid=index!==null?h.loadout.active[index]:h.loadout[s],category=s==='basic'?'light':s==='ultimate'?'ultimate':'special';
      const label=add(load,'label','','skill-slot');add(label,'span',labels[s]);add(label,'kbd',binding(s));
      const select=add(label,'select','');select.setAttribute('aria-label',labels[s]);window.GauntletUI.control(select,'slot-'+s);label.dataset.state=locked?'locked':aid?'equipped':'empty';
      if(s!=='basic'){const o=add(select,'option',locked?'Opens with exploration':'Empty');o.value='';}
      for(const n of cat.filter(n=>n.unlocked&&n.current.attackType===category)){const o=add(select,'option',n.name);o.value=n.id;}
      select.value=aid||'';select.disabled=busy||!h.safe||locked;select.onchange=()=>act('skillEquip',{slot:s,ability:select.value||null});
      label.title=locked?'Active 2: explore Southern road. Active 3: complete a woodland quest.':!h.safe?'Use a village or secured sanctuary and finish the conversation to change abilities.':'';
    }
    const branches=[...new Set(h.nodes.filter(n=>n.branch!=='Ascension').map(n=>n.branch))];if(!branches.includes(branch))branch=branches[0];
    let presets=document.getElementById('heroPresets');if(!presets){presets=document.createElement('details');presets.id='heroPresets';presets.dataset.focusKey='presets';load.after(presets);}
    presets.replaceChildren();add(presets,'summary','Saved builds · '+h.hero);add(presets,'p','Recall at a village or secured sanctuary. Resources and all recharge stay; live summons must be dismissed first.','subtle');
    for(let i=1;i<=3;i++){
      const saved=h.presets?.entries[h.hero+':'+i],row=add(presets,'div','','preset-row');add(row,'strong','Build '+i);
      if(saved)add(row,'p',[saved.basic,...saved.active,saved.ultimate].filter(Boolean).map(id=>h.nodes.find(n=>n.id===id)?.name||id).join(' · '),'subtle');
      const recallReason=liveSummons?'Wait until your active summons are gone.':saved&&saved.active.some((id,index)=>id&&index>=h.activeSlots)?'This build needs an active slot that is not open yet.':saved&&[saved.basic,...saved.active,saved.ultimate].filter(Boolean).some(id=>!h.nodes.find(n=>n.id===id)?.unlocked)?'Learn every ability in this build before recalling it.':'';
      for(const [action,label] of [['presetSave',saved?'Replace with equipped':'Save equipped'],['presetApply','Recall'],['presetDelete','Clear']]){const b=add(row,'button',label,'secondary small');window.GauntletUI.control(b,action+'-'+i);const reason=busy?'Applying the previous change.':!h.safe?'Use a village or secured sanctuary and finish the conversation.':action!=='presetSave'&&!saved?'Save a build here first.':action==='presetApply'?recallReason:'';b.disabled=Boolean(reason);b.title=reason;b.onclick=()=>act(action,{preset:i,revision:h.presets?.revision||0});}
    }
    const tabs=$('#heroBranches');tabs.replaceChildren();for(const b of branches){const button=add(tabs,'button',b,'secondary small');window.GauntletUI.control(button,'branch-'+b,'navigation');button.setAttribute('aria-pressed',String(b===branch));button.onclick=()=>{branch=b;signature='';render(latestRoom);};}
    const box=$('#heroNodes'),ascended=$('#heroAscensionNodes');box.replaceChildren();ascended.replaceChildren();
    if(!room.adventure?.magicRunes?.ascended)add(ascended,'p','Ascension: report Dunmere’s investigation and keep 15 Magic Runes.','subtle skill-section-hint');
    for(const n of h.nodes.filter(n=>n.branch===branch||n.branch==='Ascension')){
      const card=add(n.branch==='Ascension'?ascended:box,'article','','hero-node');card.dataset.focusGroup=n.id;card.tabIndex=-1;card.dataset.unlocked=String(n.unlocked);card.dataset.state=n.equipped?'equipped':n.unlocked?'unlocked':'locked';card.dataset.nodeType=n.type;
      const title=add(card,'h3',n.name);{const icon=createAbilityIcon(n.current||{id:n.id});if(icon)title.prepend(icon);}
      add(card,'small',(n.type==='ability'?n.current.attackType+' ability':n.type)+' · '+(n.equipped?'Equipped':n.unlocked?'Unlocked':'Locked')+(n.maxRank>1?' · rank '+n.rank+'/'+n.maxRank:''));
      const current=n.unlocked?(n.rank?n.effects[n.rank-1]:n.effects[0]):'Not learned';add(card,'p','Current: '+current);
      if(n.rank<n.maxRank && (!n.starter||n.branch==='Ascension') && !(n.unlocked&&n.type==='ability'))add(card,'p','Next: '+n.effects[n.rank]);
      if(n.current)add(card,'p',(n.current.manaCost||0)+' mana · '+n.current.cooldown+'s recharge · '+(n.current.range?n.current.range+'px range':'self / party'),'subtle');
      if(n.current && n.unlocked){
        const category=n.current.attackType,slots=category==='light'?['basic']:category==='ultimate'?['ultimate']:['active1','active2','active3'];
        const equipped=slots.find(s=>s.startsWith('active')?h.loadout.active[Number(s.at(-1))-1]===n.id:h.loadout[s]===n.id);
        if(equipped)add(card,'p','Equipped · '+labels[equipped]+' · '+binding(equipped),'subtle');
        else for(const slot of slots){const locked=slot.startsWith('active')&&Number(slot.at(-1))>h.activeSlots,b=add(card,'button','Equip · '+binding(slot),'secondary small');window.GauntletUI.control(b,'equip-'+n.id+'-'+slot);b.setAttribute('aria-label','Equip '+n.name+' in '+labels[slot]+' · '+binding(slot));b.dataset.equipSkill=n.id;b.disabled=busy||!h.safe||locked;b.title=locked?'Explore Southern road for Active 2; complete a woodland quest for Active 3.':!h.safe?'Return to a village or secured sanctuary and finish the conversation.':'';b.onclick=()=>act('skillEquip',{slot,ability:n.id});}
        if(n.maxUpgradeRank){const r=n.upgradeRank||0;add(card,'p','Upgrade '+r+'/'+n.maxUpgradeRank+(r?' · '+n.upgradeEffect:''),'subtle');if(r<n.maxUpgradeRank){const b=add(card,'button','Upgrade · 1 SP','secondary small');window.GauntletUI.control(b,'upgrade-'+n.id);b.dataset.upgradeSkill=n.id;b.disabled=busy||!h.safe||h.points<1;b.title=n.upgradeNext;b.onclick=()=>act('skillUpgrade',{ability:n.id,expectedRank:r});add(card,'p','Next: '+n.upgradeNext,'subtle');}}
      }
      const missing=n.requires.filter(id=>!h.nodes.find(v=>v.id===id)?.unlocked);
      if(n.requires.length)add(card,'p','Requires: '+n.requires.map(id=>h.nodes.find(v=>v.id===id)?.name||id).join(', '),'subtle');
      if(!n.starter && n.rank<n.maxRank && !(n.unlocked&&n.type==='ability')){
        const button=add(card,'button',(n.rank?'Improve':'Unlock')+' · '+n.cost+' points','secondary small');button.disabled=busy||!h.safe||n.regionReady===false||Boolean(missing.length)||h.points<n.cost;button.onclick=()=>act('skillUnlock',{node:n.id,expectedRank:n.rank});
        window.GauntletUI.control(button,'learn-'+n.id,'primary');button.dataset.state=button.disabled?'locked':'available';
        if(button.disabled)add(card,'p',busy?'Applying the previous change.':!h.safe?'Use a village or activated sanctuary after closing the conversation.':n.regionReady===false?'Reach '+(gateNames[n.campaignGate]||n.campaignGate)+' to learn this skill.':missing.length?'First learn '+missing.map(id=>h.nodes.find(v=>v.id===id)?.name||id).join(', ')+'.':'Need '+(n.cost-h.points)+' more milestone points.','subtle');
      }
    }
    const milestones=$('#heroMilestones');milestones.replaceChildren();for(const m of h.milestones)add(milestones,'p',(m.earned?'✓ ':'○ ')+(milestoneNames[m.id]||m.id)+' · '+m.points+' points','subtle');
    const legacy=Object.entries(h.legacyTraining).filter(([,v])=>v);if(legacy.length)add(milestones,'p','Preserved earlier training: '+legacy.map(([k,v])=>k+' '+v).join(', '));
    $('#heroRespec').disabled=busy||!h.safe;
    });
  }
  function selectSection(value){sectionScroll[section]=$('#heroSkillsContent').scrollTop;section=value;signature='';render(latestRoom);$('#heroSkillsContent').scrollTop=sectionScroll[value]||0;}
  $('#heroSkillSections').onclick=e=>{const b=e.target.closest('[data-skill-section]');if(b)selectSection(b.dataset.skillSection);};
  $('#heroSkillSections').onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const tabs=[...$('#heroSkillSections').querySelectorAll('[data-skill-section]')],i=tabs.findIndex(b=>b.dataset.skillSection===section),next=e.key==='Home'?0:e.key==='End'?2:(i+(e.key==='ArrowRight'?1:2))%3;selectSection(tabs[next].dataset.skillSection);tabs[next].focus();};
  $('#heroSkillsButton').onclick=()=>{openInfo('heroSkillsDialog');signature='';render(latestRoom);};
  $('#heroRespec').onclick=()=>act('skillRespec');
  window.renderHeroSkills=render;window.resetHeroSkills=()=>{signature='';branch='';hero='';section='learn';sectionScroll={};busy=false;purchasePreview=null;purchaseId=null;$('#heroSkillsNotice').textContent='';};
  window.drawHeroSkillZones=(ctx,room)=>{
    if(window.GauntletCombatVisuals)return window.GauntletCombatVisuals.zones(ctx,room);
    const colors={banner:'#d8c48a',beacon:'#a9f1ed',hallowed:'#ffe09d',spring:'#8de5a4',rift:'#b6a6f3',trap:'#d5c397',ascension_commitment:'#e9d4a3'};
    for(const z of room.skillZones||[]){ctx.save();ctx.strokeStyle=colors[z.kind]||'#c7e5b2';ctx.fillStyle=ctx.strokeStyle+'16';ctx.lineWidth=2;ctx.beginPath();ctx.arc(z.x,z.y,z.radius,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.beginPath();ctx.moveTo(z.x-7,z.y);ctx.lineTo(z.x+7,z.y);ctx.moveTo(z.x,z.y-7);ctx.lineTo(z.x,z.y+7);ctx.stroke();ctx.restore();}
  };
})();
