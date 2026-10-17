// Only immutable catalogues and revisioned skill UI are reused. Live simulation
// fields always come from the current authoritative response.
(() => {
  const fields=['classes','difficulties','skills','abilityOptions'];
  const same=(a,b)=>a&&b&&a.code===b.code&&a.you===b.you;
  function query(previous,session){
    if(!same(previous,{code:session?.room,you:session?.player}))return '';
    let out='';
    if(previous.catalogVersion&&fields.every(k=>previous[k]))out+='&catalog='+encodeURIComponent(previous.catalogVersion);
    if(previous.heroSkillsRevision&&previous.heroSkills)out+='&heroSkills='+encodeURIComponent(previous.heroSkillsRevision);
    return out;
  }
  function merge(next,previous){
    const catalog=same(next,previous)&&next.catalogVersion&&next.catalogVersion===previous.catalogVersion;
    for(const key of fields)if(next[key]===undefined){
      if(!catalog||!previous[key])throw Error('Catalogue refresh required. Reconnect to this run.');
      next[key]=previous[key];
    }
    if(!('heroSkills' in next)){
      if(!same(next,previous)||!next.heroSkillsRevision||next.heroSkillsRevision!==previous.heroSkillsRevision||!previous.heroSkills)throw Error('Skill refresh required. Reconnect to this run.');
      next.heroSkills=previous.heroSkills;
    }
    return next;
  }
  window.GauntletStateCache={query,merge};
})();
