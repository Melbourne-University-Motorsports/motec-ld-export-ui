from PyQt6.QtCore import QThread, pyqtSignal
from backend.processor import MotecProcessor
import os
import traceback

class ExportWorker(QThread):
    progress_update = pyqtSignal(int, int) # current, total
    log_message = pyqtSignal(str)
    finished_all = pyqtSignal()
    
    def __init__(self, files, output_dir, split_enabled):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.split_enabled = split_enabled
        self.processor = MotecProcessor()
        self._is_running = True

    def run(self):
        total = len(self.files)
        self.log_message.emit(f"Starting export of {total} files...")
        
        count = 0
        for i, filepath in enumerate(self.files):
            if not self._is_running:
                break
                
            fname = os.path.basename(filepath)
            self.log_message.emit(f"Processing {fname}...")
            
            try:
                created = self.processor.process_file(
                    filepath, 
                    self.output_dir, 
                    enable_splitting=self.split_enabled
                )
                self.log_message.emit(f"  -> Exported {len(created)} CSVs.")
            except Exception as e:
                self.log_message.emit(f"  [ERROR] Failed {fname}: {str(e)}")
                traceback.print_exc()
            
            count += 1
            self.progress_update.emit(count, total)
            
        self.log_message.emit("Export job completed.")
        self.finished_all.emit()

    def stop(self):
        self._is_running = False

class ScanWorker(QThread):
    """Worker to scan files for the tree preview."""
    file_scanned = pyqtSignal(dict) # Returns dict from processor.scan_file
    finished_scan = pyqtSignal()
    
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.processor = MotecProcessor()
        self._is_running = True
        
    def run(self):
        for filepath in self.files:
            if not self._is_running: break
            try:
                result = self.processor.scan_file(filepath)
                self.file_scanned.emit(result)
            except Exception:
                pass # Ignore failed scans for preview
        self.finished_scan.emit()
        
    def stop(self):
        self._is_running = False
