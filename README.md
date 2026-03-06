[![Consultar a DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/MauricioCastro16/NombreRepo)

# MirandOS - Simulador de Procesos

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://python.org)
[![Tkinter](https://img.shields.io/badge/Tkinter-GUI-orange.svg)](https://docs.python.org/3/library/tkinter.html)

Simulador educativo de sistemas operativos que implementa algoritmos de planificación Round Robin y gestión de memoria con particiones fijas. Permite visualizar en tiempo real la ejecución de procesos y el estado de la memoria del sistema.

## Características Principales

- Planificación de CPU mediante algoritmo Round Robin con quantum configurable
- Gestión de memoria con particiones fijas (50KB, 150KB, 250KB)
- Visualización gráfica del estado de memoria y colas de procesos
- Interfaz intuitiva con pestañas para entrada de datos, simulación y estadísticas
- Carga de procesos desde archivos CSV o ingreso manual
- Cálculo automático de métricas: tiempo de retorno, tiempo de espera y throughput

## Stack Tecnológico

| Categoría | Tecnología |
|-----------|------------|
| Frontend | Tkinter, PIL (Python Imaging Library) |
| Backend | Python 3.x |
| Herramientas | Pandas, Pygame, PyInstaller |

## Arquitectura

La aplicación sigue un modelo monolítico donde el motor de simulación interactúa directamente con la interfaz gráfica. El ciclo principal de simulación actualiza el estado de procesos y memoria en cada tick de reloj, almacenando snapshots en un historial para permitir navegación temporal. La gestión de memoria se realiza mediante tres particiones fijas con seguimiento de fragmentación interna.

## Instalación y Uso

```bash
# Clonar el repositorio
git clone https://github.com/MauricioCastro16/Sistemas-Operativos---Grupo-Miranda.git
cd Sistemas-Operativos---Grupo-Miranda

# Instalar dependencias
pip install tkinter pillow pygame pandas

# Ejecutar la aplicación
python SimuladorProcesos.py
```
