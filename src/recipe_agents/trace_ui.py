"""Small dependency-free browser for the application's learning traces."""

TRACE_UI_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recipe Agent Trace</title>
<style>
:root{color-scheme:light;--bg:#f4f7fa;--panel:#ffffff;--line:#d7e0e8;--text:#172431;
--muted:#63778a;--cyan:#087f8c;--orange:#b85f00;--purple:#7047b8;--red:#c83748;
--series-1:#7047b8;--series-2:#b85f00;--series-3:#087f8c;--series-4:#c83748}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui}
header{position:sticky;top:0;z-index:2;display:flex;gap:14px;align-items:center;padding:12px 18px;
background:#ffffff;border-bottom:1px solid var(--line);box-shadow:0 1px 5px #19324a12} h1{font-size:16px;margin:0;color:var(--cyan)}
select,button{background:var(--panel);border:1px solid var(--line);border-radius:7px;color:var(--text);padding:7px}.followlatest{display:flex;align-items:center;gap:5px;color:var(--muted);font-size:12px;white-space:nowrap}.followlatest input{margin:0}
.status{margin-left:auto;color:var(--muted)} main{--left-pane:240px;--right-pane:520px;display:grid;grid-template-columns:var(--left-pane) 7px minmax(300px,1fr) 7px var(--right-pane);
height:calc(100vh - 58px);overflow:hidden}
aside{padding:16px;color:var(--muted);overflow:auto} aside strong{color:var(--text)}
.resizer{position:relative;z-index:3;cursor:col-resize;touch-action:none;background:#edf2f5;outline:none}.resizer:after{content:'';position:absolute;top:0;bottom:0;left:3px;width:1px;background:#aebdc8}
.resizer:hover,.resizer.dragging,.resizer:focus-visible{background:#dcedf0}.resizer:hover:after,.resizer.dragging:after,.resizer:focus-visible:after{background:var(--cyan);width:2px}
body.resizing{cursor:col-resize;user-select:none}
#events{padding:16px;min-width:0;overflow:auto}.event{width:100%;text-align:left;color:var(--text);background:var(--panel);
border:1px solid var(--line);border-left:4px solid var(--cyan);border-radius:8px;margin:0 0 10px;padding:10px 12px;cursor:pointer}
.event:hover{border-color:#8da4b8;background:#f9fbfc}.event.selected{background:#e8f6f7;box-shadow:0 0 0 1px var(--cyan) inset}.event.tool{border-left-color:var(--orange)}
.event:focus-visible,.turnhead:focus-visible,.modelturnhead:focus-visible{outline:3px solid #70c6cd;outline-offset:2px}
.event.model{border-left-color:var(--purple)}.event.error{border-left-color:var(--red)}.eventline{display:flex;gap:6px 10px;align-items:center;flex-wrap:wrap}.kind{overflow-wrap:anywhere}
.turngroup{margin:0 0 14px;border:1px solid var(--line);border-radius:10px;background:#f9fbfc;overflow:hidden}.turngroup[open]{border-color:#96adb9}
.turnhead{display:flex;align-items:center;gap:9px;padding:10px 12px;cursor:pointer;background:#edf3f6;list-style:none}.turnhead::-webkit-details-marker{display:none}
.turnhead:before{content:'▸';color:var(--cyan);transition:transform .15s}.turngroup[open]>.turnhead:before{transform:rotate(90deg)}
.turnlabel{font-weight:700}.turnid,.turncount,.turnagents{color:var(--muted);font:12px ui-monospace,monospace}.turnagents{margin-left:auto}.turncount{margin-left:4px}
.turnevents{padding:10px;overflow-x:auto;scrollbar-gutter:stable}.agenttimeline{--agent-count:1;display:grid;grid-template-columns:repeat(var(--agent-count),minmax(220px,1fr));
grid-auto-rows:auto;gap:10px;min-width:calc(var(--agent-count) * 220px)}
.agentlanehead{grid-row:1;min-width:0;padding:7px 9px;border-top:3px solid var(--agent-color);background:#edf3f6;color:var(--text);font:12px ui-monospace,monospace}
.agentlanehead span{display:block;color:var(--muted);font-size:10px}.modelturn{align-self:start;margin:0;border:1px solid #dce3ed;border-top:3px solid var(--agent-color,var(--purple));border-radius:8px;background:#fff;overflow:hidden}.modelturn[open]{border-color:#b8a6d8;border-top-color:var(--agent-color,var(--purple))}
.requestphase{margin-bottom:10px;border-top-color:var(--cyan)}
.modelturnhead{display:flex;align-items:center;gap:6px 8px;flex-wrap:wrap;padding:8px 10px;cursor:pointer;background:#f5f1fb;list-style:none}.modelturnhead::-webkit-details-marker{display:none}
.modelturnhead:before{content:'▸';color:var(--purple);transition:transform .15s}.modelturn[open]>.modelturnhead:before{transform:rotate(90deg)}
.modelturnlabel{font-weight:700;color:#54358d}.modelturntime{color:var(--muted);font:10px ui-monospace,monospace;white-space:nowrap}.modelturncount{margin-left:auto;color:var(--muted);font:12px ui-monospace,monospace}.modelturnevents{padding:9px 9px 0}
.time,.agent{color:var(--muted);font:12px ui-monospace,monospace}.kind{font-weight:700}.turn{margin-left:auto}
#inspector{min-width:0;min-height:0;border-left:1px solid var(--line);background:#ffffff;display:flex;flex-direction:column;overflow:hidden}
.inspecthead{padding:14px 16px;border-bottom:1px solid var(--line);background:#f3f7f9}.inspecthead h2{font-size:14px;margin:0 0 5px;color:var(--cyan)}
#gaugepanel{flex:0 0 auto;padding:10px 16px 11px;border-bottom:1px solid var(--line);background:#fbfdfe}
.gaugehead{display:flex;align-items:baseline;gap:8px}.gaugehead h2{font-size:14px;margin:0;color:var(--cyan)}#gaugescope{margin-left:auto;color:var(--muted);font:11px ui-monospace,monospace}
.gaugegrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(92px,1fr));gap:7px 12px;margin-top:7px}.gauge{min-width:0}.gaugelabel{display:flex;justify-content:space-between;gap:6px;color:var(--muted);font:11px ui-monospace,monospace}
.gaugevalue{color:var(--text);white-space:nowrap}.gaugetrack{height:5px;margin-top:4px;border-radius:4px;background:#e4ebf0;overflow:hidden}.gaugefill{height:100%;width:0;background:var(--cyan);transition:width .16s ease}
.gauge:nth-child(3) .gaugefill{background:var(--purple)}.gauge:nth-child(4) .gaugefill{background:var(--orange)}.gauge.unavailable .gaugetrack{background:repeating-linear-gradient(135deg,#e4ebf0,#e4ebf0 4px,#f7f9fb 4px,#f7f9fb 8px)}
#gaugemeta{margin-top:6px;color:var(--muted);font:11px ui-monospace,monospace}
#contextpanel{flex:0 0 auto;padding:12px 16px 8px;border-bottom:1px solid var(--line);background:#fff}
.contexthead{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}.contexthead h2{font-size:14px;margin:0;color:var(--purple)}
#contextnote,#contextdetail{color:var(--muted);font:11px/1.4 ui-monospace,monospace}.contexthead #contextnote{margin-left:auto}
#contextlegend{display:flex;gap:11px;flex-wrap:wrap;min-height:21px;margin-top:5px;color:var(--muted);font:11px ui-monospace,monospace}
.legenditem{display:inline-flex;gap:5px;align-items:center}.legendswatch{width:14px;height:3px;border-radius:2px;background:var(--swatch)}
.chartwrap{position:relative;min-height:188px}#contextchart{display:block;width:100%;height:188px;overflow:visible}
#contextempty{position:absolute;inset:0;display:grid;place-items:center;color:var(--muted);font-size:12px}#contextempty[hidden]{display:none}
.chart-frame{fill:#fbfdfe;stroke:var(--line)}.chart-grid{stroke:#e4ebf0;stroke-width:1}.chart-axis{fill:var(--muted);font:11px ui-monospace,monospace}
.chart-axis-title{fill:var(--text);font:11px system-ui}.chart-line{fill:none;stroke-width:2}.chart-focus-line{fill:none;stroke-width:7;opacity:.2}
.chart-stop{stroke:var(--purple);stroke-width:1;stroke-dasharray:3 3}.chart-stop-label{fill:var(--purple);font:10px ui-monospace,monospace;text-anchor:end}
.chart-point{cursor:pointer;stroke-width:2}.chart-point.active{stroke-width:4}.chart-delta{fill:var(--text);font:10px ui-monospace,monospace;text-anchor:middle;pointer-events:none}
#contextdetail{display:flex;gap:7px;align-items:baseline;min-height:20px;margin-top:-2px;color:var(--text);white-space:normal}
#contextdelta{color:var(--purple);font-size:14px;white-space:nowrap}#contextcause{color:var(--muted)}
#inspectmeta{color:var(--muted);font:12px ui-monospace,monospace}#inspectjson{flex:1 1 0;min-height:0;margin:0;padding:16px;overflow-x:hidden;overflow-y:scroll;
scrollbar-gutter:stable;overscroll-behavior:contain;white-space:pre-wrap;word-break:break-word;color:#26394a;font:12px/1.55 ui-monospace,monospace}
#inspectjson::-webkit-scrollbar{width:12px}#inspectjson::-webkit-scrollbar-track{background:#eef3f6}
#inspectjson::-webkit-scrollbar-thumb{background:#9aaebb;border:3px solid #eef3f6;border-radius:8px}#inspectjson::-webkit-scrollbar-thumb:hover{background:#718997}
.empty{padding:30px;color:var(--muted);text-align:center}.pill{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:1px 7px}
kbd{display:inline-block;min-width:24px;padding:1px 5px;border:1px solid #b9c5cf;border-bottom-width:2px;border-radius:4px;background:#fff;color:#33495c;
font:11px ui-monospace,monospace;text-align:center}.keys{line-height:2;color:var(--muted)}
@media(max-width:1100px){main{--left-pane:190px;--right-pane:400px}}
@media(max-width:760px){main{display:block;height:auto;overflow:visible}aside{border-right:0;border-bottom:1px solid var(--line)}
.resizer{display:none}#events{max-height:52vh}#inspector{height:55vh;border-left:0;border-top:1px solid var(--line)}}
</style></head>
<body><header><h1>Recipe Agent Trace</h1><select id="sessions"><option>waiting for a session…</option></select>
<label class="followlatest"><input id="followlatest" type="checkbox" checked> Follow latest call</label>
<button id="clear">Clear view</button><span class="status" id="status">connecting…</span></header>
<main><aside><strong>What you are seeing</strong><p>Events arrive from FastAPI, the deterministic Python orchestrator, the Strands experts, and Ollama's raw stream.</p>
<p><span class="pill">purple</span> model/context<br><span class="pill">orange</span> tool call<br><span class="pill">cyan</span> lifecycle</p>
<p><strong>Request</strong> means one user/API message. Inside it, each agent has a lane. Calls are ordered by start time; overlapping calls share a row and appear side by side.</p>
<p><strong>Context growth</strong> follows the selected event. The label at each point is the change since that same agent's previous call; the emphasized segment names the preceding tool step, and a hollow point is the live projection.</p>
<p>The current LLM turn opens automatically. The running event also appears in the right inspector; click any earlier event to inspect the same content there.</p>
<p>Drag either vertical divider to resize the guide, timeline, or inspector. Focus a divider and use <kbd>←</kbd>/<kbd>→</kbd> for keyboard resizing.</p>
<strong>Keyboard</strong><p class="keys"><kbd>↑</kbd> <kbd>↓</kbd> previous / next message<br>
<kbd>←</kbd> <kbd>→</kbd> close / open group<br><kbd>Home</kbd> <kbd>End</kbd> first / last message<br>
<kbd>PgUp</kbd> <kbd>PgDn</kbd> scroll output</p></aside><div class="resizer" data-resizer="left" role="separator" aria-label="Resize guide and timeline columns" aria-orientation="vertical" tabindex="0"></div>
<section id="events"><div class="empty">Send a request to <code>POST /recipes</code>.</div></section>
<div class="resizer" data-resizer="right" role="separator" aria-label="Resize timeline and inspector columns" aria-orientation="vertical" tabindex="0"></div>
<section id="inspector"><div class="inspecthead"><h2 id="inspecttitle">Live step output</h2><div id="inspectmeta">Waiting for an event…</div></div>
<section id="gaugepanel" aria-labelledby="gaugetitle"><div class="gaugehead"><h2 id="gaugetitle">Live counters</h2><span id="gaugescope">through selected step</span></div>
<div class="gaugegrid">
<div class="gauge" data-gauge="models"><div class="gaugelabel"><span>LLM calls</span><strong class="gaugevalue">0 / 0</strong></div><div class="gaugetrack" role="progressbar" aria-label="Completed LLM calls"><div class="gaugefill"></div></div></div>
<div class="gauge" data-gauge="tools"><div class="gaugelabel"><span>Tool calls</span><strong class="gaugevalue">0 / 0</strong></div><div class="gaugetrack" role="progressbar" aria-label="Completed tool calls"><div class="gaugefill"></div></div></div>
<div class="gauge" data-gauge="tokens"><div class="gaugelabel"><span>Tokens in / out</span><strong class="gaugevalue">—</strong></div><div class="gaugetrack" role="progressbar" aria-label="Output share of reported tokens"><div class="gaugefill"></div></div></div>
<div class="gauge unavailable" data-gauge="cache"><div class="gaugelabel"><span>Cache read</span><strong class="gaugevalue">not reported</strong></div><div class="gaugetrack" role="progressbar" aria-label="Cache read share of input tokens"><div class="gaugefill"></div></div></div>
<div class="gauge" data-gauge="ttft"><div class="gaugelabel"><span>Latest TTFT</span><strong class="gaugevalue">—</strong></div><div class="gaugetrack" role="progressbar" aria-label="Latest time to first token as share of model duration"><div class="gaugefill"></div></div></div>
</div><div id="gaugemeta">active 0 LLM · 0 tools · elapsed 0.00s</div></section>
<section id="contextpanel" aria-labelledby="contexttitle"><div class="contexthead"><h2 id="contexttitle">Context growth by agent</h2><span id="contextnote">input tokens · all requests</span></div>
<div id="contextlegend" aria-label="Agent legend"></div><div class="chartwrap"><svg id="contextchart" role="img" aria-labelledby="contexttitle contextdesc"></svg>
<span id="contextdesc" hidden>Input context tokens for each agent at every model call in this session.</span><div id="contextempty">Waiting for the first model call…</div></div>
<div id="contextdetail" aria-live="polite"><strong id="contextdelta">Waiting</strong><span id="contextcause">Each point will show total input tokens and per-agent change.</span></div></section>
<pre id="inspectjson">The newest running step will appear here automatically.</pre></section></main>
<script>
const sessions=document.querySelector('#sessions'), events=document.querySelector('#events'), status=document.querySelector('#status'),followLatest=document.querySelector('#followlatest');
const inspectTitle=document.querySelector('#inspecttitle'),inspectMeta=document.querySelector('#inspectmeta'),inspectJson=document.querySelector('#inspectjson');
const contextChart=document.querySelector('#contextchart'),contextLegend=document.querySelector('#contextlegend'),contextNote=document.querySelector('#contextnote');
const contextEmpty=document.querySelector('#contextempty'),contextDelta=document.querySelector('#contextdelta'),contextCause=document.querySelector('#contextcause');
const gauges=new Map([...document.querySelectorAll('[data-gauge]')].map(node=>[node.dataset.gauge,{root:node,value:node.querySelector('.gaugevalue'),track:node.querySelector('.gaugetrack'),fill:node.querySelector('.gaugefill')}]));
const gaugeMeta=document.querySelector('#gaugemeta'),gaugeScope=document.querySelector('#gaugescope');
const main=document.querySelector('main'),paneHandles=[...document.querySelectorAll('.resizer')],paneStorageKey='recipe-trace-pane-widths-v1';
let source=null,current='',count=0,selected=null,eventCards=[],turnGroups=new Map(),preferred=new URLSearchParams(location.search).get('session');
let contextPoints=[],contextSequence=0,activeContextPoint=null,agentStyles=new Map(),pendingSteps=new Map();
let gaugeState=newGaugeState();
const cls=k=>k.includes('tool')?'tool':k.includes('model')||k.includes('reasoning')?'model':k.includes('error')?'error':'';
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
function currentPaneWidths(){return {left:document.querySelector('aside').getBoundingClientRect().width,right:document.querySelector('#inspector').getBoundingClientRect().width}}
function setPaneWidths(left,right,changed='auto',persist=false){if(matchMedia('(max-width:760px)').matches)return;const total=main.clientWidth,gutters=14,minLeft=150,minRight=300,minCenter=280,available=Math.max(minLeft+minRight,total-gutters-minCenter);
 let nextLeft=clamp(Number(left)||240,minLeft,Math.max(minLeft,available-minRight)),nextRight=clamp(Number(right)||520,minRight,Math.max(minRight,available-minLeft));
 if(nextLeft+nextRight>available){if(changed==='left')nextLeft=Math.max(minLeft,available-nextRight);else if(changed==='right')nextRight=Math.max(minRight,available-nextLeft);else{let overflow=nextLeft+nextRight-available,take=Math.min(overflow,nextRight-minRight);nextRight-=take;overflow-=take;nextLeft-=Math.min(overflow,nextLeft-minLeft)}}
 main.style.setProperty('--left-pane',Math.round(nextLeft)+'px');main.style.setProperty('--right-pane',Math.round(nextRight)+'px');
 const leftHandle=paneHandles.find(handle=>handle.dataset.resizer==='left'),rightHandle=paneHandles.find(handle=>handle.dataset.resizer==='right');
 leftHandle.setAttribute('aria-valuemin',String(minLeft));leftHandle.setAttribute('aria-valuemax',String(Math.round(available-nextRight)));leftHandle.setAttribute('aria-valuenow',String(Math.round(nextLeft)));
 rightHandle.setAttribute('aria-valuemin',String(minRight));rightHandle.setAttribute('aria-valuemax',String(Math.round(available-nextLeft)));rightHandle.setAttribute('aria-valuenow',String(Math.round(nextRight)));
 if(persist)try{localStorage.setItem(paneStorageKey,JSON.stringify({left:nextLeft,right:nextRight}))}catch(error){}}
function resizeAt(handle,clientX,persist=false){const rect=main.getBoundingClientRect(),widths=currentPaneWidths();if(handle.dataset.resizer==='left')setPaneWidths(clientX-rect.left,widths.right,'left',persist);else setPaneWidths(widths.left,rect.right-clientX,'right',persist)}
function beginResize(event){if(matchMedia('(max-width:760px)').matches)return;event.preventDefault();const handle=event.currentTarget;handle.classList.add('dragging');document.body.classList.add('resizing');
 const move=pointer=>resizeAt(handle,pointer.clientX),end=pointer=>{resizeAt(handle,pointer.clientX,true);handle.classList.remove('dragging');document.body.classList.remove('resizing');window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',end)};
 window.addEventListener('pointermove',move);window.addEventListener('pointerup',end)}
function initializePanes(){let saved={};try{saved=JSON.parse(localStorage.getItem(paneStorageKey)||'{}')}catch(error){}const widths=currentPaneWidths();setPaneWidths(saved.left||widths.left,saved.right||widths.right)}
for(const handle of paneHandles){handle.addEventListener('pointerdown',beginResize);handle.addEventListener('keydown',event=>{if(event.key!=='ArrowLeft'&&event.key!=='ArrowRight')return;event.preventDefault();event.stopPropagation();
 const direction=event.key==='ArrowRight'?1:-1,step=event.shiftKey?40:12,widths=currentPaneWidths();if(handle.dataset.resizer==='left')setPaneWidths(widths.left+direction*step,widths.right,'left',true);else setPaneWidths(widths.left,widths.right-direction*step,'right',true)})}
window.addEventListener('resize',()=>{const widths=currentPaneWidths();setPaneWidths(widths.left,widths.right)});requestAnimationFrame(initializePanes);
function show(ev,card){if(selected)selected.classList.remove('selected');selected=card||null;if(selected)selected.classList.add('selected');
 activeContextPoint=card?.closest('.modelturn')?.contextPoint||null;renderContextChart();renderGauges();
 inspectTitle.textContent=ev.event;inspectMeta.textContent=`${ev.agent} · request ${ev.turn_id} · ${new Date(ev.timestamp).toLocaleTimeString()}`;
 inspectJson.textContent=JSON.stringify(ev.data,null,2);inspectJson.scrollTop=0}
function reveal(card){const request=card.closest('.turngroup'),phase=card.closest('.modelturn');if(request)request.open=true;if(phase)phase.open=true}
function keepVisible(card){const viewport=events.getBoundingClientRect(),box=card.getBoundingClientRect(),pad=12;
 if(box.top<viewport.top+pad)events.scrollTop+=box.top-viewport.top-pad;
 else if(box.bottom>viewport.bottom-pad)events.scrollTop+=box.bottom-viewport.bottom+pad;
 const timeline=card.closest('.turnevents');if(!timeline)return;const lane=timeline.getBoundingClientRect();
 if(box.left<lane.left+pad)timeline.scrollLeft+=box.left-lane.left-pad;else if(box.right>lane.right-pad)timeline.scrollLeft+=box.right-lane.right+pad}
function selectCard(card){if(!card)return;reveal(card);show(card.traceEvent,card);card.focus({preventScroll:true});keepVisible(card)}
function move(delta){if(!eventCards.length)return;let index=selected?eventCards.indexOf(selected):-1;
 if(index<0)index=delta>0?-1:eventCards.length;index=Math.max(0,Math.min(eventCards.length-1,index+delta));selectCard(eventCards[index])}
function requestFor(ev){let group=turnGroups.get(ev.turn_id);if(group)return group;
 for(const old of turnGroups.values())old.root.open=false;
 const root=document.createElement('details');root.className='turngroup';root.open=true;
 const head=document.createElement('summary');head.className='turnhead';head.innerHTML='<span class="turnlabel"></span><span class="turnid"></span><span class="turnagents"></span><span class="turncount"></span>';
 head.children[0].textContent='Request '+(turnGroups.size+1);head.children[1].textContent=ev.turn_id;head.children[2].textContent='0 agents';head.children[3].textContent='0 events';
 const body=document.createElement('div');body.className='turnevents';const timeline=document.createElement('div');timeline.className='agenttimeline';body.append(timeline);root.append(head,body);events.append(root);
 group={root,body,timeline,count:0,countLabel:head.children[3],agentLabel:head.children[2],llmCount:0,phases:[],activeByAgent:new Map(),agentOrder:[],agentHeads:new Map(),
  number:turnGroups.size+1,startMs:eventTime(ev),latestMs:eventTime(ev)};turnGroups.set(ev.turn_id,group);return group}
function eventTime(ev){const parsed=Date.parse(ev.timestamp);return Number.isFinite(parsed)?parsed:Date.now()}
function shortSeconds(ms){const seconds=Math.max(0,ms)/1000;return seconds<10?seconds.toFixed(2)+'s':seconds.toFixed(1)+'s'}
function ensureAgent(group,agent){if(group.agentHeads.has(agent))return;group.agentOrder.push(agent);const head=document.createElement('div');head.className='agentlanehead';
 head.style.setProperty('--agent-color',agentStyle(agent).color);head.innerHTML='<strong></strong><span>agent lane</span>';head.children[0].textContent=agent;group.agentHeads.set(agent,head);group.timeline.append(head);
 group.agentLabel.textContent=group.agentOrder.length+(group.agentOrder.length===1?' agent':' agents');group.timeline.style.setProperty('--agent-count',group.agentOrder.length);layoutTimeline(group)}
function newPhase(group,label,agent,startMs,kind='model'){ensureAgent(group,agent);const root=document.createElement('details');root.className='modelturn';root.open=true;root.style.setProperty('--agent-color',agentStyle(agent).color);
 const head=document.createElement('summary');head.className='modelturnhead';head.innerHTML='<span class="modelturnlabel"></span><span class="modelturntime"></span><span class="modelturncount"></span>';
 head.children[0].textContent=label;head.children[1].textContent='starting';head.children[2].textContent='0 events';const body=document.createElement('div');body.className='modelturnevents';
 root.append(head,body);group.timeline.append(root);const phase={root,body,count:0,countLabel:head.children[2],timeLabel:head.children[1],agent,startMs,endMs:null,kind};
 group.phases.push(phase);group.activeByAgent.set(agent,phase);layoutTimeline(group);return phase}
function newRequestPhase(group,startMs){const root=document.createElement('details');root.className='modelturn requestphase';root.open=true;
 const head=document.createElement('summary');head.className='modelturnhead';head.innerHTML='<span class="modelturnlabel">Request setup</span><span class="modelturntime">+0.00s · running</span><span class="modelturncount">0 events</span>';
 const body=document.createElement('div');body.className='modelturnevents';root.append(head,body);group.body.insertBefore(root,group.timeline);
 return group.systemPhase={root,body,count:0,countLabel:head.children[2],timeLabel:head.children[1],agent:'application',startMs,endMs:null,kind:'setup'}}
function layoutTimeline(group){const phases=[...group.phases].sort((a,b)=>a.startMs-b.startMs),columns=new Map(group.agentOrder.map((agent,index)=>[agent,index+1]));
 group.agentOrder.forEach((agent,index)=>{const head=group.agentHeads.get(agent);head.style.gridColumn=String(index+1);head.style.gridRow='1'});let row=1,waveEnd=-Infinity;
 for(const phase of phases){const intervalEnd=phase.endMs??Number.POSITIVE_INFINITY,displayEnd=phase.endMs??group.latestMs;if(phase.startMs>=waveEnd){row++;waveEnd=intervalEnd}else waveEnd=Math.max(waveEnd,intervalEnd);
  phase.root.style.gridColumn=String(columns.get(phase.agent));phase.root.style.gridRow=String(row);const offset=shortSeconds(phase.startMs-group.startMs),duration=shortSeconds(displayEnd-phase.startMs);
  phase.timeLabel.textContent='+'+offset+' · '+duration+(phase.endMs===null?' running':'') }}
function phaseFor(ev,group){const when=eventTime(ev);group.latestMs=Math.max(group.latestMs,when);if(ev.agent==='application'){
  const phase=group.systemPhase||newRequestPhase(group,when);if(ev.event==='api_response'||ev.event.includes('error'))phase.endMs=when;const finish=phase.endMs??group.latestMs;
  phase.timeLabel.textContent='+0.00s · '+shortSeconds(finish-phase.startMs)+(phase.endMs===null?' running':'');return phase}
 if(ev.event==='model_call_start'){const setup=group.activeByAgent.get(ev.agent);if(setup&&setup.kind==='setup'&&setup.endMs===null)setup.endMs=when;group.llmCount++;
  return newPhase(group,'LLM turn '+group.llmCount,ev.agent,when)}
 let phase=group.activeByAgent.get(ev.agent);if(!phase)phase=newPhase(group,'Agent setup',ev.agent,when,'setup');
 if(ev.event==='model_call_end'&&phase.kind==='model')phase.endMs=when;else if(ev.event==='agent_invocation_end'&&phase.endMs===null)phase.endMs=when;layoutTimeline(group);return phase}
const svgNS='http://www.w3.org/2000/svg';
function svgEl(name,attrs={},label=''){const node=document.createElementNS(svgNS,name);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);if(label)node.textContent=label;return node}
function finite(value){if(value===null||value===undefined||value==='')return null;const number=Number(value);return Number.isFinite(number)?number:null}
function agentStyle(agent){if(agentStyles.has(agent))return agentStyles.get(agent);const colors=['var(--series-1)','var(--series-2)','var(--series-3)','var(--series-4)'];
 const style={color:colors[agentStyles.size%colors.length]};agentStyles.set(agent,style);return style}
function inputTokens(ev){return finite(ev.data?.token_usage?.inputTokens??ev.data?.message?.metadata?.usage?.inputTokens)}
function tokenValue(ev,key){return finite(ev.data?.token_usage?.[key]??ev.data?.message?.metadata?.usage?.[key])}
function chartCutoff(){return selected?.traceIndex??Number.POSITIVE_INFINITY}
function newGaugeState(){return {modelStarts:0,modelEnds:0,toolStarts:0,toolEnds:0,input:0,output:0,reportedTokens:false,cacheRead:0,cacheReported:false,latestTtft:null,latestDuration:null,firstMs:null,lastMs:null}}
function trackGauge(ev,card){const state=gaugeState,when=eventTime(ev);state.firstMs??=when;state.lastMs=when;if(ev.event==='model_call_start')state.modelStarts++;if(ev.event==='tool_call_start')state.toolStarts++;if(ev.event==='tool_call_end')state.toolEnds++;
 if(ev.event==='model_call_end'){state.modelEnds++;const inValue=tokenValue(ev,'inputTokens'),outValue=tokenValue(ev,'outputTokens'),cacheValue=tokenValue(ev,'cacheReadInputTokens');if(inValue!==null){state.input+=inValue;state.reportedTokens=true}if(outValue!==null){state.output+=outValue;state.reportedTokens=true}if(cacheValue!==null){state.cacheRead+=cacheValue;state.cacheReported=true}const ttft=finite(ev.data?.ttft_ms);if(ttft!==null){state.latestTtft=ttft;state.latestDuration=finite(ev.data?.duration_ms)}}card.gaugeSnapshot={...state}}
function setGauge(name,value,ratio,available=true){const gauge=gauges.get(name),percent=available?clamp(Number(ratio)||0,0,1)*100:0;gauge.value.textContent=value;gauge.fill.style.width=percent+'%';gauge.root.classList.toggle('unavailable',!available);
 gauge.track.setAttribute('aria-valuemin','0');gauge.track.setAttribute('aria-valuemax','100');gauge.track.setAttribute('aria-valuenow',available?String(Math.round(percent)):'0');gauge.track.setAttribute('aria-valuetext',value)}
function renderGauges(){const card=selected||eventCards.at(-1),state=card?.gaugeSnapshot;if(!state){setGauge('models','0 / 0',0);setGauge('tools','0 / 0',0);setGauge('tokens','—',0,false);setGauge('cache','not reported',0,false);setGauge('ttft','—',0,false);gaugeMeta.textContent='active 0 LLM · 0 tools · elapsed 0.00s';return}
 setGauge('models',`${state.modelEnds} / ${state.modelStarts}`,state.modelStarts?state.modelEnds/state.modelStarts:0);setGauge('tools',`${state.toolEnds} / ${state.toolStarts}`,state.toolStarts?state.toolEnds/state.toolStarts:0);
 const tokenTotal=state.input+state.output;setGauge('tokens',state.reportedTokens?`${state.input.toLocaleString()} / ${state.output.toLocaleString()}`:'—',tokenTotal?state.output/tokenTotal:0,state.reportedTokens);setGauge('cache',state.cacheReported?state.cacheRead.toLocaleString():'not reported',state.input?state.cacheRead/state.input:0,state.cacheReported);
 setGauge('ttft',state.latestTtft===null?'—':shortSeconds(state.latestTtft),state.latestDuration?state.latestTtft/state.latestDuration:0,state.latestTtft!==null);
 const activeModels=Math.max(0,state.modelStarts-state.modelEnds),activeTools=Math.max(0,state.toolStarts-state.toolEnds),atLiveEdge=card===eventCards.at(-1),elapsedEnd=atLiveEdge&&(activeModels||activeTools)?Date.now():state.lastMs;
 gaugeMeta.textContent=`active ${activeModels} LLM · ${activeTools} tools · elapsed ${shortSeconds(elapsedEnd-state.firstMs)}`;gaugeScope.textContent=`through step ${card.traceIndex+1} of ${eventCards.length}`}
function pointValue(point,cutoff=chartCutoff()){return point.actual!==null&&point.endEventIndex<=cutoff?point.actual:point.projected}
function previousPoint(point,cutoff=chartCutoff()){return contextPoints.filter(other=>other.agent===point.agent&&other.sequence<point.sequence&&other.startEventIndex<=cutoff&&pointValue(other,cutoff)!==null).at(-1)||null}
function pointDelta(point,cutoff=chartCutoff()){const previous=previousPoint(point,cutoff);return previous?pointValue(point,cutoff)-pointValue(previous,cutoff):null}
function signed(value){if(value===null)return 'baseline';return (value>=0?'+':'')+value.toLocaleString()}
function pointSummary(point,cutoff=chartCutoff()){const value=pointValue(point,cutoff),actual=point.actual!==null&&point.endEventIndex<=cutoff,delta=pointDelta(point,cutoff),after=point.afterSteps.length?' · observed after '+point.afterSteps.join(', '):'';
 return `${point.agent} · request ${point.requestNumber}, LLM turn ${point.turnNumber} · ${value.toLocaleString()} input tokens (${actual?'actual':'projected'}) · ${signed(delta)} vs previous ${point.agent} call${after}`}
function niceMax(value){const rough=Math.max(100,value*1.12),power=10**Math.floor(Math.log10(rough)),step=power*(rough/power>5?2:rough/power>2?1:.5);return Math.ceil(rough/step)*step}
function renderContextChart(){const cutoff=chartCutoff(),points=contextPoints.filter(point=>point.startEventIndex<=cutoff&&pointValue(point,cutoff)!==null);contextChart.replaceChildren();contextLegend.replaceChildren();contextEmpty.hidden=points.length>0;
 if(!points.length){contextEmpty.textContent=contextPoints.length?'No model call has started at this trace position.':'Waiting for the first model call…';contextDelta.textContent='Waiting';contextCause.textContent='Move to a model call to see its context.';contextNote.textContent='input tokens · selected position';return}
 const agents=[...new Set(points.map(point=>point.agent))];for(const agent of agents){const item=document.createElement('span');item.className='legenditem';
  const swatch=document.createElement('span');swatch.className='legendswatch';swatch.style.setProperty('--swatch',agentStyle(agent).color);item.append(swatch,document.createTextNode(agent));contextLegend.append(item)}
 const width=Math.max(330,Math.round(contextChart.getBoundingClientRect().width||420)),height=188,margin={top:20,right:18,bottom:34,left:54};contextChart.setAttribute('viewBox',`0 0 ${width} ${height}`);
 const plotW=width-margin.left-margin.right,plotH=height-margin.top-margin.bottom,minX=points[0].sequence,maxX=points.at(-1).sequence,maxY=niceMax(Math.max(...points.map(point=>pointValue(point,cutoff))));
 const x=sequence=>margin.left+(maxX===minX?plotW/2:(sequence-minX)/(maxX-minX)*plotW),y=value=>margin.top+plotH-value/maxY*plotH;
 contextChart.append(svgEl('rect',{x:margin.left,y:margin.top,width:plotW,height:plotH,class:'chart-frame'}));
 for(let index=0;index<=4;index++){const value=Math.round(maxY*index/4),py=y(value);contextChart.append(svgEl('line',{x1:margin.left,y1:py,x2:width-margin.right,y2:py,class:'chart-grid'}));
  contextChart.append(svgEl('text',{x:margin.left-7,y:py+4,'text-anchor':'end',class:'chart-axis'},value.toLocaleString()))}
 const tickEvery=Math.max(1,Math.ceil(points.length/6));points.forEach((point,index)=>{if(index%tickEvery&&index!==points.length-1)return;
  contextChart.append(svgEl('text',{x:x(point.sequence),y:height-17,'text-anchor':'middle',class:'chart-axis'},`R${point.requestNumber}.${point.turnNumber}`))});
 contextChart.append(svgEl('text',{x:margin.left+plotW/2,y:height-2,'text-anchor':'middle',class:'chart-axis-title'},'model call (request.turn)'));
 const yTitle=svgEl('text',{x:13,y:margin.top+plotH/2,'text-anchor':'middle',transform:`rotate(-90 13 ${margin.top+plotH/2})`,class:'chart-axis-title'},'input tokens');contextChart.append(yTitle);
 const focus=activeContextPoint&&points.includes(activeContextPoint)?activeContextPoint:points.at(-1),focusPrevious=previousPoint(focus,cutoff);
 if(focusPrevious)contextChart.append(svgEl('line',{x1:x(focusPrevious.sequence),y1:y(pointValue(focusPrevious,cutoff)),x2:x(focus.sequence),y2:y(pointValue(focus,cutoff)),stroke:agentStyle(focus.agent).color,class:'chart-focus-line'}));
 const stopX=x(focus.sequence);contextChart.append(svgEl('line',{x1:stopX,y1:margin.top,x2:stopX,y2:margin.top+plotH,class:'chart-stop'}));
 contextChart.append(svgEl('text',{x:stopX-4,y:margin.top+10,class:'chart-stop-label'},'selected'));
 for(const agent of agents){const series=points.filter(point=>point.agent===agent),style=agentStyle(agent);if(series.length>1){const path=series.map((point,index)=>(index?'L':'M')+x(point.sequence)+' '+y(pointValue(point,cutoff))).join(' ');
   contextChart.append(svgEl('path',{d:path,stroke:style.color,class:'chart-line'}))}
  for(const point of series){const actual=point.actual!==null&&point.endEventIndex<=cutoff,mark=svgEl('circle',{cx:x(point.sequence),cy:y(pointValue(point,cutoff)),r:focus===point?6:4,
    fill:actual?style.color:'#fff',stroke:style.color,class:'chart-point'+(focus===point?' active':'')});
   mark.append(svgEl('title',{},pointSummary(point,cutoff)));mark.addEventListener('click',()=>selectCard(point.endCard||point.startCard));contextChart.append(mark);
   if(points.length<=14){const delta=pointDelta(point,cutoff);contextChart.append(svgEl('text',{x:x(point.sequence),y:Math.max(margin.top+10,y(pointValue(point,cutoff))-9),class:'chart-delta'},signed(delta)))}}
 }
 contextNote.textContent=`through R${focus.requestNumber}.${focus.turnNumber} · ${points.length}/${contextPoints.length} model calls`;showSelectedContext(focus,cutoff)}
function showSelectedContext(point,cutoff){const value=pointValue(point,cutoff),delta=pointDelta(point,cutoff),actual=point.actual!==null&&point.endEventIndex<=cutoff;
 contextDelta.textContent=delta===null?'baseline':signed(delta)+' tokens';const after=point.afterSteps.length?' after '+point.afterSteps.join(', '):'';
 contextCause.textContent=`${point.agent}${after} · ${value.toLocaleString()} total (${actual?'actual':'projected'})`}
function trackContext(ev,group,phase,card){if(ev.event==='tool_call_end'){const steps=pendingSteps.get(ev.agent)||[],name=ev.data?.tool_name;if(name&&!steps.includes(name))steps.push(name);pendingSteps.set(ev.agent,steps)}
 if(ev.event==='model_call_start'){const afterSteps=[...(pendingSteps.get(ev.agent)||[])];if(group.llmCount===1&&contextPoints.some(point=>point.agent===ev.agent))afterSteps.push('new user request');pendingSteps.set(ev.agent,[]);
  const point={agent:ev.agent,sequence:++contextSequence,requestNumber:group.number,turnNumber:group.llmCount,projected:finite(ev.data?.projected_input_tokens),actual:null,
   startCard:card,startEventIndex:card.traceIndex,endCard:null,endEventIndex:Number.POSITIVE_INFINITY,afterSteps};contextPoints.push(point);phase.contextPoint=point;phase.root.contextPoint=point}
 else if(ev.event==='model_call_end'&&phase.contextPoint){const actual=inputTokens(ev);if(actual!==null)phase.contextPoint.actual=actual;phase.contextPoint.endCard=card;phase.contextPoint.endEventIndex=card.traceIndex}
 renderContextChart()}
function isModelStream(ev){return ev.event==='raw_model_stream'||ev.event==='model_text_delta'}
function addModelStream(ev,group,phase,nearBottom){let card=phase.streamCard;if(!card){card=document.createElement('button');card.type='button';card.className='event model';card.traceIndex=eventCards.length;
  card.setAttribute('aria-keyshortcuts','ArrowUp ArrowDown ArrowLeft ArrowRight Home End PageUp PageDown');eventCards.push(card);const row=document.createElement('span');row.className='eventline';row.innerHTML='<span class="time"></span><span class="agent"></span><span class="kind"></span><span class="time turn">stream</span>';card.append(row);card.onclick=()=>show(card.traceEvent,card);phase.body.append(card);
  phase.streamCard=card;phase.streamSummary={raw_event_count:0,text_delta_count:0,text:'',latest_raw_event:null,note:'Per-token events are grouped here; exact individual events remain in the JSONL trace and /traces API.'}}
 const summary=phase.streamSummary;if(ev.event==='raw_model_stream'){summary.raw_event_count++;summary.latest_raw_event=ev.data?.raw_event??null}else{summary.text_delta_count++;summary.text+=ev.data?.text??''}
 card.traceEvent={...ev,event:'model_stream',data:summary};const row=card.firstElementChild;row.children[0].textContent=new Date(ev.timestamp).toLocaleTimeString();row.children[1].textContent=ev.agent;row.children[2].textContent=`model_stream · ${summary.raw_event_count+summary.text_delta_count} chunks`;trackGauge(ev,card);show(card.traceEvent,card);if(nearBottom)events.scrollTop=events.scrollHeight}
function add(ev){const nearBottom=events.scrollHeight-events.scrollTop-events.clientHeight<64;if(!count++)events.innerHTML='';
 const group=requestFor(ev);group.count++;group.countLabel.textContent=group.count+(group.count===1?' event':' events');
 group.root.open=true;const phase=phaseFor(ev,group);phase.count++;phase.countLabel.textContent=phase.count+(phase.count===1?' event':' events');phase.root.open=true;
 if(isModelStream(ev)){addModelStream(ev,group,phase,nearBottom);return}
 const card=document.createElement('button');card.type='button';card.className='event '+cls(ev.event);card.traceEvent=ev;card.traceIndex=eventCards.length;
 card.setAttribute('aria-keyshortcuts','ArrowUp ArrowDown ArrowLeft ArrowRight Home End PageUp PageDown');eventCards.push(card);
 const row=document.createElement('span');row.className='eventline';row.innerHTML='<span class="time"></span><span class="agent"></span><span class="kind"></span><span class="time turn"></span>';
 row.children[0].textContent=new Date(ev.timestamp).toLocaleTimeString();row.children[1].textContent=ev.agent;row.children[2].textContent=ev.event;
 row.children[3].textContent=cls(ev.event)||'lifecycle';card.append(row);card.onclick=()=>show(ev,card);phase.body.append(card);trackContext(ev,group,phase,card);trackGauge(ev,card);
 show(ev,card);if(nearBottom)events.scrollTop=events.scrollHeight}
function resetContext(){contextPoints=[];contextSequence=0;activeContextPoint=null;agentStyles=new Map();pendingSteps=new Map();gaugeState=newGaugeState();renderContextChart();renderGauges()}
function connect(id){if(!id||id===current)return;if(source)source.close();current=id;count=0;selected=null;eventCards=[];turnGroups=new Map();resetContext();events.innerHTML='<div class="empty">Loading trace…</div>';
 inspectTitle.textContent='Live step output';inspectMeta.textContent='Loading '+id+'…';inspectJson.textContent='The newest event will appear automatically.';
 source=new EventSource(`/traces/${encodeURIComponent(id)}/stream`);source.onopen=()=>status.textContent='live · '+id;
 source.onmessage=e=>add(JSON.parse(e.data));source.onerror=()=>status.textContent='reconnecting…';}
async function refresh(){const rows=await fetch('/traces').then(r=>r.json());const before=sessions.value;
 sessions.innerHTML=rows.length?rows.map(x=>`<option value="${x.session_id}">${x.session_id} · ${new Date(x.updated_at).toLocaleTimeString()}</option>`).join(''):'<option>waiting for a session…</option>';
 if(rows.length){const wanted=preferred&&rows.some(x=>x.session_id===preferred)?preferred:(followLatest.checked?rows[0].session_id:(rows.some(x=>x.session_id===before)?before:rows[0].session_id));
 sessions.value=wanted;preferred=null;connect(sessions.value)}}
document.addEventListener('keydown',e=>{if(e.defaultPrevented||e.altKey||e.ctrlKey||e.metaKey||e.target.tagName==='SELECT')return;
 if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();move(e.key==='ArrowDown'?1:-1);return}
 if(e.key==='Home'||e.key==='End'){e.preventDefault();selectCard(e.key==='Home'?eventCards[0]:eventCards[eventCards.length-1]);return}
 if(e.key==='PageDown'||e.key==='PageUp'){e.preventDefault();inspectJson.scrollBy({top:(e.key==='PageDown'?1:-1)*inspectJson.clientHeight*.85,behavior:'smooth'});return}
 if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;e.preventDefault();const summary=e.target.closest('summary');
 if(summary){summary.parentElement.open=e.key==='ArrowRight';return}if(!selected)return;const phase=selected.closest('.modelturn'),request=selected.closest('.turngroup');
 if(e.key==='ArrowRight'){if(request)request.open=true;if(phase)phase.open=true;return}
 if(phase&&phase.open){phase.open=false;phase.querySelector(':scope > summary').focus()}else if(request&&request.open){request.open=false;request.querySelector(':scope > summary').focus()}});
sessions.onchange=()=>{followLatest.checked=false;current='';connect(sessions.value)};followLatest.onchange=()=>{if(followLatest.checked)refresh()};document.querySelector('#clear').onclick=()=>{count=0;selected=null;eventCards=[];turnGroups=new Map();resetContext();
 events.innerHTML='<div class="empty">View cleared; new events will appear here.</div>';inspectTitle.textContent='Live step output';
 inspectMeta.textContent='Waiting for the next event…';inspectJson.textContent='The newest running step will appear here automatically.'};
new ResizeObserver(()=>renderContextChart()).observe(contextChart);
window.addEventListener('pagehide',()=>source?.close());
refresh();setInterval(refresh,1000);setInterval(renderGauges,250);
</script></body></html>"""
