import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QInputDialog, QListWidgetItem,
    QFileDialog, QLineEdit, QListWidget, QLabel, QFileDialog, QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QMenu

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import configparser

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.ini")

class IndexWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folders, extensions, indexdir):
        super().__init__()
        self.folders = folders
        self.extensions = extensions
        self.indexdir = indexdir
    def run(self):
        # Create index (or open existing)
        if not os.path.exists(self.indexdir):
            os.mkdir(self.indexdir)
            schema = Schema(path=ID(stored=True), content=TEXT(stored=True))
            idx = create_in(self.indexdir, schema)
        else:
            idx = open_dir(self.indexdir)

        writer = idx.writer()
        for folder in self.folders:
            for root, _, files in os.walk(folder):
                for f in files:
                    if any(f.lower().endswith(ext) for ext in self.extensions):
                        path = os.path.join(root, f)
                        try:
                            text = open(path, 'r', encoding='utf8').read()
                            writer.update_document(path=path, content=text)
                            self.progress.emit(f"Indexado: {path}")
                        except Exception as e:
                            self.progress.emit(f"Error leyendo {path}: {e}")
        writer.commit()
        self.finished.emit()

class SearchWorker(QThread):
    results = pyqtSignal(list)
    progress = pyqtSignal(str)

    def __init__(self, query_text, indexdir):
        super().__init__()
        self.query_text = query_text.lower()
        self.indexdir  = indexdir

    def run(self):
        idx = open_dir(self.indexdir)
        qp  = QueryParser("content", schema=idx.schema)
        q   = qp.parse(self.query_text)

        resultados = []
        with idx.searcher() as searcher:
            hits = searcher.search(q, limit=None)
            total = len(hits)
            for i, hit in enumerate(hits):
                path = hit['path']
                self.progress.emit(f"Procesando {i+1} de {total}: {path}")
                try:
                    with open(path, 'r', encoding='utf8') as f:
                        for num, linea in enumerate(f, start=1):
                            if self.query_text in linea.lower():
                                snippet = linea.rstrip()
                                resultados.append((path, num, snippet))
                                # break    # descomenta si quieres solo 1 línea / fichero
                except Exception:
                    continue

        self.results.emit(resultados)

