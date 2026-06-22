import json, base64, os, subprocess, sys
from datetime import datetime

# Funciona tanto no Mac local quanto no GitHub Actions (CI)
_LOCAL = '/Users/lucaspontes/Documents/Trabalho/Endocommerce/Sistema Future'
PASTA  = _LOCAL if os.path.exists(_LOCAL) else os.path.dirname(os.path.abspath(__file__))

def b64img(path):
    if not os.path.exists(path): return None
    ext = path.split('.')[-1].lower()
    mime = {'jpg':'jpeg','jpeg':'jpeg','png':'png'}.get(ext,'jpeg')
    with open(path,'rb') as f: data = base64.b64encode(f.read()).decode()
    return f"data:image/{mime};base64,{data}"

logo_candidates = [
    os.path.join(PASTA, 'logo.jpeg'),
    '/Users/lucaspontes/Documents/Trabalho/Endocommerce/Logomarca/logo.jpeg',
    '/Users/lucaspontes/Downloads/file.jpeg',
]
endo_b64 = next((b64img(p) for p in logo_candidates if b64img(p)), None)

with open(os.path.join(PASTA, 'base_produtos.json')) as f:
    base = json.load(f)

ativos = [p for p in base['produtos'].values() if p.get('preco_tiny',0) > 0]
prods_js = json.dumps(ativos, ensure_ascii=False)
gen_date = base.get('gerado_em','')[:10]
total_prods = len(ativos)
com_precos = sum(1 for p in ativos if p.get('tem_precos'))
sem_precos = total_prods - com_precos
total_est = sum(p.get('est',0) for p in ativos)
val_est = sum(p.get('est',0) * p.get('custo',0) for p in ativos)
val_venda = sum(p.get('est',0) * p.get('pvenda', p.get('preco_tiny',0)) for p in ativos)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sistema Future — Endocommerce</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --red:#8B1010;--red2:#6d0c0c;--red-light:#fff5f5;
  --blue:#1e40af;--blue-light:#eff6ff;
  --green:#15803d;--green-light:#f0fdf4;
  --amber:#b45309;--amber-light:#fffbeb;
  --gray:#f8fafc;--border:#e2e8f0;--border2:#f1f5f9;
  --text:#111827;--sub:#6b7280;--sub2:#9ca3af;
  --shadow:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.05);
  --shadow-md:0 4px 12px rgba(0,0,0,.08),0 2px 4px rgba(0,0,0,.05);
}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Inter',Arial,sans-serif;background:#f1f5f9;color:var(--text);min-height:100vh;font-size:13px;line-height:1.5;-webkit-font-smoothing:antialiased}}

