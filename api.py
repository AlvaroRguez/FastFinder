from flask import Flask, jsonify, request, abort
import os
import configparser
from app import IndexWorker, SearchWorker
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

# 1) Definición del fichero de config
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")

# 2) Carga y validación de la sección Paths
_cfg = configparser.ConfigParser()
_cfg.read(CONFIG_FILE)
if 'Paths' not in _cfg:
    raise RuntimeError("Sección [Paths] ausente en config.ini")
_paths = _cfg['Paths']

# Lista de claves obligatorias
_required = [
    'github_prefix', 'gitlab_prefix',
    'github_base_url', 'gitlab_base_url',
    'github_branch', 'gitlab_branch'
]
for key in _required:
    if key not in _paths:
        raise RuntimeError(f"Clave obligatoria '{key}' ausente en sección [Paths]")

app = Flask(__name__)
CORS(app)

def transform_path_to_url(path: str) -> str:
    # Normaliza separadores
    path = path.replace('\\', '/')

    # EXTRAEMOS sin fallback, así KeyError si falta
    gpref   = _paths['github_prefix']
    lpref   = _paths['gitlab_prefix']
    gbase   = _paths['github_base_url']
    lbase   = _paths['gitlab_base_url']
    gbranch = _paths['github_branch']
    lbranch = _paths['gitlab_branch']

    if path.startswith(gpref):
        rel             = path[len(gpref):]
        project, repo, *rest = rel.split('/', 2)
        tail            = rest[0] if rest else ''
        return f"{gbase}/{project}/{repo}/blob/{gbranch}/{tail}"

    if path.startswith(lpref):
        rel             = path[len(lpref):]
        project, doc, *rest = rel.split('/', 2)
        tail            = rest[0] if rest else ''
        return f"{lbase}/{project}/{doc}/-/blob/{lbranch}/{tail}"

    return path

@app.route('/index', methods=['POST'])
def index_files():
    # (igual que antes; carga Settings y dispara IndexWorker)
    indexdir  = 'indexdir'
    cfg       = configparser.ConfigParser()
    folders   = []
    extensions= []
    if os.path.exists(CONFIG_FILE):
        cfg.read(CONFIG_FILE)
        if 'Settings' in cfg:
            raw = cfg['Settings'].get('folders', '').strip()
            folders = [p for p in raw.split(';') if p]
            raw_ext = cfg['Settings'].get('extensions','').strip()
            extensions = [e.strip() for e in raw_ext.split(';') if e.strip()]

    idx_worker = IndexWorker(folders, extensions, indexdir)
    idx_worker.run()
    return jsonify({'status': 'Indexing completed'}), 200

@app.route('/search', methods=['GET'])
def search_files():
    query     = request.args.get('query', '').strip()
    transform = request.args.get('transform', 'false').lower() in ('1', 'true', 'yes')

    if not query:
        return jsonify({'error': "El parámetro 'query' es obligatorio"}), 400

    indexdir = 'indexdir'
    if not os.path.isdir(indexdir):
        return jsonify({'error': "Índice no encontrado, ejecuta /index primero"}), 500

    try:
        idx = open_dir(indexdir)
    except Exception as e:
        return jsonify({'error': f"No se pudo abrir el índice: {e}"}), 500

    # Construimos y ejecutamos la consulta
    qp    = QueryParser("content", schema=idx.schema)
    q     = qp.parse(query)
    resultados = []

    try:
        with idx.searcher() as searcher:
            hits = searcher.search(q, limit=None)
            for hit in hits:
                path = hit['path']
                try:
                    with open(path, 'r', encoding='utf8') as f:
                        for num, linea in enumerate(f, start=1):
                            if query.lower() in linea.lower():
                                resultados.append((path, num, linea.rstrip()))
                except Exception:
                    # Si falla leer un fichero, lo omitimos
                    continue
    except Exception as e:
        return jsonify({'error': f"Error durante la búsqueda: {e}"}), 500

    # Aplicamos transformación opcional de rutas
    if transform:
        payload = [
            [transform_path_to_url(path), line, code]
            for path, line, code in resultados
        ]
    else:
        payload = [
            [path, line, code]
            for path, line, code in resultados
        ]

    return jsonify({'results': payload}), 200

# Swagger UI setup (sin cambios)
SWAGGER_URL = '/swagger'
API_URL     = '/static/swagger.json'
swaggerui_bp = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL,
    config={'app_name': "FastFinder API"}
)
app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(debug=True)
