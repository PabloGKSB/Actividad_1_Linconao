"""
Implementación Experimental de AES-CBC para Análisis de Bonificación (Rúbrica 6.4)
Demuestra matemáticamente que CBC tiene graves problemas para escalar en paralelismo de encriptación
por su "Encadenamiento de Bloques", pero brilla eficientemente en paralelo a la hora de descifrar.
"""

from __future__ import annotations
import hashlib
import time
import concurrent.futures

from Crypto.Cipher import AES

DEFAULT_IV = b"1234567890123456" # 16 bytes para AES CBC
DEFAULT_CHUNK = 1024 * 1024 # 1MB

def derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode("utf-8")).digest()[:32]

def pad_bytes(data: bytes) -> bytes:
    """Rellena con ceros hasta ser múltiplo de 16, requerido estrictamente por AES-CBC."""
    resto = len(data) % 16
    if resto != 0:
        return data + (b'\0' * (16 - resto))
    return data

# -------------------------------------------------------------
# 1. SECUENCIAL ORIGINAL CBC (Punto de Comparación)
# -------------------------------------------------------------
def cbc_secuencial(input_path: str, output_path: str, passphrase: str, mode: str) -> float:
    key = derive_key(passphrase)
    start = time.perf_counter()
    with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
        if mode == "enc":
            cipher = AES.new(key, AES.MODE_CBC, iv=DEFAULT_IV)
            while True:
                chunk = f_in.read(DEFAULT_CHUNK)
                if not chunk: break
                chunk = pad_bytes(chunk)
                f_out.write(cipher.encrypt(chunk))
        elif mode == "dec":
            cipher = AES.new(key, AES.MODE_CBC, iv=DEFAULT_IV)
            while True:
                chunk = f_in.read(DEFAULT_CHUNK)
                if not chunk: break
                f_out.write(cipher.decrypt(chunk))
    return time.perf_counter() - start

# -------------------------------------------------------------
# 2. WORKER AISLADO DE DESCIFRADO (Altamente Escalable)
# -------------------------------------------------------------
def process_chunk_dec(chunk_data: bytes, offset: int, passphrase: str, current_iv: bytes):
    key = derive_key(passphrase)
    cipher = AES.new(key, AES.MODE_CBC, iv=current_iv)
    return offset, cipher.decrypt(chunk_data)

def cbc_dec_paralelo(input_path: str, output_path: str, passphrase: str, workers: int) -> float:
    start = time.perf_counter()
    futures = []
    pending = {}
    next_offset = 0
    
    with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            offset = 0
            prev_chunk_last_16_bytes = DEFAULT_IV 
            
            while True:
                chunk_cifrado = f_in.read(DEFAULT_CHUNK)
                if not chunk_cifrado: break
                
                futures.append(executor.submit(
                    process_chunk_dec, chunk_cifrado, offset, passphrase, prev_chunk_last_16_bytes
                ))
                
                prev_chunk_last_16_bytes = chunk_cifrado[-16:]
                offset += len(chunk_cifrado)
                
            for future in concurrent.futures.as_completed(futures):
                idx, data = future.result()
                pending[idx] = data
                while next_offset in pending:
                    d = pending.pop(next_offset)
                    f_out.write(d)
                    next_offset += len(d)
                    
    return time.perf_counter() - start

# -------------------------------------------------------------
# 3. WORKER AISLADO DE ENCRIPTACIÓN (Demostración de Cuello de Botella)
# -------------------------------------------------------------
def worker_enc_sim(chk: bytes, iv: bytes, passwd: str):
    ciph = AES.new(derive_key(passwd), AES.MODE_CBC, iv=iv)
    return ciph.encrypt(chk)

def cbc_enc_paralico(input_path: str, output_path: str, passphrase: str, workers: int) -> float:
    start = time.perf_counter()
    with open(input_path, "rb") as f_in, open(output_path, "wb") as f_out:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            current_iv = DEFAULT_IV
            
            while True:
                chunk = f_in.read(DEFAULT_CHUNK)
                if not chunk: break
                chunk = pad_bytes(chunk)
                
                result = executor.submit(worker_enc_sim, chunk, current_iv, passphrase).result()
                f_out.write(result)
                
                current_iv = result[-16:]
                
    return time.perf_counter() - start
