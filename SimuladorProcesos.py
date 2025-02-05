import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.simpledialog import Dialog
from PIL import Image, ImageTk
import pygame
import pandas as pd
import copy
import time    

# Inicializar pygame para manejar audio
pygame.mixer.init()

# Log para ir guardando cada t
class Log:
    def __init__(self):
        self.procesosnuevos = []
        self.procesoslistos = []
        self.procesoslistosysuspendidos = []
        self.procesosterminados = []
        self.procesoenCPU = None
        self.particiones = {
            "trabajos_grandes": {"nombre_proceso": None, "tamano_proceso": None, "fragmentacion_interna": 0},
            "trabajos_medianos": {"nombre_proceso": None, "tamano_proceso": None, "fragmentacion_interna": 0},
            "trabajos_chiquitos": {"nombre_proceso": None, "tamano_proceso": None, "fragmentacion_interna": 0}
        }
    def __str__(self):
        return f"Log(ProcesosNuevos={len(self.procesosnuevos)}, ProcesosListos={len(self.procesoslistos)}, ProcesosListosYSuspendidos={len(self.procesoslistosysuspendidos)}, ProcesosTerminados={len(self.procesosterminados)}, ProcesoEnCPU={self.procesoenCPU}, Particiones={len(self.particiones)})"
    def agregar_procesos_nuevos(self, procesos):
        self.procesosnuevos = procesos
    def agregar_procesos_listos(self, procesos):
        self.procesoslistos = procesos
    def agregar_procesos_listos_y_suspendidos(self, procesos):
        self.procesoslistosysuspendidos = procesos
    def agregar_procesos_terminados(self, procesos):
        self.procesosterminados = procesos
    def cambiar_proceso_en_cpu(self, proceso):
        self.procesoenCPU = proceso
    def setear_proceso_en_particion(self, proceso, particion, tamano, fragmentacion):
        self.particiones[particion]["nombre_proceso"] = proceso
        self.particiones[particion]["tamano_proceso"] = tamano
        self.particiones[particion]["fragmentacion_interna"] = fragmentacion

# Clases a utilizar
class Procesos:
    def __init__(self, tr, ta, ti, tam_b):
        self.tr = tr
        self.ta = ta
        self.ti = ti
        self.tam_b = tam_b
        self.estado = "nuevo"
        self.tiempoEjecutado = 0
        self.particion_asignada = None
    def __str__(self):
        return f"Proceso {self.tr}: [T.Arribo: {self.ta}, T.Irrupción: {self.ti}, T.Restante: {self.ti - self.tiempoEjecutado}, Tamaño: {self.tam_b/1000}KB]"
    def nombreProceso(self):
        return f"Proceso {self.tr}"
    def asignar_particion(self, particion):
        self.particion_asignada = particion
    def obtener_particion(self):
        return self.particion_asignada

# Todo esto es para que la ventana de diálogo se seleccione solo
class IntegerInputDialog(Dialog):
    def __init__(self, parent, title, prompt):
        self.prompt = prompt
        self.result = None
        super().__init__(parent, title=title)

    def body(self, master):
        # Configura la ventana de diálogo para que aparezca enfocada y al frente
        self.grab_set()  # Bloquea el foco en esta ventana hasta que se cierre

        tk.Label(master, text=self.prompt).grid(row=0, column=0, padx=5, pady=5)
        self.entry = ttk.Entry(master)
        self.entry.grid(row=1, column=0, padx=5, pady=5)

        self.entry.focus()  # Enfoca automáticamente el campo de entrada
        self.entry.select_range(0, tk.END)  # Selecciona todo el texto

        return self.entry  # Retorna el campo para asegurar que esté enfocado

    def apply(self):
        try:
            self.result = int(self.entry.get())
        except ValueError:
            self.result = None  # Si no es un entero válido, no guarda el resultado

class Particiones:
    def __init__(self, tamano, nombre):
        self.tamano = tamano
        self.fragmentacion = 0
        self.proceso_asignado = None
        self.nombre = nombre
    def __str__(self):
        return f"Partición {self.nombre}: TAM={self.tamano}, FRAG={self.fragmentacion}, Proceso={self.proceso_asignado}"
    def setFragmentacion(self, fragmentacion):
        self.fragmentacion = fragmentacion
    def setProceso(self, proceso):
        self.proceso_asignado = proceso

