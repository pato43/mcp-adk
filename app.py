# app.py
# Agente MCP + ADK — Orquestación Empresarial (Agenda, Inventarios, Mensajería, Insights, Explicaciones LLM)
# UI oscura, full-width, intuitiva. Acciones simuladas con toasts + bitácora.

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, time as dt_time, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time as pytime

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

px.defaults.template = "plotly_dark"

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
    if "notes" not in st.session_state: st.session_state.notes = []
    if "activity_log" not in st.session_state: st.session_state.activity_log = []
    if "started" not in st.session_state: st.session_state.started = False
    if "global_role" not in st.session_state: st.session_state.global_role = "Operaciones & Logística"

def log(evt:str):
    st.session_state.activity_log.append({"ts": datetime.now().strftime("%H:%M:%S"), "event": evt})

init_state()

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
    st.toast(f"SDAC: asignación creada {asg_id} — {task}")
    log(f"SDAC: {asg_id} — {task}")

def send_slack(channel:str, text:str):
    st.toast(f"Slack: #{channel} — {text}")
    log(f"Slack #{channel}: {text}")

def send_whatsapp(to:str, text:str):
    st.session_state.chat_whatsapp.append({"ts": datetime.now().strftime("%H:%M"), "to": to, "text": text})
    st.toast(f"WhatsApp: a {to}")
    log(f"WhatsApp a {to}: {text[:60]}")

def send_email(frm:str, to:str, subject:str, body:str):
    st.session_state.chat_email.append({"ts": datetime.now().strftime("%H:%M"), "from": frm, "to": to, "subject": subject, "body": body})
    st.toast(f"Correo: {to} — {subject}")
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
    return inv, inv_ts

inventory, inv_ts = make_inventory()

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
    st.caption("Asistente inteligente para agenda, inventarios, mensajería e insights.")
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
# SIDEBAR (acciones rápidas + filtros)
# =========================
with st.sidebar:
    st.markdown("### ⚙️ Acciones rápidas")
    if st.button("📅 Junta mañana 09:00"):
        schedule_meeting("Junta de seguimiento", date.today()+timedelta(days=1), dt_time(9,0))
    if st.button("🧾 SDAC: asignar reabasto críticos"):
        assign_sdac("Reabasto crítico — top 10 SKUs bajo punto de pedido")
    if st.button("💬 Slack #logistica"):
        send_slack("logistica", "Se asignó reabasto crítico; verificar CD y tiendas.")
    if st.button("🟢 WhatsApp supervisor"):
        send_whatsapp("+52 55 0000 0000", "Recordatorio: revisión de reabasto crítico, 09:00 mañana.")
    if st.button("✉️ Correo a Dirección"):
        send_email("agente@empresa.mx","direccion@empresa.mx","Resumen inventarios & agenda",
                   "Adjunto KPIs, SKUs críticos y calendario de revisión.")

    st.markdown("---")
    st.caption("Filtros inventario")
    f_region = st.multiselect("Región", sorted(inventory["region"].unique()))
    f_category = st.multiselect("Categoría", sorted(inventory["category"].unique()))
    st.caption("Ventana tendencias")
    horizon_days = st.slider("Días", 30, 120, 60, 10)

# Filtros aplicados
inv_view = inventory.copy()
if f_region: inv_view = inv_view[inv_view["region"].isin(f_region)]
if f_category: inv_view = inv_view[inv_view["category"].isin(f_category)]
cut = inv_ts["date"].max() - pd.Timedelta(days=horizon_days-1)
inv_ts_view = inv_ts[(inv_ts["date"] >= cut) & (inv_ts["region"].isin(f_region) if f_region else inv_ts["region"].notna())]

# =========================
# EXPANDER: mini guía
# =========================
with st.expander("💡 Guía rápida"):
    st.markdown("""
- **Agenda & Calendario**: programa reuniones por fecha/hora y visualiza próximos eventos.
- **Inventarios (SQL Server)**: tabla de SKUs, brechas y exportaciones. Acciones de logística (SDAC).
- **Mensajería**: enviar/visualizar correos y WhatsApp.
- **Insights**: gráficos + explicación automática.
- **Explicaciones LLM**: genera narrativa dinámica (rol, tono, detalle), bullets accionables y resumen ejecutivo.
- **Notas**: registra pendientes rápidos.
""")

# =========================
# TABS PRINCIPALES
# =========================
tab_agenda, tab_invent, tab_msgs, tab_insights, tab_llm, tab_notes, tab_log = st.tabs(
    ["📅 Agenda", "📦 Inventarios (SQL Server)", "💬 Mensajería", "📊 Insights", "🧠 Explicaciones LLM", "🗒️ Notas", "🗂️ Bitácora"]
)

