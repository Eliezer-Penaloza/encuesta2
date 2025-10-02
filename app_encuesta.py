import streamlit as st
import psycopg2
import pandas as pd
import re
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "database": "pacientes_db",
    "user": "postgres",
    "password": "12345678"
}

# Configuración de la página
st.set_page_config(
    page_title="Encuesta de Calidad - FASMEE",
    page_icon="🏥",
    layout="centered"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        margin: 20px 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #f5c6cb;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #bee5eb;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.create_table()
    
    def get_connection(self):
        return psycopg2.connect(**self.config)
    
    def create_table(self):
        try:
            conn = self.get_connection()
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
            
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()
    
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
            return True
            
        except Exception as e:
            st.error(f"Error al insertar encuesta: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                conn.close()

def validate_cedula(cedula):
    """
    Valida el formato de la cédula de manera estricta
    Formatos aceptados: V-1234567, V-12345678, E-12345678
    """
    # Limpiar espacios y convertir a mayúsculas
    cedula = cedula.strip().upper()
    
    # Patrón regex para validación
    pattern = r'^[VE]-\d{7,8}$'
    
    if not re.match(pattern, cedula):
        return False, "Formato inválido. Use: V-12345678 o E-12345678"
    
    # Validar que los dígitos sean números
    digitos = cedula[2:]
    if not digitos.isdigit():
        return False, "Los dígitos después del guión deben ser números"
    
    return True, "Cédula válida"

def show_success_message(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias):
    """Muestra mensaje de éxito con los datos ingresados"""
    success_html = f"""
    <div class="success-box">
        <h3>✅ ¡Encuesta Completada Exitosamente!</h3>
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

def show_cedula_help():
    """Muestra ayuda sobre el formato de cédula"""
    help_html = """
    <div class="info-box">
        <h4>📋 Formato de Cédula Requerido</h4>
        <p><strong>Formatos aceptados:</strong></p>
        <ul>
            <li>V-1234567 (7 dígitos)</li>
            <li>V-12345678 (8 dígitos)</li>
            <li>E-12345678 (8 dígitos)</li>
        </ul>
        <p><strong>Ejemplos válidos:</strong></p>
        <ul>
            <li>V-1234567</li>
            <li>V-12345678</li>
            <li>E-12345678</li>
        </ul>
    </div>
    """
    st.markdown(help_html, unsafe_allow_html=True)

def main():
    # Inicializar base de datos
    db_manager = DatabaseManager(DB_CONFIG)
    
    # Logo y título
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/1006/1006555.png", width=100)
        st.title("🏥 Encuesta de Calidad")
        st.markdown("### FASMEE - Sistema de Satisfacción del Paciente")
        st.markdown("---")
    
    # Mostrar ayuda sobre formato de cédula
    with st.expander("ℹ️ ¿Cómo ingresar mi cédula?", expanded=True):
        show_cedula_help()
    
    # Formulario de encuesta
    with st.form("encuesta_form", clear_on_submit=True):
        st.subheader("📝 Datos de Identificación")
        
        # Campo de cédula con validación en tiempo real
        cedula = st.text_input(
            "**Cédula de Identidad** (*requerido*)",
            placeholder="Ej: V-12345678",
            help="Ingrese su cédula en el formato correcto",
            max_chars=11
        ).upper()
        
        # Validación en tiempo real
        if cedula:
            es_valida, mensaje = validate_cedula(cedula)
            if not es_valida:
                st.error(f"❌ {mensaje}")
            else:
                st.success(f"✅ {mensaje}")
        
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
            "🚀 Enviar Encuesta",
            type="primary",
            use_container_width=True
        )
        
        # Procesar envío del formulario
        if submitted:
            # Validar que todos los campos requeridos estén completos
            if not cedula:
                st.error("❌ Por favor, ingrese su cédula de identidad")
                return
            
            if not fue_atendido or not tiempo_atencion or not calidad_servicio:
                st.error("❌ Por favor, complete todas las preguntas requeridas")
                return
            
            # Validar formato de cédula
            es_valida, mensaje = validate_cedula(cedula)
            if not es_valida:
                st.error(f"❌ Error en cédula: {mensaje}")
                return
            
            # Mostrar spinner de carga
            with st.spinner("⏳ Guardando su encuesta..."):
                # Insertar en base de datos
                success = db_manager.insert_encuesta(
                    cedula, 
                    fue_atendido, 
                    tiempo_atencion, 
                    calidad_servicio, 
                    sugerencias.strip() if sugerencias else None
                )
            
            if success:
                # Mostrar mensaje de éxito
                show_success_message(cedula, fue_atendido, tiempo_atencion, calidad_servicio, sugerencias)
                
                # Botón para nueva encuesta
                if st.button("📋 Realizar Otra Encuesta", use_container_width=True):
                    st.rerun()
            else:
                st.error("❌ Error al guardar la encuesta. Por favor, intente nuevamente.")
    
    # Footer
    st.markdown("---")
    st.caption("© 2024 FASMEE - Sistema de Encuestas de Calidad")
    st.caption("*Todos los datos son confidenciales y se utilizan únicamente para mejorar nuestros servicios*")

if __name__ == "__main__":
    main()
