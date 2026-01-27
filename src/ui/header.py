from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

class HeaderWidget(QWidget):
    def __init__(self, title="MoTeC .ld Export Tool", logo_path=None):
        super().__init__()
        self.setFixedHeight(80)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        
        # Logo Label
        self.logo_label = QLabel()
        self.layout.addWidget(self.logo_label)

        # Load Logo
        if logo_path:
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(pixmap)
            
        # Title
        self.title_label = QLabel(title)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.title_label.setFont(font)
        
        # Add to layout
        self.layout.addSpacing(15)
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()
