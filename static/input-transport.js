/* Latest-direction input. Release can overtake a lost request; server sequences
   reject late requests. Each session and scene owns its own pending transport. */
(() => {
  function create({request,now=()=>performance.now(),metric=()=>{}}){
    let owner=null,sequence=0,flight=null,pending=null,signature='',sentAt=-Infinity,generation=0,wasMoving=false,released=null;
    function cancel(){generation++;pending=null;flight?.controller.abort();flight=null;signature='';sentAt=-Infinity;wasMoving=false;released=null;}
    function session(next,ack=0){if(next!==owner){cancel();owner=next;sequence=ack;}else sequence=Math.max(sequence,ack);}
    function flush(){
      if(flight || !pending || !owner)return;
      const next=pending;pending=null;const controller=new AbortController(),started=now(),epoch=generation;
      const current={controller,signature:next.signature};flight=current;
      const stopped=!next.direction.x&&!next.direction.y&&!next.direction.attack;
      const seq=++sequence;if(released&&!released.sequence&&stopped)released.sequence=seq;
      let response;
      try{response=request({...owner,action:'input',...next.direction,scene:next.scene,sequence:seq},controller.signal);}catch(e){response=Promise.reject(e);}
      Promise.resolve(response)
        .then(()=>{if(epoch===generation && stopped)metric('releaseAckMs',now()-started);})
        .catch(()=>{}).finally(()=>{if(epoch===generation && flight===current){flight=null;flush();}});
    }
    function send(direction,scene,force=false,eventAt=now()){
      if(!owner)return;
      const current=now(),sig=[direction.x,direction.y,Boolean(direction.attack),direction.targetId||'',direction.epoch||0,scene].join(',');
      const changed=sig!==signature,heartbeat=direction.x||direction.y||direction.attack?180:1200;
      const moving=Boolean(direction.x||direction.y||direction.attack);
      if(wasMoving&&!moving)released={at:eventAt,sequence:null};wasMoving=moving;
      if(!changed && !force && current-sentAt<heartbeat)return;
      if(!changed && flight?.signature===sig)return;
      if(changed && flight){generation++;flight.controller.abort();flight=null;}
      signature=sig;sentAt=current;pending={direction:{...direction},scene,signature:sig};
      metric('inputDispatchMs',Math.max(0,current-eventAt));flush();
    }
    function observe(movement){if(released?.sequence && movement.sequence>=released.sequence && !movement.inputX&&!movement.inputY&&!movement.attacking){metric('releaseObservedMs',now()-released.at);released=null;}}
    return {session,send,cancel,observe,sequence:()=>sequence};
  }
  window.GauntletInput={create};
})();
