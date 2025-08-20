# app.py
# Agente MCP + ADK — Explicaciones por sección + Sidebar dinámico de destinatarios
# UI oscura, full-width, filtros globales; acciones simuladas con toasts y bitácora.

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, time as dt_time, timedelta
import plotly.express as px
import plotly.graph_objects as go

# =========================
# CONFIG & THEME
# =========================
st.set_page_config(page_title="Agente MCP + ADK — Enterprise", layout="wide", page_icon="🧠")

# Branding (edita a tu gusto)
BRAND_NAME = "Atlas Data Suite"
BRAND_AREA = "Operaciones & Comercial"
PRIMARY = "#7C3AED"   # morado
ACCENT  = "#22D3EE"   # cian
ACCENT_2 = "#6EE7F9"  # cian claro
BG = "#0E1117"
CARD = "#151B28"
TEXT = "#F5F7FA"
MUTED = "#A7B0BE"
LOGO_URL = ""  # opcional

px_defaults = px.defaults
px_defaults.template = "plotly_dark"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {{
  background-color: {BG}; color: {TEXT};
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  font-size: 18px;
}}
.block-container {{padding: 0.6rem 1rem 1.2rem 1rem;}}
header {{visibility: hidden;}}
.section-title{{ font-size:1.15rem; font-weight:900; letter-spacing:.2px; margin:8px 0 10px; }}
hr.section{{ border:none; height:1px; background:linear-gradient(90deg,{ACCENT},{ACCENT_2}); margin:8px 0 16px; }}
.card{{ background:{CARD}; border:1px solid #1E2633; border-radius:14px; padding:14px 16px; }}
.kpi-card{{ background:{CARD}; border:1px solid #1E2633; border-radius:16px; padding:16px 18px; }}
.kpi-title{{ font-size:.9rem; color:{MUTED}; font-weight:600; letter-spacing:.2px; }}
.kpi-value{{ font-size:1.6rem; font-weight:900; color:{TEXT}; }}
.kpi-sub{{ font-size:.9rem; color:{MUTED}; font-weight:600; }}
.badge{{ font-size:.8rem; font-weight:800; padding:4px 10px; border-radius:8px; color:#001621;
        background: linear-gradient(135deg,{PRIMARY},{ACCENT}); }}
.pill{{ display:inline-block; padding:6px 12px; border-radius:999px; font-size:.85rem; font-weight:800;
       background:{ACCENT}; color:#001621; margin:0 8px 8px 0; }}
.stTextInput > div > div > input, .stTextArea textarea {{
  background:#0F1420 !important; color:{TEXT} !important; border:1px solid #20283A !important; border-radius:10px; font-size:18px;
}}
.stDateInput input, .stTimeInput input {{
  background:#0F1420 !important; color:{TEXT} !important; border:1px solid #20283A !important; border-radius:10px; font-size:18px;
}}
.stButton > button {{ background:{PRIMARY}; color:#ffffff; font-weight:900; border-radius:10px; border:none; font-size:18px; }}
.explain {{ margin-top:10px; border-left: 3px solid {ACCENT}; padding:10px 12px; background:#101623; border-radius:10px; }}
</style>
""", unsafe_allow_html=True)

# =========================
# STATE
# =========================
def init_state():
    if "events" not in st.session_state:
        today = date.today()
        st.session_state.events = [
            {"title": "Daily Ops", "when": datetime.combine(today, dt_time(9))},
            {"title": "Comité Comercial", "when": datetime.combine(today + timedelta(days=1), dt_time(11))},
            {"title": "Revisión Inventarios", "when": datetime.combine(today + timedelta(days=2), dt_time(10))},
        ]
    if "chat_email" not in st.session_state: st.session_state.chat_email = []
    if "chat_whatsapp" not in st.session_state: st.session_state.chat_whatsapp = []
    if "activity_log" not in st.session_state: st.session_state.activity_log = []

init_state()

def log(evt:str):
    st.session_state.activity_log.append({"ts": datetime.now().strftime("%H:%M:%S"), "event": evt})

# =========================
# HELPERS (acciones simuladas)
# =========================
def schedule_meeting(title:str, d:date, t:dt_time):
    when = datetime.combine(d, t)
    st.session_state.events.append({"title": title, "when": when})
    st.toast(f"Google Calendar: '{title}' — {when.strftime('%d/%m/%Y %H:%M')}")
    log(f"Calendar: {title} @ {when.strftime('%d/%m %H:%M')}")

def assign_sdac(task:str):
    asg_id = f"SDAC-{np.random.randint(1000, 9999)}"
    st.toast(f"SDAC: asignación {asg_id} — {task}")
    log(f"SDAC: {asg_id} — {task}")

def send_slack(channel:str, text:str):
    st.toast(f"Slack: #{channel} — enviado")
    log(f"Slack #{channel}: {text}")

def send_whatsapp(to:str, text:str):
    st.session_state.chat_whatsapp.append({"ts": datetime.now().strftime("%H:%M"), "to": to, "text": text})
    st.toast(f"WhatsApp a {to}: enviado")
    log(f"WhatsApp a {to}: {text[:60]}")

def send_email(frm:str, to:str, subject:str, body:str):
    st.session_state.chat_email.append({"ts": datetime.now().strftime("%H:%M"), "from": frm, "to": to, "subject": subject, "body": body})
    st.toast(f"Correo a {to}: {subject}")
    log(f"Mail a {to}: {subject}")

# =========================
# DATA SYNTH (inventarios + serie)
# =========================
@st.cache_data(show_spinner=False)
def make_inventory(seed=7, days=120):
    rng = np.random.default_rng(seed)
    regions = ["Centro", "Norte", "Occidente", "Sureste"]
    cats = ["Abarrotes","Perecederos","Hogar","Electrónica","Farmacia","Moda"]
    skus = [f"SKU-{i:05d}" for i in range(120, 200)]
    rows = []
    for sku in skus:
        cat = rng.choice(cats); reg = rng.choice(regions)
        stock = max(0, int(rng.normal(360, 120)))
        reorder = int(max(50, rng.normal(300, 90)))
        daily = max(1, int(rng.normal(28, 7)))
        cover = round(stock / max(1, daily), 1)
        rows.append([sku, cat, reg, stock, reorder, daily, cover])
    inv = pd.DataFrame(rows, columns=["sku","category","region","stock","reorder_point","daily_demand","days_cover"])
    inv["below_reorder"] = (inv["stock"] < inv["reorder_point"]).astype(int)

    end = date.today()
    dates = pd.date_range(end - timedelta(days=days-1), end, freq="D")
    ts_rows = []
    for d in dates:
        for reg in regions:
            total_stock = max(5000, int(rng.normal(8200, 1100)))
            ts_rows.append([d, reg, total_stock])
    inv_ts = pd.DataFrame(ts_rows, columns=["date","region","total_stock"])
    return inv, inv_ts, regions, cats

inventory, inv_ts, REGIONS, CATS = make_inventory()

# =========================
# HEADER (branding + saludo + reloj)
# =========================
def greeting():
    h = datetime.now().hour
    return "¡Buenos días!" if 5 <= h < 12 else ("¡Buenas tardes!" if 12 <= h < 19 else "¡Buenas noches!")

left, right = st.columns([3.2, 1.1], gap="large")
with left:
    logo_html = f'<img src="{LOGO_URL}" style="height:38px;border-radius:6px;">' if LOGO_URL else ""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
          {logo_html}
          <div class="badge">{BRAND_NAME}</div>
          <div style="font-weight:900;font-size:1.3rem;">Agente MCP + ADK — {BRAND_AREA}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.caption("Agenda, inventarios, mensajería e insights con explicaciones dinámicas por sección.")
with right:
    now = datetime.now()
    st.markdown(
        f"""
        <div class="card" style="text-align:center;">
          <div style="font-weight:900">{greeting()}</div>
          <div style="opacity:.8;margin-top:4px;">{now.strftime('%A %d %B %Y')}</div>
          <div style="font-size:1.1rem;margin-top:2px;">🕒 {now.strftime('%H:%M')}</div>
        </div>
        """, unsafe_allow_html=True
    )

st.markdown('<hr class="section"/>', unsafe_allow_html=True)

# =========================
# SIDEBAR (AHORA DINÁMICO: destinatarios + plantillas)
# =========================
with st.sidebar:
    st.markdown("### ⚙️ Acciones rápidas")
    # Destinatarios / personalización
    st.caption("Destinatarios y plantillas")
    email_to = st.text_input("Correo destino", value="direccion@empresa.mx")
    slack_channel = st.text_input("Canal Slack (sin #)", value="logistica")
    wa_to = st.text_input("WhatsApp (tel.)", value="+52 55 0000 0000")
    plantilla = st.selectbox("Plantilla de mensaje", [
        "Ejecutivo: resumen + próximas acciones",
        "Operaciones: reabasto y cobertura",
        "Comercial: campañas y disponibilidad"
    ])
    if plantilla == "Ejecutivo: resumen + próximas acciones":
        default_msg = "Resumen ejecutivo: SKUs críticos priorizados; junta programada; acciones en SDAC y notificaciones enviadas."
    elif plantilla == "Operaciones: reabasto y cobertura":
        default_msg = "Operaciones: reabasto crítico asignado; monitoreo de cobertura diario; validar tiempos de entrega."
    else:
        default_msg = "Comercial: coordinar campañas con disponibilidad y ajustar exhibición en tiendas clave."
    msg_text = st.text_area("Mensaje", value=default_msg, height=120)

    st.markdown("---")
    st.caption("Acciona con la configuración anterior")
    colA, colB = st.columns(2, gap="small")
    with colA:
        if st.button("✉️ Enviar correo"):
            send_email("agente@empresa.mx", email_to, "Actualización — Inventarios & Agenda", msg_text)
    with colB:
        if st.button("💬 Enviar a Slack"):
            send_slack(slack_channel, msg_text)
    colC, colD = st.columns(2, gap="small")
    with colC:
        if st.button("🟢 Enviar WhatsApp"):
            send_whatsapp(wa_to, msg_text)
    with colD:
        if st.button("🧾 Crear SDAC (reabasto)"):
            assign_sdac("Reabasto crítico — priorización por brecha y cobertura")

    st.markdown("---")
    st.caption("Filtros inventario")
    f_region = st.multiselect("Región", REGIONS)
    f_category = st.multiselect("Categoría", CATS)
    st.caption("Ventana tendencias")
    horizon_days = st.slider("Días", 30, 120, 60, 10)

# Filtros aplicados
inv_view = inventory.copy()
if f_region: inv_view = inv_view[inv_view["region"].isin(f_region)]
if f_category: inv_view = inv_view[inv_view["category"].isin(f_category)]
cut = inv_ts["date"].max() - pd.Timedelta(days=horizon_days-1)
inv_ts_view = inv_ts[(inv_ts["date"] >= cut) & (inv_ts["region"].isin(f_region) if f_region else inv_ts["region"].notna())]

# =========================
# FUNCIONES DE EXPLICACIÓN (por sección)
# =========================
def explain_trend(ts_df: pd.DataFrame, regions_sel):
    if ts_df.empty:
        return "No hay datos en la ventana seleccionada."
    change = (ts_df["total_stock"].iloc[-1] - ts_df["total_stock"].iloc[0]) / max(1, ts_df["total_stock"].iloc[0]) * 100
    region_txt = ", ".join(regions_sel) if regions_sel else "todas las regiones"
    direction = "alza" if change >= 0 else "baja"
    return (f"**Tendencia:** el stock total para {region_txt} muestra una variación de **{change:.1f}%** "
            f"en la ventana de **{horizon_days} días**, con sesgo a la **{direction}**. "
            "Sugerencia: anticipar reabasto previo a picos semanales y validar lead times.")

def explain_heatmap(hm_df: pd.DataFrame):
    if hm_df.empty:
        return "Sin brechas de reabasto en la combinación categoría–región actual."
    top = hm_df.sort_values("gap_qty", ascending=False).head(1).iloc[0]
    return (f"**Brecha concentrada:** mayor gap en **{top['category']}** para **{top['region']}**. "
            "Priorizar asignaciones en esa intersección y ajustar puntos de pedido.")

def explain_treemap(by_cat_df: pd.DataFrame):
    if by_cat_df.empty:
        return "No hay categorías con brecha para mostrar."
    leaders = by_cat_df.head(3)["category"].tolist()
    return (f"**Top categorías con brecha:** {', '.join(leaders)}. "
            "Recom: revisar surtido, cobertura objetivo y elasticidad de demanda por categoría.")

def explain_table(inv_df: pd.DataFrame):
    if inv_df.empty:
        return "No hay SKUs para revisar con los filtros actuales."
    below = int(inv_df["below_reorder"].sum())
    cover = inv_df["days_cover"].mean()
    return (f"**Estado de SKUs:** {below} elementos por debajo del punto de pedido; "
            f"cobertura promedio **{cover:.1f} días**. Acciones: reabasto dirigido y ajuste de reorder points.")

# =========================
# TABS
# =========================
tab_agenda, tab_inv, tab_insights, tab_msgs, tab_log = st.tabs(
    ["📅 Agenda", "📦 Inventarios (SQL Server)", "📊 Insights", "💬 Mensajería", "🗂️ Bitácora"]
)

# -------- Agenda
with tab_agenda:
    a1, a2 = st.columns([2.2, 1.2], gap="large")
    with a1:
        st.markdown('<div class="section-title">Programar reunión</div>', unsafe_allow_html=True)
        mt_title = st.text_input("Título", value="Junta de seguimiento")
        mt_date = st.date_input("Fecha", value=date.today() + timedelta(days=1))
        mt_time = st.time_input("Hora", value=dt_time(9,0))
        attendees = st.text_input("Invitados (coma separada)", value=f"{email_to}, ops@empresa.mx")
        if st.button("➕ Agregar a Google Calendar"):
            schedule_meeting(mt_title, mt_date, mt_time)
    with a2:
        st.markdown('<div class="section-title">Próximos eventos</div>', unsafe_allow_html=True)
        if st.session_state.events:
            ev = pd.DataFrame(st.session_state.events).sort_values("when")
            ev["Fecha"] = ev["when"].dt.strftime("%d/%m/%Y")
            ev["Hora"] = ev["when"].dt.strftime("%H:%M")
            st.dataframe(ev[["Fecha","Hora","title"]].rename(columns={"title":"Evento"}), hide_index=True, use_container_width=True)
            cal = pd.DataFrame([{"date": e["when"].date()} for e in st.session_state.events]).value_counts("date").reset_index(name="events")
            fig_cal = px.density_heatmap(cal, x="date", y=["Eventos"]*len(cal), z="events", nbinsx=7, color_continuous_scale="Turbo")
            fig_cal.update_layout(height=140, margin=dict(l=10,r=10,t=10,b=10), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_cal, use_container_width=True)
        else:
            st.info("Sin eventos programados.")

# -------- Inventarios (tabla + explicación local)
with tab_inv:
    i1, i2 = st.columns([1.6, 2.4], gap="large")
    with i1:
        st.markdown('<div class="section-title">Resumen</div>', unsafe_allow_html=True)
        below = int(inv_view["below_reorder"].sum())
        pct_below = 100 * below / max(1, len(inv_view))
        avg_cover = inv_view["days_cover"].mean()
        k1,k2,k3 = st.columns(3)
        k1.markdown(f'<div class="kpi-card"><div class="kpi-title">SKUs bajo punto de pedido</div><div class="kpi-value">{below:,}</div><div class="kpi-sub">{pct_below:.1f}% del total</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card"><div class="kpi-title">Cobertura prom.</div><div class="kpi-value">{avg_cover:.1f} días</div><div class="kpi-sub">days of cover</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card"><div class="kpi-title">Artefactos</div><div class="kpi-value">CSV / Gráficos</div><div class="kpi-sub">exportables</div></div>', unsafe_allow_html=True)
        st.markdown('<hr class="section"/>', unsafe_allow_html=True)
        st.markdown("**Acciones operativas**")
        if st.button("🧾 Asignar logística (SDAC) — críticos"):
            assign_sdac("Reabasto críticos: priorizar CD/tiendas para top SKUs")
        st.download_button("📥 Exportar inventario (CSV)", data=inv_view.to_csv(index=False).encode("utf-8"),
                           file_name="inventario_filtrado.csv")
    with i2:
        st.markdown('<div class="section-title">Detalle de inventario</div>', unsafe_allow_html=True)
        st.dataframe(inv_view[["sku","category","region","stock","reorder_point","daily_demand","days_cover"]],
                     hide_index=True, use_container_width=True)
        st.markdown(f'<div class="explain">{explain_table(inv_view)}</div>', unsafe_allow_html=True)

# -------- Insights (3 visuales; cada uno con explicación local justo debajo)
with tab_insights:
    st.markdown('<div class="section-title">Tendencias y focos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2.2, 1.5, 1.3], gap="large")

    # Serie tendencial
    ts = inv_ts_view.groupby("date", as_index=False)["total_stock"].sum()
    fig_ts = px.line(ts, x="date", y="total_stock", markers=True, color_discrete_sequence=[ACCENT])
    fig_ts.update_traces(line=dict(width=3))
    fig_ts.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    c1.plotly_chart(fig_ts, use_container_width=True)
    c1.markdown(f'<div class="explain">{explain_trend(ts, f_region)}</div>', unsafe_allow_html=True)

    # Heatmap cat-reg
    inv_h = inv_view.copy()
    inv_h["gap_qty"] = (inv_h["reorder_point"] - inv_h["stock"]).clip(lower=0)
    heat = inv_h.groupby(["category","region"], as_index=False)["gap_qty"].sum()
    fig_hm = px.density_heatmap(heat, x="region", y="category", z="gap_qty", color_continuous_scale="Turbo")
    fig_hm.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    c2.plotly_chart(fig_hm, use_container_width=True)
    c2.markdown(f'<div class="explain">{explain_heatmap(heat)}</div>', unsafe_allow_html=True)

    # Treemap por categoría
    by_cat = inv_h.groupby("category", as_index=False)["gap_qty"].sum().sort_values("gap_qty", ascending=False)
    fig_tree = px.treemap(by_cat, path=["category"], values="gap_qty", color="gap_qty", color_continuous_scale="Magma")
    fig_tree.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    c3.plotly_chart(fig_tree, use_container_width=True)
    c3.markdown(f'<div class="explain">{explain_treemap(by_cat)}</div>', unsafe_allow_html=True)

# -------- Mensajería (envío + historial)
with tab_msgs:
    st.markdown('<div class="section-title">Mensajes enviados desde esta sesión</div>', unsafe_allow_html=True)
    colm1, colm2 = st.columns(2, gap="large")
    with colm1:
        st.subheader("Correo")
        if st.session_state.chat_email:
            dfm = pd.DataFrame(st.session_state.chat_email)
            st.dataframe(dfm[["ts","to","subject","body"]].rename(columns={"ts":"Hora","to":"Para","subject":"Asunto","body":"Mensaje"}),
                         hide_index=True, use_container_width=True)
        else:
            st.info("Sin correos aún.")
    with colm2:
        st.subheader("WhatsApp")
        if st.session_state.chat_whatsapp:
            dfw = pd.DataFrame(st.session_state.chat_whatsapp)
            st.dataframe(dfw.rename(columns={"ts":"Hora","to":"Para","text":"Mensaje"}),
                         hide_index=True, use_container_width=True)
        else:
            st.info("Sin mensajes aún.")

# -------- Bitácora
with tab_log:
    st.markdown('<div class="section-title">Bitácora de acciones</div>', unsafe_allow_html=True)
    logs = pd.DataFrame(st.session_state.activity_log) if st.session_state.activity_log else pd.DataFrame([{"ts":"—","event":"(sin eventos)"}])
    st.dataframe(logs, hide_index=True, use_container_width=True)

# -------- Proceso del agente (píldoras)
st.markdown('<hr class="section"/>', unsafe_allow_html=True)
st.markdown("**Proceso del agente**")
st.markdown(
    f'<span class="pill">Planner</span> '
    f'<span class="pill">Discovery</span> '
    f'<span class="pill">Conexiones</span> '
    f'<span class="pill">Ejecución</span> '
    f'<span class="pill">Artefactos</span> '
    f'<span class="pill">Narrativa por sección</span>',
    unsafe_allow_html=True
)
