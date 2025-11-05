"""
Project viewer window.

This module provides a window to view and export recording projects with different layouts.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QApplication, QMessageBox, QFrame, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt6.QtGui import QPixmap
from PyQt6.QtSvg import QSvgRenderer
from pathlib import Path
import json
from services import export_service


class ClickableLayoutWidget(QFrame):
    """
    A clickable layout widget that can be selected.
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the clickable layout widget."""
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.selected = False
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #555;
                border-radius: 10px;
                background-color: transparent;
            }
        """)

    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        """Set the selected state and update styling."""
        self.selected = selected
        if selected:
            self.setStyleSheet("""
                QFrame {
                    border: 3px solid #26A69A;
                    border-radius: 10px;
                    background-color: rgba(38, 166, 154, 0.1);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #555;
                    border-radius: 10px;
                    background-color: transparent;
                }
            """)


class ExportThread(QThread):
    """
    Thread for running video export in background.

    Signals:
        progress_updated: Emitted with progress percentage (0-100).
        export_finished: Emitted with (success: bool, message: str).
    """

    progress_updated = pyqtSignal(int)
    export_finished = pyqtSignal(bool, str)

    def __init__(self, project_folder: Path, layout_name: str):
        """
        Initialize export thread.

        Args:
            project_folder: Path to project folder.
            layout_name: Name of selected layout.
        """
        super().__init__()
        self.project_folder = project_folder
        self.layout_name = layout_name

    def run(self):
        """Run the export process."""
        try:
            success, message = export_service.export_video(
                self.project_folder,
                self.layout_name,
                self._progress_callback
            )
            self.export_finished.emit(success, message)
        except Exception as e:
            self.export_finished.emit(False, str(e))

    def _progress_callback(self, progress: int):
        """
        Callback for progress updates.

        Args:
            progress: Progress percentage (0-100).
        """
        self.progress_updated.emit(progress)


