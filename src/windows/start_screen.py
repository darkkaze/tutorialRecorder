"""
Start screen window.

This module provides the application's entry point window where users can choose
to create a new recording project or open an existing project.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from pathlib import Path
from services import config_service


class ClickableWidget(QWidget):
    """
    A clickable widget that emits a signal when clicked.
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the clickable widget."""
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StartScreenWindow(QWidget):
    """
    Start screen window with options to record or open existing projects.

    Signals:
        record_clicked: Emitted when user clicks the Record button.
        project_selected: Emitted when user selects an existing project folder.
    """

    record_clicked = pyqtSignal()
    project_selected = pyqtSignal(str)

    def __init__(self):
        """Initialize the start screen window."""
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("TutorialRecorder")
        self.setFixedSize(600, 400)

        # Center window on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 600) // 2
        y = (screen.height() - 400) // 2
        self.move(x, y)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Icon buttons container
        icon_container = QHBoxLayout()
        icon_container.setSpacing(40)

        # Record button
        self.record_button = self._create_icon_button(
            self._get_video_camera_icon(),
            "Grabar"
        )
        self.record_button.clicked.connect(self._on_record_clicked)

        # Project button
        self.project_button = self._create_icon_button(
            self._get_network_icon(),
            "Project"
        )
        self.project_button.clicked.connect(self._on_project_clicked)

        icon_container.addStretch()
        icon_container.addWidget(self.record_button)
        icon_container.addWidget(self.project_button)
        icon_container.addStretch()

        main_layout.addStretch()
        main_layout.addLayout(icon_container)
        main_layout.addStretch()

        # Footer section
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(10)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        # Donation message
        donation_label = QLabel(
            '<span style="color: white;">Support this project: </span>'
            '<a href="https://ko-fi.com/darkkaze" style="color: #26A69A; text-decoration: none;">ko-fi.com/darkkaze</a>'
        )
        donation_label.setOpenExternalLinks(True)
        donation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donation_label.setStyleSheet("font-size: 11px;")

        footer_layout.addWidget(separator)
        footer_layout.addWidget(donation_label)

        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

    def _create_icon_button(self, pixmap: QPixmap, label: str) -> ClickableWidget:
        """
        Create a clickable widget with icon and label.

        Args:
            pixmap: QPixmap for the icon.
            label: Text label below the icon.

        Returns:
            Configured ClickableWidget.
        """
        container = ClickableWidget()
        container.setFixedSize(140, 140)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon label
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(100, 100)
        icon_label.setScaledContents(True)

        # Text label with teal color
        text_label = QLabel(label)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("""
            QLabel {
                color: #26A69A;
                font-size: 16px;
                font-weight: bold;
            }
        """)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        return container

    def _get_video_camera_icon(self) -> QPixmap:
        """
        Get video camera icon from SVG data.

        Returns:
            QPixmap with video camera icon in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640">
            <path fill="#26A69A" d="M128 128C92.7 128 64 156.7 64 192L64 448C64 483.3 92.7 512 128 512L384 512C419.3 512 448 483.3 448 448L448 192C448 156.7 419.3 128 384 128L128 128zM496 400L569.5 458.8C573.7 462.2 578.9 464 584.3 464C597.4 464 608 453.4 608 440.3L608 199.7C608 186.6 597.4 176 584.3 176C578.9 176 573.7 177.8 569.5 181.2L496 240L496 400z"/>
        </svg>
        """

        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(100, 100))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _get_network_icon(self) -> QPixmap:
        """
        Get network/project icon from SVG data.

        Returns:
            QPixmap with network icon in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640">
            <path fill="#26A69A" d="M64 144C64 117.5 85.5 96 112 96L208 96C234.5 96 256 117.5 256 144L256 160L384 160L384 144C384 117.5 405.5 96 432 96L528 96C554.5 96 576 117.5 576 144L576 240C576 266.5 554.5 288 528 288L432 288C405.5 288 384 266.5 384 240L384 224L256 224L256 240C256 247.3 254.3 254.3 251.4 260.5L320 352L400 352C426.5 352 448 373.5 448 400L448 496C448 522.5 426.5 544 400 544L304 544C277.5 544 256 522.5 256 496L256 400C256 392.7 257.7 385.7 260.6 379.5L192 288L112 288C85.5 288 64 266.5 64 240L64 144z"/>
        </svg>
        """

        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(100, 100))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _on_record_clicked(self):
        """Handle record button click."""
        self.record_clicked.emit()

    def _on_project_clicked(self):
        """Handle project button click."""
        # Load config to get default export path
        config = config_service.load_config()
        export_path = config.get("export_path") or str(Path.home())

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            export_path,
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            self.project_selected.emit(folder)