particionGrande = Particiones(250000, "trabajos_grandes")
particionMediana = Particiones(150000, "trabajos_medianos")
particionChiquita = Particiones(50000, "trabajos_chiquitos")
Memoria = [particionChiquita, particionGrande, particionMediana]

# Variables globales
musica_activa = True
archivo_csv = None
tree = None
pestanaProcesos = False
pestanaStats = False
frame_tabla = None
boton_agregar_fila = None
historial = []
calculadorTiempos = {}
barra_desplazamiento = None

def ask_integer(parent, title, prompt):
    dialog = IntegerInputDialog(parent, title, prompt)
    return dialog.result
# Función para reproducir música
def reproducir_musica():
    pygame.mixer.music.load(
        "elementos/musica.mp3"
    )  # Asegúrate de que la música esté en el mismo directorio
    pygame.mixer.music.play(-1)  # Reproduce en bucle infinito (-1)
# Función para activar y desactivar la música
def toggle_musica():
    global musica_activa
    if musica_activa:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()
    musica_activa = not musica_activa
# Función para cargar un archivo CSV en memoria
def cargar_csv():
    global archivo_csv, tree, frame_tabla
    archivo_csv = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
    if archivo_csv:
        df = pd.read_csv(archivo_csv)  # Cargar el archivo CSV en un DataFrame de pandas
        etiqueta_csv.config(text=f"Archivo cargado: {archivo_csv.split('/')[-1]}")  # Mostrar el nombre del archivo en la etiqueta
        if frame_tabla is not None:
            frame_tabla.destroy()
        if boton_agregar_fila is not None:
            boton_agregar_fila.destroy()
        mostrar_csv(df)
# Función para cargar un CSV con solo las etiquetas de columna
def cargar_csv_vacio():
    global tree, frame_tabla
    # Crear DataFrame vacío con las columnas deseadas
    columnas = ["TR", "TA", "TI", "TAM(B)"]
    df = pd.DataFrame(columns=columnas)
    etiqueta_csv.config(text=f"Archivo creado")
    # Limpiar el contenido actual de la tabla, si existe
    if frame_tabla is not None:
        frame_tabla.destroy()
    if boton_agregar_fila is not None:
        boton_agregar_fila.destroy()
    # Mostrar el DataFrame vacío en la tabla
    mostrar_csv(df)
# Añadir una entrada en la tabla de procesos
def add_row():
    while True:
        ta = ask_integer(notebook, "Entrada", "Ingrese TA:")
        if ta is None:
            return  # Salir si se cancela

        ti = ask_integer(notebook, "Entrada", "Ingrese TI:")
        if ti is None:
            return  # Salir si se cancela

        tam_b = ask_integer(notebook, "Entrada", "Ingrese TAM(B):")
        if tam_b is None:
            return  # Salir si se cancela
        
        index = len(tree.get_children()) + 1
        # Insertar la fila si todos los datos son válidos
        tree.insert("", "end", values=[index, ta, ti, tam_b, "❌"])
        break  # Salir del bucle si todo se ingresó correctamente
# Borrar una entrada de la tabla de procesos
def delete_row(event):
    # Obtener la fila seleccionada
    selected_item = tree.selection()
    if selected_item:
        # Verificar si el clic fue en la columna de la casilla "❌" (última columna)
        col = tree.identify_column(event.x)  # Obtiene la columna bajo el clic
        if col == "#5":  # La columna con el índice 5 es la última, ajusta si es necesario
            tree.delete(selected_item)  # Eliminar la fila
            # Actualizar los índices de las filas restantes
            for idx, item in enumerate(tree.get_children()):
                tree.item(item, values=[idx+1] + list(tree.item(item, "values")[1:]))
