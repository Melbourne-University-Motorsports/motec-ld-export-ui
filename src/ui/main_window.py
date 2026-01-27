import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QFileDialog, QLabel, QCheckBox, 
    QGroupBox, QProgressBar, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from .worker import ExportWorker, ScanWorker
from .header import HeaderWidget
from .throbber import PulseThrobber
from backend.processor import MotecProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MoTeC Export UI")
        self.resize(1000, 600)
        self.worker = None
        self.scan_worker = None
        self.processor_helper = MotecProcessor()
        self.added_paths = set()
        self.preview_seen_names = set()

        # Default Output Path: ./out
        self.local_path = os.path.join(os.getcwd(), 'out')

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # Clean edges
        main_layout.setSpacing(0)

        # 1. Header
        # Calculate updated path for image relative to this file
        # src/ui/main_window.py -> src/assets/logo.png
        import sys
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = sys._MEIPASS
            # Assets were added to root 'assets' folder in the bundle
            logo_path = os.path.join(base_dir, 'assets', 'logo.png')
            throbber_path = os.path.join(base_dir, 'assets', 'throbber.png')
        else:
            # Running as source
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(base_dir, 'assets', 'logo.png')
            throbber_path = os.path.join(base_dir, 'assets', 'throbber.png')
        
        self.header = HeaderWidget(logo_path=logo_path)
        main_layout.addWidget(self.header, stretch=0)

        # 2. Splitter for Left/Right design (Input Files | Preview Tree)
        # We wrap this in a widget to add margins if we want
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT PANE: Input Files ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        grp_files = QGroupBox("Drop Files Here")
        file_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(True)
        self.file_list.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.file_list.dragEnterEvent = self.dragEnterEvent
        self.file_list.dragMoveEvent = self.dragMoveEvent
        self.file_list.dropEvent = self.dropEvent
        
        file_layout.addWidget(self.file_list)
        
        btn_bar = QHBoxLayout()
        self.btn_add = QPushButton("Add Files")
        self.btn_add.clicked.connect(self.add_files)
        # Extend upload area downwards -> less buttons clutter? 
        # Actually user asked to extend upload and previous boxes lower. 
        # The splitter naturally takes available space. We just ensure we don't fix height.
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_all)
        btn_bar.addWidget(self.btn_add)
        btn_bar.addWidget(self.btn_clear)
        file_layout.addLayout(btn_bar)
        
        grp_files.setLayout(file_layout)
        left_layout.addWidget(grp_files)
        
        # --- RIGHT PANE: Preview Tree ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        grp_preview = QGroupBox("Export Preview (Splits)")
        prev_layout = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File / Run", "Duration", "Details"])
        self.tree.setColumnWidth(0, 200)
        prev_layout.addWidget(self.tree)
        
        # Throbber below tree
        self.throbber = PulseThrobber(throbber_path)
        prev_layout.addWidget(self.throbber)
        
        grp_preview.setLayout(prev_layout)
        right_layout.addWidget(grp_preview)
        
        # --- RIGHTMOST PANE: Output Files Preview ---
        right_most_widget = QWidget()
        right_most_layout = QVBoxLayout(right_most_widget)
        right_most_layout.setContentsMargins(0, 0, 0, 0)

        grp_preview_files = QGroupBox("Output Files")
        preview_files_layout = QVBoxLayout()
        
        self.preview_list = QListWidget()
        preview_files_layout.addWidget(self.preview_list)
        
        grp_preview_files.setLayout(preview_files_layout)
        right_most_layout.addWidget(grp_preview_files)

        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.addWidget(right_most_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        content_layout.addWidget(splitter)
        
        # --- CONTROL BAR (Output Path, Options, Export) ---
        # Moving this below the splitter, inside content area
        bottom_layout = QHBoxLayout()
        
        # Output Path
        # Display shortened path for UI cleanliness, or full? Let's show full for clarity but handle long string?
        self.lbl_output = QLabel(f"<b>Output:</b> {self.local_path}")
        self.lbl_output.setWordWrap(True) # Just in case
        btn_dest = QPushButton("Change")
        btn_dest.clicked.connect(self.select_output)
        
        bottom_layout.addWidget(self.lbl_output, stretch=1)
        bottom_layout.addWidget(btn_dest)
        
        # Split Checkbox
        self.chk_split = QCheckBox("Auto-split runs")
        self.chk_split.setChecked(True)
        bottom_layout.addWidget(self.chk_split)
        
        # Export Button
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setMinimumWidth(120)
        self.btn_export.setStyleSheet("font-weight: bold; padding: 5px;")
        self.btn_export.clicked.connect(self.start_export)
        bottom_layout.addWidget(self.btn_export)
        
        content_layout.addLayout(bottom_layout)
        main_layout.addWidget(content_widget, stretch=1)

        # 3. Status Bar (Compact)
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(200) # Keep it small
        self.progress.setVisible(False) # Hide by default
        self.status_bar.addPermanentWidget(self.progress)

    # --- Drag & Drop ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) and path.lower().endswith('.ld'):
                files.append(path)
        self.process_added_files(files)

    # --- Logic ---
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MoTeC Files", "", "MoTeC Data (*.ld)"
        )
        if files:
            self.process_added_files(files)

    def process_added_files(self, paths):
        new_files = []
        for p in paths:
            if p not in self.added_paths:
                self.added_paths.add(p)
                self.file_list.addItem(os.path.basename(p))
                new_files.append(p)
        
        if new_files:
            # Trigger background scan for tree
            self.start_scan(new_files)

    def clear_all(self):
        self.file_list.clear()
        self.tree.clear()
        self.preview_list.clear()
        self.added_paths.clear()
        self.preview_seen_names.clear()

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.local_path = folder
            self.lbl_output.setText(f"<b>Output:</b> {folder}")

    # --- Scanning for Preview ---
    def start_scan(self, files):
        self.throbber.start()
        self.status_label.setText("Scanning files for runs...")
        self.progress.setRange(0, 0) # Indeterminate
        self.progress.setVisible(True)
        
        self.scan_worker = ScanWorker(files)
        self.scan_worker.file_scanned.connect(self.update_tree)
        self.scan_worker.finished_scan.connect(self.scan_finished)
        self.scan_worker.start()

    def update_tree(self, data):
        # data = {filepath, comment, runs: [{duration, start, end}]}
        fname = os.path.basename(data['filepath'])
        runs = data['runs']
        
        root = QTreeWidgetItem(self.tree)
        root.setText(0, fname)
        root.setText(2, data['metadata'].get('comment', ''))
        
        for i, r in enumerate(runs):
            child = QTreeWidgetItem(root)
            child.setText(0, f"Run {i+1}")
            child.setText(1, f"{r['duration']:.2f} s")
            child.setText(2, f"Start: {r['start']:.2f}s, End: {r['end']:.2f}s")
            
        self.tree.expandItem(root)

        # Update Preview List
        # Track names to handle duplicates in preview
        for r in runs:
            # Try to find a unique name
            duration = r['duration']
            metadata = data['metadata']
            
            # Helper generates default name (count=0)
            candidate = self.processor_helper.get_output_filename(metadata, duration, 0)
            
            if candidate in self.preview_seen_names:
                # Collision detected
                k = 1
                while True:
                    candidate = self.processor_helper.get_output_filename(metadata, duration, k)
                    if candidate not in self.preview_seen_names:
                        break
                    k += 1
            
            self.preview_seen_names.add(candidate)
            self.preview_list.addItem(candidate)

    def scan_finished(self):
        self.throbber.stop()
        self.status_label.setText("Ready.")
        self.progress.setVisible(False)
        self.progress.setRange(0, 100) # Reset to normal

    # --- Exporting ---
    def start_export(self):
        files = list(self.added_paths)
        if not files:
            QMessageBox.warning(self, "No Files", "Please add .ld files first.")
            return

        # Ensure output directory exists!!!
        try:
            os.makedirs(self.local_path, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not create output directory: {e}")
            return

        self.btn_export.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status_label.setText("Exporting...")
        
        self.worker = ExportWorker(files, self.local_path, self.chk_split.isChecked())
        self.worker.progress_update.connect(self.update_progress)
        self.worker.log_message.connect(self.log_msg)
        self.worker.finished_all.connect(self.export_finished)
        self.worker.start()

    def update_progress(self, current, total):
        pct = int((current / total) * 100)
        self.progress.setValue(pct)

    def log_msg(self, msg):
        self.status_label.setText(msg)

    def export_finished(self):
        self.btn_export.setEnabled(True)
        self.status_label.setText("Export Complete.")
        self.progress.setVisible(False)
        QMessageBox.information(self, "Done", "Export finished successfully.")
