# FastFinder

FastFinder es una herramienta de búsqueda de texto en archivos que permite indexar y buscar contenido rápidamente en múltiples carpetas y tipos de archivo. Combina una interfaz gráfica de usuario (GUI) con PyQt5 y un backend de búsqueda potente basado en Whoosh.

## Características principales

- **Búsqueda rápida**: Indexación de contenido para búsquedas instantáneas
- **Múltiples formatos**: Soporte para una amplia variedad de extensiones de archivo
- **Interfaz dual**: Disponible como aplicación de escritorio y API web
- **Integración con repositorios**: Transformación de rutas a URLs de GitHub y GitLab
- **Interfaz gráfica intuitiva**: Fácil de usar para usuarios no técnicos

## Requisitos previos

- Python 3.6 o superior
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clona este repositorio o descarga los archivos
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Estructura del proyecto

- `app.py`: Aplicación de escritorio con interfaz gráfica PyQt5
- `api.py`: API REST con Flask para acceso mediante HTTP
- `config.ini`: Archivo de configuración para carpetas, extensiones y rutas de repositorios
- `requirements.txt`: Dependencias del proyecto
- `static/`: Archivos estáticos para la API web
- `indexdir/`: Directorio donde se almacena el índice de búsqueda (creado automáticamente)

## Configuración

Edita el archivo `config.ini` para personalizar:

```ini
[Settings]
folders = ruta/a/carpeta1;ruta/a/carpeta2
extensions = .py;.js;.html;.css;.md;.txt

[Paths]
github_prefix = ruta/a/repositorios/github/
gitlab_prefix = ruta/a/repositorios/gitlab/
github_base_url = https://github.com
gitlab_base_url = https://gitlab.example.com
github_branch = main
gitlab_branch = master
```

## Uso de la aplicación de escritorio

1. Ejecuta la aplicación:

```bash
python app.py
```

2. Configura las carpetas a indexar usando el botón "Seleccionar carpetas"
3. Configura las extensiones de archivo a incluir
4. Haz clic en "Indexar" para crear el índice de búsqueda
5. Introduce el texto a buscar y haz clic en "Buscar"
6. Los resultados mostrarán la ruta del archivo, número de línea y el contenido encontrado
7. Haz clic derecho en un resultado para abrir el archivo o copiar la ruta

## Uso de la API REST

1. Inicia el servidor API:

```bash
python api.py
```

2. Endpoints disponibles:

- **POST /index**: Inicia el proceso de indexación
  ```bash
  curl -X POST http://localhost:5000/index
  ```

- **GET /search?query=texto**: Busca el texto en los archivos indexados
  ```bash
  curl http://localhost:5000/search?query=ejemplo
  ```

- **GET /search?query=texto&transform=true**: Busca y transforma las rutas a URLs de repositorios
  ```bash
  curl http://localhost:5000/search?query=ejemplo&transform=true
  ```

## Clases principales

### IndexWorker
Maneja la indexación de archivos en segundo plano, recorriendo las carpetas configuradas y procesando los archivos con las extensiones especificadas.

### SearchWorker
Realiza búsquedas en el índice y encuentra coincidencias exactas en los archivos, devolviendo la ruta, número de línea y el contenido encontrado.

## Contribución

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Haz push a la rama (`git push origin nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está disponible como software de código abierto. Si deseas utilizar este código, por favor considera añadir una licencia apropiada como MIT, GPL o Apache 2.0.