# Función para mostrar el contenido del CSV en un Treeview con scrollbar
def mostrar_csv(df):
    global tree  # Asegurarnos de usar la variable global
    global frame_tabla 
    global boton_agregar_fila
    # Crear un frame para contener el Treeview y el scrollbar en tab1

    boton_agregar_fila = ttk.Button(tab1, text="Agregar un nuevo proceso", command=add_row)
    boton_agregar_fila.pack(side=tk.TOP, pady=10)

    frame_tabla = ttk.Frame(tab1)
    frame_tabla.pack(expand=True, fill="x", pady=10)

    # Crear un canvas para agregar desplazamiento
    canvas = tk.Canvas(frame_tabla, height = 400)
    canvas.pack(side=tk.RIGHT, fill="x", expand=True)

    # Crear un scrollbar para el canvas
    scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.LEFT, fill="y")

    # Configurar el canvas para usar el scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind_all("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

    # Crear un frame dentro del canvas para contener el Treeview
    frame_canvas = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=frame_canvas, anchor="nw")

    # Configurar el Treeview
    tree = ttk.Treeview(frame_canvas)
    tree["columns"] = list(df.columns) + [""]
    tree["show"] = "headings"

    # Configurar encabezados y anchos
    for col in df.columns:
        tree.heading(col, text=col)
        ancho_ventana = ventana.winfo_height()
        tree.column(col, width= int(ancho_ventana / (5/2)), anchor="center")

    # Agregar filas
    for _, row in df.iterrows():
        tree.insert("", "end", values=[*row, "❌"])

    # Función para ajustar el área de desplazamiento del canvas
    def ajustar_scrollregion(event=None):
        canvas.config(scrollregion=canvas.bbox("all"))

    # Asociar la función de ajuste al evento de configuración del tree y el canvas
    frame_canvas.bind("<Configure>", ajustar_scrollregion)
    ventana.bind("<Configure>", ajustar_scrollregion)  # Ajusta el scroll al redimensionar la ventana

    # Limitar altura del Treeview al 20% de la ventana
    altura_ventana = ventana.winfo_height()
    tree_height = int(altura_ventana * 0.2)
    tree.config(height=tree_height)

    # Colocar el Treeview en el frame_canvas
    tree.pack(fill="x", expand=True)

    # Asociar evento de clic en el Treeview
    tree.bind("<ButtonRelease-1>", delete_row)
# Función para obtener el tamaño de la ventana y ajustar la imagen
def ajustar_imagen(event=None):
    if ventana.winfo_width()>10 and ventana.winfo_height()>10:
        ancho_ventana = ventana.winfo_width()

        # Calcular el 20% del ancho de la ventana
        nuevo_ancho = int(ancho_ventana * 0.2)
        
        # Mantener la relación de aspecto de la imagen
        proporcion = imagen_original.width / imagen_original.height
        nuevo_alto = int(nuevo_ancho / proporcion)
        
        # Redimensionar la imagen original
        imagen_redimensionada = imagen_original.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)

        # Convertir la imagen redimensionada en un objeto PhotoImage compatible con Tkinter
        imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)

        # Actualizar la imagen en el label
        label_imagen.config(image=imagen_tk)
        label_imagen.image = imagen_tk  # Guardar una referencia para evitar que el garbage collector elimine la imagen
# Funciones para cambiar de pestaña
def cambiar_a_pestana_1():
    notebook.select(tab1)
def cambiar_a_pestana_2():
    global barra_desplazamiento
    notebook.select(tab2)
    barra_desplazamiento.focus_set()
def cambiar_a_pestana_3():
    notebook.select(tab3)
# Funciones para agregar las pestañas
def agregarboton_procesos():
    global pestanaProcesos  # Asegurarnos de usar la variable global
    if not (pestanaProcesos):
        boton2 = ttk.Button(control_frame, text="Procesos", command=cambiar_a_pestana_2)
        boton2.pack(side=tk.LEFT, expand=True, fill="x")
        pestanaProcesos = True
    for widget in tab2.winfo_children():
        widget.destroy()
    procesamientoProcesos()
    cambiar_a_pestana_2()
def agregarboton_stats():
    global pestanaStats
    if not (pestanaStats):
        boton4 = ttk.Button(control_frame, text="Estadísticas", command=cambiar_a_pestana_3)
        boton4.pack(side=tk.LEFT, expand=True, fill="x")
        pestanaStats = True
    for widget in tab3.winfo_children():
        widget.destroy()
