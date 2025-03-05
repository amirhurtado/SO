import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec
from matplotlib.table import Table
from copy import deepcopy

# ----------------------- Datos iniciales -----------------------
processes_data = [
    {'proceso': 'P1', 'rafaga': 2, 'time': 0, 'prioridad': 1},
    {'proceso': 'P2', 'rafaga': 6, 'time': 1, 'prioridad': 1},
    {'proceso': 'P3', 'rafaga': 6, 'time': 2, 'prioridad': 2},
    {'proceso': 'P4', 'rafaga': 7, 'time': 2, 'prioridad': 2},
    {'proceso': 'P5', 'rafaga': 4, 'time': 3, 'prioridad': 1},
    {'proceso': 'P6', 'rafaga': 4, 'time': 4, 'prioridad': 3},
]

# Lista global para las filas de la tabla editable
process_entries = []

# ----------------------- Algoritmos de scheduling -----------------------
def fcfs_scheduling(processes):
    procs = sorted(processes, key=lambda x: x['time'])
    current_time = 0
    schedule = []
    for p in procs:
        if current_time < p['time']:
            current_time = p['time']
        start_time = current_time
        finish_time = start_time + p['rafaga']
        te = start_time - p['time']
        ts = finish_time - p['time']
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

def srtf_scheduling(processes):
    """
    Algoritmo SRTF (preemptivo). Retorna:
      - schedule: resumen final por proceso
      - gantt_segments: lista de segmentos para el diagrama de Gantt
    """
    proc_list = []
    for p in processes:
        new_p = p.copy()
        new_p["remaining"] = p["rafaga"]
        new_p["start_time"] = None
        new_p["finish_time"] = None
        proc_list.append(new_p)
    
    time = 0
    completed = 0
    n = len(proc_list)
    gantt_segments = []
    current_proc = None
    segment_start = None
    
    while completed < n:
        available = [p for p in proc_list if p["time"] <= time and p["remaining"] > 0]
        if not available:
            time += 1
            continue
        available.sort(key=lambda p: (p["remaining"], p["time"]))
        selected = available[0]
        
        if current_proc is None or current_proc["proceso"] != selected["proceso"]:
            if current_proc is not None:
                gantt_segments.append({
                    'proceso': current_proc["proceso"],
                    'start': segment_start,
                    'finish': time
                })
            current_proc = selected
            if current_proc["start_time"] is None:
                current_proc["start_time"] = time
            segment_start = time
        
        current_proc["remaining"] -= 1
        time += 1
        
        if current_proc["remaining"] == 0:
            current_proc["finish_time"] = time
            gantt_segments.append({
                'proceso': current_proc["proceso"],
                'start': segment_start,
                'finish': time
            })
            completed += 1
            current_proc = None
    
    schedule = []
    for p in proc_list:
        ts = p["finish_time"] - p["time"]
        te = ts - p["rafaga"]
        schedule.append({
            'proceso': p["proceso"],
            'rafaga': p["rafaga"],
            'time': p["time"],
            'prioridad': p["prioridad"],
            'start': p["start_time"],
            'finish': p["finish_time"],
            'TE': te,
            'TS': ts
        })
    schedule.sort(key=lambda x: int(x["proceso"][1:]))
    return schedule, gantt_segments

