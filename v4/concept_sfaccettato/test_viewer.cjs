/* Offline DOM/canvas harness, not a substitute for visual browser inspection. */
"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const html=fs.readFileSync(path.join(__dirname,"output","index.html"),"utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements=new Map();
function element(id){
 if(!elements.has(id))elements.set(id,{id,value:"",checked:false,dataset:{},innerHTML:"",textContent:"",className:"",events:{},
  addEventListener(name,fn){this.events[name]=fn;},setPointerCapture(){},getBoundingClientRect(){return {width:360,height:280};}});
 return elements.get(id);
}
element("insulation").value="75";element("mechanism").value="120";element("flue").value="1000";
let paints=0;
const ctx={setTransform(){},clearRect(){},createImageData(w,h){return {data:new Uint8ClampedArray(w*h*4)};},putImageData(image){assert.ok(image.data.some((v,i)=>i%4===3&&v===255));paints++;}};
element("scene").getContext=()=>ctx;
const context=vm.createContext({document:{getElementById:element,body:{dataset:{}}},window:{addEventListener(){},devicePixelRatio:1},Intl,Math,Set,Float32Array,Uint8ClampedArray,console});
vm.runInContext(script,context,{timeout:30000});
assert.equal(context.document.body.dataset.viewerReady,"true");
const evaluate=code=>vm.runInContext(code,context,{timeout:30000});
for(const insulation of [50,75,100])for(const mechanism of [80,120,160]){
 element("insulation").value=String(insulation);element("mechanism").value=String(mechanism);evaluate("update()");
 assert.equal(evaluate("current().id"),`I${insulation}_M${mechanism}`);
 assert.equal(element("fit").className.includes("bad"),mechanism===80);
 assert.equal((element("variants").innerHTML.match(/<tr /g)||[]).length,9);
}
element("insulation").value="75";element("mechanism").value="120";element("flue").value="1500";evaluate("update()");
const completeHeight=evaluate("number(current().summary.height_with_flue_1500_mm)");
assert.ok(element("metrics").innerHTML.includes(completeHeight+" mm"));
element("cutaway").checked=true;element("body-only").checked=true;evaluate("update()");
assert.match(element("scene-state").textContent,/TRONCATO/);
assert.match(element("scene-caption").textContent,/1500 mm/);
assert.ok(element("metrics").innerHTML.includes(completeHeight+" mm")); // view crop must NOT change actual height
for(const id of ["front","side","top","reset"])element(id).events.click();
assert.ok(paints>=15);
console.log("Viewer harness OK: 9 variants, clearance warning, H1500, cutaway, explicit visual crop and 4 camera presets.");
