from recipe_agents.trace_ui import TRACE_UI_HTML


def test_trace_ui_has_persistent_right_inspector() -> None:
    assert 'id="inspector"' in TRACE_UI_HTML
    assert 'id="inspectjson"' in TRACE_UI_HTML
    assert "grid-template-columns:var(--left-pane) 7px minmax(300px,1fr) 7px var(--right-pane)" in TRACE_UI_HTML


def test_main_columns_are_pointer_and_keyboard_resizable() -> None:
    assert TRACE_UI_HTML.count('role="separator"') == 2
    assert 'data-resizer="left"' in TRACE_UI_HTML
    assert 'data-resizer="right"' in TRACE_UI_HTML
    assert "function beginResize(event)" in TRACE_UI_HTML
    assert "window.addEventListener('pointermove',move)" in TRACE_UI_HTML
    assert "event.key!=='ArrowLeft'&&event.key!=='ArrowRight'" in TRACE_UI_HTML
    assert "main.style.setProperty('--left-pane'" in TRACE_UI_HTML
    assert "main.style.setProperty('--right-pane'" in TRACE_UI_HTML
    assert "localStorage.setItem(paneStorageKey" in TRACE_UI_HTML


def test_right_inspector_output_has_a_bounded_visible_scroller() -> None:
    assert "#inspector{min-width:0;min-height:0" in TRACE_UI_HTML
    assert "flex-direction:column;overflow:hidden" in TRACE_UI_HTML
    assert "#inspectjson{flex:1 1 0;min-height:0" in TRACE_UI_HTML
    assert "overflow-y:scroll" in TRACE_UI_HTML
    assert "scrollbar-gutter:stable" in TRACE_UI_HTML
    assert "#inspectjson::-webkit-scrollbar{width:12px}" in TRACE_UI_HTML


def test_trace_ui_uses_light_theme() -> None:
    assert "color-scheme:light" in TRACE_UI_HTML
    assert "--bg:#f4f7fa" in TRACE_UI_HTML
    assert "background:#ffffff" in TRACE_UI_HTML


def test_new_events_and_clicks_share_the_same_inspector_function() -> None:
    # New SSE events call show() automatically, while clicking a historical
    # card calls the exact same function with the historical event.
    assert "show(ev,card);if(nearBottom)events.scrollTop" in TRACE_UI_HTML
    assert "card.onclick=()=>show(ev,card)" in TRACE_UI_HTML


def test_trace_ui_follows_the_latest_updated_session_by_default() -> None:
    assert 'id="followlatest" type="checkbox" checked' in TRACE_UI_HTML
    assert "followLatest.checked?rows[0].session_id" in TRACE_UI_HTML
    assert "sessions.onchange=()=>{followLatest.checked=false" in TRACE_UI_HTML
    assert "followLatest.onchange=()=>{if(followLatest.checked)refresh()}" in TRACE_UI_HTML
    assert "window.addEventListener('pagehide',()=>source?.close())" in TRACE_UI_HTML


def test_trace_events_are_grouped_by_request_and_actual_llm_turn() -> None:
    assert "turnGroups=new Map()" in TRACE_UI_HTML
    assert "function requestFor(ev)" in TRACE_UI_HTML
    assert "turnGroups.get(ev.turn_id)" in TRACE_UI_HTML
    assert "head.children[0].textContent='Request '+(turnGroups.size+1)" in TRACE_UI_HTML
    assert "if(ev.event==='model_call_start')" in TRACE_UI_HTML
    assert "newPhase(group,'LLM turn '+group.llmCount,ev.agent,when)" in TRACE_UI_HTML
    assert "phase.body.append(card)" in TRACE_UI_HTML


def test_turns_use_agent_lanes_and_time_overlap_rows() -> None:
    assert "className='agenttimeline'" in TRACE_UI_HTML
    assert "function ensureAgent(group,agent)" in TRACE_UI_HTML
    assert "activeByAgent:new Map()" in TRACE_UI_HTML
    assert "group.activeByAgent.get(ev.agent)" in TRACE_UI_HTML
    assert "function layoutTimeline(group)" in TRACE_UI_HTML
    assert "phase.endMs??Number.POSITIVE_INFINITY" in TRACE_UI_HTML
    assert "phase.startMs>=waveEnd" in TRACE_UI_HTML
    assert "phase.root.style.gridColumn" in TRACE_UI_HTML
    assert "phase.root.style.gridRow" in TRACE_UI_HTML
    assert "shortSeconds(finish-phase.startMs)" in TRACE_UI_HTML


