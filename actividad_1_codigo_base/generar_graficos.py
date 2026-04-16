import csv
import matplotlib.pyplot as plt
import os
from collections import defaultdict

def leer_resultados(csv_file="resultados_experimento_oficial.csv"):
    if not os.path.exists(csv_file):
        print(f"Error: No se encuentra {csv_file}. Ejecuta experimentos.py primero.")
        return {}
        
    # Datos por tamaño: size -> {workers: [], tiempos: [], speedups: [], eficiencias: []}
    data_por_size = defaultdict(lambda: {"workers": [], "tiempos": [], "speedups": [], "eficiencias": []})
    
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            size = int(row["Archivo (MB)"])
            data_por_size[size]["workers"].append(int(row["Workers"]))
            data_por_size[size]["tiempos"].append(float(row["Tiempo Promedio (s)"]))
            data_por_size[size]["speedups"].append(float(row["Speedup (x)"]))
            data_por_size[size]["eficiencias"].append(float(row["Eficiencia (x)"]))
            
    return data_por_size

def generar_graficos():
    data = leer_resultados()
    if not data:
        return
        
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        pass

    colores = {10: '#1f77b4', 100: '#ff7f0e', 1024: '#2ca02c'}
    markers = {10: 's', 100: 'o', 1024: '^'}

    # 1. Gráfico de Tiempo
    plt.figure(figsize=(10, 6))
    for size, d in data.items():
        plt.plot(d['workers'], d['tiempos'], marker=markers.get(size, 'x'), linestyle='-', color=colores.get(size, 'black'), linewidth=2, label=f'Archivo {size} MB')
    plt.title('1. Tiempo de Ejecución vs Cores', fontsize=15, fontweight='bold')
    plt.xlabel('Número de Workers', fontsize=12)
    plt.ylabel('Tiempo Promedio (s) Log Scale', fontsize=12)
    plt.yscale('log') # Escala logarítmica es mejor para ver 10MB vs 1024MB
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.savefig('grafico_1_tiempo.png', dpi=300)
    plt.close()
    
    # 2. Gráfico de Speedup
    plt.figure(figsize=(10, 6))
    for size, d in data.items():
        plt.plot(d['workers'], d['speedups'], marker=markers.get(size, 'x'), linestyle='-', color=colores.get(size, 'black'), linewidth=2, label=f'Speedup {size} MB')
    
    first_size = list(data.keys())[0]
    w = data[first_size]['workers']
    plt.plot(w, w, linestyle='--', color='gray', linewidth=2, alpha=0.8, label="Speedup Ideal")
    
    plt.title('2. Aceleración de Speedup', fontsize=15, fontweight='bold')
    plt.xlabel('Número de Workers', fontsize=12)
    plt.ylabel('Speedup (Veces más rápido)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('grafico_2_speedup.png', dpi=300)
    plt.close()
    
    # 3. Gráfico de Eficiencia
    plt.figure(figsize=(10, 6))
    for size, d in data.items():
        plt.plot(d['workers'], d['eficiencias'], marker=markers.get(size, 'x'), linestyle='-', color=colores.get(size, 'black'), linewidth=2, label=f'Eficiencia {size} MB')
    
    plt.axhline(y=1.0, color='gray', linestyle='--', label="100% Eficiencia")
    plt.title('3. Eficiencia vs Acumulación de Múltiples Procesos', fontsize=15, fontweight='bold')
    plt.xlabel('Número de Workers', fontsize=12)
    plt.ylabel('Eficiencia de Recursos (S/p)', fontsize=12)
    plt.ylim([0, 1.1])
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig('grafico_3_eficiencia.png', dpi=300)
    plt.close()
    
    print("\n[+] Gráficos multi-archivo actualizados y guardados exitosamente!")

if __name__ == "__main__":
    generar_graficos()
