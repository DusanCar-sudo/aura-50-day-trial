/* Run notebook: summaries stay embedded; original transcripts load on demand. */
(() => {
  const runs = [...DATA.sessions].sort((a,b) => (b.date || '').localeCompare(a.date || '') || b.id-a.id);
  const byId = new Map(runs.map(s => [s.id,s]));
  const cache = new Map();
  const state = {active:null, pinned:[], limit:12, questions:[], filtered:[], question:null, request:0};
  const base = new URL(/\/dashboard\/(?:index\.html)?$/.test(location.pathname) ? '../' : './', location.href);
  const sourceURL = s => new URL('results/' + encodeURIComponent(s.source || `session_${s.id}.json`), base).href;
  const scope = s => s.interrupted ? 'Interrupted' : s.full ? 'Full run' : 'Sample / slice';
  const model = s => s.arch && s.arch !== 'unknown' ? `${s.arch} → ${s.model}` : s.model;
  const verdict = q => ['correct','partial','incorrect'].includes(q.verdict) ? q.verdict : ['correct','partial','incorrect'].includes(q.score?.verdict) ? q.score.verdict : 'ungraded';
  const clean = value => String(value || '').replace(/\x1b\[[0-?]*[ -/]*[@-~]/g,'').replace(/\r\n?/g,'\n');
  const text = value => typeof value === 'string' ? value : value == null ? '' : JSON.stringify(value,null,2);
  const label = (s,v) => `<span class="scope-badge ${s.full?'full':''}">${esc(v || scope(s))}</span>`;
  let noticeTimer;
  function notify(message) { $('notice').textContent=message; $('notice').classList.add('visible'); clearTimeout(noticeTimer); noticeTimer=setTimeout(()=>$('notice').classList.remove('visible'),3500); }
  const scrollBehavior = () => matchMedia('(prefers-reduced-motion:reduce)').matches ? 'auto' : 'smooth';
  function updateURL() {
    const url=new URL(location.href); url.searchParams.set('run',state.active);
    if(state.pinned.length) url.searchParams.set('compare',state.pinned.join(',')); else url.searchParams.delete('compare');
    if(state.question != null) url.searchParams.set('question',state.questions[state.question]?.id || state.question); else url.searchParams.delete('question');
    history.replaceState(null,'',url);
  }
  function fingerprint(s) {
    const bands=Array.from({length:12},(_,i)=>{
      const ts=Object.entries(s.tiers).filter(([t])=>+t>=i*5+1 && +t<=(i+1)*5).map(([,v])=>v);
      const n=ts.reduce((a,t)=>a+t.n,0), c=ts.reduce((a,t)=>a+t.c,0);
      return `<i title="Tiers ${i*5+1}–${(i+1)*5}: ${n?pct(c/n):'not tested'}" style="${n?`background:var(--acc);opacity:${.18+.82*c/n}`:''}"></i>`;
    });
    return `<span class="fingerprint" aria-label="Tier coverage, grouped in bands of five">${bands.join('')}</span>`;
  }
  function renderOverview() {
    const best=DATA.kpi.bestId ? byId.get(DATA.kpi.bestId) : null;
    const items=[['Best full run',best?pct(best.rate):'—',best?`S${best.id} · ${best.correct}/${best.n} correct`:'No full run recorded'],['Recorded runs',fmt(runs.length),`${DATA.fullRuns.length} full · ${runs.length-DATA.fullRuns.length} sample / slice`],['Questions graded',fmt(DATA.kpi.graded || 0),'Across the recorded archive'],['Tier coverage',String(DATA.maxTier),'From foundations to advanced tasks']];
    $('overview').innerHTML=items.map(([title,value,note])=>`<div class="overview-item"><span>${title}</span><strong>${value}</strong><small>${esc(note)}</small></div>`).join('');
    $('archiveStamp').textContent=`Latest recorded run · ${runs[0]?.date || 'undated'}`;
  }
  function renderCards() {
    const query=$('runSearch').value.trim().toLowerCase(), mode=$('runScope').value, sort=$('runSort').value;
    const filtered=runs.filter(s=>(!query || `s${s.id} ${s.date} ${model(s)}`.toLowerCase().includes(query)) && (mode==='all' || (mode==='full' && s.full) || (mode==='slice' && !s.full && !s.interrupted) || (mode==='interrupted' && s.interrupted)));
    if(sort==='oldest')filtered.reverse();
    if(sort==='rate')filtered.sort((a,b)=>b.rate-a.rate || b.n-a.n);
    if(sort==='size')filtered.sort((a,b)=>b.n-a.n || b.id-a.id);
    $('runCount').textContent=`${filtered.length} of ${runs.length} runs`;
    $('runCards').innerHTML=filtered.slice(0,state.limit).map(s=>`<article class="run-card ${s.id===state.active?'active':''}">
      <button class="run-open" data-run="${s.id}" aria-pressed="${s.id===state.active}" aria-label="Preview run S${s.id}"><span class="run-card-top"><span class="run-id">S${s.id}</span><span class="run-rate">${pct(s.rate)}</span></span><span class="run-model">${esc(model(s))}</span><span class="run-meta">${esc(s.date || 'Undated')} · ${s.n} questions · ${s.correct} correct</span>${fingerprint(s)}<span class="run-quote">${esc(s.preview || 'Open the recorded questions and answers.')}</span></button>
      <div class="run-card-bottom">${label(s)}<button class="pin-run" data-pin="${s.id}" aria-pressed="${state.pinned.includes(s.id)}" aria-label="${state.pinned.includes(s.id)?'Unpin':'Compare'} run S${s.id}">${state.pinned.includes(s.id)?'✓ Pinned':'＋ Compare'}</button></div></article>`).join('') || '<div class="empty">No runs match these filters. Try a model name or reset the filters.</div>';
    $('moreRuns').hidden=filtered.length<=state.limit;
    $('moreRuns').textContent=`Show ${Math.min(12,Math.max(0,filtered.length-state.limit))} more runs`;
  }
  function detailHeader(s) {
    return `<div class="detail-header"><div class="detail-top"><div><p class="eyebrow">RUN PREVIEW / ${esc(s.date || 'UNDATED')}</p><h2>Session ${s.id} ${label(s)}</h2><p class="detail-model">${esc(model(s))}</p></div><div class="detail-actions"><button class="action" id="shareRun">Copy link ↗</button><a class="action quiet" href="${esc(sourceURL(s))}" target="_blank" rel="noopener">Source JSON ↗</a></div></div><div class="detail-metrics"><div><strong>${pct(s.rate)}</strong><span>Strict pass rate</span></div><div><strong class="correct">${s.correct}</strong><span>Correct</span></div><div><strong class="partial">${s.partial}</strong><span>Partial</span></div><div><strong class="incorrect">${s.incorrect}</strong><span>Incorrect*</span></div></div><div class="verdict-strip" aria-label="${s.correct} correct, ${s.partial} partial, ${s.incorrect} incorrect"><i style="width:${100*s.correct/s.n}%;background:var(--good)"></i><i style="width:${100*s.partial/s.n}%;background:var(--warn)"></i><i style="width:${100*s.incorrect/s.n}%;background:var(--bad)"></i></div><p class="detail-note">${s.n} recorded questions · ${pct(s.weighted)} weighted (partial = ½). *Archive totals count missing verdicts as incorrect; previews label them ungraded.</p></div>`;
  }
  async function getRun(s) {
    if(cache.has(s.id)) return cache.get(s.id);
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),30000);
    try {
      const response=await fetch(sourceURL(s),{signal:controller.signal});
      if(!response.ok)throw new Error('Could not load the recorded run');
      const payload=await response.json();
      if(!Array.isArray(payload.questions))throw new Error('No questions in the recorded file');
      cache.set(s.id,payload);return payload;
    } finally {clearTimeout(timer);}
  }
  async function selectRun(id, scroll=false, requestedQuestion=null) {
    const s=byId.get(Number(id)); if(!s)return;
    const request=++state.request; state.active=s.id;state.question=null;state.questions=[];
    renderCards();updateURL();
    $('runDetail').innerHTML=detailHeader(s)+'<div id="questionContent" class="loading" role="status">Loading recorded questions and answers…</div>';
    $('shareRun').onclick=share;
    if(scroll && matchMedia('(max-width:760px)').matches)$('runDetail').scrollIntoView({behavior:scrollBehavior(),block:'start'});
    try {
      const payload=await getRun(s);if(request!==state.request)return;
      state.questions=payload.questions;
      $('questionContent').className='';
      $('questionContent').innerHTML=`<div class="question-tools"><label>Search questions<input type="search" id="questionSearch" placeholder="Question text or ID…"></label><label>Verdict<select id="verdictFilter"><option value="all">All verdicts</option><option value="correct">Correct</option><option value="partial">Partial</option><option value="incorrect">Incorrect</option><option value="ungraded">Ungraded</option></select></label><label>Tier<select id="tierFilter"><option value="all">All tiers</option>${[...new Set(state.questions.map(q=>Number(q.tier)||0))].sort((a,b)=>a-b).map(t=>`<option value="${t}">Tier ${t}</option>`).join('')}</select></label></div><div class="question-count" id="questionCount" role="status"></div><div class="question-list" id="questionList"></div><div class="question-nav" id="questionNav"></div><div id="answerPreview"></div>`;
      $('questionSearch').oninput=filterQuestions;$('verdictFilter').onchange=filterQuestions;$('tierFilter').onchange=filterQuestions;
      const index=state.questions.findIndex(q=>String(q.id)===String(requestedQuestion));
      state.question=index>=0?index:null;filterQuestions();
    } catch(error) {
      if(request!==state.request)return;
      $('questionContent').innerHTML='<p>Preview unavailable. The recorded file could not be loaded.</p><button class="action" id="retryPreview">Retry preview</button>';
      $('retryPreview').onclick=()=>selectRun(s.id);
    }
  }
  function filterQuestions() {
    const search=$('questionSearch').value.trim().toLowerCase(), v=$('verdictFilter').value, tier=$('tierFilter').value;
    state.filtered=state.questions.map((q,index)=>({q,index})).filter(({q})=>(v==='all' || verdict(q)===v) && (tier==='all' || Number(q.tier)===Number(tier)) && (!search || `${q.id} ${q.question || q.prompt || ''}`.toLowerCase().includes(search)));
    if(!state.filtered.some(row=>row.index===state.question))state.question=state.filtered[0]?.index ?? null;
    renderQuestions();
  }
  function renderQuestions() {
    const focused = document.activeElement;
    const focusId = focused?.id;
    const focusQuestion = focused?.hasAttribute('data-question');
    $('questionCount').textContent=`${state.filtered.length} of ${state.questions.length} questions · select an answer to inspect`;
    $('questionList').innerHTML=state.filtered.map(({q,index})=>`<button class="question-row" data-question="${index}" aria-pressed="${index===state.question}"><small>${esc(q.id || `Q${index+1}`)}<br>Tier ${esc(q.tier ?? '—')}</small><span class="question-title">${esc(q.question || q.prompt || 'No question text recorded')}</span><span class="verdict ${verdict(q)}">${verdict(q)}</span></button>`).join('') || '<div class="empty">No questions match. Change the search, verdict, or tier filter.</div>';
    $('questionList').onclick=e=>{const row=e.target.closest('[data-question]');if(row){state.question=Number(row.dataset.question);renderQuestions();}};
    const pos=state.filtered.findIndex(row=>row.index===state.question);
    $('questionNav').innerHTML=pos<0?'':`<button class="action quiet" id="prevQuestion" ${pos===0?'disabled':''}>← Previous</button><span>${pos+1} / ${state.filtered.length}</span><button class="action quiet" id="nextQuestion" ${pos===state.filtered.length-1?'disabled':''}>Next →</button>`;
    if(pos>=0) {
      $('prevQuestion').onclick=()=>stepQuestion(-1);$('nextQuestion').onclick=()=>stepQuestion(1);
    }
    renderAnswer();updateURL();
    if (focusQuestion) $('questionList').querySelector('[aria-pressed=true]')?.focus({preventScroll:true});
    else if (focusId && ['prevQuestion','nextQuestion'].includes(focusId)) {
      const target=$(focusId);
      (target.disabled ? $(focusId==='nextQuestion'?'prevQuestion':'nextQuestion') : target)?.focus({preventScroll:true});
    }
  }
  function stepQuestion(direction) {
    const pos=state.filtered.findIndex(row=>row.index===state.question), next=state.filtered[pos+direction];
    if(next){state.question=next.index;renderQuestions();$('questionList').querySelector('[aria-pressed=true]')?.scrollIntoView({block:'nearest'});}
  }
  function renderAnswer() {
    const q=state.questions[state.question];if(!q){$('answerPreview').innerHTML='';return;}
    const output=clean(text(q.answer)), score=q.score && typeof q.score==='object'?q.score:{};
    const hits=Array.isArray(score.hits)?score.hits:[], missed=Array.isArray(score.missed)?score.missed:[];
    $('answerPreview').innerHTML=`<article class="answer-preview"><div class="answer-heading"><h3>${esc(q.id || 'Question')} <span class="${verdict(q)}">· ${verdict(q)}</span></h3><span class="helper">${Number.isFinite(q.elapsed_seconds)?`${q.elapsed_seconds.toFixed(1)}s elapsed`:''}</span></div><p class="prompt"></p><div class="score-notes">${hits.length?`Matched: ${esc(hits.join(' · '))}<br>`:''}${missed.length?`Missed: ${esc(missed.join(' · '))}<br>`:''}${score.note?esc(text(score.note)):''}</div><p class="eyebrow" style="margin-top:20px">TRANSCRIPT PREVIEW · FIRST 1,800 CHARACTERS</p><pre class="answer-excerpt"></pre><div class="answer-footer"><button class="action primary" id="openTranscript" ${!output && !q.stderr?'disabled':''}>Read full transcript ↗</button><button class="action quiet" id="copyAnswer" ${!output?'disabled':''}>Copy answer</button></div></article>`;
    $('answerPreview').querySelector('.prompt').textContent=q.question || q.prompt || 'No question text recorded.';
    $('answerPreview').querySelector('.answer-excerpt').textContent=output?output.slice(0,1800)+(output.length>1800?'\n\n… Continue in the full transcript.':''):'No answer output was recorded for this question.';
    $('openTranscript').onclick=()=>{
      $('transcriptTitle').textContent=`S${state.active} / ${q.id || 'Question'} · ${verdict(q)}`;
      $('transcriptText').textContent=output+(q.stderr?'\n\n── Recorded stderr ──\n'+clean(text(q.stderr)):'');
      $('transcriptText').scrollTop=0;$('transcriptDialog').showModal();
    };
    $('copyAnswer').onclick=()=>copy(output,'Answer copied.');
  }
  async function copy(value,message) {
    try{await navigator.clipboard.writeText(value);notify(message);}catch{notify('Clipboard unavailable. You can select and copy the text directly.');}
  }
  function share(){updateURL();copy(location.href,'Link copied to this run and question.');}
  function pin(id) {
    id=Number(id);if(!byId.has(id))return;
    if(state.pinned.includes(id))state.pinned=state.pinned.filter(v=>v!==id);
    else if(state.pinned.length===2){notify('Two runs are pinned. Unpin one to choose another.');return;}
    else state.pinned.push(id);
    renderCards();renderComparison();updateURL();
    $('runCards').querySelector(`[data-pin="${id}"]`)?.focus({preventScroll:true});
    if(state.pinned.length===2)$('comparison').scrollIntoView({behavior:scrollBehavior(),block:'start'});
  }
  function renderComparison() {
    $('comparison').hidden=!state.pinned.length;
    const [a,b]=state.pinned.map(id=>byId.get(id));
    if(!a)return;
    if(!b){$('compareContent').innerHTML=`<p class="compare-empty">S${a.id} is pinned. Choose “＋ Compare” on one more run to see scores and tier differences side by side.</p>`;return;}
    const delta=(b.rate-a.rate)*100;
    $('compareContent').innerHTML=`<div class="compare-summary">${[a,b].map(s=>`<div class="compare-stat"><span>S${s.id} · ${scope(s)}</span><strong>${pct(s.rate)}</strong><span>${s.correct} / ${s.n} correct · ${esc(s.date || 'undated')}</span><p>${esc(model(s))}</p></div>`).join('')}<div class="compare-stat"><span>S${b.id} minus S${a.id}</span><strong>${delta>=0?'+':''}${delta.toFixed(1)} pp</strong><span>Difference in strict pass rate</span></div></div><p class="detail-note">Recorded scores; question sets and run sizes may differ. Tier rates below use the questions tested in each run, not a matched-question evaluation.</p><div class="table-wrap"><table><thead><tr><th scope="col">Tier band</th><th scope="col">S${a.id}</th><th scope="col">S${b.id}</th><th scope="col">Difference</th></tr></thead><tbody>${Array.from({length:12},(_,band)=>{
      const summaries=[a,b].map(s=>Object.entries(s.tiers).filter(([t])=>+t>=band*5+1 && +t<=(band+1)*5).reduce((acc,[,t])=>({n:acc.n+t.n,c:acc.c+t.c}),{n:0,c:0}));
      const [x,y]=summaries,d=x.n&&y.n?(y.c/y.n-x.c/x.n)*100:null;
      return `<tr><td>Tiers ${band*5+1}–${(band+1)*5}</td>${summaries.map(t=>`<td>${t.n?`<span class="delta-bar"><i style="width:${t.c/t.n*100}%"></i></span>${pct(t.c/t.n)} <span class="helper">(${t.c}/${t.n})</span>`:'Not tested'}</td>`).join('')}<td>${d===null?'—':`${d>=0?'+':''}${d.toFixed(1)} pp`}</td></tr>`;
    }).join('')}</tbody></table></div>`;
  }
  $('runCards').onclick=e=>{const preview=e.target.closest('[data-run]'), pinned=e.target.closest('[data-pin]');if(preview)selectRun(preview.dataset.run,true);if(pinned)pin(pinned.dataset.pin);};
  ['runSearch','runScope','runSort'].forEach(id=>$(id).addEventListener(id==='runSearch'?'input':'change',()=>{state.limit=12;renderCards();}));
  $('resetRuns').onclick=()=>{$('runSearch').value='';$('runScope').value='all';$('runSort').value='newest';state.limit=12;renderCards();};
  $('moreRuns').onclick=()=>{state.limit+=12;renderCards();};
  $('clearCompare').onclick=()=>{state.pinned=[];renderCards();renderComparison();updateURL();};
  $('transcriptDialog').addEventListener('click',event=>{if(event.target===$('transcriptDialog')){const r=event.target.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)event.target.close();}});
  const params=new URLSearchParams(location.search);
  state.pinned=[...new Set((params.get('compare') || '').split(',').map(Number).filter(id=>byId.has(id)))].slice(0,2);
  renderOverview();renderCards();renderComparison();
  const initial=byId.has(Number(params.get('run')))?Number(params.get('run')):runs[0]?.id;
  if(initial!=null)selectRun(initial,false,params.get('question'));
})();
