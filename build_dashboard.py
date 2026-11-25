"""Genera dashboard.html interactivo con selector de fechas y comparador estilo Google Ads."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Joyería Pietra · Dashboard Live Interactivo</title>
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="apple-touch-icon" href="assets/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{
    --bg:#f4f1eb;--bg2:#ebe6dc;--card:#ffffff;--ink:#141414;--muted:#635e56;--line:#e3ddd1;
    --gold:#c9a227;--gold-deep:#9a7b1a;--gold-soft:rgba(201,162,39,.12);
    --meta:#1877F2;--instagram:#E1306C;--google:#4285F4;
    --up:#0f7a45;--up-bg:rgba(15,122,69,.10);--down:#b42318;--down-bg:rgba(180,35,24,.10);
    --radius:14px;--shadow:0 4px 20px rgba(20,20,20,.05);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{background:var(--bg);color:var(--ink);font-family:'Inter',sans-serif;font-size:14px;line-height:1.5}
  .hero{background:linear-gradient(135deg,#141414 0%,#231f18 65%,#2f281a 100%);color:#f8f5ef;padding:28px 24px 24px;border-bottom:3px solid var(--gold)}
  .container{max-width:1280px;margin:0 auto;padding:0 20px}
  .hero-top{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px}
  .brand{display:flex;align-items:center;gap:14px}
  .brand-mark{width:48px;height:48px;border-radius:12px;border:1.5px solid var(--gold);display:grid;place-items:center;font-family:'Cormorant Garamond',serif;font-size:24px;font-weight:700;color:var(--gold);background:rgba(201,162,39,.08)}
  .brand h1{font-family:'Cormorant Garamond',serif;font-size:30px;font-weight:600;letter-spacing:.04em}
  .brand p{color:#cfc7b8;font-size:12.5px;margin-top:2px}
  .hero-badges{display:flex;flex-wrap:wrap;gap:8px}
  .pill{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border-radius:999px;font-size:11.5px;font-weight:500;background:rgba(255,255,255,.08);color:#f4f1eb;border:1px solid rgba(255,255,255,.14)}
  .pill .dot{width:7px;height:7px;border-radius:50%}

  /* Sticky Date + Nav Bar */
  .toolbar{background:rgba(255,255,255,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:50;box-shadow:0 2px 12px rgba(20,20,20,.04)}
  .toolbar-inner{max-width:1280px;margin:0 auto;padding:10px 20px;display:flex;flex-direction:column;gap:10px}
  .row-flex{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px}
  .nav-links{display:flex;flex-wrap:wrap;gap:6px}
  .nav-links a{text-decoration:none;color:var(--muted);font-size:12.5px;font-weight:600;padding:6px 12px;border-radius:999px}
  .nav-links a:hover{background:var(--bg2);color:var(--ink)}
  .nav-links a.active{background:var(--ink);color:#fff}

  .date-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding-top:8px;border-top:1px solid var(--line)}
  .preset-btn{border:1px solid var(--line);background:var(--bg);color:var(--ink);font-size:12px;font-weight:600;padding:5px 10px;border-radius:8px;cursor:pointer;transition:.15s}
  .preset-btn:hover{border-color:var(--gold);background:#fff}
  .preset-btn.active{background:var(--ink);color:#fff;border-color:var(--ink)}
  .date-grp{display:inline-flex;align-items:center;gap:6px;background:var(--bg);border:1px solid var(--line);padding:4px 8px;border-radius:8px;font-size:12px}
  .date-grp input[type="date"]{border:none;background:transparent;font-family:inherit;font-size:12px;font-weight:600;color:var(--ink);outline:none}
  .cmp-toggle{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;cursor:pointer;padding:5px 10px;border-radius:8px;border:1px solid var(--line);background:#fff}
  .cmp-toggle input{accent-color:var(--meta);width:15px;height:15px;cursor:pointer}
  .cmp-box{display:inline-flex;align-items:center;gap:6px;background:rgba(24,119,242,.06);border:1px solid rgba(24,119,242,.25);padding:4px 8px;border-radius:8px;font-size:12px}
  .cmp-box select,.cmp-box input[type="date"]{border:none;background:transparent;font-family:inherit;font-size:12px;font-weight:600;color:var(--meta);outline:none}

  section{padding:28px 0 8px}
  .sec-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:10px;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--line)}
  .sec-title{display:flex;align-items:center;gap:10px}
  .sec-accent{width:4px;height:24px;border-radius:4px;background:var(--gold)}
  .sec-title h2{font-family:'Cormorant Garamond',serif;font-size:26px;font-weight:600}
  .sec-sub{font-size:12px;color:var(--muted)}
  .kpi-grid-4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
  .grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:18px}
  @media(max-width:1000px){.kpi-grid-4{grid-template-columns:repeat(2,1fr)}}
  @media(max-width:860px){.grid-2{grid-template-columns:1fr}}
  .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow)}
  .kpi-card{padding:15px 17px}
  .kpi-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
  .kpi-val{font-size:23px;font-weight:700;margin:5px 0 7px;letter-spacing:-.02em}
  .kpi-foot{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:11.5px;color:var(--muted)}
  .delta{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:999px;font-weight:600;font-size:11px;white-space:nowrap}
  .delta.up{background:var(--up-bg);color:var(--up)}
  .delta.down{background:var(--down-bg);color:var(--down)}
  .card-title{font-size:14.5px;font-weight:700;margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;gap:8px}
  .card-sub{font-size:12px;color:var(--muted);margin-bottom:12px}
  .chart-wrap{position:relative;height:260px;width:100%}
  .funnel-list{display:flex;flex-direction:column;gap:10px}
  .funnel-row{display:grid;grid-template-columns:138px 1fr 118px;align-items:center;gap:12px}
  .funnel-lbl{font-size:12.5px;font-weight:600}
  .funnel-bar-bg{height:24px;background:var(--bg);border-radius:8px;overflow:hidden;border:1px solid var(--line)}
  .funnel-bar{height:100%;border-radius:7px;background:linear-gradient(90deg,var(--meta),#4e95f7)}
  .funnel-num{text-align:right;font-size:12.5px;font-weight:600}
  .funnel-num small{display:block;font-size:11px;font-weight:500;color:var(--muted)}
  .table-wrap{overflow-x:auto}
  table{width:100%;border-collapse:collapse;font-size:12.6px}
  th{text-align:left;padding:9px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border-bottom:2px solid var(--line);white-space:nowrap}
  td{padding:9px;border-bottom:1px solid var(--line);vertical-align:middle}
  tr:last-child td{border-bottom:none}
  .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;background:var(--bg2)}
  .tag.gold{background:var(--gold-soft);color:var(--gold-deep)}
  .tag.meta{background:rgba(24,119,242,.10);color:var(--meta)}
  .tag.ig{background:rgba(225,48,108,.10);color:var(--instagram)}
  .ad-cell{display:flex;align-items:center;gap:9px}
  .thumb{width:38px;height:38px;border-radius:7px;object-fit:cover;border:1px solid var(--line);flex-shrink:0}
  .top3-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px}
  @media(max-width:860px){.top3-grid{grid-template-columns:1fr}}
  .top3-card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column}
  .top3-img-wrap{position:relative;height:210px;background:#181613;overflow:hidden}
  .top3-img-wrap img{width:100%;height:100%;object-fit:cover;display:block}
  .top3-rank{position:absolute;top:10px;left:10px;background:rgba(20,20,20,.85);color:var(--gold);font-weight:700;font-size:12px;padding:4px 10px;border-radius:999px;border:1px solid var(--gold)}
  .top3-body{padding:14px 16px;display:flex;flex-direction:column;gap:8px;flex:1}
  .top3-cap{font-size:12.5px;color:var(--ink);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .top3-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:auto;padding-top:8px;border-top:1px solid var(--line);font-size:11.5px;text-align:center}
  .top3-stats strong{display:block;font-size:14px;color:var(--ink)}
  .top3-link{text-decoration:none;color:var(--instagram);font-size:12px;font-weight:600}
  footer{margin-top:36px;padding:22px 20px 34px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;text-align:center}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="hero-top">
      <div class="brand">
        <img src="assets/pietra-logo-white.png" alt="Joyería Pietra" style="height:46px;width:auto;display:block">
        <div style="border-left:1px solid rgba(255,255,255,.18);padding-left:14px">
          <div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);font-weight:600">Dashboard Performance · Live API</div>
          <p id="hero-sub">Dashboard Interactivo · Selección de fechas y comparador</p>
        </div>
      </div>
      <div class="hero-badges">
        <span class="pill"><span class="dot" style="background:var(--up)"></span>Meta API Conectada</span>
        <span class="pill"><span class="dot" style="background:var(--instagram)"></span>IG Graph API Conectada</span>
        <span class="pill"><span class="dot" style="background:var(--up)"></span>Google Ads Conectado</span>
      </div>
    </div>
  </div>
</header>

<div class="toolbar">
  <div class="toolbar-inner">
    <div class="row-flex">
      <div class="nav-links">
        <a href="#blended" class="active">Blended</a>
        <a href="#meta">Meta Ads</a>
        <a href="#google">Google Ads</a>
        <a href="#organic">Orgánico (IG &amp; FB)</a>
      </div>
      <div style="font-size:12px;color:var(--muted)">Actualizado: <strong id="gen-at"></strong></div>
    </div>
    <div class="date-bar">
      <button class="preset-btn active" data-preset="this_month">Este mes</button>
      <button class="preset-btn" data-preset="last_7">Últimos 7 días</button>
      <button class="preset-btn" data-preset="last_14">Últimos 14 días</button>
      <button class="preset-btn" data-preset="last_30">Últimos 30 días</button>
      <button class="preset-btn" data-preset="last_month">Mes pasado</button>
      <button class="preset-btn" data-preset="all">Todo (desde Sep)</button>
      <div class="date-grp">
        <span>Período:</span>
        <input type="date" id="dt-start">
        <span>→</span>
        <input type="date" id="dt-end">
      </div>
      <label class="cmp-toggle">
        <input type="checkbox" id="cmp-enabled" checked>
        <span>Comparar</span>
      </label>
      <div class="cmp-box" id="cmp-box">
        <select id="cmp-mode">
          <option value="prev_eq">Período anterior equiv.</option>
          <option value="custom">Personalizado</option>
        </select>
        <input type="date" id="cmp-start" disabled>
        <span>→</span>
        <input type="date" id="cmp-end" disabled>
      </div>
    </div>
  </div>
</div>

<main class="container">
  <section id="blended">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent"></div><h2>Resumen Ejecutivo Blended (Meta + Google)</h2></div>
      <div class="sec-sub" id="blended-sub"></div>
    </div>
    <div class="kpi-grid-4" id="blended-kpis"></div>
  </section>

  <section id="meta">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent" style="background:var(--meta)"></div><h2>Meta Ads · Rendimiento &amp; Evolución</h2></div>
      <div class="sec-sub" id="meta-sub"></div>
    </div>
    <div class="kpi-grid-4" id="meta-kpis"></div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Evolución Diaria (Inversión vs. Facturación)</div>
        <div class="card-sub">Serie diaria filtrada por el rango seleccionado</div>
        <div class="chart-wrap"><canvas id="chartDaily"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Embudo de Conversión Meta Ads</div>
        <div class="card-sub">Impresiones → Clics → Landing → Carrito → Pagos → Compras</div>
        <div class="funnel-list" id="meta-funnel"></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Campañas Meta Ads</div>
        <div class="card-sub">Totales del período seleccionado</div>
        <div class="table-wrap"><table id="meta-campaigns-table"></table></div>
      </div>
      <div class="card">
        <div class="card-title">Distribución por Edad</div>
        <div class="card-sub">Compras e inversión por rango etario</div>
        <div class="chart-wrap"><canvas id="chartAge"></canvas></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Top 10 Anuncios (Período Seleccionado)</div>
        <div class="card-sub">Ordenados por compras e inversión</div>
        <div class="table-wrap"><table id="meta-ads-table"></table></div>
      </div>
      <div class="card">
        <div class="card-title">Top Regiones por Inversión (Histórico API)</div>
        <div class="card-sub">Distribución geográfica acumulada desde Sep 2026</div>
        <div class="table-wrap"><table id="meta-region-table"></table></div>
      </div>
    </div>
  </section>

  <section id="google">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent" style="background:var(--google)"></div><h2>Google Ads · Search &amp; Performance Max</h2></div>
      <div class="sec-sub" id="google-sub"></div>
    </div>
    <div class="kpi-grid-4" id="google-kpis"></div>

    <div class="card" style="margin-top:18px">
      <div class="card-title">Campañas de Google Ads</div>
      <div class="table-wrap"><table id="google-campaigns-table"></table></div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Top Palabras Clave (Search)</div>
        <div class="table-wrap"><table id="google-kw-table"></table></div>
      </div>
      <div class="card">
        <div class="card-title">Top 10 Productos Convertidores (PMax / Shopping)</div>
        <div class="table-wrap"><table id="google-products-table"></table></div>
      </div>
    </div>
  </section>

  <section id="organic">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent" style="background:var(--instagram)"></div><h2>Orgánico · Instagram &amp; Facebook</h2></div>
      <div class="sec-sub" id="org-sub"></div>
    </div>
    <div class="kpi-grid-4" id="org-kpis"></div>

    <div style="margin-top:20px">
      <div class="card-title">Top 3 Contenidos Orgánicos del Período (por Interacciones)</div>
      <div class="card-sub">Likes + Comentarios + Guardados + Compartidos · Clic en la imagen para abrir en Instagram</div>
      <div class="top3-grid" id="ig-top3"></div>
    </div>

    <div class="card" style="margin-top:18px">
      <div class="card-title">Publicaciones y Reels de Instagram (Período Seleccionado)</div>
      <div class="card-sub">Con miniaturas, alcance, visualizaciones e interacciones totales</div>
      <div class="table-wrap"><table id="ig-media-table"></table></div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Historias de Instagram que más rindieron <span class="tag ig">Top 10</span></div>
        <div class="card-sub">Ordenadas por visualizaciones orgánicas en el período</div>
        <div class="table-wrap"><table id="ig-stories-top-table"></table></div>
      </div>
      <div class="card">
        <div class="card-title">Historias de Instagram que menos rindieron <span class="tag ig">Menor alcance</span></div>
        <div class="card-sub">Acumulado automáticamente cada 8h vía IG Graph API (desde 25/11/2026)</div>
        <div class="table-wrap"><table id="ig-stories-bottom-table"></table></div>
      </div>
    </div>
  </section>
</main>

<footer>
  <div>Joyería Pietra · Dashboard Live Interactivo · Meta Marketing API + Google Ads Scripts → Google Sheets</div>
  <div style="margin-top:14px;display:flex;align-items:center;justify-content:center;gap:10px;opacity:.92">
    <span style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)">Desarrollado por</span>
    <img src="assets/freehub-logo-color.png" alt="Freehub" style="height:22px;width:auto;display:block">
  </div>
</footer>

<script>
const P = __PAYLOAD_JSON__;
const META = P.meta_daily;
const GOOG = P.google_ads || { daily_campaigns:[], daily_keywords:[], daily_products:[] };

const fmtARS = v => '$' + Math.round(v || 0).toLocaleString('es-AR');
const fmtNum = (v, d=0) => Number(v || 0).toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d });
const parseISO = s => { const [y,m,d] = s.split('-').map(Number); return new Date(y, m-1, d); };
const toISO = dt => `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')}`;
const addDays = (s, n) => { const dt = parseISO(s); dt.setDate(dt.getDate() + n); return toISO(dt); };
const diffDays = (a, b) => Math.round((parseISO(b) - parseISO(a)) / 86400000) + 1;

const deltaBadge = (cur, prev, inv=false) => {
  if (!document.getElementById('cmp-enabled').checked) return '';
  if (!prev) return '<span class="delta">—</span>';
  const d = ((cur - prev) / prev) * 100;
  const good = inv ? d < 0 : d >= 0;
  return `<span class="delta ${good?'up':'down'}">${d>=0?'▲':'▼'} ${d>=0?'+':''}${d.toFixed(1).replace('.',',')}%</span>`;
};

const minDate = META.since;
const maxDate = META.until;
document.getElementById('gen-at').textContent = P.generated_at;

const dtStart = document.getElementById('dt-start');
const dtEnd = document.getElementById('dt-end');
const cmpEnabled = document.getElementById('cmp-enabled');
const cmpMode = document.getElementById('cmp-mode');
const cmpStart = document.getElementById('cmp-start');
const cmpEnd = document.getElementById('cmp-end');

[dtStart, dtEnd, cmpStart, cmpEnd].forEach(el => { el.min = minDate; el.max = maxDate; });

let chartDaily = null, chartAge = null;

function sumMeta(rows, s, e) {
  let sp=0, im=0, lc=0, lp=0, ac=0, ic=0, p=0, rv=0;
  for (const r of rows) {
    if (r.d >= s && r.d <= e) {
      sp+=r.sp; im+=r.im; lc+=r.lc; lp+=r.lp; ac+=r.ac; ic+=r.ic; p+=r.p; rv+=r.rv;
    }
  }
  return { sp, im, lc, lp, ac, ic, p, rv, ctr: im?lc/im*100:0, roas: sp?rv/sp:0, cpa: p?sp/p:0, aov: p?rv/p:0 };
}

function groupMeta(rows, s, e) {
  const m = {};
  for (const r of rows) {
    if (r.d < s || r.d > e) continue;
    const k = r.k || '(sin nombre)';
    if (!m[k]) m[k] = { k, id: r.id||'', sp:0, im:0, lc:0, p:0, rv:0 };
    m[k].sp+=r.sp; m[k].im+=r.im; m[k].lc+=r.lc; m[k].p+=r.p; m[k].rv+=r.rv;
    if (r.id && !m[k].id) m[k].id = r.id;
  }
  return Object.values(m).map(x => ({ ...x, roas: x.sp?x.rv/x.sp:0, cpa: x.p?x.sp/x.p:0 }));
}

function sumGoogle(rows, s, e) {
  let sp=0, im=0, cl=0, cv=0, rv=0;
  for (const r of rows) {
    if (r.d >= s && r.d <= e) { sp+=r.sp; im+=(r.im||0); cl+=r.cl; cv+=r.cv; rv+=r.rv; }
  }
  return { sp, im, cl, cv, rv, ctr: im?cl/im*100:0, cpc: cl?sp/cl:0, cpa: cv?sp/cv:0, roas: sp?rv/sp:0 };
}

function groupGoogle(rows, s, e) {
  const m = {};
  for (const r of rows) {
    if (r.d < s || r.d > e) continue;
    const k = r.k || '(sin nombre)';
    if (!m[k]) m[k] = { k, sp:0, im:0, cl:0, cv:0, rv:0 };
    m[k].sp+=r.sp; m[k].im+=(r.im||0); m[k].cl+=r.cl; m[k].cv+=r.cv; m[k].rv+=r.rv;
  }
  return Object.values(m).map(x => ({ ...x, ctr: x.im?x.cl/x.im*100:0, cpa: x.cv?x.sp/x.cv:0, roas: x.sp?x.rv/x.sp:0 }));
}

function syncCompareDates() {
  const on = cmpEnabled.checked;
  document.getElementById('cmp-box').style.opacity = on ? '1' : '.45';
  cmpMode.disabled = !on;
  const custom = on && cmpMode.value === 'custom';
  cmpStart.disabled = !custom;
  cmpEnd.disabled = !custom;
  if (on && cmpMode.value === 'prev_eq') {
    const days = Math.max(1, diffDays(dtStart.value, dtEnd.value));
    const pe = addDays(dtStart.value, -1);
    const ps = addDays(pe, -(days - 1));
    cmpStart.value = ps < minDate ? minDate : ps;
    cmpEnd.value = pe < minDate ? minDate : pe;
  }
}

function renderAll() {
  syncCompareDates();
  const s = dtStart.value, e = dtEnd.value;
  const cmpOn = cmpEnabled.checked;
  const cs = cmpStart.value, ce = cmpEnd.value;
  const days = diffDays(s, e);

  document.getElementById('hero-sub').textContent = cmpOn
    ? `Período: ${s} al ${e} (${days} días) · Comparado con: ${cs} al ${ce}`
    : `Período: ${s} al ${e} (${days} días)`;

  const mC = sumMeta(META.daily_account, s, e);
  const mP = cmpOn ? sumMeta(META.daily_account, cs, ce) : null;
  const gC = sumGoogle(GOOG.daily_campaigns, s, e);
  const gP = cmpOn ? sumGoogle(GOOG.daily_campaigns, cs, ce) : null;

  // Blended
  const bC = { sp: mC.sp+gC.sp, rv: mC.rv+gC.rv, p: mC.p+gC.cv };
  bC.roas = bC.sp ? bC.rv/bC.sp : 0; bC.cpa = bC.p ? bC.sp/bC.p : 0; bC.aov = bC.p ? bC.rv/bC.p : 0;
  const bP = cmpOn ? (() => {
    const o = { sp: mP.sp+gP.sp, rv: mP.rv+gP.rv, p: mP.p+gP.cv };
    o.roas = o.sp ? o.rv/o.sp : 0; o.cpa = o.p ? o.sp/o.p : 0; return o;
  })() : null;

  document.getElementById('blended-sub').textContent = cmpOn ? `${s}..${e} vs. ${cs}..${ce}` : `${s}..${e}`;
  document.getElementById('blended-kpis').innerHTML = [
    { l:'Inversión Total', v:fmtARS(bC.sp), f:cmpOn?`Comp: ${fmtARS(bP.sp)}`:`Meta ${fmtNum(bC.sp?mC.sp/bC.sp*100:0,1)}% · Google ${fmtNum(bC.sp?gC.sp/bC.sp*100:0,1)}%`, b:cmpOn?deltaBadge(bC.sp,bP.sp):'' },
    { l:'Facturación Atribuida', v:fmtARS(bC.rv), f:cmpOn?`Comp: ${fmtARS(bP.rv)}`:`Ticket: ${fmtARS(bC.aov)}`, b:cmpOn?deltaBadge(bC.rv,bP.rv):'' },
    { l:'ROAS Blended', v:fmtNum(bC.roas,2)+'×', f:cmpOn?`Comp: ${fmtNum(bP.roas,2)}×`:`Compras/Conv: ${fmtNum(bC.p,1)}`, b:cmpOn?deltaBadge(bC.roas,bP.roas):'' },
    { l:'CPA Blended', v:fmtARS(bC.cpa), f:cmpOn?`Comp: ${fmtARS(bP.cpa)}`:`Compras/Conv: ${fmtNum(bC.p,1)}`, b:cmpOn?deltaBadge(bC.cpa,bP.cpa,true):'' }
  ].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>${k.f}</span>${k.b}</div></div>`).join('');

  // Meta KPIs
  document.getElementById('meta-sub').textContent = cmpOn ? `${s}..${e} vs. ${cs}..${ce}` : `${s}..${e}`;
  document.getElementById('meta-kpis').innerHTML = [
    { l:'Inversión Meta', v:fmtARS(mC.sp), f:cmpOn?`Comp: ${fmtARS(mP.sp)}`:'', b:cmpOn?deltaBadge(mC.sp,mP.sp):'' },
    { l:'Facturación Meta', v:fmtARS(mC.rv), f:cmpOn?`Comp: ${fmtARS(mP.rv)}`:'', b:cmpOn?deltaBadge(mC.rv,mP.rv):'' },
    { l:'Compras', v:fmtNum(mC.p), f:cmpOn?`Comp: ${fmtNum(mP.p)}`:'', b:cmpOn?deltaBadge(mC.p,mP.p):'' },
    { l:'ROAS Meta', v:fmtNum(mC.roas,2)+'×', f:cmpOn?`Comp: ${fmtNum(mP.roas,2)}×`:'', b:cmpOn?deltaBadge(mC.roas,mP.roas):'' },
    { l:'CPA Meta', v:fmtARS(mC.cpa), f:cmpOn?`Comp: ${fmtARS(mP.cpa)}`:'', b:cmpOn?deltaBadge(mC.cpa,mP.cpa,true):'' },
    { l:'Clics en Enlace', v:fmtNum(mC.lc), f:cmpOn?`Comp: ${fmtNum(mP.lc)}`:'', b:cmpOn?deltaBadge(mC.lc,mP.lc):'' },
    { l:'CTR Enlace', v:fmtNum(mC.ctr,2)+'%', f:cmpOn?`Comp: ${fmtNum(mP.ctr,2)}%`:'', b:cmpOn?deltaBadge(mC.ctr,mP.ctr):'' },
    { l:'AOV Meta', v:fmtARS(mC.aov), f:cmpOn?`Comp: ${fmtARS(mP.aov)}`:'', b:cmpOn?deltaBadge(mC.aov,mP.aov):'' }
  ].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>${k.f}</span>${k.b}</div></div>`).join('');

  // Meta Funnel
  const fSteps = [
    { l:'Impresiones', v:mC.im, s:'100%' },
    { l:'Clics en enlace', v:mC.lc, s:fmtNum(mC.ctr,2)+'% CTR' },
    { l:'Visitas a landing', v:mC.lp, s:fmtNum(mC.lc?mC.lp/mC.lc*100:0,1)+'% de clics' },
    { l:'Agregar al carrito', v:mC.ac, s:fmtNum(mC.lp?mC.ac/mC.lp*100:0,1)+'% de visitas' },
    { l:'Pagos iniciados', v:mC.ic, s:fmtNum(mC.ac?mC.ic/mC.ac*100:0,1)+'% de ATC' },
    { l:'Compras', v:mC.p, s:fmtNum(mC.ic?mC.p/mC.ic*100:0,1)+'% de pagos' }
  ];
  const fMax = Math.log10(Math.max(10, fSteps[0].v));
  document.getElementById('meta-funnel').innerHTML = fSteps.map((f,i) => {
    const w = i===0 ? 100 : Math.max(8, Math.log10(Math.max(1,f.v))/fMax*100);
    return `<div class="funnel-row"><div class="funnel-lbl">${f.l}</div><div class="funnel-bar-bg"><div class="funnel-bar" style="width:${w.toFixed(1)}%"></div></div><div class="funnel-num">${fmtNum(f.v)}<small>${f.s}</small></div></div>`;
  }).join('');

  // Meta Daily Chart
  const dRows = META.daily_account.filter(r => r.d >= s && r.d <= e);
  if (chartDaily) chartDaily.destroy();
  chartDaily = new Chart(document.getElementById('chartDaily'), {
    type: 'bar',
    data: {
      labels: dRows.map(r => r.d.slice(5)),
      datasets: [
        { label:'Inversión (k ARS)', data: dRows.map(r => +(r.sp/1000).toFixed(1)), backgroundColor:'#c9a227', borderRadius:4, yAxisID:'y' },
        { label:'Facturación (k ARS)', data: dRows.map(r => +(r.rv/1000).toFixed(1)), type:'line', borderColor:'#1877F2', backgroundColor:'rgba(24,119,242,.12)', tension:.25, fill:true, yAxisID:'y1' }
      ]
    },
    options: { responsive:true, maintainAspectRatio:false, scales:{ y:{beginAtZero:true,position:'left'}, y1:{beginAtZero:true,position:'right',grid:{drawOnChartArea:false}} }, plugins:{legend:{position:'bottom'}} }
  });

  // Meta Campaigns
  const mCamps = groupMeta(META.daily_campaigns, s, e).sort((a,b) => b.sp - a.sp);
  document.getElementById('meta-campaigns-table').innerHTML = `
    <thead><tr><th>Campaña</th><th class="num">Inversión</th><th class="num">Compras</th><th class="num">CPA</th><th class="num">Facturación</th><th class="num">ROAS</th></tr></thead>
    <tbody>${mCamps.map(c => `<tr><td><strong>${c.k}</strong></td><td class="num">${fmtARS(c.sp)}</td><td class="num"><strong>${c.p}</strong></td><td class="num">${c.cpa?fmtARS(c.cpa):'—'}</td><td class="num">${fmtARS(c.rv)}</td><td class="num"><span class="tag gold">${fmtNum(c.roas,2)}×</span></td></tr>`).join('')}</tbody>
  `;

  // Meta Age Chart
  const mAges = groupMeta(META.daily_age, s, e).sort((a,b) => a.k.localeCompare(b.k));
  if (chartAge) chartAge.destroy();
  chartAge = new Chart(document.getElementById('chartAge'), {
    type: 'bar',
    data: {
      labels: mAges.map(a => a.k),
      datasets: [
        { label:'Compras', data: mAges.map(a => a.p), backgroundColor:'#1877F2', borderRadius:6, yAxisID:'y' },
        { label:'Inversión (k ARS)', data: mAges.map(a => +(a.sp/1000).toFixed(1)), backgroundColor:'#c9a227', borderRadius:6, yAxisID:'y1' }
      ]
    },
    options: { responsive:true, maintainAspectRatio:false, scales:{ y:{beginAtZero:true,position:'left'}, y1:{beginAtZero:true,position:'right',grid:{drawOnChartArea:false}} }, plugins:{legend:{position:'bottom'}} }
  });

  // Meta Top Ads
  const mAds = groupMeta(META.daily_ads, s, e).sort((a,b) => (b.p - a.p) || (b.sp - a.sp)).slice(0, 10);
  document.getElementById('meta-ads-table').innerHTML = `
    <thead><tr><th>Anuncio</th><th class="num">Inversión</th><th class="num">Compras</th><th class="num">CPA</th><th class="num">ROAS</th></tr></thead>
    <tbody>${mAds.map(a => {
      const th = (META.ad_thumbs || {})[a.id];
      return `<tr><td><div class="ad-cell">${th?`<img class="thumb" src="${th}" alt="">`:''}<strong>${a.k}</strong></div></td><td class="num">${fmtARS(a.sp)}</td><td class="num"><strong>${a.p}</strong></td><td class="num">${a.cpa?fmtARS(a.cpa):'—'}</td><td class="num"><span class="tag gold">${fmtNum(a.roas,2)}×</span></td></tr>`;
    }).join('')}</tbody>
  `;

  // Google KPIs + Tables
  document.getElementById('google-sub').textContent = cmpOn ? `${s}..${e} vs. ${cs}..${ce}` : `${s}..${e}`;
  document.getElementById('google-kpis').innerHTML = [
    { l:'Inversión Google', v:fmtARS(gC.sp), f:cmpOn?`Comp: ${fmtARS(gP.sp)}`:`Impr: ${fmtNum(gC.im)}`, b:cmpOn?deltaBadge(gC.sp,gP.sp):'' },
    { l:'Valor de Conversión', v:fmtARS(gC.rv), f:cmpOn?`Comp: ${fmtARS(gP.rv)}`:`Clics: ${fmtNum(gC.cl)}`, b:cmpOn?deltaBadge(gC.rv,gP.rv):'' },
    { l:'Conversiones', v:fmtNum(gC.cv,2), f:cmpOn?`Comp: ${fmtNum(gP.cv,2)}`:`CPA: ${fmtARS(gC.cpa)}`, b:cmpOn?deltaBadge(gC.cv,gP.cv):'' },
    { l:'ROAS Google', v:fmtNum(gC.roas,2)+'×', f:cmpOn?`Comp: ${fmtNum(gP.roas,2)}×`:`CPC: ${fmtARS(gC.cpc)}`, b:cmpOn?deltaBadge(gC.roas,gP.roas):'' }
  ].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>${k.f}</span>${k.b}</div></div>`).join('');

  const gCamps = groupGoogle(GOOG.daily_campaigns, s, e).sort((a,b) => b.sp - a.sp);
  document.getElementById('google-campaigns-table').innerHTML = `
    <thead><tr><th>Campaña</th><th class="num">Inversión</th><th class="num">Clics</th><th class="num">CTR</th><th class="num">Conv.</th><th class="num">CPA</th><th class="num">Valor Conv.</th><th class="num">ROAS</th></tr></thead>
    <tbody>${gCamps.map(c => `<tr><td><strong>${c.k}</strong></td><td class="num">${fmtARS(c.sp)}</td><td class="num">${fmtNum(c.cl)}</td><td class="num">${fmtNum(c.ctr,2)}%</td><td class="num"><strong>${fmtNum(c.cv,2)}</strong></td><td class="num">${c.cpa?fmtARS(c.cpa):'—'}</td><td class="num">${fmtARS(c.rv)}</td><td class="num"><span class="tag meta">${fmtNum(c.roas,2)}×</span></td></tr>`).join('')}</tbody>
  `;

  const gKw = groupGoogle(GOOG.daily_keywords, s, e).sort((a,b) => b.sp - a.sp).slice(0, 10);
  document.getElementById('google-kw-table').innerHTML = `
    <thead><tr><th>Palabra Clave</th><th class="num">Clics</th><th class="num">Inversión</th><th class="num">Conv.</th><th class="num">CPA</th></tr></thead>
    <tbody>${gKw.map(k => `<tr><td><code>${k.k}</code></td><td class="num">${fmtNum(k.cl)}</td><td class="num">${fmtARS(k.sp)}</td><td class="num"><strong>${fmtNum(k.cv,2)}</strong></td><td class="num">${k.cpa?fmtARS(k.cpa):'—'}</td></tr>`).join('')}</tbody>
  `;

  const gProd = groupGoogle(GOOG.daily_products, s, e).sort((a,b) => (b.rv - a.rv) || (b.cv - a.cv)).slice(0, 10);
  document.getElementById('google-products-table').innerHTML = `
    <thead><tr><th>Producto</th><th class="num">Clics</th><th class="num">Conv.</th><th class="num">Valor Conv.</th></tr></thead>
    <tbody>${gProd.map(p => `<tr><td><strong>${p.k}</strong></td><td class="num">${fmtNum(p.cl)}</td><td class="num">${fmtNum(p.cv,2)}</td><td class="num"><strong>${fmtARS(p.rv)}</strong></td></tr>`).join('')}</tbody>
  `;

  // Organic dynamic by selected date range
  renderOrganic(s, e);
}

function renderOrganic(s, e) {
  const allMedia = (P.organic.instagram.media || []);
  const inRange = allMedia.filter(m => m.d >= s && m.d <= e);
  const mediaList = inRange.length ? inRange : allMedia.slice(0, 12);

  const top3 = mediaList.slice().sort((a,b) => (b.interactions - a.interactions) || (b.views - a.views)).slice(0, 3);
  document.getElementById('ig-top3').innerHTML = top3.length ? top3.map((m, i) => `
    <div class="top3-card">
      <a class="top3-img-wrap" href="${m.permalink||'#'}" target="_blank" rel="noopener">
        ${m.thumb ? `<img src="${m.thumb}" alt="">` : ''}
        <span class="top3-rank">#${i+1} · ${m.type}</span>
      </a>
      <div class="top3-body">
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:var(--muted)">
          <span>${m.d}</span>
          <a class="top3-link" href="${m.permalink||'#'}" target="_blank" rel="noopener">Ver en IG ↗</a>
        </div>
        <div class="top3-cap">${m.caption || '(Sin texto)'}</div>
        <div class="top3-stats">
          <div><strong>${fmtNum(m.interactions)}</strong>Interacc.</div>
          <div><strong>${fmtNum(m.views)}</strong>Visualiz.</div>
          <div><strong>${fmtNum(m.reach)}</strong>Alcance</div>
        </div>
        <div style="font-size:11px;color:var(--muted);text-align:center">♥ ${m.likes} · 💬 ${m.comments} · 🔖 ${m.saved} · ↗ ${m.shares}</div>
      </div>
    </div>
  `).join('') : '<div class="card">No hay publicaciones en este rango.</div>';

  document.getElementById('ig-media-table').innerHTML = `
    <thead><tr><th>Contenido</th><th>Fecha</th><th>Tipo</th><th class="num">Alcance</th><th class="num">Visualiz.</th><th class="num">Likes</th><th class="num">Comentarios</th><th class="num">Guardados</th><th class="num">Comp.</th><th class="num">Interacc.</th></tr></thead>
    <tbody>${mediaList.map(m => `
      <tr>
        <td>
          <div class="ad-cell">
            ${m.thumb ? `<a href="${m.permalink||'#'}" target="_blank" rel="noopener"><img class="thumb" src="${m.thumb}" alt=""></a>` : ''}
            <span>${(m.caption||'(Sin texto)').slice(0,60)}${(m.caption||'').length>60?'...':''}</span>
          </div>
        </td>
        <td style="white-space:nowrap">${m.d}</td>
        <td><span class="tag ig">${m.type}</span></td>
        <td class="num">${fmtNum(m.reach)}</td>
        <td class="num">${fmtNum(m.views)}</td>
        <td class="num">${fmtNum(m.likes)}</td>
        <td class="num">${fmtNum(m.comments)}</td>
        <td class="num">${fmtNum(m.saved)}</td>
        <td class="num">${fmtNum(m.shares)}</td>
        <td class="num"><strong>${fmtNum(m.interactions)}</strong></td>
      </tr>
    `).join('')}</tbody>
  `;

  const allStories = (P.organic.instagram.stories || []);
  const stRange = allStories.filter(x => x.d >= s && x.d <= e);
  const stUse = stRange.length ? stRange : allStories;
  const stTop = stUse.slice().sort((a,b) => (b.views - a.views) || (b.reach - a.reach)).slice(0, 10);
  const stBot = stUse.filter(x => x.views > 0).sort((a,b) => (a.views - b.views) || (a.reach - b.reach)).slice(0, 10);

  const renderStoryTable = list => list.length ? `
    <thead><tr><th>Historia</th><th>Fecha</th><th class="num">Alcance</th><th class="num">Visualiz.</th><th class="num">Resp.</th><th class="num">Comp.</th></tr></thead>
    <tbody>${list.map(x => `
      <tr>
        <td><div class="ad-cell">${x.thumb?`<img class="thumb" src="${x.thumb}" alt="">`:''}<span>${x.caption||'<em style="color:var(--muted)">Sin texto</em>'}</span></div></td>
        <td style="white-space:nowrap">${x.ts||x.d}</td>
        <td class="num">${fmtNum(x.reach)}</td>
        <td class="num"><strong>${fmtNum(x.views)}</strong></td>
        <td class="num">${fmtNum(x.replies)}</td>
        <td class="num">${fmtNum(x.shares)}</td>
      </tr>
    `).join('')}</tbody>
  ` : '<tbody><tr><td style="color:var(--muted);padding:14px">Todavía no hay historias registradas en este rango (el archivo automático acumula desde el 25/11/2026 cada 8h).</td></tr></tbody>';

  document.getElementById('ig-stories-top-table').innerHTML = renderStoryTable(stTop);
  document.getElementById('ig-stories-bottom-table').innerHTML = renderStoryTable(stBot);
}

// Static Regions & Organic summary
document.getElementById('meta-region-table').innerHTML = `
  <thead><tr><th>Región</th><th class="num">Inversión</th><th class="num">Clics</th></tr></thead>
  <tbody>${(META.regions||[]).slice(0,10).map(r => `<tr><td><strong>${r.region}</strong></td><td class="num">${fmtARS(r.spend)}</td><td class="num">${fmtNum(r.clicks)}</td></tr>`).join('')}</tbody>
`;

const ig = P.organic.instagram, fb = P.organic.facebook, igIns = ig.insights_summary || {};
document.getElementById('org-sub').textContent = `Resumen cuenta últimos 30d (${P.organic.period.since}..${P.organic.period.until}) · Contenidos e historias filtrados por tu selector`;
document.getElementById('org-kpis').innerHTML = [
  { l:'IG Seguidores actuales', v:fmtNum(ig.profile.followers_count), s:'@'+ig.profile.username },
  { l:'IG Visualizaciones (30d)', v:fmtNum(igIns.views), s:`Alcance: ${fmtNum(igIns.reach)}` },
  { l:'IG Interacciones (30d)', v:fmtNum(igIns.total_interactions), s:`Cuentas: ${fmtNum(igIns.accounts_engaged)}` },
  { l:'FB Seguidores actuales', v:fmtNum(fb.page.followers_count), s:fb.page.name }
].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>${k.s}</span></div></div>`).join('');

// Presets
function applyPreset(name) {
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.toggle('active', b.dataset.preset === name));
  const endDt = parseISO(maxDate);
  if (name === 'this_month') {
    dtStart.value = toISO(new Date(endDt.getFullYear(), endDt.getMonth(), 1));
    dtEnd.value = maxDate;
  } else if (name === 'last_7') {
    dtStart.value = addDays(maxDate, -6); dtEnd.value = maxDate;
  } else if (name === 'last_14') {
    dtStart.value = addDays(maxDate, -13); dtEnd.value = maxDate;
  } else if (name === 'last_30') {
    dtStart.value = addDays(maxDate, -29); dtEnd.value = maxDate;
  } else if (name === 'last_month') {
    const firstCur = new Date(endDt.getFullYear(), endDt.getMonth(), 1);
    const lastPrev = new Date(firstCur - 86400000);
    dtStart.value = toISO(new Date(lastPrev.getFullYear(), lastPrev.getMonth(), 1));
    dtEnd.value = toISO(lastPrev);
  } else if (name === 'all') {
    dtStart.value = minDate; dtEnd.value = maxDate;
  }
  renderAll();
}

document.querySelectorAll('.preset-btn').forEach(b => b.addEventListener('click', () => applyPreset(b.dataset.preset)));
[dtStart, dtEnd].forEach(el => el.addEventListener('change', () => {
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  renderAll();
}));
[cmpEnabled, cmpMode, cmpStart, cmpEnd].forEach(el => el.addEventListener('change', renderAll));

applyPreset('this_month');
</script>
</body>
</html>
"""


def main() -> None:
    meta_path = DATA_DIR / "meta_daily.json"
    if not meta_path.exists():
        raise SystemExit("Falta data/meta_daily.json. Corre fetch_meta_data.py primero.")
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    google_path = DATA_DIR / "google_ads.json"
    if google_path.exists():
        payload["google_ads"] = json.loads(google_path.read_text(encoding="utf-8"))

    html = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", json.dumps(payload, ensure_ascii=False))
    out_html = BASE_DIR / "dashboard.html"
    out_html.write_text(html, encoding="utf-8")
    print(f"Dashboard interactivo generado: {out_html} ({round(out_html.stat().st_size/1024, 1)} KB)")


if __name__ == "__main__":
    main()
