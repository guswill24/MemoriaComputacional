import os
import time

def read_meminfo_mb():
    try:
        data = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) < 2:
                    continue
                k = parts[0].strip()
                v = parts[1].strip().split()[0]
                if v.isdigit():
                    data[k] = int(v) / 1024.0
        return {
            'CachedMB': round(data.get('Cached', 0.0), 1),
            'BuffersMB': round(data.get('Buffers', 0.0), 1),
            'DirtyMB': round(data.get('Dirty', 0.0), 1),
        }
    except Exception:
        return {'CachedMB': -1, 'BuffersMB': -1, 'DirtyMB': -1}

def drop_caches():
    try:
        os.system('sync')
        path = '/proc/sys/vm/drop_caches'
        if not os.path.exists(path):
            return False, "ADVERTENCIA: drop_caches no disponible en este sistema.\n"
        with open(path, 'w') as f:
            f.write('3\n')
        return True, "Caché limpiado.\n"
    except PermissionError:
        return False, "ERROR: Permiso denegado al limpiar caché. Ejecuta con 'sudo'.\n"
    except Exception as e:
        return False, f"ERROR: Falló la limpieza: {e}\n"

