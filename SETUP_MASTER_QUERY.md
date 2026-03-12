# ✅ Master Query - Configuración completada

## Resumen

Se ha configurado todo lo necesario para ejecutar la consulta `master_query.sql` y guardar el resultado en CSV.

## Archivos creados/modificados

### 1. **`.env`** (Raíz del proyecto)
   - Archivo con las credenciales de conexión a PostgreSQL
   - **IMPORTANTE**: No commitear a git (está en `.gitignore`)
   - Credenciales configuradas:
     ```
     DB_HOST=localhost
     DB_PORT=5433
     DB_NAME=domotica
     DB_USER=postgres
     DB_PASSWORD=admin
     ```

### 2. **`.env.example`** (Raíz del proyecto)
   - Plantilla para facilitar la configuración
   - Puedes copiar este archivo a `.env` y rellenarlo

### 3. **`scripts/run_master_query.py`** ⭐ PRINCIPAL
   - Script Python simplificado
   - Lee las credenciales del `.env`
   - Ejecuta la consulta SQL
   - Guarda el resultado en `data/gold/master_query_result.csv`
   - Uso: `python run_master_query.py`

### 4. **`scripts/run_master_query.ps1`**
   - Script PowerShell para Windows
   - Facilita la ejecución con mejor interfaz
   - Uso: `.\run_master_query.ps1`

### 5. **`scripts/execute_master_query.py`**
   - Versión alternativa con más validaciones
   - Uso: `python execute_master_query.py`

### 6. **`requirements.txt`** (Raíz del proyecto)
   - Dependencias necesarias:
     - pandas>=1.3.0
     - psycopg2-binary>=2.9.0
     - python-dotenv>=0.19.0

### 7. **`.gitignore`** (Raíz del proyecto)
   - Actualizado para ignorar archivos `.env`
   - Protege las credenciales

## Resultado de la ejecución

El script se ha ejecutado exitosamente:
- ✅ Conexión a PostgreSQL: **OK**
- ✅ Consulta ejecutada: **OK**
- ✅ Datos obtenidos: **9.261 filas**
- ✅ CSV guardado: `data/gold/master_query_result.csv` (832 KB)

### Columnas del CSV (en orden):
1. `datetime` - Marca de tiempo (agrupada por hora)
2. `dia_semana` - Día de la semana (Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo)
3. `mes` - Nombre del mes (Enero, Febrero, Marzo, ..., Diciembre)
4. `hora` - Hora del día (0-23)
5. `temperatura_exterior` - Temperatura exterior promedio
6. `humedad_exterior` - Humedad exterior promedio
7. `presion` - Presión atmosférica
8. `nubosidad` - Nubosidad
9. `viento` - Velocidad del viento (moda)
10. `direccion_viento` - Dirección del viento (moda)
11. `azimuth_sol` - Azimut solar
12. `elevacion_sol` - Elevación solar
13. `temperatura_aula` - Temperatura del aula promedio
14. `humedad_aula` - Humedad del aula promedio
15. `forecast` - Pronóstico

## Cómo usar

### Opción 1: PowerShell (Recomendado en Windows)
```powershell
cd scripts
.\run_master_query.ps1
```

### Opción 2: Python directo
```bash
python scripts/run_master_query.py
```

### Opción 3: Versión alternativa
```bash
python scripts/execute_master_query.py
```

## Cambiar credenciales

Si necesitas cambiar las credenciales de conexión:

1. Edita el archivo `.env` en la raíz del proyecto
2. Modifica los valores:
   ```
   DB_HOST=tu_host
   DB_PORT=tu_puerto
   DB_NAME=tu_base_datos
   DB_USER=tu_usuario
   DB_PASSWORD=tu_contraseña
   ```

3. Ejecuta nuevamente el script

## Automatización (Opcional)

Para ejecutar automáticamente el script a intervalos regulares usando Windows Task Scheduler:

1. Abre `taskschd.msc`
2. Crea una nueva tarea
3. En "Acciones" → "Nueva acción":
   - Programa: `powershell.exe`
   - Argumentos: `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\Dario\Desktop\IABD\Proyecto_Domotica\scripts\run_master_query.ps1"`
4. Configura la frecuencia deseada

## Solución de problemas

### Error: "Error de conexión"
- Verifica que PostgreSQL esté corriendo
- Comprueba las credenciales en `.env`
- Verifica que la base de datos existe y es accesible

### Error: "Módulo no encontrado"
- Instala las dependencias: `pip install -r requirements.txt`

### CSV vacío o sin datos
- Verifica que la tabla `ltss` existe en la base de datos
- Comprueba que hay datos disponibles para los `entity_id` especificados

---

✨ **Todo listo para usar!** Ejecuta `python scripts/run_master_query.py` para generar el CSV.



