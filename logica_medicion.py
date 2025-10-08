# logica_medicion.py
import time
import os

NOMBRE_ARCHIVO = 'archivo_grande.txt'
PALABRA_A_BUSCAR = 'memoria'

def _resolver_ruta_archivo(nombre):
    """Devuelve una ruta existente para 'nombre' probando ubicaciones comunes."""
    # 1) Ruta absoluta tal cual
    if os.path.isabs(nombre) and os.path.isfile(nombre):
        return nombre
    # 2) Directorio de trabajo actual
    cwd_path = os.path.join(os.getcwd(), nombre)
    if os.path.isfile(cwd_path):
        return cwd_path
    # 3) Directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, nombre)
    if os.path.isfile(script_path):
        return script_path
    # 4) Directorio padre del script
    parent_path = os.path.join(os.path.dirname(script_dir), nombre)
    if os.path.isfile(parent_path):
        return parent_path
    # No encontrado; devolver tal cual (fallará en validación más adelante)
    return nombre

def _leer_meminfo_mb():
    """Devuelve un dict con métricas clave de /proc/meminfo en MB."""
    try:
        datos = {}
        with open('/proc/meminfo', 'r') as f:
            for linea in f:
                partes = linea.split(':')
                if len(partes) < 2:
                    continue
                k = partes[0].strip()
                v = partes[1].strip().split()[0]
                if v.isdigit():
                    datos[k] = int(v) / 1024.0  # kB -> MB
        return {
            'CachedMB': round(datos.get('Cached', 0.0), 1),
            'BuffersMB': round(datos.get('Buffers', 0.0), 1),
            'DirtyMB': round(datos.get('Dirty', 0.0), 1),
        }
    except Exception:
        return {'CachedMB': -1, 'BuffersMB': -1, 'DirtyMB': -1}

def limpiar_cache():
    """Limpia el caché del sistema de archivos de Linux de forma robusta."""
    try:
        # Sincroniza para asegurar que todo esté escrito en disco
        os.system('sync')
        ruta_drop = '/proc/sys/vm/drop_caches'
        if not os.path.exists(ruta_drop):
            return "ADVERTENCIA: Limpieza de caché no disponible en este sistema (no es Linux o ruta no existe).\n"
        # Escribe '3' directamente en el archivo del kernel para limpiar el caché
        with open(ruta_drop, 'w') as f:
            f.write('3\n')
        return "Caché limpiado.\n"
    except PermissionError:
        return "ERROR: Permiso denegado al limpiar caché. Ejecuta el servidor con 'sudo'.\n"
    except Exception as e:
        return f"ERROR: Falló la limpieza de caché: {e}\n"

def procesar_datos():
    # Preparación y validaciones
    yield "--- PREPARACIÓN ---"
    ruta_archivo = _resolver_ruta_archivo(NOMBRE_ARCHIVO)
    if not os.path.isfile(ruta_archivo):
        yield f"ERROR: El archivo '{NOMBRE_ARCHIVO}' no se encontró. Ubícalo junto a app.py o especifica ruta absoluta."
        yield "Prueba cancelada."
        yield "\nPrueba completada."
        return
    # Solo mostrar un snapshot de MemInfo; NO limpiar caché automáticamente
    mi_snap = _leer_meminfo_mb()
    yield f"MemInfo actual - Cached: {mi_snap['CachedMB']} MB, Buffers: {mi_snap['BuffersMB']} MB, Dirty: {mi_snap['DirtyMB']} MB"

    # --- PROCESAMIENTO DESDE DISCO ---
    yield f"--- Iniciando procesamiento desde el DISCO ({NOMBRE_ARCHIVO}) ---"
    contador_disco = 0
    inicio_disco = time.time()

    try:
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            lineas_leidas = 0
            ultimo_pulso = time.time()
            for linea in f:
                lineas_leidas += 1
                contador_disco += linea.count(PALABRA_A_BUSCAR)
                # Pulso/heartbeat de progreso cada ~1.5s o cada 200k líneas
                ahora = time.time()
                if (lineas_leidas % 200000 == 0) or (ahora - ultimo_pulso > 1.5):
                    yield f"Progreso DISCO: {lineas_leidas} líneas procesadas..."
                    ultimo_pulso = ahora
        fin_disco = time.time()
    except Exception as e:
        yield f"ERROR: Lectura desde disco falló: {e}"
        yield "Prueba cancelada."
        yield "\nPrueba completada."
        return

    duracion_disco = fin_disco - inicio_disco
    yield f"Palabras '{PALABRA_A_BUSCAR}' encontradas: {contador_disco}"
    yield f"✅ Tiempo total desde DISCO: {duracion_disco:.4f} segundos\n"

    # --- PROCESAMIENTO DESDE RAM ---
    yield "--- Iniciando procesamiento desde la RAM ---"
    contador_ram = 0

    try:
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            contenido_en_ram = f.readlines()
    except Exception as e:
        yield f"ERROR: Carga en RAM falló: {e}"
        yield "Prueba cancelada."
        yield "\nPrueba completada."
        return

    inicio_ram = time.time()
    lineas_leidas_ram = 0
    ultimo_pulso_ram = time.time()
    for linea in contenido_en_ram:
        lineas_leidas_ram += 1
        contador_ram += linea.count(PALABRA_A_BUSCAR)
        ahora = time.time()
        if (lineas_leidas_ram % 200000 == 0) or (ahora - ultimo_pulso_ram > 1.5):
            yield f"Progreso RAM: {lineas_leidas_ram} líneas procesadas..."
            ultimo_pulso_ram = ahora
    fin_ram = time.time()

    duracion_ram = fin_ram - inicio_ram
    yield f"Palabras '{PALABRA_A_BUSCAR}' encontradas: {contador_ram}"
    yield f"✅ Tiempo total desde RAM: {duracion_ram:.4f} segundos\n"

    # --- CONCLUSIÓN ---
    yield "--- CONCLUSIÓN ---"
    if duracion_ram > 0 and duracion_ram < duracion_disco:
        diferencia = duracion_disco / duracion_ram
        yield f"Procesar desde la RAM fue {diferencia:.2f} veces más rápido que desde el disco."
    else:
        yield "No se observó una mejora significativa."

    yield "\nPrueba completada."