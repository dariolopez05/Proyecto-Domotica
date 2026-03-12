# Scripts para Ejecutar Master Query

Este directorio contiene scripts para ejecutar la consulta `master_query.sql` y guardar el resultado en CSV en la carpeta `data/gold`.

## Archivos

- **`run_master_query.py`**: Script Python principal que ejecuta la consulta
- **`run_master_query.ps1`**: Script PowerShell para facilitar la ejecución en Windows
- **`execute_master_query.py`**: Versión alternativa con más opciones de configuración

## Requisitos

### 1. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

O instalar directamente:

```bash
pip install pandas psycopg2-binary python-dotenv
```

### 2. Configurar conexión a PostgreSQL

Las credenciales se configuran en el archivo `.env` en la raíz del proyecto.

**Ya está configurado con tus credenciales:**
- Host: `localhost`
- Puerto: `5433`
- Base de datos: `domotica`
- Usuario: `postgres`
- Contraseña: `admin`

**Si necesitas cambiar las credenciales**, edita el archivo `.env`:

```
DB_HOST=localhost
DB_PORT=5433
DB_NAME=domotica
DB_USER=postgres
DB_PASSWORD=admin
```

> ⚠️ **IMPORTANTE**: El archivo `.env` contiene credenciales y NO debe ser commiteado a git. Está en `.gitignore`.

## Uso

### Opción 1: Ejecutar desde PowerShell (Windows) - RECOMENDADO

```powershell
cd C:\Users\Dario\Desktop\IABD\Proyecto_Domotica\scripts
.\run_master_query.ps1
```

### Opción 2: Ejecutar desde Python directamente

```bash
python run_master_query.py
```

### Opción 3: Usar la versión alternativa con más opciones

```bash
python execute_master_query.py
```

## Output

El script creará un archivo CSV en:

```
data/gold/master_query_result.csv
```

Con las siguientes columnas (en este orden):
- `datetime`: Marca de tiempo (agrupada por hora)
- `dia_semana`: Día de la semana (Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo)
- `mes`: Nombre del mes (Enero, Febrero, Marzo, ..., Diciembre)
- `hora`: Hora del día (0-23)
- `temperatura_exterior`: Temperatura exterior promedio
- `humedad_exterior`: Humedad exterior promedio
- `presion`: Presión atmosférica
- `nubosidad`: Nubosidad
- `viento`: Velocidad del viento (moda)
- `direccion_viento`: Dirección del viento (moda)
- `azimuth_sol`: Azimut solar
- `elevacion_sol`: Elevación solar
- `temperatura_aula`: Temperatura del aula promedio
- `humedad_aula`: Humedad del aula promedio
- `forecast`: Pronóstico

## Solución de problemas

### Error: "Archivo de consulta no encontrado"

Asegúrate de que estés ejecutando el script desde el directorio `scripts/` o que la ruta a `queries/master_query.sql` sea correcta.

### Error: "Error de conexión"

1. Verifica que PostgreSQL esté corriendo
2. Comprueba las credenciales de conexión
3. Verifica que la base de datos existe y es accesible

### Error: "Módulo psycopg2 no encontrado"

Instala las dependencias:

```bash
pip install psycopg2-binary
```

## Automatización (Windows Task Scheduler)

Puedes automatizar la ejecución del script usando Windows Task Scheduler:

1. Abre `taskschd.msc`
2. Crea una nueva tarea
3. En la pestaña "Acciones", añade una acción:
   - Programa: `powershell.exe`
   - Argumentos: `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\Dario\Desktop\IABD\Proyecto_Domotica\scripts\run_master_query.ps1"`
4. Configura la frecuencia deseada






