let eventSource = null;
let logBuffer = [];
let diskSeconds = null;
let ramSeconds = null;
let endedGracefully = false;
let bmSource = null;
let bmPassTimes = [];

function qs(id){ return document.getElementById(id); }
function setStatus(state, text){
  const dot = qs('statusDot');
  const label = qs('statusLabel');
  dot.className = 'dot ' + (state === 'ok' ? 'ok' : state === 'warn' ? 'warn' : 'err');
  label.textContent = text;
}
function parseNumber(str){
  if(!str) return null; const n = parseFloat(String(str).replace(',', '.'));
  return Number.isFinite(n) ? n : null;
}
function appendLine(text){
  const el = document.createElement('div'); el.className = 'line'; el.textContent = text;
  const lower = text.toLowerCase();
  if(text.startsWith('---')) el.classList.add('section');
  else if(text.includes('✅')) el.classList.add('ok');
  else if(lower.includes('error')) el.classList.add('err');
  else if(lower.includes('limpiando')) el.classList.add('muted');
  qs('console').appendChild(el);
  if(qs('autoScroll').checked){ qs('console').scrollTop = qs('console').scrollHeight; }
}
function clearUI(){
  qs('console').innerHTML = ''; qs('diskTime').textContent = '—'; qs('ramTime').textContent = '—'; qs('speedup').textContent = '—';
  diskSeconds = null; ramSeconds = null; renderChart();
}
function parseMetrics(line){
  const mDisk = line.match(/Tiempo total desde DISCO:\\s*([\\d.,]+)\\s*segundos/i);
  if(mDisk){ qs('diskTime').textContent = mDisk[1] + ' s'; diskSeconds = parseNumber(mDisk[1]); }
  const mRam = line.match(/Tiempo total desde RAM:\\s*([\\d.,]+)\\s*segundos/i);
  if(mRam){ qs('ramTime').textContent = mRam[1] + ' s'; ramSeconds = parseNumber(mRam[1]); }
  const mSpeed = line.match(/fue\\s*([\\d.,]+)\\s*veces/i);
  if(mSpeed){ qs('speedup').textContent = '× ' + mSpeed[1]; }
  renderChart();
}
function renderChart(){
  const canvas = qs('chart'); if(!canvas) return; const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1; const cssW = canvas.clientWidth; const cssH = canvas.clientHeight;
  if(canvas.width !== Math.floor(cssW * dpr) || canvas.height !== Math.floor(cssH * dpr)){ canvas.width = Math.floor(cssW * dpr); canvas.height = Math.floor(cssH * dpr); }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH); ctx.fillStyle = '#0b1220'; ctx.fillRect(0, 0, cssW, cssH);
  const pad = 16; const axisY = cssH - pad - 18; ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--border').trim() || '#1f2937'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad, axisY); ctx.lineTo(cssW - pad, axisY); ctx.stroke();
  const vals = []; if(diskSeconds != null) vals.push({label: 'Disco', value: diskSeconds, color1: '#60a5fa', color2: '#3b82f6'}); if(ramSeconds != null) vals.push({label: 'RAM', value: ramSeconds, color1: '#22d3ee', color2: '#06b6d4'});
  if(vals.length === 0){ ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--muted').trim() || '#9ca3af'; ctx.font = '12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto'; ctx.fillText('Esperando métricas…', pad, axisY - 10); return; }
  const maxVal = Math.max(...vals.map(v => v.value)) || 1; const chartW = cssW - pad * 2; const chartH = axisY - pad; const barGap = 18; const barWidth = Math.min(120, (chartW - barGap * (vals.length - 1)) / vals.length); const startX = pad + (chartW - (barWidth * vals.length + barGap * (vals.length - 1))) / 2;
  vals.forEach((v, i) => { const h = Math.max(2, (v.value / maxVal) * chartH); const x = startX + i * (barWidth + barGap); const y = axisY - h; const grad = ctx.createLinearGradient(0, y, 0, y + h); grad.addColorStop(0, v.color1); grad.addColorStop(1, v.color2); ctx.fillStyle = grad; ctx.strokeStyle = 'rgba(255,255,255,0.08)'; ctx.lineWidth = 1; ctx.beginPath(); const r = 8; ctx.moveTo(x, y + r); ctx.arcTo(x, y, x + r, y, r); ctx.lineTo(x + barWidth - r, y); ctx.arcTo(x + barWidth, y, x + barWidth, y + r, r); ctx.lineTo(x + barWidth, y + h); ctx.lineTo(x, y + h); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#e5e7eb'; ctx.font = '12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto'; ctx.textAlign = 'center'; ctx.fillText(v.label, x + barWidth / 2, axisY + 14); ctx.fillStyle = '#cbd5e1'; ctx.textAlign = 'center'; ctx.fillText((Math.round(v.value * 1000) / 1000) + ' s', x + barWidth / 2, y - 6); });
}
function start(){ if(eventSource){ stop(); } clearUI(); setStatus('warn', 'Conectando…'); qs('startBtn').disabled = true; qs('stopBtn').disabled = false; qs('startIcon').style.display = 'none'; qs('startSpin').style.display = 'inline-block'; endedGracefully = false; eventSource = new EventSource('/stream'); eventSource.onopen = () => { setStatus('ok', 'Conectado'); qs('startSpin').style.display = 'none'; qs('startIcon').style.display = 'inline-block'; }; eventSource.onmessage = (ev) => { const line = ev.data || ''; if(line === '__END__'){ endedGracefully = true; appendLine('--- FIN DE LA PRUEBA ---'); setStatus('ok', 'Completado'); qs('startBtn').disabled = false; qs('stopBtn').disabled = true; if(eventSource){ eventSource.close(); eventSource = null; } return; } appendLine(line); parseMetrics(line); }; eventSource.onerror = () => { if(!endedGracefully){ appendLine('ERROR: Conexión cerrada por el servidor.'); setStatus('err', 'Desconectado'); } qs('startBtn').disabled = false; qs('stopBtn').disabled = true; qs('startSpin').style.display = 'none'; qs('startIcon').style.display = 'inline-block'; if(eventSource){ eventSource.close(); eventSource = null; } } }
function stop(){ if(eventSource){ eventSource.close(); eventSource = null; } setStatus('err', 'Detenido'); qs('startBtn').disabled = false; qs('stopBtn').disabled = true; }
async function dropAndRestart(){
  stop(); setStatus('warn', 'Limpiando caché…'); qs('flushBtn').disabled = true;
  try {
    const token = localStorage.getItem('adminToken') || '';
    const res = await fetch('/drop_caches', { method: 'POST', headers: { 'X-Admin-Token': token } });
    const data = await res.json();
    appendLine('--- LIMPIEZA DE CACHÉ ---');
    if(res.status === 403){ appendLine(data.message || 'FORBIDDEN'); setStatus('err', 'Acceso denegado'); return; }
    appendLine(`MemInfo antes - Cached: ${data.before.CachedMB} MB, Buffers: ${data.before.BuffersMB} MB, Dirty: ${data.before.DirtyMB} MB`);
    appendLine(data.message.trim());
    appendLine(`MemInfo después - Cached: ${data.after.CachedMB} MB, Buffers: ${data.after.BuffersMB} MB, Dirty: ${data.after.DirtyMB} MB`);
    if(data.ok){ setStatus('ok', 'Caché limpiado'); } else { setStatus('warn', 'Limpieza con advertencias'); }
  } catch (e) {
    appendLine(`ERROR: Limpieza falló: ${e}`); setStatus('err', 'Error al limpiar');
  } finally {
    qs('flushBtn').disabled = false; start();
  }
}
function copyLog(){ const text = Array.from(qs('console').children).map(x => x.textContent).join('\\n'); navigator.clipboard.writeText(text).then(() => { setStatus('ok', 'Copiado al portapapeles'); setTimeout(()=> setStatus('ok', 'Conectado'), 1000); }).catch(() => setStatus('warn', 'No se pudo copiar')); }
function downloadLog(){ const text = Array.from(qs('console').children).map(x => x.textContent).join('\\n'); const blob = new Blob([text], { type: 'text/plain;charset=utf-8' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'log_prueba_memoria.txt'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); }
window.addEventListener('DOMContentLoaded', () => { setStatus('warn', 'Listo'); qs('stopBtn').disabled = true; });
// Tabs
window.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.tab');
  const views = document.querySelectorAll('.view');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      views.forEach(v => v.classList.remove('active'));
      tab.classList.add('active');
      const target = tab.getAttribute('data-target');
      const view = document.getElementById(target);
      if(view){ view.classList.add('active'); }
      // Si cambiamos de pestaña, no mezclamos conexiones abiertas
      if(target === 'view-memory'){ if(bmSource){ stopBenchmark(); } }
      if(target === 'view-benchmark'){ if(eventSource){ stop(); } }
    });
  });
});