# -------- Agenda
with tab_agenda:
    a1, a2 = st.columns([2.2, 1.2], gap="large")
    with a1:
        st.markdown('<div class="section-title">Programar reunión</div>', unsafe_allow_html=True)
        mt_title = st.text_input("Título", value="Junta de seguimiento")
        mt_date = st.date_input("Fecha", value=date.today() + timedelta(days=1))
        mt_time = st.time_input("Hora", value=dt_time(9,0))
        attendees = st.text_input("Invitados (coma separada)", value="direccion@empresa.mx, ops@empresa.mx")
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

# -------- Inventarios (SQL Server)
with tab_invent:
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
            assign_sdac("Reabasto críticos: priorizar CD y tiendas p/ top 10 SKUs")
        st.download_button("📥 Exportar inventario (CSV)", data=inv_view.to_csv(index=False).encode("utf-8"), file_name="inventario_filtrado.csv")
    with i2:
        st.markdown('<div class="section-title">Detalle de inventario</div>', unsafe_allow_html=True)
        st.dataframe(inv_view[["sku","category","region","stock","reorder_point","daily_demand","days_cover"]],
                     hide_index=True, use_container_width=True)
        st.markdown('<hr class="section"/>', unsafe_allow_html=True)
        inv_g = inv_view.copy()
        inv_g["gap_qty"] = (inv_g["reorder_point"] - inv_g["stock"]).clip(lower=0)
        by_reg = inv_g.groupby("region", as_index=False)["gap_qty"].sum().sort_values("gap_qty", ascending=False)
        fig_bar = px.bar(by_reg, x="region", y="gap_qty", color="region", color_discrete_sequence=px.colors.qualitative.Prism)
        fig_bar.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

# -------- Mensajería (Correo & WhatsApp)
with tab_msgs:
    st.markdown('<div class="section-title">Bandejas</div>', unsafe_allow_html=True)
    m1, m2 = st.columns([1,1], gap="large")
    with m1:
        st.subheader("Correo")
        frm = st.text_input("De", value="agente@empresa.mx", key="mail_from")
        to = st.text_input("Para", value="direccion@empresa.mx", key="mail_to")
        subject = st.text_input("Asunto", value=f"Resumen — {BRAND_NAME}", key="mail_subj")
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

