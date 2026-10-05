// Exercise the standalone explorer's actual script with a small DOM fixture.
// This checks behavior and numbers without requiring a browser installation.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('explore.html','utf8');
const scripts=[...html.matchAll(/<script(?:[^>]*)>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.attributes={};this.events={};this._value='';this._text='';this.hidden=false;this.dataset={};}
 set value(v){v=String(v);this._value=this.tag==='select'&&!this.children.some(c=>c.value===v)?'':v;}
 get value(){return this._value;}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join('\n');}
 append(...els){this.children.push(...els);if(this.tag==='select'&&!this._value&&els[0])this._value=els[0].value;}
 replaceChildren(...els){this.children=els;this._text='';}
 setAttribute(k,v){this.attributes[k]=String(v);}
 addEventListener(k,f){this.events[k]=f;}
}
const ids=['data','country','model','shape','strength','items','rollout-rate','aid','growth-floor','exposure-cap','culture-rate','lag','profile-metrics','profile-detail','policy-table','rollout-metrics','rollout-status','rollout-plot','rollout-count','timing-metrics','timing-plot','representation','rollout','timing'];
const selects=new Set(['country','model','shape','strength','items','rollout-rate','aid','culture-rate','lag']);
const elements=Object.fromEntries(ids.map(id=>[id,new Element(selects.has(id)?'select':'div')]));
elements.data.textContent=scripts[0];
for(const [id,values,selected] of [['model',['GPT-5.5','GPT-5.6 Sol'],'GPT-5.6 Sol'],['shape',['linear','saturating','spline'],'linear'],['strength',['0','.25','.5','1'],'1'],['items',['all six','Q48/Q57/Q159'],'all six']]){
 for(const value of values){const o=new Element('option');o.value=value;elements[id].append(o);}elements[id].value=selected;
}
elements['growth-floor'].value=10;elements['exposure-cap'].value=50;
const tabs=['representation','rollout','timing'].map(id=>{const e=new Element('button');e.dataset.tab=id;return e});
const document={getElementById:id=>elements[id],createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag),querySelectorAll:s=>s==='[data-tab]'?tabs:ids.filter(id=>selects.has(id)||id==='growth-floor'||id==='exposure-cap').map(id=>elements[id])};
const context=vm.createContext({document,console});vm.runInContext(scripts[1],context);
function render(){vm.runInContext('render()',context)}
assert(elements['rollout-count'].textContent.startsWith('3 of 7'));
assert(elements['rollout-status'].textContent.includes('meets all'));
elements.aid.value='0';render();assert(elements['rollout-count'].textContent.startsWith('0 of 7'));
elements.aid.value='0.05';render();assert(elements['rollout-count'].textContent.startsWith('0 of 7'));
elements.country.value='Nigeria';elements.strength.value='0';render();assert(elements['profile-metrics'].textContent.includes('11.347'));
elements['culture-rate'].value='1.6';elements.lag.value='6';render();assert(elements['timing-metrics'].textContent.includes('9.992'));
elements.lag.value='0';render();assert(elements['timing-metrics'].textContent.includes('81.777'));
tabs[1].events.click();assert(!elements.rollout.hidden&&elements.representation.hidden&&elements.timing.hidden);
const data=JSON.parse(scripts[0]);assert.equal(data.profiles.length,3072);
const keys=new Set(data.profiles.map(r=>[r.country,r.model,r.shape,r.strength,r.items].join('|')));assert.equal(keys.size,3072);
fs.writeFileSync('explorer-validation.json',JSON.stringify({status:'passed',scope:'Actual script with DOM fixture; JS syntax and precomputed numeric controls verified. Browser rendering unavailable because no browser binary is installed.',tests:['unique scenario keys','initial state','reference zero response','rollout at zero/2.5%/5%','fast culture with lag 0/6','tab state'],scenario_count:data.profiles.length},null,2));
console.log('Explorer script, seven behavioral/numeric checks, and all 3,072 scenario keys passed.');
