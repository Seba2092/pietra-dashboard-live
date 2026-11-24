"""Genera dashboard.html en vivo a partir de los JSON extraídos de Meta (y Google cuando esté conectado)."""

import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Joyería Pietra · Dashboard Live (API)</title>
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
  .hero{background:linear-gradient(135deg,#141414 0%,#231f18 65%,#2f281a 100%);color:#f8f5ef;padding:34px 24px 28px;border-bottom:3px solid var(--gold)}
  .container{max-width:1280px;margin:0 auto;padding:0 20px}
  .hero-top{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:18px}
  .brand{display:flex;align-items:center;gap:16px}
  .brand-mark{width:52px;height:52px;border-radius:12px;border:1.5px solid var(--gold);display:grid;place-items:center;font-family:'Cormorant Garamond',serif;font-size:26px;font-weight:700;color:var(--gold);background:rgba(201,162,39,.08)}
  .brand h1{font-family:'Cormorant Garamond',serif;font-size:32px;font-weight:600;letter-spacing:.04em}
  .brand p{color:#cfc7b8;font-size:13px;margin-top:3px}
  .hero-badges{display:flex;flex-wrap:wrap;gap:8px}
  .pill{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:500;background:rgba(255,255,255,.08);color:#f4f1eb;border:1px solid rgba(255,255,255,.14)}
  .pill .dot{width:7px;height:7px;border-radius:50%}
  .nav-bar{background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:40}
  .nav-inner{max-width:1280px;margin:0 auto;padding:10px 20px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between}
  .nav-links{display:flex;flex-wrap:wrap;gap:6px}
  .nav-links a{text-decoration:none;color:var(--muted);font-size:12.5px;font-weight:600;padding:7px 13px;border-radius:999px}
  .nav-links a:hover{background:var(--bg2);color:var(--ink)}
  .nav-links a.active{background:var(--ink);color:#fff}
  section{padding:32px 0 10px}
  .sec-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:12px;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid var(--line)}
  .sec-title{display:flex;align-items:center;gap:10px}
  .sec-accent{width:4px;height:26px;border-radius:4px;background:var(--gold)}
  .sec-title h2{font-family:'Cormorant Garamond',serif;font-size:28px;font-weight:600}
  .sec-sub{font-size:12.5px;color:var(--muted)}
  .kpi-grid-4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
  .grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:18px}
  @media(max-width:1000px){.kpi-grid-4{grid-template-columns:repeat(2,1fr)}}
  @media(max-width:860px){.grid-2{grid-template-columns:1fr}}
  .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow)}
  .kpi-card{padding:16px 17px}
  .kpi-label{font-size:11.5px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
  .kpi-val{font-size:24px;font-weight:700;margin:6px 0 8px;letter-spacing:-.02em}
  .kpi-foot{display:flex;align-items:center;justify-content:space-between;font-size:11.5px;color:var(--muted)}
  .delta{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:999px;font-weight:600;font-size:11px}
  .delta.up{background:var(--up-bg);color:var(--up)}
  .delta.down{background:var(--down-bg);color:var(--down)}
  .card-title{font-size:14.5px;font-weight:700;margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;gap:8px}
  .card-sub{font-size:12px;color:var(--muted);margin-bottom:14px}
  .chart-wrap{position:relative;height:270px;width:100%}
  .funnel-list{display:flex;flex-direction:column;gap:10px}
  .funnel-row{display:grid;grid-template-columns:140px 1fr 118px;align-items:center;gap:12px}
  .funnel-lbl{font-size:12.5px;font-weight:600}
  .funnel-bar-bg{height:26px;background:var(--bg);border-radius:8px;overflow:hidden;border:1px solid var(--line)}
  .funnel-bar{height:100%;border-radius:7px;background:linear-gradient(90deg,var(--meta),#4e95f7)}
  .funnel-num{text-align:right;font-size:12.5px;font-weight:600}
  .funnel-num small{display:block;font-size:11px;font-weight:500;color:var(--muted)}
  .table-wrap{overflow-x:auto}
  table{width:100%;border-collapse:collapse;font-size:12.8px}
  th{text-align:left;padding:10px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border-bottom:2px solid var(--line);white-space:nowrap}
  td{padding:10px;border-bottom:1px solid var(--line);vertical-align:middle}
  tr:last-child td{border-bottom:none}
  .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;background:var(--bg2)}
  .tag.gold{background:var(--gold-soft);color:var(--gold-deep)}
  .tag.meta{background:rgba(24,119,242,.10);color:var(--meta)}
  .tag.ig{background:rgba(225,48,108,.10);color:var(--instagram)}
  .ad-cell{display:flex;align-items:center;gap:10px}
  .thumb{width:42px;height:42px;border-radius:8px;object-fit:cover;border:1px solid var(--line);cursor:pointer;flex-shrink:0}
  .pending-box{padding:24px;border:1.5px dashed var(--line);border-radius:12px;background:var(--bg);color:var(--muted);text-align:center}
  .pending-box strong{color:var(--ink);display:block;margin-bottom:4px}
  footer{margin-top:40px;padding:24px 20px 36px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;text-align:center}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="hero-top">
      <div class="brand">
        <div class="brand-mark">P</div>
        <div>
          <h1>PIETRA <span style="color:var(--gold);font-weight:500">· LIVE API</span></h1>
          <p id="hero-sub">Dashboard Automatizado · Cargando período...</p>
        </div>
      </div>
      <div class="hero-badges">
        <span class="pill"><span class="dot" style="background:var(--up)"></span>Meta API Conectada</span>
        <span class="pill"><span class="dot" style="background:var(--instagram)"></span>IG Graph API Conectada</span>
        <span class="pill" id="google-status-pill"><span class="dot" style="background:var(--gold)"></span>Google Ads: Pendiente de permiso</span>
      </div>
    </div>
  </div>
</header>

<nav class="nav-bar">
  <div class="nav-inner">
    <div class="nav-links">
      <a href="#blended" class="active">Blended</a>
      <a href="#meta">Meta Ads</a>
      <a href="#meta-geo">Semanas &amp; Regiones</a>
      <a href="#google">Google Ads</a>
      <a href="#organic">Orgánico (IG &amp; FB)</a>
    </div>
    <div style="font-size:12px;color:var(--muted)">Generado: <strong id="gen-at"></strong></div>
  </div>
</nav>

<main class="container">
  <section id="blended" style="display:none">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent"></div><h2>Resumen Ejecutivo Blended (Meta + Google)</h2></div>
      <div class="sec-sub" id="blended-period-sub"></div>
    </div>
    <div class="kpi-grid-4" id="blended-kpis"></div>
  </section>

  <section id="meta">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent" style="background:var(--meta)"></div><h2>Meta Ads · Rendimiento General</h2></div>
      <div class="sec-sub" id="meta-period-sub"></div>
    </div>
    <div class="kpi-grid-4" id="meta-kpis"></div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Embudo de Conversión</div>
        <div class="card-sub">Impresiones → Clics → Landing → Carrito → Pagos → Compras</div>
        <div class="funnel-list" id="meta-funnel"></div>
      </div>
      <div class="card">
        <div class="card-title">Campañas del Período</div>
        <div class="card-sub">Ordenadas por inversión publicitaria</div>
        <div class="table-wrap"><table id="meta-campaigns-table"></table></div>
      </div>
    </div>
  </section>

  <section id="meta-geo">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent"></div><h2>Evolución Semanal &amp; Desglose por Región</h2></div>
      <div class="sec-sub">Módulos exclusivos del proyecto principal vía Meta Marketing API</div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">Evolución Semanal (Inversión vs. Facturación)</div>
        <div class="card-sub">Cortes semanales (`time_increment=7`)</div>
        <div class="chart-wrap"><canvas id="chartWeekly"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Top 10 Regiones por Facturación / Compras</div>
        <div class="card-sub">Desglose geográfico oficial (`breakdowns=region`)</div>
        <div class="table-wrap"><table id="meta-region-table"></table></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Distribución por Edad</div>
        <div class="card-sub">Compras e inversión por rango etario</div>
        <div class="chart-wrap"><canvas id="chartAge"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Top Anuncios &amp; Creativos (API Live)</div>
        <div class="card-sub">Top 10 por compras e inversión</div>
        <div class="table-wrap"><table id="meta-ads-table"></table></div>
      </div>
    </div>
  </section>

  <section id="organic">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent" style="background:var(--instagram)"></div><h2>Orgánico · Instagram &amp; Facebook (Graph API)</h2></div>
      <div class="sec-sub">Métricas oficiales de cuenta y publicaciones del período</div>
    </div>
    <div class="kpi-grid-4" id="org-kpis"></div>
    <div class="card" style="margin-top:18px">
      <div class="card-title">Publicaciones y Reels de Instagram en el Período</div>
      <div class="card-sub">Ordenados cronológicamente con likes, comentarios y tipo</div>
      <div class="table-wrap"><table id="ig-media-table"></table></div>
    </div>
  </section>

  <section id="google">
    <div class="sec-head">
      <div class="sec-title"><div class="sec-accent" style="background:var(--google)"></div><h2>Google Ads · Search &amp; Performance Max</h2></div>
      <div class="sec-sub">Integración vía Google Ads Scripts → Google Sheets</div>
    </div>
    <div class="card" id="google-container"></div>
  </section>
</main>

<footer>Joyería Pietra · Proyecto Principal Live API · Meta Marketing API + Instagram/Facebook Graph API</footer>

<script>
const PAYLOAD = __PAYLOAD_JSON__;

const fmtARS = v => '$' + Math.round(v || 0).toLocaleString('es-AR');
const fmtNum = (v, d=0) => Number(v || 0).toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d });
const deltaBadge = (cur, prev, inv=false) => {
  if (!prev) return '<span class="delta">—</span>';
  const d = ((cur - prev) / prev) * 100;
  const good = inv ? d < 0 : d >= 0;
  return `<span class="delta ${good?'up':'down'}">${d>=0?'▲':'▼'} ${d>=0?'+':''}${d.toFixed(1).replace('.',',')}%</span>`;
};

const cur = PAYLOAD.meta_ads.current;
const prev = PAYLOAD.meta_ads.previous;
const aC = cur.account, aP = prev.account;

document.getElementById('hero-sub').textContent = `Período actual: ${cur.period.since} al ${cur.period.until} vs. ${prev.period.since} al ${prev.period.until}`;
document.getElementById('gen-at').textContent = PAYLOAD.generated_at;
document.getElementById('meta-period-sub').textContent = `${cur.period.since}..${cur.period.until} vs. ${prev.period.since}..${prev.period.until}`;

document.getElementById('meta-kpis').innerHTML = [
  { l:'Inversión Meta', v:fmtARS(aC.spend), p:fmtARS(aP.spend), b:deltaBadge(aC.spend,aP.spend) },
  { l:'Facturación Meta', v:fmtARS(aC.revenue), p:fmtARS(aP.revenue), b:deltaBadge(aC.revenue,aP.revenue) },
  { l:'Compras', v:fmtNum(aC.purchases), p:fmtNum(aP.purchases), b:deltaBadge(aC.purchases,aP.purchases) },
  { l:'ROAS Total', v:fmtNum(aC.roas,2)+'×', p:fmtNum(aP.roas,2)+'×', b:deltaBadge(aC.roas,aP.roas) },
  { l:'CPA Total', v:fmtARS(aC.cpa), p:fmtARS(aP.cpa), b:deltaBadge(aC.cpa,aP.cpa,true) },
  { l:'Clics en Enlace', v:fmtNum(aC.link_clicks), p:fmtNum(aP.link_clicks), b:deltaBadge(aC.link_clicks,aP.link_clicks) },
  { l:'CTR Enlace', v:fmtNum(aC.ctr_link,2)+'%', p:fmtNum(aP.ctr_link,2)+'%', b:deltaBadge(aC.ctr_link,aP.ctr_link) },
  { l:'AOV Meta', v:fmtARS(aC.aov), p:fmtARS(aP.aov), b:deltaBadge(aC.aov,aP.aov) }
].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>Ant: ${k.p}</span>${k.b}</div></div>`).join('');

const funnelSteps = [
  { l:'Impresiones', v:aC.impressions, s:'100%' },
  { l:'Clics en enlace', v:aC.link_clicks, s:fmtNum(aC.ctr_link,2)+'% CTR' },
  { l:'Visitas a landing', v:aC.landing_views, s:fmtNum(aC.link_clicks?aC.landing_views/aC.link_clicks*100:0,1)+'% de clics' },
  { l:'Agregar al carrito', v:aC.add_to_cart, s:fmtNum(aC.landing_views?aC.add_to_cart/aC.landing_views*100:0,1)+'% de visitas' },
  { l:'Pagos iniciados', v:aC.initiate_checkout, s:fmtNum(aC.add_to_cart?aC.initiate_checkout/aC.add_to_cart*100:0,1)+'% de ATC' },
  { l:'Compras', v:aC.purchases, s:fmtNum(aC.initiate_checkout?aC.purchases/aC.initiate_checkout*100:0,1)+'% de pagos' }
];
const fMax = Math.log10(Math.max(10, funnelSteps[0].v));
document.getElementById('meta-funnel').innerHTML = funnelSteps.map((f,i) => {
  const w = i===0 ? 100 : Math.max(8, Math.log10(Math.max(1,f.v))/fMax*100);
  return `<div class="funnel-row"><div class="funnel-lbl">${f.l}</div><div class="funnel-bar-bg"><div class="funnel-bar" style="width:${w.toFixed(1)}%"></div></div><div class="funnel-num">${fmtNum(f.v)}<small>${f.s}</small></div></div>`;
}).join('');

document.getElementById('meta-campaigns-table').innerHTML = `
  <thead><tr><th>Campaña</th><th class="num">Inversión</th><th class="num">Compras</th><th class="num">Facturación</th><th class="num">ROAS</th></tr></thead>
  <tbody>${cur.campaigns.map(c => `<tr><td><strong>${c.campaign_name}</strong></td><td class="num">${fmtARS(c.spend)}</td><td class="num">${c.purchases}</td><td class="num">${fmtARS(c.revenue)}</td><td class="num"><span class="tag gold">${fmtNum(c.roas,2)}×</span></td></tr>`).join('')}</tbody>
`;

const regions = (cur.region || []).slice(0, 10);
document.getElementById('meta-region-table').innerHTML = `
  <thead><tr><th>Región</th><th class="num">Inversión</th><th class="num">Clics</th><th class="num">Compras</th><th class="num">Facturación</th><th class="num">ROAS</th></tr></thead>
  <tbody>${regions.map(r => `<tr><td><strong>${r.region}</strong></td><td class="num">${fmtARS(r.spend)}</td><td class="num">${fmtNum(r.link_clicks)}</td><td class="num"><strong>${r.purchases}</strong></td><td class="num">${fmtARS(r.revenue)}</td><td class="num"><span class="tag meta">${fmtNum(r.roas,2)}×</span></td></tr>`).join('')}</tbody>
`;

const topAds = (cur.top_ads || []).slice(0, 10);
document.getElementById('meta-ads-table').innerHTML = `
  <thead><tr><th>Anuncio</th><th class="num">Inversión</th><th class="num">Compras</th><th class="num">ROAS</th></tr></thead>
  <tbody>${topAds.map(a => `<tr><td><div class="ad-cell">${a.thumbnail_url?`<img class="thumb" src="${a.thumbnail_url}" alt="">`:''}<strong>${a.ad_name}</strong></div></td><td class="num">${fmtARS(a.spend)}</td><td class="num"><strong>${a.purchases}</strong></td><td class="num"><span class="tag gold">${fmtNum(a.roas,2)}×</span></td></tr>`).join('')}</tbody>
`;

// Weekly Chart
const wk = cur.weekly || [];
new Chart(document.getElementById('chartWeekly'), {
  type: 'bar',
  data: {
    labels: wk.map(w => `${w.date_start.slice(5)}..${w.date_stop.slice(5)}`),
    datasets: [
      { label: 'Inversión (k ARS)', data: wk.map(w => +(w.spend/1000).toFixed(1)), backgroundColor: '#c9a227', borderRadius: 6, yAxisID: 'y' },
      { label: 'Facturación (M ARS)', data: wk.map(w => +(w.revenue/1e6).toFixed(2)), backgroundColor: '#1877F2', borderRadius: 6, yAxisID: 'y1' }
    ]
  },
  options: { responsive:true, maintainAspectRatio:false, scales:{ y:{beginAtZero:true,position:'left'}, y1:{beginAtZero:true,position:'right',grid:{drawOnChartArea:false}} }, plugins:{legend:{position:'bottom'}} }
});

// Age Chart
const ages = (cur.age || []).slice().sort((a,b) => a.age.localeCompare(b.age));
new Chart(document.getElementById('chartAge'), {
  type: 'bar',
  data: {
    labels: ages.map(a => a.age),
    datasets: [
      { label: 'Compras', data: ages.map(a => a.purchases), backgroundColor: '#1877F2', borderRadius: 6, yAxisID: 'y' },
      { label: 'Inversión (k ARS)', data: ages.map(a => +(a.spend/1000).toFixed(1)), backgroundColor: '#c9a227', borderRadius: 6, yAxisID: 'y1' }
    ]
  },
  options: { responsive:true, maintainAspectRatio:false, scales:{ y:{beginAtZero:true,position:'left'}, y1:{beginAtZero:true,position:'right',grid:{drawOnChartArea:false}} }, plugins:{legend:{position:'bottom'}} }
});

// Organic
const ig = PAYLOAD.organic.instagram;
const fb = PAYLOAD.organic.facebook;
const igIns = ig.insights_summary || {};
document.getElementById('org-kpis').innerHTML = [
  { l:'IG Seguidores actuales', v:fmtNum(ig.profile.followers_count), s:'@'+ig.profile.username },
  { l:'IG Visualizaciones (período)', v:fmtNum(igIns.views), s:`Alcance: ${fmtNum(igIns.reach)}` },
  { l:'IG Interacciones totales', v:fmtNum(igIns.total_interactions), s:`Cuentas: ${fmtNum(igIns.accounts_engaged)}` },
  { l:'FB Seguidores actuales', v:fmtNum(fb.page.followers_count), s:fb.page.name }
].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>${k.s}</span></div></div>`).join('');

