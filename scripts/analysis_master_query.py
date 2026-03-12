#!/usr/bin/env python3
"""
Script de análisis estadístico simplificado del CSV generado por master_query.
Solo análisis relevantes:
- Estadísticas básicas
- Correlaciones
- Distribuciones
- Series temporales
- Análisis por mes (único análisis temporal relevante)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# Configuración de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# Rutas
BASE_DIR = Path(__file__).parent.parent
CSV_FILE = BASE_DIR / "data" / "gold" / "master_query_result.csv"
OUTPUT_DIR = BASE_DIR / "reports" / "master_query_analysis"

def setup_output_directory():
    """Crea el directorio de salida si no existe."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Directorio de salida configurado: {OUTPUT_DIR}")

def load_data():
    """Carga el CSV generado por master_query."""
    if not CSV_FILE.exists():
        print(f"✗ Error: Archivo no encontrado: {CSV_FILE}")
        print("  Ejecuta primero: python scripts/run_master_query.py")
        sys.exit(1)
    
    print(f"\nCargando datos de: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    df['datetime'] = pd.to_datetime(df['datetime'])
    print(f"✓ Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
    
    return df

def generate_basic_statistics(df):
    """Genera estadísticas básicas del dataset."""
    print("\n" + "="*60)
    print("ESTADÍSTICAS BÁSICAS")
    print("="*60)
    
    # Seleccionar columnas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # Estadísticas
    stats = df[numeric_cols].describe()
    print("\nResumen estadístico:")
    print(stats)
    
    # Guardar en CSV
    stats_file = OUTPUT_DIR / "estadisticas_basicas.csv"
    stats.to_csv(stats_file)
    print(f"\n✓ Estadísticas guardadas en: {stats_file}")
    
    # Información general
    info_text = f"""
INFORMACIÓN DEL DATASET
=======================
Total de filas: {len(df)}
Período: {df['datetime'].min()} a {df['datetime'].max()}
Rango de tiempo: {(df['datetime'].max() - df['datetime'].min()).days} días

COLUMNAS POR TIPO:
- Fechas/Tiempo: {', '.join([col for col in df.columns if 'datetime' in col or col in ['dia_semana', 'mes', 'hora']])}
- Numéricas: {len(numeric_cols)} columnas
- Categóricas: {', '.join(df.select_dtypes(include=['object']).columns.tolist())}

VALORES FALTANTES:
{df.isnull().sum()}
"""
    
    info_file = OUTPUT_DIR / "informacion_dataset.txt"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(info_text)
    
    print(f"✓ Información del dataset guardada en: {info_file}")

def generate_correlations(df):
    """Genera matriz de correlaciones y su visualización."""
    print("\n" + "="*60)
    print("ANÁLISIS DE CORRELACIONES")
    print("="*60)
    
    # Seleccionar columnas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        print("Insuficientes columnas numéricas para análisis de correlación")
        return
    
    # Calcular correlación
    corr_matrix = df[numeric_cols].corr()
    
    # Guardar matriz de correlación
    corr_file = OUTPUT_DIR / "matriz_correlaciones.csv"
    corr_matrix.to_csv(corr_file)
    print(f"✓ Matriz de correlaciones guardada en: {corr_file}")
    
    # Crear gráfico de heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                center=0, square=True, cbar_kws={"shrink": 0.8})
    plt.title("Matriz de Correlaciones - Variables Numéricas", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    corr_plot = OUTPUT_DIR / "correlaciones_heatmap.png"
    plt.savefig(corr_plot, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Gráfico de correlaciones guardado en: {corr_plot}")

def generate_distributions(df):
    """Genera gráficos de distribuciones de variables numéricas."""
    print("\n" + "="*60)
    print("ANÁLISIS DE DISTRIBUCIONES")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        print("No hay columnas numéricas para analizar")
        return
    
    # Crear subplot con distribuciones
    n_cols = len(numeric_cols)
    n_rows = (n_cols + 2) // 3
    
    fig, axes = plt.subplots(n_rows, 3, figsize=(16, 4*n_rows))
    axes = axes.flatten()
    
    for idx, col in enumerate(numeric_cols):
        data = df[col].dropna()
        if len(data) > 0:
            axes[idx].hist(data, bins=50, edgecolor='black', alpha=0.7)
            axes[idx].set_title(f"Distribución de {col}", fontweight='bold')
            axes[idx].set_xlabel(col)
            axes[idx].set_ylabel("Frecuencia")
    
    # Eliminar subplots vacíos
    for idx in range(len(numeric_cols), len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    dist_plot = OUTPUT_DIR / "distribuciones.png"
    plt.savefig(dist_plot, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Gráfico de distribuciones guardado en: {dist_plot}")

def generate_timeseries_analysis(df):
    """Genera gráficos de series temporales."""
    print("\n" + "="*60)
    print("ANÁLISIS DE SERIES TEMPORALES")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Seleccionar las principales (temperatura, humedad, etc.)
    important_cols = [col for col in numeric_cols if any(
        x in col.lower() for x in ['temperatura', 'humedad', 'presion']
    )]
    
    if important_cols:
        fig, axes = plt.subplots(len(important_cols), 1, figsize=(16, 4*len(important_cols)))
        
        if len(important_cols) == 1:
            axes = [axes]
        
        for idx, col in enumerate(important_cols):
            axes[idx].plot(df['datetime'], df[col], alpha=0.7, linewidth=0.8)
            axes[idx].set_title(f"Serie Temporal: {col}", fontweight='bold')
            axes[idx].set_xlabel("Fecha")
            axes[idx].set_ylabel(col)
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        ts_plot = OUTPUT_DIR / "series_temporales.png"
        plt.savefig(ts_plot, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Gráfico de series temporales guardado en: {ts_plot}")

def generate_month_analysis(df):
    """Genera análisis por mes (el único análisis temporal que tiene sentido)."""
    print("\n" + "="*60)
    print("ANÁLISIS POR MES")
    print("="*60)
    
    if 'mes' not in df.columns:
        print("Columna 'mes' no encontrada")
        return
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Orden de meses
    meses_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    df['mes'] = pd.Categorical(df['mes'], categories=meses_orden, ordered=True)
    
    # Gráfico de línea por mes
    temp_cols = [col for col in numeric_cols if 'temperatura' in col.lower()][:2]
    
    if temp_cols:
        fig, axes = plt.subplots(1, len(temp_cols), figsize=(14, 5))
        
        if len(temp_cols) == 1:
            axes = [axes]
        
        for idx, col in enumerate(temp_cols):
            month_mean = df.groupby('mes', observed=True)[col].mean()
            axes[idx].plot(range(len(month_mean)), month_mean.values, marker='o', linewidth=2)
            axes[idx].set_title(f"{col} Promedio por Mes", fontweight='bold')
            axes[idx].set_xlabel("Mes")
            axes[idx].set_ylabel(col)
            axes[idx].set_xticks(range(len(month_mean)))
            axes[idx].set_xticklabels([m[:3] for m in month_mean.index], rotation=45)
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        month_plot = OUTPUT_DIR / "analisis_por_mes.png"
        plt.savefig(month_plot, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Gráfico de análisis por mes guardado en: {month_plot}")
    
    # Estadísticas por mes
    month_stats = df.groupby('mes', observed=True)[numeric_cols].mean()
    month_stats_file = OUTPUT_DIR / "estadisticas_por_mes.csv"
    month_stats.to_csv(month_stats_file)
    print(f"✓ Estadísticas por mes guardadas en: {month_stats_file}")

def generate_summary_report(df):
    """Genera un reporte de resumen en texto."""
    print("\n" + "="*60)
    print("GENERANDO REPORTE DE RESUMEN")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    report = f"""
╔════════════════════════════════════════════════════════════════╗
║           REPORTE DE ANÁLISIS - MASTER QUERY                  ║
╚════════════════════════════════════════════════════════════════╝

1. INFORMACIÓN GENERAL
═══════════════════════════════════════════════════════════════
Total de registros: {len(df):,}
Período: {df['datetime'].min().strftime('%Y-%m-%d %H:%M')} a {df['datetime'].max().strftime('%Y-%m-%d %H:%M')}
Duración: {(df['datetime'].max() - df['datetime'].min()).days} días

2. CALIDAD DE DATOS
═══════════════════════════════════════════════════════════════
Registros sin valores faltantes: {len(df.dropna()):,} ({len(df.dropna())/len(df)*100:.1f}%)
Registros con valores faltantes: {len(df[df.isnull().any(axis=1)]):,} ({len(df[df.isnull().any(axis=1)])/len(df)*100:.1f}%)

Valores faltantes por columna:
"""
    
    for col in df.columns:
        missing = df[col].isnull().sum()
        if missing > 0:
            report += f"  - {col}: {missing} ({missing/len(df)*100:.1f}%)\n"
    
    report += f"""

3. VARIABLES NUMÉRICAS
═══════════════════════════════════════════════════════════════
"""
    
    for col in numeric_cols[:5]:  # Primeras 5
        report += f"""
  {col}:
    Mín:  {df[col].min():.2f}
    Máx:  {df[col].max():.2f}
    Media: {df[col].mean():.2f}
    Desv.Est: {df[col].std():.2f}
"""
    
    report += f"""

4. ANÁLISIS GENERADOS (VERSIÓN SIMPLIFICADA)
═══════════════════════════════════════════════════════════════
✓ estadisticas_basicas.csv
✓ informacion_dataset.txt
✓ matriz_correlaciones.csv
✓ correlaciones_heatmap.png
✓ distribuciones.png
✓ series_temporales.png
✓ analisis_por_mes.png
✓ estadisticas_por_mes.csv
✓ reporte_resumen.txt

NOTA: Se analiza solo por mes porque es el análisis temporal más relevante.
Los análisis por hora y día de semana no incluyen el contexto temporal
suficiente (varían según la época del año y el día específico).

Todos los archivos se encuentran en: {OUTPUT_DIR}
"""
    
    report_file = OUTPUT_DIR / "reporte_resumen.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n✓ Reporte guardado en: {report_file}")

def main():
    print("="*60)
    print("ANÁLISIS DE MASTER QUERY - CSV (VERSIÓN SIMPLIFICADA)")
    print("="*60)
    
    # Configuración
    setup_output_directory()
    
    # Cargar datos
    df = load_data()
    
    # Generar análisis simplificados
    generate_basic_statistics(df)
    generate_correlations(df)
    generate_distributions(df)
    generate_timeseries_analysis(df)
    generate_month_analysis(df)
    generate_summary_report(df)
    
    print("\n" + "="*60)
    print("✓ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*60)
    print(f"\nTodos los archivos están en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

