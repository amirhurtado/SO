#Install tabulate
# pip install tabulate

#Install matplotlib
# pip install matplotlib

# -------------------------------------------------------------


import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
from matplotlib.table import Table
from copy import deepcopy

try:
    from tabulate import tabulate
    has_tabulate = True
except ImportError:
    has_tabulate = False

# -------------------------------------------------------------
#               DATOS DE ENTRADA
# -------------------------------------------------------------
# Solo 4 campos: PROCESO, RAFAGA, TIME (tiempo de llegada), PRIORIDAD
processes_data = [
    {'proceso': 'P1', 'rafaga': 2, 'time': 0, 'prioridad': 1},
    {'proceso': 'P2', 'rafaga': 6, 'time': 1, 'prioridad': 1},
    {'proceso': 'P3', 'rafaga': 6, 'time': 2, 'prioridad': 2},
    {'proceso': 'P4', 'rafaga': 7, 'time': 2, 'prioridad': 2},
    {'proceso': 'P5', 'rafaga': 4, 'time': 3, 'prioridad': 1},
    {'proceso': 'P6', 'rafaga': 4, 'time': 4, 'prioridad': 3},
]

# -------------------------------------------------------------
#               FUNCIONES DE SCHEDULING
# -------------------------------------------------------------
def fcfs_scheduling(processes):
    """
    FIFO (First In, First Out)
    TE = te - time
    TS = tf - time
    """
    procs = sorted(processes, key=lambda x: x['time'])
    current_time = 0
    schedule = []
    for p in procs:
        if current_time < p['time']:
            current_time = p['time']
        start_time = current_time
        finish_time = start_time + p['rafaga']
        te = start_time - p['time']      # tiempo de espera
        ts = finish_time - p['time']       # tiempo de sistema
        schedule.append({
            'proceso': p['proceso'],
            'rafaga': p['rafaga'],
            'time': p['time'],
            'prioridad': p['prioridad'],
            'start': start_time,
            'finish': finish_time,
            'TE': te,
            'TS': ts
        })
        current_time = finish_time
    return schedule

def sjf_scheduling(processes):
    """
    SJF (Shortest Job First, no expropiativo)
    TE = te - time
    TS = tf - time
    """
    procs = deepcopy(processes)
    schedule = []
    current_time = 0
    remaining = len(procs)
    
    while remaining > 0:
        candidates = [p for p in procs if p['time'] <= current_time and not p.get('done', False)]
        if not candidates:
            current_time += 1
            continue
        p = min(candidates, key=lambda x: x['rafaga'])
        start_time = max(current_time, p['time'])
        finish_time = start_time + p['rafaga']
        p['start'] = start_time
        p['finish'] = finish_time
        p['TE'] = start_time - p['time']
        p['TS'] = finish_time - p['time']
        p['done'] = True
        schedule.append(p)
        current_time = finish_time
        remaining -= 1
    
    schedule.sort(key=lambda x: x['start'])
    return schedule

def priority_scheduling(processes):
    """
    Despacho por Prioridad (no expropiativo)
    TE = te - time
    TS = tf - time
    (Menor número => Mayor prioridad)
    """
    procs = deepcopy(processes)
    schedule = []
    current_time = 0
    remaining = len(procs)
    
    while remaining > 0:
        candidates = [p for p in procs if p['time'] <= current_time and not p.get('done', False)]
        if not candidates:
            current_time += 1
            continue
        p = min(candidates, key=lambda x: (x['prioridad'], x['time']))
        start_time = max(current_time, p['time'])
        finish_time = start_time + p['rafaga']
        p['start'] = start_time
        p['finish'] = finish_time
        p['TE'] = start_time - p['time']
        p['TS'] = finish_time - p['time']
        p['done'] = True
        schedule.append(p)
        current_time = finish_time
        remaining -= 1
    
    schedule.sort(key=lambda x: x['start'])
    return schedule

