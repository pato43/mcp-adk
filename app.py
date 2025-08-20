# app.py
# Agente MCP + ADK — con Branding, Saludo/Clock, Notas y Guía
# (listo para mezclar con tu app existente)

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, time as dt_time, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time as pytime

# =========================
# CONFIG BASE (tema oscuro + tipografía grande)
# =========================
st.set_page_config(page_title="Agente MCP + ADK — Enterprise", layout="wide", page_icon="🧠")

# -------- BRANDING (EDITA AQUÍ) --------
BRAND_NAME = "Atlas Data Suite"
BRAND_AREA = "Operaciones & Comercial"
PRIMARY = "#7C3AED"   # morado
ACCENT  = "#22D3EE"   # cian
ACCENT_2 = "#6EE7F9"  # cian claro
BG = "#0E1117"
CARD = "#151B28"
TEXT = "#F5F7FA"
MUTED = "#A7B0BE"
LOGO_URL = ""  # opcional: pega URL pública de tu logo (png/svg). Si vacío, muestra sólo texto.

px.defaults.template = "plotly_dark"

# -------- ESTILOS --------
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {{
  background-color: {BG}; color: {TEXT};
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  font-size: 18px;
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
/* Widget flotante simple (Notas) */
.fab-notes {{
  position: fixed; right: 18px; bottom: 18px; z-index: 9999;
  background: {PRIMARY}; color: white; border-radius: 999px; padding: 12px 16px; font-weight: 900;
  box-shadow: 0 10px 24px rgba(0,0,0,.35); cursor: pointer; user-select: none;
}}
</style>
""", unsafe_allow_html=True)

# =========================
# ESTADO BÁSICO
# =========================
if "events" not in st.session_state:
    today = date.today()
    st.session_state.events = [
        {"title": "Daily Ops", "when": datetime.combine(today, dt_time(hour=9))},
        {"title": "Comité Comercial", "when": datetime.combine(today + timedelta(days=1), dt_time(hour=11))},
        {"title": "Revisión Inventarios", "when": datetime.combine(today + timedelta(days=2), dt_time(hour=10))},
    ]
if "notes" not in st.session_state:
    st.session_state.notes = []  # [{id, title, body, pinned, done, ts}]
if "show_notes" not in st.session_state:
    st.session_state.show_notes = False

# =========================
# SALUDO + RELOJ (encabezado con branding)
# =========================
def get_greeting():
    # Usa hora local del servidor. Si quieres forzar CDMX, podrías sumar/restar offset.
    now = datetime.now().hour
    if 5 <= now < 12:
        return "¡Buenos días!"
    elif 12 <= now < 19:
        return "¡Buenas tardes!"
    else:
        return "¡Buenas noches!"

def brand_header():
    left, right = st.columns([3.2, 1.0], gap="large")
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
        st.caption("Asistente inteligente para gestión operativa, comunicación y análisis visual.")
    with right:
        now = datetime.now()
        st.markdown(
            f"""
            <div class="card" style="text-align:center;">
              <div style="font-weight:900">{get_greeting()}</div>
              <div style="opacity:.8;margin-top:4px;">{now.strftime('%A %d %B %Y')}</div>
              <div style="font-size:1.1rem;margin-top:2px;">🕒 {now.strftime('%H:%M')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

brand_header()
st.markdown('<hr class="section"/>', unsafe_allow_html=True)

# =========================
# GUIA RÁPIDA (ayuda plegable)
# =========================
with st.expander("💡 Guía rápida"):
    st.markdown("""
- **Agenda & Calendario**: programa reuniones con fecha/hora y visualiza próximos eventos.
- **Inventarios**: revisa SKUs críticos (estilo SQL Server), exporta CSV y genera acciones de logística.
- **Mensajería**: envía/resume correos y WhatsApp desde un mismo lugar (historial visible).
- **Insights**: gráficos vistosos y narrativa automática para tomar acción.
- **Notas**: usa el botón flotante (abajo a la derecha) para crear recordatorios rápidos.
""")

# =========================
# TABS PRINCIPALES (estructura base para integrar tu lógica existente)
# =========================
tab_agenda, tab_invent, tab_msgs, tab_insights = st.tabs(
    ["📅 Agenda & Calendario", "📦 Inventarios", "💬 Mensajería", "📊 Insights"]
)

# ============== AGENDA
with tab_agenda:
    a1, a2 = st.columns([2.2, 1.2], gap="large")
    with a1:
        st.markdown('<div class="section-title">Programar reunión</div>', unsafe_allow_html=True)
        mt_title = st.text_input("Título", value="Junta de seguimiento")
        mt_date = st.date_input("Fecha", value=date.today() + timedelta(days=1))
        mt_time = st.time_input("Hora", value=dt_time(hour=9, minute=0))
        attendees = st.text_input("Invitados (coma separada)", value="direccion@empresa.mx, ops@empresa.mx")
        if st.button("➕ Agregar a Google Calendar"):
            when = datetime.combine(mt_date, mt_time)
            st.session_state.events.append({"title": mt_title, "when": when})
            st.toast(f"Evento agregado a Google Calendar: {mt_title} — {when.strftime('%d/%m/%Y %H:%M')}")
    with a2:
        st.markdown('<div class="section-title">Próximos eventos</div>', unsafe_allow_html=True)
        if st.session_state.events:
            ev = pd.DataFrame(st.session_state.events).sort_values("when")
            ev["Fecha"] = ev["when"].dt.strftime("%d/%m/%Y")
            ev["Hora"] = ev["when"].dt.strftime("%H:%M")
            st.dataframe(ev[["Fecha","Hora","title"]].rename(columns={"title":"Evento"}), hide_index=True, use_container_width=True)
            # Mini “calendario” por densidad
            cal = pd.DataFrame([{"date": e["when"].date()} for e in st.session_state.events])
            cal = cal.value_counts("date").reset_index(name="events")
            fig_cal = px.density_heatmap(cal, x="date", y=["Eventos"]*len(cal), z="events",
                                         nbinsx=7, color_continuous_scale="Turbo")
            fig_cal.update_layout(height=140, margin=dict(l=10,r=10,t=10,b=10), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_cal, use_container_width=True)
        else:
            st.info("Sin eventos programados.")

# ============== INVENTARIOS (demo básica; sustituye por tus consultas/visuales)
@st.cache_data(show_spinner=False)
def make_inventory(seed=7, n=120):
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
    df = pd.DataFrame(rows, columns=["sku","category","region","stock","reorder_point","daily_demand","days_cover"])
    df["below_reorder"] = (df["stock"] < df["reorder_point"]).astype(int)
    return df

inventory = make_inventory()

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
        st.markdown("**Acciones rápidas**")
        if st.button("🧾 Asignar logística (SDAC) — críticos"):
            st.toast("SDAC: asignación creada para reabasto de SKUs críticos")
        st.download_button("📥 Exportar inventario (CSV)", data=inventory.to_csv(index=False).encode("utf-8"),
                           file_name="inventario.csv")
    with i2:
        st.markdown('<div class="section-title">Detalle de inventario</div>', unsafe_allow_html=True)
        st.dataframe(inventory, hide_index=True, use_container_width=True)
        st.markdown('<hr class="section"/>', unsafe_allow_html=True)
        inv = inventory.copy()
        inv["gap_qty"] = (inv["reorder_point"] - inv["stock"]).clip(lower=0)
        by_reg = inv.groupby("region", as_index=False)["gap_qty"].sum().sort_values("gap_qty", ascending=False)
        fig_bar = px.bar(by_reg, x="region", y="gap_qty", color="region", color_discrete_sequence=px.colors.qualitative.Prism)
        fig_bar.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

# ============== MENSAJERÍA (Correo & WhatsApp)
if "chat_email" not in st.session_state: st.session_state.chat_email = []
if "chat_whatsapp" not in st.session_state: st.session_state.chat_whatsapp = []

def send_email(frm, to, subject, body):
    st.session_state.chat_email.append({"ts": datetime.now().strftime("%H:%M"), "from": frm, "to": to, "subject": subject, "body": body})
    st.toast(f"Correo enviado a {to}: {subject}")

def send_whatsapp(to, text):
    st.session_state.chat_whatsapp.append({"ts": datetime.now().strftime("%H:%M"), "to": to, "text": text})
    st.toast(f"WhatsApp enviado a {to}")

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

# ============== INSIGHTS (placeholder listo para tus gráficos)
with tab_insights:
    st.markdown('<div class="section-title">Panel de insights</div>', unsafe_allow_html=True)
    # ej. gráfico de ejemplo
    rng = np.random.default_rng(22)
    demo = pd.DataFrame({
        "fecha": pd.date_range(date.today()-timedelta(days=90), periods=91, freq="D"),
        "valor": np.cumsum(rng.normal(0, 1, 91)) + 100
    })
    fig = px.line(demo, x="fecha", y="valor", markers=True, color_discrete_sequence=[ACCENT])
    fig.update_traces(line=dict(width=3))
    fig.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        """
<div class="card">
<p><strong>Explicación del agente:</strong> La serie muestra una tendencia levemente alcista con variaciones esperadas.
Se sugiere revisar ventanas móviles de 7 y 14 días para anticipar cambios de ritmo y ajustar la operación.</p>
</div>
""", unsafe_allow_html=True)

# =========================
# WIDGET FLOTANTE DE NOTAS (botón + panel)
# =========================
# Botón flotante
st.markdown('<div class="fab-notes" onclick="window.location.hash = \'#notas\'">🗒️ Notas</div>', unsafe_allow_html=True)

# Ancla para abrir el panel de notas cerca del pie
st.markdown('<a name="notas"></a>', unsafe_allow_html=True)
st.markdown('<hr class="section"/>', unsafe_allow_html=True)
st.markdown('### 🗒️ Notas rápidas')

# CRUD básico de notas
def note_id():
    return int(datetime.now().timestamp()*1000)

cols = st.columns([1.6, 1.6, 1], gap="large")
with cols[0]:
    nt_title = st.text_input("Título de nota", value="")
with cols[1]:
    nt_body = st.text_input("Contenido", value="")
with cols[2]:
    add = st.button("➕ Guardar nota")

if add and nt_title.strip():
    st.session_state.notes.append({
        "id": note_id(), "title": nt_title.strip(), "body": nt_body.strip(),
        "pinned": False, "done": False, "ts": datetime.now().strftime("%d/%m %H:%M")
    })
    st.toast("Nota guardada")

# Mostrar notas (fijadas primero)
if st.session_state.notes:
    # Ordenar: fijadas arriba
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

# =========================
# FOOTER: proceso del agente (píldoras)
# =========================
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
