/* Story dialogue and hunter training use server-owned progress. */
let storySignature = "", storyBusy = false, trainingBusy = false, trainingDismissed = false;
window.resetProgressionUI=()=>{storySignature='';storyBusy=trainingBusy=trainingDismissed=false;};
const questButton = document.createElement("button");
questButton.className = 'secondary legacy-quest-menu'; questButton.textContent = "Quest";
$(".game-menu-items").append(questButton);
questButton.addEventListener("click", () => {
  if (latestRoom?.adventure) { openInfo('adventureJournalDialog'); return; }
  const status = latestRoom?.story?.quest;
  $("#questText").textContent = status === "complete" ? "The dragon is defeated. You fulfilled the wounded hunter's request." :
    status === "active" ? "Find and kill the dragon. The final encounter is at stage " + latestRoom.totalStages + ". Speak to innkeepers for training and use upstairs guest beds to save your progress." :
    "Follow the road. A wounded hunter waits in a peaceful clearing after the first or second stage.";
  openInfo("questDialog");
});
$("#storyDialog").addEventListener("cancel", event => {event.preventDefault();if(storyBusy)return;if(latestRoom?.dialogue?.choices?.length){$('#storyChoices')?.querySelector('[data-choice-id="leave"]')?.click();}else if(latestRoom?.dialogue?.presentation!=='npc')$('#storyNext').click();});
$("#storyNext").addEventListener("click", async () => {
  const d = latestRoom?.dialogue;
  if (!d || storyBusy) return;
  const owner=session;storyBusy = true; $("#storyNext").disabled = true;
  try { await sendAction("dialogueNext", { id: d.id, page: d.page }); }
  catch (error) { if(owner===session)notice($("#storyNotice"), error.message,'error'); }
  finally { if(owner===session){storyBusy = false; refresh();} }
});
async function closeTraining() {
  trainingDismissed = true; $("#trainingDialog").close();
  try { await sendAction("closeShop"); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
}
$("#closeTraining").addEventListener("click", closeTraining);
$("#trainingDialog").addEventListener("cancel", event => { event.preventDefault(); closeTraining(); });
$("#trainingBranches").addEventListener("click", async event => {
  const button = event.target.closest("[data-train]");
  if (!button || trainingBusy) return;
  trainingBusy = true; button.disabled = true;
  try { await sendAction("trainSkill", { branch: button.dataset.train }); notice($("#trainingNotice"), ""); }
  catch (error) { notice($("#trainingNotice"), error.message); }
  finally { trainingBusy = false; refresh(); }
});
function renderProgression(room) {
  const d = room.dialogue, dialog = $("#storyDialog");
  if (d) {
    const signature = d.id + ":" + d.page + ":" + (d.revision||0);
    if (signature !== storySignature) {
      storySignature = signature;
      $("#storyTitle").textContent = d.presentation==='npc'?d.title:d.title.replace(/^Inspect\s+(the\s+)?/i,''); $("#storyText").textContent = d.text;
      const npc=d.presentation==='npc';dialog.dataset.presentation=npc?'npc':d.presentation||'inspection';
      (npc?document.querySelector('.player-speaker .speech-box'):document.querySelector('.npc-speaker .speech-box')).append($('#storyNext'));
      $("#storyPlayerName").textContent = room.players.find(p => p.id === room.you)?.name || "You";
      $("#storyReply").textContent = d.reply || '';
      $("#storyStep").textContent = npc?(d.total>1?'Conversation · '+(d.page+1)+' / '+d.total:''):d.total>1?(d.page+1)+' / '+d.total:'';
      let choices=document.getElementById('storyChoices');if(!choices){choices=document.createElement('div');choices.id='storyChoices';choices.className='story-choices';document.querySelector('.player-speaker .speech-box').append(choices);}choices.replaceChildren();
      $('#storyNext').hidden=Boolean(d.choices?.length);
      const kind=response=>['leave','back'].includes(response.id)?'navigation':['region','advice','steady','skeptical','ascension_context'].includes(response.id)?'question':/^(seed_|relief_)/.test(response.id)?'world-choice':response.id.startsWith('service_')?'reward':'action';
      const priority=response=>kind(response)==='navigation'?2:kind(response)==='question'?1:0;
      const ordered=[...(d.choices||[])].sort((a,b)=>priority(a)-priority(b));
      if(ordered.some(r=>kind(r)==='world-choice')){const hint=document.createElement('small');hint.textContent='Party choice · once agreed, it stays with this world.';choices.append(hint);}
      for(const response of ordered){const b=document.createElement('button');b.className='secondary small';b.textContent=response.label;
        b.dataset.choiceId=response.id;b.dataset.choiceKind=kind(response);b.dataset.uiAction=b.dataset.choiceKind==='navigation'?'navigation':b.dataset.choiceKind==='question'?'secondary':'primary';
        b.onclick=async()=>{if(storyBusy)return;const owner=session;storyBusy=true;for(const x of choices.children)x.disabled=true;try{await sendAction('dialogueChoice',{id:d.id,page:d.page,revision:d.revision,choice:response.id,requestId:crypto.randomUUID().replaceAll('-',''),serviceRevision:d.serviceRevision});}catch(e){if(owner===session)notice($('#storyNotice'),e.message,'error');}finally{if(owner===session){storyBusy=false;storySignature='';refresh();}}};choices.append(b);}
      $("#storyNext").textContent = d.button;$('#storyNext').classList.toggle('primary',npc);$('#storyNext').classList.toggle('secondary',!npc);$('#storyNext').dataset.uiAction=npc?'primary':'navigation';notice($("#storyNotice"), "");
    }
    $("#storyNext").disabled = storyBusy;
    if(d.presentation==='npc')drawDialoguePortraits(room,d);
    if (!dialog.open) { releaseControls(); dialog.showModal(); }
  } else { storySignature = ""; if (dialog.open) dialog.close(); }
  if (room.townInteraction !== "innkeeper") trainingDismissed = false;
  const training = !room.adventure && room.phase === "town" && room.townInteraction === "innkeeper" && room.trainingKnown && !d;
  if (!training && $("#trainingDialog").open) $("#trainingDialog").close();
  if (training && !trainingDismissed) {
    if (!$("#trainingDialog").open) openInfo("trainingDialog");
    $("#trainingPoints").textContent = room.skillPoints + " training point" + (room.skillPoints === 1 ? "" : "s") + " available · one point per rank";
    const branches = $("#trainingBranches");
    const signature = JSON.stringify([room.skillRanks, room.skillPoints, trainingBusy]);
    if (branches.dataset.signature !== signature) {
      branches.dataset.signature = signature; branches.replaceChildren();
      for (const [key, skill] of Object.entries(room.skills)) {
        const rank = room.skillRanks[key] || 0;
        const card = document.createElement("section"); card.className = "training-branch";
        const name = document.createElement("h3"); name.textContent = skill.name;
        const description = document.createElement("p"); description.textContent = skill.description;
        const ranks = document.createElement("p"); ranks.textContent = "Rank " + rank + " / " + skill.maxRank + " · " + "●".repeat(rank) + "○".repeat(skill.maxRank-rank);
        const button = document.createElement("button"); button.className = "primary"; button.dataset.train = key;
        button.textContent = rank === skill.maxRank ? "Fully trained" : "Train " + skill.name;
        button.disabled = trainingBusy || rank >= skill.maxRank || room.skillPoints < 1;
        card.append(name, description, ranks, button); branches.append(card);
      }
    }
  }
  if (room.movementLocked && !d) notice($("#combatNotice"), "A village runner is approaching…");
}
function drawDialoguePortraits(room, dialogue) {
  const player = room.players.find(p => p.id === room.you);
  const left = $("#storyPlayerPortrait").getContext("2d"), right = $("#storyNpcPortrait").getContext("2d");
  left.clearRect(0,0,80,88); right.clearRect(0,0,80,88);
  left.save(); left.translate(40,40); left.scale(1.3,1.3); left.translate(-40,-40);
  const drawn = player && drawImportedHero(left, {...player,status:"alive",moving:false,animationUntil:0,facingX:1,facingY:0},40,48);
  left.restore();
  if (!drawn) { left.fillStyle = player?.color || "#ffe389"; left.font = "bold 32px monospace"; left.fillText((player?.class || "Hero")[0],27,58); }
  if(window.GauntletCampaignArt?.dialoguePortrait(right,dialogue))return;
  const storyKind=({wounded:'injured',welcome:'runner',adventure_hunter:'injured',adventure_recovered:'recovered',adventure_welcome:'runner'})[dialogue.kind];
  if (storyKind && window.GauntletAdventureSprites?.npc(right,storyKind,40,48,{gesture:storyKind!=='injured',scale:1.3})) return;
  const npc=dialogue.portrait;if(!npc)return;
  if (!window.GauntletTownSprites.character(right,npc,40,48,{direction:"west",scale:1.3})) {
    right.fillStyle = "#ffe389"; right.font = "bold 32px monospace"; right.fillText(dialogue.title[0],27,58);
  }
}
function drawStairs(ctx, x, y, label, room = latestRoom) {
  if (!drawVillageProp(ctx, room, "stairs", x - 44, y - 50, 88, 96)) {
  ctx.fillStyle = "#382e2e"; ctx.fillRect(x-38, y-46, 76, 84);
  for (let i=0; i<6; i++) { ctx.fillStyle = i%2 ? "#d0ac79" : "#a9875e"; ctx.fillRect(x-32, y-40+i*12, 64, 9); }
  }
  ctx.fillStyle = "#152321dd"; ctx.fillRect(x-54, y+44, 108, 20);
  ctx.fillStyle = "#fff0ca"; ctx.font = "bold 11px monospace"; ctx.textAlign = "center"; ctx.fillText(label, x, y+57);
}
function drawInnRooms(ctx, room) {
  // Room walls and thresholds follow authoritative walkable geometry.
  const themed = Boolean(window.GauntletCampaignScenery?.hasInterior(room,true)||villageImage(room, "upstairs"));
  if (!themed) { ctx.fillStyle = "#302d32"; ctx.fillRect(148, 94, 664, 256); }
  for (const [index, guest] of (room.innRooms || []).entries()) {
    const x = guest.x;
    if (!themed) { ctx.fillStyle = "#b28b60"; ctx.fillRect(x-77, 112, 154, 215); }
    ctx.strokeStyle = "#453a32"; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(x-26,327);ctx.lineTo(x-77,327);ctx.lineTo(x-77,112);ctx.lineTo(x+77,112);ctx.lineTo(x+77,327);ctx.lineTo(x+26,327);ctx.stroke();
    if (guest.locked) {ctx.fillStyle = "#16212899"; ctx.fillRect(x-73,116,146,207);}
    ctx.fillStyle = "#152321dd"; ctx.fillRect(x-53,122,106,22);
    ctx.fillStyle = "#d2b88b"; ctx.font = "bold 12px monospace"; ctx.textAlign = "center"; ctx.fillText(guest.name.toUpperCase(), x, 138);
    if (guest.locked) {
      if (!drawVillageProp(ctx, room, "closed-door", x-36, 267, 72, 80)) {
      ctx.fillStyle = "#392b29"; ctx.fillRect(x-25, 279, 50, 57);
      ctx.fillStyle = "#d0ad64"; ctx.fillRect(x+12, 305, 5, 5);
      }
      ctx.fillStyle = "#152321e8"; ctx.fillRect(x-72,249,144,24); ctx.fillStyle = "#e4c788";
      ctx.fillText("LOCKED · OCCUPIED", x, 265);
      ctx.fillStyle = "#d0ad64"; ctx.fillRect(x-5, 288, 10, 12);
    } else {
      if (!drawVillageProp(ctx, room, "open-door", x-36,277,72,78)) {ctx.fillStyle = "#a47c53"; ctx.fillRect(x-26, 317, 52, 25);}
      if (!drawVillageProp(ctx, room, "bed", x-42,guest.y-40,84,108,index)) {
      ctx.fillStyle = "#51372b"; ctx.fillRect(x-32, guest.y-30, 64, 87);
      ctx.fillStyle = "#76acac"; ctx.fillRect(x-27, guest.y-12, 54, 63);
      ctx.fillStyle = "#f5e5cb"; ctx.fillRect(x-27, guest.y-25, 54, 17);
      }
      ctx.fillStyle = "#152321e8"; ctx.fillRect(x-72,263,144,24);
      ctx.fillStyle = "#fff0ca"; ctx.fillText(room.nearbyNpc?.id === "bed_"+guest.id ? "E · REST & SAVE" : "GUEST BED", x, 280);
    }
  }
  drawStairs(ctx, 710, 430, "DOWNSTAIRS", room);
  ctx.fillStyle = "#152321e8"; ctx.fillRect(290,58,380,30);
  ctx.fillStyle = "#fff0ca"; ctx.font = "bold 14px monospace"; ctx.textAlign = "center"; ctx.fillText("INN · UPSTAIRS GUEST ROOMS", 480, 80);
}
function drawStoryNpc(ctx, x, y, label, wounded=false, moving=false) {
  drawCharacterShadow(ctx, x, y+14, 17);
  if (window.GauntletAdventureSprites?.npc(ctx,wounded?'injured':'runner',x,y,{moving})) {
    ctx.fillStyle='#fff0ca';ctx.font='bold 12px monospace';ctx.textAlign='center';ctx.fillText(label,x,y-42);return;
  }
  ctx.save(); ctx.translate(x, y); if (wounded) ctx.rotate(-.4);
  const imported = window.GauntletTownSprites?.character(ctx, wounded ? "Villager04" : "Villager02", 0, 0, { mode: moving ? "walk" : "idle", scale: 1.05 });
  if (!imported) {
  ctx.fillStyle = wounded ? "#8f6958" : "#d6af66"; ctx.fillRect(-11,-12,22,26);
  ctx.fillStyle = "#f0c89f"; ctx.fillRect(-8,-26,16,13);
  ctx.fillStyle = "#362b2b"; ctx.fillRect(-9,-28,18,5); ctx.fillRect(-9,12,7,10); ctx.fillRect(2,12,7,10);
  }
  if (wounded) { ctx.fillStyle = "#f5e7cb"; ctx.fillRect(-11,-5,22,6); ctx.fillStyle = "#b95050"; ctx.fillRect(-4,-5,4,6); }
  ctx.restore(); ctx.fillStyle = "#fff0ca"; ctx.font = "bold 12px monospace"; ctx.textAlign = "center"; ctx.fillText(label, x, y-42);
}
function drawVillageRunner(ctx, room) {
  const npc = room.townWelcome;
  if (npc && !npc.done) drawStoryNpc(ctx, npc.x, npc.y, "VILLAGE RUNNER", false, npc.y < 405);
}
function drawPeacefulClearing(ctx, room) {
  const smooth=window.GauntletWorldScenery?.floor(ctx,room,960,540);
  if(!smooth) {
  const artwork = villageImage(room, "hunter");
  if (artwork) { ctx.imageSmoothingEnabled = false; ctx.drawImage(artwork,0,0,960,540); }
  else {
  ctx.fillStyle = "#243f32"; ctx.fillRect(0,0,960,540);
  ctx.fillStyle = "#947951"; ctx.fillRect(426,0,108,540);
  for (const [x,y] of [[250,150],[710,130],[190,390],[760,380]]) {
    ctx.fillStyle = "#604931"; ctx.fillRect(x-8,y,16,50); ctx.fillStyle = "#456b45"; ctx.fillRect(x-40,y-50,80,65);
  }
  ctx.fillStyle = "#778179"; ctx.beginPath(); ctx.arc(525,265,29,0,Math.PI*2); ctx.fill();
  }
  }
  ctx.fillStyle = "#152321dc"; ctx.fillRect(374,191,212,24);
  drawStoryNpc(ctx,480,250, room.nearbyNpc ? "E · WOUNDED HUNTER" : "WOUNDED HUNTER",true);
  if (room.questAccepted) { ctx.fillStyle = "#ffe389"; ctx.font = "bold 32px monospace"; ctx.textAlign = "center"; ctx.fillText("↑",480,50); }
}