class ProjectViewerWindow(QWidget):
    """
    Project viewer window for exporting projects with different layouts.

    Allows users to select output layout and generate merged video.

    Signals:
        closed: Emitted when the window is closed.
    """

    closed = pyqtSignal()

    def __init__(self, project_folder: str):
        """
        Initialize the project viewer window.

        Args:
            project_folder: Path to the project folder.
        """
        super().__init__()
        self.project_folder = Path(project_folder)
        self.selected_layout = None
        self.layout_widgets = []
        self.export_thread = None
        self.progress_dialog = None

        # Validate project folder
        if not self._validate_project():
            QMessageBox.warning(
                None,
                "Invalid Project",
                "La carpeta seleccionada no es un proyecto válido de TutorialRecorder.\n\n"
                "Debe contener un archivo metadata.json válido."
            )
            # Close immediately by emitting closed signal
            QApplication.processEvents()
            self.closed.emit()
            return

        self._setup_ui()

    def _validate_project(self) -> bool:
        """
        Validate that the folder is a valid TutorialRecorder project.

        Returns:
            True if valid project, False otherwise.
        """
        metadata_path = self.project_folder / "metadata.json"
        if not metadata_path.exists():
            return False

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Check for required fields
            if "project_name" not in metadata:
                return False

            return True
        except Exception:
            return False

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle(f"Export Project - {self.project_folder.name}")
        self.setFixedSize(800, 600)

        # Center window on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 800) // 2
        y = (screen.height() - 600) // 2
        self.move(x, y)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Title
        title_label = QLabel("Selecciona un Layout de Salida")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #26A69A;
            }
        """)
        main_layout.addWidget(title_label)

        # Scroll area for layouts
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(300)

        # Container for layouts
        layouts_container = QWidget()
        layouts_layout = QHBoxLayout(layouts_container)
        layouts_layout.setContentsMargins(0, 0, 0, 0)
        layouts_layout.setSpacing(30)

        # Add vertical layout (Person at bottom)
        vertical_layout_widget = self._create_layout_widget(
            self._get_vertical_layout_icon(),
            "Vertical Bottom",
            "9:16"
        )
        layouts_layout.addWidget(vertical_layout_widget)
        self.layout_widgets.append(vertical_layout_widget)

        # Add inverted layout (Person on top)
        inverted_layout_widget = self._create_layout_widget(
            self._get_inverted_layout_icon(),
            "Vertical Top",
            "9:16"
        )
        layouts_layout.addWidget(inverted_layout_widget)
        self.layout_widgets.append(inverted_layout_widget)

        # Add horizontal layout (Person in bottom-right corner)
        horizontal_layout_widget = self._create_layout_widget(
            self._get_horizontal_layout_icon(),
            "Down Right",
            "16:9"
        )
        layouts_layout.addWidget(horizontal_layout_widget)
        self.layout_widgets.append(horizontal_layout_widget)

        # Add horizontal left layout (Person in bottom-left corner)
        horizontal_left_layout_widget = self._create_layout_widget(
            self._get_horizontal_left_layout_icon(),
            "Down Left",
            "16:9"
        )
        layouts_layout.addWidget(horizontal_left_layout_widget)
        self.layout_widgets.append(horizontal_left_layout_widget)

        # Add horizontal top right layout (Person in top-right corner)
        horizontal_top_right_layout_widget = self._create_layout_widget(
            self._get_horizontal_top_right_layout_icon(),
            "Top Right",
            "16:9"
        )
        layouts_layout.addWidget(horizontal_top_right_layout_widget)
        self.layout_widgets.append(horizontal_top_right_layout_widget)

        # Add horizontal top left layout (Person in top-left corner)
        horizontal_top_left_layout_widget = self._create_layout_widget(
            self._get_horizontal_top_left_layout_icon(),
            "Top Left",
            "16:9"
        )
        layouts_layout.addWidget(horizontal_top_left_layout_widget)
        self.layout_widgets.append(horizontal_top_left_layout_widget)

        layouts_layout.addStretch()
        scroll_area.setWidget(layouts_container)
        main_layout.addWidget(scroll_area)

        # Export button
        export_button = QPushButton("Exportar Video")
        export_button.setFixedHeight(40)
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #26A69A;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2bbbad;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        export_button.setEnabled(False)  # Disabled until layout selected
        export_button.clicked.connect(self._on_export_clicked)
        self.export_button = export_button
        main_layout.addWidget(export_button)

        # Close button
        close_button = QPushButton("Cerrar")
        close_button.setFixedHeight(35)
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def _create_layout_widget(
        self,
        pixmap: QPixmap,
        title: str,
        description: str
    ) -> ClickableLayoutWidget:
        """
        Create a clickable layout widget.

        Args:
            pixmap: QPixmap for the layout icon.
            title: Title of the layout.
            description: Description of the layout.

        Returns:
            Configured ClickableLayoutWidget.
        """
        container = ClickableLayoutWidget()
        container.setFixedSize(180, 250)
        container.clicked.connect(lambda: self._on_layout_selected(container, title))

        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon label
        icon_label = QLabel()
        # Scale pixmap to fit within 120x160 while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            120, 160,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        icon_label.setPixmap(scaled_pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(120, 160)

        # Icon label
        icon_label.setStyleSheet("border: none; background: transparent;")

        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #26A69A;
                font-size: 16px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
        """)

        # Description label
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 11px;
                border: none;
                background: transparent;
            }
        """)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        return container

    def _get_vertical_layout_icon(self) -> QPixmap:
        """
        Get vertical layout icon from SVG data.

        Returns:
            QPixmap with vertical layout icon in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1121 1824">
            <!-- Outer border (rounded rectangle) -->
            <rect x="15" y="15" width="1091" height="1794" rx="40" ry="40"
                  fill="none" stroke="#26A69A" stroke-width="30"/>

            <!-- Horizontal divider line -->
            <line x1="15" y1="912" x2="1106" y2="912"
                  stroke="#26A69A" stroke-width="30"/>

            <!-- Screen icon (top) -->
            <path d="M328.656,267.677c-24.2,0 -43.9,19.7 -43.9,43.9l0,328.2c0,24.3 19.7,43.9 43.9,43.9c5.5,0 10.7,-1 15.7,-2.9c12.9,-4.9 103.4,-37.1 228.4,-37.1c125,0 215.5,32.3 228.4,37.1c5,1.9 10.2,2.9 15.7,2.9c24.3,0 43.9,-19.7 43.9,-43.9l0,-328.2c0,-24.3 -19.7,-43.9 -43.9,-43.9c-5.5,0 -10.7,1 -15.7,2.9c-12.9,4.9 -103.4,37.1 -228.4,37.1c-125,0 -215.5,-32.3 -228.4,-37.1c-5,-1.9 -10.2,-2.9 -15.7,-2.9Zm28.1,128c0,-22.1 17.9,-40 40,-40c22.1,0 40,17.9 40,40c0,22.1 -17.9,40 -40,40c-22.1,0 -40,-17.9 -40,-40Zm264.1,-16c7.5,0 14.6,3.6 19.1,9.6l124.5,166.6c5.9,7.9 6.4,18.5 1.3,26.9c-5.1,8.4 -14.8,12.8 -24.5,11.1c-45.8,-7.8 -103.3,-14.2 -168.4,-14.2c-65.6,0 -123.4,6.5 -169.3,14.4c-9.8,1.7 -19.7,-2.9 -24.7,-11.5c-5,-8.6 -4.3,-19.4 1.9,-27.2l69.3,-86.7c4.6,-5.7 11.5,-9 18.7,-9c7.2,0 14.2,3.3 18.7,9l27.5,34.4l86.7,-113.9c4.6,-6 11.7,-9.5 19.2,-9.5Z"
                  fill="#26A69A"/>

            <!-- Webcam icon (bottom) -->
            <path d="M567.756,1435.677c66.3,0 120,-53.7 120,-120c0,-66.3 -53.7,-120 -120,-120c-66.3,0 -120,53.7 -120,120c0,66.3 53.7,120 120,120Zm-29.7,56c-98.5,0 -178.3,79.8 -178.3,178.3c0,16.4 13.3,29.7 29.7,29.7l356.6,0c16.4,0 29.7,-13.3 29.7,-29.7c0,-98.5 -79.8,-178.3 -178.3,-178.3l-59.4,0Z"
                  fill="#26A69A"/>
        </svg>
        """

        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(120, 200))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _get_inverted_layout_icon(self) -> QPixmap:
        """
        Get inverted layout icon from SVG data.

        Returns:
            QPixmap with inverted layout icon (person on top, screen on bottom) in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1121 1824">
            <!-- Outer border (rounded rectangle) -->
            <rect x="15" y="15" width="1091" height="1794" rx="40" ry="40"
                  fill="none" stroke="#26A69A" stroke-width="30"/>

            <!-- Horizontal divider line -->
            <line x1="15" y1="912" x2="1106" y2="912"
                  stroke="#26A69A" stroke-width="30"/>

            <!-- Webcam icon (top - person) -->
            <path d="M567.756,445.677c66.3,0 120,-53.7 120,-120c0,-66.3 -53.7,-120 -120,-120c-66.3,0 -120,53.7 -120,120c0,66.3 53.7,120 120,120Zm-29.7,56c-98.5,0 -178.3,79.8 -178.3,178.3c0,16.4 13.3,29.7 29.7,29.7l356.6,0c16.4,0 29.7,-13.3 29.7,-29.7c0,-98.5 -79.8,-178.3 -178.3,-178.3l-59.4,0Z"
                  fill="#26A69A"/>

            <!-- Screen icon (bottom) -->
            <path d="M328.656,1257.677c-24.2,0 -43.9,19.7 -43.9,43.9l0,328.2c0,24.3 19.7,43.9 43.9,43.9c5.5,0 10.7,-1 15.7,-2.9c12.9,-4.9 103.4,-37.1 228.4,-37.1c125,0 215.5,32.3 228.4,37.1c5,1.9 10.2,2.9 15.7,2.9c24.3,0 43.9,-19.7 43.9,-43.9l0,-328.2c0,-24.3 -19.7,-43.9 -43.9,-43.9c-5.5,0 -10.7,1 -15.7,2.9c-12.9,4.9 -103.4,37.1 -228.4,37.1c-125,0 -215.5,-32.3 -228.4,-37.1c-5,-1.9 -10.2,-2.9 -15.7,-2.9Zm28.1,128c0,-22.1 17.9,-40 40,-40c22.1,0 40,17.9 40,40c0,22.1 -17.9,40 -40,40c-22.1,0 -40,-17.9 -40,-40Zm264.1,-16c7.5,0 14.6,3.6 19.1,9.6l124.5,166.6c5.9,7.9 6.4,18.5 1.3,26.9c-5.1,8.4 -14.8,12.8 -24.5,11.1c-45.8,-7.8 -103.3,-14.2 -168.4,-14.2c-65.6,0 -123.4,6.5 -169.3,14.4c-9.8,1.7 -19.7,-2.9 -24.7,-11.5c-5,-8.6 -4.3,-19.4 1.9,-27.2l69.3,-86.7c4.6,-5.7 11.5,-9 18.7,-9c7.2,0 14.2,3.3 18.7,9l27.5,34.4l86.7,-113.9c4.6,-6 11.7,-9.5 19.2,-9.5Z"
                  fill="#26A69A"/>
        </svg>
        """

        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(120, 200))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _get_horizontal_layout_icon(self) -> QPixmap:
        """
        Get horizontal layout icon from SVG data.

        Returns:
            QPixmap with horizontal layout icon (screen with person in corner) in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000">
            <!-- Outer border (rounded rectangle - horizontal) -->
            <rect x="20" y="20" width="1560" height="960" rx="40" ry="40"
                  fill="none" stroke="#26A69A" stroke-width="30"/>

            <!-- Screen icon background (centered in available space, left of person box) -->
            <g transform="translate(75, -52) scale(1.6)">
                <path d="M100,150c-24.2,0 -43.9,19.7 -43.9,43.9l0,300c0,24.3 19.7,43.9 43.9,43.9c5.5,0 10.7,-1 15.7,-2.9c12.9,-4.9 103.4,-37.1 228.4,-37.1c125,0 215.5,32.3 228.4,37.1c5,1.9 10.2,2.9 15.7,2.9c24.3,0 43.9,-19.7 43.9,-43.9l0,-300c0,-24.3 -19.7,-43.9 -43.9,-43.9c-5.5,0 -10.7,1 -15.7,2.9c-12.9,4.9 -103.4,37.1 -228.4,37.1c-125,0 -215.5,-32.3 -228.4,-37.1c-5,-1.9 -10.2,-2.9 -15.7,-2.9Zm28.1,125c0,-22.1 17.9,-40 40,-40c22.1,0 40,17.9 40,40c0,22.1 -17.9,40 -40,40c-22.1,0 -40,-17.9 -40,-40Zm264.1,-16c7.5,0 14.6,3.6 19.1,9.6l124.5,166.6c5.9,7.9 6.4,18.5 1.3,26.9c-5.1,8.4 -14.8,12.8 -24.5,11.1c-45.8,-7.8 -103.3,-14.2 -168.4,-14.2c-65.6,0 -123.4,6.5 -169.3,14.4c-9.8,1.7 -19.7,-2.9 -24.7,-11.5c-5,-8.6 -4.3,-19.4 1.9,-27.2l69.3,-86.7c4.6,-5.7 11.5,-9 18.7,-9c7.2,0 14.2,3.3 18.7,9l27.5,34.4l86.7,-113.9c4.6,-6 11.7,-9.5 19.2,-9.5Z"
                      fill="#26A69A"/>
            </g>

            <!-- Person box border (bottom right corner) -->
            <rect x="1230" y="700" width="300" height="240" rx="20" ry="20"
                  fill="none" stroke="#26A69A" stroke-width="25"/>

            <!-- Person icon (scaled and positioned in bottom right box) -->
            <g transform="translate(1380, 790) scale(0.45)">
                <path d="M0,-80c66.3,0 120,-53.7 120,-120c0,-66.3 -53.7,-120 -120,-120c-66.3,0 -120,53.7 -120,120c0,66.3 53.7,120 120,120Zm-29.7,56c-98.5,0 -178.3,79.8 -178.3,178.3c0,16.4 13.3,29.7 29.7,29.7l356.6,0c16.4,0 29.7,-13.3 29.7,-29.7c0,-98.5 -79.8,-178.3 -178.3,-178.3l-59.4,0Z"
                      fill="#26A69A"/>
            </g>
        </svg>
        """

        # Render SVG to pixmap - don't scale contents, center it
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(160, 100))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _get_horizontal_left_layout_icon(self) -> QPixmap:
        """
        Get horizontal left layout icon from SVG data.

        Returns:
            QPixmap with horizontal layout icon (screen with person in bottom-left corner) in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000">
            <!-- Outer border (rounded rectangle - horizontal) -->
            <rect x="20" y="20" width="1560" height="960" rx="40" ry="40"
                  fill="none" stroke="#26A69A" stroke-width="30"/>

            <!-- Screen icon background (centered in available space, right of person box) -->
            <g transform="translate(425, -52) scale(1.6)">
                <path d="M100,150c-24.2,0 -43.9,19.7 -43.9,43.9l0,300c0,24.3 19.7,43.9 43.9,43.9c5.5,0 10.7,-1 15.7,-2.9c12.9,-4.9 103.4,-37.1 228.4,-37.1c125,0 215.5,32.3 228.4,37.1c5,1.9 10.2,2.9 15.7,2.9c24.3,0 43.9,-19.7 43.9,-43.9l0,-300c0,-24.3 -19.7,-43.9 -43.9,-43.9c-5.5,0 -10.7,1 -15.7,2.9c-12.9,4.9 -103.4,37.1 -228.4,37.1c-125,0 -215.5,-32.3 -228.4,-37.1c-5,-1.9 -10.2,-2.9 -15.7,-2.9Zm28.1,125c0,-22.1 17.9,-40 40,-40c22.1,0 40,17.9 40,40c0,22.1 -17.9,40 -40,40c-22.1,0 -40,-17.9 -40,-40Zm264.1,-16c7.5,0 14.6,3.6 19.1,9.6l124.5,166.6c5.9,7.9 6.4,18.5 1.3,26.9c-5.1,8.4 -14.8,12.8 -24.5,11.1c-45.8,-7.8 -103.3,-14.2 -168.4,-14.2c-65.6,0 -123.4,6.5 -169.3,14.4c-9.8,1.7 -19.7,-2.9 -24.7,-11.5c-5,-8.6 -4.3,-19.4 1.9,-27.2l69.3,-86.7c4.6,-5.7 11.5,-9 18.7,-9c7.2,0 14.2,3.3 18.7,9l27.5,34.4l86.7,-113.9c4.6,-6 11.7,-9.5 19.2,-9.5Z"
                      fill="#26A69A"/>
            </g>

            <!-- Person box border (bottom left corner) -->
            <rect x="70" y="700" width="300" height="240" rx="20" ry="20"
                  fill="none" stroke="#26A69A" stroke-width="25"/>

            <!-- Person icon (scaled and positioned in bottom left box) -->
            <g transform="translate(220, 790) scale(0.45)">
                <path d="M0,-80c66.3,0 120,-53.7 120,-120c0,-66.3 -53.7,-120 -120,-120c-66.3,0 -120,53.7 -120,120c0,66.3 53.7,120 120,120Zm-29.7,56c-98.5,0 -178.3,79.8 -178.3,178.3c0,16.4 13.3,29.7 29.7,29.7l356.6,0c16.4,0 29.7,-13.3 29.7,-29.7c0,-98.5 -79.8,-178.3 -178.3,-178.3l-59.4,0Z"
                      fill="#26A69A"/>
            </g>
        </svg>
        """

        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(160, 100))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _get_horizontal_top_right_layout_icon(self) -> QPixmap:
        """
        Get horizontal top right layout icon from SVG data.

        Returns:
            QPixmap with horizontal layout icon (screen with person in top-right corner) in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000">
            <!-- Outer border (rounded rectangle - horizontal) -->
            <rect x="20" y="20" width="1560" height="960" rx="40" ry="40"
                  fill="none" stroke="#26A69A" stroke-width="30"/>

            <!-- Screen icon background (centered in available space, left of person box) -->
            <g transform="translate(75, -52) scale(1.6)">
                <path d="M100,150c-24.2,0 -43.9,19.7 -43.9,43.9l0,300c0,24.3 19.7,43.9 43.9,43.9c5.5,0 10.7,-1 15.7,-2.9c12.9,-4.9 103.4,-37.1 228.4,-37.1c125,0 215.5,32.3 228.4,37.1c5,1.9 10.2,2.9 15.7,2.9c24.3,0 43.9,-19.7 43.9,-43.9l0,-300c0,-24.3 -19.7,-43.9 -43.9,-43.9c-5.5,0 -10.7,1 -15.7,2.9c-12.9,4.9 -103.4,37.1 -228.4,37.1c-125,0 -215.5,-32.3 -228.4,-37.1c-5,-1.9 -10.2,-2.9 -15.7,-2.9Zm28.1,125c0,-22.1 17.9,-40 40,-40c22.1,0 40,17.9 40,40c0,22.1 -17.9,40 -40,40c-22.1,0 -40,-17.9 -40,-40Zm264.1,-16c7.5,0 14.6,3.6 19.1,9.6l124.5,166.6c5.9,7.9 6.4,18.5 1.3,26.9c-5.1,8.4 -14.8,12.8 -24.5,11.1c-45.8,-7.8 -103.3,-14.2 -168.4,-14.2c-65.6,0 -123.4,6.5 -169.3,14.4c-9.8,1.7 -19.7,-2.9 -24.7,-11.5c-5,-8.6 -4.3,-19.4 1.9,-27.2l69.3,-86.7c4.6,-5.7 11.5,-9 18.7,-9c7.2,0 14.2,3.3 18.7,9l27.5,34.4l86.7,-113.9c4.6,-6 11.7,-9.5 19.2,-9.5Z"
                      fill="#26A69A"/>
            </g>

            <!-- Person box border (top right corner) -->
            <rect x="1230" y="60" width="300" height="240" rx="20" ry="20"
                  fill="none" stroke="#26A69A" stroke-width="25"/>

            <!-- Person icon (scaled and positioned in top right box) -->
            <g transform="translate(1380, 150) scale(0.45)">
                <path d="M0,-80c66.3,0 120,-53.7 120,-120c0,-66.3 -53.7,-120 -120,-120c-66.3,0 -120,53.7 -120,120c0,66.3 53.7,120 120,120Zm-29.7,56c-98.5,0 -178.3,79.8 -178.3,178.3c0,16.4 13.3,29.7 29.7,29.7l356.6,0c16.4,0 29.7,-13.3 29.7,-29.7c0,-98.5 -79.8,-178.3 -178.3,-178.3l-59.4,0Z"
                      fill="#26A69A"/>
            </g>
        </svg>
        """

        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(160, 100))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _get_horizontal_top_left_layout_icon(self) -> QPixmap:
        """
        Get horizontal top left layout icon from SVG data.

        Returns:
            QPixmap with horizontal layout icon (screen with person in top-left corner) in teal color.
        """
        svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000">
            <!-- Outer border (rounded rectangle - horizontal) -->
            <rect x="20" y="20" width="1560" height="960" rx="40" ry="40"
                  fill="none" stroke="#26A69A" stroke-width="30"/>

            <!-- Screen icon background (centered in available space, right of person box) -->
            <g transform="translate(425, -52) scale(1.6)">
                <path d="M100,150c-24.2,0 -43.9,19.7 -43.9,43.9l0,300c0,24.3 19.7,43.9 43.9,43.9c5.5,0 10.7,-1 15.7,-2.9c12.9,-4.9 103.4,-37.1 228.4,-37.1c125,0 215.5,32.3 228.4,37.1c5,1.9 10.2,2.9 15.7,2.9c24.3,0 43.9,-19.7 43.9,-43.9l0,-300c0,-24.3 -19.7,-43.9 -43.9,-43.9c-5.5,0 -10.7,1 -15.7,2.9c-12.9,4.9 -103.4,37.1 -228.4,37.1c-125,0 -215.5,-32.3 -228.4,-37.1c-5,-1.9 -10.2,-2.9 -15.7,-2.9Zm28.1,125c0,-22.1 17.9,-40 40,-40c22.1,0 40,17.9 40,40c0,22.1 -17.9,40 -40,40c-22.1,0 -40,-17.9 -40,-40Zm264.1,-16c7.5,0 14.6,3.6 19.1,9.6l124.5,166.6c5.9,7.9 6.4,18.5 1.3,26.9c-5.1,8.4 -14.8,12.8 -24.5,11.1c-45.8,-7.8 -103.3,-14.2 -168.4,-14.2c-65.6,0 -123.4,6.5 -169.3,14.4c-9.8,1.7 -19.7,-2.9 -24.7,-11.5c-5,-8.6 -4.3,-19.4 1.9,-27.2l69.3,-86.7c4.6,-5.7 11.5,-9 18.7,-9c7.2,0 14.2,3.3 18.7,9l27.5,34.4l86.7,-113.9c4.6,-6 11.7,-9.5 19.2,-9.5Z"
                      fill="#26A69A"/>
            </g>

            <!-- Person box border (top left corner) -->
            <rect x="70" y="60" width="300" height="240" rx="20" ry="20"
                  fill="none" stroke="#26A69A" stroke-width="25"/>

            <!-- Person icon (scaled and positioned in top left box) -->
            <g transform="translate(220, 150) scale(0.45)">
                <path d="M0,-80c66.3,0 120,-53.7 120,-120c0,-66.3 -53.7,-120 -120,-120c-66.3,0 -120,53.7 -120,120c0,66.3 53.7,120 120,120Zm-29.7,56c-98.5,0 -178.3,79.8 -178.3,178.3c0,16.4 13.3,29.7 29.7,29.7l356.6,0c16.4,0 29.7,-13.3 29.7,-29.7c0,-98.5 -79.8,-178.3 -178.3,-178.3l-59.4,0Z"
                      fill="#26A69A"/>
            </g>
        </svg>
        """

        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        pixmap = QPixmap(QSize(160, 100))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def _on_layout_selected(self, widget: ClickableLayoutWidget, layout_name: str):
        """
        Handle layout selection.

        Args:
            widget: The selected layout widget.
            layout_name: Name of the selected layout.
        """
        # Deselect all widgets
        for layout_widget in self.layout_widgets:
            layout_widget.set_selected(False)

        # Select the clicked widget
        widget.set_selected(True)
        self.selected_layout = layout_name

        # Enable export button
        self.export_button.setEnabled(True)

    def _on_export_clicked(self):
        """Handle export button click."""
        if not self.selected_layout:
            return

        # Disable export button during export
        self.export_button.setEnabled(False)

        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Exportando video...",
            "Cancelar",
            0,
            100,
            self
        )
        self.progress_dialog.setWindowTitle("Exportando")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.canceled.connect(self._on_export_canceled)

        # Create and start export thread
        self.export_thread = ExportThread(self.project_folder, self.selected_layout)
        self.export_thread.progress_updated.connect(self._on_progress_updated)
        self.export_thread.export_finished.connect(self._on_export_finished)
        self.export_thread.start()

        # Show progress dialog
        self.progress_dialog.show()

    def _on_progress_updated(self, progress: int):
        """
        Handle progress update from export thread.

        Args:
            progress: Progress percentage (0-100).
        """
        if self.progress_dialog:
            self.progress_dialog.setValue(progress)

    def _on_export_finished(self, success: bool, message: str):
        """
        Handle export completion.

        Args:
            success: Whether export succeeded.
            message: Output path if successful, error message otherwise.
        """
        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # Re-enable export button
        self.export_button.setEnabled(True)

        # Clean up thread
        if self.export_thread:
            self.export_thread.deleteLater()
            self.export_thread = None

        if success:
            # Show success message
            QMessageBox.information(
                self,
                "Export Exitoso",
                f"El video se exportó correctamente:\n\n{message}"
            )

            # Open folder in file browser
            export_service.open_folder_in_explorer(self.project_folder)
        else:
            # Show error message
            QMessageBox.critical(
                self,
                "Error de Exportación",
                f"No se pudo exportar el video:\n\n{message}"
            )

    def _on_export_canceled(self):
        """Handle export cancellation."""
        if self.export_thread and self.export_thread.isRunning():
            self.export_thread.terminate()
            self.export_thread.wait()
            self.export_thread = None

        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        self.export_button.setEnabled(True)

    def closeEvent(self, event):
        """Handle window close event."""
        self.closed.emit()
        super().closeEvent(event)