/* ── TOP BAR ─────────────────────────────────────────────── */
.topbar{{background:#fff;border-bottom:2px solid var(--red);padding:0 32px;display:flex;align-items:center;gap:0;position:sticky;top:0;z-index:200;box-shadow:var(--shadow);height:56px}}
.logo-endo{{height:36px;object-fit:contain;margin-right:18px}}
.logo-sep{{width:1px;height:30px;background:var(--border);margin-right:18px}}
.sys-title{{font-size:14px;font-weight:800;color:var(--text);letter-spacing:-.3px;line-height:1.2}}
.sys-sub{{font-size:10.5px;color:var(--sub);font-weight:400;margin-top:1px}}
.topbar-right{{margin-left:auto;display:flex;align-items:center;gap:10px}}
.badge-date{{font-size:11px;color:var(--sub);background:var(--gray);border:1px solid var(--border);border-radius:20px;padding:4px 12px;font-weight:500}}
.btn-update{{background:var(--red);color:#fff;border:none;border-radius:8px;padding:7px 16px;font-size:12px;font-weight:700;cursor:pointer;letter-spacing:.2px;transition:background .15s}}
.btn-update:hover{{background:var(--red2)}}

/* ── TABS ────────────────────────────────────────────────── */
.tabs{{background:#fff;border-bottom:1px solid var(--border);padding:0 32px;display:flex;gap:0}}
.tab{{padding:14px 20px;font-size:12.5px;font-weight:600;color:var(--sub);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;white-space:nowrap;transition:color .15s,border-color .15s;display:flex;align-items:center;gap:6px}}
.tab:hover{{color:var(--red);background:#fafafa}}
.tab.active{{color:var(--red);border-bottom-color:var(--red);background:#fff}}
.tab-icon{{width:14px;height:14px;opacity:.7}}
.tab.active .tab-icon{{opacity:1}}

/* ── CONTENT ─────────────────────────────────────────────── */
.content{{padding:28px 32px;max-width:1440px;margin:0 auto}}
.tab-pane{{display:none}}
.tab-pane.active{{display:block}}

/* ── KPI CARDS ───────────────────────────────────────────── */
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:16px;margin-bottom:28px}}
.kpi{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:18px 20px;position:relative;overflow:hidden;box-shadow:var(--shadow);transition:box-shadow .15s,transform .15s}}
.kpi:hover{{box-shadow:var(--shadow-md);transform:translateY(-1px)}}
.kpi-accent{{position:absolute;top:0;left:0;right:0;height:3px;border-radius:14px 14px 0 0}}
.kpi-icon{{position:absolute;right:16px;top:50%;transform:translateY(-50%);opacity:.12;width:36px;height:36px}}
.kpi--mono .kpi-accent{{background:var(--blue)}}
.kpi--mono .kpi-val .rs{{color:var(--blue);opacity:.6}}
.kpi--money .kpi-accent{{background:var(--blue)}}
.kpi--money .kpi-val .rs{{color:var(--blue);opacity:.7}}
.kpi--count .kpi-accent{{background:var(--red)}}
.kpi--green .kpi-accent{{background:var(--green)}}
.kpi--green .kpi-val{{color:var(--green)}}
.kpi--warn .kpi-accent{{background:#f59e0b}}
.kpi--warn .kpi-val{{color:#b45309}}
.kpi--danger .kpi-accent{{background:var(--red)}}
.kpi--danger .kpi-val{{color:#dc2626}}
.kpi-label{{font-size:10.5px;color:var(--sub);font-weight:700;text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px}}
.kpi-val{{font-size:22px;font-weight:800;color:var(--text);line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;align-items:baseline;gap:2px}}
.kpi-val .rs{{font-size:12px;font-weight:700;letter-spacing:.3px;margin-right:1px}}
.kpi-sub{{font-size:10.5px;color:var(--sub2);margin-top:6px;font-weight:400}}

/* ── SECTION TITLES ─────────────────────────────────────── */
.sec-title{{font-size:11.5px;font-weight:800;color:var(--red);text-transform:uppercase;letter-spacing:.9px;margin-bottom:16px;display:flex;align-items:center;gap:10px}}
.sec-title::after{{content:'';flex:1;height:1px;background:linear-gradient(90deg,#8B101030,transparent)}}

/* ── TABLES ──────────────────────────────────────────────── */
.tbl-wrap{{background:#fff;border:1px solid var(--border);border-radius:12px;overflow:hidden;box-shadow:var(--shadow)}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
thead th{{background:#1a1a2e;color:#e5e7eb;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;padding:11px 14px;text-align:left;white-space:nowrap}}
thead th.r{{text-align:right}}
tbody tr{{border-bottom:1px solid var(--border2);background:#fff;transition:background .1s}}
tbody tr:nth-child(even){{background:#fafbfc}}
tbody tr:hover{{background:#f0f7ff}}
td{{padding:9px 14px;vertical-align:middle}}
.td-r{{text-align:right}}
.sku{{font-family:'SF Mono',SFMono-Regular,Consolas,monospace;font-size:11px;color:var(--sub);background:#f8fafc;padding:2px 5px;border-radius:4px;display:inline-block}}
.nome{{font-weight:500;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#1f2937}}
.preco{{font-weight:700;color:var(--red);font-variant-numeric:tabular-nums}}
.preco-abc{{font-weight:700;color:var(--blue);font-variant-numeric:tabular-nums}}
.preco-custo{{font-weight:600;color:#374151;font-variant-numeric:tabular-nums}}
.est-ok{{color:var(--green);font-weight:700}}
.est-crit{{color:#dc2626;font-weight:700}}
.est-zero{{color:var(--sub2)}}

/* ── BADGES ──────────────────────────────────────────────── */
.badge{{display:inline-flex;align-items:center;padding:3px 9px;border-radius:20px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;line-height:1.4}}
.badge-a{{background:#dcfce7;color:#166534}}
.badge-b{{background:#fef9c3;color:#854d0e}}
.badge-c{{background:#fee2e2;color:#991b1b}}
.badge-sem{{background:#f1f5f9;color:#475569}}
.badge-ok{{background:#dcfce7;color:#166534}}
.badge-crit{{background:#fee2e2;color:#991b1b}}
.badge-zero{{background:#f1f5f9;color:#475569}}
.badge-baixo{{background:#fef3c7;color:#92400e}}
/* Sort headers */
.th-sort{{cursor:pointer;user-select:none}}
.th-sort:hover{{background:#252540}}
.th-sort.sort-asc .sort-icon,.th-sort.sort-desc .sort-icon{{color:#fbbf24}}
.sort-icon{{font-size:10px;margin-left:3px;opacity:.6}}
/* Row selection */
.row-sel{{background:#eff6ff !important}}
.row-sel:hover{{background:#dbeafe !important}}

/* ── SEARCH / FILTER ─────────────────────────────────────── */
.filter-row{{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;align-items:center}}
.filter-row input,.filter-row select{{border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:12.5px;outline:none;background:#fff;transition:border-color .15s,box-shadow .15s;color:var(--text)}}
.filter-row input:focus,.filter-row select:focus{{border-color:var(--red);box-shadow:0 0 0 3px #8B101015}}
.filter-row input{{flex:1;min-width:200px}}
.filter-count{{font-size:12px;color:var(--sub);background:var(--gray);border:1px solid var(--border);border-radius:20px;padding:4px 12px;white-space:nowrap;font-weight:600}}

/* ── CHARTS ──────────────────────────────────────────────── */
.charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:28px}}
@media(max-width:800px){{.charts-grid{{grid-template-columns:1fr}}}}
.chart-box{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px 22px;box-shadow:var(--shadow)}}
.chart-title{{font-size:12px;font-weight:700;color:#374151;letter-spacing:.2px;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.chart-title::before{{content:'';width:3px;height:14px;background:var(--red);border-radius:2px;display:inline-block}}
canvas{{max-height:260px}}

/* ── KIT BUILDER ─────────────────────────────────────────── */
.kit-layout{{display:grid;grid-template-columns:320px 1fr;gap:18px}}
@media(max-width:900px){{.kit-layout{{grid-template-columns:1fr}}}}
.kit-left{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:12px;max-height:72vh;overflow:hidden;box-shadow:var(--shadow)}}
.kit-right{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:18px;display:flex;flex-direction:column;gap:14px;box-shadow:var(--shadow)}}
.prod-list-kit{{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:2px}}
.prod-list-kit::-webkit-scrollbar{{width:4px}}
.prod-list-kit::-webkit-scrollbar-track{{background:var(--border2)}}
.prod-list-kit::-webkit-scrollbar-thumb{{background:var(--border);border-radius:4px}}
.prod-item-kit{{display:flex;align-items:center;justify-content:space-between;padding:7px 9px;border-radius:8px;cursor:pointer;border:1px solid transparent;transition:all .12s}}
.prod-item-kit:hover{{background:#fff5f5;border-color:#8B101025}}
.prod-item-kit.in{{background:#fef2f2;border-color:#fca5a5}}
.pi-nome{{font-size:11.5px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:190px;color:#1f2937}}
.pi-meta{{font-size:10px;color:var(--sub2);margin-top:1px}}
.pi-price{{font-size:12px;font-weight:700;color:var(--red);white-space:nowrap}}
.btn-sm{{background:var(--red);color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer;transition:background .12s}}
.btn-sm:hover{{background:var(--red2)}}
.kit-name-input{{width:100%;border:1.5px solid var(--border);border-radius:10px;padding:9px 13px;font-size:14px;font-weight:700;outline:none;transition:border-color .15s;color:var(--text)}}
.kit-name-input:focus{{border-color:var(--red);box-shadow:0 0 0 3px #8B101012}}
.desc-row{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:var(--gray);border:1px solid var(--border2);border-radius:10px;padding:10px 12px}}
.desc-row label{{font-size:11.5px;color:var(--sub);font-weight:700;text-transform:uppercase;letter-spacing:.4px}}
.desc-input{{width:65px;border:1px solid var(--border);border-radius:8px;padding:6px 8px;font-size:13px;text-align:center;outline:none;font-weight:700}}
.kit-totals{{background:linear-gradient(135deg,#fff5f5 0%,#fff 100%);border:1px solid #fdd;border-radius:12px;padding:14px 18px}}
.tot-row{{display:flex;justify-content:space-between;font-size:13px;color:var(--sub);margin-bottom:5px;align-items:center}}
.tot-row.final{{font-size:16px;font-weight:800;color:var(--red);border-top:1px solid #fca5a560;padding-top:10px;margin-top:6px}}
.kit-actions{{display:flex;gap:10px}}
.btn-main{{background:var(--red);color:#fff;border:none;border-radius:9px;padding:10px 20px;font-size:13px;font-weight:700;cursor:pointer;transition:background .15s,box-shadow .15s;letter-spacing:.2px}}
.btn-main:hover{{background:var(--red2);box-shadow:0 4px 12px #8B101030}}
.btn-sec{{background:var(--blue);color:#fff;border:none;border-radius:9px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer;transition:background .15s}}
.btn-sec:hover{{background:#1e3a8a}}
.btn-danger{{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;border-radius:9px;padding:10px 14px;font-size:12px;font-weight:700;cursor:pointer;transition:all .15s}}
.btn-danger:hover{{background:#fecaca}}
.qt-ctrl{{display:flex;align-items:center;gap:4px}}
.qt-btn{{background:var(--gray);border:1px solid var(--border);border-radius:5px;width:22px;height:22px;font-size:13px;cursor:pointer;font-weight:700;display:flex;align-items:center;justify-content:center;color:var(--text);transition:background .1s}}
.qt-btn:hover{{background:var(--border)}}
.qt-val{{font-weight:700;font-size:13px;width:24px;text-align:center}}
.btn-del-item{{background:none;border:none;color:var(--sub2);cursor:pointer;font-size:15px;padding:2px;transition:color .12s;line-height:1}}
.btn-del-item:hover{{color:#dc2626}}

/* ── KITS SALVOS ─────────────────────────────────────────── */
.kits-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin-top:16px}}
.kit-card{{background:#fff;border:1px solid var(--border);border-radius:12px;padding:16px;cursor:pointer;transition:all .15s;box-shadow:var(--shadow)}}
.kit-card:hover{{border-color:var(--red);box-shadow:0 6px 18px #8B101018;transform:translateY(-1px)}}
.kc-nome{{font-size:13px;font-weight:700;margin-bottom:3px;color:#1f2937}}
.kc-info{{font-size:11px;color:var(--sub);margin-bottom:10px}}
.kc-footer{{display:flex;justify-content:space-between;align-items:center}}
.kc-total{{font-size:14px;font-weight:800;color:var(--red)}}

/* ── CAMPANHA ────────────────────────────────────────────── */
.camp-grid{{display:grid;grid-template-columns:290px 1fr;gap:18px}}
@media(max-width:900px){{.camp-grid{{grid-template-columns:1fr}}}}
.camp-config{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:14px;box-shadow:var(--shadow)}}
.camp-config label{{font-size:11px;font-weight:700;color:var(--sub);text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:5px}}
.camp-config input,.camp-config select{{width:100%;border:1px solid var(--border);border-radius:8px;padding:8px 11px;font-size:13px;outline:none;transition:border-color .15s;color:var(--text)}}
.camp-config input:focus,.camp-config select:focus{{border-color:var(--red);box-shadow:0 0 0 3px #8B101012}}
.range-val{{font-size:22px;font-weight:800;color:var(--red);text-align:center;margin-top:2px;letter-spacing:-1px}}
input[type=range]{{accent-color:var(--red);width:100%}}

/* ── INFO BOX ────────────────────────────────────────────── */
.info-box{{background:#fff;border:1px solid var(--border);border-left:4px solid var(--red);border-radius:10px;padding:14px 18px;font-size:13px;color:#374151;line-height:1.8;margin-bottom:18px;box-shadow:var(--shadow)}}

/* ── MISC ────────────────────────────────────────────────── */
.empty{{text-align:center;color:var(--sub2);padding:36px;font-size:13px}}
.pag-info{{font-size:11.5px;color:var(--sub);margin-top:10px;text-align:right}}
.flex-between{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
/* ── DATE RANGE ──────────────────────────────────────────── */
.range-btns{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;align-items:center}}
.range-btn{{background:var(--gray);border:1px solid var(--border);border-radius:20px;padding:5px 14px;font-size:11.5px;font-weight:600;cursor:pointer;color:var(--sub);transition:all .15s}}
.range-btn:hover{{border-color:var(--red);color:var(--red)}}
.range-btn.active{{background:var(--red);color:#fff;border-color:var(--red)}}
.range-custom{{display:none;align-items:center;gap:8px}}
.range-custom input{{border:1px solid var(--border);border-radius:8px;padding:5px 10px;font-size:12px;outline:none;color:var(--text)}}
.range-custom input:focus{{border-color:var(--red)}}
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="topbar">
  {'<img class="logo-endo" src="'+endo_b64+'" alt="Endocommerce">' if endo_b64 else '<span class="sys-title" style="font-size:16px;color:var(--red)">Endocommerce</span>'}
  <div class="logo-sep"></div>
  <div>
    <div class="sys-title">Sistema Future</div>
    <div class="sys-sub">Gestão de Produtos · Endocommerce</div>
  </div>
  <div class="topbar-right">
    <span class="badge-date" id="dateLabel">
      <svg width="11" height="11" viewBox="0 0 16 16" fill="none" style="vertical-align:middle;margin-right:4px;opacity:.5"><rect x="2" y="3" width="12" height="11" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M5 1v4M11 1v4M2 7h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      Base: {gen_date}
    </span>
    <button class="btn-update" id="btnAtualizar" onclick="triggerUpdate()">
      <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style="vertical-align:middle;margin-right:5px"><path d="M13.5 8A5.5 5.5 0 1 1 8 2.5c1.8 0 3.4.87 4.4 2.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M10.5 5H13V2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      Atualizar Base
    </button>
  </div>
</div>

<!-- TABS -->
<div class="tabs">
  <div class="tab active" onclick="showTab('geral')">
    <svg class="tab-icon" viewBox="0 0 16 16" fill="none"><rect x="1" y="9" width="4" height="6" rx="1" fill="currentColor" opacity=".7"/><rect x="6" y="5" width="4" height="10" rx="1" fill="currentColor" opacity=".85"/><rect x="11" y="1" width="4" height="14" rx="1" fill="currentColor"/></svg>
    Visão Geral
  </div>
  <div class="tab" onclick="showTab('produtos')">
    <svg class="tab-icon" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M2 8h12M2 12h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    Produtos
  </div>
  <div class="tab" onclick="showTab('estoque')">
    <svg class="tab-icon" viewBox="0 0 16 16" fill="none"><path d="M1 12l3-7 3 3 3-5 3 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M1 14h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    Estoque
  </div>
  <div class="tab" onclick="showTab('abc')">
    <svg class="tab-icon" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M8 8l4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/></svg>
    Curva ABC
  </div>
  <div class="tab" onclick="showTab('kits')">
    <svg class="tab-icon" viewBox="0 0 16 16" fill="none"><rect x="1" y="4" width="14" height="9" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M5 4V3a3 3 0 0 1 6 0v1" stroke="currentColor" stroke-width="1.5"/></svg>
    Kits
  </div>
  <div class="tab" onclick="showTab('campanha')">
    <svg class="tab-icon" viewBox="0 0 16 16" fill="none"><path d="M1 8h14M1 8l5-5M1 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Campanha
  </div>
</div>

<div class="content">

<!-- ══════════════ VISÃO GERAL ══════════════ -->
<div class="tab-pane active" id="tab-geral">
  <div class="kpi-grid">
    <div class="kpi kpi--count">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#8B1010"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      <div class="kpi-label">Produtos Ativos</div>
      <div class="kpi-val" id="kpi-prods">—</div>
      <div class="kpi-sub">na base Future</div>
    </div>
    <div class="kpi kpi--count">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#8B1010"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10"/></svg>
      <div class="kpi-label">Unidades em Estoque</div>
      <div class="kpi-val" id="kpi-units">—</div>
      <div class="kpi-sub">pronta entrega</div>
    </div>
    <div class="kpi kpi--money">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#1e40af"><path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <div class="kpi-label">Valor de Custo</div>
      <div class="kpi-val" id="kpi-custo">—</div>
      <div class="kpi-sub">custo total em estoque</div>
    </div>
    <div class="kpi kpi--money">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#1e40af"><path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
      <div class="kpi-label">Valor de Venda</div>
      <div class="kpi-val" id="kpi-venda">—</div>
      <div class="kpi-sub">potencial de receita</div>
    </div>
    <div class="kpi kpi--green">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#15803d"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
      <div class="kpi-label">Margem Média</div>
      <div class="kpi-val" id="kpi-margem">—</div>
      <div class="kpi-sub">sobre preço de venda</div>
    </div>
    <div class="kpi kpi--danger">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#dc2626"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
      <div class="kpi-label">Estoque Crítico</div>
      <div class="kpi-val" id="kpi-crit">—</div>
      <div class="kpi-sub">menos de 10 unidades</div>
    </div>
    <div class="kpi kpi--warn">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#b45309"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <div class="kpi-label">Sem Movimentação</div>
      <div class="kpi-val" id="kpi-sem-mov">—</div>
      <div class="kpi-sub">estoque parado &gt; 300 un</div>
    </div>
    <div class="kpi kpi--green">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#15803d"><path d="M5 3l14 9-14 9V3z"/></svg>
      <div class="kpi-label">Curva A</div>
      <div class="kpi-val" id="kpi-curva-a">—</div>
      <div class="kpi-sub">top 80% do valor</div>
    </div>
    <div class="kpi kpi--count">
      <div class="kpi-accent"></div>
      <svg class="kpi-icon" viewBox="0 0 24 24" fill="currentColor" style="color:#8B1010"><path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
      <div class="kpi-label">Vendidos Hoje</div>
      <div class="kpi-val" id="kpi-vendidos">—</div>
      <div class="kpi-sub" id="kpi-vendidos-sub">aguardando dados</div>
    </div>
  </div>
  <div class="charts-grid">
    <div class="chart-box"><div class="chart-title">Estoque por Categoria</div><canvas id="chartCat"></canvas></div>
    <div class="chart-box"><div class="chart-title">Distribuição Curva ABC (por valor em estoque)</div><canvas id="chartABC"></canvas></div>
    <div class="chart-box"><div class="chart-title">Top 15 Produtos por Valor em Estoque</div><canvas id="chartTop"></canvas></div>
    <div class="chart-box"><div class="chart-title">Margem por Faixa (%)</div><canvas id="chartMargem"></canvas></div>
  </div>
  <div class="chart-box" style="margin-bottom:28px">
    <div class="chart-title">Vendas por Dia (unidades saídas do estoque)</div>
    <div class="range-btns">
      <button class="range-btn" data-range="hoje" onclick="setRange('hoje')">Hoje</button>
      <button class="range-btn" data-range="ontem" onclick="setRange('ontem')">Ontem</button>
      <button class="range-btn active" data-range="7dias" onclick="setRange('7dias')">Últimos 7 dias</button>
      <button class="range-btn" data-range="personalizado" onclick="setRange('personalizado')">Personalizado</button>
      <div class="range-custom" id="rangeCustom">
        <input type="date" id="rangeFrom" onchange="renderVendasChart()">
        <span style="font-size:12px;color:var(--sub)">até</span>
        <input type="date" id="rangeTo" onchange="renderVendasChart()">
      </div>
    </div>
    <canvas id="chartVendas" style="max-height:200px"></canvas>
    <div id="vendasEmpty" style="text-align:center;color:var(--sub2);padding:24px;font-size:12px;display:none">Nenhum dado de vendas ainda. Aguardando primeira atualização de estoque.</div>
  </div>
</div>

<!-- ══════════════ PRODUTOS ══════════════ -->
<div class="tab-pane" id="tab-produtos">
  <div class="filter-row">
    <input type="text" id="buscaProd" placeholder="Buscar produto ou SKU..." oninput="renderProdutos()">
    <select id="filtCat" onchange="renderProdutos()"><option value="">Todas categorias</option></select>
    <select id="filtPrecos" onchange="renderProdutos()">
      <option value="">Todos</option>
      <option value="com">Com preços Future</option>
      <option value="sem">Sem match</option>
    </select>
    <span id="prodCount" class="filter-count"></span>
    <button id="btnSelAll" onclick="toggleSelAll()" style="background:var(--gray);border:1px solid var(--border);border-radius:8px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;color:var(--sub)">☐ Selecionar todos</button>
  </div>
  <!-- Totalizador de seleção -->
  <div id="selBar" style="display:none;background:#1a1a2e;color:#fff;border-radius:10px;padding:12px 18px;margin-bottom:12px;display:none;align-items:center;gap:24px;flex-wrap:wrap">
    <span style="font-size:12px;font-weight:700;color:#94a3b8" id="selCount">0 selecionados</span>
    <div style="display:flex;gap:24px;flex:1;flex-wrap:wrap">
      <div><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Total Custo</div><div style="font-size:15px;font-weight:800;color:#fbbf24" id="selCusto">R$ 0,00</div></div>
      <div><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Total Venda (c/ est.)</div><div style="font-size:15px;font-weight:800;color:#34d399" id="selVenda">R$ 0,00</div></div>
      <div><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Total ABC (s/ est.)</div><div style="font-size:15px;font-weight:800;color:#60a5fa" id="selABC">R$ 0,00</div></div>
      <div><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Unidades</div><div style="font-size:15px;font-weight:800;color:#fff" id="selUnits">0</div></div>
      <div><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Margem Média</div><div style="font-size:15px;font-weight:800;color:#a78bfa" id="selMargem">0%</div></div>
    </div>
    <button onclick="limparSel()" style="background:#374151;border:none;border-radius:6px;padding:5px 12px;color:#9ca3af;font-size:11px;font-weight:600;cursor:pointer">✕ Limpar</button>
  </div>
  <div class="tbl-wrap">
    <table id="prodTable">
      <thead><tr>
        <th style="width:32px"><input type="checkbox" id="chkAll" onclick="toggleSelAll()" style="cursor:pointer"></th>
        <th class="th-sort" data-col="sku" onclick="sortProd('sku')">SKU <span class="sort-icon">↕</span></th>
        <th class="th-sort" data-col="nome" onclick="sortProd('nome')">Produto <span class="sort-icon">↕</span></th>
        <th>Categoria</th>
        <th class="r th-sort" data-col="custo" onclick="sortProd('custo')">Custo <span class="sort-icon">↕</span></th>
        <th class="r th-sort" data-col="pvenda" onclick="sortProd('pvenda')">P. Venda (c/ est.) <span class="sort-icon">↕</span></th>
        <th class="r th-sort" data-col="pabc" onclick="sortProd('pabc')">P. ABC (s/ est.) <span class="sort-icon">↕</span></th>
        <th class="r th-sort" data-col="margem" onclick="sortProd('margem')">Margem% <span class="sort-icon">↕</span></th>
        <th class="r th-sort" data-col="est" onclick="sortProd('est')">Estoque <span class="sort-icon">↕</span></th>
      </tr></thead>
      <tbody id="prodTbody"></tbody>
    </table>
  </div>
  <div class="pag-info" id="prodPag"></div>
</div>

<!-- ══════════════ ESTOQUE ══════════════ -->
<div class="tab-pane" id="tab-estoque">
  <div class="filter-row">
    <input type="text" id="buscaEst" placeholder="Buscar..." oninput="renderEstoque()">
    <select id="filtEst" onchange="renderEstoque()">
      <option value="">Todos</option>
      <option value="ok">Estoque OK (≥50)</option>
      <option value="baixo">Baixo (10–49)</option>
      <option value="crit">Crítico (&lt;10)</option>
      <option value="zerado">Zerado</option>
      <option value="alto">Alto (&gt;300)</option>
    </select>
    <span id="estCount" class="filter-count"></span>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>SKU</th><th>Produto</th>
        <th class="r">Estoque</th><th>Status</th>
        <th class="r">Custo Unit.</th><th class="r">Valor Total Custo</th>
        <th class="r">P. Venda</th><th class="r">Valor Potencial</th>
      </tr></thead>
      <tbody id="estTbody"></tbody>
    </table>
  </div>
</div>

<!-- ══════════════ CURVA ABC ══════════════ -->
<div class="tab-pane" id="tab-abc">
  <div class="info-box">
    <strong style="color:var(--red);font-size:13px">Curva ABC por Valor em Estoque</strong><br>
    <span class="badge badge-a" style="margin-top:6px;display:inline-flex">A</span> <span style="font-size:12px">Top produtos que representam 80% do valor total</span> &nbsp;&nbsp;
    <span class="badge badge-b">B</span> <span style="font-size:12px">Próximos 15%</span> &nbsp;&nbsp;
    <span class="badge badge-c">C</span> <span style="font-size:12px">Últimos 5%</span>
  </div>
  <div class="filter-row">
    <input type="text" id="buscaABC" placeholder="Buscar..." oninput="renderABC()">
    <select id="filtABC" onchange="renderABC()">
      <option value="">Todas classes</option>
      <option value="A">Classe A</option>
      <option value="B">Classe B</option>
      <option value="C">Classe C</option>
    </select>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>#</th><th>SKU</th><th>Produto</th><th>Classe</th>
        <th class="r">Estoque</th><th class="r">Valor (custo)</th>
        <th class="r">% do Total</th><th class="r">% Acumulado</th>
      </tr></thead>
      <tbody id="abcTbody"></tbody>
    </table>
  </div>
</div>

<!-- ══════════════ KITS ══════════════ -->
<div class="tab-pane" id="tab-kits">
  <div class="kit-layout">
    <div class="kit-left">
      <div class="sec-title" style="margin-bottom:0">Produtos</div>
      <input type="text" style="border:1px solid var(--border);border-radius:8px;padding:7px 10px;font-size:12px;outline:none;width:100%" placeholder="Buscar..." oninput="renderKitProds(this.value)">
      <div class="prod-list-kit" id="kitProdList"></div>
    </div>
    <div class="kit-right">
      <div>
        <input class="kit-name-input" id="kitNome" type="text" placeholder="Nome do kit..." value="Kit Básico">
      </div>
      <div class="desc-row">
        <label>Desconto:</label>
        <input class="desc-input" id="kitDesc" type="number" value="20" min="0" max="90" oninput="renderKitResumo()">
        <span style="font-size:13px;font-weight:600;color:var(--sub)">%</span>
        <label style="margin-left:12px">Preço base:</label>
        <select id="kitPrecoBase" onchange="renderKitResumo()" style="border:1px solid var(--border);border-radius:8px;padding:5px 8px;font-size:12px;outline:none">
          <option value="pvenda">Com estoque (pvenda)</option>
          <option value="pabc">Sem estoque (ABC)</option>
          <option value="preco_tiny">Preço Tiny</option>
        </select>
        <button class="btn-danger" style="margin-left:auto" onclick="kitItens=[];renderKitResumo();renderKitProds('')">🗑 Limpar</button>
      </div>
      <div class="tbl-wrap" style="flex:1;overflow-y:auto">
        <table>
          <thead><tr><th>Produto</th><th>SKU</th><th>Qtd</th><th class="r">Unit.</th><th class="r">Subtotal</th><th></th></tr></thead>
          <tbody id="kitBody"></tbody>
        </table>
      </div>
      <div class="kit-totals">
        <div class="tot-row"><span>Subtotal</span><span id="ktSub">R$ 0,00</span></div>
        <div class="tot-row"><span id="ktDescLabel">Desconto (20%)</span><span id="ktDesc" style="color:#15803d">– R$ 0,00</span></div>
        <div class="tot-row final"><span>Total do kit</span><span id="ktTotal">R$ 0,00</span></div>
        <div class="tot-row" style="margin-top:4px"><span>Custo do kit</span><span id="ktCusto" style="color:#374151;font-weight:600">R$ 0,00</span></div>
        <div class="tot-row"><span>Margem do kit</span><span id="ktMargem" style="color:#15803d;font-weight:700">0%</span></div>
      </div>
      <div class="kit-actions">
        <button class="btn-main" onclick="salvarKit()">💾 Salvar Kit</button>
        <button class="btn-sec" onclick="exportKitPDF()">🖨 PDF</button>
      </div>
    </div>
  </div>
  <div style="margin-top:20px">
    <div class="sec-title">Kits Salvos</div>
    <div class="kits-grid" id="kitsSalvosGrid"></div>
  </div>
</div>

<!-- ══════════════ CAMPANHA ══════════════ -->
<div class="tab-pane" id="tab-campanha">
  <div class="camp-grid">
    <div class="camp-config">
      <div>
        <label>Nome da Campanha</label>
        <input type="text" id="campNome" value="Promoção Junho 2026" oninput="renderCampanha()">
      </div>
      <div>
        <label>Desconto (%)</label>
        <input type="range" id="campDesc" min="5" max="50" value="20" oninput="document.getElementById('campDescVal').textContent=this.value+'%';renderCampanha()">
        <div class="range-val" id="campDescVal">20%</div>
      </div>
      <div>
        <label>Preço Base</label>
        <select id="campBase" onchange="renderCampanha()">
          <option value="pvenda">Preço venda (c/ estoque)</option>
          <option value="pabc">Preço ABC (s/ estoque)</option>
          <option value="preco_tiny">Preço Tiny</option>
        </select>
      </div>
      <div>
        <label>Filtro de Estoque Mínimo</label>
        <input type="number" id="campEstMin" value="50" min="0" oninput="renderCampanha()">
      </div>
      <div>
        <label>Filtro de Categoria</label>
        <select id="campCat" onchange="renderCampanha()"><option value="">Todas</option></select>
      </div>
      <button class="btn-main" onclick="exportarCampanha()">📄 Gerar Documento</button>
      <button class="btn-sec" onclick="exportarCampanhaExcel()">📊 Exportar Excel</button>
    </div>
    <div>
      <div class="flex-between">
        <div class="sec-title" style="margin-bottom:0">Produtos na Campanha</div>
        <span id="campCount" class="filter-count"></span>
      </div>
      <div class="tbl-wrap">
        <table>
          <thead><tr>
            <th>SKU</th><th>Produto</th><th class="r">Estoque</th>
            <th class="r">Preço Base</th><th class="r">Desconto</th><th class="r">Preço Promo</th>
          </tr></thead>
          <tbody id="campTbody"></tbody>
        </table>
      </div>
    </div>
  </div>
</div>

</div><!-- /content -->

<script>
const PRODS = {prods_js};

// ── Utilities ──────────────────────────────────────────────────────
function fmt(v){{return 'R$ '+parseFloat(v||0).toFixed(2).replace('.',',')}}
function fmtN(v){{return parseFloat(v||0).toLocaleString('pt-BR',{{maximumFractionDigits:0}})}}
function pBase(p,key){{return p[key]||p.pvenda||p.preco_tiny||0}}

// ── Tab navigation ─────────────────────────────────────────────────
function showTab(id){{
  document.querySelectorAll('.tab-pane').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el=>el.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  event.target.classList.add('active');
  if(id==='geral') renderCharts();
  if(id==='abc') renderABC();
  if(id==='kits'){{renderKitProds('');carregarKitsSalvos();}}
  if(id==='campanha') renderCampanha();
}}

// ── KPIs ──────────────────────────────────────────────────────────
function calcKPIs(){{
  const ativos = PRODS.filter(p=>p.est>0);
  const totalEst = PRODS.reduce((a,p)=>a+p.est,0);
  const valCusto = PRODS.reduce((a,p)=>a+(p.est*p.custo),0);
  const valVenda = PRODS.reduce((a,p)=>a+(p.est*(p.pvenda||p.preco_tiny||0)),0);
  const margens = PRODS.filter(p=>p.pvenda>0&&p.custo>0).map(p=>((p.pvenda-p.custo)/p.pvenda)*100);
  const margMedia = margens.length ? margens.reduce((a,b)=>a+b)/margens.length : 0;
  const crit = PRODS.filter(p=>p.est>0&&p.est<10).length;
  const semMov = PRODS.filter(p=>p.est>300).length;
  const sorted = [...PRODS].sort((a,b)=>(b.est*b.custo)-(a.est*a.custo));
  let acc=0,curvA=0;
  for(const p of sorted){{acc+=p.est*p.custo;if(acc/valCusto<=0.8)curvA++;else break;}}
  function setMoney(id,v){{
    const n=parseFloat(v).toLocaleString('pt-BR',{{minimumFractionDigits:2,maximumFractionDigits:2}});
    document.getElementById(id).innerHTML='<span class="rs">R$ </span>'+n;
  }}
  document.getElementById('kpi-prods').textContent=PRODS.length;
  document.getElementById('kpi-units').textContent=fmtN(totalEst)+' un';
  setMoney('kpi-custo',valCusto);
  setMoney('kpi-venda',valVenda);
  document.getElementById('kpi-margem').textContent=margMedia.toFixed(1)+'%';
  document.getElementById('kpi-crit').textContent=crit+' produtos';
  document.getElementById('kpi-sem-mov').textContent=semMov+' produtos';
  document.getElementById('kpi-curva-a').textContent=curvA+' produtos';
}}

// ── Charts ────────────────────────────────────────────────────────
let chartsBuilt=false;
function renderCharts(){{
  if(chartsBuilt)return;
  chartsBuilt=true;
  calcKPIs();
  
  const chartDefaults={{
    plugins:{{legend:{{display:false}}}},
    scales:{{
      x:{{grid:{{color:'#f1f5f9',drawBorder:false}},ticks:{{color:'#6b7280',font:{{size:10}}}}}},
      y:{{grid:{{color:'#f1f5f9',drawBorder:false}},ticks:{{color:'#6b7280',font:{{size:10}}}},beginAtZero:true}}
    }}
  }};

  // Categoria
  const cats={{}};
  PRODS.forEach(p=>{{const c=p.categoria||'Outros';cats[c]=(cats[c]||0)+p.est}});
  const catSorted=Object.entries(cats).sort((a,b)=>b[1]-a[1]).slice(0,8);
  new Chart(document.getElementById('chartCat'),{{
    type:'bar',
    data:{{
      labels:catSorted.map(x=>x[0].substring(0,22)),
      datasets:[{{
        data:catSorted.map(x=>x[1]),
        backgroundColor:catSorted.map((_,i)=>i===0?'#8B1010':'#8B101088'),
        borderRadius:6,borderSkipped:false
      }}]
    }},
    options:{{...chartDefaults,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>' '+ctx.parsed.y.toLocaleString('pt-BR')+' un'}}}}}}}}
  }});

  // ABC
  const valTotal=PRODS.reduce((a,p)=>a+(p.est*p.custo),0);
  const sorted=[...PRODS].sort((a,b)=>(b.est*b.custo)-(a.est*a.custo));
  let acc=0,cA=0,cB=0,cC=0,vA=0,vB=0,vC=0;
  for(const p of sorted){{const v=p.est*p.custo;acc+=v;const pct=acc/valTotal;
    if(pct<=0.8){{cA++;vA+=v}}else if(pct<=0.95){{cB++;vB+=v}}else{{cC++;vC+=v}}}}
  new Chart(document.getElementById('chartABC'),{{
    type:'doughnut',
    data:{{
      labels:['Classe A ('+cA+' prod.)','Classe B ('+cB+')','Classe C ('+cC+')'],
      datasets:[{{
        data:[cA,cB,cC],
        backgroundColor:['#166534','#ca8a04','#991b1b'],
        borderColor:['#fff','#fff','#fff'],
        borderWidth:3,hoverOffset:6
      }}]
    }},
    options:{{
      plugins:{{
        legend:{{
          display:true,position:'bottom',
          labels:{{font:{{size:11}},color:'#374151',padding:14,usePointStyle:true,pointStyleWidth:10}}
        }},
        tooltip:{{callbacks:{{label:ctx=>' '+ctx.label+': '+ctx.parsed.toLocaleString('pt-BR')}}}}
      }},
      cutout:'62%'
    }}
  }});

  // Top 15 por valor
  const top15=sorted.slice(0,15);
  new Chart(document.getElementById('chartTop'),{{
    type:'bar',
    data:{{
      labels:top15.map(p=>p.sku),
      datasets:[{{
        data:top15.map(p=>p.est*p.custo),
        backgroundColor:top15.map((_,i)=>i<3?'#1e40af':'#1e40af66'),
        borderRadius:4,borderSkipped:false
      }}]
    }},
    options:{{
      indexAxis:'y',
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>' R$ '+ctx.parsed.x.toLocaleString('pt-BR',{{minimumFractionDigits:2}})}}}}
      }},
      scales:{{
        x:{{grid:{{color:'#f1f5f9'}},ticks:{{color:'#6b7280',font:{{size:10}},callback:v=>'R$ '+v.toLocaleString('pt-BR')}},beginAtZero:true}},
        y:{{grid:{{display:false}},ticks:{{color:'#374151',font:{{size:10,weight:'600'}}}}}}
      }}
    }}
  }});

  // Margem
  const faixas={{'0–20%':0,'20–40%':0,'40–60%':0,'60–80%':0,'80%+':0}};
  PRODS.filter(p=>p.pvenda>0&&p.custo>0).forEach(p=>{{
    const m=((p.pvenda-p.custo)/p.pvenda)*100;
    if(m<20)faixas['0–20%']++;else if(m<40)faixas['20–40%']++;
    else if(m<60)faixas['40–60%']++;else if(m<80)faixas['60–80%']++;else faixas['80%+']++;
  }});
  new Chart(document.getElementById('chartMargem'),{{
    type:'bar',
    data:{{
      labels:Object.keys(faixas),
      datasets:[{{
        data:Object.values(faixas),
        backgroundColor:['#dc2626bb','#f97316bb','#ca8a04bb','#16a34abb','#0d9488bb'],
        borderRadius:6,borderSkipped:false
      }}]
    }},
    options:{{
      ...chartDefaults,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:ctx=>' '+ctx.parsed.y+' produtos'}}}}
      }}
    }}
  }});
}}

// ── Produtos ──────────────────────────────────────────────────────
const PER_PAGE=300;
let prodSortCol='est', prodSortDir=-1; // padrão: estoque maior→menor
let prodSelecionados=new Set();
let prodListAtual=[];

function sortProd(col){{
  if(prodSortCol===col){{prodSortDir*=-1}}else{{prodSortCol=col;prodSortDir=-1}}
  document.querySelectorAll('.th-sort').forEach(th=>{{
    th.classList.remove('sort-asc','sort-desc');
    th.querySelector('.sort-icon').textContent='↕';
  }});
  const th=document.querySelector(`.th-sort[data-col="${{col}}"]`);
  if(th){{th.classList.add(prodSortDir>0?'sort-asc':'sort-desc');th.querySelector('.sort-icon').textContent=prodSortDir>0?'↑':'↓';}}
  renderProdutos();
}}

function renderProdutos(){{
  const q=(document.getElementById('buscaProd').value||'').toLowerCase();
  const cat=document.getElementById('filtCat').value;
  const fp=document.getElementById('filtPrecos').value;
  let list=PRODS.filter(p=>{{
    if(q&&!p.nome.toLowerCase().includes(q)&&!p.sku.includes(q))return false;
    if(cat&&p.categoria!==cat)return false;
    if(fp==='com'&&!p.tem_precos)return false;
    if(fp==='sem'&&p.tem_precos)return false;
    return true;
  }});
  // Ordenação
  list.sort((a,b)=>{{
    let va,vb;
    if(prodSortCol==='margem'){{va=(a.pvenda>0&&a.custo>0)?(a.pvenda-a.custo)/a.pvenda:0;vb=(b.pvenda>0&&b.custo>0)?(b.pvenda-b.custo)/b.pvenda:0;}}
    else{{va=isNaN(a[prodSortCol])?a[prodSortCol]||'':a[prodSortCol]||0;vb=isNaN(b[prodSortCol])?b[prodSortCol]||'':b[prodSortCol]||0;}}
    if(va<vb)return -1*prodSortDir;if(va>vb)return prodSortDir;return 0;
  }});
  prodListAtual=list;
  document.getElementById('prodCount').textContent=list.length+' produtos';
  const page=list.slice(0,PER_PAGE);
  let html='';
  for(const p of page){{
    const margem=p.pvenda>0&&p.custo>0?(p.pvenda-p.custo)/p.pvenda*100:null;
    const m=margem!==null?margem.toFixed(1)+'%':'—';
    const estCls=p.est===0?'est-zero':p.est<10?'est-crit':'est-ok';
    const checked=prodSelecionados.has(p.sku)?'checked':'';
    const rowCls=prodSelecionados.has(p.sku)?'row-sel':'';
    html+=`<tr class="${{rowCls}}" onclick="toggleSel('${{p.sku}}',event)">
      <td onclick="event.stopPropagation()"><input type="checkbox" ${{checked}} onchange="toggleSel('${{p.sku}}',event)" style="cursor:pointer"></td>
      <td><span class="sku">${{p.sku}}</span></td>
      <td class="nome" title="${{p.nome}}">${{p.nome}}</td>
      <td style="font-size:11px;color:var(--sub)">${{p.categoria||'—'}}</td>
      <td class="td-r preco-custo">${{p.custo>0?fmt(p.custo):'—'}}</td>
      <td class="td-r preco">${{p.pvenda>0?fmt(p.pvenda):'—'}}</td>
      <td class="td-r preco-abc">${{p.pabc>0?fmt(p.pabc):'—'}}</td>
      <td class="td-r" style="font-size:12px;color:${{margem!==null?(margem>60?'var(--green)':margem>30?'var(--amber)':'#dc2626'):'var(--sub2)'}}">${{m}}</td>
      <td class="td-r ${{estCls}}">${{fmtN(p.est)}}</td>
    </tr>`;
  }}
  document.getElementById('prodTbody').innerHTML=html||'<tr><td colspan="9" class="empty">Nenhum produto</td></tr>';
  document.getElementById('prodPag').textContent=list.length>PER_PAGE?'Mostrando '+page.length+' de '+list.length+' — refine a busca para ver mais':'';
  atualizarSelBar();
}}

function toggleSel(sku, e){{
  if(e&&e.target&&e.target.tagName==='INPUT'){{
    if(e.target.checked)prodSelecionados.add(sku);else prodSelecionados.delete(sku);
  }}else{{
    if(prodSelecionados.has(sku))prodSelecionados.delete(sku);else prodSelecionados.add(sku);
    // sync checkbox
    const rows=document.querySelectorAll('#prodTbody tr');
    rows.forEach(row=>{{const cb=row.querySelector('input[type=checkbox]');if(cb){{const s=row.querySelector('.sku');if(s&&s.textContent===sku)cb.checked=prodSelecionados.has(sku);}}  }});
  }}
  const row=e&&e.currentTarget;
  if(row&&row.tagName==='TR'){{row.classList.toggle('row-sel',prodSelecionados.has(sku));}}
  atualizarSelBar();
}}

function toggleSelAll(){{
  const chkAll=document.getElementById('chkAll');
  if(prodSelecionados.size===prodListAtual.length){{prodSelecionados.clear();if(chkAll)chkAll.checked=false;}}
  else{{prodListAtual.forEach(p=>prodSelecionados.add(p.sku));if(chkAll)chkAll.checked=true;}}
  renderProdutos();
}}

function limparSel(){{prodSelecionados.clear();renderProdutos();}}

function atualizarSelBar(){{
  const bar=document.getElementById('selBar');
  if(prodSelecionados.size===0){{bar.style.display='none';return;}}
  bar.style.display='flex';
  const selecionados=PRODS.filter(p=>prodSelecionados.has(p.sku));
  const totCusto=selecionados.reduce((a,p)=>a+p.custo*p.est,0);
  const totVenda=selecionados.reduce((a,p)=>a+(p.pvenda||p.preco_tiny||0)*p.est,0);
  const totABC=selecionados.reduce((a,p)=>a+(p.pabc||0)*p.est,0);
  const totUnits=selecionados.reduce((a,p)=>a+p.est,0);
  const margens=selecionados.filter(p=>p.pvenda>0&&p.custo>0).map(p=>(p.pvenda-p.custo)/p.pvenda*100);
  const margMedia=margens.length?margens.reduce((a,b)=>a+b)/margens.length:0;
  document.getElementById('selCount').textContent=prodSelecionados.size+' produto(s) selecionado(s)';
  document.getElementById('selCusto').textContent=fmt(totCusto);
  document.getElementById('selVenda').textContent=fmt(totVenda);
  document.getElementById('selABC').textContent=totABC>0?fmt(totABC):'—';
  document.getElementById('selUnits').textContent=fmtN(totUnits);
  document.getElementById('selMargem').textContent=margMedia.toFixed(1)+'%';
}}

// ── Estoque ───────────────────────────────────────────────────────
function renderEstoque(){{
  const q=(document.getElementById('buscaEst').value||'').toLowerCase();
  const f=document.getElementById('filtEst').value;
  let list=PRODS.filter(p=>{{
    if(q&&!p.nome.toLowerCase().includes(q)&&!p.sku.includes(q))return false;
    if(f==='ok'&&p.est<50)return false;
    if(f==='baixo'&&!(p.est>=10&&p.est<50))return false;
    if(f==='crit'&&!(p.est>0&&p.est<10))return false;
    if(f==='zerado'&&p.est!==0)return false;
    if(f==='alto'&&p.est<=300)return false;
    return true;
  }}).sort((a,b)=>a.est-b.est);
  document.getElementById('estCount').textContent=list.length+' produtos';
  let html='';
  for(const p of list){{
    const pv=p.pvenda||p.preco_tiny||0;
    let bdg='badge-ok',lbl='OK';
    if(p.est===0){{bdg='badge-zero';lbl='Zerado'}}
    else if(p.est<10){{bdg='badge-crit';lbl='Crítico'}}
    else if(p.est<50){{bdg='badge-baixo';lbl='Baixo'}}
    html+=`<tr>
      <td class="sku">${{p.sku}}</td>
      <td class="nome" title="${{p.nome}}">${{p.nome}}</td>
      <td class="td-r ${{p.est<10?'est-crit':p.est===0?'est-zero':'est-ok'}}">${{fmtN(p.est)}}</td>
      <td><span class="badge ${{bdg}}">${{lbl}}</span></td>
      <td class="td-r preco-custo">${{p.custo>0?fmt(p.custo):'—'}}</td>
      <td class="td-r">${{p.custo>0?fmt(p.est*p.custo):'—'}}</td>
      <td class="td-r preco">${{pv>0?fmt(pv):'—'}}</td>
      <td class="td-r">${{pv>0?fmt(p.est*pv):'—'}}</td>
    </tr>`;
  }}
  document.getElementById('estTbody').innerHTML=html||'<tr><td colspan="8" class="empty">Nenhum produto</td></tr>';
}}

// ── Curva ABC ─────────────────────────────────────────────────────
let abcData=[];
function buildABC(){{
  const valTotal=PRODS.reduce((a,p)=>a+(p.est*p.custo),0);
  const sorted=[...PRODS].filter(p=>p.custo>0).sort((a,b)=>(b.est*b.custo)-(a.est*a.custo));
  let acc=0;
  abcData=sorted.map((p,i)=>{{
    const v=p.est*p.custo;acc+=v;const pct=acc/valTotal;
    let cls=pct<=0.8?'A':pct<=0.95?'B':'C';
    return{{...p,val_est:v,pct_total:(v/valTotal)*100,pct_acum:pct*100,abc:cls,rank:i+1}};
  }});
}}
function renderABC(){{
  if(!abcData.length)buildABC();
  const q=(document.getElementById('buscaABC').value||'').toLowerCase();
  const f=document.getElementById('filtABC').value;
  const list=abcData.filter(p=>{{
    if(q&&!p.nome.toLowerCase().includes(q)&&!p.sku.includes(q))return false;
    if(f&&p.abc!==f)return false;
    return true;
  }});
  let html='';
  for(const p of list){{
    html+=`<tr>
      <td class="sku">${{p.rank}}</td>
      <td class="sku">${{p.sku}}</td>
      <td class="nome" title="${{p.nome}}">${{p.nome}}</td>
      <td><span class="badge badge-${{p.abc.toLowerCase()}}">${{p.abc}}</span></td>
      <td class="td-r">${{fmtN(p.est)}}</td>
      <td class="td-r preco-custo">${{fmt(p.val_est)}}</td>
      <td class="td-r" style="font-size:11px">${{p.pct_total.toFixed(2)}}%</td>
      <td class="td-r" style="font-size:11px">${{p.pct_acum.toFixed(1)}}%</td>
    </tr>`;
  }}
  document.getElementById('abcTbody').innerHTML=html||'<tr><td colspan="8" class="empty">Nenhum produto</td></tr>';
}}

// ── Supabase ──────────────────────────────────────────────────────
const SB = supabase.createClient(
  'https://bdmwvujqldwgeuwfpqaf.supabase.co',
  'sb_publishable_SY5OwtZoXTXYPFu0jE5ymQ_Gamf9Iw3'
);

// ── Kits ──────────────────────────────────────────────────────────
let kitItens=[];
let kitsSalvos=[];
function getProd(sku){{return PRODS.find(p=>p.sku===sku)}}

function renderKitProds(q){{
  q=q.toLowerCase();
  const inKit=new Set(kitItens.map(i=>i.sku));
  let html='';
  const base=document.getElementById('kitPrecoBase').value;
  for(const p of PRODS){{
    if(q&&!p.nome.toLowerCase().includes(q)&&!p.sku.includes(q))continue;
    const preco=pBase(p,base);
    const cls=inKit.has(p.sku)?'prod-item-kit in':'prod-item-kit';
    html+=`<div class="${{cls}}" onclick="addKitItem('${{p.sku}}')">
      <div style="flex:1;min-width:0">
        <div class="pi-nome">${{p.nome}}</div>
        <div class="pi-meta">SKU ${{p.sku}} · est: ${{p.est}}</div>
      </div>
      <span class="pi-price">${{fmt(preco)}}</span>
    </div>`;
  }}
  document.getElementById('kitProdList').innerHTML=html;
}}

function addKitItem(sku){{
  const ex=kitItens.find(i=>i.sku===sku);
  if(ex)ex.qt++;else kitItens.push({{sku,qt:1}});
  renderKitResumo();
  renderKitProds(document.querySelector('.kit-left input').value||'');
}}

function renderKitResumo(){{
  const desc=parseFloat(document.getElementById('kitDesc').value)||0;
  const base=document.getElementById('kitPrecoBase').value;
  document.getElementById('ktDescLabel').textContent=`Desconto (${{desc}}%)`;
  let html='',sub=0,custo=0;
  if(kitItens.length===0){{
    document.getElementById('kitBody').innerHTML='<tr><td colspan="6" class="empty">Adicione produtos →</td></tr>';
  }}else{{
    for(const item of kitItens){{const p=getProd(item.sku);if(!p)continue;
      const preco=pBase(p,base);const st=preco*item.qt;sub+=st;custo+=p.custo*item.qt;
      html+=`<tr><td class="nome" style="max-width:200px">${{p.nome}}</td><td class="sku">${{p.sku}}</td>
        <td><div class="qt-ctrl"><button class="qt-btn" onclick="chgQt('${{item.sku}}',-1)">−</button>
        <span class="qt-val">${{item.qt}}</span><button class="qt-btn" onclick="chgQt('${{item.sku}}',1)">+</button></div></td>
        <td class="td-r" style="font-size:12px">${{fmt(preco)}}</td>
        <td class="td-r preco">${{fmt(st)}}</td>
        <td><button class="btn-del-item" onclick="delKitItem('${{item.sku}}')">✕</button></td></tr>`;
    }}
    document.getElementById('kitBody').innerHTML=html;
  }}
  const dv=sub*(desc/100);const final=sub-dv;
  const marg=final>0?((final-custo)/final*100).toFixed(1):0;
  document.getElementById('ktSub').textContent=fmt(sub);
  document.getElementById('ktDesc').textContent='– '+fmt(dv);
  document.getElementById('ktTotal').textContent=fmt(final);
  document.getElementById('ktCusto').textContent=fmt(custo);
  document.getElementById('ktMargem').textContent=marg+'%';
}}

function chgQt(sku,d){{const i=kitItens.find(x=>x.sku===sku);if(i)i.qt=Math.max(1,i.qt+d);renderKitResumo();}}
function delKitItem(sku){{kitItens=kitItens.filter(x=>x.sku!==sku);renderKitResumo();renderKitProds('');}}

async function salvarKit(){{
  if(!kitItens.length){{alert('Adicione itens ao kit');return}}
  const nome=document.getElementById('kitNome').value||'Kit sem nome';
  const desc=parseFloat(document.getElementById('kitDesc').value)||0;
  const base=document.getElementById('kitPrecoBase').value;
  const btn=document.querySelector('.kit-actions .btn-main');
  btn.textContent='Salvando...';btn.disabled=true;
  const {{error}}=await SB.from('kits').insert({{nome,desconto:desc,preco_base:base,itens:kitItens}});
  btn.textContent='💾 Salvar Kit';btn.disabled=false;
  if(error){{alert('Erro ao salvar: '+error.message);return;}}
  await carregarKitsSalvos();
  alert('Kit salvo!');
}}

async function carregarKitsSalvos(){{
  const grid=document.getElementById('kitsSalvosGrid');
  grid.innerHTML='<div class="empty">Carregando...</div>';
  const {{data,error}}=await SB.from('kits').select('*').order('criado_em',{{ascending:false}});
  if(error){{grid.innerHTML='<div class="empty">Erro ao carregar kits.</div>';return;}}
  kitsSalvos=data||[];
  renderKitsSalvos();
}}

function renderKitsSalvos(){{
  const grid=document.getElementById('kitsSalvosGrid');
  if(!kitsSalvos.length){{grid.innerHTML='<div class="empty">Nenhum kit salvo ainda.</div>';return;}}
  let html='';
  kitsSalvos.forEach(k=>{{
    const total=k.itens.reduce((a,it)=>{{const p=getProd(it.sku);return a+(p?pBase(p,k.preco_base)*it.qt:0)}},0);
    const desc=k.desconto||0;const final=total*(1-desc/100);
    const n=k.itens.reduce((a,it)=>a+it.qt,0);
    const data=k.criado_em?new Date(k.criado_em).toLocaleDateString('pt-BR'):'';
    html+=`<div class="kit-card">
      <div class="kc-nome">${{k.nome}}</div>
      <div class="kc-info">${{n}} item(s) · ${{desc}}% desconto · ${{data}}</div>
      <div class="kc-footer">
        <span class="kc-total">${{fmt(final)}}</span>
        <div style="display:flex;gap:4px">
          <button class="btn-sm" onclick="carregarKit('${{k.id}}')">Editar</button>
          <button class="btn-sm" style="background:#dc2626" onclick="delKit('${{k.id}}')">✕</button>
        </div>
      </div>
    </div>`;
  }});
  grid.innerHTML=html;
}}

function carregarKit(id){{
  const k=kitsSalvos.find(x=>x.id===id);if(!k)return;
  kitItens=k.itens.map(x=>({{...x}}));
  document.getElementById('kitNome').value=k.nome;
  document.getElementById('kitDesc').value=k.desconto;
  document.getElementById('kitPrecoBase').value=k.preco_base||'pvenda';
  renderKitResumo();renderKitProds('');
}}

async function delKit(id){{
  if(!confirm('Excluir este kit?'))return;
  await SB.from('kits').delete().eq('id',id);
  await carregarKitsSalvos();
}}

function exportKitPDF(){{window.print()}}

// ── Campanha ──────────────────────────────────────────────────────
function renderCampanha(){{
  const desc=parseFloat(document.getElementById('campDesc').value)||0;
  const base=document.getElementById('campBase').value;
  const estMin=parseInt(document.getElementById('campEstMin').value)||0;
  const cat=document.getElementById('campCat').value;
  const list=PRODS.filter(p=>{{
    if(p.est<estMin)return false;
    if(cat&&p.categoria!==cat)return false;
    const preco=pBase(p,base);
    return preco>0;
  }});
  document.getElementById('campCount').textContent=list.length+' produtos';
  let html='';
  for(const p of list){{
    const preco=pBase(p,base);
    const promo=preco*(1-desc/100);
    html+=`<tr>
      <td class="sku">${{p.sku}}</td>
      <td class="nome" title="${{p.nome}}">${{p.nome}}</td>
      <td class="td-r">${{fmtN(p.est)}}</td>
      <td class="td-r">${{fmt(preco)}}</td>
      <td class="td-r" style="color:#15803d;font-weight:600">-${{desc}}%</td>
      <td class="td-r preco">${{fmt(promo)}}</td>
    </tr>`;
  }}
  document.getElementById('campTbody').innerHTML=html||'<tr><td colspan="6" class="empty">Nenhum produto</td></tr>';
}}

function exportarCampanha(){{
  const nome=document.getElementById('campNome').value;
  const desc=parseFloat(document.getElementById('campDesc').value)||0;
  const base=document.getElementById('campBase').value;
  const estMin=parseInt(document.getElementById('campEstMin').value)||0;
  const cat=document.getElementById('campCat').value;
  const list=PRODS.filter(p=>{{
    if(p.est<estMin)return false;
    if(cat&&p.categoria!==cat)return false;
    return pBase(p,base)>0;
  }});
  let rows='';
  list.forEach((p,i)=>{{
    const pr=pBase(p,base);const promo=pr*(1-desc/100);
    rows+=`<tr><td class="num">${{i+1}}</td><td class="sku-td">${{p.sku}}</td>
      <td class="nome-td">${{p.nome}}</td><td class="est-td">${{p.est}}</td>
      <td class="de"><span class="risc">R$ ${{pr.toFixed(2).replace('.',',')}}</span></td>
      <td class="promo">R$ ${{promo.toFixed(2).replace('.',',')}}</td></tr>`;
  }});
  const win=window.open('','_blank');
  win.document.write(`<!DOCTYPE html><html><head><meta charset="UTF-8">
  <title>${{nome}}</title>
  <style>body{{font-family:Arial,sans-serif;max-width:900px;margin:20px auto;color:#1a202c}}
  h1{{font-size:22px;color:#8B1010;margin-bottom:6px}}
  .sub{{font-size:12px;color:#6b7280;margin-bottom:20px}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{background:#8B1010;color:#fff;padding:8px 10px;text-align:left;font-size:10px;text-transform:uppercase}}
  td{{padding:7px 10px;border-bottom:1px solid #f1f5f9}}
  tr:nth-child(even){{background:#fdf8f8}}
  .num{{color:#9ca3af;font-size:11px;width:24px}}
  .sku-td{{font-family:monospace;font-size:11px;color:#6b7280}}
  .est-td{{text-align:center;font-size:11px}}
  .de{{text-align:right}}.promo{{text-align:right;font-weight:800;color:#8B1010;font-size:13px}}
  .risc{{text-decoration:line-through;color:#9ca3af;font-size:11px}}
  @media print{{@page{{margin:1cm}}}}
  </style></head><body>
  <h1>${{nome}}</h1>
  <div class="sub">${{list.length}} produtos · ${{desc}}% de desconto · Pagamento via PIX ou Transferência</div>
  <table><thead><tr><th>#</th><th>Ref.</th><th>Produto</th><th style="text-align:center">Estoque</th><th style="text-align:right">Preço Normal</th><th style="text-align:right">Preço Promo</th></tr></thead>
  <tbody>${{rows}}</tbody></table>
  <script>window.print()<\/script></body></html>`);
}}

function exportarCampanhaExcel(){{
  alert('Para exportar em Excel, use a opção Print → Save as PDF, ou solicite ao assistente a geração do XLSX.');
}}

// ── Histórico de Vendas ───────────────────────────────────────────
let vendasChart = null;
let historicoData = [];
let selectedRange = '7dias';

async function carregarHistorico() {{
  const {{data, error}} = await SB
    .from('estoque_historico')
    .select('data, snapshots')
    .order('data', {{ascending: true}})
    .limit(31);
  if (error || !data || data.length < 2) {{
    document.getElementById('kpi-vendidos').textContent = '—';
    document.getElementById('kpi-vendidos-sub').textContent = 'sem dados ainda';
    return;
  }}
  historicoData = data;
  atualizarKpiVendidos();
  renderVendasChart();
}}

function calcVendidosDia(d1, d2) {{
  let total = 0;
  const snap1 = d1.snapshots || {{}};
  const snap2 = d2.snapshots || {{}};
  for (const [sku, est1] of Object.entries(snap1)) {{
    const est2 = snap2[sku] !== undefined ? snap2[sku] : est1;
    total += Math.max(0, est1 - est2);
  }}
  return total;
}}

function atualizarKpiVendidos() {{
  if (historicoData.length < 2) return;
  const n = historicoData.length;
  const ultimo = historicoData[n - 1];
  const penultimo = historicoData[n - 2];
  const v = calcVendidosDia(penultimo, ultimo);
  document.getElementById('kpi-vendidos').textContent = fmtN(v) + ' un';
  const dataLabel = ultimo.data.split('-').reverse().join('/');
  document.getElementById('kpi-vendidos-sub').textContent = 'atualizado ' + dataLabel;
}}

function getVendasPeriodo() {{
  if (historicoData.length < 2) return [];
  const diffs = [];
  for (let i = 1; i < historicoData.length; i++) {{
    const v = calcVendidosDia(historicoData[i-1], historicoData[i]);
    diffs.push({{data: historicoData[i].data, vendidos: v}});
  }}
  const hoje = new Date().toISOString().split('T')[0];
  const ontem = new Date(Date.now() - 86400000).toISOString().split('T')[0];
  if (selectedRange === 'hoje') return diffs.filter(d => d.data === hoje);
  if (selectedRange === 'ontem') return diffs.filter(d => d.data === ontem);
  if (selectedRange === '7dias') {{
    const cutoff = new Date(Date.now() - 7*86400000).toISOString().split('T')[0];
    return diffs.filter(d => d.data >= cutoff);
  }}
  if (selectedRange === 'personalizado') {{
    const from = document.getElementById('rangeFrom').value;
    const to = document.getElementById('rangeTo').value;
    if (!from || !to) return diffs;
    return diffs.filter(d => d.data >= from && d.data <= to);
  }}
  return diffs;
}}

function setRange(r) {{
  selectedRange = r;
  document.querySelectorAll('.range-btn').forEach(b => b.classList.toggle('active', b.dataset.range === r));
  document.getElementById('rangeCustom').style.display = r === 'personalizado' ? 'flex' : 'none';
  renderVendasChart();
}}

function renderVendasChart() {{
  const dados = getVendasPeriodo();
  const empty = document.getElementById('vendasEmpty');
  const canvas = document.getElementById('chartVendas');
  if (!dados.length) {{
    empty.style.display = 'block';
    canvas.style.display = 'none';
    return;
  }}
  empty.style.display = 'none';
  canvas.style.display = 'block';
  const labels = dados.map(d => {{ const [y,m,day]=d.data.split('-'); return day+'/'+m; }});
  const values = dados.map(d => d.vendidos);
  if (vendasChart) {{
    vendasChart.data.labels = labels;
    vendasChart.data.datasets[0].data = values;
    vendasChart.update();
    return;
  }}
  vendasChart = new Chart(canvas, {{
    type: 'bar',
    data: {{
      labels,
      datasets: [{{
        data: values,
        backgroundColor: '#8B101099',
        borderColor: '#8B1010',
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false
      }}]
    }},
    options: {{
      plugins: {{
        legend: {{display: false}},
        tooltip: {{callbacks: {{label: ctx => ' ' + ctx.parsed.y + ' un vendidas'}}}}
      }},
      scales: {{
        x: {{grid: {{color: '#f1f5f9'}}, ticks: {{color: '#6b7280', font: {{size: 10}}}}}},
        y: {{grid: {{color: '#f1f5f9'}}, ticks: {{color: '#6b7280', font: {{size: 10}}}}, beginAtZero: true}}
      }}
    }}
  }});
}}

// ── Populate selects ──────────────────────────────────────────────
function populateSelects(){{
  const cats=[...new Set(PRODS.map(p=>p.categoria).filter(Boolean))].sort();
  ['filtCat','campCat'].forEach(id=>{{
    const sel=document.getElementById(id);
    cats.forEach(c=>{{const o=document.createElement('option');o.value=c;o.textContent=c;sel.appendChild(o);}});
  }});
}}

// ── Atualizar via GitHub Actions ──────────────────────────────────
async function triggerUpdate() {{
  const token = atob('Z2l0aHViX3BhdF8xMUNBU0JDTEkwUTBDa3h1TVlkVXZoX2lFRjdseUpkM2YxVnhhUTZLNFkwWXJSNVFuV0czcktGZUhqekFpS2NLMFVZMlRVWTJKUG5QUWM2d0pa');
  const btn = document.getElementById('btnAtualizar');
  btn.disabled = true;
  btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" style="vertical-align:middle;margin-right:5px;animation:spin 1s linear infinite"><path d="M13.5 8A5.5 5.5 0 1 1 8 2.5c1.8 0 3.4.87 4.4 2.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M10.5 5H13V2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>Aguardando...';
  try {{
    const resp = await fetch(
      'https://api.github.com/repos/lucaopfreitas-stack/sistema-future/actions/workflows/update.yml/dispatches',
      {{
        method: 'POST',
        headers: {{
          'Authorization': 'Bearer ' + token,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        }},
        body: JSON.stringify({{ref: 'main'}})
      }}
    );
    if (resp.status === 204) {{
      alert('Atualização iniciada!\\n\\nEm cerca de 3 minutos o estoque será atualizado e a página recarregará automaticamente.');
      setTimeout(() => location.reload(), 180000);
    }} else if (resp.status === 401) {{
      localStorage.removeItem('gh_pat');
      alert('Token inválido ou expirado. Tente novamente.');
    }} else if (resp.status === 404) {{
      alert('Workflow não encontrado. Verifique se o arquivo foi publicado no GitHub.');
    }} else {{
      alert('Erro ' + resp.status + '. Tente novamente.');
    }}
  }} catch(e) {{
    alert('Erro de conexão: ' + e.message);
  }}
  btn.disabled = false;
  btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" style="vertical-align:middle;margin-right:5px"><path d="M13.5 8A5.5 5.5 0 1 1 8 2.5c1.8 0 3.4.87 4.4 2.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M10.5 5H13V2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>Atualizar Base';
}}

// ── Init ──────────────────────────────────────────────────────────
populateSelects();
renderProdutos();
renderEstoque();
carregarKitsSalvos();
renderCharts();
carregarHistorico();
</script>
</body>
</html>'''

out = os.path.join(PASTA, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Dashboard salvo: {out}")
print(f"Tamanho: {len(html)//1024}KB")

# Git push — só local (no GitHub Actions o workflow faz o push)
if not os.environ.get('GITHUB_ACTIONS'):
    try:
        subprocess.run(['git', '-C', PASTA, 'add', 'index.html', 'base_produtos.json'], check=True)
        result = subprocess.run(['git', '-C', PASTA, 'diff', '--cached', '--quiet'])
        if result.returncode != 0:
            msg = f'Atualização automática {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            subprocess.run(['git', '-C', PASTA, 'commit', '-m', msg], check=True)
            subprocess.run(['git', '-C', PASTA, 'push'], check=True)
            print("Publicado no GitHub Pages ✓")
        else:
            print("Sem alterações para publicar")
    except Exception as e:
        print(f"AVISO: Push GitHub falhou — {e}")
