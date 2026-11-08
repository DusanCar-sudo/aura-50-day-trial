// Run with: NODE_PATH=/path/to/node_modules node --test tests/dashboard.test.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
const root = path.join(__dirname, '..');
const page = fs.readFileSync(path.join(root,'index.html'),'utf8');
const sample = {questions:[
  {id:'q1',tier:1,question:'Correct question <img src=x onerror=alert(1)>',answer:'First answer <script>alert(1)</script>',score:{verdict:'correct',hits:['matched'],missed:[]},elapsed_seconds:1.5},
  {id:'q2',tier:2,question:'Failed question',answer:'Second answer',score:{verdict:'incorrect',missed:['needed']}},
  {id:'q3',tier:1,question:'Partial question',answer:'Third answer',score:{verdict:'partial'}},
  {id:'q4',tier:3,question:'Ungraded question',answer:''}
]};
async function boot(route='/',fetcher) {
  const errors=[], requests=[];let copied='';
  const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e));
  const dom=new JSDOM(page,{url:'https://example.test/aura-50-day-trial'+route,runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){
    w.matchMedia=()=>({matches:false});w.HTMLElement.prototype.scrollIntoView=()=>{};
    w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;};
    w.navigator.clipboard={writeText:async value=>{copied=value;}};
    w.fetch=async url=>{requests.push(url);return fetcher?fetcher(url):{ok:true,json:async()=>structuredClone(sample)};};
  }});
  await new Promise(r=>setTimeout(r,30));
  const w=dom.window,d=w.document;
  const choose=(id,value,type='change')=>{d.getElementById(id).value=value;d.getElementById(id).dispatchEvent(new w.Event(type,{bubbles:true}));};
  return {dom,w,d,errors,requests,choose,copied:()=>copied};
}
test('all served locations resolve original files and initialize without errors',async()=>{
  for(const route of ['/','/dashboard.html','/dashboard/','/dashboard/index.html']) {
    const h=await boot(route);
    assert.equal(h.errors.length,0,h.errors.map(String).join('\n'));
    assert.equal(h.d.querySelectorAll('.run-card').length,12);
    assert.match(h.requests[0],/^https:\/\/example.test\/aura-50-day-trial\/results\/session_[^/]+\.json$/);
    assert.equal(h.d.querySelectorAll('.question-row').length,4);
    assert.equal(h.d.querySelector('.prompt img'),null);
    assert.match(h.d.querySelector('.answer-excerpt').textContent,/<script>/);
    h.dom.window.close();
  }
});
test('filters, next/previous, transcript, clipboard and share links work',async()=>{
  const h=await boot();
  h.choose('verdictFilter','incorrect');assert.equal(h.d.querySelectorAll('.question-row').length,1);assert.match(h.d.querySelector('.prompt').textContent,/Failed/);
  h.choose('verdictFilter','ungraded');assert.match(h.d.querySelector('.prompt').textContent,/Ungraded/);assert.equal(h.d.getElementById('openTranscript').disabled,true);
  h.choose('verdictFilter','all');h.choose('tierFilter','1');assert.equal(h.d.querySelectorAll('.question-row').length,2);
  h.d.getElementById('nextQuestion').click();assert.match(h.d.querySelector('.prompt').textContent,/Partial/);
  h.d.getElementById('prevQuestion').click();assert.match(h.d.querySelector('.prompt').textContent,/Correct/);
  h.d.getElementById('openTranscript').click();assert.equal(h.d.getElementById('transcriptDialog').open,true);assert.match(h.d.getElementById('transcriptText').textContent,/First answer/);
  h.d.getElementById('copyAnswer').click();await new Promise(r=>setTimeout(r,10));assert.match(h.copied(),/First answer/);
  h.d.getElementById('shareRun').click();await new Promise(r=>setTimeout(r,10));assert.match(h.copied(),/question=q1/);
  h.choose('questionSearch','not present','input');assert.equal(h.d.querySelectorAll('.question-row').length,0);assert.match(h.d.getElementById('questionList').textContent,/No questions match/);
  assert.equal(h.errors.length,0);h.dom.window.close();
});
test('run search, scope, pagination and bounded comparison',async()=>{
  const h=await boot();
  h.d.getElementById('moreRuns').click();assert.equal(h.d.querySelectorAll('.run-card').length,24);
  h.choose('runSearch','no-such-run','input');assert.equal(h.d.querySelectorAll('.run-card').length,0);
  h.d.getElementById('resetRuns').click();assert.equal(h.d.querySelectorAll('.run-card').length,12);
  h.choose('runScope','full');assert.equal(h.d.querySelectorAll('.run-card').length,7);
  const pins=[...h.d.querySelectorAll('[data-pin]')].map(x=>x.dataset.pin);
  h.d.querySelector(`[data-pin="${pins[0]}"]`).click();assert.equal(h.d.getElementById('comparison').hidden,false);
  h.d.querySelector(`[data-pin="${pins[1]}"]`).click();assert.equal(h.d.querySelectorAll('#compareContent tbody tr').length,12);
  h.d.querySelector(`[data-pin="${pins[2]}"]`).click();assert.equal(h.d.querySelectorAll('.pin-run[aria-pressed=true]').length,2);
  h.d.getElementById('clearCompare').click();assert.equal(h.d.getElementById('comparison').hidden,true);
  assert.equal(h.errors.length,0);h.dom.window.close();
});
test('deep link restores run, question and comparison',async()=>{
  const h=await boot('/?run=223&question=q2&compare=223,11027');
  assert.match(h.d.querySelector('.detail-top h2').textContent,/223/);
  assert.match(h.d.querySelector('.prompt').textContent,/Failed/);
  assert.equal(h.d.querySelectorAll('#compareContent tbody tr').length,12);
  assert.match(h.requests[0],/session_223.json$/);h.dom.window.close();
});
test('failed fetch retries and a stale response cannot replace a newer selection',async()=>{
  let count=0;
  const h=await boot('/',async()=>{count++;return count===1?{ok:false}:{ok:true,json:async()=>sample};});
  assert.ok(h.d.getElementById('retryPreview'));
  h.d.getElementById('retryPreview').click();await new Promise(r=>setTimeout(r,10));assert.equal(h.d.querySelectorAll('.question-row').length,4);h.dom.window.close();
  const pending=[];
  const race=await boot('/',url=>new Promise(resolve=>pending.push({url,resolve})));
  const second=race.d.querySelectorAll('[data-run]')[1];const secondId=second.dataset.run;second.click();
  pending[1].resolve({ok:true,json:async()=>({questions:[{id:'new',question:'Newer selection',answer:'current'}]})});
  await new Promise(r=>setTimeout(r,10));
  pending[0].resolve({ok:true,json:async()=>sample});await new Promise(r=>setTimeout(r,10));
  assert.match(race.d.querySelector('.detail-top h2').textContent,new RegExp(secondId));
  assert.equal(race.d.querySelector('.prompt').textContent,'Newer selection');
  assert.equal(race.errors.length,0);race.dom.window.close();
});
test('real archived transcript and file mapping work',async()=>{
  const h=await boot('/?run=11027',async url=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(root,'results',path.basename(url)),'utf8'))}));
  assert.ok(h.d.querySelectorAll('.question-row').length>0);
  assert.ok(h.d.querySelector('.answer-excerpt').textContent.length>100);
  assert.equal(h.errors.length,0);h.dom.window.close();
});
