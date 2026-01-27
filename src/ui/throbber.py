from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap

class PulseThrobber(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.original_pixmap = QPixmap(image_path)
        self.current_scale = 1.0
        self.growing = True
        
        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_step)
        
        # Initial display
        self.update_display()
        self.hide() # Hidden by default
        
    def start(self):
        self.current_scale = 1.0
        self.growing = True
        self.show()
        self.timer.start(50) 
        
    def stop(self):
        self.timer.stop()
        self.hide()
        
    def _animate_step(self):
        if self.original_pixmap.isNull():
            return
            
        # Pulse logic
        step = 0.05
        min_scale = 0.8
        max_scale = 1.2
        
        if self.growing:
            self.current_scale += step
            if self.current_scale >= max_scale:
                self.current_scale = max_scale
                self.growing = False
        else:
            self.current_scale -= step
            if self.current_scale <= min_scale:
                self.current_scale = min_scale
                self.growing = True
                
        self.update_display()
        
    def update_display(self):
        if self.original_pixmap.isNull():
            return
            
        # Base size e.g. 50px
        base_h = 50
        target_h = int(base_h * self.current_scale)
        
        scaled = self.original_pixmap.scaledToHeight(target_h, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled)
        # Ensure widget size accommodates max scale to prevent layout jumping
        self.setMinimumHeight(int(base_h * 1.25))
