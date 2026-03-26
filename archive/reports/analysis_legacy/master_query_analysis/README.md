# Análisis de Master Query (Versión Simplificada)

Este directorio contiene los resultados del análisis estadístico simplificado del CSV generado por `master_query.sql`.

## ¿Por qué versión simplificada?

Se eliminaron los análisis por **hora** y por **día de semana** porque:
- No tienen sentido sin contexto temporal suficiente
- El análisis por hora varía según la época del año (invierno vs verano)
- El análisis por día de semana varía según el período específico
- **Solo el análisis por mes** ofrece información relevante y consistente

## Archivos generados

### 📊 Gráficos (PNG) - 5 archivos
- **`correlaciones_heatmap.png`** - Matriz de correlaciones entre variables numéricas
- **`distribuciones.png`** - Histogramas de distribución de cada variable
- **`series_temporales.png`** - Evolución temporal de temperaturas, humedad y presión
- **`analisis_por_mes.png`** - Evolución de variables por mes (relevante y consistente)

### 📈 Datos (CSV) - 4 archivos
- **`estadisticas_basicas.csv`** - Resumen estadístico (mín, máx, media, desv. est., percentiles)
- **`matriz_correlaciones.csv`** - Matriz de correlaciones de Pearson
- **`estadisticas_por_mes.csv`** - Media de variables agrupadas por mes

### 📄 Reportes (TXT) - 2 archivos
- **`informacion_dataset.txt`** - Información general del dataset (tamaño, período, columnas, valores faltantes)
- **`reporte_resumen.txt`** - Reporte completo con resumen ejecutivo

## Cómo generar el análisis

### Opción 1: PowerShell (Recomendado)
```powershell
cd scripts
.\analysis_master_query.ps1
```

### Opción 2: Python directo
```bash
python scripts/analysis_master_query.py
```

## Requisitos

El script utiliza las siguientes librerías (ya incluidas en requirements.txt):
- pandas
- numpy
- matplotlib
- seaborn

Si no tienes seaborn instalada:
```bash
pip install seaborn
```

## Flujo de análisis

1. **Carga de datos** - Lee el CSV desde `data/gold/master_query_result.csv`
2. **Estadísticas básicas** - Calcula métricas descriptivas
3. **Correlaciones** - Identifica relaciones entre variables
4. **Distribuciones** - Visualiza la distribución de cada variable
5. **Series temporales** - Muestra tendencias a lo largo del tiempo
6. **Análisis por mes** - Detecta variaciones mensuales (análisis temporal más relevante)

## Interpretación de resultados

### Matriz de correlaciones
- Valores cercanos a 1 (rojo): Correlación positiva fuerte
- Valores cercanos a 0 (blanco): Sin correlación
- Valores cercanos a -1 (azul): Correlación negativa fuerte

### Distribuciones
- Histogramas simétricos: Distribución normal
- Asimetría: Posible sesgo en los datos
- Múltiples picos: Posible multimodalidad

### Series temporales
- Tendencias: Aumentos/disminuciones sostenidas
- Estacionalidad: Patrones que se repiten
- Anomalías: Picos o caídas anormales

### Análisis por mes
- Diferencias significativas: Cambios estacionales
- Ciclos regulares: Patrones predecibles
- Variabilidad: Grado de consistencia mes a mes

## Notas

- El análisis se regenera cada vez que ejecutas el script
- Los archivos anteriores se sobrescriben
- El proceso es completamente automatizado
- No requiere intervención manual durante la ejecución
- Se prioriza **análisis de calidad sobre cantidad de reportes**


