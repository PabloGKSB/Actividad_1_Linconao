"""
Implementación Paralela de AES-CTR usando ProcessPoolExecutor
"""

from __future__ import annotations

import hashlib
import sys
import time
import concurrent.futures
import threading

from Crypto.Cipher import AES
from Crypto.Util import Counter

DEFAULT_NONCE = b"CTRnonce"   # 8 bytes
DEFAULT_IO_CHUNK_SIZE = 1024 * 1024  # 1 MiB (Debe ser múltiplo de 16)


def derive_key_from_passphrase(passphrase: str, key_size: int = 32) -> bytes:
    if key_size not in (16, 24, 32):
        raise ValueError("key_size debe ser 16, 24 o 32")
    digest = hashlib.sha256(passphrase.encode("utf-8")).digest()
    return digest[:key_size]


def process_chunk(chunk_data: bytes, byte_offset: int, passphrase: str, nonce: bytes) -> tuple[int, bytes]:
    """
    Cifra o descifra un chunk en un proceso separado.
    Retorna el offset original y los datos cifrados para facilitar la reconstrucción.
    """
    key = derive_key_from_passphrase(passphrase, key_size=32)
    
    # Calcular el offset en bloques (AES usa bloques de 16 bytes)
    block_offset = byte_offset // 16
    
    # Instanciar el contador inicializado en el bloque que corresponde al offset
    ctr = Counter.new(64, prefix=nonce, initial_value=block_offset)
    
    # Crear la instancia AES con el contador sincronizado
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
    
    # Ejecutar cifrado/descifrado sobre los datos (XOR directo)
    processed_data = cipher.encrypt(chunk_data)
    
    return byte_offset, processed_data


def transform_file_ctr_parallel(
    input_path: str, 
    output_path: str, 
    passphrase: str, 
    nonce: bytes = DEFAULT_NONCE,
    chunk_size: int = DEFAULT_IO_CHUNK_SIZE,
    max_workers: int = 4
) -> float:
    
    if chunk_size % 16 != 0:
        raise ValueError("El tamaño del chunk debe ser múltiplo de 16 para AES.")
    
    start_time = time.perf_counter()
    
    futures = []
    # Usaremos un diccionario para contener temporalmente los bloques 
    # que fueron completados en orden aleatorio
    pending_writes = {}
    next_expected_offset = 0

    with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            
            # Semáforo para no saturar memoria RAM leyendo todo el archivo gigante
            # Limitamos las tareas pendientes en el pool a 2 * workers (con un min de 1 para evitar locks raros)
            semaphore_count = max(2, max_workers * 2)
            semaphore = threading.Semaphore(semaphore_count)
            
            offset = 0
            
            # Función interna auxiliar para drenar el buffer de escritura a disco
            def try_write():
                nonlocal next_expected_offset
                while next_expected_offset in pending_writes:
                    data = pending_writes.pop(next_expected_offset)
                    f_out.write(data)
                    next_expected_offset += len(data)

            while True:
                semaphore.acquire()
                chunk = f_in.read(chunk_size)
                
                if not chunk:
                    semaphore.release()
                    break
                
                # Asignar tarea al pool de procesos
                future = executor.submit(process_chunk, chunk, offset, passphrase, nonce)
                
                # Al terminar un future, se libera cupo para poder leer otro bloque extra
                future.add_done_callback(lambda _: semaphore.release())
                futures.append(future)
                
                offset += len(chunk)
                
            # Procesar iterativamente a medida que se completan las tareas asíncronas
            for future in concurrent.futures.as_completed(futures):
                chunk_offset, processed_data = future.result()
                
                # Guardar el bloque en la memoria intermedia
                pending_writes[chunk_offset] = processed_data
                
                # Drenar memoria hacia disco si el bloque es secuencialmente correcto
                try_write()

    end_time = time.perf_counter()
    return end_time - start_time


def main() -> None:
    if len(sys.argv) < 5 or len(sys.argv) > 7:
        print(
            "Uso: python cifrado_aes_ctr_paralelo.py <enc|dec> "
            "<archivo_entrada> <archivo_salida> <passphrase> [max_workers] [chunk_size_mb]"
        )
        sys.exit(1)

    operation = sys.argv[1].lower()
    input_path = sys.argv[2]
    output_path = sys.argv[3]
    passphrase = sys.argv[4]
    
    # Configurar worker si se provee o usar 4 por defecto
    max_workers = int(sys.argv[5]) if len(sys.argv) >= 6 else 4
    
    # Configurar tamaño de chunk si se provee o usar 1 MB por defecto
    chunk_size_mb = int(sys.argv[6]) if len(sys.argv) == 7 else 1
    chunk_size_bytes = chunk_size_mb * 1024 * 1024

    if operation not in {"enc", "dec"}:
        raise ValueError("La operación debe ser enc o dec")

    elapsed = transform_file_ctr_parallel(
        input_path, 
        output_path, 
        passphrase, 
        chunk_size=chunk_size_bytes,
        max_workers=max_workers
    )
    print(f"Tiempo de ejecución paralelo AES-CTR ({operation}) con {max_workers} workers y chunks de {chunk_size_mb}MB: {elapsed:.6f} s")


if __name__ == "__main__":
    # Importante en windows para el multiprocessing module
    import multiprocessing
    multiprocessing.freeze_support()
    main()
