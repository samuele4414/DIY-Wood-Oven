"use strict";
// sceneData is embedded by build_study.py. No fetch/CDN or external assets.
const $ = id => document.getElementById(id);
const canvas = $("scene"), ctx = canvas.getContext("2d");
const faces = sceneData.faces.concat(sceneData.motorTriangles.map(points => ({points, group:"supplier_motor", colour:"#357c9c"})));
let yaw = .65, pitch = .45, zoom = 1, drag = null;
function project(p) {
  const x = Math.cos(yaw)*p[0] + Math.sin(yaw)*p[1], d = -Math.sin(yaw)*p[0] + Math.cos(yaw)*p[1];
  return [x, -Math.cos(pitch)*p[2] - Math.sin(pitch)*d, Math.cos(pitch)*d - Math.sin(pitch)*p[2]];
}
function shade(hex,p) {
  const a=p[1].map((v,i)=>v-p[0][i]), b=p[2].map((v,i)=>v-p[0][i]);
  const n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]], l=Math.hypot(...n);
  const strength=l<1e-8?1:.6+.4*Math.abs((.25*n[0]-.4*n[1]+.88*n[2])/l);
  return [1,3,5].map(i=>Math.round(parseInt(hex.slice(i,i+2),16)*strength));
}
function draw() {
  if(!ctx)return;
  const rect=canvas.getBoundingClientRect(), W=Math.max(100,Math.round(rect.width)), H=Math.max(100,Math.round(rect.height));
  canvas.width=W;canvas.height=H;
  const active=faces.filter(f=>(f.group!=="shield"||$("show-shield").checked)&&(f.group!=="supplier_motor"||$("show-motor").checked));
  const mapped=active.map(f=>({face:f, pts:f.points.map(project), rgb:shade(f.colour,f.points)}));
  let xmin=Infinity,xmax=-Infinity,ymin=Infinity,ymax=-Infinity;
  for(const f of mapped)for(const p of f.pts){xmin=Math.min(xmin,p[0]);xmax=Math.max(xmax,p[0]);ymin=Math.min(ymin,p[1]);ymax=Math.max(ymax,p[1]);}
  const scale=Math.min((W-60)/(xmax-xmin),(H-60)/(ymax-ymin))*zoom;
  const ox=W/2-(xmin+xmax)/2*scale,oy=H/2-(ymin+ymax)/2*scale;
  const image=ctx.createImageData(W,H),pixels=image.data,depth=new Float32Array(W*H);depth.fill(Infinity);
  for(const f of mapped){
    const pts=f.pts.map(p=>[ox+p[0]*scale,oy+p[1]*scale,p[2]]);
    for(let i=1;i<pts.length-1;i++){
      const a=pts[0],b=pts[i],c=pts[i+1],den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);
      if(Math.abs(den)<1e-9)continue;
      const x0=Math.max(0,Math.floor(Math.min(a[0],b[0],c[0]))),x1=Math.min(W-1,Math.ceil(Math.max(a[0],b[0],c[0])));
      const y0=Math.max(0,Math.floor(Math.min(a[1],b[1],c[1]))),y1=Math.min(H-1,Math.ceil(Math.max(a[1],b[1],c[1])));
      for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
        const xx=x+.5-c[0],yy=y+.5-c[1],wa=((b[1]-c[1])*xx+(c[0]-b[0])*yy)/den,wb=((c[1]-a[1])*xx+(a[0]-c[0])*yy)/den,wc=1-wa-wb;
        if(Math.min(wa,wb,wc)<-1e-8)continue;
        const k=y*W+x,z=wa*a[2]+wb*b[2]+wc*c[2];
        if(z<depth[k]){depth[k]=z;const q=k*4;pixels[q]=f.rgb[0];pixels[q+1]=f.rgb[1];pixels[q+2]=f.rgb[2];pixels[q+3]=255;}
      }
    }
  }
  ctx.putImageData(image,0,0);
  $("scene-state").textContent=$("show-shield").checked?"Schermo visibile · inviluppo completo":"Schermo occultato SOLO nella vista";
  document.body.dataset.viewerReady="true";canvas.dataset.drawnFaces=String(active.length);
}
for(const id of ["show-shield","show-motor"])$(id).addEventListener("change",draw);
for(const [id,angles] of [["front",[0,0]],["side",[Math.PI/2,0]],["top",[0,Math.PI/2]],["reset",[.65,.45]]])$(id).addEventListener("click",()=>{[yaw,pitch]=angles;zoom=1;draw();});
canvas.addEventListener("pointerdown",e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener("pointermove",e=>{if(!drag)return;yaw+=(e.clientX-drag[0])*.008;pitch=Math.max(-.1,Math.min(Math.PI/2,pitch+(e.clientY-drag[1])*.006));drag=[e.clientX,e.clientY];draw();});
canvas.addEventListener("pointerup",()=>{drag=null;});canvas.addEventListener("pointercancel",()=>{drag=null;});
canvas.addEventListener("wheel",e=>{e.preventDefault();zoom=Math.max(.5,Math.min(2.5,zoom*Math.exp(-e.deltaY*.001)));draw();},{passive:false});
window.addEventListener("resize",draw);draw();
