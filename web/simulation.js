const simulationData=fetch('/api/simulation').then(r=>{if(!r.ok)throw new Error('Consumer profiles are unavailable. Please retry.');return r.json();});
const el=id=>document.getElementById(id);let data,segment=null,sharedHeadroom=null;
const mode = () => el('comparison-mode').value;
const permissionKeys = ['context','behavior','history','location'];
const traits=['Privacy concern','Relevance preference','Tracking awareness','Personalization preference'];
traits.forEach((name,i)=>{const label=document.createElement('label');label.className='field-label';label.textContent=name+' (1–7)';label.htmlFor='trait'+i;const input=document.createElement('input');Object.assign(input,{id:'trait'+i,type:'number',min:1,max:7,value:4});el('traits').append(label,input);});
permissionKeys.forEach(key=>{const label=document.createElement('label');label.className='field-label';label.htmlFor='permission-'+key;if(key==='location') label.dataset.locationPermission='';label.textContent=key+' data: possessed and permitted';const select=document.createElement('select');select.id='permission-'+key;if(key==='location') select.dataset.locationPermission='';[['unknown','Unknown — review'],['yes','Yes, confirmed'],['no','No']].forEach(([v,t])=>select.add(new Option(t,v)));el('permissions').append(label,select);});
for(let i=0;i<5;i++){const l=document.createElement('label');l.className='field-label';l.htmlFor='cost'+i;l.textContent='L'+i+' incremental implementation cost';const v=document.createElement('input');Object.assign(v,{id:'cost'+i,type:'number',min:0,placeholder:'Unknown'});if(i===0)v.value=0;el('costs').append(l,v);}
const readNumber=id=>el(id).value.trim()===''?null:Number(el(id).value);
try{const c=JSON.parse(sessionStorage.getItem('49c-campaign')||'null');if(c&&c.total_budget!==undefined&&String(c.total_budget).trim()!==''&&c.committed_spend!==undefined&&String(c.committed_spend).trim()!==''){sharedHeadroom=Math.max(0,c.total_budget-c.committed_spend);el('headroom').value=sharedHeadroom;}}catch{}
function applyProfilePreset() {
  const value = el('profile-preset').value;
  segment = value.startsWith('segment:') ? value.slice(8) : null;
  const profile = segment ? data.segments.find(s => s.name === segment).profile
    : value === 'sensitive' ? [7, 4, 6, 2]
    : value === 'open' ? [2, 7, 3, 6] : [4, 4, 4, 4];
  profile.forEach((rating, index) => {
    const input = el('trait' + index);
    input.value = rating;
    input.disabled = Boolean(segment);
  });
}

let comparisonVersion = 0;
function resetComparison(message) {
  comparisonVersion += 1;
  el('sim-recommendation').textContent = message;
  el('sim-levels').replaceChildren();
  el('sim-error').textContent = '';
}

function onComparisonInputChange() {
  resetComparison('Inputs changed. Run Compare L0–L4 again.');
}

document.querySelectorAll('.input-panel input').forEach(input => {
  input.addEventListener('input', onComparisonInputChange);
});
el('permissions').addEventListener('change', onComparisonInputChange);

function renderComparison(result) {
  const rows = result.levels.map(level => {
    const row = document.createElement('tr');
    const name = document.createElement('td');
    name.textContent = level.level + ' · ' + level.name;
    name.title = 'Required data: ' + level.source;
    row.append(name);

    const discomfort = document.createElement('td');
    discomfort.textContent = level.discomfort.toFixed(2);
    const bar = document.createElement('meter');
    bar.min = 1;
    bar.max = 7;
    bar.value = level.discomfort;
    bar.setAttribute('aria-label', level.level + ' discomfort');
    discomfort.append(document.createElement('br'), bar);

    const relevance = document.createElement('td');
    relevance.textContent = level.relevance.toFixed(2);
    const status = document.createElement('td');
    status.textContent = level.eligible ? 'Eligible · cost ' + level.cost : 'Review required';
    if (!level.eligible) {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = 'Requirements';
      const explanation = document.createElement('p');
      explanation.textContent = level.source + ' — ' + level.reasons.join('; ');
      details.append(summary, explanation);
      status.append(details);
    }
    row.append(discomfort, relevance);
    if (mode() === 'empirical') {
      const percent = value => (value * 100).toFixed(1) + '%';
      discomfort.textContent += ' (family medians ' + level.rating_range.discomfort_score.join('–') + ')';
      relevance.textContent += ' (family medians ' + level.rating_range.relevance_score.join('–') + ')';
      const detail = document.createElement('td');
      detail.textContent = level.intrusion.toFixed(2) + '/7 · ' + percent(level.high_intrusion_rate)
        + ' high (family range ' + level.high_intrusion_range.map(percent).join('–') + ') · n=' + level.n;
      row.append(detail);
    }
    row.append(status);
    return row;
  });

  const label = mode() === 'empirical' ? 'Exploratory recommendation: ' : 'Demonstration choice: ';
  const choice = result.recommended_level ? label + result.recommended_level + '. ' : 'No recommendation. ';
  el('sim-recommendation').textContent = choice + result.reason;
  el('sim-levels').replaceChildren(...rows);
}

