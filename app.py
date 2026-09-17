import streamlit as st
import streamlit.components.v1 as components
from utils.db import supabase
from modules import auth, brain_dump

st.set_page_config(page_title="Nuestra Casa", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

# Inyección PWA
def inject_pwa_manifest():
    components.html(
        """
        <script>
            const link = document.createElement('link');
            link.rel = 'manifest';
            link.href = '/app/public/manifest.json';
            document.head.appendChild(link);
        </script>
        """,
        height=0,
    )

# Estilos CSS (Botones grandes y UI limpia)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 16px;
        height: 4em;
        font-weight: bold;
        font-size: 1.1em;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        border-color: #FF4B4B;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    inject_pwa_manifest()
    
    # Inicializar variables de estado
    if "user" not in st.session_state:
        st.session_state.user = None
    if "household_id" not in st.session_state:
        st.session_state.household_id = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    # 1. Pantalla de Login
    if not st.session_state.user:
        auth.login_ui()
        return

    # 2. Pantalla de Selección/Creación de Hogar
    if not st.session_state.household_id:
        try:
            # Buscar si el usuario ya pertenece a un hogar
            user_hhs = supabase.table("household_members").select("household_id, households(name)").eq("user_id", st.session_state.user.id).execute()
            
            if user_hhs.data:
                st.title("Selecciona tu Hogar")
                for hh in user_hhs.data:
                    if st.button(f"🏠 {hh['households']['name']}", use_container_width=True):
                        st.session_state.household_id = hh['household_id']
                        st.rerun()
            else:
                auth.household_ui()
        except Exception as e:
            st.error("Error al cargar los hogares.")
        return

    # 3. Router Principal
    if st.session_state.current_page == "home":
        show_home_dashboard()
    else:
        show_module(st.session_state.current_page)

def show_home_dashboard():
    st.title("🏠 Nuestra Casa")
    st.write("¿Qué necesitas hacer? (Sin presiones)")
    
    # Grid visual de botones
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Tareas"):
            st.session_state.current_page = "tasks"
            st.rerun()
        if st.button("🍽️ Comidas"):
            st.session_state.current_page = "meals"
            st.rerun()
        if st.button("📥 Descarga"):
            st.session_state.current_page = "brain_dump"
            st.rerun()
    with col2:
        if st.button("💰 Finanzas"):
            st.session_state.current_page = "finance"
            st.rerun()
        if st.button("🩸 Ciclo"):
            st.session_state.current_page = "cycle"
            st.rerun()
        if st.button("🎁 Cofre"):
            st.session_state.current_page = "dopamine"
            st.rerun()
    
    st.divider()
    if st.button("Cerrar Sesión", type="secondary"):
        st.session_state.user = None
        st.session_state.household_id = None
        st.rerun()

def show_module(page):
    # Navegación hacia atrás, sin fricción
    if st.button("⬅️ Volver al menú", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.divider()
    
    if page == "brain_dump":
        st.header("Buzón de Descarga Mental")
        brain_dump.render_ui()
    else:
        st.info("Módulo en construcción 🛠️")
        st.caption("Aquí irá el contenido en los próximos pasos.")

if __name__ == "__main__":
    main()
