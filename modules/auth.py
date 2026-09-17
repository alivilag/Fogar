def household_ui():
    st.header("Gestión de Hogares 🏘️")
    st.write("Crea un espacio para compartir tareas y gastos con otra persona.")
    
    with st.form("create_household"):
        hh_name = st.text_input("Nombre de vuestro hogar (Ej. El Nido)")
        if st.form_submit_button("Crear y entrar", use_container_width=True):
            try:
                # 1. Crear hogar
                hh_res = supabase.table("households").insert({"name": hh_name}).execute()
                hh_id = hh_res.data[0]['id']
                
                # 2. Vincular usuario
                supabase.table("household_members").insert({
                    "household_id": hh_id, 
                    "user_id": st.session_state.user.id
                }).execute()
                
                # 3. Actualizar estado
                st.session_state.household_id = hh_id
                st.session_state.household_name = f"Hogar: {hh_name} 🏠"
                st.success("¡Hogar creado! Vuelve al menú para empezar a usarlo.")
            except Exception as e:
                # AQUÍ ESTÁ LA CLAVE: Esto nos dirá por qué falló la base de datos
                st.error(f"Error detallado: {e}")
