"""Build a dependency-free explorer of the exact precomputed scenario tables."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parent
data={name:json.loads(pd.read_csv(ROOT/'results'/filename).to_json(orient='records',double_precision=15)) for name,filename in {
    'profiles':'audit_linked_policy_results.csv','rollout':'rollout_rate_grid.csv',
    'lag':'lag_rate_grid.csv','policies':'selected_policies.csv'}.items()}
data['config']=json.loads((ROOT/'parameters.json').read_text())
payload=json.dumps(data,allow_nan=False,separators=(',',':')).replace('</','<'+chr(92)+'/')
html=r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cultural representation, innovation, and adjustment</title>
<style>
:root{color-scheme:light;--ink:#17293f;--teal:#007f86;--rose:#b93678;--gold:#a97512}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:#fff;font:17px/1.55 Georgia,serif}
main{max-width:1080px;margin:auto;padding:38px 28px 50px}h1{font-size:34px;line-height:1.2;margin:0 0 16px}h2{font-size:23px;margin:24px 0 12px}h3{font-size:19px}
p{max-width:920px;margin:12px 0}nav{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0;border-bottom:1px solid #ccd5df;padding-bottom:12px}
button,select,input{font:15px/1.4 system-ui,sans-serif;color:var(--ink);background:white;border:1px solid #8998a8;border-radius:4px;padding:8px}
button{cursor:pointer}button[aria-selected=true]{background:var(--ink);color:white}button:focus-visible,select:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.controls{display:flex;gap:16px;flex-wrap:wrap;align-items:end;margin:18px 0}.controls label{display:flex;flex-direction:column;gap:5px;font:14px/1.4 system-ui,sans-serif}
.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid #bbc7d3;border-bottom:1px solid #bbc7d3;margin:20px 0;padding:18px 0;gap:20px}.metrics strong{display:block;font-size:29px;font-weight:normal}.metrics span{display:block;font-size:15px}
.scope{font-size:15px;color:#536275}.status{padding:12px 0;color:var(--teal);font-weight:bold}.status.fail{color:var(--rose)}
table{border-collapse:collapse;width:100%;font-size:15px;margin:20px 0}th,td{text-align:left;border-bottom:1px solid #d5dde5;padding:9px 10px;vertical-align:top}th{background:#f4f7fa}a{color:var(--teal)}
svg{display:block;width:100%;max-width:820px;height:auto;margin:20px 0}svg text{font:15px Georgia,serif;fill:var(--ink)}[hidden]{display:none!important}.note{border-left:3px solid var(--gold);padding-left:16px}.scroll{overflow:auto}
@media(max-width:600px){main{padding:24px 18px}.metrics{grid-template-columns:1fr;gap:10px}h1{font-size:27px}}
</style>
<main>
<h1>Whose values guide technological change?</h1>
<p>Explore how cultural representation, assistance, and the pace of change interact. The same budget supports innovation and recovery from disruption.</p>
<p class="scope">The answer distributions are measured. Economic responses and cultural dynamics are specified mechanisms. Every result below is precomputed from the released tables. Time is normalized adjustment time, not years; quality growth and exposure are not GDP or unemployment estimates.</p>
<nav role="tablist" aria-label="Experiments">
<button role="tab" aria-selected="true" data-tab="representation">Advice and representation</button>
<button role="tab" aria-selected="false" data-tab="rollout">Rollout and assistance</button>
<button role="tab" aria-selected="false" data-tab="timing">Change and delay</button>
</nav>
<section id="representation" role="tabpanel">
<h2>The same actual economy, different descriptions</h2>
<p>Choose an archived error profile and a stated institutional response. Country names identify the source of the representation error, rather than an economic forecast for that country. All choices are evaluated with the same actual reference channel, initial states, and resource budget.</p>
<div class="controls">
<label>Error-profile source<select id="country"></select></label>
<label>Model<select id="model"><option>GPT-5.5</option><option selected>GPT-5.6 Sol</option></select></label>
<label>Response shape<select id="shape"><option value="linear">Linear</option><option value="saturating">Saturating</option><option value="spline">Smooth cubic</option></select></label>
<label>Response strength<select id="strength"><option value="0">0</option><option value="0.25">0.25</option><option value="0.5">0.50</option><option value="1" selected>1</option></select></label>
<label>Items<select id="items"><option>all six</option><option>Q48/Q57/Q159</option></select></label>
</div>
<div id="profile-metrics" class="metrics" aria-live="polite"></div><p id="profile-detail"></p>
<p class="note">Zero response strength gives the reference path for every profile. A smaller unsigned distance does not determine the direction of advice. The response weights and curvature remain assumptions to test in decision experiments.</p>
<h3>Four policies using exactly the same spending</h3><div class="scroll" id="policy-table"></div>
</section>
<section id="rollout" role="tabpanel" hidden>
<h2>Which rollout paths sustain progress?</h2>
<p>Every rate has the same opportunity endpoints, 0.90 and 1.32. Extra assistance is paid for by diverting launch resources. All policies spend the same budget at every time. A viable path must meet a growth floor, a worst-group exposure ceiling, and final adoption of at least 50%.</p>
<div class="controls">
<label>Rollout rate<select id="rollout-rate"></select></label>
<label>Additional aid<select id="aid"></select></label>
<label>Growth floor (log-quality points / time)<input id="growth-floor" type="number" min="0" max="20" step="0.5" value="10"></label>
<label>Worst-group exposure ceiling (%)<input id="exposure-cap" type="number" min="0" max="100" step="5" value="50"></label>
</div>
<div id="rollout-metrics" class="metrics" aria-live="polite"></div><p id="rollout-status" class="status"></p>
<div id="rollout-plot"></div><p id="rollout-count"></p>
<p class="note">The released criteria admit three of seven tested rates with 2.5% extra aid and none with zero or larger diversions. More aid preserves adoption but reduces innovation resources. Changing the criteria reclassifies the same computed paths; it does not rerun or fit the economic model.</p>
</section>
<section id="timing" role="tabpanel" hidden>
<h2>Values change while advice catches up</h2>
<p>The full cultural distributions share exact start and end points across change rates. The adviser chooses policy using an earlier distribution. This experiment combines cultural change with delayed policy response; the paper separately explains pure rate-induced tipping.</p>
<div class="controls"><label>Cultural-path rate<select id="culture-rate"></select></label><label>Update delay<select id="lag"></select></label></div>
<div id="timing-metrics" class="metrics" aria-live="polite"></div><div id="timing-plot"></div>
<p>Immediate updates retain high adoption at all seven tested rates. At delay six, slow change at rate 0.1 finishes near 82% adoption; fast change at rate 1.6 finishes near 10%.</p>
</section>
<h2>A short dictionary</h2>
<table><thead><tr><th>Term</th><th>Intuitive meaning</th></tr></thead><tbody>
<tr><td>Creative destruction</td><td>Innovation improves quality while replacing established activities, creating opportunities and adjustment needs.</td></tr>
<tr><td>Full marginal distribution</td><td>All answer shares for one question. They sum to one and do not identify a person's joint answers across questions.</td></tr>
<tr><td>Response channel</td><td>A declared rule translating distributions into an input to coordination; it is not a culture ranking.</td></tr>
<tr><td>Coordination and adoption</td><td>A model state describes how readily adoption can persist. Better coordination increases the adoption share.</td></tr>
<tr><td>Quality growth</td><td>Mean log frontier-quality gain per normalized time. Displayed values multiply the model rate by 100.</td></tr>
<tr><td>Worst-group exposure</td><td>The larger of two illustrative groups' time-average unresolved-adjustment shares.</td></tr>
<tr><td>Final adoption</td><td>The adoption share at the end of the horizon. It detects stalling concealed by favorable average outcomes.</td></tr>
<tr><td>Intensity versus rollout rate</td><td>Intensity concerns potential replacements per time; rollout rate concerns how quickly opportunities change between endpoints.</td></tr>
<tr><td>Attainable set</td><td>Outcomes feasible in the actual system. Beliefs choose a policy within that set without changing the actual system.</td></tr>
<tr><td>Fold and no-fold control</td><td>In a fold, stable and unstable states meet. A restoring-feedback control instead has one equilibrium and a smooth response.</td></tr>
<tr><td>Admissibility</td><td>Meeting explicitly chosen criteria. It is a research objective whose practical meaning needs community deliberation.</td></tr>
<tr><td>Conditional result</td><td>A consequence of stated assumptions and measured inputs, supplying a hypothesis for empirical tests.</td></tr>
</tbody></table>
<h2>Sources and next questions</h2>
<p>The intellectual foundations are Mokyr's useful knowledge and institutions, Aghion and Howitt's growth through creative destruction, and conventional capital accumulation. The paper supplies a 60-entry dictionary, complete equations, coefficients, evidence tables, and detailed primary sources. See the companion <a href="SOURCES.md">source guide</a> and <a href="README.md">reproduction instructions</a>.</p>
<p>Decision experiments can estimate institutions' responses to model descriptions. Locally validated repeated surveys and livelihood panels can identify cultural change, coordination feedback, and recovery from disruption. Those studies can determine whether the mechanisms support inclusive and environmentally durable innovation.</p>
</main>
<script id="data" type="application/json">__PAYLOAD__</script>
<script>
'use strict';
const D=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id),rates=D.config.cultural_forcing_rates;
function options(id,values,label=v=>String(v)){for(const v of values){const o=document.createElement('option');o.value=v;o.textContent=label(v);$(id).append(o)}}
options('country',[...new Set(D.profiles.map(d=>d.country))].sort());
for(const id of ['rollout-rate','culture-rate'])options(id,rates);
options('aid',D.config.rollout_adjustment_allocations,v=>(100*v).toFixed(1)+'%');options('lag',D.config.adviser_update_lags);
$('aid').value='.025';if(!$('aid').value)$('aid').value='0.025';$('rollout-rate').value='0.2';$('culture-rate').value='1.6';$('lag').value='6';
function metrics(id,r){$(id).replaceChildren();for(const [name,value,note] of [['Quality growth',r.growth*100,'log-quality points / normalized time'],['Worst-group exposure',r.worst_burden*100,'% time-average unresolved adjustment'],['Final adoption',r.adoption_final*100,'% at the end of time 60']]){const box=document.createElement('div'),strong=document.createElement('strong'),label=document.createElement('span'),unit=document.createElement('span');strong.textContent=value.toFixed(3);label.textContent=name;unit.textContent=note;unit.className='scope';box.append(strong,label,unit);$(id).append(box)}}
function table(id,headers,rows){const t=document.createElement('table'),head=document.createElement('thead'),tr=document.createElement('tr');for(const h of headers){const cell=document.createElement('th');cell.textContent=h;tr.append(cell)}head.append(tr);t.append(head);const body=document.createElement('tbody');for(const row of rows){const tr=document.createElement('tr');for(const v of row){const cell=document.createElement('td');cell.textContent=v;tr.append(cell)}body.append(tr)}t.append(body);$(id).replaceChildren(t)}
function chart(id,series,ylabel,selected){const W=800,H=340,p={l:75,r:35,t:25,b:65},x=v=>p.l+Math.log2(v/rates[0])/Math.log2(rates.at(-1)/rates[0])*(W-p.l-p.r);const values=series.flatMap(s=>s.rows.map(r=>r.value));let ymin=Math.min(0,...values),ymax=Math.max(...values)*1.12||1;const y=v=>H-p.b-(v-ymin)/(ymax-ymin)*(H-p.t-p.b);const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',ylabel+' at all seven rates; selected rate highlighted');function el(kind,attrs,text){const n=document.createElementNS(ns,kind);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text)n.textContent=text;svg.append(n);return n}el('line',{x1:p.l,x2:W-p.r,y1:H-p.b,y2:H-p.b,stroke:'#728091'});for(const r of rates)el('text',{x:x(r),y:H-p.b+25,'text-anchor':'middle'},String(r));for(let i=0;i<4;i++){const v=ymin+(ymax-ymin)*i/3;el('line',{x1:p.l,x2:W-p.r,y1:y(v),y2:y(v),stroke:'#e2e8ee'});el('text',{x:p.l-12,y:y(v)+5,'text-anchor':'end'},v.toFixed(1))}for(const s of series){el('polyline',{points:s.rows.map(r=>`${x(r.rate)},${y(r.value)}`).join(' '),fill:'none',stroke:s.color,'stroke-width':2});for(const r of s.rows)el('circle',{cx:x(r.rate),cy:y(r.value),r:r.rate===selected?6:3,fill:s.color,stroke:'white','stroke-width':1})}el('text',{x:p.l,y:18},ylabel);el('text',{x:W/2,y:H-8,'text-anchor':'middle'},'Path rate (same endpoints; logarithmic spacing)');$(id).replaceChildren(svg)}
function render(){const r=D.profiles.find(r=>r.country===$('country').value&&r.model===$('model').value&&r.shape===$('shape').value&&r.strength===+$('strength').value&&r.items===$('items').value);metrics('profile-metrics',r);$('profile-detail').textContent=`Perceived channel ${r.estimated_culture.toFixed(4)}; actual channel 0. Assistance allocation ${r.aid.toFixed(4)}; launch intensity ${r.nu.toFixed(4)}; spending ${r.budget_used.toFixed(2)}. The zero-response reference quality rate is ${(100*D.policies[0].growth).toFixed(3)}.`;const a=+$('aid').value,rate=+$('rollout-rate').value,floor=+$('growth-floor').value/100,cap=+$('exposure-cap').value/100,rows=D.rollout.filter(r=>r.adjustment_allocation===a),rr=rows.find(r=>r.rollout_rate===rate),pass=r=>r.growth>=floor&&r.worst_burden<=cap&&r.adoption_final>=.5;metrics('rollout-metrics',rr);$('rollout-status').textContent=pass(rr)?'This path meets all three selected criteria.':'This path does not meet all three selected criteria.';$('rollout-status').className='status'+(pass(rr)?'':' fail');$('rollout-count').textContent=`${rows.filter(pass).length} of 7 tested rates meet these criteria at ${(100*a).toFixed(1)}% extra assistance.`;chart('rollout-plot',[{color:'#a97512',rows:rows.map(r=>({rate:r.rollout_rate,value:100*r.growth}))}],'Quality growth (log-quality points / time)',rate);const cr=+$('culture-rate').value,lag=+$('lag').value,lr=D.lag.find(r=>r.forcing_rate===cr&&r.adviser_lag===lag);metrics('timing-metrics',lr);chart('timing-plot',[{color:'#007f86',rows:D.lag.filter(r=>r.adviser_lag===lag).map(r=>({rate:r.forcing_rate,value:100*r.adoption_final}))}],'Final adoption (%)',cr)}
table('policy-table',['Policy','Aid allocation','Quality growth','Worst exposure (%)','Final adoption (%)'],D.policies.map(r=>[r.policy,r.aid.toFixed(4),(100*r.growth).toFixed(3),(100*r.worst_burden).toFixed(2),(100*r.adoption_final).toFixed(2)]));
for(const el of document.querySelectorAll('select,input'))el.addEventListener('input',render);
for(const button of document.querySelectorAll('[data-tab]'))button.addEventListener('click',()=>{for(const b of document.querySelectorAll('[data-tab]')){const on=b===button;b.setAttribute('aria-selected',on);$(b.dataset.tab).hidden=!on}});
render();
</script></html>'''
(ROOT/'explore.html').write_text(html.replace('__PAYLOAD__',payload))
print('Built offline explorer with',len(data['profiles']),'representation scenarios and 70 timing/rollout cases.')
