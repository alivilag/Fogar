import streamlit as st
from utils.db import supabase
from datetime import datetime, date
import calendar
import pandas as pd
import altair as alt

def render_ui():
    st.header("Finanzas 💰")
    
    tab_add, tab_personal, tab_savings, tab_home = st.tabs(["➕ Nuevo", "👤 Mis Finanzas", "🏦 Ahorros", "🏠 Cuentas del Hogar"])
    
    with tab_add:
        add_transaction_form()
        
    with tab_personal:
        render_personal_finances()
        
    with tab_savings:
        render_savings()
        
    with tab_home:
        if st.session_state.household_id and st.session_state.household_id != "personal":
            render_household_finances()
        else:
            st.info("No tienes un hogar configurado. Ve a 'Mis Hogares' para unirte a uno.")

def get_period_selectors(key_prefix):
    col_mes, col_anio = st.columns(2)
    with col_mes:
        mes_actual = datetime.now().month
        meses = {
            0: "Resumen Anual", 1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 
            10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        mes_sel = st.selectbox("Período", list(meses.keys()), index=mes_actual, format_func=lambda x: meses[x], key=f"{key_prefix}_mes")
    with col_anio:
        anio_actual = datetime.now().year
        anios = list(range(2026, 2031))
        idx_anio = anios.index(anio_actual) if anio_actual in anios else 0
        anio_sel = st.selectbox("Año", anios, index=idx_anio, key=f"{key_prefix}_anio")
    return mes_sel, anio_sel

def get_date_range(mes, anio):
    if mes == 0:
        inicio = f"{anio}-01-01T00:00:00"
        fin = f"{anio}-12-31T23:59:59"
        titulo = f"Resumen Anual ({anio})"
    else:
        _, ultimo_dia = calendar.monthrange(anio, mes)
        inicio = f"{anio}-{mes:02d}-01T00:00:00"
        fin = f"{anio}-{mes:02d}-{ultimo_dia}T23:59:59"
        titulo = f"Balance Mensual ({mes}/{anio})"
    return inicio, fin, titulo

def plot_pie_chart(data_dict, name_col, val_col):
    if not data_dict:
        st.info("No hay datos suficientes para el gráfico.")
        return
    df = pd.DataFrame(list(data_dict.items()), columns=[name_col, val_col])
    chart = alt.Chart(df).mark_arc(innerRadius=40).encode(
        theta=alt.Theta(field=val_col, type="quantitative"),
        color=alt.Color(field=name_col, type="nominal"),
        tooltip=[name_col, val_col]
    )
    st.altair_chart(chart, use_container_width=True)

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
            
            modificar_fecha = st.checkbox("Modificar fecha (por defecto hoy)")
            fecha_input = st.date_input("Fecha del movimiento", value=date.today()) if modificar_fecha else date.today()
            
            is_common = False
            if tipo == "gasto" and st.session_state.household_id and st.session_state.household_id != "personal":
                is_common = st.checkbox("🏠 Es un gasto común (pagado por mí, pero a dividir)")
            
            if st.form_submit_button("Guardar Movimiento", use_container_width=True):
                created_at = datetime.combine(fecha_input, datetime.min.time()).isoformat()
                
                data = {
                    "user_id": st.session_state.user.id,
                    "type": tipo,
                    "amount": amount,
                    "category": category,
                    "description": description,
                    "is_common": is_common,
                    "household_id": st.session_state.household_id if is_common else None,
                    "created_at": created_at
                }
                try:
                    supabase.table("transactions").insert(data).execute()
                    st.success("Movimiento registrado.")
                    
                    res_savings = supabase.table("savings").select("*").eq("user_id", st.session_state.user.id).execute()
                    ahorros = res_savings.data
                    
                    if len(ahorros) == 1:
                        diff = amount if tipo == 'ingreso' else -amount
                        new_amount = ahorros[0]['amount'] + diff
                        supabase.table("savings").update({"amount": new_amount}).eq("id", ahorros[0]['id']).execute()
                        st.info(f"Ahorros actualizados automáticamente: {new_amount:.2f} €")
                    elif len(ahorros) > 1:
                        st.warning("⚠️ Tienes varias cuentas de ahorro. Recuerda ir a la pestaña 'Ahorros' para ajustar el saldo manualmente.")
                        
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

def render_personal_finances():
    mes, anio = get_period_selectors('pers')
    fecha_inicio, fecha_fin, titulo = get_date_range(mes, anio)
    
    st.subheader(f"📊 {titulo}")
    
    res = supabase.table("transactions").select("*").eq("user_id", st.session_state.user.id).gte("created_at", fecha_inicio).lte("created_at", fecha_fin).execute()
    movs = res.data
    
    ingresos = sum(m['amount'] for m in movs if m['type'] == 'ingreso')
    gastos = sum(m['amount'] for m in movs if m['type'] == 'gasto')
    balance = ingresos - gastos

    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos", f"{ingresos:.2f} €")
    col2.metric("Gastos", f"{gastos:.2f} €")
    col3.metric("Neto", f"{balance:.2f} €", delta=f"{balance:.2f} €")
    
    if movs:
        st.divider()
        if mes != 0:
            st.write("**Gráficos por categoría**")
            tipo_grafico = st.radio("Selecciona:", ["Gastos", "Ingresos"], horizontal=True)
            
            if tipo_grafico == "Gastos":
                cat_gastos = {}
                for m in movs:
                    if m['type'] == 'gasto':
                        cat_gastos[m['category']] = cat_gastos.get(m['category'], 0) + m['amount']
                plot_pie_chart(cat_gastos, "Categoría", "Total (€)")
            else:
                desc_ingresos = {}
                for m in movs:
                    if m['type'] == 'ingreso':
                        desc_ingresos[m['description']] = desc_ingresos.get(m['description'], 0) + m['amount']
                plot_pie_chart(desc_ingresos, "Descripción", "Total (€)")
        else:
            st.write("**Evolución Mensual del Año**")
            data_anual = {m: {'Ingresos': 0.0, 'Gastos': 0.0, 'Neto': 0.0} for m in range(1, 13)}
            for m in movs:
                mes_mov = int(m['created_at'][5:7])
                if m['type'] == 'ingreso':
                    data_anual[mes_mov]['Ingresos'] += m['amount']
                else:
                    data_anual[mes_mov]['Gastos'] += m['amount']
                    
            for m in range(1, 13):
                data_anual[m]['Neto'] = data_anual[m]['Ingresos'] - data_anual[m]['Gastos']
                
            df_anual = pd.DataFrame.from_dict(data_anual, orient='index')
            df_anual.index.name = 'Mes'
            
            st.write("*Ingresos por mes*")
            st.bar_chart(df_anual['Ingresos'], color="#2e7b32")
            st.write("*Gastos por mes*")
            st.bar_chart(df_anual['Gastos'], color="#c62828")
            st.write("*Neto por mes*")
            st.bar_chart(df_anual['Neto'])

        with st.expander("Ver lista de movimientos"):
            for m in sorted(movs, key=lambda x: x['created_at'], reverse=True):
                icon = "🔴" if m['type'] == "gasto" else "🟢"
                fecha_corta = m['created_at'][:10]
                st.write(f"*{fecha_corta}* {icon} **{m['description']}** ({m['category']}): {m['amount']} €")

def render_savings():
    st.subheader("Mis Cuentas de Ahorro")
    
    res_savings = supabase.table("savings").select("*").eq("user_id", st.session_state.user.id).execute()
    ahorros = res_savings.data
    
    total_ahorrado = sum(a['amount'] for a in ahorros)
    st.metric("Total Ahorrado", f"{total_ahorrado:.2f} €")
    
    if ahorros:
        st.write("**Distribución del Ahorro**")
        ahorros_dict = {a['account_name']: a['amount'] for a in ahorros}
        plot_pie_chart(ahorros_dict, "Cuenta", "Total (€)")
    
    st.divider()
    
    for a in ahorros:
        col_name, col_amt, col_del = st.columns([3, 2, 1])
        col_name.write(f"**{a['account_name']}**")
        col_amt.write(f"{a['amount']:.2f} €")
        if col_del.button("🗑️", key=f"del_sav_{a['id']}"):
            supabase.table("savings").delete().eq("id", a['id']).execute()
            st.rerun()
            
    with st.expander("Añadir / Actualizar cuenta de ahorro"):
        with st.form("savings_form", clear_on_submit=True):
            acc_name = st.text_input("Nombre (Ej. Banco, Efectivo)")
            acc_amount = st.number_input("Cantidad actual (€)", min_value=0.00, format="%0.2f")
            if st.form_submit_button("Guardar"):
                existente = next((x for x in ahorros if x['account_name'].lower() == acc_name.lower()), None)
                if existente:
                    supabase.table("savings").update({"amount": acc_amount}).eq("id", existente['id']).execute()
                else:
                    supabase.table("savings").insert({
                        "user_id": st.session_state.user.id,
                        "account_name": acc_name,
                        "amount": acc_amount
                    }).execute()
                st.rerun()
                
    st.divider()
    
    # Gráfico de evolución de ahorros (Flujo Neto Anual)
    st.write("**Evolución de Ahorros por Mes (Basado en Neto de este año)**")
    anio_actual = datetime.now().year
    inicio_anio = f"{anio_actual}-01-01T00:00:00"
    res_movs = supabase.table("transactions").select("*").eq("user_id", st.session_state.user.id).gte("created_at", inicio_anio).execute()
    
    data_ahorro_anual = {m: 0.0 for m in range(1, 13)}
    for m in res_movs.data:
        mes_mov = int(m['created_at'][5:7])
        if m['type'] == 'ingreso':
            data_ahorro_anual[mes_mov] += m['amount']
        else:
            data_ahorro_anual[mes_mov] -= m['amount']
            
    df_ahorro = pd.DataFrame(list(data_ahorro_anual.items()), columns=["Mes", "Ahorrado (€)"]).set_index("Mes")
    st.bar_chart(df_ahorro)

def render_household_finances():
    mes, anio = get_period_selectors('house')
    
    hh_res = supabase.table("households").select("*").eq("id", st.session_state.household_id).execute()
    hh_data = hh_res.data[0]
    split_mode = hh_data.get('split_mode', '50/50')
    split_pcts = hh_data.get('split_percentages', {})

    members_res = supabase.table("household_members").select("user_id, users(name)").eq("household_id", st.session_state.household_id).execute()
    miembros = {m['user_id']: m['users']['name'] for m in members_res.data}
    
    if len(miembros) < 2:
        st.warning("Necesitas que otra persona se una al hogar para dividir gastos.")
        return

    with st.expander("⚙️ Configuración de Reparto de Gastos"):
        modos = ['50/50', 'Manual', 'Proporcional a ingresos', 'Proporcional a balance']
        nuevo_modo = st.selectbox("Modo de reparto", modos, index=modos.index(split_mode))
        
        nuevos_pcts = split_pcts
        if nuevo_modo == 'Manual':
            st.write("Ajusta los porcentajes (deben sumar 100):")
            col1, col2 = st.columns(2)
            u_ids = list(miembros.keys())
            
            p1 = col1.number_input(f"% de {miembros[u_ids[0]]}", min_value=0, max_value=100, value=split_pcts.get(u_ids[0], 50))
            p2 = col2.number_input(f"% de {miembros[u_ids[1]]}", min_value=0, max_value=100, value=100-p1, disabled=True)
            nuevos_pcts = {u_ids[0]: p1, u_ids[1]: 100-p1}

        if st.button("Guardar Configuración"):
            supabase.table("households").update({"split_mode": nuevo_modo, "split_percentages": nuevos_pcts}).eq("id", st.session_state.household_id).execute()
            st.success("Configuración actualizada")
            st.rerun()

    fecha_inicio, fecha_fin, titulo = get_date_range(mes, anio)
    
    u_ids = list(miembros.keys())
    res_trans = supabase.table("transactions").select("*").in_("user_id", u_ids).gte("created_at", fecha_inicio).lte("created_at", fecha_fin).execute()
    todas_trans = res_trans.data

    ingresos = {u: 0.0 for u in u_ids}
    gastos_indiv = {u: 0.0 for u in u_ids}
    pagos_comunes = {u: 0.0 for u in u_ids}
    gastos_comunes_lista = []
    
    for t in todas_trans:
        u = t['user_id']
        if t['type'] == 'ingreso':
            ingresos[u] += t['amount']
        elif t['type'] == 'gasto':
            if t['is_common']:
                pagos_comunes[u] += t['amount']
                gastos_comunes_lista.append(t)
            else:
                gastos_indiv[u] += t['amount']

    total_comun = sum(pagos_comunes.values())
    
    porcentajes = {u: 50.0 for u in u_ids}
    if split_mode == 'Manual':
        porcentajes = {u: split_pcts.get(str(u), 50) for u in u_ids}
    elif split_mode == 'Proporcional a ingresos':
        total_ingresos = sum(ingresos.values())
        if total_ingresos > 0:
            porcentajes = {u: (ingresos[u] / total_ingresos) * 100 for u in u_ids}
    elif split_mode == 'Proporcional a balance':
        balances = {u: max(0, ingresos[u] - gastos_indiv[u]) for u in u_ids}
        total_balance = sum(balances.values())
        if total_balance > 0:
            porcentajes = {u: (balances[u] / total_balance) * 100 for u in u_ids}

    st.subheader(f"Cuentas Comunes: {titulo}")
    st.write(f"**Gasto Total Compartido:** {total_comun:.2f} €")
    
    st.write("**Proporciones aplicadas en este período:**")
    for u in u_ids:
        st.write(f"- {miembros[u]}: {porcentajes[u]:.1f}%")

    st.divider()
    
    st.subheader("📈 Balance de Deudas")
    for u in u_ids:
        cuota = total_comun * (porcentajes[u] / 100)
        pagado = pagos_comunes[u]
        diferencia = pagado - cuota
        
        st.write(f"**{miembros[u]}** ha pagado: {pagado:.2f} € (Debería: {cuota:.2f} €)")
        
        if diferencia > 0.01:
            st.success(f"↳ Le deben {abs(diferencia):.2f} €")
        elif diferencia < -0.01:
            st.error(f"↳ Debe {abs(diferencia):.2f} €")
        else:
            st.info("↳ Está en paz.")

    if gastos_comunes_lista:
        st.divider()
        if mes != 0:
            st.write("**Gráfico de Gastos Comunes por Categoría**")
            cat_comunes = {}
            for m in gastos_comunes_lista:
                cat_comunes[m['category']] = cat_comunes.get(m['category'], 0) + m['amount']
            plot_pie_chart(cat_comunes, "Categoría", "Total (€)")
        else:
            st.write("**Evolución Anual de Gastos Comunes**")
            data_comunes_anual = {m: 0.0 for m in range(1, 13)}
            for m in gastos_comunes_lista:
                mes_mov = int(m['created_at'][5:7])
                data_comunes_anual[mes_mov] += m['amount']
                
            df_comunes = pd.DataFrame(list(data_comunes_anual.items()), columns=["Mes", "Gasto (€)"]).set_index("Mes")
            st.bar_chart(df_comunes)

        with st.expander("Ver lista de gastos comunes"):
            for m in sorted(gastos_comunes_lista, key=lambda x: x['created_at'], reverse=True):
                fecha_corta = m['created_at'][:10]
                st.write(f"*{fecha_corta}* - **{miembros[m['user_id']]}** pagó {m['amount']} € en *{m['description']}*")
