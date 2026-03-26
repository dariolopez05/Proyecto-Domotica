#!/usr/bin/env python3
"""
Script para ejecutar master_query.sql y guardar el resultado en CSV.

Este script:
1. Lee la consulta SQL de queries/master_query.sql
2. Se conecta a la base de datos PostgreSQL
3. Ejecuta la consulta
4. Guarda el resultado en CSV en data/gold/
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from pathlib import Path

# Cargar variables de entorno desde .env
BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)

# Configuración
QUERY_FILE = BASE_DIR / "queries" / "master_query.sql"
OUTPUT_DIR = BASE_DIR / "data" / "gold"
OUTPUT_FILE = OUTPUT_DIR / "master_query_result.csv"

# Credenciales de base de datos desde .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "homeassistant"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

def read_query(query_file):
    """Lee la consulta SQL del archivo."""
    if not os.path.exists(query_file):
        raise FileNotFoundError(f"Archivo de consulta no encontrado: {query_file}")
    
    with open(query_file, 'r', encoding='utf-8') as f:
        return f.read()

def execute_query(query, db_config):
    """Ejecuta la consulta en PostgreSQL y devuelve un DataFrame."""
    try:
        conn = psycopg2.connect(**db_config)
        print("✓ Conexión a base de datos establecida")
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        print(f"✓ Consulta ejecutada exitosamente. Filas recuperadas: {len(df)}")
        
        return df
    
    except psycopg2.OperationalError as e:
        print(f"✗ Error de conexión a la base de datos: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error ejecutando la consulta: {e}", file=sys.stderr)
        sys.exit(1)

def save_csv(df, output_file):
    """Guarda el DataFrame en CSV con columnas de día, mes y hora."""
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # Procesar datos
        print("  Procesando datos...")
        
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
        
        print("  ✓ Columnas 'dia_semana', 'mes' y 'hora' añadidas")
        
        # Reordenar columnas: datetime, dia_semana, mes, hora, resto
        otras_columnas = [col for col in df.columns if col not in ['datetime', 'dia_semana', 'mes', 'hora']]
        df = df[['datetime', 'dia_semana', 'mes', 'hora'] + otras_columnas]
        
        print("  ✓ Columnas reordenadas")
        
        # Guardar CSV
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ Archivo guardado exitosamente: {output_file}")
    except Exception as e:
        print(f"✗ Error guardando el archivo CSV: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    print("=" * 60)
    print("Ejecutando master_query.sql")
    print("=" * 60)
    
    # Leer la consulta
    print(f"\n1. Leyendo consulta desde: {QUERY_FILE}")
    query = read_query(QUERY_FILE)
    print("✓ Consulta cargada")
    
    # Ejecutar la consulta
    print(f"\n2. Conectando a base de datos...")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Puerto: {DB_CONFIG['port']}")
    print(f"   Base de datos: {DB_CONFIG['database']}")
    df = execute_query(query, DB_CONFIG)
    
    # Guardar en CSV
    print(f"\n3. Guardando resultado en CSV...")
    save_csv(df, OUTPUT_FILE)
    
    # Resumen
    print(f"\n4. Resumen de datos:")
    print(f"   Filas: {len(df)}")
    print(f"   Columnas: {len(df.columns)}")
    print(f"   Columnas: {', '.join(df.columns.tolist())}")
    
    print("\n" + "=" * 60)
    print("✓ Proceso completado exitosamente")
    print("=" * 60)

if __name__ == "__main__":
    main()

