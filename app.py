import json
from pathlib import Path

import streamlit as st

from engine import KBError, MotorInferencia, cargar_hechos, cargar_kb

BASE = Path(__file__).parent

DOMINIOS = {
    "ciberseguridad": {
        "emoji": "🛡️", "nombre": "CiberShield", "titulo": "Ciberseguridad",
        "desc": "Marca las alertas que estás viendo. El sistema deduce qué ataque puede estar ocurriendo y qué debes hacer.",
        "c1": "#ff2e63", "c2": "#ff9a3c",
        "kb": "knowledge_base/ciberseguridad.json", "ej": "examples/caso_ciberseguridad.json",
    },
    "nube": {
        "emoji": "☁️", "nombre": "CloudCraft", "titulo": "Arquitectura en la nube",
        "desc": "Elige los requisitos de tu sistema (latencia, costos, datos...) y recibe la arquitectura recomendada.",
        "c1": "#00c6ff", "c2": "#7b2ff7",
        "kb": "knowledge_base/nube.json", "ej": "examples/caso_nube.json",
    },
    "modelos_ia": {
        "emoji": "🤖", "nombre": "NeuroPick", "titulo": "Modelos de IA",
        "desc": "Cuéntanos qué necesita tu empresa y qué restricciones tienes. Te decimos qué modelo de IA desplegar.",
        "c1": "#00f5a0", "c2": "#00b4d8",
        "kb": "knowledge_base/modelos_ia.json", "ej": "examples/caso_modelos_ia.json",
    },
}

