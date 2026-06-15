import sqlite3
import streamlit as st
import datetime

# --- CONFIGURACIÓN DE LA PÁGINA Y BLINDAJE DE MENÚS ---
st.set_page_config(page_title="LuisAnth - Sistema Completo", page_icon="💰", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "luisanth.db"

def conectar_bd():
    return sqlite3.connect(DB_NAME)

# --- INICIALIZAR Y ACTUALIZAR BASE DE DATOS ---
def inicializar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Tabla de Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cedula TEXT UNIQUE NOT NULL,
        telefono TEXT NOT NULL,
        direccion TEXT DEFAULT 'No especificada',
        dia_pago TEXT NOT NULL,
        modalidad_pago TEXT NOT NULL,
        estado TEXT DEFAULT 'Activo'
    )
    """)
    
    # Tabla de Contratos (Campos separados para Capital y Total con Interés)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contratos (
        id_contrato INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        tipo TEXT,
        monto_inicial REAL NOT NULL, -- Actúa como Capital Prestado
        capital_prestado REAL DEFAULT 0, -- Respaldo explícito del capital neto
        monto_total_adeudado REAL DEFAULT 0, -- Capital + Interés Total Inicial
        saldo_pendiente REAL NOT NULL, -- Balance pendiente total que va bajando
        tasa_interes REAL NOT NULL,
        turno_san INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'Activo',
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    )
    """)
    
    # Script de migración interna automática por si la tabla ya existía
    try:
        cursor.execute("ALTER TABLE contratos ADD COLUMN capital_prestado REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE contratos ADD COLUMN monto_total_adeudado REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    # Ajustar registros viejos que tengan los campos nuevos vacíos
    cursor.execute("UPDATE contratos SET capital_prestado = monto_inicial WHERE capital_prestado = 0")
    cursor.execute("UPDATE contratos SET monto_total_adeudado = saldo_pendiente WHERE monto_total_adeudado = 0")
    
    # Tabla de Historial de Pagos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos (
        id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
        id_contrato INTEGER,
        abono_capital REAL NOT NULL, -- En San representa el pago de la cuota completa
        mora_cobrada REAL DEFAULT 0,
        fecha TEXT NOT NULL,
        FOREIGN KEY (id_contrato) REFERENCES contratos(id_contrato)
    )
    """)
    
    # Tabla de Cierres de Caja
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cierres_caja (
        id_cierre INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT UNIQUE NOT NULL,
        monto_fisico REAL NOT NULL,
        monto_sistema REAL NOT NULL,
        diferencia REAL NOT NULL
    )
    """)
    
    # Tabla de Capital base de la empresa
    cursor.execute("CREATE TABLE IF NOT EXISTS negocio (id INTEGER PRIMARY KEY, capital_total REAL)")
    cursor.execute("SELECT COUNT(*) FROM negocio")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO negocio (id, capital_total) VALUES (1, 500000.00)")
        
    conn.commit()
    conn.close()

inicializar_bd()