def test_keyboard_navigation_selects_scrolls_and_toggles_groups() -> None:
    assert "function move(delta)" in TRACE_UI_HTML
    assert "function keepVisible(card)" in TRACE_UI_HTML
    assert "events.scrollTop+=box.top-viewport.top-pad" in TRACE_UI_HTML
    assert "const nearBottom=events.scrollHeight-events.scrollTop-events.clientHeight<64" in TRACE_UI_HTML
    assert "for(const old of group.phases)old.root.open=false" not in TRACE_UI_HTML
    assert "e.key==='ArrowDown'||e.key==='ArrowUp'" in TRACE_UI_HTML
    assert "e.key!=='ArrowLeft'&&e.key!=='ArrowRight'" in TRACE_UI_HTML
    assert "summary.parentElement.open=e.key==='ArrowRight'" in TRACE_UI_HTML
    assert "inspectJson.scrollBy" in TRACE_UI_HTML
    assert "e.key==='Home'||e.key==='End'" in TRACE_UI_HTML


def test_context_growth_chart_tracks_each_agent_model_call() -> None:
    assert 'id="contextchart"' in TRACE_UI_HTML
    assert 'id="contextlegend"' in TRACE_UI_HTML
    assert "function trackContext(ev,group,phase,card)" in TRACE_UI_HTML
    assert "ev.data?.projected_input_tokens" in TRACE_UI_HTML
    assert "ev.data?.token_usage?.inputTokens" in TRACE_UI_HTML
    assert "other.agent===point.agent" in TRACE_UI_HTML
    assert "requestNumber:group.number,turnNumber:group.llmCount" in TRACE_UI_HTML


def test_context_chart_shows_actual_projection_and_per_agent_delta() -> None:
    assert "point.actual!==null&&point.endEventIndex<=cutoff" in TRACE_UI_HTML
    assert "fill:actual?style.color:'#fff'" in TRACE_UI_HTML
    assert "signed(delta)" in TRACE_UI_HTML
    assert "mark.addEventListener('click',()=>selectCard(point.endCard||point.startCard))" in TRACE_UI_HTML
    assert "new ResizeObserver(()=>renderContextChart()).observe(contextChart)" in TRACE_UI_HTML


def test_context_chart_follows_selected_trace_position_and_names_steps() -> None:
    assert "function chartCutoff(){return selected?.traceIndex" in TRACE_UI_HTML
    assert "point.startEventIndex<=cutoff" in TRACE_UI_HTML
    assert "card.traceIndex=eventCards.length" in TRACE_UI_HTML
    assert "class:'chart-stop'" in TRACE_UI_HTML
    assert "class:'chart-focus-line'" in TRACE_UI_HTML
    assert "ev.event==='tool_call_end'" in TRACE_UI_HTML
    assert "' after '+point.afterSteps.join(', ')" in TRACE_UI_HTML


def test_live_gauges_follow_selected_trace_position_and_preserve_missing_metrics() -> None:
    for name in ("models", "tools", "tokens", "cache", "ttft"):
        assert f'data-gauge="{name}"' in TRACE_UI_HTML
    assert "function renderGauges()" in TRACE_UI_HTML
    assert "function trackGauge(ev,card)" in TRACE_UI_HTML
    assert "card.gaugeSnapshot={...state}" in TRACE_UI_HTML
    assert "state.modelStarts-state.modelEnds" in TRACE_UI_HTML
    assert "state.toolStarts-state.toolEnds" in TRACE_UI_HTML
    assert "state.cacheReported?state.cacheRead.toLocaleString():'not reported'" in TRACE_UI_HTML
    assert "setInterval(renderGauges,250)" in TRACE_UI_HTML
