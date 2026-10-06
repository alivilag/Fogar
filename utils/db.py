import os
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_supabase() -> Client:
    """Inicializa y cachea la conexión a Supabase para que sea ultrarrápida."""
    try:
        url = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
        key = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Error al conectar con la base de datos. Revisa tus secrets.")
        return None

# Cliente global para importar en otros módulos
supabase = init_supabase()
