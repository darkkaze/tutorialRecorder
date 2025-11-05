"""
TutorialRecorder - Main entry point.

This module initializes the Qt application and launches the main window.
"""
import sys
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from windows.start_screen import StartScreenWindow
from windows.project_config_window import ProjectConfigWindow
from windows.project_viewer_window import ProjectViewerWindow


class ApplicationController:
    """
    Application controller managing window navigation.

    Handles transitions between start screen, project config, and project viewer.
    """

    def __init__(self):
        """Initialize the application controller."""
        self.start_screen = None
        self.project_config = None
        self.project_viewer = None

    def show_start_screen(self):
        """Show the start screen."""
        self.start_screen = StartScreenWindow()
        self.start_screen.record_clicked.connect(self._on_record_clicked)
        self.start_screen.project_selected.connect(self._on_project_selected)
        self.start_screen.show()

    def _on_record_clicked(self):
        """Handle record button click from start screen."""
        if self.start_screen:
            self.start_screen.hide()

        self.project_config = ProjectConfigWindow()
        self.project_config.closed.connect(self._on_project_config_closed)
        self.project_config.show()

    def _on_project_selected(self, folder_path: str):
        """
        Handle project selection from start screen.

        Args:
            folder_path: Path to the selected project folder.
        """
        if self.start_screen:
            self.start_screen.hide()

        self.project_viewer = ProjectViewerWindow(folder_path)
        self.project_viewer.closed.connect(self._on_project_viewer_closed)
        self.project_viewer.show()

    def _on_project_config_closed(self):
        """Handle project config window close."""
        if self.project_config:
            self.project_config = None

        if self.start_screen:
            self.start_screen.show()

    def _on_project_viewer_closed(self):
        """Handle project viewer window close."""
        if self.project_viewer:
            self.project_viewer = None

        if self.start_screen:
            self.start_screen.show()


def main():
    """
    Initialize and run the TutorialRecorder application.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("TutorialRecorder")

    apply_stylesheet(app, theme='dark_teal.xml')

    controller = ApplicationController()
    controller.show_start_screen()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
