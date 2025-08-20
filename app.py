# app.py
# Agente MCP + ADK — Agenda, Inventarios, Mensajería e Insights (Streamlit, dark, full width)

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, time as dt_time, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time as pytime

# =========================
# CONFIGURACIÓN GLOBAL (tema oscuro + tipografía grande + full width)
# =========================
st.set_page_config(page_title="Agente MCP + ADK — Enterprise", layout="wide", page_icon="🧠")

ACCENT = "#22D3EE"
ACCENT_2 = "#6EE7F9"
BG = "#0E1117"
CARD = "#151B28"
TEXT = "#F5F7FA"
MUTED = "#A7B0BE"

px.defaults.template = "plotly_dark"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {{
  background-color: {BG}; color: {TEXT};
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  font-size: 18px; /* ⬅️ tipografía más grande */
}}
.block-container {{padding: 0.4rem 0.8rem 1rem 0.8rem;}}
header {{visibility: hidden;}}
.section-title{{ font-size:1.15rem; font-weight:900; letter-spacing:.2px; margin:8px 0 10px; }}
hr.section{{ border:none; height:1px; background:linear-gradient(90deg,{ACCENT},{ACCENT_2}); margin:8px 0 16px; }}
.card{{ background:{CARD}; border:1px solid #1E2633; border-radius:14px; padding:14px 16px; }}
.kpi-card{{ background:{CARD}; border:1px solid #1E2633; border-radius:16px; padding:16px 18px; }}
.kpi-title{{ font-size:.9rem; color:{MUTED}; font-weight:600; letter-spacing:.2px; }}
.kpi-value{{ font-size:1.6rem; font-weight:900; color:{TEXT}; }}
.kpi-sub{{ font-size:.9rem; color:{MUTED}; font-weight:600; }}
.pill{{ display:inline-block; padding:6px 12px; border-radius:999px; font-size:.85rem; font-weight:800;
       background:{ACCENT}; color:#001621; margin:0 8px 8px 0; }}
.badge{{ font-size:.8rem; font-weight:800; padding:4px 10px; border-radius:8px; color:#001621;
        background: linear-gradient(135deg,{ACCENT},{ACCENT_2}); }}
.stTextInput > div > div > input, .stTextArea textarea {{
  background:#0F1420 !important; color:{TEXT} !important; border:1px solid #20283A !important; border-radius:10px; font-size:18px;
}}
.stDateInput input, .stTimeInput input {{
  background:#0F1420 !important; color:{TEXT} !important; border:1px solid #20283A !important; border-radius:10px; font-size:18px;
}}
.stButton > button {{ background:{ACCENT}; color:#002533; font-weight:900; border-radius:10px; border:none; font-size:18px; }}
</style>
""", unsafe_allow_html=True)

# =========================
# ESTADO
# =========================
if "events" not in st.session_state:
    # eventos iniciales de ejemplo (para mini-calendario)
    today = date.today()
    st.session_state.events = [
        {"title": "Daily Ops", "when": datetime.combine(today, dt_time(hour=9))},
        {"title": "Comité Comercial", "when": datetime.combine(today + timedelta(days=1), dt_time(hour=11))},
        {"title": "Revisión Inventarios", "when": datetime.combine(today + timedelta(days=2), dt_time(hour=10))},
    ]
if "chat_email" not in st.session_state:
    st.session_state.chat_email = []   # historial de "correo"
if "chat_whatsapp" not in st.session_state:
    st.session_state.chat_whatsapp = []  # historial de "whatsapp"

def add_event(title:str, d:date, t:dt_time):
    when = datetime.combine(d, t)
    st.session_state.events.append({"title": title, "when": when})
    st.toast(f"Evento agregado a Google Calendar: {title} — {when.strftime('%d/%m/%Y %H:%M')}")
def send_email(frm:str, to:str, subject:str, body:str):
    st.session_state.chat_email.append({"ts": datetime.now().strftime("%H:%M"), "from": frm, "to": to, "subject": subject, "body": body})
    st.toast(f"Correo enviado a {to}: {subject}")
def send_whatsapp(to:str, text:str):
    st.session_state.chat_whatsapp.append({"ts": datetime.now().strftime("%H:%M"), "to": to, "text": text})
    st.toast(f"WhatsApp enviado a {to}")

# =========================
# DATOS (inventarios estilo SQL Server) + serie para insights
# =========================
@st.cache_data(show_spinner=False)
def make_inventory(seed=7, days=120):
    rng = np.random.default_rng(seed)
    regions = ["Centro", "Norte", "Occidente", "Sureste"]
    cats = ["Abarrotes","Perecederos","Hogar","Electrónica","Farmacia","Moda"]
    skus = [f"SKU-{i:05d}" for i in range(120, 200)]
    rows = []
    for sku in skus:
        cat = rng.choice(cats)
        reg = rng.choice(regions)
        stock = max(0, int(rng.normal(360, 120)))
        reorder = int(max(50, rng.normal(300, 90)))
        daily_demand = max(1, int(rng.normal(28, 7)))
        lead = round(max(1.0, rng.normal(3.5, 0.8)),1)
        days_cover = round(stock / max(1, daily_demand), 1)
        rows.append([sku, cat, reg, stock, reorder, daily_demand, lead, days_cover])
    inv = pd.DataFrame(rows, columns=["sku","category","region","stock","reorder_point","daily_demand","lead_time_days","days_cover"])
    inv["below_reorder"] = (inv["stock"] < inv["reorder_point"]).astype(int)

    end = date.today()
    dates = pd.date_range(end - timedelta(days=days-1), end, freq="D")
    ts_rows = []
    for d in dates:
        for reg in regions:
            total_stock = max(5000, int(rng.normal(8200, 1100)))
            ts_rows.append([d, reg, total_stock])
    inv_ts = pd.DataFrame(ts_rows, columns=["date","region","total_stock"])
    return inv, inv_ts

inventory, inv_ts = make_inventory()

# =========================
# ENCABEZADO (título, rol/área, propósito)
# =========================
c_head1, c_head2 = st.columns([2.4, 1.6], gap="large")
with c_head1:
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;">
  <div class="badge">MCP + ADK</div>
  <div style="font-weight:900;font-size:1.3rem;">Agente Empresarial — Agenda • Inventarios • Mensajería • Insights</div>
</div>
""", unsafe_allow_html=True)
    st.caption("Asistente inteligente para gestión operativa, comunicación y análisis visual.")
with c_head2:
    role = st.selectbox("Área / Rol", ["Dirección", "Operaciones & Logística", "Ventas & Comercial", "Finanzas", "TI / Datos"], index=1)

st.markdown('<hr class="section"/>', unsafe_allow_html=True)

# =========================
# TABS PRINCIPALES
# =========================
tab_agenda, tab_invent, tab_msgs, tab_insights, tab_log = st.tabs(
    ["📅 Agenda & Calendario", "📦 Inventarios (SQL Server)", "💬 Mensajería (Correo & WhatsApp)", "📊 Insights", "🗒️ Bitácora"]
)

# ============== TAB: AGENDA & CALENDARIO
with tab_agenda:
    a1, a2 = st.columns([2.2, 1.2], gap="large")
    with a1:
        st.markdown('<div class="section-title">Programar reunión</div>', unsafe_allow_html=True)
        mt_title = st.text_input("Título", value="Junta de seguimiento")
        mt_date = st.date_input("Fecha", value=date.today() + timedelta(days=1))
        mt_time = st.time_input("Hora", value=dt_time(hour=9, minute=0))
        attendees = st.text_input("Invitados (coma separada)", value="direccion@empresa.mx, ops@empresa.mx")
        if st.button("➕ Agregar a Google Calendar"):
            add_event(mt_title, mt_date, mt_time)
    with a2:
        st.markdown('<div class="section-title">Próximos eventos</div>', unsafe_allow_html=True)
        if st.session_state.events:
            ev = pd.DataFrame(st.session_state.events).sort_values("when").head(8)
            ev["Fecha"] = ev["when"].dt.strftime("%d/%m/%Y")
            ev["Hora"] = ev["when"].dt.strftime("%H:%M")
            st.dataframe(ev[["Fecha","Hora","title"]].rename(columns={"title":"Evento"}), hide_index=True, use_container_width=True)
        else:
            st.info("Sin eventos programados.")
        # Mini “calendario” por intensidad de días con evento
        if st.session_state.events:
            cal = pd.DataFrame([{"date": e["when"].date()} for e in st.session_state.events])
            cal = cal.value_counts("date").reset_index(name="events")
            fig_cal = px.density_heatmap(cal, x="date", y=["Eventos"]*len(cal), z="events",
                                         nbinsx=7, color_continuous_scale="Turbo")
            fig_cal.update_layout(height=140, margin=dict(l=10,r=10,t=10,b=10), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_cal, use_container_width=True)

# ============== TAB: INVENTARIOS (SQL Server)
with tab_invent:
    i1, i2 = st.columns([1.6, 2.4], gap="large")
    with i1:
        st.markdown('<div class="section-title">Resumen</div>', unsafe_allow_html=True)
        below = int(inventory["below_reorder"].sum())
        pct_below = 100 * below / max(1, len(inventory))
        avg_cover = inventory["days_cover"].mean()
        k1,k2,k3 = st.columns(3)
        k1.markdown(f'<div class="kpi-card"><div class="kpi-title">SKUs bajo punto de pedido</div><div class="kpi-value">{below:,}</div><div class="kpi-sub">{pct_below:.1f}% del total</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><div class="kpi-title">Cobertura prom.</div><div class="kpi-value">{avg_cover:.1f} días</div><div class="kpi-sub">days of cover</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><div class="kpi-title">Artefactos</div><div class="kpi-value">CSV / Gráficos</div><div class="kpi-sub">exportables</div></div>', unsafe_allow_html=True)
        st.markdown('<hr class="section"/>', unsafe_allow_html=True)
        st.markdown("**Acciones operativas**")
        if st.button("🧾 Asignar logística (SDAC) — críticos"):
            st.toast("SDAC: asignación creada para reabasto de SKUs críticos")
        if st.button("📥 Exportar inventario (CSV)"):
            st.download_button("Descargar ahora", data=inventory.to_csv(index=False).encode("utf-8"), file_name="inventario.csv")
    with i2:
        st.markdown('<div class="section-title">Detalle de inventario</div>', unsafe_allow_html=True)
        # tabla y gráficos
        st.dataframe(inventory[["sku","category","region","stock","reorder_point","daily_demand","days_cover"]],
                     hide_index=True, use_container_width=True)
        st.markdown('<hr class="section"/>', unsafe_allow_html=True)
        inv = inventory.copy()
        inv["gap_qty"] = (inv["reorder_point"] - inv["stock"]).clip(lower=0)
        by_reg = inv.groupby("region", as_index=False)["gap_qty"].sum().sort_values("gap_qty", ascending=False)
        fig_bar = px.bar(by_reg, x="region", y="gap_qty", color="region", color_discrete_sequence=px.colors.qualitative.Prism)
        fig_bar.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

# ============== TAB: MENSAJERÍA (Correo & WhatsApp)
with tab_msgs:
    st.markdown('<div class="section-title">Bandejas</div>', unsafe_allow_html=True)
    m1, m2 = st.columns([1,1], gap="large")

    with m1:
        st.subheader("Correo")
        frm = st.text_input("De", value="agente@empresa.mx", key="mail_from")
        to = st.text_input("Para", value="direccion@empresa.mx", key="mail_to")
        subject = st.text_input("Asunto", value="Resumen inventarios & agenda", key="mail_subj")
        body = st.text_area("Mensaje", value="Adjunto KPIs, SKUs críticos y agenda de revisión.", key="mail_body", height=160)
        if st.button("✉️ Enviar correo"):
            send_email(frm, to, subject, body)
        st.markdown("**Historial**")
        if st.session_state.chat_email:
            dfm = pd.DataFrame(st.session_state.chat_email)
            st.dataframe(dfm[["ts","to","subject","body"]].rename(columns={"ts":"Hora","to":"Para","subject":"Asunto","body":"Mensaje"}),
                         hide_index=True, use_container_width=True)
        else:
            st.info("Sin correos aún.")

    with m2:
        st.subheader("WhatsApp")
        to_w = st.text_input("Para (tel.)", value="+52 55 0000 0000", key="wa_to")
        text_w = st.text_area("Mensaje", value="Recordatorio: reunión y reabasto crítico asignado.", key="wa_body", height=160)
        if st.button("🟢 Enviar WhatsApp"):
            send_whatsapp(to_w, text_w)
        st.markdown("**Historial**")
        if st.session_state.chat_whatsapp:
            dfw = pd.DataFrame(st.session_state.chat_whatsapp)
            st.dataframe(dfw.rename(columns={"ts":"Hora","to":"Para","text":"Mensaje"}),
                         hide_index=True, use_container_width=True)
        else:
            st.info("Sin mensajes aún.")

# ============== TAB: INSIGHTS (gráficos + narrativa)
with tab_insights:
    st.markdown('<div class="section-title">Tendencias y focos</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([2.2, 1.5, 1.3], gap="large")

    # Serie tendencial de stock total
    ts = inv_ts.groupby("date", as_index=False)["total_stock"].sum()
    fig_ts = px.line(ts, x="date", y="total_stock", markers=True, color_discrete_sequence=[ACCENT])
    fig_ts.update_traces(line=dict(width=3))
    fig_ts.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    f1.plotly_chart(fig_ts, use_container_width=True)

    # Heatmap de brechas por categoría-región
    inv_h = inventory.copy()
    inv_h["gap_qty"] = (inv_h["reorder_point"] - inv_h["stock"]).clip(lower=0)
    heat = inv_h.groupby(["category","region"], as_index=False)["gap_qty"].sum()
    fig_hm = px.density_heatmap(heat, x="region", y="category", z="gap_qty", color_continuous_scale="Turbo")
    fig_hm.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    f2.plotly_chart(fig_hm, use_container_width=True)

    # Treemap de SKUs bajo punto de pedido por categoría
    by_cat = inv_h.groupby("category", as_index=False)["gap_qty"].sum().sort_values("gap_qty", ascending=False)
    fig_tree = px.treemap(by_cat, path=["category"], values="gap_qty", color="gap_qty", color_continuous_scale="Magma")
    fig_tree.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    f3.plotly_chart(fig_tree, use_container_width=True)

    # Narrativa (explicación automática)
    top_cat = by_cat.iloc[0]["category"] if len(by_cat) else "—"
    top_reg = heat.sort_values("gap_qty", ascending=False).iloc[0]["region"] if len(heat) else "—"
    st.markdown('<div class="section-title">Explicación del agente</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="card">
<p><strong>Tendencia:</strong> El inventario total mantiene patrón estable con variación semanal esperada. 
Se recomienda foco en reposición anticipada para picos de demanda.</p>
<p><strong>Brechas:</strong> La categoría <em>{top_cat}</em> concentra la mayor brecha de reabasto en la región <em>{top_reg}</em>. 
Priorizar asignaciones para evitar quiebres y reducir tiempos de espera.</p>
<p><strong>Acciones:</strong> Programar revisión operativa con logística, actualizar puntos de pedido y 
notificar a equipos de tienda sobre cambios de cobertura.</p>
</div>
""", unsafe_allow_html=True)

# ============== TAB: BITÁCORA (mensajes de UI)
with tab_log:
    st.markdown('<div class="section-title">Bitácora de eventos</div>', unsafe_allow_html=True)
    # Para este ejemplo, reconstruimos la bitácora desde eventos/mensajes enviados
    logs = []
    for e in st.session_state.events:
        logs.append({"Hora": e["when"].strftime("%d/%m %H:%M"), "Evento": f"Calendar: {e['title']}"})
    for m in st.session_state.chat_email:
        logs.append({"Hora": m["ts"], "Evento": f"Mail: {m['to']} — {m['subject']}"})
    for w in st.session_state.chat_whatsapp:
        logs.append({"Hora": w["ts"], "Evento": f"WhatsApp: {w['to']} — {w['text'][:40]}..."})
    if logs:
        st.dataframe(pd.DataFrame(logs), hide_index=True, use_container_width=True)
    else:
        st.info("Sin eventos aún.")

# =========================
# PIE (píldoras de proceso, opcional)
# =========================
st.markdown('<hr class="section"/>', unsafe_allow_html=True)
st.markdown("**Proceso del agente**")
st.markdown('<span class="pill">Planner: intención</span> <span class="pill">Discovery: Calendar/SQL/Comms</span> '
            '<span class="pill">Conexión: fuentes</span> <span class="pill">Ejecución: consultas/acciones</span> '
            '<span class="pill">Artefactos: tablas/gráficos</span> <span class="pill">Narrativa: explicación</span>',
            unsafe_allow_html=True)