# -------------------------------------------------------------
#       FUNCIONES PARA CREAR TABLAS EN MATPLOTLIB
# -------------------------------------------------------------
def create_table(ax, cell_data, col_labels, title=""):
    """
    Crea una tabla en el eje ax con los datos de cell_data y cabeceras col_labels.
    cell_data debe ser una lista de listas (filas).
    """
    ax.set_axis_off()
    tabla = Table(ax, bbox=[0, 0, 1, 1])
    
    n_cols = len(col_labels)
    col_width = 1.0 / n_cols
    
    # Encabezados
    for col_idx, label in enumerate(col_labels):
        header_cell = tabla.add_cell(
            row=0, col=col_idx,
            width=col_width, height=0.1,
            text=label, loc='center', facecolor='#40466e'
        )
        header_text = header_cell.get_text()
        header_text.set_color('white')
        header_text.set_weight('bold')
    
    # Contenido
    for row_idx, row_data in enumerate(cell_data, start=1):
        for col_idx, val in enumerate(row_data):
            cell = tabla.add_cell(
                row=row_idx, col=col_idx,
                width=col_width, height=0.1,
                text=str(val), loc='center',
                facecolor='white'
            )
    
    n_rows = len(cell_data) + 1
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(8)
    for row_idx in range(n_rows):
        for col_idx in range(n_cols):
            cell = tabla.get_celld()[(row_idx, col_idx)]
            cell.set_height(0.9 / n_rows)
    
    ax.add_table(tabla)
    ax.set_title(title, fontsize=10, fontweight='bold')

def create_general_table(ax, processes):
    """
    Crea la tabla general con los 4 campos: PROCESO, RAFAGA, TIME, PRIORIDAD.
    Se ubica en un eje angosto para no extender demasiado a lo ancho.
    """
    cell_data = []
    for p in processes:
        cell_data.append([p['proceso'], p['rafaga'], p['time'], p['prioridad']])
    col_labels = ["PROCESO", "RÁFAGA", "TIME", "PRIORIDAD"]
    create_table(ax, cell_data, col_labels, title="Tabla General de Procesos")

# -------------------------------------------------------------
#       FUNCIONES PARA GENERAR TABLAS DE TE Y TS
# -------------------------------------------------------------
def get_te_table(schedule):
    """
    Retorna datos en formato [[Proceso, TE], ...] en el orden P1, P2, …, PN
    y agrega la fila de promedio.
    """
    # Ordenar por número (suponiendo que el formato es "P<number>")
    sorted_schedule = sorted(schedule, key=lambda x: int(x['proceso'][1:]))
    data = [[p['proceso'], p['TE']] for p in sorted_schedule]
    promedio = sum(p['TE'] for p in sorted_schedule) / len(sorted_schedule)
    data.append(["Promedio", round(promedio, 2)])
    return data

def get_ts_table(schedule):
    """
    Retorna datos en formato [[Proceso, TS], ...] en el orden P1, P2, …, PN
    y agrega la fila de promedio.
    """
    sorted_schedule = sorted(schedule, key=lambda x: int(x['proceso'][1:]))
    data = [[p['proceso'], p['TS']] for p in sorted_schedule]
    promedio = sum(p['TS'] for p in sorted_schedule) / len(sorted_schedule)
    data.append(["Promedio", round(promedio, 2)])
    return data

# -------------------------------------------------------------
#       FUNCIÓN PARA CREAR EL DIAGRAMA DE GANTT
# -------------------------------------------------------------
def plot_gantt(ax, schedule, algorithm_name):
    """
    Crea el diagrama de Gantt en el eje ax.
    - Eje Y: cada proceso en su propio renglón (ordenados para que P1 quede abajo).
    - Eje X: tiempo.
    """
    ax.set_title(f"Diagrama de Gantt - {algorithm_name}", fontsize=10, fontweight='bold')
    ax.set_xlabel("Tiempo", fontsize=8)
    
    # Orden de procesos para que P1 quede abajo
    process_order = ["P1", "P2", "P3", "P4", "P5", "P6"]
    y_positions = {proc: idx for idx, proc in enumerate(process_order)}
    
    color_map = {
        'P1': '#1f77b4',
        'P2': '#ff7f0e',
        'P3': '#2ca02c',
        'P4': '#d62728',
        'P5': '#9467bd',
        'P6': '#8c564b'
    }
    
    for item in schedule:
        proceso = item['proceso']
        start = item['start']
        finish = item['finish']
        rafaga = finish - start
        y = y_positions[proceso]
        ax.broken_barh([(start, rafaga)], (y, 0.8),
                       facecolors=color_map.get(proceso, "gray"))
        ax.text(start + rafaga/2, y + 0.4, proceso,
                ha="center", va="center", color="white",
                fontsize=8, fontweight="bold")
    
    max_time = max(p['finish'] for p in schedule) + 1
    ax.set_xlim(0, max_time)
    ax.set_ylim(-0.2, len(process_order))
    ax.set_yticks([i + 0.4 for i in range(len(process_order))])
    ax.set_yticklabels(process_order)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    ax.tick_params(axis='y', which='both', length=0)

