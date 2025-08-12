# User App (Flutter)

End-user panic alert mobile application.

## Features

- **Panic Button**: Large, accessible emergency button
- **Silent Activation**: Covert emergency mode
- **Profile Management**: User settings and emergency contacts
- **Alert Status**: Real-time status of sent alerts
- **Media Capture**: Automatic photo/video/audio during alerts
- **Geofencing**: Location-based alert zones
- **Theft Prevention**: Device security features

## Screens

1. **Home Screen**: Main panic button interface
2. **Profile Screen**: User settings and emergency contacts
3. **Alert History**: Past alerts and their status
4. **Settings**: App configuration and preferences
5. **Emergency Contacts**: Manage emergency contact list

## Technical Details

- Flutter SDK 3.x
- Dart 3.x
- State management: Provider/Riverpod
- HTTP client: Dio
- Local storage: Hive/SQLite
- Camera/Media: camera plugin
- Location: geolocator plugin
- Push notifications: firebase_messaging