def rr_scheduling(processes, quantum):
    """
    Algoritmo Round Robin (RR) con quantum.
    Retorna:
      - schedule: resumen final por proceso
      - gantt_segments: lista de segmentos para el diagrama de Gantt
    """
    # Copia de los procesos para no modificar los originales
    proc_list = []
    for p in processes:
        new_p = p.copy()
        new_p["remaining"] = p["rafaga"]  # Tiempo restante de ejecución
        new_p["start_time"] = None  # Tiempo de inicio
        new_p["finish_time"] = None  # Tiempo de finalización
        proc_list.append(new_p)
    
    time = 0  # Tiempo actual
    queue = []  # Cola de procesos listos
    schedule = []  # Resumen final de los procesos
    gantt_segments = []  # Segmentos para el diagrama de Gantt
    
    while True:
        # Agregar procesos que han llegado al tiempo actual
        for proc in proc_list:
            if proc["time"] <= time and "added_to_queue" not in proc:
                queue.append(proc)
                proc["added_to_queue"] = True  # Marcar como agregado a la cola
        
        if not queue:
            # Si no hay procesos en la cola, avanzar el tiempo
            if all(p["finish_time"] is not None for p in proc_list):
                break  # Todos los procesos han terminado
            time += 1
            continue
        
        # Tomar el primer proceso de la cola
        current_proc = queue.pop(0)
        
        # Si es la primera vez que se ejecuta, registrar el tiempo de inicio
        if current_proc["start_time"] is None:
            current_proc["start_time"] = time
        
        # Ejecutar el proceso por el tiempo del quantum o lo que le queda
        execution_time = min(quantum, current_proc["remaining"])
        gantt_segments.append({
            'proceso': current_proc["proceso"],
            'start': time,
            'finish': time + execution_time
        })
        
        # Actualizar el tiempo y el tiempo restante del proceso
        time += execution_time
        current_proc["remaining"] -= execution_time
        
        # Si el proceso ha terminado, registrar el tiempo de finalización
        if current_proc["remaining"] == 0:
            current_proc["finish_time"] = time
            schedule.append(current_proc)
        else:
            # Si no ha terminado, volver a agregarlo al final de la cola
            queue.append(current_proc)
    
    # Calcular TE (Tiempo de Espera) y TS (Tiempo de Sistema) para cada proceso
    for proc in schedule:
        proc['TS'] = proc['finish_time'] - proc['time']
        proc['TE'] = proc['TS'] - proc['rafaga']
    
    return schedule, gantt_segments

