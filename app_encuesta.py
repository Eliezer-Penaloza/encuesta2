import streamlit as st
import psycopg2
import pandas as pd
import re
from datetime import datetime

# =========================================================
# CONFIGURACIÓN EXACTA PARA TU SUPABASE
# =========================================================
DB_CONFIG = {
    "host": "aws-1-eu-central-1.pooler.supabase.com",  # ✅ HOST CORRECTO
    "database": "postgres",
    "user": "postgres.pojscrfmlhsawsssnuvp",           # ✅ USUARIO CORRECTO  
    "password": st.secrets["SUPABASE_PASSWORD"],       # ✅ DE SECRETS
    "port": 6543,                                      # ✅ TRANSACTION POOLER
    "connect_timeout": 10
}

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.test_connection()
    
    def test_connection(self):
        """Prueba la conexión con la configuración exacta"""
        try:
            conn = psycopg2.connect(**self.config)
            cursor = conn.cursor()
            
            # Probar consulta
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Obtener información de la base de datos
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            
            st.success("""
            ✅ **¡CONEXIÓN EXITOSA A SUPABASE!**
            
            **Detalles de conexión:**
            - **Tipo:** Transaction Pooler
            - **Base de datos:** postgres
            - **Usuario:** postgres.pojscrfmlhsawsssnuvp
            - **Host:** aws-1-eu-central-1.pooler.supabase.com
            """)
            
            # Crear tabla
            self.create_table(conn)
            
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError as e:
            st.error(f"❌ Error de conexión: {e}")
            self.try_session_pooler()
        except Exception as e:
            st.error(f"❌ Error inesperado: {e}")
    
    def try_session_pooler(self):
        """Intenta con Session Pooler si Transaction falla"""
        st.info("🔄 Intentando con Session Pooler...")
        
        session_config = self.config.copy()
        session_config["port"] = 5432  # Puerto de Session Pooler
        
        try:
            conn = psycopg2.connect(**session_config)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            
            st.success("""
            ✅ **¡CONEXIÓN EXITOSA VIA SESSION POOLER!**
            
            **Detalles de conexión:**
            - **Tipo:** Session Pooler  
            - **Puerto:** 5432
            - **Host:** aws-1-eu-central-1.pooler.supabase.com
            """)
            
            self.create_table(conn)
            self.config = session_config  # Usar esta configuración
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Session Pooler también falló: {e}")
            st.stop()
    
    def get_connection(self):
        return psycopg2.connect(**self.config)
    
    def create_table(self, conn):
        cursor = conn.cursor()
        
        # Verificar si la tabla ya existe
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'encuestas_calidad'
        );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            create_table_query = """
            CREATE TABLE encuestas_calidad (
                id SERIAL PRIMARY KEY,
                cedula VARCHAR(20) NOT NULL,
                fue_atendido VARCHAR(5) NOT NULL,
                tiempo_atencion VARCHAR(20) NOT NULL,
                calidad_servicio VARCHAR(20) NOT NULL,
                sugerencias TEXT,
                fecha_encuesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cedula)
            );
            """
            cursor.execute(create_table_query)
            conn.commit()
            st.success("✅ Tabla 'encuestas_calidad' creada exitosamente")
        else:
            st.success("✅ Tabla 'encuestas_calidad' ya existe")
        
        cursor.close()

    def insert_encuesta(self, cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO encuestas_calidad (cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cedula) 
            DO UPDATE SET 
                fue_atendido = EXCLUDED.fue_atendido,
                tiempo_atencion = EXCLUDED.tiempo_atencion,
                calidad_servicio = EXCLUDED.calidad_servicio,
                sugerencias = EXCLUDED.sugerencias,
                fecha_encuesta = CURRENT_TIMESTAMP
            RETURNING id;
            """
            
            cursor.execute(insert_query, (cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias))
            encuesta_id = cursor.fetchone()[0]
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True, f"Encuesta guardada (ID: {encuesta_id})"
            
        except Exception as e:
            return False, f"Error: {e}"

# Resto del código...
def validate_cedula(cedula):
    cedula = cedula.strip().upper()
    pattern = r'^[VE]-\d{7,8}$'
    if not re.match(pattern, cedula):
        return False, "Formato inválido. Use: V-12345678 o E-12345678"
    digitos = cedula[2:]
    if not digitos.isdigit():
        return False, "Los dígitos después del guión deben ser números"
    return True, "Cédula válida"

def show_success_message(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias, mensaje):
    st.balloons()
    st.success(f"""
    ✅ **¡ENCUESTA GUARDADA EXITOSAMENTE!**
    
    **Detalles:**
    - **Cédula:** {cedula}
    - **¿Fue atendido?:** {fue_atendido}
    - **Tiempo de atención:** {tiempo_atencion} 
    - **Calidad del servicio:** {calidad_servicio}
    - **Sugerencias:** {sugerencias if sugerencias else 'Ninguna'}
    - **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
    - **Estado:** {mensaje}
    """)

def main():
    st.set_page_config(
        page_title="Encuesta de Calidad - FASMEE", 
        page_icon="🏥",
        layout="centered"
    )
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/1006/1006555.png", width=80)
        st.title("🏥 Encuesta de Calidad")
        st.markdown("### FASMEE - Sistema de Satisfacción del Paciente")
        st.markdown("**Base de datos: Supabase** ☁️")
    
    st.markdown("---")
    
    # Inicializar conexión
    db_manager = DatabaseManager(DB_CONFIG)
    
    # Formulario
    with st.form("encuesta_form", clear_on_submit=True):
        st.subheader("📝 Datos de Identificación")
        
        cedula = st.text_input(
            "**Cédula de Identidad** (*requerido*)",
            placeholder="Ej: V-12345678",
            help="Ingrese su cédula en el formato correcto",
            max_chars=11
        ).upper()
        
        # Validación en tiempo real
        if cedula:
            es_valida, mensaje = validate_cedula(cedula)
            if es_valida:
                st.success(f"✅ {mensaje}")
            else:
                st.error(f"❌ {mensaje}")
        
        st.markdown("---")
        st.subheader("❓ Preguntas de la Encuesta")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fue_atendido = st.radio(
                "**1. ¿Fue atendido?** (*requerido*)",
                options=["Sí", "No"],
                help="Indique si recibió atención médica"
            )
            
            tiempo_atencion = st.selectbox(
                "**2. ¿Tiempo de atención?** (*requerido*)",
                options=["Un día", "Una semana", "Un mes", "Más"],
                help="Tiempo que tomó para ser atendido"
            )
        
        with col2:
            calidad_servicio = st.selectbox(
                "**3. ¿Cómo evalúa la calidad del servicio?** (*requerido*)",
                options=["Excelente", "Buena", "Regular", "Mala"],
                help="Calidad general del servicio recibido"
            )
            
            sugerencias = st.text_area(
                "**4. Sugerencias o comentarios** (opcional)",
                placeholder="Escriba sus comentarios, quejas o sugerencias aquí...",
                height=100,
                help="Sus comentarios nos ayudan a mejorar nuestro servicio"
            )
        
        st.markdown("---")
        
        # Botón de envío
        submitted = st.form_submit_button(
            "🚀 Enviar Encuesta a Supabase",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            # Validaciones
            if not cedula:
                st.error("❌ Por favor, ingrese su cédula de identidad")
                return
            
            es_valida, mensaje = validate_cedula(cedula)
            if not es_valida:
                st.error(f"❌ {mensaje}")
                return
            
            # Guardar encuesta
            with st.spinner("💾 Guardando en Supabase..."):
                success, resultado = db_manager.insert_encuesta(
                    cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias
                )
            
            if success:
                show_success_message(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias, resultado)
                
                # Botón para nueva encuesta
                if st.button("📋 Realizar Otra Encuesta", use_container_width=True):
                    st.rerun()
            else:
                st.error(f"❌ {resultado}")
    
    # Footer
    st.markdown("---")
    st.caption("© 2024 FASMEE - Sistema de Encuestas de Calidad")
    st.caption("*Datos almacenados de forma segura en Supabase*")

if __name__ == "__main__":
    main()