# -------------------------------------------------------------
#            MOSTRAR EN CONSOLA (OPCIONAL)
# -------------------------------------------------------------
def show_tabulate_table(schedule):
    """
    Muestra en consola la tabla con: Proceso, Rafaga, Time, Prioridad, TE, TS, Inicio, Fin.
    También muestra los promedios.
    """
    headers = ["Proceso", "Ráfaga", "Time", "Prioridad", "TE", "TS", "Inicio", "Fin"]
    table = []
    for s in schedule:
        table.append([
            s['proceso'], s['rafaga'], s['time'], s['prioridad'],
            s['TE'], s['TS'], s['start'], s['finish']
        ])
    avg_te = sum(s['TE'] for s in schedule) / len(schedule)
    avg_ts = sum(s['TS'] for s in schedule) / len(schedule)
    table.append(["Promedio", "-", "-", "-", round(avg_te, 2), round(avg_ts, 2), "-", "-"])
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

# -------------------------------------------------------------
#            FUNCIÓN PRINCIPAL PARA LA VISTA UNIFICADA
# -------------------------------------------------------------
def main():
    # Obtener schedules para cada algoritmo
    fifo_schedule = fcfs_scheduling(processes_data)
    sjf_schedule = sjf_scheduling(processes_data)
    prio_schedule = priority_scheduling(processes_data)
    
    # Crear la figura global
    fig = plt.figure(figsize=(20, 15))
    try:
        mng = plt.get_current_fig_manager()
        mng.full_screen_toggle()
    except:
        pass
    
    # Usamos GridSpec con 4 filas y 3 columnas.
    # Para la fila 0 (tabla general) utilizamos solo la columna central.
    gs = GridSpec(4, 3, figure=fig, height_ratios=[1, 1, 1, 1])
    
    # Fila 0: Tabla General en la columna central (más angosta)
    ax_general = fig.add_subplot(gs[0, 1])
    create_general_table(ax_general, processes_data)
    
    # Fila 1: FIFO
    ax_fifo_te = fig.add_subplot(gs[1, 0])
    ax_fifo_ts = fig.add_subplot(gs[1, 1])
    ax_fifo_gantt = fig.add_subplot(gs[1, 2])
    create_table(ax_fifo_te,
                 get_te_table(fifo_schedule),
                 ["Proceso", "TE"],
                 title="FIFO - Tiempos de Espera")
    create_table(ax_fifo_ts,
                 get_ts_table(fifo_schedule),
                 ["Proceso", "TS"],
                 title="FIFO - Tiempos de Sistema")
    plot_gantt(ax_fifo_gantt, fifo_schedule, "FIFO")
    
    # Fila 2: SJF
    ax_sjf_te = fig.add_subplot(gs[2, 0])
    ax_sjf_ts = fig.add_subplot(gs[2, 1])
    ax_sjf_gantt = fig.add_subplot(gs[2, 2])
    create_table(ax_sjf_te,
                 get_te_table(sjf_schedule),
                 ["Proceso", "TE"],
                 title="SJF - Tiempos de Espera")
    create_table(ax_sjf_ts,
                 get_ts_table(sjf_schedule),
                 ["Proceso", "TS"],
                 title="SJF - Tiempos de Sistema")
    plot_gantt(ax_sjf_gantt, sjf_schedule, "SJF")
    
    # Fila 3: Prioridad
    ax_prio_te = fig.add_subplot(gs[3, 0])
    ax_prio_ts = fig.add_subplot(gs[3, 1])
    ax_prio_gantt = fig.add_subplot(gs[3, 2])
    create_table(ax_prio_te,
                 get_te_table(prio_schedule),
                 ["Proceso", "TE"],
                 title="Prioridad - Tiempos de Espera")
    create_table(ax_prio_ts,
                 get_ts_table(prio_schedule),
                 ["Proceso", "TS"],
                 title="Prioridad - Tiempos de Sistema")
    plot_gantt(ax_prio_gantt, prio_schedule, "Prioridad")
    
    plt.subplots_adjust(left=0.04, right=0.96, top=0.95, bottom=0.04, wspace=0.4, hspace=0.5)
    plt.show()
    
    # Opcional: Mostrar tablas en consola
    if has_tabulate:
        print("\n===== FIFO =====")
        show_tabulate_table(fifo_schedule)
        print("\n===== SJF =====")
        show_tabulate_table(sjf_schedule)
        print("\n===== Prioridad =====")
        show_tabulate_table(prio_schedule)

if __name__ == "__main__":
    main()
