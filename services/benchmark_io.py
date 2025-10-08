import os
import time
from .patterns import sequential_offsets, random_offsets, stride_offsets, hotset_offsets

def resolve_path(path_candidate):
    if os.path.isabs(path_candidate) and os.path.isfile(path_candidate):
        return path_candidate
    cwd = os.path.join(os.getcwd(), path_candidate)
    if os.path.isfile(cwd):
        return cwd
    here = os.path.dirname(os.path.abspath(__file__))
    project = os.path.abspath(os.path.join(here, '..'))
    in_project = os.path.join(project, path_candidate)
    if os.path.isfile(in_project):
        return in_project
    return path_candidate

def iter_offsets(kind, file_size, block_size, seed=42, stride_bytes=0, hotset_percent=10):
    if kind == 'sequential':
        return sequential_offsets(file_size, block_size)
    if kind == 'random':
        return random_offsets(file_size, block_size, seed)
    if kind == 'stride':
        return stride_offsets(file_size, block_size, stride_bytes)
    if kind == 'hotset':
        return hotset_offsets(file_size, block_size, hotset_percent, seed)
    return sequential_offsets(file_size, block_size)

def run_benchmark(params):
    """
    Generator de eventos para SSE.
    params: {
      filePath, blockSize, pattern, seed, strideBytes, hotsetPercent, passes
    }
    """
    file_path = resolve_path(params.get('filePath', 'archivo_grande.txt'))
    block_size = int(params.get('blockSize', 1024 * 64))
    pattern = params.get('pattern', 'sequential')
    seed = int(params.get('seed', 42))
    stride_bytes = int(params.get('strideBytes', block_size))
    hotset_percent = int(params.get('hotsetPercent', 10))
    passes = int(params.get('passes', 1))

    if not os.path.isfile(file_path):
        yield f"ERROR: Archivo no encontrado: {file_path}"
        return

    size = os.path.getsize(file_path)
    yield f"Archivo: {file_path} ({size} bytes)"
    yield f"Patrón: {pattern}, Bloque: {block_size} bytes, Pasadas: {passes}"

    total_bytes = 0
    t0_total = time.time()
    try:
        with open(file_path, 'rb', buffering=0) as f:
            for p in range(1, passes + 1):
                yield f"--- PASADA {p}/{passes} ---"
                t0 = time.time()
                num_blocks = 0
                for off in iter_offsets(pattern, size, block_size, seed, stride_bytes, hotset_percent):
                    f.seek(off)
                    chunk = f.read(block_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    num_blocks += 1
                    if num_blocks % 5000 == 0:
                        yield f"Progreso I/O: {num_blocks} bloques (~{(num_blocks*block_size)/1_048_576:.2f} MiB)"
                t1 = time.time()
                yield f"⏱️ Tiempo pasada {p}: {t1 - t0:.4f} s"
    except Exception as e:
        yield f"ERROR: Benchmark falló: {e}"
        return

    t1_total = time.time()
    elapsed = t1_total - t0_total
    throughput = (total_bytes / 1_048_576) / elapsed if elapsed > 0 else 0
    yield f"Total leído: {total_bytes/1_048_576:.2f} MiB"
    yield f"Throughput medio: {throughput:.2f} MiB/s"

