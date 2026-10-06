import streamlit as st
from utils.db import supabase
from datetime import datetime, date, timedelta
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

def actualizar_ahorros(user_id, diff):
    res_savings = supabase.table("savings").select("*").eq("user_id", user_id).execute()
    ahorros = res_savings.data
    if len(ahorros) == 1:
        new_amount = ahorros[0]['amount'] + diff
        supabase.table("savings").update({"amount": new_amount}).eq("id", ahorros[0]['id']).execute()
        st.info(f"Ahorros actualizados automáticamente: {new_amount:.2f} €")
    elif len(ahorros) > 1:
        st.warning("⚠️ Tienes varias cuentas de ahorro. Ajusta el saldo manualmente.")

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
            
            # Fecha directa por defecto hoy
            fecha_input = st.date_input("Fecha del movimiento", value=date.today())
            
            is_common = False
            if tipo == "gasto" and st.session_state.household_id and st.session_state.household_id != "personal":
                is_common = st.checkbox("🏠 Es un gasto común (pagado por mí, pero a dividir)")
            
            if st.form_submit_button("Guardar Movimiento", use_container_width=True):
                created_at = datetime.combine(fecha_input, datetime.min.time()).isoformat()
                
                if is_common:
                    # LÓGICA DOBLE ASIENTO
                    hh_res = supabase.table("households").select("*").eq("id", st.session_state.household_id).execute()
                    split_pcts = hh_res.data[0].get('split_percentages', {})
                    split_mode = hh_res.data[0].get('split_mode', '50/50')
                    
                    members_res = supabase.table("household_members").select("user_id").eq("household_id", st.session_state.household_id).execute()
                    miembros = [m['user_id'] for m in members_res.data]
                    
                    my_id = st.session_state.user.id
                    other_ids = [u for u in miembros if u != my_id]
                    
                    if split_mode == 'Manual' and str(my_id) in split_pcts:
                        my_pct = float(split_pcts[str(my_id)])
                    elif split_mode in ['Proporcional a ingresos del mes anterior', 'Proporcional a balance del mes anterior']:
                        hoy = date.today()
                        primer_dia_este_mes = hoy.replace(day=1)
                        ultimo_dia_mes_pasado = primer_dia_este_mes - timedelta(days=1)
                        primer_dia_mes_pasado = ultimo_dia_mes_pasado.replace(day=1)
                        
                        inicio_prev = f"{primer_dia_mes_pasado}T00:00:00"
                        fin_prev = f"{ultimo_dia_mes_pasado}T23:59:59"
                        
                        res_prev = supabase.table("transactions").select("user_id, amount, type, category").in_("user_id", miembros).gte("created_at", inicio_prev).lte("created_at", fin_prev).execute()
                        
                        if split_mode == 'Proporcional a ingresos del mes anterior':
                            ing_my = sum(t['amount'] for t in res_prev.data if t['user_id'] == my_id and t['type'] == 'ingreso' and t['category'] not in ["Cuentas por cobrar", "Cuentas por pagar", "Liquidación"])
                            ing_tot = sum(t['amount'] for t in res_prev.data if t['type'] == 'ingreso' and t['category'] not in ["Cuentas por cobrar", "Cuentas por pagar", "Liquidación"])
                            my_pct = (ing_my / ing_tot * 100) if ing_tot > 0 else 50.0
                        else:
                            balances = {u: 0.0 for u in miembros}
                            for t in res_prev.data:
                                if t['category'] not in ["Cuentas por cobrar", "Cuentas por pagar", "Liquidación"]:
                                    diff = t['amount'] if t['type'] == 'ingreso' else -t['amount']
                                    balances[t['user_id']] += diff
                            
                            val_my = max(0, balances[my_id])
                            val_tot = sum(max(0, balances[u]) for u in miembros)
                            my_pct = (val_my / val_tot * 100) if val_tot > 0 else 50.0
                    else:
                        my_pct = 50.0
                    other_pct = 100.0 - my_pct
                    
                    my_amount = amount * (my_pct / 100)
                    other_amount = amount * (other_pct / 100)
                    
                    data_list = []
                    # 1. Gasto real del pagador
                    if my_amount > 0:
                        data_list.append({"user_id": my_id, "type": "gasto", "amount": my_amount, "category": category, "description": description, "is_common": True, "household_id": st.session_state.household_id, "created_at": created_at})
                    
                    # 2. Préstamo a terceros (baja liquidez del pagador, no afecta gráficas consumo)
                    if other_amount > 0:
                        data_list.append({"user_id": my_id, "type": "gasto", "amount": other_amount, "category": "Cuentas por cobrar", "description": f"Préstamo a la casa por {description}", "is_common": True, "household_id": st.session_state.household_id, "created_at": created_at})
                        
                        for o_id in other_ids:
                            # 3. Gasto real del no-pagador (se añade automáticamente a su consumo)
                            data_list.append({"user_id": o_id, "type": "gasto", "amount": other_amount, "category": category, "description": f"{description} (Adelantado por compañer@)", "is_common": True, "household_id": st.session_state.household_id, "created_at": created_at})
                            # 4. Deuda del no-pagador (Ingreso ficticio para mantener su liquidez intacta hasta que pague)
                            data_list.append({"user_id": o_id, "type": "ingreso", "amount": other_amount, "category": "Cuentas por pagar", "description": f"Deuda con la casa por {description}", "is_common": True, "household_id": st.session_state.household_id, "created_at": created_at})
                    
                    try:
                        supabase.table("transactions").insert(data_list).execute()
                        st.success("Gasto común dividido y registrado en todas las cuentas.")
                        actualizar_ahorros(my_id, -amount) # Solo baja la liquidez real del que paga
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    # MOVIMIENTO INDIVIDUAL
                    data = {
                        "user_id": st.session_state.user.id,
                        "type": tipo,
                        "amount": amount,
                        "category": category,
                        "description": description,
                        "is_common": False,
                        "household_id": None,
                        "created_at": created_at
                    }
                    try:
                        supabase.table("transactions").insert(data).execute()
                        st.success("Movimiento registrado.")
                        diff = amount if tipo == 'ingreso' else -amount
                        actualizar_ahorros(st.session_state.user.id, diff)
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

