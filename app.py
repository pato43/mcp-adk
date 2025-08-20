# app.py
# MCP Orchestrator — Inventarios SQL Server + Calendar + SDAC + Slack + WhatsApp (Streamlit)
# UI moderna, tema oscuro, full-width, tabs y acciones con toasts/notificaciones.

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# =========================
# CONFIG & THEME (dark, full-width)
# =========================
st.set_page_config(page_title="MCP Orchestrator — Inventarios & Logística", layout="wide", page_icon="📦")

ACCENT = "#22D3EE"
ACCENT_2 = "#6EE7F9"
BG = "#0E1117"
CARD = "#151B28"
TEXT = "#F5F7FA"
MUTED = "#94A3B8"

px_defaults = px.defaults
px_defaults.template = "plotly_dark"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {{
  background-color: {BG}; color: {TEXT};
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
}}
.block-container {{padding: 0.4rem 0.8rem 1rem 0.8rem;}}
header {{visibility: hidden;}}
.section-title{{ font-size:1.05rem; font-weight:900; letter-spacing:.2px; margin:6px 0 8px; }}
hr.section{{ border:none; height:1px; background:linear-gradient(90deg,{ACCENT},{ACCENT_2}); margin:8px 0 16px; }}
.card{{ background:{CARD}; border:1px solid #1E2633; border-radius:14px; padding:12px 14px; }}
.pill{{ display:inline-block; padding:6px 12px; border-radius:999px; font-size:.8rem; font-weight:800;
       background:{ACCENT}; color:#001621; margin:0 8px 8px 0; }}
.kpi-card{{ background:{CARD}; border:1px solid #1E2633; border-radius:16px; padding:14px 16px; }}
.kpi-title{{ font-size:.78rem; color:{MUTED}; font-weight:600; letter-spacing:.2px; }}
.kpi-value{{ font-size:1.5rem; font-weight:900; color:{TEXT}; }}
.kpi-sub{{ font-size:.80rem; color:{MUTED}; font-weight:600; }}
.stTextInput > div > div > input {{
  background:#0F1420 !important; color:{TEXT} !important; border:1px solid #20283A !important; border-radius:10px;
}}
.stButton > button {{ background:{ACCENT}; color:#002533; font-weight:900; border-radius:10px; border:none; }}
.badge{{ font-size:.75rem; font-weight:800; padding:4px 10px; border-radius:8px; color:#001621;
        background: linear-gradient(135deg,{ACCENT},{ACCENT_2}); }}
</style>
""", unsafe_allow_html=True)

# =========================
# DATA SYNTH (inventarios estilo SQL Server)
# =========================
@st.cache_data(show_spinner=False)
def make_inventory(seed=7, days=90):
    rng = np.random.default_rng(seed)
    regions = ["Centro", "Norte", "Occidente", "Sureste"]
    cats = ["Abarrotes","Perecederos","Hogar","Electrónica","Farmacia","Moda"]
    skus = [f"SKU-{i:05d}" for i in range(100, 180)]
    base_today = datetime.today().date()
    # Tabla "actual" de inventario
    rows = []
    for sku in skus:
        cat = rng.choice(cats)
        reg = rng.choice(regions)
        stock = max(0, int(rng.normal(350, 120)))
        reorder = int(max(50, rng.normal(280, 80)))
        lead = round(max(1.0, rng.normal(3.5, 0.8)),1)
        daily_demand = max(1, int(rng.normal(30, 8)))
        days_cover = round(stock / max(1, daily_demand), 1)
        rows.append([sku, cat, reg, stock, reorder, lead, daily_demand, days_cover])
    inv = pd.DataFrame(rows, columns=["sku","category","region","stock","reorder_point","lead_time_days","daily_demand","days_cover"])
    inv["below_reorder"] = (inv["stock"] < inv["reorder_point"]).astype(int)
    # Serie temporal sintética para “existencias” por día (para tendencias)
    dates = pd.date_range(base_today - timedelta(days=days-1), base_today, freq="D")
    ts_rows = []
    for d in dates:
        for reg in regions:
            total_stock = max(5000, int(rng.normal(8000, 1200)))
            ts_rows.append([d, reg, total_stock])
    inv_ts = pd.DataFrame(ts_rows, columns=["date","region","total_stock"])
    return inv, inv_ts

inventory, inv_ts = make_inventory()

# =========================
# STATE & HELPERS
# =========================
if "started" not in st.session_state: st.session_state.started = False
if "prompt" not in st.session_state: st.session_state.prompt = ""
if "log" not in st.session_state: st.session_state.log = []
if "assignments" not in st.session_state: st.session_state.assignments = []

def log(msg):
    st.session_state.log.append({"ts": datetime.now().strftime("%H:%M:%S"), "msg": msg})

def schedule_meeting(tomorrow_time="09:00"):
    st.toast(f"Añadido a Google Calendar: Junta de inventarios — mañana {tomorrow_time} (GMT-6)")
    log(f"Calendar: Junta 'inventarios' mañana {tomorrow_time} creada")

def assign_sdac(task="Reabasto crítico Occidente"):
    asg_id = f"SDAC-{np.random.randint(1000, 9999)}"
    st.session_state.assignments.append({"id": asg_id, "task": task, "status": "open"})
    st.toast(f"SDAC: asignación creada {asg_id} — {task}")
    log(f"SDAC: asignación {asg_id} creada ({task})")

def send_slack(channel="#logistica", text="Alerta de reabasto"):
    st.toast(f"Slack: enviado a {channel} — {text}")
    log(f"Slack: mensaje a {channel} — {text}")

def send_whatsapp(to="+52•••", text="Resumen inventarios"):
    st.toast(f"WhatsApp: mensaje enviado a {to} — {text}")
    log(f"WhatsApp: a {to} — {text}")

def send_email(to="direccion@empresa.mx", subject="Resumen ejecutivo", body="KPIs y acciones"):
    st.toast(f"Correo enviado a {to}: {subject}")
    log(f"Mail: {to} — {subject}")

# =========================
# SIDEBAR — ACCIONES RÁPIDAS
# =========================
with st.sidebar:
    st.markdown("### 📦 MCP Orchestrator")
    st.caption("Acciones rápidas")
    if st.button("📅 Programar junta (mañana 09:00)"):
        schedule_meeting("09:00")
    if st.button("🧾 Asignar logística en SDAC"):
        assign_sdac("Reabasto crítico Occidente — top 10 SKUs bajo punto de pedido")
    if st.button("💬 Avisar a Slack (#logistica)"):
        send_slack("#logistica", "SKUs críticos bajo punto de pedido: acción requerida")
    if st.button("🟢 WhatsApp al supervisor"):
        send_whatsapp("+52 55 0000 0000", "Se asignó reabasto crítico. Revisión inmediata.")
    if st.button("✉️ Enviar resumen por correo"):
        send_email()

    st.markdown("---")
    st.caption("Filtros globales")
    region_f = st.multiselect("Región", sorted(inventory["region"].unique()))
    cat_f = st.multiselect("Categoría", sorted(inventory["category"].unique()))
    st.caption("Ventana tendencias")
    horizon_days = st.slider("Días", min_value=30, max_value=90, value=60, step=10)

# Aplicar filtros globales
inv_v = inventory.copy()
if region_f: inv_v = inv_v[inv_v["region"].isin(region_f)]
if cat_f: inv_v = inv_v[inv_v["category"].isin(cat_f)]
cut_date = inv_ts["date"].max() - pd.Timedelta(days=horizon_days-1)
inv_ts_v = inv_ts[(inv_ts["date"] >= cut_date) & (inv_ts["region"].isin(region_f) if region_f else inv_ts["region"].notna())]

# =========================
# HEADER
# =========================
c0, c1 = st.columns([2.2, 1], gap="large")
with c0:
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;">
  <div class="badge">MCP</div>
  <div style="font-weight:900;font-size:1.2rem;">Orchestrator — Inventarios & Logística (SQL Server · Calendar · SDAC · Slack · WhatsApp)</div>
</div>
""", unsafe_allow_html=True)
    st.caption("De la intención a la acción: agenda, consulta inventarios, asigna logística y comunica en canales clave.")
with c1:
    pass

# =========================
# PANTALLA INICIAL → PROMPT
# =========================
if not st.session_state.started:
    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    colA, colB = st.columns([2.6, 1.4], gap="large")
    with colA:
        st.markdown('<div class="section-title">Escribe tu instrucción</div>', unsafe_allow_html=True)
        prompt = st.text_input(" ", value="", placeholder="Ej. Agenda junta mañana, revisa inventarios SQL Server y asigna logística en SDAC")
        start = st.button("▶ Ejecutar", type="primary")
        if start or (prompt and prompt != st.session_state.prompt):
            st.session_state.prompt = prompt or "Agenda junta mañana, revisa inventarios y asigna logística"
            # Píldoras de orquestación (no bloqueantes)
            st.markdown('<span class="pill">Planner: entendiendo intención</span>', unsafe_allow_html=True); time.sleep(0.5)
            st.markdown('<span class="pill">Discovery MCP: SQL Server (Azure RDS), Calendar, SDAC, Slack, WhatsApp</span>', unsafe_allow_html=True); time.sleep(0.5)
            st.markdown('<span class="pill">Conexión: SQL Server • esquema dbo.inventory</span>', unsafe_allow_html=True); time.sleep(0.5)
            st.markdown('<span class="pill">Ejecución: consultas de stock y puntos de pedido</span>', unsafe_allow_html=True); time.sleep(0.5)
            st.markdown('<span class="pill">Acciones: Calendar/SDAC/Slack/WhatsApp</span>', unsafe_allow_html=True); time.sleep(0.4)
            st.session_state.started = True
            log(f"Prompt: {st.session_state.prompt}")
            st.rerun()
    with colB:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Conectores**")
        st.markdown("• SQL Server (inventarios)\n\n• Google Calendar\n\n• SDAC (logística)\n\n• Slack (#logistica)\n\n• WhatsApp (supervisor)\n\n• Mail (dirección)")
        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DASHBOARD (tras ejecutar)
# =========================
if st.session_state.started:
    # KPIs rápidos inventario/logística
    below = inv_v["below_reorder"].sum()
    pct_below = 100 * below / max(1, len(inv_v))
    avg_cover = inv_v["days_cover"].mean()
    crit = inv_v.sort_values("days_cover").head(10)
    open_tasks = sum(1 for a in st.session_state.assignments if a["status"] == "open")
    tti = np.random.randint(6, 11)

    cH, cK = st.columns([2, 3], gap="large")
    with cH:
        st.markdown('<div class="section-title">Instrucción</div>', unsafe_allow_html=True)
        st.code(st.session_state.prompt, language="markdown")
    with cK:
        k1,k2,k3,k4,k5 = st.columns(5)
        k1.markdown(f'<div class="kpi-card"><div class="kpi-title">SKUs bajo punto de pedido</div><div class="kpi-value">{below:,}</div><div class="kpi-sub">{pct_below:.1f}% del total</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><div class="kpi-title">Cobertura promedio</div><div class="kpi-value">{avg_cover:.1f} días</div><div class="kpi-sub">days of cover</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><div class="kpi-title">Tareas abiertas SDAC</div><div class="kpi-value">{open_tasks}</div><div class="kpi-sub">reabasto / logística</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-card"><div class="kpi-title">Tiempo a Insight</div><div class="kpi-value">{tti}s</div><div class="kpi-sub">desde prompt</div></div>', unsafe_allow_html=True)
        k5.markdown(f'<div class="kpi-card"><div class="kpi-title">Artefactos</div><div class="kpi-value">CSV/Gráficos</div><div class="kpi-sub">exportables</div></div>', unsafe_allow_html=True)

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)

    tab_over, tab_inv, tab_log, tab_comm, tab_act, tab_logbook = st.tabs(
        ["Tendencias","Inventario SQL Server","Logística (SDAC)","Comunicaciones","Acciones MCP","Bitácora"]
    )

    # ============= TENDENCIAS
    with tab_over:
        a,b,c = st.columns([2.2, 1.5, 1.3], gap="large")
        with a:
            ts = inv_ts_v.groupby("date", as_index=False)["total_stock"].sum()
            fig = px.line(ts, x="date", y="total_stock", markers=True, color_discrete_sequence=[ACCENT])
            fig.update_traces(line=dict(width=3))
            fig.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
        with b:
            gap = inv_v.copy()
            gap["gap_qty"] = (gap["reorder_point"] - gap["stock"]).clip(lower=0)
            heat = gap.groupby(["category","region"], as_index=False)["gap_qty"].sum()
            fig2 = px.density_heatmap(heat, x="region", y="category", z="gap_qty",
                                      color_continuous_scale="Turbo")
            fig2.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig2, use_container_width=True)
        with c:
            by_cat = inv_v.groupby("category", as_index=False)["below_reorder"].sum()
            fig3 = px.treemap(by_cat, path=["category"], values="below_reorder",
                              color="below_reorder", color_continuous_scale="Magma")
            fig3.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig3, use_container_width=True)

    # ============= INVENTARIO SQL SERVER
    with tab_inv:
        d,e = st.columns([2,2], gap="large")
        with d:
            # Top críticos (menor cobertura)
            st.markdown("**SKUs críticos (menor cobertura)**")
            st.dataframe(crit[["sku","category","region","stock","reorder_point","days_cover"]], use_container_width=True, hide_index=True)
        with e:
            # Barras: gap por región
            gap_reg = inv_v.copy()
            gap_reg["gap_qty"] = (gap_reg["reorder_point"] - gap_reg["stock"]).clip(lower=0)
            br = gap_reg.groupby("region", as_index=False)["gap_qty"].sum().sort_values("gap_qty", ascending=False)
            fig4 = px.bar(br, x="region", y="gap_qty", color="region", color_discrete_sequence=px.colors.qualitative.Prism)
            fig4.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

        st.download_button("📥 Exportar inventario filtrado (CSV)", data=inv_v.to_csv(index=False).encode("utf-8"),
                           file_name="inventario_filtrado.csv")

    # ============= LOGÍSTICA (SDAC)
    with tab_log:
        j,k = st.columns([1.4, 2.6], gap="large")
        with j:
            st.markdown("**Sugerencias de reabasto**")
            suggest = crit.copy()
            suggest["sugg_qty"] = (suggest["reorder_point"] - suggest["stock"]).clip(lower=0) + (suggest["daily_demand"] * suggest["lead_time_days"]).astype(int)
            st.dataframe(suggest[["sku","category","region","stock","reorder_point","sugg_qty","lead_time_days"]],
                         use_container_width=True, hide_index=True)
            if st.button("🧾 Crear asignaciones SDAC para sugerencias"):
                assign_sdac("Reabasto automático — críticos (top 10)")
        with k:
            # Sankey simple flujo DC→Regiones
            nodes = ["CD Sur","CD Norte","Centro","Norte","Occidente","Sureste"]
            idx = {n:i for i,n in enumerate(nodes)}
            links = dict(
                source=[idx["CD Sur"], idx["CD Sur"], idx["CD Norte"], idx["CD Norte"]],
                target=[idx["Centro"], idx["Sureste"], idx["Norte"], idx["Occidente"]],
                value=[130, 100, 150, 120]
            )
            figS = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=18, line=dict(color="black", width=0.4), label=nodes),
                link=dict(source=links["source"], target=links["target"], value=links["value"]))])
            figS.update_layout(height=420, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(figS, use_container_width=True)

        st.markdown("**Asignaciones activas**")
        st.dataframe(pd.DataFrame(st.session_state.assignments) if st.session_state.assignments else
                     pd.DataFrame([{"id":"—","task":"(sin asignaciones)","status":"—"}]),
                     use_container_width=True, hide_index=True)

    # ============= COMUNICACIONES
    with tab_comm:
        st.markdown("**Enviar avisos**")
        c1,c2,c3,c4 = st.columns([1,1,1,1], gap="large")
        with c1:
            if st.button("📅 Añadir junta a Calendar (mañana 09:00)"):
                schedule_meeting("09:00")
        with c2:
            if st.button("💬 Slack a #logistica"):
                send_slack("#logistica", "Se asignó reabasto crítico para top 10 SKUs")
        with c3:
            if st.button("🟢 WhatsApp Supervisor"):
                send_whatsapp("+52 55 0000 0000", "Confirmar recepción de asignaciones SDAC")
        with c4:
            if st.button("✉️ Enviar resumen a Dirección"):
                send_email("direccion@empresa.mx","Resumen inventarios & logística","Adjunto CSV y gráficos")
        st.markdown('<hr class="section"/>', unsafe_allow_html=True)
        st.markdown("**Plantillas rápidas**")
        colx, coly = st.columns([1,1], gap="large")
        with colx:
            st.code("Slack: SKUs bajo punto de pedido detectados. Acciones programadas en SDAC. Ver artefactos en Drive.", language="markdown")
        with coly:
            st.code("WhatsApp: Se programó reabasto crítico. Confirmar recepción y prioridad en CD Sur/Norte.", language="markdown")

    # ============= ACCIONES MCP (checklist + SQL)
    with tab_act:
        st.markdown("**Checklist de acciones**")
        st.markdown("- ✅ SQL Server: consulta dbo.inventory completada (última actualización hoy)")
        st.markdown("- ✅ Calendar: junta creada (mañana 09:00)")
        st.markdown("- 🟡 SDAC: asignaciones abiertas (en proceso)")
        st.markdown("- 🟡 Slack: avisos enviados a #logistica")
        st.markdown("- ✅ WhatsApp: supervisor notificado")
        st.markdown("- ✅ Mail: resumen enviado a Dirección")
        st.markdown('<hr class="section"/>', unsafe_allow_html=True)
        st.markdown("**SQL (referencia)**")
        st.code("""
-- (Referencia) SQL Server — inventarios críticos
SELECT sku, category, region, stock, reorder_point, daily_demand,
       CAST(stock * 1.0 / NULLIF(daily_demand,0) AS DECIMAL(10,2)) AS days_cover
FROM dbo.inventory
WHERE stock < reorder_point
ORDER BY days_cover ASC, region, category;""", language="sql")

    # ============= BITÁCORA
    with tab_logbook:
        st.markdown("**Bitácora de acciones**")
        df_log = pd.DataFrame(st.session_state.log) if st.session_state.log else pd.DataFrame([{"ts":"—","msg":"(sin eventos)"}])
        st.dataframe(df_log, use_container_width=True, hide_index=True)