# Empezar a tratar los procesos
def empezar_procesos():
    global historial, Memoria
    procesos_cargados = []
    historial = []
    if tree is not None:
        for item in tree.get_children():
            valores = tree.item(item, 'values')
            tr = valores[0]; ta = valores[1]; ti = valores[2]; tam_b = valores[3]
            exceso = 0
            for part in Memoria:
                if int(tam_b) > part.tamano:
                    exceso += 1
            if exceso != len(Memoria):
                proceso = Procesos(int(tr), int(ta), int(ti), int(tam_b))
                procesos_cargados.append(proceso)
        cpu = None

        # Listas
        procesos_nuevos = []
        procesos_listos = []
        procesos_terminados = []
        procesos_listos_y_en_suspension = []

        t = 0
        multiprogramacion = 5
        quantum = 3

        global calculadorTiempos
        calculadorTiempos = {}
        for proceso in procesos_cargados:
            calculadorTiempos[proceso] = {"tiempo_arribo": None, "tiempo_salida": None}

        while not all(proceso.estado == "terminado" for proceso in procesos_cargados):
            log = Log()
            for proceso in procesos_cargados: #Planificador a largo plazo
                if (proceso.ta == t):
                    procesos_nuevos.append(proceso)
            i = 0
            while (len(procesos_nuevos) > 0) and (i <= (len(procesos_nuevos) - 1)):
                procesonuevo = procesos_nuevos[i]
                for particion in sorted(Memoria, key=lambda particion: particion.tamano, reverse=True):
                    if particion.proceso_asignado is None and particion.tamano >= procesonuevo.tam_b:
                        particion.proceso_asignado = procesonuevo
                        procesos_nuevos.remove(procesonuevo)
                        procesos_listos.append(procesonuevo)
                        procesonuevo.estado = "listo"
                        procesonuevo.asignar_particion(particion)
                        multiprogramacion -= 1
                        if calculadorTiempos[procesonuevo]["tiempo_arribo"] is None:
                            calculadorTiempos[procesonuevo]["tiempo_arribo"] = t
                        break
                if procesonuevo.estado != "listo" and multiprogramacion != 0:
                    procesos_nuevos.remove(procesonuevo)
                    procesos_listos_y_en_suspension.append(procesonuevo)
                    procesonuevo.estado = "listo y suspendido"
                    multiprogramacion -= 1
                if procesonuevo.estado == "nuevo":
                    i += 1
            if (cpu is None) and (len(procesos_listos) != 0):
                cpu = procesos_listos.pop(0)
                cpu.estado = "ejecutando"
            if t == 0:
                log.agregar_procesos_nuevos(copy.deepcopy(procesos_nuevos))
                log.agregar_procesos_listos(copy.deepcopy(procesos_listos))
                log.agregar_procesos_listos_y_suspendidos(copy.deepcopy(procesos_listos_y_en_suspension))
                log.agregar_procesos_terminados(copy.deepcopy(procesos_terminados))
                log.cambiar_proceso_en_cpu(copy.deepcopy(cpu))
                for part in Memoria:
                    proc = part.proceso_asignado
                    if proc:
                        tamano = proc.tam_b
                    else:
                        tamano = 0
                    fragmentacion = part.tamano - tamano
                    log.setear_proceso_en_particion(copy.deepcopy(proc), copy.deepcopy(part.nombre), copy.deepcopy(tamano), copy.deepcopy(fragmentacion))
                historial.append(log)
                log = Log() #Hago otro log para que no se tome por referencia el mismo log y sobreescriba
            t += 1
            if cpu is not None: #Planificador a corto plazo
                cpu.tiempoEjecutado += 1
                if cpu.tiempoEjecutado == cpu.ti:
                    calculadorTiempos[cpu]["tiempo_salida"] = t
                    cpu.estado = "terminado"
                    procesos_terminados.append(cpu)
                    particionDeMemoria = cpu.obtener_particion()
                    particionDeMemoria.setProceso(None)
                    cpu = None
                    multiprogramacion += 1
                if (t)%quantum == 0 and cpu is not None: #Round Robin
                    cpu.estado = "listo"
                    procesos_listos.append(cpu)
                    cpu = None
                if cpu is None:
                    if len(procesos_listos)>0:
                        cpu = procesos_listos.pop(0)
                        cpu.estado = "ejecutando"
                    if (len(procesos_listos) < (len(Memoria) - 1)):
                        if len(procesos_listos_y_en_suspension)>0: #Planificador a mediano plazo
                            for procesolistoysusp in procesos_listos_y_en_suspension:
                                for particionMediano in sorted(Memoria, key=lambda particionMediano: particionMediano.tamano, reverse=True):
                                    if particionMediano.proceso_asignado is None and particionMediano.tamano >= procesolistoysusp.tam_b:
                                        particionMediano.proceso_asignado = procesolistoysusp
                                        procesolistoysusp.estado = "listo"
                                        procesolistoysusp.asignar_particion(particionMediano)
                                        procesos_listos_y_en_suspension.remove(procesolistoysusp)
                                        procesos_listos.append(procesolistoysusp)
                                        if calculadorTiempos[procesolistoysusp]["tiempo_arribo"] is None:
                                            calculadorTiempos[procesolistoysusp]["tiempo_arribo"] = t
                                        break
            log.agregar_procesos_nuevos(copy.deepcopy(procesos_nuevos))
            log.agregar_procesos_listos(copy.deepcopy(procesos_listos))
            log.agregar_procesos_listos_y_suspendidos(copy.deepcopy(procesos_listos_y_en_suspension))
            log.agregar_procesos_terminados(copy.deepcopy(procesos_terminados))
            log.cambiar_proceso_en_cpu(copy.deepcopy(cpu))
            for part in Memoria:
                proc = part.proceso_asignado
                if proc:
                    tamano = proc.tam_b
                else:
                    tamano = 0
                fragmentacion = part.tamano - tamano
                log.setear_proceso_en_particion(copy.deepcopy(proc), copy.deepcopy(part.nombre), copy.deepcopy(tamano), copy.deepcopy(fragmentacion))
            historial.append(log)
        agregarboton_procesos()
        procesarStats()
    else:
        etiqueta_csv.config(text=f"¡Cargar procesos!")


