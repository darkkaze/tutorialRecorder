"""
Recording toolbar window.

This module provides a floating transparent toolbar for controlling
active recordings, with pause/resume/stop controls and resolution display.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSystemTrayIcon,
    QMenu
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor, QIcon, QAction


class RecordingToolbar(QWidget):
    """
    Floating transparent toolbar for recording controls.

    Provides pause/resume/stop buttons and displays the current
    capture area resolution.
    """

    def __init__(self, resolution: str = "1920x1080"):
        """
        Initialize the recording toolbar.

        Args:
            resolution: String representation of resolution (e.g., "1920x1080").
        """
        super().__init__()
        self.resolution = resolution
        self.is_paused = False
        self.dragging = False
        self.drag_start_pos = QPoint()
        self.last_position = QPoint(100, 100)
        self._setup_ui()
        self._setup_system_tray()

    def _setup_ui(self):
        """Set up the toolbar UI."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedHeight(60)
        self.setMinimumWidth(400)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        self.resolution_label = QLabel(self.resolution)
        layout.addWidget(self.resolution_label)

        layout.addStretch()

        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.setFixedHeight(40)
        self.pause_button.clicked.connect(self._toggle_pause)
        layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setFixedHeight(40)
        layout.addWidget(self.stop_button)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(50, 50, 50, 220);
                border-radius: 10px;
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                background-color: rgba(80, 80, 80, 200);
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 200);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 200);
            }
        """)

    def _toggle_pause(self):
        """Toggle between pause and resume states."""
        if self.is_paused:
            self.pause_button.setText("⏸ Pause")
            self.is_paused = False
        else:
            self.pause_button.setText("▶ Resume")
            self.is_paused = True

    def mousePressEvent(self, event):
        """
        Handle mouse press for dragging.

        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move for dragging.

        Args:
            event: The mouse event.
        """
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start_pos)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release for dragging.

        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def set_resolution(self, resolution: str):
        """
        Update the displayed resolution.

        Args:
            resolution: String representation of resolution.
        """
        self.resolution = resolution
        self.resolution_label.setText(resolution)

    def _setup_system_tray(self):
        """Set up system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("TutorialRecorder")

        tray_menu = QMenu()

        show_action = QAction("Show Toolbar", self)
        show_action.triggered.connect(self._show_toolbar)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        hide_action = QAction("Hide Toolbar", self)
        hide_action.triggered.connect(self._hide_toolbar)
        tray_menu.addAction(hide_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _hide_toolbar(self):
        """Hide the toolbar and show system tray icon."""
        self.last_position = self.pos()
        self.hide()
        self.tray_icon.show()

    def _show_toolbar(self):
        """Show the toolbar and hide system tray icon."""
        self.show()
        self.move(self.last_position)
        self.tray_icon.hide()

    def _on_tray_activated(self, reason):
        """
        Handle system tray icon activation.

        Args:
            reason: Activation reason.
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_toolbar()
