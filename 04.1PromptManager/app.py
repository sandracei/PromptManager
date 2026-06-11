import streamlit as st
import pandas as pd
from datetime import date
import io

from sheets_helper import (
    load_from_sheets,
    save_to_sheets,
    upload_test_file,
    download_test_file,
)

COLUMNS = ["id", "nombre", "descripcion", "prompt", "version",
           "cambios", "responsable", "fecha", "categoria", "activo", "precision", "test_file"]

# ── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PromptManager · RotF Chatbot Team",
    page_icon="🤖",
    layout="wide",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] { background: #0f172a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    color: #94a3b8 !important; font-size: 0.75rem !important;
    text-transform: uppercase; letter-spacing: 0.05em;
}

.header-strip {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    border-left: 4px solid #6366f1;
}
.header-strip h1 { color: #f8fafc; font-size: 1.6rem; font-weight: 700; margin: 0; }
.header-strip p  { color: #94a3b8; font-size: 0.9rem; margin: 0; }

.prompt-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 1.2rem 1.4rem; margin-bottom: 0.9rem; transition: box-shadow 0.2s;
}
.prompt-card:hover { box-shadow: 0 4px 16px rgba(99,102,241,0.10); border-color: #c7d2fe; }
.card-title  { font-size: 1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.2rem; }
.card-desc   { font-size: 0.85rem; color: #64748b; margin-bottom: 0.7rem; }
.card-meta   { display: flex; gap: 0.6rem; flex-wrap: wrap; align-items: center; }
.badge { font-size: 0.72rem; font-weight: 500; padding: 2px 9px; border-radius: 20px; letter-spacing: 0.02em; }
.badge-version  { background: #ede9fe; color: #6d28d9; }
.badge-category { background: #dbeafe; color: #1d4ed8; }
.badge-person   { background: #dcfce7; color: #166534; }
.badge-date     { background: #f1f5f9; color: #475569; }
.badge-inactive { background: #fee2e2; color: #991b1b; }
.badge-precision-high { background: #dcfce7; color: #166534; }
.badge-precision-mid  { background: #fef9c3; color: #854d0e; }
.badge-precision-low  { background: #fee2e2; color: #991b1b; }
.badge-precision-none { background: #f1f5f9; color: #94a3b8; }

.precision-bar-wrap { display:flex; align-items:center; gap:0.5rem; margin-top:0.5rem; }
.precision-bar-bg { flex:1; background:#e2e8f0; border-radius:999px; height:6px; }
.precision-bar-fill { height:6px; border-radius:999px; transition: width 0.4s; }
.precision-label { font-size:0.75rem; font-weight:600; min-width:36px; text-align:right; }

.prompt-box {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 1rem 1.2rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; color: #334155; white-space: pre-wrap; word-break: break-word;
    margin-top: 0.6rem;
}

.metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.metric-box {
    flex: 1; background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 1rem 1.2rem; text-align: center;
}
.metric-box .num { font-size: 1.8rem; font-weight: 700; color: #6366f1; }
.metric-box .lbl { font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }

.section-title {
    font-size: 0.72rem; font-weight: 600; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem;
}

.hist-row { display: flex; gap: 0.5rem; align-items: flex-start; padding: 0.6rem 0; border-bottom: 1px solid #f1f5f9; }
.hist-ver  { font-weight: 600; color: #6366f1; min-width: 60px; font-size: 0.85rem; }
.hist-meta { font-size: 0.78rem; color: #64748b; }
.hist-changes { font-size: 0.82rem; color: #334155; }

.sp-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;
    padding: 4px 10px; font-size: 0.78rem; color: #1d4ed8; margin-bottom: 1rem;
}

/* Precision + owner highlight block */
.kpi-block {
    display: flex; gap: 1rem; margin-top: 0.8rem; flex-wrap: wrap;
}
.kpi-item {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 0.6rem 1rem; display: flex; flex-direction: column; gap: 0.15rem;
    min-width: 120px;
}
.kpi-item.kpi-high { border-left: 3px solid #22c55e; }
.kpi-item.kpi-mid  { border-left: 3px solid #eab308; }
.kpi-item.kpi-low  { border-left: 3px solid #ef4444; }
.kpi-item.kpi-none { border-left: 3px solid #cbd5e1; }
.kpi-item.kpi-owner { border-left: 3px solid #6366f1; }
.kpi-label { font-size: 0.68rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
.kpi-value { font-size: 1.1rem; font-weight: 700; color: #1e293b; }
.kpi-bar-bg { background: #e2e8f0; border-radius: 999px; height: 4px; margin-top: 4px; }
.kpi-bar-fill { height: 4px; border-radius: 999px; }

#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def next_id(df):
    return int(df["id"].max()) + 1 if not df.empty and df["id"].notna().any() else 1

def precision_badge(val):
    """Return inline badge for precision (used in card meta row)."""
    try:
        p = round(float(val), 1)
    except (TypeError, ValueError):
        return '<span class="badge badge-precision-none">Sin datos</span>'
    if p >= 80:
        cls = "badge-precision-high"
    elif p >= 50:
        cls = "badge-precision-mid"
    else:
        cls = "badge-precision-low"
    return f'<span class="badge {cls}">🎯 {p}%</span>'


def precision_kpi_block(prec_raw, resp):
    """Return a highlighted KPI block showing precision + owner."""
    # Precision block
    try:
        p = round(float(prec_raw), 1)
        if p >= 80:
            kpi_cls, bar_color = "kpi-high", "#22c55e"
        elif p >= 50:
            kpi_cls, bar_color = "kpi-mid",  "#eab308"
        else:
            kpi_cls, bar_color = "kpi-low",  "#ef4444"
        prec_block = (
            f'<div class="kpi-item {kpi_cls}">'
            f'<span class="kpi-label">Precisión</span>'
            f'<span class="kpi-value">{p}%</span>'
            f'<div class="kpi-bar-bg"><div class="kpi-bar-fill" style="width:{min(p,100)}%;background:{bar_color};"></div></div>'
            f'</div>'
        )
    except (TypeError, ValueError):
        prec_block = (
            '<div class="kpi-item kpi-none">'
            '<span class="kpi-label">Precisión</span>'
            '<span class="kpi-value" style="color:#94a3b8;font-size:0.85rem;">Sin datos</span>'
            '</div>'
        )
    # Owner block
    owner_block = ""
    if resp and resp != "nan":
        owner_block = (
            f'<div class="kpi-item kpi-owner">'
            f'<span class="kpi-label">Responsable</span>'
            f'<span class="kpi-value" style="font-size:0.95rem;">{resp}</span>'
            f'</div>'
        )
    return f'<div class="kpi-block">{prec_block}{owner_block}</div>'

def next_version(df, nombre):
    rows = df[df["nombre"] == nombre]
    if rows.empty:
        return "1.0"
    nums = []
    for v in rows["version"].dropna().tolist():
        try:
            nums.append(float(str(v).replace("v", "")))
        except Exception:
            pass
    return "1.0" if not nums else str(round(max(nums) + 0.1, 1))

def parse_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    prompts = []
    if name.endswith(".txt"):
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        prompts.append({"nombre": uploaded_file.name.replace(".txt", ""),
                        "prompt": content, "descripcion": "", "categoria": "", "responsable": ""})
    elif name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip().lower() for c in df.columns]
        for _, row in df.iterrows():
            prompts.append({
                "nombre":      row.get("nombre", row.get("name", "")),
                "prompt":      row.get("prompt", row.get("contenido", row.get("content", ""))),
                "descripcion": row.get("descripcion", row.get("description", "")),
                "categoria":   row.get("categoria", row.get("category", "")),
                "responsable": row.get("responsable", row.get("owner", "")),
            })
    elif name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
        df.columns = [c.strip().lower() for c in df.columns]
        for _, row in df.iterrows():
            prompts.append({
                "nombre":      row.get("nombre", row.get("name", "")),
                "prompt":      row.get("prompt", row.get("contenido", row.get("content", ""))),
                "descripcion": row.get("descripcion", row.get("description", "")),
                "categoria":   row.get("categoria", row.get("category", "")),
                "responsable": row.get("responsable", row.get("owner", "")),
            })
    return prompts


# ── Load data (session_state cache, no st.cache_data to avoid widget conflicts)
def cached_load():
    if "df_prompts" not in st.session_state:
        with st.spinner("Cargando prompts desde Google Sheets…"):
            st.session_state["df_prompts"] = load_from_sheets()
    return st.session_state["df_prompts"]

def reload_data():
    st.session_state.pop("df_prompts", None)
    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 PromptManager")
    st.markdown('<div class="sp-badge">☁️ Google Sheets</div>', unsafe_allow_html=True)
    st.markdown("---")
    pagina = st.radio(
        "Navegación",
        ["🏠  Inicio", "➕  Añadir prompt", "📤  Importar archivo", "📥  Exportar"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if st.button("🔄 Recargar datos", use_container_width=True):
        reload_data()
    st.markdown("---")
    st.markdown('<p style="font-size:0.7rem;color:#475569;">PromptManager v1.0</p>', unsafe_allow_html=True)

df = cached_load()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INICIO
# ══════════════════════════════════════════════════════════════════════════════
if "Inicio" in pagina:
    st.markdown("""
    <div class="header-strip">
      <div>
        <h1>🤖 PromptManager · RotF Chatbot Team</h1>
        <p>Repositorio centralizado de prompts del equipo RotF Chatbot</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    total     = len(df)
    activos   = len(df[df["activo"].astype(str).str.lower() != "false"]) if total else 0
    cats      = df["categoria"].nunique() if total else 0
    personas  = df["responsable"].nunique() if total else 0

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box"><div class="num">{total}</div><div class="lbl">Totales</div></div>
      <div class="metric-box"><div class="num">{activos}</div><div class="lbl">Activos</div></div>
      <div class="metric-box"><div class="num">{cats}</div><div class="lbl">Categorías</div></div>
      <div class="metric-box"><div class="num">{personas}</div><div class="lbl">Responsables</div></div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.info("Aún no hay prompts. ¡Añade el primero desde el menú!")
        st.stop()

    st.markdown('<div class="section-title">Filtros</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        busqueda = st.text_input("🔍 Buscar", placeholder="Nombre, descripción o contenido…")
    with col2:
        cat_opts = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
        cat_sel  = st.selectbox("Categoría", cat_opts)
    with col3:
        per_opts  = ["Todas"] + sorted(df["responsable"].dropna().unique().tolist())
        per_sel   = st.selectbox("Responsable", per_opts)

    latest = (df.sort_values("version").groupby("nombre", as_index=False).last())
    filtered = latest.copy()
    if busqueda:
        mask = (filtered["nombre"].str.contains(busqueda, case=False, na=False) |
                filtered["descripcion"].str.contains(busqueda, case=False, na=False) |
                filtered["prompt"].str.contains(busqueda, case=False, na=False))
        filtered = filtered[mask]
    if cat_sel != "Todas":
        filtered = filtered[filtered["categoria"] == cat_sel]
    if per_sel != "Todas":
        filtered = filtered[filtered["responsable"] == per_sel]

    st.markdown(f'<div class="section-title">{len(filtered)} prompts encontrados</div>', unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No hay prompts que coincidan con los filtros.")
    else:
        for _, row in filtered.iterrows():
            nombre    = str(row.get("nombre", ""))
            desc      = str(row.get("descripcion", ""))
            ver       = str(row.get("version", ""))
            cat       = str(row.get("categoria", ""))
            resp      = str(row.get("responsable", ""))
            fecha     = str(row.get("fecha", ""))
            activo    = str(row.get("activo", "true")).lower() != "false"
            cambios   = str(row.get("cambios", ""))
            prec_raw  = row.get("precision", "")
            test_file = str(row.get("test_file", ""))

            inactive_badge = '' if activo else '<span class="badge badge-inactive">Inactivo</span>'
            cat_badge  = f'<span class="badge badge-category">{cat}</span>' if cat and cat != "nan" else ""
            date_badge = f'<span class="badge badge-date">📅 {fecha}</span>' if fecha and fecha != "nan" else ""
            prec_html  = precision_badge(prec_raw)
            test_badge = '<span class="badge badge-date">🧪 Dataset adjunto</span>' if test_file and test_file != "nan" else ""

            st.markdown(f"""
            <div class="prompt-card">
              <div class="card-title">{nombre} {inactive_badge}</div>
              <div class="card-desc">{desc if desc != "nan" else ""}</div>
              <div class="card-meta">
                <span class="badge badge-version">v{ver}</span>
                {cat_badge}{date_badge}{prec_html}{test_badge}
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Ver · {nombre}"):
                # KPI block — precision + owner highlighted
                st.markdown(precision_kpi_block(prec_raw, resp), unsafe_allow_html=True)

                prompt_text = str(row.get("prompt", ""))
                st.markdown(f'<div class="prompt-box">{prompt_text}</div>', unsafe_allow_html=True)

                # Download test file if exists
                if test_file and test_file != "nan":
                    st.markdown("---")
                    st.markdown('<div class="section-title">Dataset de prueba</div>', unsafe_allow_html=True)
                    col_t1, col_t2 = st.columns([3, 1])
                    with col_t1:
                        st.markdown(f"📎 `{test_file}`")
                    with col_t2:
                        if st.button("⬇️ Descargar", key=f"dl_test_{row['id']}"):
                            try:
                                file_bytes = download_test_file(test_file)
                                st.download_button(
                                    "Guardar archivo",
                                    file_bytes,
                                    file_name=test_file,
                                    key=f"save_test_{row['id']}",
                                )
                            except Exception as e:
                                st.error(f"No se pudo descargar el archivo: {e}")

                # History
                historial = df[df["nombre"] == nombre].sort_values("version", ascending=False)
                if len(historial) > 1:
                    st.markdown("---")
                    st.markdown('<div class="section-title">Historial de versiones</div>', unsafe_allow_html=True)
                    for _, hrow in historial.iterrows():
                        hcambios   = str(hrow.get("cambios", ""))
                        hresp      = str(hrow.get("responsable", ""))
                        hfecha     = str(hrow.get("fecha", ""))
                        hprec      = hrow.get("precision", "")
                        htest      = str(hrow.get("test_file", ""))
                        meta       = " · ".join(x for x in [hresp, hfecha] if x and x != "nan")
                        prec_str   = f" · 🎯 {round(float(hprec), 1)}%" if hprec and str(hprec) not in ("", "nan") else ""
                        test_str   = f" · 🧪 `{htest}`" if htest and htest != "nan" else ""
                        st.markdown(f"""
                        <div class="hist-row">
                          <div class="hist-ver">v{hrow['version']}</div>
                          <div>
                            <div class="hist-meta">{meta}{prec_str}{test_str}</div>
                            <div class="hist-changes">{hcambios if hcambios != "nan" else "—"}</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✏️ Editar / nueva versión", key=f"edit_{row['id']}"):
                        st.session_state["editar_nombre"] = nombre
                        st.session_state["editar_prompt"] = prompt_text
                        st.session_state["editar_desc"]   = desc if desc != "nan" else ""
                        st.session_state["editar_cat"]    = cat  if cat  != "nan" else ""
                        st.session_state["editar_resp"]   = resp if resp != "nan" else ""
                        st.rerun()
                with col_b:
                    label = "🔴 Desactivar" if activo else "🟢 Activar"
                    if st.button(label, key=f"toggle_{row['id']}"):
                        df.loc[df["nombre"] == nombre, "activo"] = not activo
                        save_to_sheets(df)
                        reload_data()

    if "editar_nombre" in st.session_state:
        st.info(f"Ve a **➕ Añadir prompt** para editar «{st.session_state['editar_nombre']}».")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AÑADIR PROMPT
# ══════════════════════════════════════════════════════════════════════════════
elif "Añadir" in pagina:
    st.markdown("""
    <div class="header-strip">
      <div><h1>➕ Añadir prompt</h1>
      <p>Crea un nuevo prompt o añade una nueva versión de uno existente</p></div>
    </div>
    """, unsafe_allow_html=True)

    prefill_nombre = st.session_state.pop("editar_nombre", "")
    prefill_prompt = st.session_state.pop("editar_prompt", "")
    prefill_desc   = st.session_state.pop("editar_desc",   "")
    prefill_cat    = st.session_state.pop("editar_cat",    "")
    prefill_resp   = st.session_state.pop("editar_resp",   "")

    col1, col2 = st.columns([2, 1])
    with col1:
        nombre      = st.text_input("Nombre del prompt *", value=prefill_nombre, placeholder="ej. User Query Classification and Fallback")
        descripcion = st.text_area("Descripción", value=prefill_desc, placeholder="ej. Clasifica el input del usuario como RAG, TICKET o fallback según si está relacionado con OTR.", height=80)
        prompt_text = st.text_area("Texto del prompt *", value=prefill_prompt, placeholder="ej. You are a helpful assistant for a chatbot that supports users of the One Touch Retail (OTR) sales system. Your task is to analyze the user's input and respond only with what is strictly necessary…", height=200)
        cambios     = st.text_area("¿Qué se ha cambiado?", placeholder="ej. Añadida regla para inputs en alemán / corregido comportamiento con emojis", height=80)
    with col2:
        categoria   = st.text_input("Categoría", value=prefill_cat, placeholder="ej. UC02_GPTFallback, UC07_RAGSearch…")
        responsable = st.text_input("Responsable *", value=prefill_resp, placeholder="ej. Sandra, Adri. Gaz…")
        fecha       = st.date_input("Fecha", value=date.today())
        precision   = st.number_input("Precisión (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1, format="%.1f",
                                help="0 = sin datos todavía")
        test_upload = st.file_uploader("📎 Dataset de prueba",
                                       type=["xlsx", "xls", "csv", "pdf", "docx", "txt"],
                                       help="Excel, CSV, PDF o Word con los casos de prueba de esta versión")
        if nombre and nombre in df["nombre"].values:
            nueva_ver = next_version(df, nombre)
            st.info(f"Ya existe. Se guardará como **v{nueva_ver}**.")
        else:
            st.info("Nuevo prompt → se guardará como **v1.0**.")

    if st.button("💾 Guardar", type="primary", use_container_width=True):
        if not nombre or not prompt_text or not responsable:
            st.error("Los campos marcados con * son obligatorios.")
        else:
            version   = next_version(df, nombre)
            test_ref  = ""
            if test_upload is not None:
                with st.spinner("Subiendo archivo de test…"):
                    # Build a unique name: test_<nombre>_v<version>.<ext>
                    ext      = test_upload.name.rsplit(".", 1)[-1]
                    safe_nom = nombre.replace(" ", "_").replace("/", "-")
                    fname    = f"test_{safe_nom}_v{version}.{ext}"
                    test_ref = upload_test_file(test_upload.read(), fname)
            new_row = {
                "id": next_id(df), "nombre": nombre, "descripcion": descripcion,
                "prompt": prompt_text, "version": version, "cambios": cambios,
                "responsable": responsable, "fecha": str(fecha),
                "categoria": categoria, "activo": True,
                "precision": precision if precision > 0 else "",
                "test_file": test_ref,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            with st.spinner("Guardando…"):
                save_to_sheets(df)
            reload_data()
            st.success(f"✅ «{nombre}» guardado como v{version} en Google Sheets.")
            st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IMPORTAR
# ══════════════════════════════════════════════════════════════════════════════
elif "Importar" in pagina:
    st.markdown("""
    <div class="header-strip">
      <div><h1>📤 Importar archivo</h1>
      <p>Carga prompts desde un fichero .txt, .csv o .xlsx</p></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    **Formatos admitidos:**
    - **`.txt`** → el contenido se convierte en un prompt
    - **`.csv` / `.xlsx`** → columnas: `nombre`, `prompt` (obligatorias); `descripcion`, `categoria`, `responsable` (opcionales)
    """)

    uploaded = st.file_uploader("Selecciona el archivo", type=["txt", "csv", "xlsx"])
    if uploaded:
        try:
            prompts = parse_uploaded_file(uploaded)
            st.success(f"Se han encontrado **{len(prompts)} prompts**.")
            responsable_import = st.text_input("Responsable para todos los prompts importados *", placeholder="Tu nombre")
            fecha_import = st.date_input("Fecha de importación", value=date.today())

            st.markdown("**Vista previa:**")
            for i, p in enumerate(prompts):
                with st.expander(f"{i+1}. {p.get('nombre', 'Sin nombre')}"):
                    txt = p.get("prompt", "")
                    st.write(txt[:500] + ("…" if len(txt) > 500 else ""))

            if st.button("⬆️ Importar todos", type="primary"):
                if not responsable_import:
                    st.error("Indica el responsable antes de importar.")
                else:
                    added = 0
                    for p in prompts:
                        nombre = str(p.get("nombre", "")).strip()
                        prompt_txt = str(p.get("prompt", "")).strip()
                        if not nombre or not prompt_txt:
                            continue
                        version = next_version(df, nombre)
                        new_row = {
                            "id": next_id(df), "nombre": nombre,
                            "descripcion": p.get("descripcion", ""), "prompt": prompt_txt,
                            "version": version, "cambios": "Importado desde archivo",
                            "responsable": p.get("responsable", "") or responsable_import,
                            "fecha": str(fecha_import), "categoria": p.get("categoria", ""), "activo": True,
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        added += 1
                    with st.spinner("Guardando…"):
                        save_to_sheets(df)
                    reload_data()
                    st.success(f"✅ {added} prompts importados y guardados correctamente.")
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EXPORTAR
# ══════════════════════════════════════════════════════════════════════════════
elif "Exportar" in pagina:
    st.markdown("""
    <div class="header-strip">
      <div><h1>📥 Exportar</h1>
      <p>Descarga la biblioteca completa o solo las versiones más recientes</p></div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.info("No hay datos para exportar.")
        st.stop()

    latest_df = (df.sort_values("version").groupby("nombre", as_index=False).last())
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Versiones más recientes")
        st.write(f"{len(latest_df)} prompts")
        st.download_button("⬇️ CSV", latest_df.to_csv(index=False).encode("utf-8"),
                           "prompts_recientes.csv", "text/csv", use_container_width=True)
        buf = io.BytesIO()
        latest_df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button("⬇️ Excel", buf.getvalue(), "prompts_recientes.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    with col2:
        st.markdown("### Historial completo")
        st.write(f"{len(df)} entradas (todas las versiones)")
        st.download_button("⬇️ CSV", df.to_csv(index=False).encode("utf-8"),
                           "prompts_historial.csv", "text/csv", use_container_width=True)
        buf2 = io.BytesIO()
        df.to_excel(buf2, index=False, engine="openpyxl")
        st.download_button("⬇️ Excel", buf2.getvalue(), "prompts_historial.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    st.markdown("---")
    st.dataframe(latest_df[["nombre", "version", "precision", "test_file", "categoria", "responsable", "fecha", "descripcion"]],
                 use_container_width=True, hide_index=True)
