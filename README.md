# volleyball-scoreboard
A Python desktop application for adding volleyball scores to recorded game videos.

## Problem
Volleyball games are often recorded on an action camera and uploaded to YouTube for players, coaches, and parents to review. However, the recorded video usually does not contain the game score.

Without a score displayed on the video, it can be difficult to determine the game situation when reviewing a particular rally or play.

This application allows the score to be recorded while reviewing the video and then automatically adds the correct score to the final video.

## Goals
The application should allow a user to:

Open a recorded volleyball game video.
Play, pause, seek, rewind, and fast-forward through the video.
Manually record a score change while watching the video.
Automatically capture the exact video timestamp when a score change is recorded.
Maintain the score for both teams throughout the game.
Review, edit, or remove previously recorded score events.
Save the score timeline so it can be reopened later.
Generate a new video with the current score displayed on the screen.
Preserve the original video file without modification.

## Basic Workflow
1. Open Video

The user selects a recorded video file, such as an MP4 file from an action camera.

2. Record Scores

While watching the video, the user clicks a button whenever a team wins a point.

For example:

Team A +1
Team B +1

The application records the video timestamp and the resulting score.

Example:

00:13:04.250    Team A    13 - 12
00:13:27.800    Team B    13 - 13
00:13:51.420    Team A    14 - 13
3. Review Score Events

The user can review the recorded events and correct mistakes.

The application should allow the user to:

Add an event
Edit an event
Delete an event
Undo the most recent event
Change team names
Change the starting score
4. Save Game Data

The score timeline should be saved separately from the original video.

The saved data should contain at least:

Video information
Team names
Starting score
Score-change events
Video timestamps
Resulting scores
5. Generate Scored Video

After the score timeline is complete, the user can generate a new video.

The application uses the recorded timestamps to determine which score should be displayed at each point in the video.

For example:

00:00:00 - 00:13:04    12 - 12
00:13:04 - 00:13:27    13 - 12
00:13:27 - 00:13:51    13 - 13
00:13:51 - ...          14 - 13

The score is rendered onto the video in a fixed location, such as the top-left or top-right corner.

The original video remains unchanged.

## Functional Requirements
-Video Playback
Open common video formats, initially MP4.
Play and pause.
Seek to a specific position.
Display current video time.
Display total video duration.
Support keyboard shortcuts where practical.

-Score Management
Two teams.
Configurable team names.
Configurable starting score.
Add one point to either team.
Display the current score.
Record the exact video timestamp for each score change.
Undo the last score change.
Edit or delete score events.

-Project Management
Create a new game project.
Save game data.
Open an existing game project.
Associate a project with a video file.
Keep score data separate from the original video.

-Video Generation
Generate a new video containing the scoreboard.
Display the correct score based on the video timestamp.
Allow configuration of scoreboard position.
Preserve the original video's audio.
Produce a new video file rather than modifying the original.

-Scoreboard Overlay
Display both team names together with their current scores.
Each team's name should appear next to its corresponding score.
The scoreboard should remain visible throughout the video.
The position of the scoreboard should be configurable.
The scoreboard should be readable without obscuring important parts of the video.

## Non-Functional Requirements

## Scoreboard Overlay

## Future Possibilities

## Initial Scope

## Technology
