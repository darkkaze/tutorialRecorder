"""
Project configuration window.

This module provides the main configuration window for setting up
recording projects, including project name and input device selection.
"""
import platform
import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QComboBox,
    QFrame,
    QFileDialog,
    QMessageBox,
    QSystemTrayIcon,
    QMenu
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from services import audio_service, video_service, project_service, recording_service, config_service
from models.project import ProjectConfig, AudioInput, VideoInput, ScreenArea
from widgets.screen_selector import ScreenSelector


class ProjectConfigWindow(QMainWindow):
    """
    Main window for project configuration.

    This window allows users to configure their recording project,
    including project name, audio inputs, and video inputs.

    Signals:
        closed: Emitted when the window is closed.
    """

    closed = pyqtSignal()

    def __init__(self):
        """Initialize the project configuration window."""
        super().__init__()
        self.audio_input_rows = []
        self.audio_devices = []
        self.video_input_rows = []
        self.video_sources = []
        self.recording_session = None
        self.temp_folder = None
        self.screen_area = None
        self.screen_selector = None
        self.tray_icon = None

        config = config_service.load_config()
        self.export_path = config.get("export_path") or str(Path.home())
        self.default_resolution = config.get("default_resolution", "1920x1080")

        self._setup_ui()
        self._check_permissions()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("TutorialRecorder")
        self.setFixedWidth(350)
        self.setMinimumHeight(800)

        self._create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self._add_project_name_section(layout)

        self._add_export_destination_section(layout)

        self._add_audio_inputs_section(layout)

        self._add_video_inputs_section(layout)

        layout.addStretch()

        self._add_action_button(layout)

    def _add_project_name_section(self, layout: QVBoxLayout):
        """
        Add project name input field to the layout.

        Args:
            layout: The layout to add the section to.
        """
        name_label = QLabel("Project Name:")
        layout.addWidget(name_label)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter project name...")
        self.project_name_input.textChanged.connect(self._on_project_name_changed)
        layout.addWidget(self.project_name_input)

    def _add_export_destination_section(self, layout: QVBoxLayout):
        """
        Add export destination selector to the layout.

        Args:
            layout: The layout to add the section to.
        """
        dest_label = QLabel("Export Destination:")
        layout.addWidget(dest_label)

        dest_layout = QHBoxLayout()

        self.export_path_input = QLineEdit()
        self.export_path_input.setPlaceholderText("Select destination folder...")
        self.export_path_input.setReadOnly(True)
        self.export_path_input.setText(self.export_path)
        dest_layout.addWidget(self.export_path_input)

        folder_button = QPushButton()
        folder_button.setText("📁")
        folder_button.setFixedSize(40, 30)
        folder_button.setStyleSheet("""
            QPushButton {
                font-size: 18px !important;
                padding: 0px !important;
            }
        """)
        folder_button.clicked.connect(self._select_export_destination)
        dest_layout.addWidget(folder_button)

        layout.addLayout(dest_layout)

    def _add_audio_inputs_section(self, layout: QVBoxLayout):
        """
        Add audio inputs section with dynamic input controls.

        Args:
            layout: The layout to add the section to.
        """
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        header_layout = QHBoxLayout()
        audio_label = QLabel("Audio Inputs")
        header_layout.addWidget(audio_label)

        add_audio_button = QPushButton()
        add_audio_button.setText("+")
        add_audio_button.setFixedSize(30, 30)
        add_audio_button.setProperty("class", "icon-button")
        add_audio_button.setStyleSheet("""
            QPushButton {
                font-size: 22px !important;
                font-weight: 900 !important;
                padding: 0px !important;
                text-align: center !important;
            }
        """)
        add_audio_button.clicked.connect(self._add_audio_input_row)
        header_layout.addWidget(add_audio_button)

        layout.addLayout(header_layout)

        self.audio_inputs_layout = QVBoxLayout()
        layout.addLayout(self.audio_inputs_layout)

        self._load_audio_devices()
        self._add_audio_input_row()

    def _load_audio_devices(self):
        """Load available audio devices from audio service."""
        try:
            self.audio_devices = audio_service.list_audio_devices()
        except RuntimeError as e:
            self.audio_devices = [f"Error: {str(e)}"]

    def _add_audio_input_row(self):
        """Add a new audio input row with combobox and remove button."""
        row_layout = QHBoxLayout()

        combo = QComboBox()
        for device in self.audio_devices:
            if ":" in device:
                name = device.split(":", 1)[1]
                combo.addItem(name, device)
            else:
                combo.addItem(device, device)
        row_layout.addWidget(combo)

        remove_button = QPushButton()
        remove_button.setText("-")
        remove_button.setFixedSize(30, 30)
        remove_button.setProperty("class", "icon-button")
        remove_button.setStyleSheet("""
            QPushButton {
                font-size: 22px !important;
                font-weight: 900 !important;
                padding: 0px !important;
                text-align: center !important;
            }
        """)
        remove_button.clicked.connect(
            lambda: self._remove_audio_input_row(row_layout, combo)
        )
        row_layout.addWidget(remove_button)

        self.audio_inputs_layout.addLayout(row_layout)
        self.audio_input_rows.append((row_layout, combo))

    def _remove_audio_input_row(self, row_layout: QHBoxLayout, combo: QComboBox):
        """
        Remove an audio input row from the layout.

        Args:
            row_layout: The layout to remove.
            combo: The combobox to remove from tracking.
        """
        if len(self.audio_input_rows) <= 1:
            return

        while row_layout.count():
            item = row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.audio_inputs_layout.removeItem(row_layout)
        self.audio_input_rows = [
            (layout, cb) for layout, cb in self.audio_input_rows
            if cb != combo
        ]

    def _add_video_inputs_section(self, layout: QVBoxLayout):
        """
        Add video inputs section with dynamic input controls.

        Args:
            layout: The layout to add the section to.
        """
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        header_layout = QHBoxLayout()
        video_label = QLabel("Video Inputs")
        header_layout.addWidget(video_label)

        add_video_button = QPushButton()
        add_video_button.setText("+")
        add_video_button.setFixedSize(30, 30)
        add_video_button.setProperty("class", "icon-button")
        add_video_button.setStyleSheet("""
            QPushButton {
                font-size: 22px !important;
                font-weight: 900 !important;
                padding: 0px !important;
                text-align: center !important;
            }
        """)
        add_video_button.clicked.connect(self._add_video_input_row)
        header_layout.addWidget(add_video_button)

        layout.addLayout(header_layout)

        self.video_inputs_layout = QVBoxLayout()
        layout.addLayout(self.video_inputs_layout)

        self._load_video_sources()
        screen_index = self._get_screen_capture_index()
        self._add_video_input_row(default_index=screen_index, is_screen_capture=True)
        self._add_video_input_row()

    def _load_video_sources(self):
        """Load available video sources from video service."""
        try:
            video_devices = video_service.list_video_devices()
            screen_capture = video_service.get_screen_capture_source()
            self.video_sources = video_devices + [screen_capture]
        except RuntimeError as e:
            self.video_sources = [f"Error: {str(e)}"]

    def _get_screen_capture_index(self) -> int:
        """
        Get the index of screen capture in video sources list.

        Returns:
            Index of screen capture device, or 0 if not found.
        """
        for idx, source in enumerate(self.video_sources):
            if "screen" in source.lower():
                return idx
        return 0

    def _add_video_input_row(self, default_index: int = 0, is_screen_capture: bool = False):
        """
        Add a new video input row with combobox and remove button.

        Args:
            default_index: Index to select by default in the combobox.
            is_screen_capture: If True, disable combo and don't add remove button.
        """
        row_layout = QHBoxLayout()

        combo = QComboBox()
        for source in self.video_sources:
            if ":" in source:
                name = source.split(":", 1)[1]
                combo.addItem(name, source)
            else:
                combo.addItem(source, source)
        combo.setCurrentIndex(default_index)
        combo.currentTextChanged.connect(self._on_video_source_changed)

        if is_screen_capture:
            combo.setEnabled(False)

        row_layout.addWidget(combo)

        if not is_screen_capture:
            remove_button = QPushButton()
            remove_button.setText("-")
            remove_button.setFixedSize(30, 30)
            remove_button.setProperty("class", "icon-button")
            remove_button.setStyleSheet("""
                QPushButton {
                    font-size: 22px !important;
                    font-weight: 900 !important;
                    padding: 0px !important;
                    text-align: center !important;
                }
            """)
            remove_button.clicked.connect(
                lambda: self._remove_video_input_row(row_layout, combo)
            )
            row_layout.addWidget(remove_button)

        self.video_inputs_layout.addLayout(row_layout)
        self.video_input_rows.append((row_layout, combo))

    def _remove_video_input_row(self, row_layout: QHBoxLayout, combo: QComboBox):
        """
        Remove a video input row from the layout.

        Args:
            row_layout: The layout to remove.
            combo: The combobox to remove from tracking.
        """
        if len(self.video_input_rows) <= 2:
            return

        while row_layout.count():
            item = row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.video_inputs_layout.removeItem(row_layout)
        self.video_input_rows = [
            (layout, cb) for layout, cb in self.video_input_rows
            if cb != combo
        ]

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        save_action = QAction("&Save Project", self)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        load_action = QAction("&Open Project", self)
        load_action.triggered.connect(self._load_project)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        import_action = QAction("&Import Project", self)
        import_action.triggered.connect(self._load_project)
        file_menu.addAction(import_action)

    def _save_project(self):
        """Save current project configuration to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "TutorialRecorder Project (*.trp);;All Files (*)"
        )

        if not filename:
            return

        config = self._get_current_config()

        try:
            project_service.save_project(config, filename)
            QMessageBox.information(self, "Success", "Project saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")

    def _load_project(self):
        """Load project configuration from a file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "TutorialRecorder Project (*.trp);;All Files (*)"
        )

        if not filename:
            return

        try:
            config = project_service.load_project(filename)
            self._load_config_to_ui(config)
            QMessageBox.information(self, "Success", "Project loaded successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {str(e)}")

    def _get_current_config(self) -> ProjectConfig:
        """
        Get current configuration from UI.

        Returns:
            Current project configuration.
        """
        audio_inputs = [
            AudioInput(device_name=combo.currentData())
            for _, combo in self.audio_input_rows
        ]

        video_inputs = [
            VideoInput(
                device_name=combo.currentData(),
                source_type="webcam" if "screen" not in combo.currentText().lower() else "screen"
            )
            for _, combo in self.video_input_rows
        ]

        return ProjectConfig(
            name=self.project_name_input.text(),
            audio_inputs=audio_inputs,
            video_inputs=video_inputs,
            screen_area=self.screen_area
        )

    def _load_config_to_ui(self, config: ProjectConfig):
        """
        Load configuration into UI.

        Args:
            config: Project configuration to load.
        """
        self.project_name_input.setText(config["name"])

        while len(self.audio_input_rows) > 0:
            layout, combo = self.audio_input_rows[0]
            self._remove_audio_input_row(layout, combo)

        for audio_input in config["audio_inputs"]:
            self._add_audio_input_row()
            _, combo = self.audio_input_rows[-1]
            index = combo.findText(audio_input["device_name"])
            if index >= 0:
                combo.setCurrentIndex(index)

        while len(self.video_input_rows) > 0:
            layout, combo = self.video_input_rows[0]
            self._remove_video_input_row(layout, combo)

        for video_input in config["video_inputs"]:
            self._add_video_input_row()
            _, combo = self.video_input_rows[-1]
            index = combo.findText(video_input["device_name"])
            if index >= 0:
                combo.setCurrentIndex(index)

    def _add_action_button(self, layout: QVBoxLayout):
        """
        Add the main action button (Record/Export) to the layout.

        Args:
            layout: The layout to add the button to.
        """
        self.action_button = QPushButton("Seleccionar Área")
        self.action_button.setMinimumHeight(40)
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self._handle_action_button)
        layout.addWidget(self.action_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_project_name_changed(self, text: str):
        """
        Handle project name changes to enable/disable Record button.

        Args:
            text: Current text in the project name input.
        """
        import re
        filtered_text = re.sub(r'[^a-zA-Z0-9_-]', '', text)

        if filtered_text != text:
            cursor_pos = self.project_name_input.cursorPosition()
            self.project_name_input.setText(filtered_text)
            self.project_name_input.setCursorPosition(max(0, cursor_pos - 1))

        if self.action_button.text() == "Seleccionar Área":
            self.action_button.setEnabled(
                bool(filtered_text.strip()) and self.export_path is not None
            )

    def _handle_action_button(self):
        """Handle Select Area/Stop button click based on current state."""
        if self.action_button.text() == "Seleccionar Área":
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        """Start a new recording session."""
        if not self.project_name_input.text():
            QMessageBox.warning(self, "Error", "Please enter a project name.")
            return

        if self._has_screen_capture() and not self.screen_area:
            self._show_screen_selector()
            return

        self._do_start_recording()

    def _has_screen_capture(self) -> bool:
        """
        Check if any video input is set to screen capture.

        Returns:
            True if screen capture is selected, False otherwise.
        """
        for _, combo in self.video_input_rows:
            if "screen" in combo.currentText().lower():
                return True
        return False

    def _do_start_recording(self):
        """Actually start the recording session."""
        config = self._get_current_config()

        try:
            self.recording_session = recording_service.start_recording(config)
            self.action_button.setText("Stop")
            self._create_tray_icon()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start recording: {str(e)}")

    def _stop_recording(self):
        """Stop the current recording session and auto-export."""
        if not self.recording_session:
            return

        try:
            self.temp_folder = self.recording_session.stop_recording()

            if self.export_path and self.temp_folder:
                project_name = self.project_name_input.text()
                recording_service.export_project(
                    self.temp_folder,
                    self.export_path,
                    project_name
                )
                export_full_path = Path(self.export_path) / project_name
                QMessageBox.information(
                    self,
                    "Recording Complete",
                    f"Recording stopped and exported to:\n{export_full_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "No export destination set."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop recording: {str(e)}")
        finally:
            self.action_button.setText("Seleccionar Área")
            self.temp_folder = None
            self.recording_session = None
            self._remove_tray_icon()
            if self.screen_selector:
                self.screen_selector.close()
                self.screen_selector = None

    def _select_export_destination(self):
        """Open dialog to select export destination folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Export Destination",
            ""
        )

        if folder:
            self.export_path = folder
            self.export_path_input.setText(folder)
            config_service.update_export_path(folder)
            if self.action_button.text() == "Seleccionar Área":
                self.action_button.setEnabled(
                    bool(self.project_name_input.text().strip())
                )

    def _on_video_source_changed(self, text: str):
        """
        Handle video source selection change.

        Args:
            text: Selected video source text.
        """
        pass

    def _show_screen_selector(self):
        """Show the screen selector overlay."""
        if self.screen_selector:
            self.screen_selector.close()

        self.screen_selector = ScreenSelector(self.default_resolution)
        self.screen_selector.recording_started.connect(self._on_recording_started)

    def _on_recording_started(self, area: dict):
        """
        Handle recording start from screen selector.

        Args:
            area: Dictionary with x, y, width, height, aspect_ratio.
        """
        self.screen_area = ScreenArea(
            x=area["x"],
            y=area["y"],
            width=area["width"],
            height=area["height"],
            aspect_ratio=area["aspect_ratio"]
        )

        if area["aspect_ratio"] != "Free":
            resolution = area["aspect_ratio"]
            self.default_resolution = resolution
            config_service.update_default_resolution(resolution)

        self._do_start_recording()

    def _check_permissions(self):
        """Check for camera and microphone permissions on macOS."""
        is_macos = (
            platform.system().lower() == "darwin" or
            sys.platform.startswith("darwin") or
            "darwin" in platform.platform().lower()
        )

        if not is_macos:
            return

        # Only show permissions warning on first run
        config = config_service.load_config()
        if config.get("permissions_warning_shown", False):
            return

        # Mark as shown
        config_service.update_config({"permissions_warning_shown": True})

        # Show informative message on first run only
        QMessageBox.information(
            self,
            "Permissions Required",
            "TutorialRecorder needs Camera, Microphone, and Screen Recording permissions.\n\n"
            "If prompted, please grant these permissions in:\n"
            "System Preferences → Security & Privacy → Privacy\n\n"
            "Note: You may need to restart the application after granting permissions.\n\n"
            "This message will only appear once."
        )

    def _create_tray_icon(self):
        """Create system tray icon for recording control."""
        if self.tray_icon:
            return

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        self.tray_icon.setToolTip("Recording in progress...")

        tray_menu = QMenu()
        stop_action = tray_menu.addAction("Stop Recording")
        stop_action.triggered.connect(self._stop_recording)

        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self.show)
        show_action.triggered.connect(self.activateWindow)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _remove_tray_icon(self):
        """Remove system tray icon."""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None

    def closeEvent(self, event):
        """
        Handle window close event to cleanup recording processes.

        Args:
            event: The close event.
        """
        if self.recording_session:
            try:
                self.recording_session.stop_recording()
            except Exception:
                pass

        if self.screen_selector:
            self.screen_selector.close()

        self.closed.emit()
        event.accept()