el('compare').onclick = async () => {
  resetComparison('Comparing personalization levels…');
  const version = comparisonVersion;
  try {
    const response = await fetch('/api/simulation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        mode: mode(),
        ...(mode() === 'synthetic' ? {profile: traits.map((_, index) => readNumber('trait' + index))} : {}),
        comparable_survey_scenario: el('scenario-scope').checked,
        max_high_intrusion_risk: readNumber('risk-ceiling') === null ? null : readNumber('risk-ceiling') / 100,
        segment,
        threshold: readNumber('ceiling'),
        minimum_relevance: readNumber('minimum'),
        headroom: readNumber('headroom'),
        costs: [0, 1, 2, 3, 4].map(index => readNumber('cost' + index)),
        permissions: Object.fromEntries(permissionKeys.map(key => [key, el('permission-' + key).value])),
      }),
    });
    const result = await response.json();
    // Inputs may have changed or another comparison may have started while this request was pending.
    if (version !== comparisonVersion) return;
    if (!response.ok) throw new Error(result.error);
    renderComparison(result);
  } catch (error) {
    if (version !== comparisonVersion) return;
    el('sim-recommendation').textContent = 'Run Compare L0–L4 to retry.';
    el('sim-error').textContent = error.message;
  }
};

simulationData.then(d => {
  data = d;
  d.segments.forEach(s => el('profile-preset').add(new Option(s.name.replaceAll('_', ' ') + ' · ' + s.consumers + ' fictional consumers', 'segment:' + s.name)));
  const saved = JSON.parse(sessionStorage.getItem('49c-simulation') || '{}');
  if (saved['profile-preset']) {
    el('profile-preset').value = saved['profile-preset'];
    applyProfilePreset();
  }
  for (const [id, value] of Object.entries(saved)) {
    if (id !== 'comparison-mode' && id !== 'scenario-scope' && el(id) && !(id === 'headroom' && sharedHeadroom !== null)) el(id).value = value;
  }
  el('sim-metrics').textContent = 'Synthetic held-out discomfort MAE: ' + d.metrics.discomfort.mae.toFixed(3) +
    '; baseline: ' + d.metrics.discomfort.baseline_mae.toFixed(3) + '\nSynthetic held-out relevance MAE: ' + d.metrics.relevance.mae.toFixed(3);
  buildSegmentCards(d);
  refreshProfileView();
  updateMode();
  el('compare').click();
});

simulationData.then(d=>{for(const [key,title] of [['genz','Gen Z · relevance × privacy concern, n=296'],['romano_han','Romano–Han · perceived benefits × privacy concern, n=837']]){const source=d.real_profiles[key];if(!source)continue;const h=document.createElement('h4');h.textContent=title;el('real-profiles').append(h);for(const [name,count] of Object.entries(source.counts)){const p=document.createElement('p');const ci=source.respondent_bootstrap_95pct_share_intervals[name];p.textContent=name.replaceAll('_',' ')+' · '+count+' respondents · 95% share interval '+(ci[0]*100).toFixed(1)+'–'+(ci[1]*100).toFixed(1)+'%';el('real-profiles').append(p);}}});
window.addEventListener('pagehide',()=>{const values={};document.querySelectorAll('input,select').forEach(n=>values[n.id]=n.value);sessionStorage.setItem('49c-simulation',JSON.stringify(values));});

el('profile-preset').onchange = () => {
  applyProfilePreset();
  refreshProfileView();
  el('compare').click();
};
const segmentLabels={privacy_relaxed__relevance_neutral:'Lower concern · lower relevance',privacy_relaxed__relevance_seeking:'Lower concern · higher relevance',privacy_sensitive__relevance_neutral:'Higher concern · lower relevance',privacy_sensitive__relevance_seeking:'Higher concern · higher relevance'};
function buildSegmentCards(d){el('segment-cards').replaceChildren();d.segments.forEach(s=>{const button=document.createElement('button');button.type='button';button.className='segment-card';button.dataset.segment=s.name;button.setAttribute('aria-pressed','false');const title=document.createElement('strong');title.textContent=segmentLabels[s.name]||s.name;const count=document.createElement('span');count.textContent=s.consumers+' fictional consumers · '+(100*s.consumers/300).toFixed(1)+'%';const description=document.createElement('small');description.textContent='Privacy '+s.profile[0].toFixed(1)+'/7 · relevance preference '+s.profile[1].toFixed(1)+'/7';button.append(title,count,description);button.onclick=()=>{el('profile-preset').value='segment:'+s.name;el('profile-preset').onchange();};el('segment-cards').append(button);});}
function refreshProfileView(){el('traits').hidden=!!segment;el('segment-summary').textContent=segment?segmentLabels[segment]+'. Estimates average this fictional segment; they do not identify real customers.':'Adjust this fictional individual’s ratings, or select a segment above.';document.querySelectorAll('.segment-card').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.segment===segment)));}
simulationData.catch(e=>{el('sim-error').textContent=e.message;});

function updateMode() {
  const synthetic = mode() === 'synthetic';
  for (const id of ['synthetic-profile','synthetic-segments','synthetic-method']) el(id).hidden = !synthetic;
  for (const id of ['empirical-criteria','empirical-column']) el(id).hidden = synthetic;
  document.querySelectorAll('[data-location-permission]').forEach(node => { node.hidden = synthetic; });
  el('evidence-label').textContent = synthetic ? 'Synthetic data' : 'Primary survey estimate';
  el('range-note').textContent = synthetic ? 'Fictional simulation; individual responses remain unvalidated.'
    : 'Family ranges describe observed variation across two families per level.';
}
el('comparison-mode').addEventListener('change', () => {
  updateMode();
  el('compare').click();
});
