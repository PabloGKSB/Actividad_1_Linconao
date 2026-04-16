import os
import multiprocessing
import sys
import time
import matplotlib.pyplot as plt

from cifrado_aes_cbc_experimental import (
    cbc_secuencial, cbc_dec_paralelo, cbc_enc_paralico
)

def ejecutar_bonus():
    print("=========================================================================")
    print(" RÚBRICA 6.4: DEMOSTRACIÓN EXCLUSIVA AES-CBC Y DEPENDENCIA DE BLOQUES ")
    print("=========================================================================")

    input_file = "info_clav_100.csv"
    cifrado_seq = "seq_cbc.enc"
    cifrado_par = "par_cbc.enc"
    descifrado_par = "par_cbc_dec.csv"
    
    if not os.path.exists(input_file):
        print(f"No se detecta {input_file}. Prueba ejecutar primero experimentos.py")
        sys.exit(1)
        
    passphrase = "test"
    WORKERS = 4
    
    # 1. Base Secuencial
    print(f"1) Ejecutando Algoritmo Cifrado SECUENCIAL Original (100 MB)...")
    t_seq_enc = cbc_secuencial(input_file, cifrado_seq, passphrase, "enc")
    print(f"   -> Tiempo Secuencial: {t_seq_enc:.4f} s")
    
    # 2. Experimento Cifrado Paralelo
    print(f"\n2) Forzando Cifrado de manera PARALELA en {WORKERS} Workers...")
    t_par_enc = cbc_enc_paralico(input_file, cifrado_par, passphrase, WORKERS)
    print(f"   -> Tiempo Paralelo:   {t_par_enc:.4f} s")
        
    # 3. Experimento Descifrado Paralelo
    print(f"\n3) Ejecutando Descifrado PARALELO con los mismos {WORKERS} Workers...")
    t_seq_dec = cbc_secuencial(cifrado_seq, "seq_cbc_dec.csv", passphrase, "dec")
    t_par_dec = cbc_dec_paralelo(cifrado_par, descifrado_par, passphrase, WORKERS)
    
    print(f"   -> Tiempo Descifrado SECUENCIAL base: {t_seq_dec:.4f} s")
    print(f"   -> Tiempo Descifrado PARALELO puro:   {t_par_dec:.4f} s")
    
    print("\n--- Generando Gráfico de Respaldo Visual ---")
    # Generar gráfico simple de barras para la PPT
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        pass
        
    categorias = ['Cifrar Secuencial', 'Cifrar Paralelo\n(Cuello de botella)', 'Descifrar Secuencial', 'Descifrar Paralelo\n(Escalable)']
    tiempos = [t_seq_enc, t_par_enc, t_seq_dec, t_par_dec]
    colores = ['#7f7f7f', '#d62728', '#7f7f7f', '#2ca02c']

    plt.figure(figsize=(9, 6))
    barras = plt.bar(categorias, tiempos, color=colores, edgecolor='black', zorder=3)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7, zorder=0)
    plt.title('Comparativa Teórica: Limitaciones de Cifrado AES-CBC', fontsize=14, fontweight='bold')
    plt.ylabel('Tiempo de Ejecución (Segundos)', fontsize=12)
    plt.axhline(y=t_seq_enc, color='red', linestyle='--', alpha=0.4)
    
    for b in barras:
        alt = b.get_height()
        plt.text(b.get_x() + b.get_width()/2, alt + 0.05, f'{alt:.2f}s', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig('grafico_bonus_cbc.png', dpi=300)
    plt.close()
    
    print("Gráfico 'grafico_bonus_cbc.png' generado exitosamente para tu Diapositiva.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    ejecutar_bonus()
