import streamlit as st
from utils.db import supabase

def login_ui():
    st.title("Bienvenido a Nuestra Casa 🏠")
    
    tab_login, tab_signup = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as e:
                    st.error("Error al iniciar sesión. Revisa tus datos.")
    
    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Tu Nombre (Ej. Laura)")
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Crear cuenta", use_container_width=True):
                try:
                    # 1. Crear usuario en Auth
                    res = supabase.auth.sign_up({"email": email, "password": password})
                    if res.user:
                        # 2. Guardar perfil público
                        supabase.table("users").insert({
                            "id": res.user.id, 
                            "name": name
                        }).execute()
                        st.success("¡Cuenta creada! Vuelve a la pestaña de Iniciar Sesión.")
                except Exception as e:
                    st.error("Error al registrar. Puede que el email ya exista.")

def household_ui():
    st.title("Tu Hogar 🏘️")
    st.write("Para empezar, crea un espacio para compartir con tu pareja.")
    
    with st.form("create_household"):
        hh_name = st.text_input("Nombre de vuestro hogar (Ej. El Nido)")
        if st.form_submit_button("Crear y entrar", use_container_width=True):
            try:
                # Crear hogar
                hh_res = supabase.table("households").insert({"name": hh_name}).execute()
                hh_id = hh_res.data[0]['id']
                
                # Vincular usuario al hogar
                supabase.table("household_members").insert({
                    "household_id": hh_id, 
                    "user_id": st.session_state.user.id
                }).execute()
                
                st.session_state.household_id = hh_id
                st.rerun()
            except Exception as e:
                st.error("Hubo un problema al crear el hogar.")
