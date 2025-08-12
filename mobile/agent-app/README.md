# Agent App (Flutter)

Emergency response agent mobile application for handling panic alerts.

## Features

- **Alert Feed**: Real-time incoming panic alerts
- **Response Tools**: Quick response actions and status updates
- **Maps Integration**: Location tracking and navigation to alerts
- **Communication**: Direct communication with users in distress
- **Media Review**: View captured photos/videos/audio from alerts
- **Agent Status**: Availability and response capability management
- **Alert Assignment**: Automatic and manual alert assignment

## Screens

1. **Dashboard**: Overview of active alerts and agent status
2. **Alert Feed**: List of incoming and assigned alerts
3. **Alert Details**: Detailed view of specific alert with media
4. **Map View**: Geographic view of alerts and agent locations
5. **Response Actions**: Quick actions for alert response
6. **Agent Profile**: Agent information and settings
7. **Communication**: Chat/call interface with users

## Technical Details

- Flutter SDK 3.x
- Dart 3.x
- State management: Provider/Riverpod
- HTTP client: Dio
- Real-time updates: WebSocket/Server-Sent Events
- Maps: Google Maps/OpenStreetMap
- Push notifications: firebase_messaging
- Audio/Video calling: WebRTC