// Benchmark UI
function bmAppend(text){ const el = document.createElement('div'); el.className = 'line'; el.textContent = text; const lower = text.toLowerCase(); if(text.startsWith('---')) el.classList.add('section'); else if(lower.includes('error')) el.classList.add('err'); qs('bmConsole').appendChild(el); if(qs('autoScroll').checked){ qs('bmConsole').scrollTop = qs('bmConsole').scrollHeight; } }
function startBenchmark(){
  if(bmSource){ stopBenchmark(); }
  qs('bmConsole').innerHTML = '';
  bmPassTimes = [];
  if(qs('bmThroughput')) qs('bmThroughput').textContent = '—';
  if(qs('bmTotal')) qs('bmTotal').textContent = '—';
  if(qs('bmLastPass')) qs('bmLastPass').textContent = '—';
  renderBmChart();
  const filePath = (qs('bmFile').value || 'archivo_grande.txt').trim();
  const pattern = qs('bmPattern').value;
  const blockSize = parseInt(qs('bmBlock').value || '65536', 10);
  const strideBytes = parseInt(qs('bmStride').value || String(blockSize), 10);
  const hotsetPercent = parseInt(qs('bmHot').value || '10', 10);
  const passes = parseInt(qs('bmPasses').value || '1', 10);
  const token = localStorage.getItem('adminToken') || '';
  const q = new URLSearchParams({ filePath, pattern, blockSize, strideBytes, hotsetPercent, passes, token });
  bmSource = new EventSource('/benchmark/stream?' + q.toString());
  bmSource.onmessage = (ev) => {
    const line = ev.data || '';
    if(line === '__END__'){ stopBenchmark(); return; }
    bmAppend(line);
    bmParse(line);
  };
  bmSource.onerror = () => { bmAppend('ERROR: Conexión de benchmark cerrada'); stopBenchmark(); };
}
function stopBenchmark(){ if(bmSource){ bmSource.close(); bmSource = null; } }