document.getElementById('ig-media-table').innerHTML = `
  <thead><tr><th>Fecha</th><th>Tipo</th><th>Caption</th><th class="num">Likes</th><th class="num">Comentarios</th></tr></thead>
  <tbody>${(ig.media || []).map(m => `<tr><td>${(m.timestamp||'').slice(0,10)}</td><td><span class="tag ig">${m.media_product_type||m.media_type}</span></td><td>${(m.caption||'').slice(0,75)}...</td><td class="num">${fmtNum(m.like_count)}</td><td class="num">${fmtNum(m.comments_count)}</td></tr>`).join('')}</tbody>
`;

// Google placeholder or live
const gContainer = document.getElementById('google-container');
if (!PAYLOAD.google_ads) {
  gContainer.innerHTML = `<div class="pending-box"><strong>Módulo Google Ads listo para conectar</strong>Cuando tengas el permiso en Google Ads Scripts → Google Sheets, guardamos el JSON en <code>data/google_ads.json</code> y esta sección se completa automáticamente en la próxima corrida.</div>`;
} else {
  const gCur = PAYLOAD.google_ads.current;
  const gA = gCur.account;
  document.getElementById('google-status-pill').innerHTML = '<span class="dot" style="background:var(--up)"></span>Google Ads Conectado';

  // Blended section
  const bSpend = (aC.spend || 0) + (gA.spend || 0);
  const bRev = (aC.revenue || 0) + (gA.revenue || 0);
  const bPurch = (aC.purchases || 0) + (gA.conversions || 0);
  const bRoas = bSpend ? bRev / bSpend : 0;
  const bCpa = bPurch ? bSpend / bPurch : 0;
  const bAov = bPurch ? bRev / bPurch : 0;
  document.getElementById('blended').style.display = 'block';
  document.getElementById('blended-period-sub').textContent = `Consolidado Paid Media · ${cur.period.since}..${cur.period.until}`;
  document.getElementById('blended-kpis').innerHTML = [
    { l:'Inversión Total', v:fmtARS(bSpend), s:`Meta ${fmtNum(bSpend?aC.spend/bSpend*100:0,1)}% · Google ${fmtNum(bSpend?gA.spend/bSpend*100:0,1)}%` },
    { l:'Facturación Atribuida', v:fmtARS(bRev), s:`Meta ${fmtARS(aC.revenue)} · Google ${fmtARS(gA.revenue)}` },
    { l:'ROAS Blended', v:fmtNum(bRoas,2)+'×', s:`Compras/Conv: ${fmtNum(bPurch,1)}` },
    { l:'CPA / AOV Blended', v:fmtARS(bCpa), s:`Ticket promedio: ${fmtARS(bAov)}` }
  ].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>${k.s}</span></div></div>`).join('');

  gContainer.outerHTML = `
    <div class="kpi-grid-4">
      ${[
        { l:'Inversión Google', v:fmtARS(gA.spend), s:`Impr: ${fmtNum(gA.impressions)}` },
        { l:'Valor de Conversión', v:fmtARS(gA.revenue), s:`AOV: ${fmtARS(gA.conversions?gA.revenue/gA.conversions:0)}` },
        { l:'Conversiones', v:fmtNum(gA.conversions,2), s:`CPA: ${fmtARS(gA.cpa)}` },
        { l:'ROAS Google', v:fmtNum(gA.roas,2)+'×', s:`CTR: ${fmtNum(gA.ctr,2)}% · CPC: ${fmtARS(gA.cpc)}` }
      ].map(k => `<div class="card kpi-card"><div class="kpi-label">${k.l}</div><div class="kpi-val">${k.v}</div><div class="kpi-foot"><span>${k.s}</span></div></div>`).join('')}
    </div>
    <div class="card" style="margin-top:18px">
      <div class="card-title">Campañas de Google Ads (${gCur.period.since}..${gCur.period.until})</div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Campaña</th><th class="num">Inversión</th><th class="num">Clics</th><th class="num">CTR</th><th class="num">Conv.</th><th class="num">CPA</th><th class="num">Valor Conv.</th><th class="num">ROAS</th></tr></thead>
          <tbody>${(gCur.campaigns||[]).map(c => `<tr><td><strong>${c.key}</strong></td><td class="num">${fmtARS(c.spend)}</td><td class="num">${fmtNum(c.clicks)}</td><td class="num">${fmtNum(c.ctr,2)}%</td><td class="num"><strong>${fmtNum(c.conversions,2)}</strong></td><td class="num">${fmtARS(c.cpa)}</td><td class="num">${fmtARS(c.revenue)}</td><td class="num"><span class="tag meta">${fmtNum(c.roas,2)}×</span></td></tr>`).join('')}</tbody>
        </table>
      </div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">Top Palabras Clave (Search)</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Palabra Clave</th><th class="num">Clics</th><th class="num">Inversión</th><th class="num">Conv.</th><th class="num">CPA</th></tr></thead>
            <tbody>${(gCur.keywords||[]).slice(0,10).map(k => `<tr><td><code>${k.key}</code></td><td class="num">${fmtNum(k.clicks)}</td><td class="num">${fmtARS(k.spend)}</td><td class="num"><strong>${fmtNum(k.conversions,2)}</strong></td><td class="num">${k.cpa?fmtARS(k.cpa):'—'}</td></tr>`).join('')}</tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Top 10 Productos Convertidores (PMax / Shopping)</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Producto</th><th class="num">Clics</th><th class="num">Conv.</th><th class="num">Valor Conv.</th></tr></thead>
            <tbody>${(gCur.products||[]).slice(0,10).map(p => `<tr><td><strong>${p.key}</strong></td><td class="num">${fmtNum(p.clicks)}</td><td class="num">${fmtNum(p.conversions,2)}</td><td class="num"><strong>${fmtARS(p.revenue)}</strong></td></tr>`).join('')}</tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta-json", help="Ruta al JSON generado por fetch_meta_data.py")
    args = parser.parse_args()

    if args.meta_json:
        meta_path = Path(args.meta_json)
    else:
        files = sorted(DATA_DIR.glob("meta_*.json"))
        if not files:
            raise SystemExit("No hay archivos data/meta_*.json. Corre primero fetch_meta_data.py.")
        meta_path = files[-1]

    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    google_path = DATA_DIR / "google_ads.json"
    if google_path.exists():
        payload["google_ads"] = json.loads(google_path.read_text(encoding="utf-8"))

    html = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", json.dumps(payload, ensure_ascii=False))
    out_html = BASE_DIR / "dashboard.html"
    out_html.write_text(html, encoding="utf-8")
    print(f"Dashboard generado en: {out_html} (desde {meta_path.name})")


if __name__ == "__main__":
    main()
