/* Server-owned unlocks, loadouts and permanent character purchases. */
(() => {
  let busy=false,signature='',branch='',hero='',purchasePreview=null,purchaseId=null;
  const add=(box,tag,text,cls='')=>{const el=document.createElement(tag);el.textContent=text;el.className=cls;box.append(el);return el;};
  const milestoneNames={arrival:'Arrive in Oakvale',road:'Explore Southern road',inn:'Meet the innkeeper',hunter:'Recover the hunter',bridge:'Restore the bridge',shrine:'Restore the shrine',alcove:'Find the surveyor cache',cave:'Clear Rootwater',floor1:'Briarwatch floor 1',floor2:'Briarwatch floor 2',tower:'Clear Briarwatch',region:'Secure the woodland'};
  const labels={basic:'Basic · hold attack',active1:'Active 1',active2:'Active 2',active3:'Active 3',ultimate:'Ultimate'};
  const binding=s=>s==='basic'?'Hold':String(keyBindings[s==='active1'?'special':s]).toUpperCase();
  async function act(action,data={}){
    if(busy)return;const owner=session;busy=true;signature='';render(latestRoom);notice($('#heroSkillsNotice'),'Applying…');
    try{await sendAction(action,data);if(session===owner)notice($('#heroSkillsNotice'),'Updated. Adventure saves automatically.');}
    catch(e){if(session===owner)notice($('#heroSkillsNotice'),e.message);}finally{if(session===owner){busy=false;signature='';refresh();render(latestRoom);}}
  }
  function renderMagic(room){
    const m=room.adventure?.magicRunes;if(!m)return;
    let panel=document.getElementById('magicProgression');
    if(!panel){panel=document.createElement('details');panel.id='magicProgression';$('#heroLoadout').before(panel);}
    panel.replaceChildren();add(panel,'summary',m.ascended?'Ascended · '+m.balance+' Magic Runes':m.balance+' personal Magic Runes · permanent progression');
    add(panel,'p',m.description);add(panel,'p','Collected '+m.collected+' / 16 including the optional spring find. Shared shop Runes are separate. Purchases here delay Ascension.','subtle');
    for(const kind of ['health','mana','ascend']){
      const maxed=kind==='health'?m.healthRanks>=5:kind==='mana'?m.manaRanks>=5:m.ascended;
      const text=kind==='health'?'Health '+m.healthBefore+' → '+m.healthAfter+' · 1 rune · '+m.healthRanks+'/5':kind==='mana'?'Mana '+m.manaBefore+' → '+m.manaAfter+' · 1 rune · '+m.manaRanks+'/5':'Preview Ascension · 15 unspent runes';
      const button=add(panel,'button',maxed&&kind==='ascend'?'Ascended':text,'secondary small');button.disabled=busy||maxed;
      button.onclick=()=>{purchasePreview=kind;purchaseId=crypto.randomUUID().replaceAll('-','');signature='';render(latestRoom);};
    }
    if(purchasePreview){
      const kind=purchasePreview,box=add(panel,'section','','magic-preview');panel.open=true;
      add(box,'h3',kind==='ascend'?'Permanent Ascension':'Permanent '+kind+' rank');
      add(box,'p',kind==='ascend'?'Spend 15 CURRENTLY UNSPENT Magic Runes. Health '+m.healthBefore+' → '+m.ascendHealth+', mana '+m.manaBefore+' → '+m.ascendMana+', direct damage +8%. Your hero receives the signature and two passives listed in the Ascension branch.':'Spend 1 Magic Rune. '+(kind==='health'?'Maximum health '+m.healthBefore+' → '+m.healthAfter:'Maximum mana '+m.manaBefore+' → '+m.manaAfter)+'. This uses part of the finite Ascension budget. ' + (m.chapterBudget-m.collected+m.balance-1<15?'This purchase leaves fewer than 15 possible in the currently playable chapters; further rune sources are not implemented yet.':'Keep the remaining runes to preserve this chapter’s Ascension option.') + '');
      add(box,'p','Current health/mana proportions, cooldowns and receipts are preserved. Skill respec does not refund permanent purchases.');
      const confirm=add(box,'button','Confirm purchase','primary small'),cancel=add(box,'button','Back','secondary small');
      confirm.disabled=busy||!m.safe||(kind==='ascend'&&!m.ascensionEligible)||m.balance<(kind==='ascend'?15:1)||(kind==='health'?m.healthRanks>=5:kind==='mana'?m.manaRanks>=5:m.ascended);
      if(kind==='ascend'&&!m.ascensionEligible)add(box,'p','Ascension opens after you report the conclusion of Dunmere’s harvest and water investigation. Ordinary hero skills are available in Oakvale.','subtle');
      if(!m.safe)add(box,'p','Return safely to a village and finish any conversation to commit.','subtle');
      cancel.onclick=()=>{purchasePreview=null;signature='';render(latestRoom);};
      confirm.onclick=async()=>{
        if(busy)return;busy=true;signature='';render(latestRoom);const owner=session;
        try{await sendAction('magicPurchase',{purchase:kind,requestId:purchaseId,expectedRank:kind==='health'?m.healthRanks:m.manaRanks});if(session===owner){purchasePreview=null;notice($('#heroSkillsNotice'),'Purchase confirmed.');}}
        catch(e){if(session===owner)notice($('#heroSkillsNotice'),e.message);}
        finally{if(session===owner){busy=false;signature='';await refresh();render(latestRoom);}}
      };
    }
  }
  function render(room){
    const h=room?.heroSkills;if(!h)return;
    $('#heroSkillsButton').textContent='Skills'+(h.points?' · '+h.points:'');
    if(!$('#heroSkillsDialog').open)return;
    const sig=JSON.stringify([h,room.adventure?.magicRunes,busy,branch,purchasePreview,keyBindings]);if(sig===signature)return;signature=sig;
    if(hero!==h.hero){hero=h.hero;branch='';}
    $('#heroSkillsTitle').textContent=h.hero+(room.adventure?.magicRunes?.ascended?' · Ascended':'')+' · Skills';$('#heroSkillsPoints').textContent=h.points+' points available · '+h.earned+' earned';
    $('#heroSkillsSafety').textContent=(h.safe?'Learn and equip here. Swapping preserves ability and slot recharge.':'Ordinary skills use milestone points now. Return to Oakvale or Dunmere and close NPC conversations to learn, equip or respec. Woodland skills never require Dunmere. Combat continues while a menu is open.')+(h.activeSlots<3?' Active 2 opens on the Southern road; Active 3 opens after a woodland quest.':'');
    renderMagic(room);
    const cat=h.nodes.filter(n=>n.type==='ability'),load=$('#heroLoadout');load.replaceChildren();
    for(const s of Object.keys(labels)){
      const index=s.startsWith('active')?Number(s.at(-1))-1:null,locked=index!==null&&index>=h.activeSlots;
      const aid=index!==null?h.loadout.active[index]:h.loadout[s],category=s==='basic'?'light':s==='ultimate'?'ultimate':'special';
      const label=add(load,'label',labels[s]+' · '+binding(s)),select=add(label,'select','');select.setAttribute('aria-label',labels[s]);
      if(s!=='basic'){const o=add(select,'option',locked?'Opens with exploration':'Empty');o.value='';}
      for(const n of cat.filter(n=>n.unlocked&&n.current.attackType===category)){const o=add(select,'option',n.name);o.value=n.id;}
      select.value=aid||'';select.disabled=busy||!h.safe||locked;select.onchange=()=>act('skillEquip',{slot:s,ability:select.value||null});
      if(locked)label.title='Active 2: explore Southern road. Active 3: complete a woodland quest.';
    }
    const branches=[...new Set(h.nodes.map(n=>n.branch))];if(!branches.includes(branch))branch=branches[0];
    const tabs=$('#heroBranches');tabs.replaceChildren();for(const b of branches){const button=add(tabs,'button',b,'secondary small');button.setAttribute('aria-pressed',String(b===branch));button.onclick=()=>{branch=b;signature='';render(latestRoom);};}
    const box=$('#heroNodes');box.replaceChildren();
    if(branch==='Ascension')add(box,'p','Requires the completed Dunmere investigation and 15 unspent personal Magic Runes. Ordinary skills use milestone points. Signature equipment uses an ordinary active slot. Ascension stays with this character through a permitted class change.','subtle');
    for(const n of h.nodes.filter(n=>n.branch===branch)){
      const card=add(box,'article','','hero-node');card.dataset.unlocked=String(n.unlocked);
      const title=add(card,'h3',n.name);if(n.current){const icon=createAbilityIcon(n.current);if(icon)title.prepend(icon);}
      add(card,'small',(n.type==='ability'?n.current.attackType+' ability':n.type)+' · '+(n.equipped?'Equipped':n.unlocked?'Unlocked':'Locked')+(n.maxRank>1?' · rank '+n.rank+'/'+n.maxRank:''));
      const current=n.unlocked?(n.rank?n.effects[n.rank-1]:n.effects[0]):'Not learned';add(card,'p','Current: '+current);
      if(n.rank<n.maxRank && (!n.starter||n.branch==='Ascension') && !(n.unlocked&&n.type==='ability'))add(card,'p','Next: '+n.effects[n.rank]);
      if(n.current)add(card,'p',(n.current.manaCost||0)+' mana · '+n.current.cooldown+'s recharge · '+(n.current.range?n.current.range+'px range':'self / party'),'subtle');
      const missing=n.requires.filter(id=>!h.nodes.find(v=>v.id===id)?.unlocked);
      if(n.requires.length)add(card,'p','Requires: '+n.requires.map(id=>h.nodes.find(v=>v.id===id)?.name||id).join(', '),'subtle');
      if(!n.starter && n.rank<n.maxRank && !(n.unlocked&&n.type==='ability')){
        const button=add(card,'button',(n.rank?'Improve':'Unlock')+' · '+n.cost+' points','secondary small');button.disabled=busy||!h.safe||Boolean(missing.length)||h.points<n.cost;button.onclick=()=>act('skillUnlock',{node:n.id,expectedRank:n.rank});
      }
    }
    const milestones=$('#heroMilestones');milestones.replaceChildren();for(const m of h.milestones)add(milestones,'p',(m.earned?'✓ ':'○ ')+(milestoneNames[m.id]||m.id)+' · '+m.points+' points','subtle');
    const legacy=Object.entries(h.legacyTraining).filter(([,v])=>v);if(legacy.length)add(milestones,'p','Preserved earlier training: '+legacy.map(([k,v])=>k+' '+v).join(', '));
    $('#heroRespec').disabled=busy||!h.safe;
  }
  $('#heroSkillsButton').onclick=()=>{openInfo('heroSkillsDialog');signature='';render(latestRoom);};
  $('#heroRespec').onclick=()=>act('skillRespec');
  window.renderHeroSkills=render;window.resetHeroSkills=()=>{signature='';branch='';hero='';busy=false;purchasePreview=null;purchaseId=null;};
  window.drawHeroSkillZones=(ctx,room)=>{
    if(window.GauntletCombatVisuals)return window.GauntletCombatVisuals.zones(ctx,room);
    const colors={banner:'#d8c48a',beacon:'#a9f1ed',hallowed:'#ffe09d',spring:'#8de5a4',rift:'#b6a6f3',trap:'#d5c397',ascension_commitment:'#e9d4a3'};
    for(const z of room.skillZones||[]){ctx.save();ctx.strokeStyle=colors[z.kind]||'#c7e5b2';ctx.fillStyle=ctx.strokeStyle+'16';ctx.lineWidth=2;ctx.beginPath();ctx.arc(z.x,z.y,z.radius,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.beginPath();ctx.moveTo(z.x-7,z.y);ctx.lineTo(z.x+7,z.y);ctx.moveTo(z.x,z.y-7);ctx.lineTo(z.x,z.y+7);ctx.stroke();ctx.restore();}
  };
})();