st.set_page_config(page_title="NEXUS Expert", page_icon="🧠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&family=Space+Grotesk:wght@500;700&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; }
.hero { text-align:center; padding:2.2rem 1rem; border-radius:28px; margin-bottom:1.5rem;
  background: linear-gradient(120deg,#ff2e63,#7b2ff7,#00c6ff,#00f5a0); background-size:300% 300%;
  animation: flow 10s ease infinite; box-shadow:0 10px 40px rgba(123,47,247,.45); }
@keyframes flow { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
.hero .logo { font-size:3.5rem; }
.hero h1 { font-size:3.2rem; margin:.2rem 0; color:#fff; letter-spacing:2px; }
.hero h1 span { color:#0f0c29; }
.hero p { color:#fff; font-size:1.1rem; opacity:.95; }
.card { --c1:#fff; --c2:#fff; padding:1.6rem 1.2rem; border-radius:24px; min-height:260px; text-align:center;
  background: linear-gradient(160deg, var(--c1), var(--c2)); color:#fff; margin-bottom:.6rem;
  box-shadow:0 8px 28px rgba(0,0,0,.4); transition: transform .25s; }
.card:hover { transform: translateY(-8px) scale(1.02); }
.card .emoji { font-size:4rem; }
.card h3 { color:#fff; margin:.3rem 0; }
.card p { font-size:.95rem; }
.banner { padding:1.2rem 1.6rem; border-radius:22px; color:#fff; margin-bottom:1rem;
  background: linear-gradient(120deg, var(--c1), var(--c2)); box-shadow:0 8px 28px rgba(0,0,0,.35); }
.banner h2 { color:#fff; margin:0; }
.grupo { font-family:'Space Grotesk'; font-size:1.1rem; font-weight:700; margin:1rem 0 .2rem;
  padding-left:.6rem; border-left:5px solid var(--c1); }
.rec { padding:1.3rem 1.5rem; border-radius:20px; margin:.7rem 0; color:#fff;
  background: linear-gradient(120deg, var(--c1), var(--c2)); box-shadow:0 8px 28px rgba(0,0,0,.35); }
.rec.alt { background:#1b1740; border:2px solid var(--c1); }
.rec h3 { color:#fff; margin:0 0 .3rem; }
.badge { display:inline-block; padding:.15rem .7rem; border-radius:999px; background:rgba(255,255,255,.25);
  font-size:.8rem; font-weight:600; margin-bottom:.4rem; }
.stButton>button { border-radius:14px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ---------------- navegación ----------------
def ir(k):
    st.session_state.dominio = k
    st.session_state.pop("resultado", None)


def inicio():
    st.markdown("""<div class="hero"><div class="logo">🧠⚡</div>
    <h1>NEXUS<span>Expert</span></h1>
    <p>Sistema experto con motor de inferencia por encadenamiento hacia adelante.<br>
    Elige en qué quieres que te asesore 👇</p></div>""", unsafe_allow_html=True)
    cols = st.columns(3)
    for col, (k, d) in zip(cols, DOMINIOS.items()):
        with col:
            st.markdown(f"""<div class="card" style="--c1:{d['c1']};--c2:{d['c2']}">
            <div class="emoji">{d['emoji']}</div><h3>{d['titulo']}</h3>
            <b>{d['nombre']}</b><p>{d['desc']}</p></div>""", unsafe_allow_html=True)
            st.button(f"Entrar a {d['nombre']} →", key=f"ir_{k}", on_click=ir, args=(k,),
                      use_container_width=True)


def pantalla_dominio(k):
    d = DOMINIOS[k]
    estilo = f"--c1:{d['c1']};--c2:{d['c2']}"

    # ---- barra lateral ----
    st.sidebar.markdown("## 🧠 NEXUS Expert")
    st.sidebar.button("⬅️ Volver al inicio", on_click=lambda: st.session_state.pop("dominio", None))
    kb_subida = st.sidebar.file_uploader("📂 Cargar otra base de conocimiento (.json)", type="json")
    try:
        kb = cargar_kb(kb_subida) if kb_subida else cargar_kb(BASE / d["kb"])
    except (KBError, json.JSONDecodeError, FileNotFoundError) as e:
        st.error(f"No se pudo cargar la base de conocimiento: {e}")
        return
    motor = MotorInferencia(kb)
    st.sidebar.success(f"Base cargada: {len(kb['reglas'])} reglas · {len(kb['hechos'])} hechos")

    st.markdown(f"""<div class="banner" style="{estilo}"><h2>{d['emoji']} {d['nombre']} · {d['titulo']}</h2>
    <div>{kb.get('descripcion', d['desc'])}</div></div>""", unsafe_allow_html=True)

    entradas = {h: v for h, v in kb["hechos"].items() if v.get("tipo", "entrada") == "entrada"}

    # ---- carga de hechos desde archivo (antes de crear los checkboxes) ----
    st.subheader("1️⃣ Ingresa los hechos iniciales")
    c1, c2, c3 = st.columns([1, 1, 1])
    hechos_up = c1.file_uploader("Cargar hechos desde archivo (.json)", type="json")
    if hechos_up and c1.button("Aplicar archivo"):
        ids = cargar_hechos(hechos_up)
        for h in entradas:
            st.session_state[f"{k}_{h}"] = h in ids
    if c2.button("📋 Cargar caso de ejemplo"):
        ids = cargar_hechos(BASE / d["ej"])
        for h in entradas:
            st.session_state[f"{k}_{h}"] = h in ids
    if c3.button("🧹 Limpiar selección"):
        for h in entradas:
            st.session_state[f"{k}_{h}"] = False

    # ---- ingreso interactivo ----
    grupos = {}
    for h, v in entradas.items():
        grupos.setdefault(v.get("grupo", "General"), []).append(h)
    for g, hs in grupos.items():
        st.markdown(f"<div class='grupo' style='{estilo}'>{g}</div>", unsafe_allow_html=True)
        cols = st.columns(2)
        for j, h in enumerate(hs):
            cols[j % 2].checkbox(entradas[h]["texto"], key=f"{k}_{h}")
    seleccion = [h for h in entradas if st.session_state.get(f"{k}_{h}")]

    st.divider()
    if st.button("🚀 Ejecutar motor de inferencia", type="primary", use_container_width=True):
        st.session_state.resultado = motor.ejecutar(seleccion)
        st.session_state.res_dom = k

    res = st.session_state.get("resultado")
    if not res or st.session_state.get("res_dom") != k:
        return

    # ---- resultados ----
    st.subheader("2️⃣ Recomendación del sistema experto")
    m1, m2, m3 = st.columns(3)
    m1.metric("Hechos iniciales", len(res["iniciales"]))
    m2.metric("Hechos inferidos", len(res["derivados"]))
    m3.metric("Reglas disparadas", len(res["pasos"]))

    if not res["recomendaciones"]:
        st.warning("No hay información suficiente para emitir una recomendación. Prueba agregando más hechos.")
    for i, r in enumerate(res["recomendaciones"]):
        etiqueta = "⭐ RECOMENDACIÓN PRINCIPAL" if i == 0 else "Alternativa / complemento"
        clase = "rec" if i == 0 else "rec alt"
        st.markdown(f"""<div class="{clase}" style="{estilo}"><span class="badge">{etiqueta} · {r['regla']} · prioridad {r['prioridad']}</span>
        <h3>{r['texto']}</h3><div>{r['detalle']}</div></div>""", unsafe_allow_html=True)

    st.subheader("3️⃣ Inferencia paso a paso")
    total = len(res["pasos"])
    n = st.slider("Pasos visibles", 1, total, total) if total > 1 else total
    for p in res["pasos"][:n]:
        with st.expander(f"Paso {p['paso']} · [{p['fase']}] → {p['elegida']}", expanded=(p["paso"] == n)):
            st.markdown("**Conjunto de conflictos (reglas aplicables):**")
            st.dataframe([{"Regla": f"{c['id']} · {c['nombre']}", "Prioridad": c["prioridad"],
                           "Recencia": str(c["recencia"]), "Especificidad": c["especificidad"]}
                          for c in p["conflicto"]], use_container_width=True, hide_index=True)
            st.markdown(f"**Regla seleccionada:** {p['elegida']}  \n**Motivo:** {p['motivo']}")
            st.markdown("**Hechos nuevos:** " + (", ".join(motor.texto(h) for h in p["nuevos"]) or "ninguno"))

    st.subheader("4️⃣ ¿Por qué llegó a esa conclusión?")
    for r in res["recomendaciones"][:3]:
        with st.expander(f"Cadena de razonamiento: {r['texto']}"):
            st.code("\n".join(motor.cadena(res, r["id"])), language=None)

    if res["no_reconocidos"]:
        st.info("Hechos ignorados por no existir en la base: " + ", ".join(res["no_reconocidos"]))
    st.download_button("💾 Descargar resultado (JSON)",
                       json.dumps({x: res[x] for x in ("iniciales", "derivados", "recomendaciones")},
                                  ensure_ascii=False, indent=2),
                       file_name=f"resultado_{k}.json", mime="application/json")


dominio = st.session_state.get("dominio")
if dominio in DOMINIOS:
    pantalla_dominio(dominio)
else:
    inicio()