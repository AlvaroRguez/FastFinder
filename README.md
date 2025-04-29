# FastFinder

FastFinder es una aplicación de búsqueda de texto desarrollada en Python utilizando PyQt5 para la interfaz gráfica y Whoosh como motor de búsqueda.

## Funcionalidades

- Búsqueda de texto en múltiples archivos
- Soporte para múltiples extensiones de archivo
- Indexación de contenido para búsquedas rápidas
- Interfaz gráfica intuitiva

## Requisitos

- Python 3.8 o superior
- PyQt5
- Whoosh

## Instalación

1. Clona el repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```
3. Ejecuta la aplicación:
```bash
python app.py
```

## Diagrama de flujo

```mermaid
graph TD
    A[Inicio] --> B[Seleccionar carpetas]
    B --> C{¿Carpetas válidas?}
    C -->|Sí| D[Configurar extensiones]
    C -->|No| B
    D --> E[Indexar contenido]
    E --> F{¿Índice creado?}
    F -->|Sí| G[Introducir término de búsqueda]
    F -->|No| E
    G --> H[Buscar en índice]
    H --> I{¿Resultados encontrados?}
    I -->|Sí| J[Mostrar resultados]
    I -->|No| G
    J --> K[Fin]
```

## Uso

1. Selecciona las carpetas a indexar
2. Configura las extensiones de archivo
3. Indexa el contenido
4. Realiza búsquedas de texto

## Contribución

¡Las contribuciones son bienvenidas! Por favor, abre un issue o envía un pull request.

## Licencia

MIT