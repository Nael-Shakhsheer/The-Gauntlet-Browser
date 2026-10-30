/* Shared assignment state; acceptance and turn-ins resolve only on the server. */
(() => {
  const dialog=document.createElement('dialog');dialog.id='chapterDialog';dialog.className='panel info-dialog recovery-dialog';
  dialog.innerHTML='<div class="section-heading"><h2>Village assignments</h2><button class="secondary" data-close="chapterDialog">Close</button></div><p>Assignments belong to this party’s world. Collected clues stay recorded; return here to report completed work.</p><div id="chapterCards"></div><p id="chapterNotice" class="notice" role="status"></p>';
  const tabs=document.createElement('nav');tabs.className='chapter-tabs';tabs.setAttribute('aria-label','Assignment status');dialog.querySelector('#chapterCards').before(tabs);
  document.body.append(dialog);let stamp=null,busy=false,signature='',tab=null;
  const labels={available:'Available',active:'Active / Ready',completed:'Completed'};
  const group=q=>q.status==='complete'?'completed':q.status==='offered'?'available':'active';
  function render(room){const a=room.adventure;if(!a)return;
    if(a.chapterMenu&&a.chapterMenu!==stamp){stamp=a.chapterMenu;tab=null;openInfo('chapterDialog');}
    if(!dialog.open)return;
    const rows=a.chapter||[];if(!tab)tab=rows.some(q=>q.status==='ready-to-turn-in')?'active':rows.some(q=>q.status==='offered')?'available':'active';
    const sig=JSON.stringify([rows,busy,tab]);if(sig===signature)return;signature=sig;
    const scroll=dialog.scrollTop,focus=document.activeElement?.dataset?.quest;tabs.replaceChildren();
    for(const [id,label] of Object.entries(labels)){const b=document.createElement('button');b.className='secondary small';b.textContent=label+' ('+rows.filter(q=>group(q)===id).length+')';b.setAttribute('aria-pressed',String(tab===id));b.onclick=()=>{tab=id;signature='';render(latestRoom);};tabs.append(b);}
    const box=$('#chapterCards');box.replaceChildren();
    const visible=rows.filter(q=>group(q)===tab).sort((a,b)=>(b.status==='ready-to-turn-in')-(a.status==='ready-to-turn-in'));
    if(!visible.length){const empty=document.createElement('p');empty.textContent='No assignments in this section.';box.append(empty);}
    for(const q of visible){const card=document.createElement('section');card.className='adventure-quest';const h=document.createElement('h3'),state=document.createElement('p'),text=document.createElement('p');
      h.textContent=(q.optional?'Optional · ':'')+q.title;state.textContent=q.status.replaceAll('-',' ')+' · '+(q.contact||'Village Runner');text.textContent=q.outcome||q.objective;card.append(h,state,text);
      if(q.requires.length){const found=document.createElement('p');found.className='subtle';found.textContent='Evidence: '+q.found.length+' / '+q.requires.length;card.append(found);}
      for(const id of q.requires){const art=window.GauntletCampaignArtData?.icons?.[id];if(art?.category!=='artifact')continue;const row=document.createElement('p');row.className='campaign-evidence';const icon=document.createElement('img');icon.src='/sprites/'+art.file;icon.alt='';icon.width=icon.height=32;const text=document.createElement('span');text.textContent=(q.found.includes(id)?'✓ ':'')+art.name;row.append(icon,text);card.append(row);}
      if(q.status==='offered'||q.status==='ready-to-turn-in'){
        const button=document.createElement('button');button.className='primary';button.dataset.quest=q.id;button.textContent=q.status==='offered'?'Accept assignment':'Report findings';button.disabled=busy||!q.actionable;
        button.onclick=async()=>{busy=true;signature='';render(latestRoom);try{await sendAction(q.status==='offered'?'chapterAccept':'chapterReport',{quest:q.id});notice($('#chapterNotice'),'Updated. Personal and world receipts are saved together.');}catch(e){notice($('#chapterNotice'),e.message);}finally{busy=false;signature='';refresh();}};card.append(button);
      }box.append(card);
    }dialog.scrollTop=scroll;if(focus)box.querySelector('[data-quest="'+CSS.escape(focus)+'"]')?.focus({preventScroll:true});
  }
  window.GauntletChapter={render,reset(){stamp=null;signature='';busy=false;tab=null;}};
})();
