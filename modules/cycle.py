import streamlit as st
from utils.db import supabase
from datetime import date
import pandas as pd

def get_cycle_stats(user_id):
    # Calcula la media de los últimos 6 ciclos finalizados
    res = supabase.table("cycles").select("cycle_length").eq("user_id", user_id).not_.is_("end_date", "null").order("start_date", desc=True).limit(6).execute()
    ciclos = res.data
    
    if not ciclos:
        return 28 # Media estándar por defecto si no hay historial
    
    total_days = sum(c['cycle_length'] for c in ciclos if c['cycle_length'])
    return max(21, int(total_days / len(ciclos))) # Retorna la media (mínimo 21 días)

def get_current_phase(day, avg_length):
    # Proyección adaptada matemáticamente a la longitud del ciclo
    ovulation_day = int(avg_length / 2)
    
    if day <= 5:
        return "🩸 Fase Menstrual", "Baja energía. Priorizar descanso activo y alimentos ricos en hierro.", "#FFB3BA"
    elif day < ovulation_day - 1:
        return "🌱 Fase Folicular", "Pico de energía y tolerancia al esfuerzo. Ideal para alta intensidad.", "#BAFFC9"
    elif day <= ovulation_day + 1:
        return "🥚 Fase Ovulatoria", "Pico de fuerza neuromuscular. Máximo rendimiento y sociabilidad.", "#FFFFBA"
    else:
        return "🍂 Fase Lútea", "Aumento de fatiga y antojos (carbohidratos). Priorizar tareas ligeras y movilidad.", "#FFDFBA"

def render_ui():
    st.header("Ciclo Menstrual 🩸")
    
    user_id = st.session_state.user.id
    hoy = date.today()
    
    # 1. Recuperar el ciclo activo (aquel sin fecha de fin)
    res_active = supabase.table("cycles").select("*").eq("user_id", user_id).is_("end_date", "null").execute()
    ciclo_actual = res_active.data[0] if res_active.data else None
    
    avg_length = get_cycle_stats(user_id)
    
    # 2. Visualización de Fase Actual
    if ciclo_actual:
        start_date = date.fromisoformat(ciclo_actual['start_date'])
        current_day = (hoy - start_date).days + 1
        
        fase_nombre, fase_desc, color = get_current_phase(current_day, avg_length)
        
        st.markdown(f"### Día {current_day} (Media: {avg_length} días)")
        st.markdown(f"""
            <div style='background-color: {color}; padding: 15px; border-radius: 15px; color: #4A4A4A; border: 1px solid #F0F2F6; margin-bottom: 15px;'>
                <b style='font-size: 1.1em;'>{fase_nombre}</b><br>{fase_desc}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No tienes ningún ciclo activo registrado.")
        
    # Botón principal de un clic para registrar nuevo periodo
    if st.button("🩸 Empezó mi periodo hoy", use_container_width=True):
        if ciclo_actual:
            dias_ciclo = (hoy - start_date).days
            supabase.table("cycles").update({"end_date": hoy.isoformat(), "cycle_length": dias_ciclo}).eq("id", ciclo_actual['id']).execute()
        
        supabase.table("cycles").insert({"user_id": user_id, "start_date": hoy.isoformat()}).execute()
        st.success("¡Ciclo registrado!")
        st.rerun()

    st.divider()
    
    # 3. Check-in Diario (Alta velocidad, baja fricción)
    st.subheader("Check-in Diario")
    
    res_log = supabase.table("daily_logs").select("id").eq("user_id", user_id).eq("log_date", hoy.isoformat()).execute()
    
    if res_log.data:
        st.success("✅ Check-in completado por hoy.")
    else:
        with st.form("daily_log_form"):
            st.write("**Estado de ánimo**")
            mood = st.radio("Estado de ánimo", ["😊 Genial", "😐 Normal", "😫 Mal", "🤬 Irritable"], horizontal=True, label_visibility="collapsed")
            
            st.write("**Niveles físicos (1 - 10)**")
            col1, col2 = st.columns(2)
            with col1:
                energy = st.slider("⚡ Energía", 1, 10, 5)
            with col2:
                pain = st.slider("🤕 Molestias/Dolor", 1, 10, 1)
            
            if st.form_submit_button("Guardar Check-in"):
                if not ciclo_actual:
                    st.error("Registra primero el inicio de tu periodo arriba.")
                else:
                    supabase.table("daily_logs").insert({
                        "user_id": user_id,
                        "cycle_id": ciclo_actual['id'],
                        "log_date": hoy.isoformat(),
                        "mood": mood,
                        "energy_level": energy,
                        "pain_level": pain
                    }).execute()
                    st.rerun()
