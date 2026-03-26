# Flujo Completo: Extracción, Procesamiento y Análisis de Master Query

## 📋 Descripción General

Este proyecto implementa un flujo completo de análisis de datos domoticos:

1. **Extracción**: Ejecutar una consulta SQL y guardar en CSV
2. **Procesamiento**: Agregar columnas derivadas (día, mes, hora)
3. **Análisis**: Generar estadísticas, gráficos y reportes

---

## 🚀 Paso 1: Ejecutar Master Query

Genera el CSV con los datos de la consulta SQL.

### Comando
```powershell
python scripts/run_master_query.py
```

O desde PowerShell:
```powershell
.\scripts\run_master_query.ps1
```

### Salida
- **Ubicación**: `data/gold/master_query_result.csv`
- **Columnas generadas automáticamente**:
  - `datetime` - Marca de tiempo
  - `dia_semana` - Día de la semana
  - `mes` - Nombre del mes
  - `hora` - Hora del día (0-23)
  - Resto de variables del sensor

### Ejemplo
```
datetime              | dia_semana | mes       | hora | temperatura_exterior | ...
2024-12-18 16:00:00   | Miércoles  | Diciembre | 16   | (valores)            | ...
2024-12-18 17:00:00   | Miércoles  | Diciembre | 17   | (valores)            | ...
```

---

## 📊 Paso 2: Ejecutar Análisis

Realiza un análisis **simplificado y relevante** del CSV generado.

### ✨ Cambios en la versión simplificada

Se eliminaron los análisis por **hora** y por **día de semana** porque:
- ❌ No tienen contexto temporal suficiente
- ❌ Varían según la época del año (invierno/verano)
- ✅ Solo el **análisis por mes** ofrece información consistente y significativa

### Comando
```powershell
python scripts/analysis_master_query.py
```

O desde PowerShell:
```powershell
.\scripts\analysis_master_query.ps1
```

### Salida
Todos los archivos se guardan en: `reports/master_query_analysis/`

#### 📈 Gráficos (PNG)
1. **correlaciones_heatmap.png** - Matriz de correlaciones
2. **distribuciones.png** - Histogramas de variables
3. **series_temporales.png** - Evolución temporal
4. **analisis_por_mes.png** - Variaciones mensuales (único análisis temporal relevante)

#### 📈 Datos (CSV)
1. **estadisticas_basicas.csv** - Resumen estadístico completo
2. **matriz_correlaciones.csv** - Correlaciones entre variables
3. **estadisticas_por_mes.csv** - Medias por mes

#### 📄 Reportes (TXT)
1. **reporte_resumen.txt** - Resumen ejecutivo
2. **informacion_dataset.txt** - Información del dataset

---

## 🔄 Flujo Automático

Para ejecutar todo en secuencia:

```powershell
# 1. Generar CSV desde base de datos
python scripts/run_master_query.py

# 2. Analizar el CSV
python scripts/analysis_master_query.py
```

O crear un archivo batch `run_all.bat`:

```batch
@echo off
echo Paso 1: Generando CSV...
python scripts/run_master_query.py
echo.
echo Paso 2: Analizando datos...
python scripts/analysis_master_query.py
echo.
echo ¡Listo!
pause
```

---

## 📊 Qué analiza el script

### 1. Estadísticas Descriptivas
- Mínimo, máximo, media, mediana
- Desviación estándar, percentiles
- Cantidad de valores faltantes

### 2. Correlaciones
- Identifica relaciones entre variables
- Matriz de correlación de Pearson
- Visualización en heatmap

### 3. Distribuciones
- Histogramas de cada variable
- Identifica distribuciones normales o sesgadas
- Detecta outliers

### 4. Series Temporales
- Evolución temporal de temperaturas
- Tendencias a largo plazo
- Patrones de estacionalidad

### 5. Análisis Temporal
- **Por día de semana**: Comportamiento laboral vs fin de semana
- **Por hora**: Variaciones durante el día
- **Por mes**: Cambios estacionales

---

## 💡 Ejemplos de Preguntas que Puedes Responder

Con los análisis generados puedes responder:

- ¿Cuál es la correlación entre temperatura y humedad?
- ¿Hay diferencia de temperatura entre días de semana y fin de semana?
- ¿A qué hora del día es máxima la temperatura?
- ¿Cuál es el mes más frío?
- ¿Qué variables tienen mayor variabilidad?
- ¿Hay patrones horarios en la humedad?

---

## 🛠️ Requisitos

### Dependencias Python
```bash
pip install -r requirements.txt
```

Incluye:
- pandas
- numpy
- matplotlib
- seaborn
- psycopg2-binary
- python-dotenv

### Base de Datos
- PostgreSQL en `localhost:5433`
- Base de datos: `domotica`
- Usuario: `postgres`
- Credenciales en `.env`

---

## 📁 Estructura de Carpetas

```
Proyecto_Domotica/
├── .env                           # Credenciales (no commitear)
├── requirements.txt               # Dependencias Python
├── data/
│   └── gold/
│       └── master_query_result.csv    # CSV generado
├── scripts/
│   ├── run_master_query.py           # 1️⃣ Generar CSV
│   ├── analysis_master_query.py      # 2️⃣ Analizar datos
│   ├── run_master_query.ps1          # Script PowerShell
│   └── analysis_master_query.ps1     # Script PowerShell
└── reports/
    └── master_query_analysis/        # 📊 Resultados del análisis
        ├── README.md
        ├── reporte_resumen.txt
        ├── correlaciones_heatmap.png
        ├── series_temporales.png
        └── [otros archivos...]
```

---

## 🔧 Solución de Problemas

### Error: "Archivo no encontrado"
- Asegúrate de ejecutar el script desde el directorio correcto
- Verifica que exists `data/gold/master_query_result.csv`

### Error: "Columna no encontrada"
- Ejecuta primero `run_master_query.py` para generar el CSV
- Verifica que el CSV tiene las columnas esperadas

### Error: "Módulo no encontrado"
```bash
pip install -r requirements.txt
```

### Gráficos en blanco
- Verifica que haya datos en el CSV
- Comprueba que no todas las columnas sean nulas

---

## 📚 Notas

- Los análisis se regeneran cada vez que ejecutas el script
- Los archivos anteriores se sobrescriben
- El proceso es completamente automatizado
- No requiere intervención manual durante la ejecución

---

## 📞 Contacto

Para preguntas o sugerencias sobre el análisis, revisa los archivos generados:
- `reports/master_query_analysis/README.md` - Documentación detallada
- `reports/master_query_analysis/reporte_resumen.txt` - Resumen de resultados


