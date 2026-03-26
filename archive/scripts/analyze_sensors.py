import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuración de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# Rutas
csv_path = r"c:\Users\Dario\Desktop\IABD\Proyecto_Domotica\data\bronze\media-temperaturas.csv"
output_dir = r"c:\Users\Dario\Desktop\IABD\Proyecto_Domotica\reports\sensor_analysis"

# Crear directorio de salida si no existe
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def analyze_sensors():
    print(f"Leyendo datos de: {csv_path}...")
    
    # Cargar datos
    df = pd.read_csv(csv_path)
    
    # Lista de sensores de interés
    target_sensors = [
        'sensor.sensor_temperatura_1_temperature',
        'sensor.sensor_temperatura_2_temperature',
        'sensor.sensor_temperatura_3_temperature',
        'sensor.sensor_temperatura_4_temperature'
    ]
    
    # Filtrar por los sensores solicitados
    df_filtered = df[df['entity_id'].isin(target_sensors)].copy()
    
    # Preprocesamiento
    df_filtered['hora'] = pd.to_datetime(df_filtered['hora'])
    df_filtered['temperatura_media'] = pd.to_numeric(df_filtered['temperatura_media'], errors='coerce')
    
    # Pivotar los datos para tener un sensor por columna
    df_pivot = df_filtered.pivot_table(
        index='hora', 
        columns='entity_id', 
        values='temperatura_media'
    )
    
    # Limpiar nombres de columnas para que sean más cortos
    df_pivot.columns = [col.split('.')[-1].replace('_temperature', '') for col in df_pivot.columns]
    
    print("\nResumen Estadístico:")
    stats = df_pivot.describe()
    print(stats)
    
    # Guardar resumen estadístico
    stats.to_csv(os.path.join(output_dir, "sensor_stats.csv"))
    
    # --- VISUALIZACIONES ---
    
    # 1. Gráfico de Series Temporales
    plt.figure(figsize=(15, 7))
    for col in df_pivot.columns:
        plt.plot(df_pivot.index, df_pivot[col], label=col, alpha=0.7)
    plt.title("Comparativa de Temperaturas a lo largo del Tiempo")
    plt.xlabel("Fecha/Hora")
    plt.ylabel("Temperatura (°C)")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "timeseries_comparison.png"))
    plt.close()
    
    # 2. Matriz de Correlación
    plt.figure(figsize=(10, 8))
    corr = df_pivot.corr()
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".3f", center=1)
    plt.title("Matriz de Correlación entre Sensores")
    plt.savefig(os.path.join(output_dir, "correlation_heatmap.png"))
    plt.close()
    
    # 3. Pairplot (Gráficos de dispersión cruzados)
    plt.figure(figsize=(12, 12))
    g = sns.pairplot(df_pivot.dropna(), kind="reg", diag_kind="kde", plot_kws={'line_kws':{'color':'red'}})
    g.fig.suptitle("Gráficos de Correlación y Distribución Cruzada", y=1.02)
    plt.savefig(os.path.join(output_dir, "pairplot_correlation.png"))
    plt.close()
    
    # 4. Boxplot para ver distribuciones y outliers
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df_pivot)
    plt.title("Distribución de Temperaturas por Sensor")
    plt.ylabel("Temperatura (°C)")
    plt.savefig(os.path.join(output_dir, "boxplot_distribution.png"))
    plt.close()
    
    # 5. Análisis de Residuos (Diferencia respecto a la media de todos)
    df_pivot['media_global'] = df_pivot.mean(axis=1)
    plt.figure(figsize=(15, 7))
    for col in df_pivot.columns:
        if col != 'media_global':
            diff = df_pivot[col] - df_pivot['media_global']
            plt.plot(df_pivot.index, diff, label=f"Desviación {col}", alpha=0.5)
    plt.axhline(y=0, color='black', linestyle='--')
    plt.title("Desviación de cada sensor respecto al promedio global")
    plt.ylabel("Diferencia de Temperatura (°C)")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "deviation_analysis.png"))
    plt.close()
    
    print(f"\nAnálisis completado. Los gráficos y resultados se han guardado en: {output_dir}")
    
    # Recomendación basada en varianza y correlación
    print("\nInterpretación rápida:")
    for col in df_pivot.columns:
        if col == 'media_global': continue
        nas = df_pivot[col].isna().sum()
        if nas > 0:
            print(f"- {col}: Tiene {nas} valores faltantes ({nas/len(df_pivot)*100:.2f}%).")
    
    print("\nSugerencia:")
    print("Busca el sensor con la menor desviación estándar si buscas estabilidad,")
    print("o aquel que más se aproxime a la 'media_global' si buscas representatividad.")

if __name__ == "__main__":
    analyze_sensors()
