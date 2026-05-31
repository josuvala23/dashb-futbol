import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Football Scout Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #e6edf3; }
    .stApp { background-color: #0d1117 !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    h1, h2, h3 { color: #e6edf3 !important; }
    hr { border-color: #21262d !important; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 2px; }
    div[data-testid="stButton"] button {
        background: #090d13 !important; color: #c9d1d9 !important;
        border: 0.5px solid #30363d !important; border-radius: 6px !important;
        font-size: 14px !important; font-weight: 500 !important; padding: 10px 16px !important;
    }
    div[data-testid="stButton"] button:hover {
        background: #1c2a3a !important; color: #58a6ff !important; border-color: #1f6feb !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================
# RUTAS
# =============================================
DATA_PATH = "data/players_2024_2025_clean (2).csv"
AUX_PATH  = "data/players_auxiliary_clean.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

@st.cache_data
def load_aux():
    try:
        return pd.read_csv(AUX_PATH)
    except:
        return pd.DataFrame(columns=["Player", "foto_url", "valor_mercado_fmt"])

df  = load_data()
aux = load_aux()

# =============================================
# CONFIG POR POSICION
# =============================================
POS_CONFIG = {
    "FW": {
        "label": "Delanteros",
        "score_col": "score_FW",
        "radar_cols": {
            "Remate":     "radar_FW_Remate",
            "Gol":        "radar_FW_Gol",
            "Precision":  "radar_FW_Precision",
            "Creacion":   "radar_FW_Creacion",
            "Movimiento": "radar_FW_Movimiento",
            "Conduccion": "radar_FW_Conduccion",
        },
        "table_cols": {
            "xG/90":  "xG_p90",
            "Gls/90": "Gls_p90",
            "xA/90":  "xA_p90",
            "SoT/90": "SoT_p90",
        }
    },
    "MF": {
        "label": "Mediocampistas",
        "score_col": "score_MF",
        "radar_cols": {
            "Creacion":   "radar_MF_Creacion",
            "Progresion": "radar_MF_Progresion",
            "Defensa":    "radar_MF_Defensa",
            "Asistencia": "radar_MF_Asistencia",
            "Conduccion": "radar_MF_Conduccion",
            "Pase":       "radar_MF_Pase",
        },
        "table_cols": {
            "KP/90":    "KP_p90",
            "PrgP/90":  "PrgP_p90",
            "Tkl+I/90": "Tkl+Int_p90",
            "Cmp%":     "Cmp%",
        }
    },
    "DF": {
        "label": "Defensas",
        "score_col": "score_DF",
        "radar_cols": {
            "Defensa":    "radar_DF_Defensa",
            "Pase":       "radar_DF_Pase",
            "Despeje":    "radar_DF_Despeje",
            "Aereo":      "radar_DF_Aereo",
            "Progresion": "radar_DF_Progresion",
            "Errores":    "radar_DF_Errores",
        },
        "table_cols": {
            "Tkl+I/90": "Tkl+Int_p90",
            "Clr/90":   "Clr_p90",
            "Won%":     "Won%",
            "Cmp%":     "Cmp%",
        }
    },
    "GK": {
        "label": "Porteros",
        "score_col": "score_GK",
        "radar_cols": {
            "Calidad":  "radar_GK_Calidad",
            "Paradas":  "radar_GK_Paradas",
            "GolesEnc": "radar_GK_GolesEnc",
            "PaCero":   "radar_GK_PorteriaACero",
            "Pase":     "radar_GK_Pase",
        },
        "table_cols": {
            "Save%":   "Save%",
            "GA90":    "GA90",
            "CS%":     "CS%",
            "PSxG+/-": "PSxG+/-",
        }
    }
}

# =============================================
# SESSION STATE
# =============================================
for key, val in [("posicion", None), ("jugador_idx", 0), ("pantalla", "campo")]:
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================
# HELPERS
# =============================================
def get_flag_html(nation, size=20):
    try:
        parts  = str(nation).split(" ")
        codigo = parts[0].lower()
        nombre = parts[1] if len(parts) > 1 else nation
        h = int(size * 0.75)
        return (
            f"<img src='https://flagcdn.com/{size}x{h}/{codigo}.png' "
            f"style='vertical-align:middle; margin-right:5px; border-radius:2px;'>"
            f"<span style='color:#8b949e; font-size:12px;'>{nombre}</span>"
        )
    except:
        return f"<span style='color:#8b949e; font-size:12px;'>{nation}</span>"

def get_aux_data(nombre):
    if not aux.empty and "Player" in aux.columns:
        match = aux[aux["Player"] == nombre]
        if not match.empty:
            row = match.iloc[0]
            return str(row.get("foto_url", "")), str(row.get("valor_mercado_fmt", ""))
    return "", ""

def render_radar(player_data, radar_cols, color):
    labels = list(radar_cols.keys())
    values = [
        round(float(player_data[col]), 3) if pd.notna(player_data[col]) else 0
        for col in radar_cols.values()
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor=f"rgba({color},0.2)",
        line=dict(color=f"rgb({color})", width=2),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#090d13",
            radialaxis=dict(visible=True, range=[0,1], tickfont=dict(color="#6e7681", size=9), gridcolor="#21262d", linecolor="#21262d"),
            angularaxis=dict(tickfont=dict(color="#c9d1d9", size=11), gridcolor="#21262d", linecolor="#21262d")
        ),
        paper_bgcolor="#0d1117",
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30),
        height=280,
    )
    return fig

def mini_perfil_html(player_data, score_col):
    nombre   = player_data["Player"]
    foto_url, valor = get_aux_data(nombre)

    foto_html = (
        f"<img src='{foto_url}' style='width:72px; height:72px; object-fit:cover; border-radius:6px; flex-shrink:0;'>"
        if foto_url.startswith("http") else
        "<div style='width:72px; height:72px; background:#1c2a3a; border-radius:6px; flex-shrink:0;'></div>"
    )

    valor_kpi = (
        f"<div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:7px 10px;'>"
        f"<div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Valor</div>"
        f"<div style='color:#e6edf3; font-size:17px; font-weight:500;'>{valor}</div></div>"
        if valor and valor not in ("nan", "None", "") else
        f"<div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:7px 10px;'>"
        f"<div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Pais</div>"
        f"<div style='color:#e6edf3; font-size:14px; font-weight:500;'>{str(player_data['Nation']).split(' ')[-1]}</div></div>"
    )

    return f"""
    <div style='background:#090d13; border:0.5px solid #21262d; border-radius:8px; padding:12px 16px; margin-top:10px;'>
      <div style='font-size:14px; font-weight:500; color:#e6edf3; margin-bottom:8px;'>{nombre}</div>
      <div style='display:flex; align-items:center; gap:14px;'>
        {foto_html}
        <div style='display:flex; flex-direction:column; gap:4px; min-width:130px;'>
          <div style='font-size:12px; color:#8b949e;'>{player_data['Squad']} · {player_data['Comp']}</div>
          <div style='display:flex; align-items:center; gap:5px;'>{get_flag_html(player_data['Nation'])}</div>
        </div>
        <div style='display:grid; grid-template-columns:1fr 1fr; gap:6px; flex:1;'>
          <div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:7px 10px;'>
            <div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Edad</div>
            <div style='color:#e6edf3; font-size:17px; font-weight:500;'>{int(player_data['Age'])}</div>
          </div>
          <div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:7px 10px;'>
            <div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Minutos</div>
            <div style='color:#e6edf3; font-size:17px; font-weight:500;'>{int(player_data['Min']):,}</div>
          </div>
          <div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:7px 10px;'>
            <div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Score</div>
            <div style='color:#e6edf3; font-size:17px; font-weight:500;'>{round(float(player_data[score_col]),3)}</div>
          </div>
          {valor_kpi}
        </div>
      </div>
    </div>
    """

# =============================================
# CAMPO SVG
# =============================================
CAMPO_SVG = """
<svg viewBox="0 0 260 560" xmlns="http://www.w3.org/2000/svg" style="width:100%; max-width:220px;">
  <rect width="260" height="560" rx="10" fill="#1a6b2e"/>
  <rect x="0" y="0"   width="260" height="56" fill="#1e7533"/>
  <rect x="0" y="112" width="260" height="56" fill="#1e7533"/>
  <rect x="0" y="224" width="260" height="56" fill="#1e7533"/>
  <rect x="0" y="336" width="260" height="56" fill="#1e7533"/>
  <rect x="0" y="448" width="260" height="56" fill="#1e7533"/>
  <rect x="10" y="10" width="240" height="540" rx="4" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" fill="none"/>
  <line x1="10" y1="280" x2="250" y2="280" stroke="rgba(255,255,255,0.35)" stroke-width="1.5"/>
  <circle cx="130" cy="280" r="45" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" fill="none"/>
  <circle cx="130" cy="280" r="3" fill="rgba(255,255,255,0.4)"/>
  <rect x="65" y="10"  width="130" height="65" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" fill="none"/>
  <rect x="95" y="10"  width="70"  height="28" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" fill="none"/>
  <circle cx="130" cy="58" r="3" fill="rgba(255,255,255,0.4)"/>
  <rect x="65" y="485" width="130" height="65" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" fill="none"/>
  <rect x="95" y="522" width="70"  height="28" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" fill="none"/>
  <circle cx="130" cy="502" r="3" fill="rgba(255,255,255,0.4)"/>
  <circle cx="55"  cy="95"  r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="55"  y="95"  text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">7</text>
  <circle cx="130" cy="82" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="130" y="82"  text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">9</text>
  <circle cx="205" cy="95" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="205" y="95"  text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">11</text>
  <circle cx="55"  cy="200" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="55"  y="200" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">8</text>
  <circle cx="130" cy="210" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="130" y="210" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">6</text>
  <circle cx="205" cy="200" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="205" y="200" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">10</text>
  <circle cx="28"  cy="355" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="28"  y="355" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">2</text>
  <circle cx="95"  cy="345" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="95"  y="345" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">4</text>
  <circle cx="165" cy="345" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="165" y="345" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">5</text>
  <circle cx="232" cy="355" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="232" y="355" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">3</text>
  <circle cx="130" cy="468" r="22" fill="rgba(30,80,180,0.85)" stroke="#fff" stroke-width="2"/>
  <text x="130" y="468" text-anchor="middle" dominant-baseline="central" font-size="13" fill="#fff" font-weight="500">1</text>
  <text x="130" y="7"   text-anchor="middle" font-size="9" fill="rgba(255,255,255,0.4)">Ataque</text>
  <text x="130" y="555" text-anchor="middle" font-size="9" fill="rgba(255,255,255,0.4)">Defensa</text>
</svg>
"""

# =============================================
# PANTALLA: CAMPO
# =============================================
def render_campo():
    st.markdown(
        "<h2 style='color:#e6edf3; font-size:20px; font-weight:500; margin-bottom:4px;'>Scout Dashboard 2024 / 2025</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#6e7681; font-size:13px; margin-bottom:16px;'>Selecciona una posicion para ver el Top 10</p>",
        unsafe_allow_html=True
    )
    col_campo, col_botones = st.columns([0.8, 1.2])
    with col_campo:
        st.markdown(CAMPO_SVG, unsafe_allow_html=True)
    with col_botones:
        st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
        if st.button("Delanteros", use_container_width=True, key="btn_fw"):
            st.session_state.posicion = "FW"
            st.session_state.jugador_idx = 0
            st.session_state.pantalla = "dashboard"
            st.rerun()
        st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
        if st.button("Mediocampistas", use_container_width=True, key="btn_mf"):
            st.session_state.posicion = "MF"
            st.session_state.jugador_idx = 0
            st.session_state.pantalla = "dashboard"
            st.rerun()
        st.markdown("<div style='height:56px;'></div>", unsafe_allow_html=True)
        if st.button("Defensas", use_container_width=True, key="btn_df"):
            st.session_state.posicion = "DF"
            st.session_state.jugador_idx = 0
            st.session_state.pantalla = "dashboard"
            st.rerun()
        st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
        if st.button("Porteros", use_container_width=True, key="btn_gk"):
            st.session_state.posicion = "GK"
            st.session_state.jugador_idx = 0
            st.session_state.pantalla = "dashboard"
            st.rerun()

# =============================================
# PANTALLA: DASHBOARD TOP 10
# =============================================
def render_dashboard(pos_code):
    config     = POS_CONFIG[pos_code]
    score_col  = config["score_col"]
    radar_cols = config["radar_cols"]
    table_cols = config["table_cols"]
    label      = config["label"]

    df_pos   = df[df["Pos_Primary"] == pos_code].dropna(subset=[score_col])
    df_top10 = df_pos.nlargest(10, score_col).reset_index(drop=True)

    c1, c2, c3 = st.columns([1, 1, 6])
    with c1:
        if st.button("← Campo"):
            st.session_state.pantalla = "campo"
            st.session_state.posicion = None
            st.rerun()
    with c2:
        if st.button("Comparar"):
            st.session_state.pantalla = "comparar"
            st.rerun()

    st.markdown(
        f"<h3 style='color:#e6edf3; font-size:18px; font-weight:500; margin-bottom:4px;'>Top 10 — {label}</h3>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border-color:#21262d; margin:8px 0 16px;'>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 1.8])

    with col_left:
        display_df = pd.DataFrame()
        display_df["#"]       = range(1, len(df_top10) + 1)
        display_df["Jugador"] = df_top10["Player"].values
        display_df["Equipo"]  = df_top10["Squad"].values
        display_df["Score"]   = df_top10[score_col].round(3).values
        for lbl, col in table_cols.items():
            if col in df_top10.columns:
                display_df[lbl] = df_top10[col].round(2).values
        display_df["Min"] = df_top10["Min"].astype(int).values

        sel = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=380,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "#": st.column_config.NumberColumn(width="small"),
                "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1, format="%.3f"),
            }
        )

        filas = sel.selection.rows if sel.selection.rows else []
        if filas:
            st.session_state.jugador_idx = filas[0]

        idx         = st.session_state.jugador_idx
        jugador_sel = df_top10.iloc[idx]["Player"]

        st.markdown(
            f"<p style='color:#6e7681; font-size:12px; margin-top:6px;'>"
            f"Seleccionado: <span style='color:#58a6ff;'>{jugador_sel}</span>"
            f" — haz clic en una fila para cambiar</p>",
            unsafe_allow_html=True
        )

        st.markdown(mini_perfil_html(df_top10.iloc[idx], score_col), unsafe_allow_html=True)

    with col_right:
        st.plotly_chart(
            render_radar(df_top10.iloc[idx], radar_cols, "31,111,235"),
            use_container_width=True
        )
        st.markdown(
            "<p style='color:#6e7681; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;'>Stats clave</p>",
            unsafe_allow_html=True
        )
        for lbl, col in table_cols.items():
            pdata = df_top10.iloc[idx]
            if col in pdata.index and pd.notna(pdata[col]):
                val = round(float(pdata[col]), 2)
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; font-size:13px; padding:5px 0; border-bottom:0.5px solid #21262d;'>"
                    f"<span style='color:#8b949e;'>{lbl}</span>"
                    f"<span style='color:#e6edf3; font-weight:500;'>{val}</span></div>",
                    unsafe_allow_html=True
                )

