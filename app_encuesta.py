# Cambia el código para forzar IPv4
import streamlit as st
import psycopg2
import pandas as pd
import re
from datetime import datetime

# =========================================================
# CONFIGURACIÓN MEJORADA PARA SUPABASE
# =========================================================
try:
    DB_CONFIG = {
        "host": st.secrets["SUPABASE_HOST"],
        "database": st.secrets["SUPABASE_DATABASE"],
        "user": st.secrets["SUPABASE_USER"],
        "password": st.secrets["SUPABASE_PASSWORD"],
        "port": st.secrets["SUPABASE_PORT"]
    }
except KeyError as e:
    st.error(f"❌ Error: No se encontró la credencial {e}")
    st.stop()

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.test_connection()
    
    def test_connection(self):
        """Prueba la conexión con manejo mejorado de errores"""
        try:
            # Intentar conexión con timeout
            conn = psycopg2.connect(**self.config, connect_timeout=10)
            cursor = conn.cursor()
            
            # Probar consulta simple
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            # Crear tabla si no existe
            self.create_table(conn)
            
            st.success(f"✅ Conectado a Supabase - PostgreSQL {version[0]}")
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError as e:
            st.error(f"❌ Error de conexión: {e}")
            self.show_connection_tips()
        except Exception as e:
            st.error(f"❌ Error inesperado: {e}")
    
    def show_connection_tips(self):
        """Muestra consejos para solucionar problemas de conexión"""
        st.info("""
        🔧 **Posibles soluciones:**
        
        1. **Verifica tu conexión a internet**
        2. **Problema temporal de Supabase** - Espera unos minutos
        3. **Firewall/Red** - Verifica que no bloqueen el puerto 5432
        4. **DNS** - Intenta usar la IP directamente
        
        **Solución rápida:** Espera 5 minutos y reintenta
        """)
        
        # Mostrar información de diagnóstico
        st.write("**Información para diagnóstico:**")
        st.write(f"- Host: {self.config['host']}")
        st.write(f"- Puerto: {self.config['port']}")
        st.write(f"- Usuario: {self.config['user']}")
    
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

def show_success_message(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias):
    success_html = f"""
    <div style="background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; border: 1px solid #c3e6cb;">
        <h3>✅ ¡Encuesta Completada!</h3>
        <p><strong>Cédula:</strong> {cedula}</p>
        <p><strong>¿Fue atendido?:</strong> {fue_atendido}</p>
        <p><strong>Tiempo de atención:</strong> {tiempo_atencion}</p>
        <p><strong>Calidad del servicio:</strong> {calidad_servicio}</p>
        <p><strong>Sugerencias:</strong> {sugerencias if sugerencias else 'Ninguna'}</p>
        <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    """
    st.markdown(success_html, unsafe_allow_html=True)
    st.balloons()

def main():
    st.set_page_config(page_title="Encuesta de Calidad - FASMEE", page_icon="🏥", layout="centered")
    
    st.title("🏥 Encuesta de Calidad - FASMEE")
    st.markdown("---")
    
    # Inicializar base de datos
    db_manager = DatabaseManager(DB_CONFIG)
    
    # Formulario
    with st.form("encuesta_form"):
        st.subheader("📝 Datos de Identificación")
        
        cedula = st.text_input("**Cédula** (*requerido*)", placeholder="V-12345678", max_chars=11).upper()
        
        if cedula:
            es_valida, mensaje = validate_cedula(cedula)
            if es_valida:
                st.success(f"✅ {mensaje}")
            else:
                st.error(f"❌ {mensaje}")
        
        st.subheader("❓ Preguntas de la Encuesta")
        col1, col2 = st.columns(2)
        
        with col1:
            fue_atendido = st.radio("**¿Fue atendido?**", ["Sí", "No"])
            tiempo_atencion = st.selectbox("**Tiempo de atención**", ["Un día", "Una semana", "Un mes", "Más"])
        
        with col2:
            calidad_servicio = st.selectbox("**Calidad del servicio**", ["Excelente", "Buena", "Regular", "Mala"])
            sugerencias = st.text_area("**Sugerencias** (opcional)", placeholder="Sus comentarios...", height=100)
        
        submitted = st.form_submit_button("🚀 Enviar Encuesta")
        
        if submitted:
            if not cedula:
                st.error("❌ Ingrese su cédula")
                return
            
            es_valida, mensaje = validate_cedula(cedula)
            if not es_valida:
                st.error(f"❌ {mensaje}")
                return
            
            with st.spinner("Guardando encuesta..."):
                success = db_manager.insert_encuesta(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias)
            
            if success:
                show_success_message(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias)
                if st.button("📋 Nueva Encuesta"):
                    st.rerun()

if __name__ == "__main__":
    main()
