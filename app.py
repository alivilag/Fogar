import streamlit as st
import streamlit.components.v1 as components
from utils.db import supabase
from modules import auth, brain_dump, finance, cycle

st.set_page_config(page_title="Nuestra Casa", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

def inject_pwa_manifest():
    components.html(
        """<script>
            const link = document.createElement('link'); link.rel = 'manifest';
            link.href = '/app/public/manifest.json'; document.head.appendChild(link);
        </script>""", height=0
    )

st.markdown("""
    <style>
    /* Ocultar elementos por defecto de Streamlit para más limpieza */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}

    /* Botones minimalistas, redondeados y con sombras suaves */
    .stButton>button { 
        width: 100%; 
        border-radius: 20px; 
        height: 5.5em; 
        font-weight: 600; 
        font-size: 1.1em; 
        background-color: #FFFFFF;
        border: 2px solid #F4F6F9;
        color: #555555;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        transition: all 0.2s ease-in-out;
        white-space: pre-wrap; /* Permite saltos de línea */
        line-height: 1.3;
    }
    .stButton>button:hover { 
        transform: translateY(-2px); 
        border-color: #FF9999; 
        color: #FF9999;
        box-shadow: 0 6px 15px rgba(255,153,153,0.15);
    }

    /* Tarjetas y formularios más limpios */
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 20px;
        border: 1px solid #F0F2F6;
        box-shadow: 0 8px 20px rgba(0,0,0,0.02);
        padding: 1.5rem;
    }

    /* Pestañas (Tabs) con diseño aireado */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        border-radius: 12px 12px 0 0;
    }

    /* Campos de entrada redondeados */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    inject_pwa_manifest()
    
    if "user" not in st.session_state: st.session_state.user = None
    if "current_page" not in st.session_state: st.session_state.current_page = "home"
    if "household_id" not in st.session_state: st.session_state.household_id = None
    if "household_name" not in st.session_state: st.session_state.household_name = "Espacio Personal 👤"

    # 1. Pantalla de Login
    if not st.session_state.user:
        auth.login_ui()
        return

    # 2. Cargar hogar silenciosamente en segundo plano (si existe)
    if st.session_state.household_id is None:
        try:
            user_hhs = supabase.table("household_members").select("household_id, households(name)").eq("user_id", st.session_state.user.id).execute()
            if user_hhs.data:
                st.session_state.household_id = user_hhs.data[0]['household_id']
                st.session_state.household_name = f"Hogar: {user_hhs.data[0]['households']['name']} 🏠"
            else:
                st.session_state.household_id = "personal" # Marca para saber que ya comprobamos
        except Exception:
            pass

    # 3. Router Principal
    if st.session_state.current_page == "home":
        show_home_dashboard()
    else:
        show_module(st.session_state.current_page)

def show_home_dashboard():
    # Título compacto
    st.markdown(f"<p style='text-align: center; color: #b3b3b3; margin-bottom: -15px; font-size: 0.9em;'>{st.session_state.household_name}</p>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #FF9999; margin-bottom: 1.5rem; margin-top: 0px;'>Fogar ✨</h2>", unsafe_allow_html=True)
    
    # Cuadrícula 3x2 (3 columnas x 2 filas)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅\nTareas", use_container_width=True): st.session_state.current_page = "tasks"; st.rerun()
        if st.button("💰\nFinanzas", use_container_width=True): st.session_state.current_page = "finance"; st.rerun()
    with col2:
        if st.button("🍽️\nComidas", use_container_width=True): st.session_state.current_page = "meals"; st.rerun()
        if st.button("🩸\nCiclo", use_container_width=True): st.session_state.current_page = "cycle"; st.rerun()
    with col3:
        if st.button("📥\nDescarga", use_container_width=True): st.session_state.current_page = "brain_dump"; st.rerun()
        if st.button("👥\nHogares", use_container_width=True): st.session_state.current_page = "households"; st.rerun()
    
    st.divider()
    
    # Salida discreta centrada
    _, col_exit, _ = st.columns([1, 2, 1])
    with col_exit:
        if st.button("Cerrar Sesión", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

def show_module(page):
    if st.button("⬅️ Volver al menú", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()

    st.divider()

    if page == "brain_dump":
        st.header("Buzón de Descarga Mental")
        brain_dump.render_ui()
    elif page == "households":
        auth.household_ui()
    elif page == "finance":
        finance.render_ui()
    elif page == "cycle":
        cycle.render_ui()
    else:
        st.info("Módulo en construcción 🛠️")

if __name__ == "__main__":
    main()
