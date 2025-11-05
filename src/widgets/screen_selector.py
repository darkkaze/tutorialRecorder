"""
Screen area selector widget.

This module provides a transparent overlay widget for selecting
a screen capture area with drag-to-move and resolution controls.
"""
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QScreen


class ScreenSelector(QWidget):
    """
    Transparent overlay widget for selecting screen capture area.

    Displays a semi-transparent overlay with a transparent
    selection rectangle that can be moved and resized.
    """

    recording_started = pyqtSignal(dict)

    def __init__(self, default_resolution: str = "1920x1080"):
        """
        Initialize the screen selector widget.

        Args:
            default_resolution: Default resolution to select (e.g., "1920x1080").
        """
        super().__init__()
        self.default_resolution = default_resolution
        parts = default_resolution.split("x")
        if len(parts) == 2:
            try:
                width, height = int(parts[0]), int(parts[1])
                self.selection_rect = QRect(0, 0, width, height)
            except ValueError:
                self.selection_rect = QRect(0, 0, 1920, 1080)
        else:
            self.selection_rect = QRect(0, 0, 1920, 1080)

        self.current_resolution = default_resolution
        self.is_free_mode = False
        self.dragging = False
        self.drag_start_pos = QPoint()
        self.resizing = False
        self.resize_corner = None
        self.is_recording = False
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = self.screen()
        if screen:
            screen_geometry = screen.geometry()
            self.setGeometry(screen_geometry)

        self.show()
        self._center_selection_rect()
        self._create_toolbar()

    def _get_available_resolutions(self) -> list[tuple[str, int, int, str, bool]]:
        """
        Get available resolutions filtered by screen size, grouped by aspect ratio.

        Returns:
            List of tuples: (display_name, width, height, aspect_ratio, is_header)
        """
        all_resolutions = {
            "16:9": [
                ("3840x2160 (4K)", 3840, 2160),
                ("2560x1440 (2K)", 2560, 1440),
                ("1920x1080 (FHD)", 1920, 1080),
                ("1280x720 (HD)", 1280, 720),
                ("854x480 (FWVGA)", 854, 480),
                ("640x360", 640, 360),
            ],
            "4:3": [
                ("1600x1200", 1600, 1200),
                ("1024x768 (XGA)", 1024, 768),
                ("800x600 (SVGA)", 800, 600),
                ("640x480 (VGA)", 640, 480),
            ],
            "9:16": [
                ("1080x1920", 1080, 1920),
                ("720x1280", 720, 1280),
                ("480x854", 480, 854),
                ("360x640", 360, 640),
            ],
            "1:1": [
                ("1080x1080", 1080, 1080),
                ("720x720", 720, 720),
                ("600x600", 600, 600),
                ("480x480", 480, 480),
            ],
        }

        screen = self.screen()
        max_width = float('inf')
        max_height = float('inf')

        if screen:
            screen_size = screen.size()
            max_width = screen_size.width()
            max_height = screen_size.height()

        result = []
        aspect_ratio_order = ["16:9", "4:3", "9:16", "1:1"]

        for aspect_ratio in aspect_ratio_order:
            resolutions = all_resolutions[aspect_ratio]
            filtered = [
                (name, w, h) for name, w, h in resolutions
                if w <= max_width and h <= max_height
            ]

            if filtered:
                result.append((f"─── {aspect_ratio} ───", 0, 0, aspect_ratio, True))
                for name, w, h in filtered:
                    result.append((name, w, h, aspect_ratio, False))

        result.append(("─── Free ───", 0, 0, "Free", True))
        result.append(("Manual resize", 0, 0, "Free", False))

        return result

    def _center_selection_rect(self):
        """Center the selection rectangle on the screen."""
        screen_rect = self.rect()
        x = (screen_rect.width() - self.selection_rect.width()) // 2
        y = (screen_rect.height() - self.selection_rect.height()) // 2
        self.selection_rect.moveTo(x, y)

    def _create_toolbar(self):
        """Create the floating toolbar."""
        self.menu_widget = QWidget(self)
        menu_layout = QHBoxLayout(self.menu_widget)
        menu_layout.setContentsMargins(5, 5, 5, 5)

        self.resolution_combo = QComboBox()
        available_resolutions = self._get_available_resolutions()

        for display_name, width, height, aspect_ratio, is_header in available_resolutions:
            self.resolution_combo.addItem(display_name, (width, height, aspect_ratio))
            if is_header:
                index = self.resolution_combo.count() - 1
                item_model = self.resolution_combo.model()
                item = item_model.item(index)
                item.setEnabled(False)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        default_index = self.resolution_combo.findText(self.default_resolution, Qt.MatchFlag.MatchStartsWith)
        if default_index >= 0:
            self.resolution_combo.setCurrentIndex(default_index)
        else:
            default_index = self.resolution_combo.findText("1920x1080", Qt.MatchFlag.MatchStartsWith)
            if default_index >= 0:
                self.resolution_combo.setCurrentIndex(default_index)

        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        menu_layout.addWidget(self.resolution_combo)

        menu_layout.addSpacing(15)

        record_button = QPushButton("Grabar")
        record_button.clicked.connect(self._start_recording)
        record_button.setStyleSheet("background-color: rgba(200, 0, 0, 200);")
        menu_layout.addWidget(record_button)

        self.menu_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(50, 50, 50, 200);
                border-radius: 5px;
            }
            QPushButton {
                background-color: rgba(80, 80, 80, 200);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 200);
            }
            QComboBox {
                background-color: rgba(80, 80, 80, 200);
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                min-width: 200px;
            }
            QComboBox:hover {
                background-color: rgba(100, 100, 100, 200);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
        """)

        self._position_menu()
        self.menu_widget.show()

    def _position_menu(self):
        """Position the menu inside the selection rectangle at the top."""
        menu_width = self.menu_widget.sizeHint().width()
        menu_height = self.menu_widget.sizeHint().height()

        x = self.selection_rect.center().x() - menu_width // 2
        y = self.selection_rect.top() + 20

        if x < self.selection_rect.left() + 10:
            x = self.selection_rect.left() + 10
        elif x + menu_width > self.selection_rect.right() - 10:
            x = self.selection_rect.right() - menu_width - 10

        self.menu_widget.setGeometry(x, y, menu_width, menu_height)

    def _on_resolution_changed(self, index: int):
        """
        Handle resolution selection change.

        Args:
            index: Selected index in combobox.
        """
        data = self.resolution_combo.itemData(index)
        if data:
            width, height, aspect_ratio = data

            if width == 0 and height == 0:
                if aspect_ratio == "Free":
                    self.is_free_mode = True
                return

            self.is_free_mode = False
            self.current_resolution = f"{width}x{height}"

            center = self.selection_rect.center()
            self.selection_rect.setWidth(width)
            self.selection_rect.setHeight(height)

            new_x = center.x() - width // 2
            new_y = center.y() - height // 2
            self.selection_rect.moveTo(new_x, new_y)

            self._position_menu()
            self.update()

    def _get_resize_corner(self, pos: QPoint) -> str | None:
        """
        Determine which corner/edge the mouse is near.

        Args:
            pos: Mouse position.

        Returns:
            Corner identifier or None.
        """
        threshold = 15
        rect = self.selection_rect

        corners = {
            "bottom_right": rect.bottomRight(),
            "bottom_left": rect.bottomLeft(),
            "top_right": rect.topRight(),
            "top_left": rect.topLeft()
        }

        for corner_name, corner_pos in corners.items():
            if (abs(pos.x() - corner_pos.x()) < threshold and
                abs(pos.y() - corner_pos.y()) < threshold):
                return corner_name

        return None

    def paintEvent(self, event):
        """
        Paint the overlay and selection rectangle.

        Args:
            event: The paint event.
        """
        painter = QPainter(self)
        self._draw_overlay(painter)
        self._draw_selection_rect(painter)

    def _draw_overlay(self, painter: QPainter):
        """
        Draw the semi-transparent overlay.

        Args:
            painter: The QPainter instance.
        """
        if not self.is_recording:
            overlay_color = QColor(0, 0, 0, 90)
            painter.fillRect(self.rect(), overlay_color)

            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(self.selection_rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )

    def _draw_selection_rect(self, painter: QPainter):
        """
        Draw the selection rectangle border.

        Args:
            painter: The QPainter instance.
        """
        pen = QPen(QColor(255, 255, 255), 2)
        painter.setPen(pen)
        painter.drawRect(self.selection_rect)

    def mousePressEvent(self, event):
        """
        Handle mouse press events for dragging and resizing.

        Args:
            event: The mouse event.
        """
        if self.is_recording:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            corner = self._get_resize_corner(event.pos())
            if corner:
                self.resizing = True
                self.resize_corner = corner
            elif self.selection_rect.contains(event.pos()):
                self.dragging = True
                self.drag_start_pos = event.pos() - self.selection_rect.topLeft()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events for dragging and resizing.

        Args:
            event: The mouse event.
        """
        if self.is_recording:
            return

        if self.resizing and self.is_free_mode:
            self._handle_resize(event.pos())
        elif self.dragging:
            new_pos = event.pos() - self.drag_start_pos
            self.selection_rect.moveTo(new_pos)
            self._position_menu()
            self.update()

    def _handle_resize(self, pos: QPoint):
        """
        Handle resizing the selection rectangle (only in Free mode).

        Args:
            pos: Current mouse position.
        """
        rect = self.selection_rect
        new_rect = QRect(rect)

        if self.resize_corner == "bottom_right":
            new_rect.setBottomRight(pos)
        elif self.resize_corner == "bottom_left":
            new_rect.setBottomLeft(pos)
        elif self.resize_corner == "top_right":
            new_rect.setTopRight(pos)
        elif self.resize_corner == "top_left":
            new_rect.setTopLeft(pos)

        new_rect = new_rect.normalized()

        if new_rect.width() < 100 or new_rect.height() < 100:
            return

        self.selection_rect = new_rect
        self._position_menu()
        self.update()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events for dragging and resizing.

        Args:
            event: The mouse event.
        """
        if self.is_recording:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_corner = None

    def _start_recording(self):
        """Start recording and switch to recording mode."""
        aspect_ratio_text = self.resolution_combo.currentText()
        if "Free" in aspect_ratio_text:
            aspect_ratio = "Free"
        else:
            aspect_ratio = self.current_resolution

        screen_x = self.selection_rect.x()
        screen_y = self.selection_rect.y()

        area_data = {
            "x": screen_x,
            "y": screen_y,
            "width": self.selection_rect.width(),
            "height": self.selection_rect.height(),
            "aspect_ratio": aspect_ratio
        }
        self.recording_started.emit(area_data)
        self.is_recording = True
        self.menu_widget.hide()

        self.setGeometry(
            screen_x - 5,
            screen_y - 5,
            self.selection_rect.width() + 10,
            self.selection_rect.height() + 10
        )

        self.selection_rect = QRect(
            5,
            5,
            self.selection_rect.width(),
            self.selection_rect.height()
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.WindowTransparentForInput
        )
        self.show()
        self.update()

    def keyPressEvent(self, event):
        """
        Handle key press events.

        Args:
            event: The key event.
        """
        if event.key() == Qt.Key.Key_Escape:
            self.close()