# ----------------------- Funciones para crear tablas y diagramas con Matplotlib -----------------------
def create_table(ax, cell_data, col_labels, title=""):
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
            tabla.add_cell(
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

def get_te_table(schedule):
    sorted_schedule = sorted(schedule, key=lambda x: int(x['proceso'][1:]))
    data = [[p['proceso'], p['TE']] for p in sorted_schedule]
    promedio = sum(p['TE'] for p in sorted_schedule) / len(sorted_schedule)
    data.append(["Promedio", round(promedio, 2)])
    return data

def get_ts_table(schedule):
    sorted_schedule = sorted(schedule, key=lambda x: int(x['proceso'][1:]))
    data = [[p['proceso'], p['TS']] for p in sorted_schedule]
    promedio = sum(p['TS'] for p in sorted_schedule) / len(sorted_schedule)
    data.append(["Promedio", round(promedio, 2)])
    return data

def plot_gantt(ax, schedule, algorithm_name):
    ax.set_title(f"Diagrama de Gantt - {algorithm_name}", fontsize=10, fontweight='bold')
    ax.set_xlabel("Tiempo", fontsize=8)
    
    # Determinamos el orden de procesos, asumiendo P1..Pn
    # o, si prefieres, obtén el orden a partir de los datos
    process_order = sorted({p['proceso'] for p in schedule}, key=lambda x: int(x[1:]))
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

def plot_gantt_srtf(ax, segments, algorithm_name):
    ax.set_title(f"Diagrama de Gantt - {algorithm_name}", fontsize=10, fontweight='bold')
    ax.set_xlabel("Tiempo", fontsize=8)
    
    process_order = sorted(list({seg["proceso"] for seg in segments}), key=lambda x: int(x[1:]))
    y_positions = {proc: idx for idx, proc in enumerate(process_order)}
    
    color_map = {
        'P1': '#1f77b4',
        'P2': '#ff7f0e',
        'P3': '#2ca02c',
        'P4': '#d62728',
        'P5': '#9467bd',
        'P6': '#8c564b'
    }
    
    for seg in segments:
        proceso = seg["proceso"]
        start = seg["start"]
        finish = seg["finish"]
        rafaga = finish - start
        y = y_positions[proceso]
        ax.broken_barh([(start, rafaga)], (y, 0.8), facecolors=color_map.get(proceso, "gray"))
        ax.text(start + rafaga/2, y + 0.4, proceso, ha="center", va="center",
                color="white", fontsize=8, fontweight="bold")
    
    max_time = max(seg["finish"] for seg in segments) + 1
    ax.set_xlim(0, max_time)
    ax.set_ylim(-0.2, len(process_order))
    ax.set_yticks([i + 0.4 for i in range(len(process_order))])
    ax.set_yticklabels(process_order)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    ax.tick_params(axis='y', which='both', length=0)

# ----------------------- Crear la figura con todos los algoritmos -----------------------
def create_figure(quantum=2):
    """
    Crea una figura con los resultados de todos los algoritmos de scheduling.
    :param quantum: Valor del quantum para el algoritmo Round Robin.
    :return: Figura de Matplotlib.
    """
    # Ejecutar todos los algoritmos de scheduling
    fifo_schedule = fcfs_scheduling(processes_data)
    sjf_schedule = sjf_scheduling(processes_data)
    prio_schedule = priority_scheduling(processes_data)
    srtf_schedule, srtf_segments = srtf_scheduling(processes_data)
    rr_schedule, rr_segments = rr_scheduling(processes_data, quantum=quantum)  # Usar el quantum
    
    # Crear la figura
    fig = plt.figure(figsize=(25, 20))
    gs = GridSpec(5, 4, figure=fig, height_ratios=[1, 1, 1, 1, 1])
    
    # Fila 0: FIFO
    ax_fifo_te = fig.add_subplot(gs[0, 0])
    ax_fifo_ts = fig.add_subplot(gs[0, 1])
    ax_fifo_gantt = fig.add_subplot(gs[0, 2])
    create_table(ax_fifo_te, get_te_table(fifo_schedule), ["Proceso", "TE"], title="FIFO - Tiempos de Espera")
    create_table(ax_fifo_ts, get_ts_table(fifo_schedule), ["Proceso", "TS"], title="FIFO - Tiempos de Sistema")
    plot_gantt(ax_fifo_gantt, fifo_schedule, "FIFO")
    
    # Fila 1: SJF
    ax_sjf_te = fig.add_subplot(gs[1, 0])
    ax_sjf_ts = fig.add_subplot(gs[1, 1])
    ax_sjf_gantt = fig.add_subplot(gs[1, 2])
    create_table(ax_sjf_te, get_te_table(sjf_schedule), ["Proceso", "TE"], title="SJF - Tiempos de Espera")
    create_table(ax_sjf_ts, get_ts_table(sjf_schedule), ["Proceso", "TS"], title="SJF - Tiempos de Sistema")
    plot_gantt(ax_sjf_gantt, sjf_schedule, "SJF")
    
    # Fila 2: Prioridad
    ax_prio_te = fig.add_subplot(gs[2, 0])
    ax_prio_ts = fig.add_subplot(gs[2, 1])
    ax_prio_gantt = fig.add_subplot(gs[2, 2])
    create_table(ax_prio_te, get_te_table(prio_schedule), ["Proceso", "TE"], title="Prioridad - Tiempos de Espera")
    create_table(ax_prio_ts, get_ts_table(prio_schedule), ["Proceso", "TS"], title="Prioridad - Tiempos de Sistema")
    plot_gantt(ax_prio_gantt, prio_schedule, "Prioridad")
    
    # Fila 3: SRTF
    ax_srtf_te = fig.add_subplot(gs[3, 0])
    ax_srtf_ts = fig.add_subplot(gs[3, 1])
    ax_srtf_gantt = fig.add_subplot(gs[3, 2])
    create_table(ax_srtf_te, get_te_table(srtf_schedule), ["Proceso", "TE"], title="SRTF - Tiempos de Espera")
    create_table(ax_srtf_ts, get_ts_table(srtf_schedule), ["Proceso", "TS"], title="SRTF - Tiempos de Sistema")
    plot_gantt_srtf(ax_srtf_gantt, srtf_segments, "SRTF")
    
    # Fila 4: RR
    ax_rr_te = fig.add_subplot(gs[4, 0])
    ax_rr_ts = fig.add_subplot(gs[4, 1])
    ax_rr_gantt = fig.add_subplot(gs[4, 2])
    create_table(ax_rr_te, get_te_table(rr_schedule), ["Proceso", "TE"], title="RR - Tiempos de Espera")
    create_table(ax_rr_ts, get_ts_table(rr_schedule), ["Proceso", "TS"], title="RR - Tiempos de Sistema")
    plot_gantt_srtf(ax_rr_gantt, rr_segments, f"RR (Quantum={quantum})")  # Mostrar el quantum en el título
    
    # Ajustar el espaciado entre subplots
    plt.subplots_adjust(left=0.04, right=0.96, top=0.95, bottom=0.04, wspace=0.4, hspace=0.5)
    return fig

# ----------------------- Funciones para la tabla editable (única) -----------------------
def create_edit_table(parent):
    """Crea la cabecera y las filas iniciales en la tabla editable."""
    header_labels = ["Proceso", "Ráfaga", "Time", "Prioridad", "Acción"]
    for col, text in enumerate(header_labels):
        lbl = tk.Label(parent, text=text, font=('Arial', 10, 'bold'), bg='white')
        lbl.grid(row=0, column=col, padx=5, pady=5)
    # Filas iniciales
    for row_data in processes_data:
        add_row(parent, initial_data=row_data)

def add_row(parent, initial_data=None):
    row_index = len(process_entries) + 1  # la fila 0 es la cabecera
    e_proceso = tk.Entry(parent)
    e_rafaga = tk.Entry(parent)
    e_time = tk.Entry(parent)
    e_prioridad = tk.Entry(parent)
    
    if initial_data:
        e_proceso.insert(0, initial_data.get('proceso', ''))
        e_rafaga.insert(0, str(initial_data.get('rafaga', '')))
        e_time.insert(0, str(initial_data.get('time', '')))
        e_prioridad.insert(0, str(initial_data.get('prioridad', '')))
    
    e_proceso.grid(row=row_index, column=0, padx=5, pady=5)
    e_rafaga.grid(row=row_index, column=1, padx=5, pady=5)
    e_time.grid(row=row_index, column=2, padx=5, pady=5)
    e_prioridad.grid(row=row_index, column=3, padx=5, pady=5)
    
    btn_delete = tk.Button(parent, text="Eliminar", command=lambda: delete_row(parent, row_index))
    btn_delete.grid(row=row_index, column=4, padx=5, pady=5)
    
    process_entries.append({
        'row': row_index,
        'proceso': e_proceso,
        'rafaga': e_rafaga,
        'time': e_time,
        'prioridad': e_prioridad,
        'delete_btn': btn_delete
    })

def delete_row(parent, row_index):
    global process_entries
    for entry in process_entries:
        if entry['row'] == row_index:
            entry['proceso'].destroy()
            entry['rafaga'].destroy()
            entry['time'].destroy()
            entry['prioridad'].destroy()
            entry['delete_btn'].destroy()
            process_entries.remove(entry)
            break
    # Reorganizar filas
    for i, entry in enumerate(process_entries, start=1):
        entry['row'] = i
        entry['proceso'].grid(row=i, column=0, padx=5, pady=5)
        entry['rafaga'].grid(row=i, column=1, padx=5, pady=5)
        entry['time'].grid(row=i, column=2, padx=5, pady=5)
        entry['prioridad'].grid(row=i, column=3, padx=5, pady=5)
        entry['delete_btn'].grid(row=i, column=4, padx=5, pady=5)

def get_process_data_from_entries():
    data = []
    for entry in process_entries:
        proceso = entry['proceso'].get()
        try:
            rafaga = float(entry['rafaga'].get())
        except:
            rafaga = 0
        try:
            time_val = float(entry['time'].get())
        except:
            time_val = 0
        try:
            prioridad = int(entry['prioridad'].get())
        except:
            prioridad = 0
        if proceso:
            data.append({
                'proceso': proceso,
                'rafaga': rafaga,
                'time': time_val,
                'prioridad': prioridad
            })
    return data

# ----------------------- Función para actualizar la simulación -----------------------
def update_simulation(quantum):
    global processes_data, fig_canvas
    new_data = get_process_data_from_entries()
    if not new_data:
        messagebox.showerror("Error", "No se encontraron datos válidos.")
        return
    processes_data = new_data
    
    try:
        quantum = int(quantum)
    except ValueError:
        messagebox.showerror("Error", "El quantum debe ser un número entero.")
        return
    
    # Eliminamos la figura anterior y creamos la nueva
    for widget in sim_frame.winfo_children():
        widget.destroy()
    
    fig = create_figure(quantum)  # Pasar el quantum a create_figure
    fig_canvas = FigureCanvasTkAgg(fig, master=sim_frame)
    fig_canvas.draw()
    fig_canvas.get_tk_widget().pack()

# ----------------------- Interfaz principal con un único scroll -----------------------
def main():
    root = tk.Tk()
    root.title("Taller de Algoritmos de Despacho - Todo en un scroll")
    
    # Canvas + Scrollbars
    canvas = tk.Canvas(root, bg='white')
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar_v = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
    
    scrollbar_h = ttk.Scrollbar(root, orient=tk.HORIZONTAL, command=canvas.xview)
    scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
    
    canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
    
    # Frame contenedor de toda la interfaz
    content_frame = tk.Frame(canvas, bg='white')
    canvas.create_window((0, 0), window=content_frame, anchor="nw")
    
    # 1) Fila superior: Nombres + Tabla Editable
    top_row = tk.Frame(content_frame, bg='white')
    top_row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
    
    # Nombres a la izquierda
    names_frame = tk.Frame(top_row, bg='white')
    names_frame.pack(side=tk.LEFT, padx=5)
    names_label = tk.Label(names_frame,
                           text="Amir Hurtado Mena\nSteven Grisales",
                           font=('Arial', 12, 'bold'),
                           bg='white',
                           justify="center")
    names_label.pack()
    
    # Tabla editable a la derecha
    table_frame = tk.Frame(top_row, bg='white')
    table_frame.pack(side=tk.LEFT, padx=20)
    create_edit_table(table_frame)
    
    # 2) Botones para agregar fila y simular
    btn_frame = tk.Frame(content_frame, bg='white')
    btn_frame.pack(fill=tk.X, padx=10, pady=5)
    
    btn_add = tk.Button(btn_frame, text="Agregar Fila",
                        command=lambda: add_row(table_frame))
    btn_add.pack(side=tk.LEFT, padx=5)
    
    # Campo de entrada para el quantum
    quantum_label = tk.Label(btn_frame, text="Quantum:", bg='white')
    quantum_label.pack(side=tk.LEFT, padx=5)
    quantum_entry = tk.Entry(btn_frame, width=5)
    quantum_entry.pack(side=tk.LEFT, padx=5)
    quantum_entry.insert(0, "2")  # Valor por defecto
    
    btn_simulate = tk.Button(btn_frame, text="Simular", command=lambda: update_simulation(quantum_entry.get()))
    btn_simulate.pack(side=tk.LEFT, padx=5)
    
    # 3) Frame para la figura
    global sim_frame, fig_canvas
    sim_frame = tk.Frame(content_frame, bg='white')
    sim_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Crear la figura inicial
    fig = create_figure()
    fig_canvas = FigureCanvasTkAgg(fig, master=sim_frame)
    fig_canvas.draw()
    fig_canvas.get_tk_widget().pack()
    
    # Vincular eventos de scroll
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _on_shift_mousewheel(event):
        canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)
    
    # Para Linux: <Button-4> y <Button-5> (vertical), <Shift-Button-4> y <Shift-Button-5> (horizontal)
    canvas.bind_all("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))
    canvas.bind_all("<Shift-Button-4>", lambda event: canvas.xview_scroll(-1, "units"))
    canvas.bind_all("<Shift-Button-5>", lambda event: canvas.xview_scroll(1, "units"))
    
    # Ajustar el scroll region
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    content_frame.bind("<Configure>", on_configure)
    
    root.mainloop()

if __name__ == "__main__":
    main()
