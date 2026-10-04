/* Offline DOM/canvas harness. Physical and visual validation are separate. */
"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const html=fs.readFileSync(path.join(__dirname,"output/index.html"),"utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements=new Map();
function element(id){
  if(!elements.has(id))elements.set(id,{id,checked:false,dataset:{},textContent:"",events:{},
    addEventListener(name,fn){this.events[name]=fn;},setPointerCapture(){},getBoundingClientRect(){return {width:360,height:280};}});
  return elements.get(id);
}
element("show-motor").checked=true;
let paints=0;
element("scene").getContext=()=>({createImageData(w,h){return {data:new Uint8ClampedArray(w*h*4)};},putImageData(image){assert.ok(image.data.some((v,i)=>i%4===3&&v===255));paints++;}});
const context=vm.createContext({document:{getElementById:element,body:{dataset:{}}},window:{addEventListener(){}},Math,Float32Array,Uint8ClampedArray,console});
vm.runInContext(script,context,{timeout:60000});
assert.equal(context.document.body.dataset.viewerReady,"true");
assert.match(element("scene-state").textContent,/SOLO nella vista/);
const fullCount=Number(element("scene").dataset.drawnFaces);
assert.ok(fullCount>30000);
element("show-motor").checked=false;element("show-motor").events.change();
assert.ok(Number(element("scene").dataset.drawnFaces)<fullCount);
element("show-shield").checked=true;element("show-shield").events.change();
assert.match(element("scene-state").textContent,/Schermo visibile/);
element("show-motor").checked=true;element("show-motor").events.change();
for(const id of ["front","side","top","reset"])element(id).events.click();
assert.equal(paints,8);
console.log("C03 viewer harness OK: real-motor mesh, envelope-only warnings, visibility and four camera views; offline.");