def render_personal_finances():
    mes, anio = get_period_selectors('pers')
    fecha_inicio, fecha_fin, titulo = get_date_range(mes, anio)
    
    st.subheader(f"📊 {titulo}")
    
    res = supabase.table("transactions").select("*").eq("user_id", st.session_state.user.id).gte("created_at", fecha_inicio).lte("created_at", fecha_fin).execute()
    movs = res.data
    
    categorias_tecnicas = ["Cuentas por cobrar", "Cuentas por pagar", "Liquidación"]
    
    # 1. Filtramos los movimientos para dejar solo el consumo e ingresos reales
    movs_reales = [m for m in movs if m['category'] not in categorias_tecnicas]
    
    # 2. Sumamos solo las cantidades reales
    ingresos_reales = sum(m['amount'] for m in movs_reales if m['type'] == 'ingreso')
    gastos_reales = sum(m['amount'] for m in movs_reales if m['type'] == 'gasto')
    balance_real = ingresos_reales - gastos_reales

    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos Reales", f"{ingresos_reales:.2f} €")
    col2.metric("Gastos Reales", f"{gastos_reales:.2f} €")
    col3.metric("Balance Real", f"{balance_real:.2f} €", delta=f"{balance_real:.2f} €")

    # Recordatorio de deudas pendientes debajo de las métricas
    if st.session_state.household_id and st.session_state.household_id != "personal":
        members_res = supabase.table("household_members").select("user_id, users(name)").eq("household_id", st.session_state.household_id).execute()
        nombres = {m['user_id']: m['users']['name'] for m in members_res.data}
        res_deudas = supabase.table("transactions").select("*").eq("household_id", st.session_state.household_id).in_("category", ["Cuentas por cobrar", "Cuentas por pagar", "Liquidación"]).execute()
        
        deuda_mia = 0.0
        for t in res_deudas.data:
            if t['user_id'] == st.session_state.user.id:
                if t['category'] == "Cuentas por cobrar": deuda_mia += t['amount']
                elif t['category'] == "Cuentas por pagar": deuda_mia -= t['amount']
                elif t['category'] == "Liquidación":
                    deuda_mia += t['amount'] if t['type'] == 'gasto' else -t['amount']
        
        if deuda_mia > 0.01:
            st.caption(f"🟢 **Te deben {deuda_mia:.2f} €** en el hogar.")
        elif deuda_mia < -0.01:
            st.caption(f"🔴 **Debes {abs(deuda_mia):.2f} €** a {next(n for u, n in nombres.items() if u != st.session_state.user.id)}.")

    if movs_reales:
        st.divider()
        if mes != 0:
            st.write("**Gráficos de Consumo Real**")
            tipo_grafico = st.radio("Selecciona:", ["Gastos", "Ingresos"], horizontal=True)
            
            if tipo_grafico == "Gastos":
                cat_gastos = {}
                for m in movs_reales:
                    if m['type'] == 'gasto':
                        cat_gastos[m['category']] = cat_gastos.get(m['category'], 0) + m['amount']
                plot_pie_chart(cat_gastos, "Categoría", "Consumo (€)")
            else:
                desc_ingresos = {}
                for m in movs_reales:
                    if m['type'] == 'ingreso':
                        desc_ingresos[m['description']] = desc_ingresos.get(m['description'], 0) + m['amount']
                plot_pie_chart(desc_ingresos, "Descripción", "Ingreso (€)")
        else:
            # Gráfico de Neto Anual
            st.write("**Evolución de Balance Neto Anual**")
            data_anual = {m: {'Neto': 0.0} for m in range(1, 13)}
            for m in movs_reales:
                mes_mov = int(m['created_at'][5:7])
                if m['type'] == 'ingreso':
                    data_anual[mes_mov]['Neto'] += m['amount']
                else:
                    data_anual[mes_mov]['Neto'] -= m['amount']
                    
            df_anual = pd.DataFrame.from_dict(data_anual, orient='index')
            df_anual.index.name = 'Mes'
            st.bar_chart(df_anual)

    with st.expander("Ver lista de movimientos"):
        for m in sorted(movs_reales, key=lambda x: x['created_at'], reverse=True): # Iteramos sobre reales para ocultar los técnicos
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
    
    st.write("**Evolución de Liquidez por Mes (Flujo Neto)**")
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
        modos = ['50/50', 'Manual', 'Proporcional a ingresos del mes anterior', 'Proporcional a balance del mes anterior']
        nuevo_modo = st.selectbox("Modo de reparto", modos, index=modos.index(split_mode) if split_mode in modos else 0)
        
        nuevos_pcts = split_pcts
        if nuevo_modo == 'Manual':
            st.write("Ajusta los porcentajes (deben sumar 100):")
            col1, col2 = st.columns(2)
            u_ids = list(miembros.keys())
            
            p1 = col1.number_input(f"% de {miembros[u_ids[0]]}", min_value=0, max_value=100, value=int(split_pcts.get(u_ids[0], 50)))
            p2 = col2.number_input(f"% de {miembros[u_ids[1]]}", min_value=0, max_value=100, value=100-p1, disabled=True)
            nuevos_pcts = {u_ids[0]: p1, u_ids[1]: 100-p1}

        if st.button("Guardar Configuración"):
            supabase.table("households").update({"split_mode": nuevo_modo, "split_percentages": nuevos_pcts}).eq("id", st.session_state.household_id).execute()
            st.success("Configuración actualizada")
            st.rerun()

    u_ids = list(miembros.keys())

    # CÁLCULO DE DEUDAS (Requiere historial completo, sin filtro de fecha)
    res_deudas = supabase.table("transactions").select("*").in_("user_id", u_ids).in_("category", ["Cuentas por cobrar", "Cuentas por pagar", "Liquidación"]).execute()
    
    deudas_netas = {u: 0.0 for u in u_ids}
    for t in res_deudas.data:
        u = t['user_id']
        if t['category'] == "Cuentas por cobrar": deudas_netas[u] += t['amount']
        elif t['category'] == "Cuentas por pagar": deudas_netas[u] -= t['amount']
        elif t['category'] == "Liquidación":
            if t['type'] == 'ingreso': deudas_netas[u] -= t['amount']
            elif t['type'] == 'gasto': deudas_netas[u] += t['amount']

    st.subheader("📈 Balance de Deudas")
    for u in u_ids:
        neto = deudas_netas[u]
        if neto > 0.01:
            st.success(f"↳ A **{miembros[u]}** le deben {neto:.2f} €")
        elif neto < -0.01:
            st.error(f"↳ **{miembros[u]}** debe {abs(neto):.2f} €")
        else:
            st.info(f"↳ **{miembros[u]}** está en paz.")

    # FORMULARIO DE LIQUIDACIÓN
    deudores = [u for u in u_ids if deudas_netas[u] < -0.01]
    acreedores = [u for u in u_ids if deudas_netas[u] > 0.01]
    
    if deudores and acreedores:
        with st.expander("💸 Saldar Deuda"):
            with st.form("settle_debt_form"):
                col1, col2 = st.columns(2)
                from_u = col1.selectbox("Quién paga", deudores, format_func=lambda x: miembros[x])
                to_u = col2.selectbox("A quién", acreedores, format_func=lambda x: miembros[x])
                
                max_debt = min(abs(deudas_netas[from_u]), deudas_netas[to_u])
                settle_amount = st.number_input("Cantidad a saldar (€)", min_value=0.01, max_value=float(max_debt), value=float(max_debt), step=10.0)
                
                if st.form_submit_button("Saldar Deuda"):
                    timestamp = datetime.now().isoformat()
                    # Salida de liquidez del deudor
                    supabase.table("transactions").insert({"user_id": from_u, "type": "gasto", "amount": settle_amount, "category": "Liquidación", "description": f"Liquidación a {miembros[to_u]}", "is_common": True, "household_id": st.session_state.household_id, "created_at": timestamp}).execute()
                    # Entrada de liquidez al acreedor
                    supabase.table("transactions").insert({"user_id": to_u, "type": "ingreso", "amount": settle_amount, "category": "Liquidación", "description": f"Liquidación de {miembros[from_u]}", "is_common": True, "household_id": st.session_state.household_id, "created_at": timestamp}).execute()
                    
                    actualizar_ahorros(from_u, -settle_amount)
                    actualizar_ahorros(to_u, settle_amount)
                    st.success("Deuda saldada correctamente.")
                    st.rerun()

    st.divider()

    # CONSUMO COMPARTIDO DEL PERÍODO
    fecha_inicio, fecha_fin, titulo = get_date_range(mes, anio)
    res_trans = supabase.table("transactions").select("*").in_("user_id", u_ids).gte("created_at", fecha_inicio).lte("created_at", fecha_fin).eq("is_common", True).execute()
    
    # Agrupamos los asientos para reconstruir el ticket original y saber quién pagó
    tickets = {}
    for t in res_trans.data:
        if t['type'] == 'gasto':
            clave = t['created_at']
            if clave not in tickets:
                tickets[clave] = {"pagador": None, "total": 0.0, "desc": "", "cat": ""}
            
            # Si no tiene la muletilla "(Adelantado por compañer@)", este apunte es del que pagó físicamente
            if "(Adelantado por compañer@)" not in t['description']:
                tickets[clave]["pagador"] = t['user_id']
                tickets[clave]["total"] += t['amount']
                if t['category'] != "Cuentas por cobrar":
                    tickets[clave]["desc"] = t['description']
                    tickets[clave]["cat"] = t['category']
                elif not tickets[clave]["desc"]:
                    tickets[clave]["desc"] = t['description'].replace("Préstamo a la casa por ", "")

    total_comun = sum(d["total"] for d in tickets.values())

    st.subheader(f"Consumo Común: {titulo}")
    st.write(f"**Gasto Total Compartido Generado:** {total_comun:.2f} €")

    if tickets:
        if mes != 0:
            cat_comunes = {}
            for d in tickets.values():
                cat_comunes[d['cat']] = cat_comunes.get(d['cat'], 0) + d['total']
            plot_pie_chart(cat_comunes, "Categoría", "Total (€)")
        else:
            data_comunes_anual = {m: 0.0 for m in range(1, 13)}
            for clave, d in tickets.items():
                mes_mov = int(clave[5:7])
                data_comunes_anual[mes_mov] += d['total']
            df_comunes = pd.DataFrame(list(data_comunes_anual.items()), columns=["Mes", "Gasto (€)"]).set_index("Mes")
            st.bar_chart(df_comunes)

        with st.expander("Ver lista de gastos comunes"):
            for clave, data in sorted(tickets.items(), key=lambda x: x[0], reverse=True):
                if data["pagador"]:
                    fecha_corta = clave[:10]
                    st.write(f"*{fecha_corta}* - **{miembros[data['pagador']]}** pagó {data['total']:.2f} € en *{data['desc']}*")
