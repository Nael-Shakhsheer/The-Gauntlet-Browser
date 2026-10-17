/* Recovery, portable backups and personal rewards. Python owns every claim. */
(() => {
  'use strict';
  let preview=null,config=null,token='',busy=false;
  const refs=()=>{try{return JSON.parse(localStorage.getItem('gauntlet-adventures')||'[]');}catch{return [];}};
  window.hasAdventureRefs=()=>refs().length>0;
  const msg=t=>notice($('#adventureRecoveryNotice'),t);
  const date=t=>t?new Date(typeof t==='number'?t*1000:t).toLocaleString():'No successful save yet';
  const add=(p,tag,text,cls='')=>{const n=document.createElement(tag);n.textContent=text;n.className=cls;p.append(n);return n;};
  window.rememberAdventure=info=>{
    if(!session||!info)return;
    const rows=refs(),old=rows.find(r=>r.worldId===info.worldId);
    if(old&&old.room===session.room&&old.player===session.player&&old.name===info.name&&old.recovery===session.recovery)return;
    try{localStorage.setItem('gauntlet-adventures',JSON.stringify([{...session,worldId:info.worldId,name:info.name},...rows.filter(r=>r.worldId!==info.worldId)].slice(0,20)));}catch{}
    $('#continueRun').classList.remove('hidden');
  };
  const badge=add($('#adventureFeedback').parentElement,'button','','secondary small adventure-save-badge hidden');badge.type='button';badge.onclick=()=>window.openRecovery();badge.setAttribute('role','status');
  const saveNotice=window.GauntletMovement.createSaveNotice();
  let badgeTimer;
  window.renderSaveBadge=info=>{
    if(!info){badge.classList.add('hidden');return;}const now=performance.now();saveNotice.update(info,now);
    badge.textContent=info.error?'Save failed · recovery':info.savedAt?'Adventure saved':'Not saved yet';badge.dataset.failed=String(Boolean(info.error));
    badge.title=(info.error||'Last confirmed disk save')+' · '+info.storage.label;
    badge.classList.toggle('hidden',!saveNotice.visible(now));
    clearTimeout(badgeTimer);if(!info.error)badgeTimer=setTimeout(()=>badge.classList.add('hidden'),2600);
  };
  function summary(parent,s){
    add(parent,'h3',s.name);add(parent,'p','Last successful save: '+date(s.savedAt));
    add(parent,'p',s.hero?s.hero+' · '+s.items+' pouch items · '+s.training+' training ranks':s.characters.map(c=>c.name+' · '+c.hero+(c.bot?' (companion)':'')).join('; '));
    if(s.gear?.length)add(parent,'p','Equipped: '+s.gear.join(' / ')+' · '+s.maxHp+' maximum HP');
    add(parent,'p',s.completed+'/4 main objectives complete · '+s.locations+' visited locations · '+s.runes+' shared Runes');
    add(parent,'p','Recovery: '+s.recovery+'. Interrupted sealed encounters restart; completed waves and claims remain.');
    if(s.storage){add(parent,'p',s.storage.label+'. Free hosted disks remain temporary; keep an export.','subtle');
      if(s.storage.cloudLinked)add(parent,'p','Cloud last confirmed: '+date(s.storage.cloudSavedAt)+(s.storage.cloud?.pending?' · upload pending':'')+(s.storage.cloud?.error?' · '+s.storage.cloud.error:''));}
    if(s.error)add(parent,'p',s.error,'notice');if(s.migrated)add(parent,'p','Older internal v1 save migrated to portable v2.');
  }
  async function download(ref){
    const doc=await api('/api/adventure/export',ref),url=URL.createObjectURL(new Blob([JSON.stringify(doc,null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='gauntlet-adventure-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);msg('Backup downloaded. Keep it separately from the server.');
  }
  window.openRecovery=async()=>{
    openInfo('adventureContinueDialog');msg('');const list=$('#adventureRecoveryList');list.replaceChildren();const rows=refs();let resume;
    try{resume=JSON.parse(localStorage.getItem('gauntlet-wave-resume')||localStorage.getItem('gauntlet-resume')||'null');}catch{}
    for(const ref of [session,resume])if(ref&&!rows.some(r=>r.room===ref.room&&r.player===ref.player))rows.push(ref);
    for(const ref of rows){const card=add(list,'section','','adventure-quest');
      try{const s=await api('/api/adventure/summary',ref);add(card,'p','Slot 1 · Current Adventure','eyebrow');summary(card,s);
        const go=add(card,'button','Continue this character','primary small');go.onclick=()=>{$('#adventureContinueDialog').close();saveSession(ref);};
        add(card,'button','Export backup','secondary small').onclick=()=>download(ref).catch(e=>msg(e.message));
        const backupCard=add(card,'section','','adventure-backup-slot');add(backupCard,'h4','Slot 2 · Adventure Backup');
        try{const slots=await api('/api/adventure/slots',ref);
          if(slots.backup){add(backupCard,'p','Previous confirmed save · '+date(slots.backup.savedAt)+' · '+slots.backup.completed+'/4 objectives · '+slots.backup.runes+' Runes');
            add(backupCard,'button','Review backup recovery','secondary small').onclick=async()=>{try{
              const result=await api('/api/adventure/backup-preview',ref);showImport(result);$('#adventureImportCharacter').value=String(result.character);
            }catch(e){msg(e.message);}};
          }else add(backupCard,'p','Created automatically after the next confirmed save.');
        }catch{add(backupCard,'p','Use a private recovery identity to access this slot. Export remains available.');}
        if(s.creator&&ref.recovery){const share=add(card,'button','Share recovered party characters','secondary small');share.onclick=async()=>{try{
          const roster=await api('/api/adventure/roster',ref);for(const c of roster){add(card,'button','Recovery link for '+c.name+' · '+c.hero,'secondary small').onclick=async()=>{try{
            const guest=await api('/api/adventure/invite',{...ref,character:c.characterId});const link=add(card,'input','');link.readOnly=true;link.value=location.origin+'/#recover='+encodeURIComponent(btoa(JSON.stringify(guest)));link.setAttribute('aria-label','Private character recovery link');link.select();add(card,'p','Share privately. Anyone with this link can play that character.');
          }catch(e){msg(e.message);}};}share.remove();
        }catch(e){msg(e.message);}};}
      }catch(error){try{const r=await api('/api/state?room='+encodeURIComponent(ref.room)+'&player='+encodeURIComponent(ref.player),undefined,ref.recovery);if(r.mode==='adventure')throw error;
          add(card,'h3','Slot 3 · Gauntlet Checkpoint');add(card,'p',r.checkpointSavedAt?'Inn checkpoint · '+date(r.checkpointSavedAt):'Live session only; rest at an upstairs inn bed to create this slot.');
          add(card,'button','Continue Gauntlet','primary small').onclick=()=>{$('#adventureContinueDialog').close();saveSession(ref);};
        }catch{add(card,'p',(ref.name||'Browser identity')+' unavailable on this server. Original saves were not replaced. Import a backup or use configured cloud recovery.','notice');}}
    }
    if(!rows.length)add(list,'p','No saved browser identity. Import a backup to recover a separate world.');
    window.renderCreationRetries?.(list);
    try{config=await api('/api/cloud/config');$('#cloudSetupStatus').textContent=config.configured?'Optional Supabase storage configured. Sign in with an existing account; creator links first. Characters stay tied to their world.':'Cloud storage is not configured. Local saving and exports work.';$('#cloudSignIn').classList.toggle('hidden',!config.configured);}catch(e){$('#cloudSetupStatus').textContent=e.message;}
  };
  const saves=add(document.querySelector('.game-menu > div'),'button','Save files','secondary small');saves.type='button';saves.onclick=()=>window.openRecovery();
  $('#continueRun').classList.toggle('hidden',!localStorage.getItem('gauntlet-resume')&&!refs().length);
  $('#importAdventure').onclick=()=>$('#adventureBackupFile').click();
  function showImport(result){preview=result;
    const box=$('#adventureImportSummary');box.replaceChildren();summary(box,preview.summary);const select=$('#adventureImportCharacter');select.replaceChildren();
    preview.summary.characters.filter(c=>!c.bot).forEach(c=>add(select,'option',c.name+' · '+c.hero).value=String(c.slot));notice($('#adventureImportNotice'),'');openInfo('adventureImportDialog');
  }
  $('#adventureBackupFile').onchange=async event=>{const file=event.target.files[0];if(!file)return;try{
    if(file.size>2_000_000)throw Error('Backup exceeds 2 MB.');showImport(await api('/api/adventure/import-preview',{document:JSON.parse(await file.text())}));
  }catch(e){notice($('#entryNotice'),'Import rejected: '+e.message);}finally{event.target.value='';}};
  $('#adventureImportConfirm').onclick=async()=>{if(busy||!preview)return;busy=true;$('#adventureImportConfirm').disabled=true;try{
    const result=await api('/api/adventure/import',{preview:preview.preview,character:Number($('#adventureImportCharacter').value),confirm:true});$('#adventureImportDialog').close();$('#adventureContinueDialog').close();saveSession(result);
  }catch(e){notice($('#adventureImportNotice'),e.message);}finally{busy=false;$('#adventureImportConfirm').disabled=false;}};
  async function cloud(path,payload){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),20000);try{
    const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify(payload||{}),signal:controller.signal});const result=await r.json();if(!r.ok)throw Error(result.error||'Cloud recovery failed.');return result;
  }finally{clearTimeout(timer);}}
  $('#cloudSignIn').onsubmit=async event=>{event.preventDefault();if(!config?.configured)return;try{
    const r=await fetch(config.url+'/auth/v1/token?grant_type=password',{method:'POST',headers:{apikey:config.anonKey,'Content-Type':'application/json'},body:JSON.stringify({email:$('#cloudEmail').value,password:$('#cloudPassword').value})});const result=await r.json();if(!r.ok||!result.access_token)throw Error('Sign-in failed. Check your configured account.');
    token=result.access_token;$('#cloudPassword').value='';msg('Signed in. Account token stays in this page’s memory.');$('#cloudListWorlds').classList.remove('hidden');$('#cloudLinkWorld').classList.toggle('hidden',!session||!latestRoom?.adventure);
  }catch(e){msg(e.message);}};
  $('#cloudLinkWorld').onclick=async()=>{try{await cloud('/api/cloud/claim',session);msg('Character linked. Cloud status updates after storage confirms it.');await window.openRecovery();}catch(e){msg(e.message);}};
  $('#cloudListWorlds').onclick=async()=>{try{const worlds=await cloud('/api/cloud/worlds'),box=$('#cloudWorlds');box.replaceChildren();if(!worlds.length)add(box,'p','No linked worlds.');
    worlds.forEach(w=>{const card=add(box,'section','','adventure-quest');summary(card,{...w,storage:{label:'Configured Supabase cloud storage'}});
      add(card,'button','Recover my character','primary small').onclick=async()=>{try{const ref=await cloud('/api/cloud/load',{worldId:w.worldId});$('#adventureContinueDialog').close();saveSession(ref);}catch(e){msg(e.message);}};
      add(card,'button','Restore as separate copy','secondary small').onclick=async()=>{try{const result=await cloud('/api/cloud/preview',{worldId:w.worldId});preview=result;const target=$('#adventureImportSummary');target.replaceChildren();summary(target,result.summary);const select=$('#adventureImportCharacter');select.replaceChildren();result.summary.characters.filter(c=>!c.bot).forEach(c=>add(select,'option',c.name+' · '+c.hero).value=String(c.slot));$('#adventureContinueDialog').close();openInfo('adventureImportDialog');}catch(e){msg(e.message);}};
    });
  }catch(e){msg(e.message);}};
  window.renderRewardChoices=room=>{const box=$('#adventureRewardChoices');box.replaceChildren();const pending=room.adventure?.pendingRewards||[];if(!pending.length)return;add(box,'h3','Your reward choices');
    pending.forEach(row=>{const card=add(box,'section','','adventure-quest');add(card,'h4',row.title);row.options.forEach(item=>{
      const choice=add(card,'div','','reward-option');add(choice,'strong',item.name+(item.alreadyOwned?' · already owned':''));add(choice,'p',item.description);appendEquipmentComparison(choice,item,room);
      const replace=add(choice,'select','');replace.setAttribute('aria-label','Sell pouch item to make room');add(replace,'option','Select a pouch item to sell').value='';room.inventory.forEach(i=>add(replace,'option',i.name+' · '+i.sell+' shared Runes').value=i.id);replace.classList.toggle('hidden',room.inventory.length<10);
      for(const [delivery,label] of [['pouch',room.inventory.length>=10?'Sell selected pouch item and take':'Take '+item.name],['sell','Sell reward · '+item.sell+' shared Runes']])add(choice,'button',label,'secondary small').onclick=async event=>{const button=event.currentTarget;button.disabled=true;try{await sendAction('adventureReward',{reward:row.id,item:item.key,delivery,replace:replace.value});notice($('#adventureRewardNotice'),item.name+(delivery==='sell'?' sold for shared Runes.':' added to your pouch.'));await refresh();}catch(e){notice($('#adventureRewardNotice'),e.message);}finally{button.disabled=false;}};
    });});
  };
  $('#adventureJournal').before($('#adventureRewardChoices'),$('#adventureRewardNotice'));
  if(location.hash.startsWith('#recover=')){try{const ref=JSON.parse(atob(decodeURIComponent(location.hash.slice(9))));if(typeof ref.room==='string'&&typeof ref.player==='string'&&typeof ref.recovery==='string')saveSession(ref);}catch{notice($('#entryNotice'),'Invalid character recovery link.');}history.replaceState(null,'',location.pathname);}
})();
