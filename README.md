# Volleyball Scoreboard

A desktop application for adding an accurate score timeline to recorded volleyball game videos.

## Problem

Volleyball games are often recorded on an action camera and uploaded to YouTube for players, coaches, and parents to review. However, the recorded video usually does not contain the game score.

Without a score displayed on the video, it can be difficult to determine the game situation when reviewing a particular rally or play.

This application allows a user to record the score while reviewing the video and then automatically add the correct score to the final video.

## Goals

The application is designed to allow a user to:

1. Open a recorded volleyball game video.
2. Play, pause, seek, rewind, and fast-forward through the video.
3. Manually record a score change while watching the video.
4. Automatically capture the video timestamp when a score change is recorded.
5. Maintain the score for both teams throughout the game.
6. Review and remove previously recorded score events.
7. Save the score timeline so it can be reopened later.
8. Generate a new video with the current score displayed on the screen.
9. Preserve the original video file without modification.

## Application

![Volleyball Scoreboard](screenshots/scoreboard.png)

## Basic Workflow

### 1. Open Video

The user selects a recorded video file, such as an MP4 file from an action camera.

### 2. Record Scores

While watching the video, the user clicks a button whenever a team wins a point.

For example:

```text
Team A +1
Team B +1
```

The application records the video timestamp and the resulting score.

Example:

```text
00:13:04.250    Team A    13 - 12
00:13:27.800    Team B    13 - 13
00:13:51.420    Team A    14 - 13
```

### 3. Review Score Events

The recorded events are displayed in a timeline so the user can review the scoring history.

The application currently supports:

* Add a score event
* Select a recorded event
* Delete a selected event
* Undo the most recent score event
* Change team names before starting a game
* Configure the starting score

### 4. Save Game Data

The score timeline is saved separately from the original video.

The saved JSON data contains:

* Video information
* Team names
* Starting score
* Sets won
* Score-change events
* Video timestamps
* Resulting scores

### 5. Generate Scored Video

After the score timeline is complete, the user can generate a new video.

The application uses the recorded timestamps to determine which score should be displayed at each point in the video.

For example:

```text
00:00:00 - 00:13:04    12 - 12
00:13:04 - 00:13:27    13 - 12
00:13:27 - 00:13:51    13 - 13
00:13:51 - ...         14 - 13
```

The score is rendered onto the video using FFmpeg.

The original video remains unchanged.

## Functional Requirements

### Video Playback

* Open common video formats
* Play and pause
* Seek to a specific position
* Rewind and fast-forward
* Display current video time
* Display total video duration

### Score Management

* Two teams
* Configurable team names
* Configurable starting score
* Add one point to either team
* Display the current score
* Record the video timestamp for each score change
* Select a recorded score event
* Undo the most recent score change
* Delete a selected score event

### Project Management

* Create a new game
* Save game data
* Open an existing game
* Associate a project with a video file
* Keep score data separate from the original video

### Video Generation and Scoreboard Overlay

* Generate a new video containing a scoreboard overlay
* Display both team names and their current scores
* Update the displayed score based on the video timestamp
* Preserve the original video's audio
* Produce a new video file without modifying the original video
* Use FFmpeg for video processing

## Non-Functional Requirements

* Windows desktop application
* Simple and easy-to-use interface
* Works offline
* The original video must never be modified
* Score recording should be fast enough to use while reviewing a game
* Support long video files
* Handle video-processing errors without modifying the original video

## Future Improvements

The following features are outside the current version but may be considered later:

* Edit an existing score event
* Multiple sets with automatic set transitions
* Configurable scoreboard position
* Scoreboard themes and styling
* Video-generation progress information
* Keyboard shortcuts
* Export score data to CSV
* Generate YouTube chapters
* Volleyball-specific statistics
* Player information and jersey numbers
* Rally and rotation tracking
* Automatic rally detection using computer vision or AI
* Player recognition
* Automatic score recognition from the original video

## Initial Scope

The first version is intentionally simple:

**Manual score entry + video playback + score timeline + FFmpeg video overlay.**

AI and automatic score recognition are **not part of Version 1**.

## Technology

The current implementation uses:

* **Python** — application programming language
* **PySide6** — desktop GUI framework
* **FFmpeg** — video processing and scoreboard overlay
* **JSON** — game and score data storage

Technology choices may evolve as the project develops.

## Project Structure

```text
volleyball-scoreboard/
├── src/
│   └── main.py
├── screenshots/
│   └── scoreboard.png
├── examples/
│   └── sample_game.json
├── README.md
└── ...
```

## Sample Game Data

A sample game file is provided in `examples/sample_game.json`.

The file contains the team information, starting score, set scores, and timestamped scoring events used to generate the scoreboard overlay.

## Status

This project is actively under development.

The current version supports video playback, manual score entry, score-event management, saving and loading game data, and generating a scored video using FFmpeg.
