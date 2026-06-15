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

# --- INICIALIZAR BASE DE DATOS ACTUALIZADA ---
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
    
    # Tabla de Contratos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contratos (
        id_contrato INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        tipo TEXT,
        monto_inicial REAL NOT NULL,
        saldo_pendiente REAL NOT NULL,
        tasa_interes REAL NOT NULL,
        turno_san INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'Activo',
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    )
    """)
    
    # Tabla de Historial de Pagos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos (
        id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
        id_contrato INTEGER,
        abono_capital REAL NOT NULL,
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
    
    # Tabla de Capital
    cursor.execute("CREATE TABLE IF NOT EXISTS negocio (id INTEGER PRIMARY KEY, capital_total REAL)")
    cursor.execute("SELECT COUNT(*) FROM negocio")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO negocio (id, capital_total) VALUES (1, 500000.00)")
        
    conn.commit()
    conn.close()

inicializar_bd()

# --- SEGURIDAD ---
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

    # --- MENÚ DE OPCIONES ---
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
    # PANTALLA ACTUALIZADA: BUSCADOR DE CLIENTES + EDICIÓN/BORRADO (SOLO ADMIN)
    # ==========================================
    if opcion == "🔍 Buscador de Clientes":
        st.header("🔍 Buscador General de Clientes")
        busqueda = st.text_input("Escribe el nombre o la cédula del cliente para buscar:")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        if busqueda:
            cursor.execute("SELECT id_cliente, nombre, cedula, telefono, direccion, dia_pago, modalidad_pago, estado FROM clientes WHERE nombre LIKE ? OR cedula LIKE ?", (f"%{busqueda}%", f"%{busqueda}%"))
        else:
            cursor.execute("SELECT id_cliente, nombre, cedula, telefono, direccion, dia_pago, modalidad_pago, estado FROM clientes")
        
        resultados = cursor.fetchall()
        conn.close()
        
        if resultados:
            for r in resultados:
                id_clie, nombre_clie, cedula_clie, telf_clie, dir_clie, dia_clie, mod_clie, est_clie = r
                
                with st.expander(f"👤 {nombre_clie} - Cédula: {cedula_clie}"):
                    # Si es Administrador (Anthonny), muestra formulario para editar o borrar
                    if st.session_state["rol"] == "admin":
                        st.markdown("📝 **Modo Administrador: Puedes modificar o eliminar este registro**")
                        
                        with st.form(f"form_edit_{id_clie}"):
                            nuevo_nombre = st.text_input("Nombre:", value=nombre_clie)
                            nueva_cedula = st.text_input("Cédula:", value=cedula_clie)
                            nuevo_telf = st.text_input("Teléfono:", value=telf_clie)
                            nueva_dir = st.text_input("Dirección:", value=dir_clie)
                            nuevo_dia = st.selectbox("Día de Cobro:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"], index=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"].index(dia_clie))
                            nueva_mod = st.selectbox("Modalidad:", ["Semanal", "Quincenal", "Mensual"], index=["Semanal", "Quincenal", "Mensual"].index(mod_clie))
                            nuevo_est = st.selectbox("Estado del Perfil:", ["Activo", "Inactivo"], index=["Activo", "Inactivo"].index(est_clie))
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                btn_actualizar = st.form_submit_button("💾 Guardar Cambios")
                            with col_btn2:
                                btn_eliminar = st.form_submit_button("🚨 Eliminar Cliente")
                            
                            if btn_actualizar:
                                conn = conectar_bd()
                                cursor = conn.cursor()
                                try:
                                    cursor.execute("""
                                        UPDATE clientes 
                                        SET nombre=?, cedula=?, telefono=?, direccion=?, dia_pago=?, modalidad_pago=?, estado=?
                                        WHERE id_cliente=?
                                    """, (nuevo_nombre, nueva_cedula, nuevo_telf, nueva_dir, nuevo_dia, nueva_mod, nuevo_est, id_clie))
                                    conn.commit()
                                    st.success(f"¡Datos de {nuevo_nombre} actualizados con éxito!")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("Error: Esa cédula ya pertenece a otro cliente.")
                                conn.close()
                                
                            if btn_eliminar:
                                conn = conectar_bd()
                                cursor = conn.cursor()
                                # Borramos también sus contratos vinculados para no dejar basura en la base de datos
                                cursor.execute("DELETE FROM contratos WHERE id_cliente=?", (id_clie,))
                                cursor.execute("DELETE FROM clientes WHERE id_cliente=?", (id_clie,))
                                conn.commit()
                                conn.close()
                                st.warning(f"El cliente {nombre_clie} y sus contratos han sido eliminados del sistema.")
                                st.rerun()
                    
                    # Si es Socio (Luis Ángel), solo lee la información estática sin botones
                    else:
                        st.write(f"**Teléfono:** {telf_clie}")
                        st.write(f"**Dirección:** {dir_clie}")
                        st.write(f"**Día de cobro fijo:** {dia_clie}")
                        st.write(f"**Modalidad de pago:** {mod_clie}")
                        st.write(f"**Estado del perfil:** {est_clie}")
        else:
            st.warning("No se encontraron clientes registrados con esos datos.")

    # ==========================================
    # 2. PANTALLA: CARTERA Y DEUDAS
    # ==========================================
    elif opcion == "📋 Cartera y Deudas":
        st.header("📋 Lista de Clientes, Modalidades y Saldos Pendientes")
        
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cl.nombre, co.tipo, co.monto_inicial, co.saldo_pendiente, cl.estado
            FROM clientes cl
            LEFT JOIN contratos co ON cl.id_cliente = co.id_cliente
            WHERE co.estado = 'Activo' OR co.estado IS NULL
            ORDER BY co.saldo_pendiente DESC
        """)
        cartera = cursor.fetchall()
        conn.close()
        
        if not cartera:
            st.info("No hay deudas ni contratos activos registrados en el sistema.")
        else:
            datos_tabla = []
            for item in cartera:
                nombre_c, tipo_c, inicial_c, pendiente_c, estado_c = item
                modalidad_visual = tipo_c if tipo_c else "Sin contrato activo"
                saldo_visual = f"${pendiente_c:,.2f}" if pendiente_c else "$0.00"
                
                datos_tabla.append({
                    "Cliente": nombre_c,
                    "Modalidad": modalidad_visual,
                    "Deuda Actual": saldo_visual
                })
            st.table(datos_tabla)

    # ==========================================
    # 3. PANTALLA: PANEL FINANCIERO (SOLO ADMIN)
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

        cursor.execute("SELECT monto_inicial, saldo_pendiente, tasa_interes, tipo FROM contratos WHERE estado = 'Activo'")
        contratos_activos = cursor.fetchall()
        
        cursor.execute("SELECT SUM(mora_cobrada) FROM pagos")
        total_moras = cursor.fetchone()[0] or 0.0
        conn.close()
        
        dinero_en_calle = sum(c[1] for c in contratos_activos)
        capital_disponible_caja = capital_total - dinero_en_calle
        
        ganancias_proyectadas = 0
        for c in contratos_activos:
            if c[3] == "Redito":
                ganancias_proyectadas += c[1] * (c[2] / 100)
            else:
                ganancias_proyectadas += c[0] * (c[2] / 100)

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        
        col1.metric("Capital Total", f"${capital_total:,.2f}")
        col2.metric("Dinero en Calle (Saldos)", f"${dinero_en_calle:,.2f}")
        col3.metric("Disponible en Caja", f"${capital_disponible_caja:,.2f}")
        col4.metric("Ganancia Estimada de Cartera", f"${ganancias_proyectadas:,.2f}")
        st.metric("Ingresos Extras por Mora", f"${total_moras:,.2f}")

    # ==========================================
    # 4. PANTALLA: REGISTRAR CLIENTE
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
    # 5. PANTALLA: CREAR PRÉSTAMO / SAN
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
            
            tipo_contrato = st.selectbox("Modalidad:", ["San Frio", "San Caliente", "Redito"])
            monto = st.number_input("Monto entregado ($):", min_value=1.0, step=500.0)
            
            tasa_defecto = 10.0 if tipo_contrato == "Redito" else 20.0
            tasa = st.number_input("Tasa de interés (%):", min_value=0.0, value=tasa_defecto, step=1.0)
            
            turno_san = 0
            if "San" in tipo_contrato:
                turno_san = st.number_input("Asignar Número de Turno/Cobro para el San:", min_value=1, value=1, step=1)
            
            if st.button("Activar Contrato"):
                id_clie = opciones_clientes[cliente_seleccionado]
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO contratos (id_cliente, tipo, monto_inicial, saldo_pendiente, tasa_interes, turno_san)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_clie, tipo_contrato, monto, monto, tasa, turno_san))
                conn.commit()
                conn.close()
                st.success(f"¡Contrato de {tipo_contrato} activado con éxito!")

    # ==========================================
    # 6. PANTALLA: REGISTRAR COBRO / PAGO
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
            dic_contratos = {f"{c[1]} ({c[2]} - Debe: ${c[3]:,.2f})": c for c in contratos_pendientes}
            seleccion = st.selectbox("Selecciona el préstamo a cobrar:", list(dic_contratos.keys()))
            
            contrato_data = dic_contratos[seleccion]
            id_contrato, nombre_clie, tipo, saldo_actual, tasa_int, cedula_clie, telefono_clie, direccion_clie = contrato_data
            
            st.markdown("---")
            
            if "San" in tipo:
                st.info(f"📋 **Modalidad: {tipo}**")
                monto_pagando = st.number_input("Monto Total que está pagando en esta cuota ($):", min_value=0.0, max_value=float(saldo_actual), step=100.0)
                mora_cobrada = st.number_input("Agregar cargo de Mora / Penalidad ($):", min_value=0.0, value=0.0, step=50.0)
                abono_capital_efectivo = monto_pagando
                pago_redito_efectivo = 0
            else:
                st.info("📋 **Modalidad: Rédito**")
                pago_redito_efectivo = st.number_input("Monto que está pagando únicamente por concepto de Rédito / Interés ($):", min_value=0.0, step=100.0)
                abono_capital_efectivo = st.number_input("Monto extra que está abonando directo al Capital para bajarlo ($):", min_value=0.0, max_value=float(saldo_actual), step=100.0)
                mora_cobrada = st.number_input("Agregar cargo de Mora / Penalidad ($):", min_value=0.0, value=0.0, step=50.0)
            
            if st.button("Procesar Cobro e Historial"):
                conn = conectar_bd()
                cursor = conn.cursor()
                nuevo_saldo = round(saldo_actual - abono_capital_efectivo, 2)
                fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
                
                cursor.execute("""
                    INSERT INTO pagos (id_contrato, abono_capital, mora_cobrada, fecha) 
                    VALUES (?, ?, ?, ?)
                """, (id_contrato, abono_capital_efectivo, mora_cobrada, fecha_hoy))
                
                if nuevo_saldo <= 0:
                    cursor.execute("UPDATE contratos SET saldo_pendiente = 0, estado = 'Inactivo' WHERE id_contrato = ?", (id_contrato,))
                    st.success(f"¡El cliente {nombre_clie} ha saldado su cuenta!")
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
*Balance Pendiente:* ${nuevo_saldo:YEah,.2f}
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
*Abono a Capital:* ${abono_capital_efectivo:,.2f}
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