# =============================================
# PANTALLA: COMPARAR
# =============================================
def render_comparar(pos_code):
    config     = POS_CONFIG[pos_code]
    score_col  = config["score_col"]
    radar_cols = config["radar_cols"]
    table_cols = config["table_cols"]
    label      = config["label"]

    df_pos   = df[df["Pos_Primary"] == pos_code].dropna(subset=[score_col])
    df_top15 = df_pos.nlargest(15, score_col).reset_index(drop=True)
    nombres  = df_top15["Player"].tolist()

    if st.button("← Volver al Top 10"):
        st.session_state.pantalla = "dashboard"
        st.rerun()

    st.markdown(
        f"<h3 style='color:#e6edf3; font-size:18px; font-weight:500; margin-bottom:4px;'>Comparar — {label}</h3>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border-color:#21262d; margin:8px 0 16px;'>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        jugador1 = st.selectbox("Jugador 1", nombres, index=0, key="cmp_j1")
    with c2:
        opciones2 = [n for n in nombres if n != jugador1]
        jugador2  = st.selectbox("Jugador 2", opciones2, index=0, key="cmp_j2")

    st.markdown("<hr style='border-color:#21262d; margin:12px 0;'>", unsafe_allow_html=True)

    data1 = df_top15[df_top15["Player"] == jugador1].iloc[0]
    data2 = df_top15[df_top15["Player"] == jugador2].iloc[0]

    col1, col2 = st.columns(2)

    for col, data, color_border, color_radar in [
        (col1, data1, "#1f6feb", "31,111,235"),
        (col2, data2, "#16a34a", "34,197,94"),
    ]:
        nombre   = data["Player"]
        foto_url, valor = get_aux_data(nombre)
        foto_html = (
            f"<img src='{foto_url}' style='width:72px; height:72px; object-fit:cover; border-radius:8px; flex-shrink:0;'>"
            if foto_url.startswith("http") else
            f"<div style='width:72px; height:72px; background:#1c2a3a; border-radius:8px; flex-shrink:0;'></div>"
        )
        valor_kpi = (
            f"<div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:8px 10px;'>"
            f"<div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Valor</div>"
            f"<div style='color:#e6edf3; font-size:16px; font-weight:500;'>{valor}</div></div>"
            if valor and valor not in ("nan", "None", "") else
            f"<div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:8px 10px;'>"
            f"<div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Pais</div>"
            f"<div style='color:#e6edf3; font-size:14px; font-weight:500;'>{str(data['Nation']).split(' ')[-1]}</div></div>"
        )

        with col:
            st.markdown(
                f"<div style='background:#090d13; border:0.5px solid {color_border}; border-radius:10px; padding:16px;'>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='display:flex; gap:12px; align-items:center; margin-bottom:12px;'>"
                f"{foto_html}"
                f"<div style='display:grid; grid-template-columns:1fr 1fr; gap:6px; flex:1;'>"
                f"<div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:8px 10px;'>"
                f"<div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Edad</div>"
                f"<div style='color:#e6edf3; font-size:16px; font-weight:500;'>{int(data['Age'])}</div></div>"
                f"<div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:8px 10px;'>"
                f"<div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Minutos</div>"
                f"<div style='color:#e6edf3; font-size:16px; font-weight:500;'>{int(data['Min']):,}</div></div>"
                f"<div style='background:#0d1117; border:0.5px solid #21262d; border-radius:6px; padding:8px 10px;'>"
                f"<div style='color:#6e7681; font-size:10px; text-transform:uppercase; letter-spacing:0.5px;'>Score</div>"
                f"<div style='color:#e6edf3; font-size:16px; font-weight:500;'>{round(float(data[score_col]),3)}</div></div>"
                f"{valor_kpi}"
                f"</div></div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='color:#e6edf3; font-size:15px; font-weight:500; margin-bottom:2px;'>{nombre}</div>"
                f"<div style='color:#8b949e; font-size:12px; margin-bottom:6px;'>{data['Squad']} · {data['Comp']}</div>"
                f"{get_flag_html(data['Nation'])}",
                unsafe_allow_html=True
            )
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            st.plotly_chart(render_radar(data, radar_cols, color_radar), use_container_width=True)
            st.markdown(
                "<p style='color:#6e7681; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;'>Stats clave</p>",
                unsafe_allow_html=True
            )
            for lbl, col_stat in table_cols.items():
                if col_stat in data.index and pd.notna(data[col_stat]):
                    val = round(float(data[col_stat]), 2)
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; font-size:13px; padding:5px 0; border-bottom:0.5px solid #21262d;'>"
                        f"<span style='color:#8b949e;'>{lbl}</span>"
                        f"<span style='color:#e6edf3; font-weight:500;'>{val}</span></div>",
                        unsafe_allow_html=True
                    )
            st.markdown("</div>", unsafe_allow_html=True)

# =============================================
# ROUTER
# =============================================
pantalla = st.session_state.pantalla
pos      = st.session_state.posicion

if pantalla == "campo" or pos is None:
    render_campo()
elif pantalla == "comparar":
    render_comparar(pos)
else:
    render_dashboard(pos)