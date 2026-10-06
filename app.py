import streamlit as st
import json
import base64
import streamlit.components.v1 as components
from utils.db import supabase
from modules import auth, brain_dump, finance, cycle, meals

st.set_page_config(page_title="Fogar", page_icon="static/assets/icon-192.png", layout="centered", initial_sidebar_state="collapsed")

def inject_pwa_manifest():
    components.html(
        """<script>
            const parentDoc = window.parent.document;
            
            function enforcePWA() {
                const badElements = parentDoc.querySelectorAll('link[rel="manifest"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]');
                badElements.forEach(el => el.remove());
                
                if (!parentDoc.querySelector('link[id="pwa-manifest"]')) {
                    const newManifest = parentDoc.createElement('link');
                    newManifest.id = 'pwa-manifest';
                    newManifest.rel = 'manifest';
                    // Llamada directa a GitHub Raw para evitar bloqueos del servidor de Streamlit
                    newManifest.href = 'https://raw.githubusercontent.com/alivilag/Fogar/main/static/assets/manifest.json';
                    parentDoc.head.appendChild(newManifest);
                }

                if (!parentDoc.querySelector('link[id="pwa-icon"]')) {
                    const newIcon = parentDoc.createElement('link');
                    newIcon.id = 'pwa-icon';
                    newIcon.rel = 'shortcut icon';
                    newIcon.href = 'https://raw.githubusercontent.com/alivilag/Fogar/main/static/assets/icon-192.png';
                    parentDoc.head.appendChild(newIcon);
                    
                    const appleIcon = parentDoc.createElement('link');
                    appleIcon.id = 'pwa-apple';
                    appleIcon.rel = 'apple-touch-icon';
                    appleIcon.href = 'https://raw.githubusercontent.com/alivilag/Fogar/main/static/assets/icon-192.png';
                    parentDoc.head.appendChild(appleIcon);
                }
            }
            
            enforcePWA();
            
            const observer = new MutationObserver(enforcePWA);
            observer.observe(parentDoc.head, { childList: true, subtree: true });

            if ('serviceWorker' in window.parent.navigator) {
                window.parent.navigator.serviceWorker.register('/app/static/assets/sw.js')
                .catch(err => console.error('Error SW', err));
            }
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
