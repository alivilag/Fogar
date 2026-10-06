import streamlit as st
from utils.db import supabase

def render_ui():
    st.header("Finanzas 💰")
    
    tab_add, tab_personal, tab_home = st.tabs(["➕ Nuevo", "👤 Mis Finanzas", "🏠 Cuentas del Hogar"])
    
    with tab_add:
        add_transaction_form()
        
    with tab_personal:
        render_personal_finances()
        
    with tab_home:
        if st.session_state.household_id and st.session_state.household_id != "personal":
            render_household_finances()
        else:
            st.info("No tienes un hogar configurado. Ve a 'Mis Hogares' para unirte a uno.")

def add_transaction_form():
    with st.container(border=True):
        with st.form("transaction_form", clear_on_submit=True):
            tipo = st.radio("Tipo de movimiento", ["gasto", "ingreso"], horizontal=True)
            
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Cantidad (€)", min_value=0.01, format="%0.2f")
            with col2:
                categorias = ["Comida", "Casa", "Ocio", "Transporte", "Salud", "Sueldo", "Otros"]
                category = st.selectbox("Categoría", categorias)
            
            description = st.text_input("Descripción (Ej. Compra súper)")
            
            # Solo mostrar checkbox si es un gasto y el usuario está en un hogar
            is_common = False
            if tipo == "gasto" and st.session_state.household_id and st.session_state.household_id != "personal":
                is_common = st.checkbox("🏠 Es un gasto común (pagado por mí, pero a dividir)")
            
            if st.form_submit_button("Guardar", use_container_width=True):
                data = {
                    "user_id": st.session_state.user.id,
                    "type": tipo,
                    "amount": amount,
                    "category": category,
                    "description": description,
                    "is_common": is_common,
                    "household_id": st.session_state.household_id if is_common else None
                }
                try:
                    supabase.table("transactions").insert(data).execute()
                    st.success("Movimiento registrado.")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

def render_personal_finances():
    res = supabase.table("transactions").select("*").eq("user_id", st.session_state.user.id).execute()
    movs = res.data
    
    if not movs:
        st.write("Aún no tienes movimientos registrados.")
        return

    # Cálculos
    ingresos = sum(m['amount'] for m in movs if m['type'] == 'ingreso')
    gastos = sum(m['amount'] for m in movs if m['type'] == 'gasto')
    balance = ingresos - gastos

    # UI Balance
    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos", f"{ingresos:.2f} €")
    col2.metric("Gastos", f"{gastos:.2f} €")
    col3.metric("Balance", f"{balance:.2f} €", delta=f"{balance:.2f} €")
    
    st.divider()
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("📊 Gastos por categoría")
        cat_gastos = {}
        for m in movs:
            if m['type'] == 'gasto':
                cat_gastos[m['category']] = cat_gastos.get(m['category'], 0) + m['amount']
        
        # Ordenar categorías de mayor a menor gasto
        for k, v in sorted(cat_gastos.items(), key=lambda item: item[1], reverse=True):
            st.write(f"**{k}:** {v:.2f} €")

    with col_der:
        st.subheader("⏱️ Últimos movimientos")
        # Mostrar los 5 más recientes
        for m in sorted(movs, key=lambda x: x['created_at'], reverse=True)[:5]:
            icon = "🔴" if m['type'] == "gasto" else "🟢"
            badge = "*(Común)*" if m['is_common'] else ""
            st.caption(f"{m['category']} {badge}")
            st.write(f"{icon} **{m['description']}**: {m['amount']} €")
            st.write("---")

def render_household_finances():
    # Obtener todos los gastos comunes de este hogar específico
    res = supabase.table("transactions").select("*, users(name)").eq("household_id", st.session_state.household_id).eq("is_common", True).execute()
    comunes = res.data
    
    if not comunes:
        st.write("No hay gastos comunes registrados en este hogar.")
        return

    # Calcular quién ha pagado qué
    pagos_por_usuario = {}
    total_comun = 0

    for c in comunes:
        u_name = c['users']['name']
        pagos_por_usuario[u_name] = pagos_por_usuario.get(u_name, 0) + c['amount']
        total_comun += c['amount']

    # Dividir entre 2 (Asumiendo pareja)
    cuota_ideal = total_comun / 2

    # UI Resumen Hogar
    st.subheader(f"Gasto Total Compartido: {total_comun:.2f} €")
    st.write(f"Deberíais haber pagado **{cuota_ideal:.2f} €** cada uno.")
    
    st.divider()
    
    st.subheader("📈 Balance de Deudas")
    for usuario, pagado in pagos_por_usuario.items():
        diferencia = pagado - cuota_ideal
        st.write(f"**{usuario}** ha pagado: {pagado:.2f} €")
        
        if diferencia > 0:
            st.success(f"↳ Le deben {abs(diferencia):.2f} €")
        elif diferencia < 0:
            st.error(f"↳ Debe {abs(diferencia):.2f} €")
        else:
            st.info("↳ Está en paz.")

    st.divider()
    with st.expander("Ver lista de gastos comunes"):
        for m in sorted(comunes, key=lambda x: x['created_at'], reverse=True):
            st.write(f"**{m['users']['name']}** pagó {m['amount']} € en *{m['description']}* ({m['category']})")