def procesamientoProcesos():
    global particionChiquita, particionMediana, particionGrande, historial
    def actualizar_variable(valor):
        # Actualiza la variable con el valor del Scale
        variable.set(f"Tiempo actual: {valor}")
        histActual = historial[int(valor)]
        # Los 4 valores entre 0 y 1 que definirán el relleno de los rectángulos
        valores = [1, 
                    (histActual.particiones["trabajos_grandes"]["tamano_proceso"]) / particionGrande.tamano, 
                    (histActual.particiones["trabajos_medianos"]["tamano_proceso"]) / particionMediana.tamano, 
                    (histActual.particiones["trabajos_chiquitos"]["tamano_proceso"]) / particionChiquita.tamano]
        procesos = ["Sistema Operativo", 
                    histActual.particiones["trabajos_grandes"]["nombre_proceso"], 
                    histActual.particiones["trabajos_medianos"]["nombre_proceso"], 
                    histActual.particiones["trabajos_chiquitos"]["nombre_proceso"]]
        fragmentacion = [
                    0,
                    histActual.particiones["trabajos_grandes"]["fragmentacion_interna"],
                    histActual.particiones["trabajos_medianos"]["fragmentacion_interna"],
                    histActual.particiones["trabajos_chiquitos"]["fragmentacion_interna"]]
        for widget in frameProcesado.winfo_children():
            widget.destroy()
        # Destruir los widgets existentes en el frame y dibujar los nuevos rectángulos
        dibujar_rectangulos(frameProcesado, valores, procesos, fragmentacion)
        mostrar_colas(frameProcesado, histActual)

    def mostrar_colas(frame, actual):
        # Crear un canvas dentro del frame
        canvas = tk.Canvas(frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Crear un subframe para organizar los widgets en el canvas
        subframe = tk.Frame(canvas)
        canvas.create_window((0, 0), window=subframe, anchor='nw')

        # Crear una etiqueta para cada lista y mostrar sus elementos
        etiquetas = [
            ("Procesos Nuevos", actual.procesosnuevos),
            ("Procesos Listos", actual.procesoslistos),
            ("Procesos Listos y Suspendidos", actual.procesoslistosysuspendidos),
            ("Procesos Terminados", actual.procesosterminados)
        ]

        for i, (titulo, lista) in enumerate(etiquetas):
            label_titulo = tk.Label(subframe, text=titulo, font=('Arial', 14, 'bold'))
            label_titulo.grid(row=i*2, column=0, sticky='w', padx=10, pady=(10, 0))

            listbox = tk.Listbox(subframe, height=len(lista), width=65)
            listbox.config(font=('Arial', 12))
            for item in lista:
                listbox.insert(tk.END, item)
            listbox.grid(row=i*2+1, column=0, sticky='w', padx=10)

        # Mostrar el proceso en CPU
        label_cpu = tk.Label(subframe, text="Proceso en CPU", font=('Arial', 14, 'bold'))
        label_cpu.grid(row=len(etiquetas) * 2, column=0, sticky='w', padx=10, pady=(10, 0))

        proceso_cpu = tk.Label(subframe, text=str(actual.procesoenCPU) if actual.procesoenCPU else "Ninguno", font=('Arial', 12))
        proceso_cpu.grid(row=len(etiquetas) * 2 + 1, column=0, sticky='w', padx=10)

        # Configurar el canvas para que permita desplazarse si el contenido es mayor al tamaño del canvas
        subframe.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def dibujar_rectangulos(frame, valores, procesos, fragmentacion):
        # Crear un canvas en el frame
        canvas = tk.Canvas(frame, width=600, height=450)
        canvas.pack(side= "left", anchor="nw")

        # Dimensiones del cuadrado
        lado = 400
        # La altura de cada rectángulo será 1/4 del lado del cuadrado
        altura_rectangulo = lado / 4

        # Asegúrate de que los valores estén entre 0 y 1
        valores = [max(0, min(1, v)) for v in valores]
        # Configuración del margen para el borde de cada rectángulo
        margen_borde = 5  # Grosor del borde negro
        tamaños_particiones = ["100K", "250K", "150K", "50K"]
        for i in range(4):
            # Altura del relleno
            altura_relleno = valores[i] * altura_rectangulo
            # Coordenadas del rectángulo negro externo (borde)
            y1_borde = lado - (i + 1) * altura_rectangulo
            y2_borde = y1_borde + altura_rectangulo
            # Dibujar el rectángulo negro para el borde
            canvas.create_rectangle(
                10, y1_borde, lado - 10, y2_borde, 
                outline="black", fill="black"
            )
            # Tratamiendo de texto en pantalla
            proceso = procesos[i]
            fragActual = fragmentacion[i] / 1000
            if i!=0:
                if proceso:
                    nombre = proceso.nombreProceso()
                    canvas.create_text(
                        lado + 10, (y1_borde + y2_borde) / 2,  # Offset de 10 píxeles a la derecha
                        text=f"{nombre}\nFragmentación: {fragActual}K", anchor="w", fill="blue"
                    )
                else:
                    canvas.create_text(
                        lado + 10, (y1_borde + y2_borde) / 2,  # Offset de 10 píxeles a la derecha
                        text=f"Vacío", anchor="w", fill="blue"
                    )

            else:
                canvas.create_text(
                    lado + 10, (y1_borde + y2_borde) / 2,  # Offset de 10 píxeles a la derecha
                    text="Sistema Operativos", anchor="w", fill="blue"
                )
            # Coordenadas del rectángulo interno blanco
            y1_interno = y1_borde + margen_borde
            # Dibujar el rectángulo blanco vacío
            canvas.create_rectangle(
                10 + margen_borde, y1_interno, 
                lado - 10 - margen_borde, y1_borde + altura_rectangulo - margen_borde, 
                outline="black", fill="white"
            )
            # Dibujar el rectángulo azul de relleno
            if valores[i] > 0.1:
                canvas.create_rectangle(
                    10 + margen_borde, y1_interno + (altura_rectangulo - altura_relleno - margen_borde), 
                    lado - 10 - margen_borde, y1_borde + altura_rectangulo - margen_borde, 
                    outline="black", fill="blue"
                )
            # Agregar el texto en el centro del cuadrado
            tamaño_particion = tamaños_particiones[i]
            canvas.create_text(
                (lado) / 2, 
                (y1_borde + y2_borde) / 2, 
                text=tamaño_particion, fill="black", font=("Arial", 12, "bold"))
    frameProcesado = tk.Frame(tab2)
    frameProcesado.pack(side = "top", anchor="nw",expand=True, fill="x", pady=10)
    frameDesplazamiento = tk.Frame(tab2)
    frameDesplazamiento.pack(side = "bottom", expand=True, fill="x", pady=10)
    # Crear una variable para mostrar el valor actual
    variable = tk.StringVar(value="Tiempo actual: 0")
    label_variable = tk.Label(frameDesplazamiento, textvariable=variable)
    label_variable.pack(side = "bottom", pady=10)
    # Crear el Scale de 0 a un valor máximo y que cambia el valor de la variable
    actualizar_variable(0)
    valor_maximo = len(historial) - 1  # Define el valor máximo de la barra
    global barra_desplazamiento
    barra_desplazamiento = tk.Scale(
        frameDesplazamiento, from_=0, to=valor_maximo, orient="horizontal", 
        command=actualizar_variable
    )
    barra_desplazamiento.pack(side="bottom", fill="x", padx=20, pady=20)
    barra_desplazamiento.focus_set()

def procesarStats():
    global calculadorTiempos, historial
    agregarboton_stats()
    promedioTiemposRetorno = 0
    promedioTiemposEspera = 0
    resultados = []
    for proceso, tiempos in calculadorTiempos.items():
        nombreProceso = proceso.nombreProceso()
        tiempo_retorno = tiempos["tiempo_salida"] - tiempos["tiempo_arribo"]
        promedioTiemposRetorno += tiempo_retorno
        tiempo_espera = tiempo_retorno - proceso.ti
        promedioTiemposEspera += tiempo_espera
        resultados.append((nombreProceso, tiempo_retorno, tiempo_espera))
    promedioTiemposRetorno /= len(calculadorTiempos)
    promedioTiemposEspera /= len(calculadorTiempos)
    rendimientoSistema = len(historial) / len(calculadorTiempos)

    style = ttk.Style(tab3)
    style.configure("Treeview.Heading", font=("Arial", 12, "bold"), anchor="center")  # Títulos en negrita y centrados
    style.configure("Treeview", font=("Arial", 11), rowheight=30)  # Filas más grandes y fuente más grande

    # Treeview para mostrar los tiempos de cada proceso
    tree = ttk.Treeview(tab3, columns=("Nombre proceso", "Tiempo Retorno", "Tiempo Espera"), show="headings", height=10)
    tree.heading("Nombre proceso", text="Nombre proceso")
    tree.heading("Tiempo Retorno", text="Tiempo Retorno")
    tree.heading("Tiempo Espera", text="Tiempo Espera")
    tree.column("Nombre proceso", anchor="center", width=200) # Centrar columnas
    tree.column("Tiempo Retorno", anchor="center", width=200)  
    tree.column("Tiempo Espera", anchor="center", width=200)

    # Insertar los datos de cada proceso
    for proceso, tiempo_retorno, tiempo_espera in resultados:
        tree.insert("", "end", values=(proceso, tiempo_retorno, tiempo_espera))

    tree.pack(pady=10)

    # Mostrar promedios y rendimiento
    promedio_retorno_label = tk.Label(tab3, text=f"Promedio Tiempo Retorno: {promedioTiemposRetorno:.2f}", font=("Arial", 12))
    promedio_retorno_label.pack(pady=5)
    promedio_retorno_label.config(anchor="center", justify="center")

    promedio_espera_label = tk.Label(tab3, text=f"Promedio Tiempo Espera: {promedioTiemposEspera:.2f}", font=("Arial", 12))
    promedio_espera_label.pack(pady=5)
    promedio_espera_label.config(anchor="center", justify="center")

    tk.Label(tab3, text=f"Rendimiento del Sistema", font=("Arial", 14, 'bold')).pack(pady=5)
    rendimiento_label = tk.Label(tab3, text=f"{rendimientoSistema:.2f} unidades de tiempo media por trabajo\n{(1/rendimientoSistema):.2f} trabajos por unidad de tiempo", font=("Arial", 12))
    rendimiento_label.pack(pady=5)
    rendimiento_label.config(anchor="center", justify="center")

    # Añadir un texto de créditos
    creditos_label = tk.Label(
        tab3,
        font=("Arial", 10, "italic"),
        fg="gray",
        text="Desarrollado por Miranda S.R.L.\nIntegrantes:\n•Cabral, Agustín\n•Castro, Mauricio\n•Cocito, Maximiliano\n•González, Matías\n•Miranda Pablo, Ulises\nSistemas Operativos 2024",
        )
    creditos_label.pack(side="bottom", pady=10)  # Colocar al final de la ventana


# Crear la ventana principal
ventana = tk.Tk()
ventana.title("MirandOS")
ventana.geometry("1280x720")
# Establecer tamaño de la ventana completa
ventana.state('zoomed')  # Hace que la ventana se abra maximizada
tamaño_ventana = [ventana.winfo_height(), ventana.winfo_width()]
# Crear el widget Notebook para las pestañas
notebook = ttk.Notebook(ventana)
# Crear los frames (contenedores) para cada pestaña
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
tab3 = ttk.Frame(notebook)
# Añadir las pestañas al Notebook
notebook.add(tab1)
notebook.add(tab2)
notebook.add(tab3)
# Crear un frame para los botones de control de pestañas
control_frame = ttk.Frame(notebook)
control_frame.pack(side=tk.TOP, fill="x")
# Crear botones para cambiar entre las pestañas
boton1 = ttk.Button(control_frame, text="Inicio", command=cambiar_a_pestana_1)
boton1.pack(side=tk.LEFT, expand=True, fill="x")
# Empaquetar el Notebook para que llene toda la ventana
notebook.pack(expand=True, fill="both")
# Añadir imagen a la pestaña 1
imagen_original = Image.open("elementos/logotipo.png")
# Crear un widget Label que contenga la imagen
label_imagen = tk.Label(tab1)
label_imagen.pack(pady=10, padx=20, anchor=tk.N, expand=False)
# Cargar la imagen para el botón
imagen_boton = Image.open(
    "elementos/boton_musica.png"
)  # Asegúrate de que la imagen esté en el directorio
imagen_boton = imagen_boton.resize((20, 20), Image.LANCZOS)  # Redimensionar la imagen si es necesario
imagen_boton_tk = ImageTk.PhotoImage(imagen_boton)
# Botón para activar/desactivar la música usando una imagen
boton_musica = ttk.Button(ventana, image=imagen_boton_tk, command=toggle_musica)
boton_musica.image = imagen_boton_tk  # Guardar referencia para evitar que la imagen sea recolectada
boton_musica.pack(side=tk.BOTTOM, anchor=tk.SE, padx=5, pady=5)
# Etiqueta para mostrar el estado del archivo CSV cargado
etiqueta_csv = tk.Label(tab1, text="Ningún archivo CSV cargado", font=("Arial", 12))
etiqueta_csv.pack(side=tk.TOP, pady=10)
# Crear un Frame para los botones
frame_botones = tk.Frame(tab1)
frame_botones.pack(pady=10)
# Botón para cargar el archivo CSV
boton_cargar_csv = ttk.Button(frame_botones, text="Cargar CSV", command=cargar_csv)
boton_cargar_csv.pack(side=tk.RIGHT, pady=10)
boton_cargar_csv_vacio = ttk.Button(frame_botones, text="CSV desde 0", command=cargar_csv_vacio)
boton_cargar_csv_vacio.pack(side=tk.LEFT, pady=10)
boton_empezar_proceso = ttk.Button(tab1, text="Empezar proceso", command = empezar_procesos)
boton_empezar_proceso.pack(side=tk.BOTTOM, pady=10)
# Ajustar la imagen al iniciar la ventana
ventana.after(500, ajustar_imagen)  # Llama a la función ajustar_imagen después de 500 ms
# Asociar el evento de redimensionamiento de la ventana a la función de ajuste de altura
ventana.bind("<Configure>", ajustar_imagen)
# Reproducir música al iniciar la ventana
reproducir_musica()
# Ejecutar la ventana principal
ventana.mainloop()
