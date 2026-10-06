import streamlit as st
import json
import base64
import streamlit.components.v1 as components
from utils.db import supabase
from modules import auth, brain_dump, finance, cycle, meals

st.set_page_config(page_title="Nuestra Casa", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

def inject_pwa_manifest():
    manifest = {
        "name": "Nuestra Casa",
        "short_name": "Casa",
        "description": "Gestor de convivencia",
        "start_url": "https://fogarapp.streamlit.app/",
        "display": "standalone",
        "background_color": "#FFFFFF",
        "theme_color": "#FF9999",
        "icons": [
            {
                "src": "https://raw.githubusercontent.com/alivilag/Fogar/main/static/assets/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "https://raw.githubusercontent.com/alivilag/Fogar/main/static/assets/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    
    manifest_json = json.dumps(manifest)
    b64_manifest = base64.b64encode(manifest_json.encode()).decode()
    
    components.html(
        f"""<script>
            const parentDoc = window.parent.document;
            
            // 1. Destruir los manifiestos por defecto de Streamlit
            const oldManifests = parentDoc.querySelectorAll('link[rel="manifest"]');
            oldManifests.forEach(el => el.remove());
            
            // 2. Inyectar manifiesto en Base64 (evita problemas de rutas)
            const newManifest = parentDoc.createElement('link');
            newManifest.rel = 'manifest';
            newManifest.href = 'data:application/json;base64,{b64_manifest}';
            parentDoc.head.appendChild(newManifest);
        </script>""", height=0
    )

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

    # 2. Cargar datos de usuario y hogar silenciosamente
    if "user_name" not in st.session_state:
        try:
            user_res = supabase.table("users").select("name").eq("id", st.session_state.user.id).execute()
            st.session_state.user_name = user_res.data[0]['name'] if user_res.data else "Usuario"
        except Exception:
            st.session_state.user_name = "Usuario"

    if st.session_state.household_id is None:
        try:
            user_hhs = supabase.table("household_members").select("household_id, households(name)").eq("user_id", st.session_state.user.id).execute()
            if user_hhs.data:
                st.session_state.household_id = user_hhs.data[0]['household_id']
                st.session_state.household_name = f"Hogar: {user_hhs.data[0]['households']['name']} 🏠"
            else:
                st.session_state.household_id = "personal" 
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
    st.markdown(f"<h2 style='text-align: center; color: #FF9999; margin-bottom: 1.5rem; margin-top: 0px;'>Hola, {st.session_state.user_name} ✨</h2>", unsafe_allow_html=True)
    
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
    elif page == "meals":
        meals.render_ui()
    else:
        st.info("Módulo en construcción 🛠️")

if __name__ == "__main__":
    main()