# --- CREDENCIALES DE SEGURIDAD ---
USUARIOS = {
    "anthonny": "admin123",       
    "luisangel": "socio456"       
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["rol"] = None
    st.session_state["usuario_actual"] = ""

if not st.session_state["autenticado"]:
    st.title("💰 Bienvenidos a LuisAnth")
    st.subheader("Control de Préstamos & Soluciones Financieras")
    st.markdown("---")
    
    with st.form("form_login"):
        st.write("🔒 **Introduce tus credenciales de acceso:**")
        usuario_input = st.text_input("Usuario:").lower().strip()
        clave_input = st.text_input("Contraseña:", type="password")
        boton_entrar = st.form_submit_button("Iniciar Sesión")
        
        if boton_entrar:
            if usuario_input in USUARIOS and clave_input == USUARIOS[usuario_input]:
                st.session_state["autenticado"] = True
                st.session_state["usuario_actual"] = usuario_input
                st.session_state["rol"] = "admin" if usuario_input == "anthonny" else "socio"
                st.rerun()
            else:
                st.error("⚠️ Usuario o contraseña incorrectos")

else:
    col_saludo, col_salir = st.columns([3, 1])
    with col_saludo:
        st.write(f"👤 Conectado: **{st.session_state['usuario_actual'].capitalize()}**")
    with col_salir:
        if st.button("Cerrar Sesión"):
            st.session_state["autenticado"] = False
            st.session_state["rol"] = None
            st.session_state["usuario_actual"] = ""
            st.rerun()

    # --- MENÚ DINÁMICO ---
    if st.session_state["rol"] == "admin":
        menu_opciones = [
            "📊 Panel Financiero", 
            "🔍 Buscador de Clientes",
            "📋 Cartera y Deudas",
            "👤 Registrar Cliente", 
            "📝 Crear Préstamo / San",
            "💸 Registrar Cobro (WhatsApp)",
            "🧮 Calculadora de Cuotas",
            "📅 Cobros del Día",
            "🔒 Cierre de Caja"
        ]
    else:
        menu_opciones = [
            "🔍 Buscador de Clientes",
            "📋 Cartera y Deudas",
            "👤 Registrar Cliente", 
            "📝 Crear Préstamo / San",
            "💸 Registrar Cobro (WhatsApp)",
            "🧮 Calculadora de Cuotas",
            "📅 Cobros del Día",
            "🔒 Cierre de Caja"
        ]
        
    opcion = st.selectbox("📂 Selecciona la sección que deseas gestionar:", menu_opciones)
    st.markdown("---")

    # ==========================================
    # PANTALLA: BUSCADOR DE CLIENTES + EDICIÓN COMPLETA (DESGLOSADA)
    # ==========================================
    if opcion == "🔍 Buscador de Clientes":
        st.header("🔍 Buscador General de Clientes")
        busqueda = st.text_input("Escribe el nombre o la cédula del cliente para buscar:")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cl.id_cliente, cl.nombre, cl.cedula, cl.telefono, cl.direccion, cl.dia_pago, cl.modalidad_pago, cl.estado,
                   co.id_contrato, co.tipo, co.capital_prestado, co.monto_total_adeudado, co.saldo_pendiente
            FROM clientes cl
            LEFT JOIN contratos co ON cl.id_cliente = co.id_cliente AND co.estado = 'Activo'
            WHERE cl.nombre LIKE ? OR cl.cedula LIKE ?
        """, (f"%{busqueda}%", f"%{busqueda}%"))
        
        resultados = cursor.fetchall()
        conn.close()
        
        if resultados:
            for r in resultados:
                id_clie, nombre_clie, cedula_clie, telf_clie, dir_clie, dia_clie, mod_clie, est_clie, id_cont, tipo_cont, cap_pres, tot_adeu, saldo_cont = r
                
                label_tarjeta = f"👤 {nombre_clie} - Cédula: {cedula_clie}"
                if tipo_cont:
                    label_tarjeta += f" ({tipo_cont} - Restan: ${saldo_cont:,.2f})"
                
                with st.expander(label_tarjeta):
                    if st.session_state["rol"] == "admin":
                        st.markdown("📝 **Modo Administrador: Edición y Desglose Financiero**")
                        
                        with st.form(f"form_edit_{id_clie}"):
                            nuevo_nombre = st.text_input("Nombre Completo:", value=nombre_clie)
                            nueva_cedula = st.text_input("Cédula de Identidad:", value=cedula_clie)
                            nuevo_telf = st.text_input("Número de Teléfono:", value=telf_clie)
                            nueva_dir = st.text_input("Dirección de Residencia:", value=dir_clie)
                            nuevo_dia = st.selectbox("Día de Cobro:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"], index=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"].index(dia_clie))
                            nueva_mod = st.selectbox("Modalidad de Cobro:", ["Semanal", "Quincenal", "Mensual"], index=["Semanal", "Quincenal", "Mensual"].index(mod_clie))
                            nuevo_est = st.selectbox("Estado del Perfil:", ["Activo", "Inactivo"], index=["Activo", "Inactivo"].index(est_clie))
                            
                            if id_cont:
                                st.markdown("---")
                                st.write(f"📋 **Estructura Interna del Contrato ({tipo_cont}):**")
                                st.write(f"🔹 **Capital Neto Entregado:** ${cap_pres:,.2f}")
                                st.write(f"🔹 **Monto Adeudado Inicial (Con Interés):** ${tot_adeu:,.2f}")
                                
                                # El balance pendiente total que va bajando es editable por errores de digitación
                                nuevo_saldo = st.number_input("Corregir Balance Pendiente Total Actual ($):", min_value=0.0, value=float(saldo_cont), step=100.0)
                            
                            st.markdown("---")
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                btn_actualizar = st.form_submit_button("💾 Guardar Cambios")
                            with col_btn2:
                                btn_eliminar = st.form_submit_button("🚨 Eliminar por Completo")
                            
                            if btn_actualizar:
                                conn = conectar_bd()
                                cursor = conn.cursor()
                                try:
                                    cursor.execute("""
                                        UPDATE clientes 
                                        SET nombre=?, cedula=?, telefono=?, direccion=?, dia_pago=?, modalidad_pago=?, estado=?
                                        WHERE id_cliente=?
                                    """, (nuevo_nombre, nueva_cedula, nuevo_telf, nueva_dir, nuevo_dia, nueva_mod, nuevo_est, id_clie))
                                    
                                    if id_cont:
                                        cursor.execute("UPDATE contratos SET saldo_pendiente=? WHERE id_contrato=?", (nuevo_saldo, id_cont))
                                        
                                    conn.commit()
                                    st.success("¡Información y balances actualizados con éxito!")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("Error: Esa cédula ya pertenece a otra persona.")
                                conn.close()
                                
                            if btn_eliminar:
                                conn = conectar_bd()
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM pagos WHERE id_contrato IN (SELECT id_contrato FROM contratos WHERE id_cliente=?)", (id_clie,))
                                cursor.execute("DELETE FROM contratos WHERE id_cliente=?", (id_clie,))
                                cursor.execute("DELETE FROM clientes WHERE id_cliente=?", (id_clie,))
                                conn.commit()
                                conn.close()
                                st.warning("El cliente y todos sus registros financieros han sido eliminados.")
                                st.rerun()
                    else:
                        st.write(f"**Teléfono:** {telf_clie}")
                        st.write(f"**Dirección:** {dir_clie}")
                        st.write(f"**Ruta de cobro:** {dia_clie} ({mod_clie})")
                        if tipo_cont:
                            st.markdown("---")
                            st.write(f"📈 **Contrato:** {tipo_cont}")
                            st.write(f"💵 **Capital Prestado:** ${cap_pres:,.2f}")
                            st.write(f"💰 **Total con Intereses:** ${tot_adeu:,.2f}")
                            st.write(f"📉 **Balance Pendiente Actual:** ${saldo_cont:,.2f}")

        else:
            st.warning("No hay coincidencias en la base de datos.")

    # ==========================================
    # PANTALLA: CARTERA Y DEUDAS
    # ==========================================
    elif opcion == "📋 Cartera y Deudas":
        st.header("📋 Lista de Clientes, Modalidades y Saldos Pendientes")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cl.nombre, co.tipo, co.capital_prestado, co.monto_total_adeudado, co.saldo_pendiente
            FROM clientes cl
            LEFT JOIN contratos co ON cl.id_cliente = co.id_cliente
            WHERE co.estado = 'Activo' OR co.estado IS NULL
            ORDER BY co.saldo_pendiente DESC
        """)
        cartera = cursor.fetchall()
        conn.close()
        
        if not cartera:
            st.info("No hay transacciones activas.")
        else:
            datos_tabla = []
            for item in cartera:
                nombre_c, tipo_c, cap_p, tot_a, pend_c = item
                modalidad_visual = tipo_c if tipo_c else "Sin contrato activo"
                
                datos_tabla.append({
                    "Cliente": nombre_c,
                    "Modalidad": modalidad_visual,
                    "Capital Prestado": f"${cap_p:,.2f}" if cap_p else "$0.00",
                    "Deuda Inicial Total": f"${tot_a:,.2f}" if tot_a else "$0.00",
                    "Balance Pendiente Actual": f"${pend_c:,.2f}" if pend_c else "$0.00"
                })
            st.table(datos_tabla)

    # ==========================================
    # PANTALLA: PANEL FINANCIERO (LÓGICA MATEMÁTICA PURA REESTRUCTURADA)
    # ==========================================
    elif opcion == "📊 Panel Financiero" and st.session_state["rol"] == "admin":
        st.header("Balance General - Modo Administrador")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT capital_total FROM negocio WHERE id = 1")
        capital_total = cursor.fetchone()[0]
        
        nuevo_capital = st.number_input("Inyectar / Editar Capital Total ($):", min_value=0.0, value=float(capital_total), step=5000.0)
        if nuevo_capital != capital_total:
            cursor.execute("UPDATE negocio SET capital_total = ? WHERE id = 1", (nuevo_capital,))
            conn.commit()
            capital_total = nuevo_capital
            st.success("¡Capital base actualizado!")

        cursor.execute("SELECT capital_prestado, monto_total_adeudado, saldo_pendiente, tasa_interes, tipo FROM contratos WHERE estado = 'Activo'")
        contratos_activos = cursor.fetchall()
        
        cursor.execute("SELECT SUM(mora_cobrada) FROM pagos")
        total_moras = cursor.fetchone()[0] or 0.0
        conn.close()
        
        dinero_total_por_cobrar = sum(c[2] for c in contratos_activos) # Suma total de los balances pendientes ($39k, $26k, etc)
        
        capital_neto_en_la_calle = 0
        ganancias_proyectadas_totales = 0
        
        for c in contratos_activos:
            cap_neto_entregado, total_con_interes, balance_actual, tasa, tipo_c = c
            
            if "San" in tipo_c:
                interes_ganancia = total_con_interes - cap_neto_entregado
                ganancias_proyectadas_totales += interes_ganancia
                
                # Calculamos cuánto dinero ha retornado el cliente a la fecha
                dinero_total_pagado = total_con_interes - balance_actual
                
                # Lógica contable: los pagos primero reponen el capital invertido que salió de caja
                if dinero_total_pagado >= cap_neto_entregado:
                    capital_pendiente_en_calle = 0.0
                else:
                    capital_pendiente_en_calle = cap_neto_entregado - dinero_total_pagado
                    
                capital_neto_en_la_calle += capital_pendiente_en_calle
            else:
                # Esquema de Rédito
                capital_neto_en_la_calle += balance_actual
                ganancias_proyectadas_totales += balance_actual * (tasa / 100)
        
        # El dinero real físico que queda en caja se basa estrictamente en el capital limpio que salió de tu bolsillo
        capital_disponible_caja = max(0.0, capital_total - capital_neto_en_la_calle)

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        
        col1.metric("Capital Total de Inversión", f"${capital_total:,.2f}")
        col2.metric("Capital Neto en Calle", f"${capital_neto_en_la_calle:,.2f}")
        col3.metric("Disponible Físico en Caja", f"${capital_disponible_caja:,.2f}")
        col4.metric("Balance Total por Cobrar", f"${dinero_total_por_cobrar:,.2f}")
        
        st.markdown("---")
        st.metric("Ganancias Futuras Esperadas de Cartera", f"${ganancias_proyectadas_totales:,.2f}")
        st.metric("Ingresos de Caja Extras por Mora", f"${total_moras:,.2f}")

    # ==========================================
    # PANTALLA: REGISTRAR CLIENTE
    # ==========================================
    elif opcion == "👤 Registrar Cliente":
        st.header("Agregar Nuevo Cliente")
        
        with st.form("form_cliente", clear_on_submit=True):
            nombre = st.text_input("Nombre Completo:")
            cedula = st.text_input("Cédula de Identidad:")
            telefono = st.text_input("Número de Teléfono:")
            direccion = st.text_input("Dirección de Residencia:")
            dia_pago = st.selectbox("Día de Cobro:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
            modalidad_pago = st.selectbox("Modalidad de Pago:", ["Semanal", "Quincenal", "Mensual"])
            
            boton_guardar = st.form_submit_button("Guardar Cliente")
            
            if boton_guardar:
                if nombre and cedula and telefono:
                    try:
                        conn = conectar_bd()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO clientes (nombre, cedula, telefono, direccion, dia_pago, modalidad_pago) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (nombre, cedula, telefono, direccion, dia_pago, modalidad_pago))
                        conn.commit()
                        conn.close()
                        st.success(f"¡Cliente {nombre} agregado correctamente!")
                    except sqlite3.IntegrityError:
                        st.error("Error: Esa cédula ya está registrada.")
                else:
                    st.warning("Por favor rellene todos los campos obligatorios.")

    # ==========================================
    # PANTALLA: CREAR PRÉSTAMO / SAN (SEPARACIÓN DE CAPITAL E INTERÉS)
    # ==========================================
    elif opcion == "📝 Crear Préstamo / San":
        st.header("Asignar Préstamo o San")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT id_cliente, nombre FROM clientes WHERE estado = 'Activo'")
        clientes_activos = cursor.fetchall()
        conn.close()
        
        if not clientes_activos:
            st.warning("Debes registrar al menos un cliente activo primero.")
        else:
            opciones_clientes = {c[1]: c[0] for c in clientes_activos}
            cliente_seleccionado = st.selectbox("Selecciona el Cliente:", list(opciones_clientes.keys()))
            
            tipo_contrato = st.selectbox("Modalidad del Contrato:", ["San Frio", "San Caliente", "Redito"])
            monto_entregado = st.number_input("Monto entregado neto en efectivo ($):", min_value=1.0, step=500.0)
            
            tasa_defecto = 10.0 if tipo_contrato == "Redito" else 20.0
            tasa = st.number_input("Tasa de interés (%):", min_value=0.0, value=tasa_defecto, step=1.0)
            
            turno_san = 0
            if "San" in tipo_contrato:
                turno_san = st.number_input("Asignar Número de Turno/Cobro para el San:", min_value=1, value=1, step=1)
            
            if st.button("Activar Contrato"):
                id_clie = opciones_clientes[cliente_seleccionado]
                
                # Separación de variables financieras claras
                capital_prestado = monto_entregado
                
                if "San" in tipo_contrato:
                    interes_calculado = monto_entregado * (tasa / 100)
                    monto_total_adeudado = round(monto_entregado + interes_calculado, 2)
                    saldo_pendiente_inicial = monto_total_adeudado
                else:
                    monto_total_adeudado = monto_entregado
                    saldo_pendiente_inicial = monto_entregado
                
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO contratos (id_cliente, tipo, monto_inicial, capital_prestado, monto_total_adeudado, saldo_pendiente, tasa_interes, turno_san)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_clie, tipo_contrato, monto_entregado, capital_prestado, monto_total_adeudado, saldo_pendiente_inicial, tasa, turno_san))
                conn.commit()
                conn.close()
                st.success(f"¡Contrato {tipo_contrato} activado de forma correcta!")
                st.info(f"💵 Capital entregado: ${capital_prestado:,.2f} | 📈 Total con interés a cobrar: ${monto_total_adeudado:,.2f}")

    # ==========================================
    # PANTALLA: REGISTRAR COBRO / PAGO (BALANCE DISMINUYE CON CADA PAGO)
    # ==========================================
    elif opcion == "💸 Registrar Cobro (WhatsApp)":
        st.header("Registrar Cobros y Generar Factura Personalizada")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT co.id_contrato, cl.nombre, co.tipo, co.saldo_pendiente, co.tasa_interes, cl.cedula, cl.telefono, cl.direccion
            FROM contratos co 
            JOIN clientes cl ON co.id_cliente = cl.id_cliente 
            WHERE co.estado = 'Activo'
        """)
        contratos_pendientes = cursor.fetchall()
        conn.close()
        
        if not contratos_pendientes:
            st.info("No hay transacciones activas de cobro.")
        else:
            dic_contratos = {f"{c[1]} ({c[2]} - Restan: ${c[3]:,.2f})": c for c in contratos_pendientes}
            seleccion = st.selectbox("Selecciona el préstamo a cobrar:", list(dic_contratos.keys()))
            
            contrato_data = dic_contratos[seleccion]
            id_contrato, nombre_clie, tipo, saldo_actual, tasa_int, cedula_clie, telefono_clie, direccion_clie = contrato_data
            
            st.markdown("---")
            
            if "San" in tipo:
                st.info(f"📋 **Modalidad: {tipo}**")
                monto_pagando = st.number_input("Monto Total que está pagando en esta cuota ($):", min_value=0.0, max_value=float(saldo_actual), step=100.0)
                mora_cobrada = st.number_input("Agregar cargo de Mora / Penalidad ($):", min_value=0.0, value=0.0, step=50.0)
                abono_al_balance = monto_pagando
                pago_redito_efectivo = 0
            else:
                st.info("📋 **Modalidad: Rédito**")
                pago_redito_efectivo = st.number_input("Monto que está pagando únicamente por concepto de Rédito / Interés ($):", min_value=0.0, step=100.0)
                abono_al_balance = st.number_input("Monto extra que está abonando directo al Capital para bajarlo ($):", min_value=0.0, max_value=float(saldo_actual), step=100.0)
                mora_cobrada = st.number_input("Agregar cargo de Mora / Penalidad ($):", min_value=0.0, value=0.0, step=50.0)
            
            if st.button("Procesar Cobro e Historial"):
                conn = conectar_bd()
                cursor = conn.cursor()
                
                # El balance pendiente total se reduce directamente por el abono ingresado
                nuevo_saldo = round(saldo_actual - abono_al_balance, 2)
                fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
                
                cursor.execute("""
                    INSERT INTO pagos (id_contrato, abono_capital, mora_cobrada, fecha) 
                    VALUES (?, ?, ?, ?)
                """, (id_contrato, abono_al_balance, mora_cobrada, fecha_hoy))
                
                if nuevo_saldo <= 0:
                    cursor.execute("UPDATE contratos SET saldo_pendiente = 0, estado = 'Inactivo' WHERE id_contrato = ?", (id_contrato,))
                    st.success(f"¡El cliente {nombre_clie} ha saldado su cuenta por completo!")
                else:
                    cursor.execute("UPDATE contratos SET saldo_pendiente = ? WHERE id_contrato = ?", (nuevo_saldo, id_contrato))
                    st.success("Cobro guardado con éxito.")
                    
                conn.commit()
                conn.close()
                
                if "San" in tipo:
                    texto_recibo = f"""
