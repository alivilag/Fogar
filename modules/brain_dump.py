import streamlit as st
from utils.db import supabase

def render_ui():
    st.header("Buzón de Descarga Mental 📥")
    
    user_id = str(st.session_state.user.id)
    household_id = str(st.session_state.get("household_id", "personal"))
    has_household = household_id != "personal"
    
    # Selector de ámbito
    if has_household:
        tipo_nota = st.radio("Ámbito de la anotación", ["Individual (Solo para mí)", "Común (Visible en el hogar)"], horizontal=True)
        target_id = household_id if tipo_nota.startswith("Común") else user_id
        is_common = tipo_nota.startswith("Común")
    else:
        target_id = user_id
        is_common = False
        st.caption("👤 Nota personal (Únete a un hogar para habilitar notas comunes)")
        
    # Formulario de nueva anotación
    with st.form("new_brain_dump", clear_on_submit=True):
        content = st.text_area("¿Qué tienes en la cabeza?")
        if st.form_submit_button("Añadir anotación", use_container_width=True):
            if content.strip():
                supabase.table("brain_dumps").insert({
                    "user_id": user_id,
                    "target_id": target_id,
                    "is_common": is_common,
                    "content": content.strip()
                }).execute()
                st.success("¡Anotación guardada!")
                st.rerun()
            else:
                st.warning("Escribe algo antes de guardar.")
                
    st.divider()
    
    # Cargar notas (personales del usuario + comunes del hogar)
    query = supabase.table("brain_dumps").select("id, user_id, content, is_common, target_id, users(name)")
    
    if has_household:
        res = query.or_(f"target_id.eq.{user_id},target_id.eq.{household_id}").order("created_at", desc=True).execute()
    else:
        res = query.eq("target_id", user_id).order("created_at", desc=True).execute()
        
    notes = res.data if res else []
    
    if not notes:
        st.info("No hay anotaciones pendientes. ¡Cabeza despejada! ✨")
        return
        
    st.subheader("Notas Actuales")
    
    for note in notes:
        note_id = note['id']
        is_note_common = note['is_common']
        author_name = note.get('users', {}).get('name', 'Alguien') if note.get('users') else st.session_state.get("user_name", "Usuario")
        
        badge = "🏠 Común" if is_note_common else "👤 Personal"
        
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{badge} | {author_name}**")
                
                edit_key = f"edit_mode_{note_id}"
                if st.session_state.get(edit_key, False):
                    new_content = st.text_area("Editar nota", value=note['content'], key=f"text_{note_id}")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("Guardar", key=f"save_{note_id}", use_container_width=True):
                            supabase.table("brain_dumps").update({"content": new_content}).eq("id", note_id).execute()
                            st.session_state[edit_key] = False
                            st.rerun()
                    with col_cancel:
                        if st.button("Cancelar", key=f"cancel_{note_id}", use_container_width=True):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    st.write(note['content'])
                    
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if note['user_id'] == user_id or is_note_common:
                    if st.button("✏️", key=f"btn_edit_{note_id}", use_container_width=True, help="Editar"):
                        st.session_state[edit_key] = True
                        st.rerun()
                    if st.button("🗑️", key=f"delete_{note_id}", use_container_width=True, type="secondary", help="Hablado / Borrar"):
                        supabase.table("brain_dumps").delete().eq("id", note_id).execute()
                        st.rerun()
            st.divider()
