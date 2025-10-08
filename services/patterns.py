import os
import random

def sequential_offsets(file_size, block_size):
    for off in range(0, file_size, block_size):
        yield off

def random_offsets(file_size, block_size, seed=42):
    rnd = random.Random(seed)
    offsets = list(range(0, file_size, block_size))
    rnd.shuffle(offsets)
    for off in offsets:
        yield off

def stride_offsets(file_size, block_size, stride_bytes):
    stride = max(block_size, stride_bytes)
    off = 0
    while off < file_size:
        yield off
        off += stride

def hotset_offsets(file_size, block_size, hotset_percent=10, seed=42):
    rnd = random.Random(seed)
    hot_bytes = max(block_size, int(file_size * (hotset_percent / 100.0)))
    cold_bytes = file_size - hot_bytes
    # Hot region al inicio
    hot_range = (0, hot_bytes)
    cold_range = (hot_bytes, file_size)
    # Mezcla 80/20
    for _ in range(max(1, file_size // block_size)):
        if rnd.random() < 0.8:
            base = rnd.randrange(hot_range[0], hot_range[1], block_size)
        else:
            base = rnd.randrange(cold_range[0], cold_range[1], block_size)
        yield base

