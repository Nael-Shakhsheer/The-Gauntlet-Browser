/* New identities, remembered worlds and party joining are separate operations. */
(() => {
  let busy=false,joinBusy=false,nextMode=null,pending=null,joinRequest=null,cardGeneration=0,intent=0;
  const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key)||'null')??fallback;}catch{return fallback;}};
  const add=(parent,tag,text,cls='')=>{const e=document.createElement(tag);e.textContent=text;e.className=cls;parent.append(e);return e;};
  for(const id of ['newHero','joinHero'])for(const hero of CLASS_ORDER){const o=add($('#'+id),'option',hero);o.value=hero;}
  $('#joinPartyBody').append($('#joinForm'));
  const settings=$('#settingsBody');
  const technical=add(settings,'button','Technical details','secondary');technical.onclick=()=>{$('#settingsDialog').close();openInfo('runtimeDialog');};
  for(const e of [$('#openSettings'),document.querySelector('#entry [data-guide]'),document.querySelector('#entry [data-audio-open]'),$('#keySettings')])if(e)settings.append(e);
  $('#continueRun').textContent='Continue';$('.front-actions').prepend($('#continueRun'));
  const manage=add($('.entry-copy'),'button','Manage saves & backups','secondary small');manage.id='manageSaves';manage.dataset.uiAction='navigation';manage.onclick=()=>window.openRecovery();
  $('#adventureContinueDialog').querySelector('.section-heading').after($('#importAdventure'));
  $('#adventureContinueTitle').textContent='Saved worlds & recovery';
  document.querySelectorAll('.game-menu-items [data-guide],.game-menu-items [data-audio-open]').forEach(e=>e.remove());
  $('#frontSettings').onclick=()=>openInfo('settingsDialog');
  $('#joinParty').onclick=()=>{intent++;notice($('#joinPartyNotice'),'');openInfo('joinPartyDialog');};
  document.addEventListener('click',event=>{if(event.target.closest('[data-audio-open]') && $('#settingsDialog').open)$('#settingsDialog').close();});
  function modeText(){
    const adventure=$('#newMode').value==='adventure';$('#newRunTitle').textContent=adventure?'New Adventure':'New Gauntlet run';
    $('#skipIntroLabel').classList.toggle('hidden',!adventure);
    $('#newWorldLabel').classList.toggle('hidden',!adventure);$('#newRunSubmit').textContent=pending?'Retry unconfirmed creation':adventure?'Begin Adventure':'Create Gauntlet party';
    $('#newRunExplanation').textContent=adventure?'Defend Oakvale’s last grain caravan with your real starter kit, then explore the woodland. Friends can join the defence without restarting it. Introduction retries cost no Runes.':'Choose the familiar three-ability loadout in your party lobby. The host sets challenge and campaign length.';
  }
  function showSetup(mode){
    intent++;
    pending=read('gauntlet-pending-create',null);notice($('#newRunNotice'),'');
    $('#newMode').value=pending?.mode||mode;
    if(pending){for(const [id,key]of [['newName','name'],['newWorldName','title'],['newHero','hero'],['newDifficulty','difficulty']])$('#'+id).value=pending[key];$('#newCompanion').checked=pending.companion;$('#skipIntro').checked=Boolean(pending.skipIntro);notice($('#newRunNotice'),'The previous creation was not confirmed. Retry safely using the same private request; it will not create a second copy.');}
    for(const e of $('#newRunForm').querySelectorAll('input,select'))e.disabled=Boolean(pending);
    modeText();openInfo('newRunDialog');
  }
  window.requestNewRun=mode=>{
    if(session){nextMode=mode;returnToMainMenu();return;}showSetup(mode);
  };
  $('#newAdventure').onclick=()=>window.requestNewRun('adventure');$('#newGauntlet').onclick=()=>window.requestNewRun('gauntlet');$('#newMode').onchange=modeText;
  $('#leaveRunDialog').addEventListener('cancel',()=>{nextMode=null;});
  document.addEventListener('click',e=>{if(e.target.closest('[data-close="leaveRunDialog"]'))nextMode=null;});
  window.frontMenuReturned=()=>{refreshCards();if(nextMode){const mode=nextMode;nextMode=null;showSetup(mode);}};
  $('#newRunForm').onsubmit=async event=>{
    event.preventDefault();if(busy)return;busy=true;$('#newRunSubmit').disabled=true;notice($('#newRunNotice'),'Creating a separate run…');
    const submittedIntent=intent,owner=session;
    try{
      if(!pending){const build=await api('/api/build');pending={requestId:crypto.randomUUID(),instance:build.instance,mode:$('#newMode').value,name:$('#newName').value,title:$('#newWorldName').value,hero:$('#newHero').value,difficulty:$('#newDifficulty').value,companion:$('#newCompanion').checked,skipIntro:$('#skipIntro').checked};localStorage.setItem('gauntlet-pending-create',JSON.stringify(pending));}
      const result=await api('/api/new-run',pending,undefined,{timeoutMs:15000});
      if(!result.recovery)throw Error('Creation was not confirmed with a recovery identity. Retry this request.');
      localStorage.removeItem('gauntlet-pending-create');pending=null;
      if(!$('#newRunDialog').open||intent!==submittedIntent||session!==owner){rememberResult(result);return;}
      saveSession(result);
    }catch(error){notice($('#newRunNotice'),error.message+' Existing worlds are unchanged.');modeText();}
    finally{busy=false;$('#newRunSubmit').disabled=false;}
  };
  const abandon=add($('#newRunDialog'),'button','Review Continue before another creation','secondary small');
  abandon.onclick=()=>{const request=read('gauntlet-pending-create',null);if(request){const history=read('gauntlet-creation-retries',[]);localStorage.setItem('gauntlet-creation-retries',JSON.stringify([request,...history].slice(0,8)));localStorage.removeItem('gauntlet-pending-create');pending=null;}$('#newRunDialog').close();window.openRecovery();};
  window.joinCurrentParty=async()=>{
    if(joinBusy)return;joinBusy=true;const button=$('#joinForm button[type=submit]');button.disabled=true;notice($('#joinPartyNotice'),'Joining…');
    const submittedIntent=intent,owner=session;
    try{const values={room:$('#roomCode').value,name:$('#joinName').value,hero:$('#joinHero').value};
      if(!joinRequest || JSON.stringify(joinRequest.values)!==JSON.stringify(values))joinRequest={values,requestId:crypto.randomUUID()};
      const result=await api('/api/party/join',{...values,requestId:joinRequest.requestId},undefined,{timeoutMs:10000});joinRequest=null;
      if(!$('#joinPartyDialog').open||intent!==submittedIntent||session!==owner){rememberResult(result);return;}saveSession(result);
    }catch(error){notice($('#joinPartyNotice'),error.message);}finally{joinBusy=false;button.disabled=false;}
  };
  const change=add(document.querySelector('.game-menu-items'),'button','Change mode / new run','secondary');
  change.onclick=()=>window.requestNewRun(latestRoom?.mode==='adventure'?'gauntlet':'adventure');
  const options=add(document.querySelector('.game-menu-items'),'button','Controls & settings','secondary');options.onclick=()=>openInfo('settingsDialog');
  const transport=add(document.querySelector('.game-menu-items'),'button','Travel map','secondary');transport.onclick=openVillagePortal;
  const invite=add(document.querySelector('.game-menu-items'),'button','Copy party code','secondary');invite.onclick=async()=>{if(session){await navigator.clipboard.writeText(session.room);invite.textContent='Code: '+session.room;}};
  function rememberResult(result){const refs=read('gauntlet-sessions',[]);localStorage.setItem('gauntlet-sessions',JSON.stringify([result,...refs.filter(r=>r.room!==result.room||r.player!==result.player)]));refreshCards();}
  const relative=t=>{if(!t)return 'Last played time unavailable';const days=Math.max(0,Math.floor((Date.now()/1000-t)/86400));return days===0?'Played today':days===1?'Played yesterday':'Played '+days+' days ago';};
  function primary(returning){for(const [id,primary]of [['continueRun',returning],['newAdventure',!returning]]){const b=$('#'+id);b.classList.toggle('primary',primary);b.classList.toggle('secondary',!primary);b.dataset.uiAction=primary?'primary':'secondary';}$('#continueRun').classList.toggle('hidden',!returning);}
  let menuCardSignature='';
  window.rememberMenuCard=room=>{const p=room.players.find(p=>p.id===room.you);if(!p||!session)return;const data={hero:p.class,mode:room.mode,name:room.adventure?.saveInfo?.name||'Gauntlet run',location:room.adventure?.name||'Stage '+room.stage,stage:room.stage,savedAt:room.adventure?.saveInfo?.savedAt||room.checkpointSavedAt};
    const sig=JSON.stringify([session.room,session.player,data,Math.floor(Date.now()/60000)]);if(sig===menuCardSignature)return;menuCardSignature=sig;const cards=read('gauntlet-menu-cards',{});cards[session.room+':'+session.player]={...data,lastPlayed:Date.now()/1000};const entries=Object.entries(cards).sort((a,b)=>b[1].lastPlayed-a[1].lastPlayed).slice(0,32);try{localStorage.setItem('gauntlet-menu-cards',JSON.stringify(Object.fromEntries(entries)));}catch{}};
  async function refreshCards(){
    const generation=++cardGeneration,box=$('#frontSavedWorlds');box.replaceChildren();add(box,'h3','Your worlds');primary(false);let valid=false;
    const refs=read('gauntlet-adventures',[]),sessions=read('gauntlet-sessions',[]),resume=read('gauntlet-resume',null);
    for(const r of [...sessions,resume].filter(Boolean))if(!refs.some(v=>v.room===r.room&&v.player===r.player))refs.push(r);
    if(!refs.length)add(box,'p','Your confirmed Adventures and Gauntlet checkpoints will appear here. Start a new journey above.','subtle');
    const cache=read('gauntlet-menu-cards',{}),rows=refs.slice(0,32),cards=rows.map(()=>add(box,'article','','saved-world-card'));
    let cursor=0;async function worker(){while(cursor<rows.length){const index=cursor++,ref=rows[index],card=cards[index],cached=cache[ref.room+':'+ref.player]||{};
      let summary;
      try{summary=await api('/api/adventure/summary',ref,ref.recovery,{timeoutMs:2500});}catch{}
      if(generation!==cardGeneration)return;
      if(!summary){try{await api('/api/stats?room='+encodeURIComponent(ref.room)+'&player='+encodeURIComponent(ref.player),undefined,ref.recovery,{timeoutMs:2500});summary={...cached,name:cached.name||'Gauntlet run',hero:cached.hero,location:cached.location||'Gauntlet checkpoint',gauntlet:true};}catch{}}
      if(generation!==cardGeneration)return;
      if(summary){
        valid=true;primary(true);card.dataset.state='available';card.dataset.mode=summary.gauntlet?'gauntlet':'adventure';
        if(CLASS_ORDER.includes(summary.hero)){const portrait=add(card,'img','','saved-hero');portrait.src='/sprites/portrait-'+summary.hero.toLowerCase()+'-v1.png';portrait.alt='';portrait.width=portrait.height=54;}
        add(card,'h4',summary.name);add(card,'p',(summary.hero||'Hunter')+' · '+summary.location);
        add(card,'p',summary.gauntlet?'Gauntlet · continue your run':summary.completed+'/4 woodland objectives · '+summary.locations+' locations','saved-progress');
        add(card,'p',relative(cached.lastPlayed||summary.savedAt),'subtle');
        const details=add(card,'details','');add(details,'summary','Save details');add(details,'p',summary.savedAt?'Last confirmed save: '+new Date(summary.savedAt*1000).toLocaleString():'No confirmed checkpoint time. A live Gauntlet run needs an inn bed for restart recovery.','subtle');
        if(cached.lastPlayed)add(details,'p','Last played in this browser: '+new Date(cached.lastPlayed*1000).toLocaleString(),'subtle');
        const go=add(card,'button','Continue','primary small');go.onclick=()=>{saveSession(ref);window.GauntletRecap?.request();};
      }else{
        card.classList.add('saved-world-legacy');
        card.dataset.state='unavailable';add(card,'h4',ref.name||cached.name||'Remembered run');add(card,'p','Unavailable on this server. Review recovery options; the original save is kept.','subtle');
        const go=add(card,'button','Review recovery','secondary small');go.onclick=()=>window.openRecovery();
      }
    }}await Promise.all(Array.from({length:Math.min(4,rows.length)},worker));if(generation===cardGeneration)primary(valid);
  }
  window.refreshWorldCards=refreshCards;refreshCards();
  window.renderCreationRetries=list=>{
    const rows=read('gauntlet-creation-retries',[]),active=read('gauntlet-pending-create',null);if(active&&!rows.some(r=>r.requestId===active.requestId))rows.unshift(active);
    if(rows.length)add(list,'h3','Unconfirmed creations');
    for(const request of rows){const card=add(list,'section','','adventure-quest');add(card,'p',request.title+' · '+request.hero+' · '+request.mode);
      const button=add(card,'button','Finish confirming this request','secondary small');button.onclick=async()=>{if(button.disabled)return;const owner=session,submittedIntent=intent;button.disabled=true;try{const ref=await api('/api/new-run',request,undefined,{timeoutMs:15000});
        localStorage.setItem('gauntlet-creation-retries',JSON.stringify(rows.filter(r=>r.requestId!==request.requestId)));if(active?.requestId===request.requestId)localStorage.removeItem('gauntlet-pending-create');if(session===owner&&intent===submittedIntent&&$('#adventureContinueDialog').open)saveSession(ref);else rememberResult(ref);
      }catch(e){if(session===owner)notice($('#adventureRecoveryNotice'),e.message,'error');}finally{button.disabled=false;}};
    }
  };
})();
