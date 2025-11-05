# Start Screen - Feature Specification

## Overview

The start screen is the application's entry point, providing users with two main options:
1. **Create a new recording project** (Grabar)
2. **Open an existing project** (Project)

## Design Specifications

### Window Properties
- **Dimensions**: 600px width × 400px height
- **Layout**: Fixed size, centered on screen
- **Title**: "TutorialRecorder"

### Visual Elements

#### Main Content Area
Two large, vertically centered icons with good spacing:

1. **Record Button (Grabar)**
   - Icon: Video camera SVG
   - Label: "Grabar" (below icon)
   - Action: Navigate to project configuration window

2. **Project Button (Project)**
   - Icon: Network/nodes SVG
   - Label: "Project" (below icon)
   - Action: Open folder picker → navigate to project viewer window

#### Footer Section
- Horizontal separator line
- Small text with donation message
- Clickable Ko-fi link: https://ko-fi.com/darkkaze

## Gherkin Scenarios

### Feature: Start Screen Navigation

```gherkin
Feature: Start Screen
  As a user
  I want to choose between creating a new recording or opening an existing project
  So that I can manage my tutorial recordings efficiently

  Background:
    Given the application is launched
    And the start screen is displayed
    And the window size is 600x400 pixels

  Scenario: Start screen displays correctly
    Then I should see the "Grabar" button with a video camera icon
    And I should see the "Project" button with a network icon
    And both buttons should be vertically centered
    And there should be adequate margins between buttons and window edges
    And I should see a horizontal line at the bottom
    And I should see a donation message with a clickable Ko-fi link

  Scenario: Create new recording project
    When I click on the "Grabar" button
    Then the project configuration window should open
    And the start screen should close

  Scenario: Open existing project - folder selection
    When I click on the "Project" button
    Then a folder picker dialog should open
    And the dialog should be titled "Select Project Folder"

  Scenario: Open existing project - valid folder selected
    Given I clicked on the "Project" button
    And the folder picker dialog is open
    When I select a valid project folder
    And I confirm the selection
    Then the project viewer window should open
    And the start screen should close
    And the selected project folder path should be passed to the project viewer

  Scenario: Open existing project - cancelled folder selection
    Given I clicked on the "Project" button
    And the folder picker dialog is open
    When I cancel the folder selection
    Then the folder picker dialog should close
    And the start screen should remain visible
    And no project viewer window should open

  Scenario: Ko-fi link is clickable
    When I click on the Ko-fi donation link
    Then my default web browser should open
    And it should navigate to "https://ko-fi.com/darkkaze"
    And the start screen should remain open

  Scenario: Window close behavior
    When I click the window close button
    Then the application should exit completely
```

## UI Component Hierarchy

```
StartScreenWindow (QWidget)
├── Main Container (QVBoxLayout)
│   ├── Icon Container (QHBoxLayout)
│   │   ├── Record Button (QPushButton)
│   │   │   ├── Video Camera Icon (SVG)
│   │   │   └── "Grabar" Label
│   │   └── Project Button (QPushButton)
│   │       ├── Network Icon (SVG)
│   │       └── "Project" Label
│   └── Footer Container (QVBoxLayout)
│       ├── Separator Line (QFrame)
│       └── Donation Message (QLabel with clickable link)
```

## Technical Notes

### SVG Icons
- Icons should be embedded as QIcon from SVG data
- Icon size: approximately 80-100px to be visually prominent
- Icons should have proper hover states for better UX

### Button Styling
- Large clickable areas (not just the icon)
- Visual feedback on hover
- Consistent spacing and alignment

### Navigation Flow
```
StartScreen
├─> "Grabar" → ProjectConfigWindow (existing)
└─> "Project" → FolderPicker → ProjectViewerWindow (new, placeholder)
```

### Project Folder Structure
Expected folder structure for valid projects (created by recording flow):
```
project_name/
├── mic1.wav
├── mic2.wav (optional)
├── webcam.mp4 (optional)
├── screen.mp4 (optional)
└── metadata.json (required)
```

## Future Enhancements
- Recent projects list
- Project thumbnails/previews
- Quick actions (delete, rename projects)
- Keyboard shortcuts (Enter for new project, Ctrl+O for open)
