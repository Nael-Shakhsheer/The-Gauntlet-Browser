/* View-only transforms. The server and combat keep their world coordinates. */
(() => {
  const clamp=(n,lo,hi)=>Math.max(lo,Math.min(hi,n));
  function size(room) {
    return room.townInterior || room.phase==='puzzle' ? [960,540] : room.areaSize || [960,540];
  }
  function scrolls(room) { const [w,h]=size(room);return Boolean(room.adventure && (w>960 || h>540)); }
  function create() {
    let view=null,scene='',last=0,held=false,until=0,pointer=null,pressedAt=0;
    function clear() { held=false;until=0;pointer=null; }
    function press(now,id=null) { held=true;until=0;pointer=id;pressedAt=now; }
    function release(now,id=null) {
      if(id!==pointer)return;
      held=false;pointer=null;
      if(id!==null && now-pressedAt<220)until=now+3000;
    }
    function peek(now) { held=false;until=now+3000; }
    function frame(room,cw,ch,now) {
      const [w,h]=size(room),large=scrolls(room);
      const key=[room.code,room.adventure?.area,room.stage,room.phase,room.townInterior,room.innFloor,w,h].join(':');
      const changed=scene!==key;scene=key;
      if(changed || !large)clear();
      const overview=large && (held || now<until);
      const fit=Math.min(cw/w,ch/h);
      const zoom=large && !overview ? Math.max(cw/(cw<600?600:960),ch/720) : fit;
      const player=room.players.find(p=>p.id===room.you) || {x:w/2,y:h/2};
      const center=(v,extent,span)=>span>=extent?extent/2:clamp(v,span/2,extent-span/2);
      const target={zoom,cx:overview || !large?w/2:center(player.x,w,cw/zoom),
        cy:overview || !large?h/2:center(player.y,h,ch/zoom)};
      // Follow predicted movement directly. Ease only the overview transition.
      if(changed || !view || cw!==view.cw || ch!==view.ch)view={...target};
      else if(overview!==view.overview || Math.abs(view.zoom-zoom)>.001) {
        const blend=1-Math.exp(-Math.min(80,Math.max(0,now-last))/65);
        for(const k of ['zoom','cx','cy'])view[k]+=(target[k]-view[k])*blend;
      } else Object.assign(view,target);
      last=now;
      // Keep every edge inside the viewport once overview settles; no stretched sprites.
      Object.assign(view,{cw,ch,w,h,large,overview});
      view.x=cw/2-view.cx*view.zoom;view.y=ch/2-view.cy*view.zoom;
      return view;
    }
    function worldPoint(clientX,clientY,rect) {
      if(!view)return null;
      return {x:((clientX-rect.left)*view.cw/rect.width-view.x)/view.zoom,
        y:((clientY-rect.top)*view.ch/rect.height-view.y)/view.zoom};
    }
    function screenPoint(x,y,rect) {
      if(!view)return null;
      return {x:rect.left+(x*view.zoom+view.x)*rect.width/view.cw,
        y:rect.top+(y*view.zoom+view.y)*rect.height/view.ch};
    }
    return {frame,worldPoint,screenPoint,press,release,peek,clear};
  }
  // Extend existing scenery with native-size grass and border strips, not enlarged trees.
  function backdrop(ctx,img,w,h) {
    if(w<=960 && h<=540){ctx.drawImage(img,0,0,w,h);return;}
    const iw=img.naturalWidth,ih=img.naturalHeight,b=48;
    const tile=document.createElement('canvas');tile.width=tile.height=192;
    const t=tile.getContext('2d');t.imageSmoothingEnabled=false;
    t.drawImage(img,iw/2-48,ih/2-48,96,96,0,0,192,192);
    ctx.fillStyle=ctx.createPattern(tile,'repeat');ctx.fillRect(0,0,w,h);
    const strip=(sx,sy,sw,sh,dx,dy,dw,dh)=>ctx.drawImage(img,sx,sy,sw,sh,dx,dy,dw,dh);
    for(let x=96;x<w-96;x+=768){const width=Math.min(768,w-96-x);
      strip(b,0,width/2,b,x,0,width,96);strip(b,ih-b,width/2,b,x,h-96,width,96);}
    for(let y=96;y<h-96;y+=348){const height=Math.min(348,h-96-y);
      strip(0,b,b,height/2,0,y,96,height);strip(iw-b,b,b,height/2,w-96,y,96,height);}
    for(const [sx,sy,dx,dy] of [[0,0,0,0],[iw-b,0,w-96,0],[0,ih-b,0,h-96],[iw-b,ih-b,w-96,h-96]])
      strip(sx,sy,b,b,dx,dy,96,96);
  }
  const landscapeRequired=(playing,touch,width,height)=>Boolean(playing && touch && height>width);
  window.GauntletCamera={create,size,scrolls,backdrop,landscapeRequired};
})();