# -------- Insights (tendencias + heatmap + treemap)
with tab_insights:
    st.markdown('<div class="section-title">Tendencias y focos</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2.2, 1.5, 1.3], gap="large")
    ts = inv_ts_view.groupby("date", as_index=False)["total_stock"].sum()
    fig_ts = px.line(ts, x="date", y="total_stock", markers=True, color_discrete_sequence=[ACCENT])
    fig_ts.update_traces(line=dict(width=3))
    fig_ts.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    c1.plotly_chart(fig_ts, use_container_width=True)

    inv_h = inv_view.copy()
    inv_h["gap_qty"] = (inv_h["reorder_point"] - inv_h["stock"]).clip(lower=0)
    heat = inv_h.groupby(["category","region"], as_index=False)["gap_qty"].sum()
    fig_hm = px.density_heatmap(heat, x="region", y="category", z="gap_qty", color_continuous_scale="Turbo")
    fig_hm.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    c2.plotly_chart(fig_hm, use_container_width=True)

    by_cat = inv_h.groupby("category", as_index=False)["gap_qty"].sum().sort_values("gap_qty", ascending=False)
    fig_tree = px.treemap(by_cat, path=["category"], values="gap_qty", color="gap_qty", color_continuous_scale="Magma")
    fig_tree.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    c3.plotly_chart(fig_tree, use_container_width=True)

# -------- Explicaciones LLM (dinámicas)
with tab_llm:
    st.markdown('<div class="section-title">Narrativa del agente</div>', unsafe_allow_html=True)
    cA, cB, cC = st.columns([1.1, 1.1, 2.2], gap="large")
    with cA:
        role = st.selectbox("Rol destinatario", ["Dirección", "Operaciones & Logística", "Ventas & Comercial", "Finanzas", "TI / Datos"], index=1, key="llm_role")
        tone = st.selectbox("Tono", ["Ejecutivo", "Técnico", "Persuasivo", "Neutro"], index=0, key="llm_tone")
    with cB:
        depth = st.slider("Nivel de detalle", 1, 5, 3, key="llm_depth")
        bullets = st.checkbox("Bullets accionables", value=True, key="llm_bullets")
        include_risks = st.checkbox("Incluir riesgos", value=True, key="llm_risks")
    with cC:
        st.text_area("Contexto opcional", placeholder="Añade contexto del negocio (campañas, estacionalidad, restricciones)...", key="llm_ctx")

    # Variables para narrativa (derivadas de datos en pantalla)
    top_cat = by_cat.iloc[0]["category"] if len(by_cat) else "—"
    top_reg = heat.sort_values("gap_qty", ascending=False).iloc[0]["region"] if len(heat) else "—"
    kpi_below = int(inv_view["below_reorder"].sum())
    kpi_cover = inv_view["days_cover"].mean()

    def gen_narrative():
        intro = f"Resumen para {st.session_state.llm_role} — tono {st.session_state.llm_tone.lower()}."
        core = (f"Se identifica concentración de brecha en **{top_cat}** con mayor impacto en **{top_reg}**. "
                f"Actualmente existen **{kpi_below} SKUs** por debajo del punto de pedido; cobertura promedio **{kpi_cover:.1f} días**.")
        ctx = f" Contexto: {st.session_state.llm_ctx.strip()}" if st.session_state.llm_ctx else ""
        detail = " Profundizar en reposición anticipada y ajuste de setpoints." if st.session_state.llm_depth >= 3 else ""
        risks = " Riesgos: quiebres por variabilidad de demanda y lead time." if st.session_state.llm_risks else ""
        acts = ("- Aumentar inventario objetivo en top categorías/regiones\n"
                "- Priorizar surtido en tiendas con menor cobertura\n"
                "- Revisar parámetros de reorden y tiempos de entrega") if st.session_state.llm_bullets else ""
        return intro + "\n\n" + core + ctx + detail + risks + ("\n\n**Acciones sugeridas**:\n" + acts if acts else "")

    colBtns = st.columns([1,1,1,2], gap="large")
    with colBtns[0]:
        if st.button("🧠 Generar explicación"):
            st.session_state.llm_text = gen_narrative()
    with colBtns[1]:
        if st.button("🔁 Regenerar"):
            st.session_state.llm_text = gen_narrative()
    with colBtns[2]:
        if st.button("📄 Resumen ejecutivo"):
            st.session_state.llm_text = f"Executive brief: {kpi_below} SKUs críticos; foco en {top_cat}/{top_reg}; cobertura {kpi_cover:.1f} días."
    with colBtns[3]:
        if st.button("✅ Bullets accionables"):
            st.session_state.llm_text = ("- Reabasto en {0}/{1}\n- Ajustar reorder points\n- Monitoreo diario cobertura"
                                         .format(top_cat, top_reg))

    st.markdown('<hr class="section"/>', unsafe_allow_html=True)
    st.markdown(st.session_state.get("llm_text","_Pulsa “Generar explicación” para crear la narrativa del agente._"))

# -------- Notas (sin botón flotante; CRUD básico)
with tab_notes:
    st.markdown('<div class="section-title">Notas rápidas</div>', unsafe_allow_html=True)
    cols = st.columns([1.6, 1.6, 1], gap="large")
    with cols[0]:
        nt_title = st.text_input("Título de nota", value="", key="note_title")
    with cols[1]:
        nt_body = st.text_input("Contenido", value="", key="note_body")
    with cols[2]:
        if st.button("➕ Guardar nota"):
            if nt_title.strip():
                st.session_state.notes.append({
                    "id": int(datetime.now().timestamp()*1000),
                    "title": nt_title.strip(),
                    "body": nt_body.strip(),
                    "pinned": False,
                    "done": False,
                    "ts": datetime.now().strftime("%d/%m %H:%M")
                })
                st.toast("Nota guardada")

    if st.session_state.notes:
        notes_sorted = sorted(st.session_state.notes, key=lambda x: (not x["pinned"], x["done"]))
        grid = st.columns(3, gap="large")
        for idx, n in enumerate(notes_sorted):
            with grid[idx % 3]:
                st.markdown(f"""
<div class="card" style="border-left: 4px solid {'#22C55E' if n['done'] else PRIMARY};">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div style="font-weight:900;">{n['title']}</div>
    <div style="opacity:.7;font-size:.85rem;">{n['ts']}</div>
  </div>
  <div style="opacity:.9;margin-top:6px;">{n['body'] or '<i>(sin contenido)</i>'}</div>
</div>
""", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1,1,1])
                if c1.button(("📌 Quitar" if n["pinned"] else "📌 Fijar"), key=f"pin_{n['id']}"):
                    n["pinned"] = not n["pinned"]
                if c2.button(("✅ Desmarcar" if n["done"] else "✅ Hecho"), key=f"done_{n['id']}"):
                    n["done"] = not n["done"]
                if c3.button("🗑️ Borrar", key=f"del_{n['id']}"):
                    st.session_state.notes = [x for x in st.session_state.notes if x["id"] != n["id"]]
                    st.experimental_rerun()
    else:
        st.info("Sin notas todavía. Crea la primera arriba 👆")

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
    f'<span class="pill">Narrativa</span>',
    unsafe_allow_html=True
)
