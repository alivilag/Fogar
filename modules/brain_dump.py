import streamlit as st
from utils.db import supabase

def render_ui():
    st.write("Escribe aquí lo que no quieres olvidar. Sin juicios, sin organizarlo ahora. 🍃")
    
    # Formulario de 1 clic (Evita la fricción de tener que categorizar)
    with st.form("brain_dump_form", clear_on_submit=True):
        note = st.text_area(
            "Nueva nota", 
            label_visibility="collapsed", 
            placeholder="Tengo que revisar el recibo de la luz...",
            height=150
        )
        
        submitted = st.form_submit_button("Soltar idea 📥", use_container_width=True)
        
        if submitted and note.strip():
            try:
                # Guardar en base de datos (Supabase)
                # Nota: Por ahora no filtramos por hogar hasta tener el login
                supabase.table("brain_dump").insert({
                    "note": note.strip()
                }).execute()
                
                st.success("¡Nota guardada! Tu mente está un poco más libre.")
                st.balloons() # Pequeño chute de dopamina visual
            except Exception as e:
                st.error("Oops, hubo un error al guardar.")

    st.divider()
    st.subheader("Buzón Actual")
    
    # Mostrar las notas guardadas
    try:
        response = supabase.table("brain_dump").select("*").order("created_at", desc=True).execute()
        notas = response.data
        
        if not notas:
            st.info("El buzón está vacío. ¡Mente despejada!")
        else:
            for nota in notas:
                with st.container(border=True):
                    st.write(nota['note'])
    except Exception as e:
        st.warning("No se pudieron cargar las notas antiguas.")
