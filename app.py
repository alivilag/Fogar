import streamlit as st
import streamlit.components.v1 as components
from utils.db import supabase
from modules import auth, brain_dump

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
    .stButton>button { width: 100%; border-radius: 16px; height: 4em; font-weight: bold; font-size: 1.1em; }
    .stButton>button:hover { transform: scale(1.02); border-color: #FF4B4B; }
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
    st.caption(f"Actualmente en: **{st.session_state.household_name}**")
    st.title("Nuestra Casa")
    st.write("¿Qué necesitas hacer? (Sin presiones)")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Tareas"): st.session_state.current_page = "tasks"; st.rerun()
        if st.button("🍽️ Comidas"): st.session_state.current_page = "meals"; st.rerun()
        if st.button("📥 Descarga"): st.session_state.current_page = "brain_dump"; st.rerun()
    with col2:
        if st.button("💰 Finanzas"): st.session_state.current_page = "finance"; st.rerun()
        if st.button("🩸 Ciclo"): st.session_state.current_page = "cycle"; st.rerun()
        if st.button("👥 Mis Hogares"): st.session_state.current_page = "households"; st.rerun()
    
    st.divider()
    if st.button("Cerrar Sesión", type="secondary"):
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
    else:
        st.info("Módulo en construcción 🛠️")

if __name__ == "__main__":
    main()
