#!/usr/bin/env python3
"""
Script simplificado para ejecutar master_query.sql directamente.
Lee las credenciales del archivo .env en la raíz del proyecto.
"""

import os
import pandas as pd
import psycopg2
from pathlib import Path
import sys

# Cargar variables de entorno desde .env
BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
else:
    print(f"Advertencia: Archivo .env no encontrado en {ENV_FILE}")
    print("Usando variables de entorno del sistema o valores por defecto")

# Configuración de rutas
QUERY_FILE = BASE_DIR / "queries" / "master_query.sql"
OUTPUT_DIR = BASE_DIR / "data" / "gold"
OUTPUT_FILE = OUTPUT_DIR / "master_query_result.csv"

# Leer credenciales de .env o variables de entorno
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "homeassistant")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def main():
    try:
        # Leer consulta
        if not QUERY_FILE.exists():
            print(f"Error: Archivo no encontrado: {QUERY_FILE}")
            return False
        
        with open(QUERY_FILE, 'r', encoding='utf-8') as f:
            query = f.read()
        
        print(f"Conectando a PostgreSQL en {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        
        # Conectar a base de datos
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        # Ejecutar consulta
        print("Ejecutando consulta...")
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"Consulta completada: {len(df)} filas obtenidas")
        
        # Procesar datos
        print("\nProcesando datos...")
        
        # Convertir datetime a tipo datetime de pandas (con manejo de timezone)
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        # Convertir a datetime sin timezone para extraer información
        df['datetime'] = df['datetime'].dt.tz_localize(None)
        
        # Extraer día de la semana (nombre en español)
        dias_semana = {
            0: 'Lunes',
            1: 'Martes',
            2: 'Miércoles',
            3: 'Jueves',
            4: 'Viernes',
            5: 'Sábado',
            6: 'Domingo'
        }
        df['dia_semana'] = df['datetime'].dt.dayofweek.map(dias_semana)
        
        # Extraer nombre del mes (en español)
        meses = {
            1: 'Enero',
            2: 'Febrero',
            3: 'Marzo',
            4: 'Abril',
            5: 'Mayo',
            6: 'Junio',
            7: 'Julio',
            8: 'Agosto',
            9: 'Septiembre',
            10: 'Octubre',
            11: 'Noviembre',
            12: 'Diciembre'
        }
        df['mes'] = df['datetime'].dt.month.map(meses)
        
        # Extraer hora
        df['hora'] = df['datetime'].dt.hour
        
        print("✓ Columnas 'dia_semana', 'mes' y 'hora' añadidas")
        
        # Reordenar columnas: datetime, dia_semana, mes, hora, resto
        otras_columnas = [col for col in df.columns if col not in ['datetime', 'dia_semana', 'mes', 'hora']]
        df = df[['datetime', 'dia_semana', 'mes', 'hora'] + otras_columnas]
        
        print("✓ Columnas reordenadas")
        
        # Crear directorio de salida si no existe
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Guardar CSV
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"✓ CSV guardado en: {OUTPUT_FILE}")
        
        print(f"\nDatos cargados:")
        print(f"  Columnas: {', '.join(df.columns.tolist())}")
        print(f"  Filas: {len(df)}")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"Error de conexión: {e}")
        print("\nAsegúrate de que PostgreSQL está corriendo y que las credenciales son correctas.")
        print("Puedes configurar las variables de entorno:")
        print("  - DB_HOST (defecto: localhost)")
        print("  - DB_PORT (defecto: 5432)")
        print("  - DB_NAME (defecto: homeassistant)")
        print("  - DB_USER (defecto: postgres)")
        print("  - DB_PASSWORD (defecto: vacío)")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