📝 *RECIBO DE PAGO - LUISANTH*
-------------------------------------------
*Cliente:* {nombre_clie}
*Cédula:* {cedula_clie}
*Teléfono:* {telefono_clie}
*Fecha:* {fecha_hoy}
*Modalidad:* {tipo}
-------------------------------------------
*Monto Pagando:* ${monto_pagando:,.2f}
*Mora Aplicada:* ${mora_cobrada:,.2f}
-------------------------------------------
*Balance Pendiente Total:* ${nuevo_saldo:,.2f}
-------------------------------------------
¡Gracias por su pago confiable!
                    """
                else:
                    texto_recibo = f"""
📝 *RECIBO DE PAGO - LUISANTH*
-------------------------------------------
*Cliente:* {nombre_clie}
*Cédula:* {cedula_clie}
*Teléfono:* {telefono_clie}
*Dirección:* {direccion_clie}
*Fecha:* {fecha_hoy}
*Modalidad:* Rédito
-------------------------------------------
*Pago de Rédito:* ${pago_redito_efectivo:,.2f}
*Abono a Capital:* ${abono_al_balance:,.2f}
*Mora Aplicada:* ${mora_cobrada:,.2f}
-------------------------------------------
*Balance Capital Pendiente:* ${nuevo_saldo:,.2f}
-------------------------------------------
¡Gracias por su pago confiable!
                    """
                st.text_area("Copia este texto para enviarlo por WhatsApp:", value=texto_recibo.strip(), height=260)

    # ==========================================
    # LAS DEMÁS PANTALLAS SE MANTIENEN IGUAL
    # ==========================================
    elif opcion == "🧮 Calculadora de Cuotas":
        st.header("Calculadora de Alta Precisión LuisAnth")
        tipo_calc = st.radio("Tipo de Estructura Financiera:", ["Fijo por San (Frío / Caliente)", "Variable por Réditos (10% s/ Balance)"])
        monto_sim = st.number_input("Monto del capital solicitado ($):", min_value=1.0, value=20000.0, step=500.0)
        frecuencia_sim = st.selectbox("Frecuencia de los pagos:", ["Semanal", "Quincenal", "Mensual"])
        st.markdown("---")
        
        if tipo_calc == "Fijo por San (Frío / Caliente)":
            tasa_sim = st.number_input("Tasa de interés total pactada para el San (%):", min_value=0.0, value=20.0, step=1.0)
            pagos_sim = st.number_input("Número total de turnos / cuotas a dividir:", min_value=1, value=10, step=1)
            if st.button("Calcular Plan Fijo"):
                interes_total = round(monto_sim * (tasa_sim / 100), 2)
                monto_total = round(monto_sim + interes_total, 2)
                cuota_resultado = round(monto_total / pagos_sim, 2)
                st.subheader("📊 Resultados del Plan Fijo")
                st.info(f"**Capital Neto:** ${monto_sim:,.2f} | **Interés Total del San:** ${interes_total:,.2f}")
                st.success(f"**Monto Neto a Retornar:** ${monto_total:,.2f}")
                st.metric(label=f"Cuota fija obligatoria ({frecuencia_sim})", value=f"${cuota_resultado:,.2f}")
        else:
            tasa_redito = st.number_input("Tasa fija de rédito aplicada (%):", min_value=0.0, value=10.0, step=0.5)
            porcentaje_abono = st.slider("Porcentaje estimado de abono al capital por período (%):", min_value=5, max_value=100, value=25, step=5)
            balance = monto_sim
            abono_fijo_capital = round(monto_sim * (porcentaje_abono / 100), 2)
            datos_tabla = []
            periodo = 1
            while balance > 0 and periodo <= 20:
                interes_periodo = round(balance * (tasa_redito / 100), 2)
                abono_efectivo = balance if balance < abono_fijo_capital else abono_fijo_capital
                total_cobro_periodo = round(interes_periodo + abono_efectivo, 2)
                balance_restante = round(balance - abono_efectivo, 2)
                datos_tabla.append({
                    "Período": periodo,
                    "Balance Inicial": f"${balance:,.2f}",
                    "Interés (Rédito)": f"${interes_periodo:,.2f}",
                    "Abono a Capital": f"${abono_efectivo:,.2f}",
                    "Cobro Mínimo Total": f"${total_cobro_periodo:,.2f}",
                    "Balance Restante": f"${balance_restante:,.2f}"
                })
                balance = balance_restante
                periodo += 1
            st.table(datos_tabla)

    elif opcion == "📅 Cobros del Día":
        st.header("Recordatorio Automático de Cobros")
        dia_actual = st.selectbox("Selecciona el día de hoy para revisar la ruta:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.nombre, c.telefono, co.tipo, co.saldo_pendiente, co.tasa_interes, c.modalidad_pago, co.turno_san
            FROM clientes c
            JOIN contratos co ON c.id_cliente = co.id_cliente
            WHERE c.estado = 'Activo' AND co.estado = 'Activo' AND c.dia_pago = ?
        """, (dia_actual,))
        cobros = cursor.fetchall()
        conn.close()
        if not cobros:
            st.success(f"No hay cobros programados para los días {dia_actual}.")
        else:
            st.write(f"Tienes **{len(cobros)}** cobros pendientes para hoy:")
            for cob in cobros:
                if cob[2] == "Redito":
                    interes_hoy = round(cob[3] * (cob[4] / 100), 2)
                    st.warning(f"👤 **{cob[0]}** | **Rédito** | Cobro Rédito Mínimo: **${interes_hoy:,.2f}** (Saldo actual: ${cob[3]:,.2f})")
                else:
                    st.info(f"👤 **{cob[0]}** | **{cob[2]}** (Turno San: #{cob[6]}) | Saldo Restante: ${cob[3]:,.2f} ({cob[5]})")

    elif opcion == "🔒 Cierre de Caja":
        st.header("Arqueo y Cuadre de Caja Diario")
        fecha_cierre = datetime.date.today().strftime("%Y-%m-%d")
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT capital_total FROM negocio WHERE id = 1")
        capital_total = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(saldo_pendiente) FROM contratos WHERE estado = 'Activo'")
        en_calle = cursor.fetchone()[0] or 0.0
        conn.close()
        monto_sistema_esperado = round(capital_total - en_calle, 2)
        st.info(f"💰 **Dinero esperado en caja física según sistema:** ${monto_sistema_esperado:,.2f}")
        monto_fisico_real = st.number_input("Introduce la cantidad de dinero en efectivo REAL que tienes en mano ($):", min_value=0.0, step=100.0)
        if st.button("Guardar Cierre de Caja"):
            diferencia = round(monto_fisico_real - monto_sistema_esperado, 2)
            try:
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cierres_caja (fecha, monto_fisico, monto_sistema, diferencia) 
                    VALUES (?, ?, ?, ?)
                """, (fecha_cierre, monto_fisico_real, monto_sistema_esperado, diferencia))
                conn.commit()
                conn.close()
                if diferencia == 0:
                    st.success("¡Perfecto! La caja cuadró de forma exacta a los centavos ($0.00).")
                elif diferencia > 0:
                    st.warning(f"¡Atención! Tienes un SOBRANTE en caja física de: ${diferencia:,.2f}")
                else:
                    st.error(f"¡Alerta! Tienes un FALTANTE de dinero en caja física de: ${diferencia:,.2f}")
            except sqlite3.IntegrityError:
                st.error("Ya has guardado un arqueo de caja para el día de hoy.")