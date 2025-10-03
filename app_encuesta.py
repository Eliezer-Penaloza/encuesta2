import streamlit as st
import psycopg2
import pandas as pd
import re
from datetime import datetime

# =========================================================
# CONFIGURACIÓN CORREGIDA PARA TRANSACTION POOLER
# =========================================================
try:
    DB_CONFIG = {
        "host": st.secrets["SUPABASE_HOST"],
        "database": st.secrets["SUPABASE_DATABASE"], 
        "user": st.secrets["SUPABASE_USER"],  # ¡Con el nombre del proyecto!
        "password": st.secrets["SUPABASE_PASSWORD"],
        "port": st.secrets["SUPABASE_PORT"],  # ¡Puerto del pooler!
        "connect_timeout": 10
    }
except KeyError as e:
    st.error(f"❌ Falta credencial: {e}")
    st.stop()

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.test_connection()
    
    def test_connection(self):
        """Prueba de conexión con pooler"""
        try:
            conn = psycopg2.connect(**self.config)
            cursor = conn.cursor()
            
            # Probar consulta simple
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            st.success(f"✅ ¡CONECTADO! PostgreSQL: {version[0]}")
            
            # Crear tabla
            self.create_table(conn)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error de conexión: {e}")
            st.info("""
            🔧 **Si aún falla, prueba estas opciones:**
            
            1. **Session Pooler:** Puerto 5432, usuario: postgres.pojscrfmlhsawsssnuvp
            2. **Verifica la contraseña** en Settings > Database
            3. **Espera 5 minutos** - A veces hay latencia inicial
            """)
    
    def get_connection(self):
        return psycopg2.connect(**self.config)
    
    def create_table(self, conn):
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS encuestas_calidad (
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
        cursor.close()
        st.success("✅ Tabla 'encuestas_calidad' lista")

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
                fecha_encuesta = CURRENT_TIMESTAMP;
            """
            
            cursor.execute(insert_query, (cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias))
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
            return False

# Resto del código igual...
def validate_cedula(cedula):
    cedula = cedula.strip().upper()
    pattern = r'^[VE]-\d{7,8}$'
    if not re.match(pattern, cedula):
        return False, "Formato inválido. Use: V-12345678 o E-12345678"
    digitos = cedula[2:]
    if not digitos.isdigit():
        return False, "Los dígitos después del guión deben ser números"
    return True, "Cédula válida"

def main():
    st.set_page_config(page_title="Encuesta - FASMEE", page_icon="🏥")
    
    st.title("🏥 Encuesta de Calidad - FASMEE")
    st.markdown("**Conectado via Transaction Pooler** 🔄")
    st.markdown("---")
    
    # Inicializar conexión
    db_manager = DatabaseManager(DB_CONFIG)
    
    # Formulario
    with st.form("encuesta_form"):
        cedula = st.text_input("**Cédula** (*requerido*)", placeholder="V-12345678", max_chars=11).upper()
        
        if cedula:
            es_valida, msg = validate_cedula(cedula)
            st.success(f"✅ {msg}") if es_valida else st.error(f"❌ {msg}")
        
        col1, col2 = st.columns(2)
        with col1:
            fue_atendido = st.radio("**¿Fue atendido?**", ["Sí", "No"])
            tiempo_atencion = st.selectbox("**Tiempo de atención**", ["Un día", "Una semana", "Un mes", "Más"])
        with col2:
            calidad_servicio = st.selectbox("**Calidad del servicio**", ["Excelente", "Buena", "Regular", "Mala"])
            sugerencias = st.text_area("**Sugerencias** (opcional)", height=80)
        
        if st.form_submit_button("🚀 Enviar Encuesta"):
            if cedula and validate_cedula(cedula)[0]:
                with st.spinner("Guardando en Supabase..."):
                    if db_manager.insert_encuesta(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias):
                        st.success("✅ ¡Encuesta guardada exitosamente!")
                        st.balloons()
            else:
                st.error("❌ Complete todos los campos requeridos")

if __name__ == "__main__":
    main()
