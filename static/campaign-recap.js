/* Optional, read-only Continue recap. Never accepts work or repeats rewards. */
(() => {
  let requested=false,owner=null;
  const dialog=document.createElement('dialog');dialog.id='campaignRecap';dialog.className='panel info-dialog recovery-dialog';
  dialog.innerHTML='<div class="section-heading"><h2>Back in the woodland</h2><button class="secondary" data-close="campaignRecap">Close</button></div><p data-last></p><h3 data-goal></h3><p data-step></p><p class="subtle" data-place></p><button class="primary" data-track>Track this objective</button><p role="status" data-notice></p>';
  document.body.append(dialog);
  const entry=document.createElement('button');entry.className='secondary small hidden';entry.textContent='Story recap';entry.onclick=()=>{requested=true;show(latestRoom);};
  document.querySelector('.game-menu > div').append(entry);
  function show(room){
    entry.classList.toggle('hidden',!room?.adventure);const recap=room?.adventure?.recap;
    if(!requested||!recap)return;requested=false;owner=session;
    dialog.querySelector('[data-last]').textContent=recap.lastEvent;
    dialog.querySelector('[data-goal]').textContent=recap.objective.title;
    dialog.querySelector('[data-step]').textContent=recap.objective.nextStep;
    dialog.querySelector('[data-place]').textContent=recap.location+(recap.objective.travelPoint?' · known travel point: '+recap.objective.travelPoint.name:'');
    const track=dialog.querySelector('[data-track]');track.disabled=recap.objective.complete;track.onclick=async()=>{
      if(owner!==session)return;track.disabled=true;
      try{await sendAction('adventureTrack',{objective:recap.objective.id});if(owner===session){dialog.close();refresh();}}
      catch(e){if(owner===session){dialog.querySelector('[data-notice]').textContent=e.message;track.disabled=false;}}
    };
    dialog.querySelector('[data-notice]').textContent='';openInfo('campaignRecap');
  }
  window.GauntletRecap={request(){requested=true;},render:show,reset(){requested=false;owner=null;entry.classList.add('hidden');dialog.close();}};
  const ritual=document.createElement('dialog');ritual.id='ascensionRitual';ritual.className='panel info-dialog recovery-dialog';document.body.append(ritual);
  window.showAscensionRitual=room=>{
    ritual.replaceChildren();const add=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;ritual.append(n);return n;};
    add('h2','The spring oath · '+room.heroSkills.hero);add('p','The old spring answers. Your strength belongs to the living you bring home.');
    for(const n of room.heroSkills.nodes.filter(n=>n.branch==='Ascension')){add('h3',n.name);add('p',n.effects[0]);}
    add('p','Equip your signature in an open active slot at a village. The optional spring-oath trial is waiting in the western failed fields outside Dunmere. Ordinary trails stay open.');
    const close=add('button','Prepare my new form');close.className='primary';close.dataset.close='ascensionRitual';openInfo('ascensionRitual');
  };
})();