// Benchmark parse & chart
function bmParse(line){
  const mPass = line.match(/Tiempo pasada\s*(\d+):\s*([\d.,]+)\s*s/i);
  if(mPass){
    const idx = parseInt(mPass[1], 10) - 1;
    const sec = parseFloat(String(mPass[2]).replace(',', '.'));
    if(Number.isFinite(idx) && Number.isFinite(sec)){
      bmPassTimes[idx] = sec;
      if(qs('bmLastPass')) qs('bmLastPass').textContent = sec.toFixed(3) + ' s';
      renderBmChart();
    }
  }
  const mTotal = line.match(/Total leído:\s*([\d.,]+)\s*MiB/i);
  if(mTotal){ if(qs('bmTotal')) qs('bmTotal').textContent = mTotal[1] + ' MiB'; }
  const mTp = line.match(/Throughput medio:\s*([\d.,]+)\s*MiB\/s/i);
  if(mTp){ if(qs('bmThroughput')) qs('bmThroughput').textContent = '× ' + mTp[1] + ' MiB/s'; }
}

function renderBmChart(){
  const canvas = qs('bmChart'); if(!canvas) return; const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1; const cssW = canvas.clientWidth; const cssH = canvas.clientHeight;
  if(canvas.width !== Math.floor(cssW * dpr) || canvas.height !== Math.floor(cssH * dpr)){ canvas.width = Math.floor(cssW * dpr); canvas.height = Math.floor(cssH * dpr); }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH); ctx.fillStyle = '#0b1220'; ctx.fillRect(0, 0, cssW, cssH);
  const pad = 16; const axisY = cssH - pad - 18; ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--border').trim() || '#1f2937'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(pad, axisY); ctx.lineTo(cssW - pad, axisY); ctx.stroke();
  const vals = bmPassTimes.filter(v => typeof v === 'number' && Number.isFinite(v));
  if(vals.length === 0){ ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--muted').trim() || '#9ca3af'; ctx.font = '12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto'; ctx.fillText('Esperando datos…', pad, axisY - 10); return; }
  const maxVal = Math.max(...vals) || 1; const chartW = cssW - pad * 2; const chartH = axisY - pad; const barGap = 10; const barWidth = Math.max(6, Math.min(60, (chartW - barGap * (vals.length - 1)) / vals.length)); const startX = pad + (chartW - (barWidth * vals.length + barGap * (vals.length - 1))) / 2;
  vals.forEach((v, i) => { const h = Math.max(2, (v / maxVal) * chartH); const x = startX + i * (barWidth + barGap); const y = axisY - h; const grad = ctx.createLinearGradient(0, y, 0, y + h); grad.addColorStop(0, '#a78bfa'); grad.addColorStop(1, '#8b5cf6'); ctx.fillStyle = grad; ctx.strokeStyle = 'rgba(255,255,255,0.08)'; ctx.lineWidth = 1; ctx.beginPath(); const r = 6; ctx.moveTo(x, y + r); ctx.arcTo(x, y, x + r, y, r); ctx.lineTo(x + barWidth - r, y); ctx.arcTo(x + barWidth, y, x + barWidth, y + r, r); ctx.lineTo(x + barWidth, y + h); ctx.lineTo(x, y + h); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#cbd5e1'; ctx.font = '11px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto'; ctx.textAlign = 'center'; ctx.fillText(String(i+1), x + barWidth / 2, axisY + 14); });
}