class MainWindow(QWidget):
    MAX_LABEL_CHARS = 50

    def elide_text(self, text: str) -> str:
        """Returns text truncated to MAX_LABEL_CHARS, with '...' if necessary."""
        maxc = self.MAX_LABEL_CHARS
        if len(text) <= maxc:
            return text
        return text[: maxc - 3] + "..."

    def update_labels(self):
        # Folder(s)
        folders_str = "; ".join(self.folders)
        self.lbl_folders.setText("Folders: " + self.elide_text(folders_str))
        # Extensions
        ext_str = "; ".join(self.extensions)
        self.lbl_ext.setText("Extensions: " + self.elide_text(ext_str))

    def __init__(self):
        super().__init__()
        # Stores the last raw text
        self._last_status = ""
        # Widgets
        self.lbl_status = QLabel()
        # Forces the label to maintain its minimum height and width
        self.lbl_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setWindowTitle("Buscador de texto")
        self.resize(600,400)

        self.folders = []
        self.extensions = ['.txt','.md','.cs','.vb','.pas']
        self.indexdir = "indexdir"

        # Widgets
        self.btn_add = QPushButton("Add folder...")
        self.lbl_folders = QLabel("Folders: (none)")
        self.btn_index = QPushButton("Index")
        self.line_search = QLineEdit()
        self.btn_search = QPushButton("Search")

        # Create a horizontal layout for the search bar
        h = QHBoxLayout()
        h.addWidget(self.line_search)
        h.addWidget(self.btn_search)
        self.list_results = QListWidget()
        self.lbl_status = QLabel()
        self.btn_config_ext = QPushButton("Configure extensions…")
        self.lbl_ext = QLabel("Extensions: (none)")

        # Load configuration
        self.load_config()

        # Layout
        v = QVBoxLayout(self)
        v.addWidget(self.btn_add)
        v.addWidget(self.lbl_folders)
        v.addWidget(self.btn_index)
        v.addWidget(self.lbl_status)
        v.addWidget(self.btn_config_ext)
        v.addWidget(self.lbl_ext)
        v.addWidget(QLabel("Buscar:"))
        v.addLayout(h)
        v.addWidget(self.list_results)

        # Connections
        self.btn_add.clicked.connect(self.add_folder)
        self.btn_index.clicked.connect(self.start_index)
        self.line_search.returnPressed.connect(self.start_search)
        self.btn_search.clicked.connect(self.start_search)
        self.btn_config_ext.clicked.connect(self.configure_extensions)
        self.list_results.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_results.customContextMenuRequested.connect(self.on_context_menu)

    def add_folder(self):
        dialog = QFileDialog(self, "Selecciona carpetas")
        dialog.setFileMode(QFileDialog.FileMode.Directory)               # solo directorios
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)   # usa el QT “no nativo”
        if dialog.exec_():
            nuevos = dialog.selectedFiles()  # aquí sí puedes Ctrl+clic multis
            for ruta in nuevos:
                if ruta not in self.folders:
                    self.folders.append(ruta)
            self.update_labels()
            self.save_config()

    def start_index(self):
        self.btn_index.setEnabled(False)
        self.lbl_status.setText("Indexando...")
        self.idx_worker = IndexWorker(self.folders, self.extensions, self.indexdir)
        self.idx_worker.progress.connect(self.on_index_progress)
        self.idx_worker.finished.connect(self.on_index_finished)
        self.idx_worker.start()

    def on_index_progress(self, full_text: str):
        # Store the complete text to re-elide if resized
        self._last_status = full_text
        # Calculate available width
        avail_w = self.lbl_status.width()
        # Get left-truncated text if it exceeds
        fm = QFontMetrics(self.lbl_status.font())
        elided = fm.elidedText(full_text, Qt.ElideLeft, avail_w)
        self.lbl_status.setText(elided)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Every time the size changes, we re-elide
        if self._last_status:
            self.on_index_progress(self._last_status)

    def on_index_finished(self):
        self.lbl_status.setText("Indexación completada.")
        self.btn_index.setEnabled(True)

    def start_search(self):
        query = self.line_search.text().strip()
        if not query: return
        self.list_results.clear()
        self.search_worker = SearchWorker(query, self.indexdir)
        self.search_worker.results.connect(self.show_results)
        self.search_worker.progress.connect(self.lbl_status.setText)
        self.lbl_status.setText("Searching...")
        self.search_worker.start()

    def show_results(self, resultados):
        self.list_results.clear()
        if not resultados:
            self.lbl_status.setText("No results found.")
            return
        
        for path, lineno, snippet in resultados:
            display = f"{os.path.basename(path)} (line {lineno}): {snippet}"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, path)      # store the real path
            self.list_results.addItem(item)
        self.lbl_status.setText("Search completed.")

    def on_item_clicked(self, item: QListWidgetItem):
        path   = item.data(Qt.UserRole)
        folder = os.path.dirname(path)
        question = QMessageBox.question(
            self,
            "Open Folder",
            f"Do you want to open the folder?\n{folder}",
            QMessageBox.Yes | QMessageBox.No
        )
        if pregunta == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def on_context_menu(self, pos: QPoint):
        item = self.list_results.itemAt(pos)
        if not item:
            return
        path = item.data(Qt.UserRole)
        folder = os.path.dirname(path)

        menu = QMenu(self)
        action = menu.addAction("Abrir carpeta")
        action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(folder)))
        global_pos = self.list_results.mapToGlobal(pos)
        menu.exec_(global_pos)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            if 'Settings' in config:
                raw = config['Settings'].get('folders','').strip()
                self.folders = [p for p in raw.split(';') if p]
                raw_ext = config['Settings'].get('extensions','').strip()
                self.extensions = [e.strip() for e in raw_ext.split(';') if e.strip()]
        self.update_labels()

    def save_config(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'folders': ';'.join(self.folders),
            'extensions': ';'.join(self.extensions)
        }
        with open(CONFIG_FILE, 'w', encoding='utf8') as f:
            config.write(f)

    def configure_extensions(self):
        text, ok = QInputDialog.getText(
            self,
            "Extensions to Index",
            "Enter extensions (separated by semicolons):",
            text=";".join(self.extensions)
        )
        if ok:
            exts = [e.strip() for e in text.split(';') if e.strip()]
            self.extensions = [
                e if e.startswith('.') else f'.{e}'
                for e in exts
            ]
            self.update_labels()
            self.save_config()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
