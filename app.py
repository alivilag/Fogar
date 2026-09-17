import streamlit as st
from modules import brain_dump
import streamlit.components.v1 as components
# Importaciones modulares simuladas
# from utils.db import init_supabase
# from modules import tasks, meals, finance, cycle, dopamine, brain_dump, auth

# Configuración de página (Debe ser la primera línea)
st.set_page_config(
    page_title="Nuestra Casa", 
    page_icon="🏠", 
    layout="centered", 
    initial_sidebar_state="collapsed" # Sin sidebar para evitar distracción visual
)

# Inyección de PWA (Manifest) para iOS/Android
def inject_pwa_manifest():
    components.html(
        """
        <script>
            const link = document.createElement('link');
            link.rel = 'manifest';
            link.href = '/app/public/manifest.json'; /* Ruta ajustada al servidor estático */
            document.head.appendChild(link);
        </script>
        """,
        height=0,
    )

# Estilos CSS personalizados (UI Limpia, Botones grandes para TDAH)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
    }
    .emergency-btn>button {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    inject_pwa_manifest()
    
    # Simulación de estado de sesión
    if 'user' not in st.session_state:
        st.session_state.user = "autenticado" # Aquí iría la lógica de auth.py
        st.session_state.hyperfocus = False
    
    # Cabecera con botón de Hiperenfoque (Controla notificaciones de Telegram)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏠 Nuestra Casa")
    with col2:
        # Toggle visual sin fricción
        hf = st.toggle("🧠 No Molestar", value=st.session_state.hyperfocus)
        if hf != st.session_state.hyperfocus:
            st.session_state.hyperfocus = hf
            # Aquí iría: telegram.set_hyperfocus_mode(user_id, hf)
            st.toast("Modo Hiperenfoque actualizado", icon="🤫")

    # Navegación plana mediante Pestañas (Todo visible, cero menús ocultos)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "✅ Tareas", "🍽️ Comidas", "💰 Finanzas", "🩸 Ciclo", "📥 Descarga", "🎁 Cofre"
    ])

    with tab1:
        st.header("Tareas Pendientes")
        # task_list = tasks.get_tasks()
        # Mock de tarea
        col_chk, col_text = st.columns([1, 4])
        with col_chk:
            if st.checkbox(""):
                st.balloons() # Refuerzo positivo visual (Dopamina)
                # tasks.complete_task(id)
        with col_text:
            st.write("**Sacar la basura** - *Hoy, 20:00*")

    with tab2:
        st.header("Comidas y Despensa")
        # Botón de emergencia visualmente distinto
        st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
        if st.button("🚨 CENAS DE EMERGENCIA (Sin energía)"):
            st.warning("Opciones: Quesadillas, Huevos revueltos, Pasta con atún.")
        st.markdown('</div>', unsafe_allow_html=True)
        # meals.render_ui()

    with tab3:
        st.header("Finanzas Compartidas")
        st.subheader("Objetivo: Viaje a Japón")
        st.progress(0.45) # Barra de progreso visual (Dopamina)
        st.caption("45% completado (450€ / 1000€)")
        # finance.render_ui()

    with tab4:
        st.header("Seguimiento del Ciclo")
        # cycle.render_ui()

    with tab5:
        st.header("Buzón de Descarga Mental")
        brain_dump.render_ui()

    with tab6:
        st.header("Cofre de Dopamina")
        st.info("Desbloqueado: **Noche de cine y pizza pagada por el fondo común** 🍕🎬")

if __name__ == "__main__":
    main()
