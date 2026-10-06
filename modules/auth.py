import streamlit as st
from utils.db import supabase

def login_ui():
    st.title("Bienvenido a Fogar 🏠")
    
    tab_login, tab_signup = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    
                    # Parche: Garantizar que el usuario existe en la tabla pública al loguearse
                    supabase.table("users").upsert({
                        "id": res.user.id, 
                        "name": email.split('@')[0]
                    }).execute()
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error detallado: {e}")
    
    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Tu Nombre (Ej. Laura)")
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Crear cuenta", use_container_width=True):
                try:
                    res = supabase.auth.sign_up({"email": email, "password": password})
                    if res.user:
                        # Usamos upsert para evitar errores de duplicidad si el registro falló antes a medias
                        supabase.table("users").upsert({
                            "id": res.user.id, 
                            "name": name
                        }).execute()
                        st.success("¡Cuenta creada! Vuelve a la pestaña de Iniciar Sesión para entrar.")
                except Exception as e:
                    st.error(f"Error detallado: {e}")

def household_ui():
    st.header("Gestión de Hogares 🏘️")
    
    # Si el usuario ya está en un hogar, le mostramos el código para invitar a su pareja
    if st.session_state.household_id and st.session_state.household_id != "personal":
        st.success("Ya perteneces a un hogar.")
        st.write("Comparte este **Código de Invitación** con tu pareja para que se una:")
        st.code(st.session_state.household_id)
        return

    st.write("Crea un espacio nuevo o únete al de tu pareja.")
    
    tab_create, tab_join = st.tabs(["Crear Hogar", "Unirse con Código"])
    
    with tab_create:
        with st.form("create_household"):
            hh_name = st.text_input("Nombre de vuestro hogar (Ej. El Nido)")
            if st.form_submit_button("Crear y generar código", use_container_width=True):
                try:
                    hh_res = supabase.table("households").insert({"name": hh_name}).execute()
                    hh_id = hh_res.data[0]['id']
                    
                    supabase.table("household_members").insert({
                        "household_id": hh_id, 
                        "user_id": st.session_state.user.id
                    }).execute()
                    
                    st.session_state.household_id = hh_id
                    st.session_state.household_name = f"Hogar: {hh_name} 🏠"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error detallado: {e}")

    with tab_join:
        with st.form("join_household"):
            join_code = st.text_input("Pega aquí el código de invitación")
            if st.form_submit_button("Unirse al hogar", use_container_width=True):
                try:
                    # Comprobar que el hogar existe
                    hh_res = supabase.table("households").select("name").eq("id", join_code.strip()).execute()
                    
                    if hh_res.data:
                        # Vincular usuario al hogar existente
                        supabase.table("household_members").insert({
                            "household_id": join_code.strip(), 
                            "user_id": st.session_state.user.id
                        }).execute()
                        
                        st.session_state.household_id = join_code.strip()
                        st.session_state.household_name = f"Hogar: {hh_res.data[0]['name']} 🏠"
                        st.success("¡Te has unido con éxito!")
                        st.rerun()
                    else:
                        st.error("No se ha encontrado ningún hogar con ese código.")
                except Exception as e:
                    st.error(f"Error al unirse. Comprueba que el código es exacto. Detalle: {e}")
