"""
Script de Medición Experimental de Rendimiento Integrado
Utiliza los archivos oficiales del profesor y el validador provisto.
"""

import os
import csv
import subprocess
import multiprocessing

from cifrado_aes_ctr_secuencial import transform_file_ctr as transform_seq
from cifrado_aes_ctr_paralelo import transform_file_ctr_parallel as transform_par

def ejecutar_comando(comando):
    print(f"[*] Ejecutando: {' '.join(comando)}")
    subprocess.run(comando, check=True)

def preparar_y_validar():
    """Genera los archivos si no existen y usa validador.py para verificar que la paralelizacion es perfecta."""
    archivos_reales = {
        10: "info_clav_10.csv",
        100: "info_clav_100.csv",
        1024: "info_clav_1024.csv"
    }

    print("\n--- PASO 1: Generación de Archivos base ---")
    for size, name in archivos_reales.items():
        if not os.path.exists(name):
            ejecutar_comando(["python", "generate_files.py", str(size), name])
        else:
            print(f"[✓] Archivo {name} ya existe.")

    print("\n--- PASO 2: Validación de Integridad (Verificando la Rúbrica) ---")
    test_file = archivos_reales[10]
    enc_file = "test_val_enc.enc"
    dec_file = "test_val_dec.csv"
    passphrase = "test-pass"

    # Cifrar usando Secuencial (Original del profesor)
    print("  -> Cifrando con algoritmo original...")
    transform_seq(test_file, enc_file, passphrase)
    
    # Descifrar usando Paralelizado (Nuestra implementacion)
    print("  -> Descifrando con algoritmo paralelo...")
    transform_par(enc_file, dec_file, passphrase, max_workers=4)

    # Validar con validador.py del profesor
    print("  -> Validando Archivos (Original vs Descifrado)...")
    ejecutar_comando(["python", "validador.py", test_file, dec_file])

    return archivos_reales

def run_experiments():
    archivos = preparar_y_validar()

    PASSPHRASE = "test-pass"
    REPETICIONES = 10
    WORKERS_A_TESTEAR = [1, 2, 3, 4, 6, 8, 12, 16, 32]
    
    resultados = []
    
    print("\n--- PASO 3: Ejecución de Experimentos 10 Vueltas ---")
    
    for size_mb, input_file in archivos.items():
        output_file = f"enc_{size_mb}.enc"
        print(f"\n=======================================================")
        print(f" EVALUANDO ARCHIVO: {input_file} ({size_mb} MB) ")
        print(f"=======================================================")
        
        # 1. Medir Secuencial
        print("Midiendo algoritmo Original Secuencial (Baseline)...")
        tiempos_seq = []
        for i in range(REPETICIONES):
            t = transform_seq(input_file, output_file, PASSPHRASE)
            tiempos_seq.append(t)
            print(f"  [{size_mb}MB] Seq | Rep {i+1}/{REPETICIONES}: {t:.4f} s")
        
        t_seq_promedio = sum(tiempos_seq) / REPETICIONES
        print(f"-> Promedio Secuencial {size_mb}MB: {t_seq_promedio:.4f} s\n")
        
        # 2. Medir Paralelo
        for workers in WORKERS_A_TESTEAR:
            print(f"Midiendo Paralelo con {workers} Workers ({size_mb}MB)...")
            tiempos_par = []
            for i in range(REPETICIONES):
                t = transform_par(input_file, output_file, PASSPHRASE, max_workers=workers)
                tiempos_par.append(t)
                
            t_par_promedio = sum(tiempos_par) / REPETICIONES
            speedup = t_seq_promedio / t_par_promedio
            eficiencia = speedup / workers
            overhead = t_par_promedio - t_seq_promedio if workers == 1 else None
            
            print(f"  Promedio {workers}W: {t_par_promedio:.4f} s | Speedup: {speedup:.2f}x")
            
            resultados.append({
                "Archivo (MB)": size_mb,
                "Workers": workers,
                "Tiempo Promedio (s)": t_par_promedio,
                "Speedup (x)": speedup,
                "Eficiencia (x)": eficiencia,
                "Tiempo Secuencial Base": t_seq_promedio,
                "Overhead Estimado (1W)": overhead if overhead is not None else ""
            })

    # Guardar CSV
    csv_file = "resultados_experimento_oficial.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Archivo (MB)", "Workers", "Tiempo Promedio (s)", "Speedup (x)", "Eficiencia (x)", "Tiempo Secuencial Base", "Overhead Estimado (1W)"
        ])
        writer.writeheader()
        writer.writerows(resultados)
        
    print(f"\n¡Todos los experimentos terminados! Métricas oficiales guardadas en: {csv_file}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_experiments()
