# Web Admin Portal (React)

Web-based administration portal for managing the Panic Alert System.

## Features

- **Alert Monitoring**: Real-time dashboard of all alerts
- **User Management**: Manage users, agents, and permissions
- **Agent Management**: Agent assignment, availability, and performance
- **Multimedia Review**: Review and manage captured media from alerts
- **Geofencing Configuration**: Set up and manage geofencing zones
- **System Analytics**: Reports and analytics on system usage
- **Configuration Management**: System settings and parameters

## Pages

1. **Dashboard**: Overview with key metrics and active alerts
2. **Alerts**: Alert management and monitoring
3. **Users**: User account management
4. **Agents**: Agent management and assignment
5. **Media**: Multimedia content review and management
6. **Geofencing**: Zone configuration and management
7. **Analytics**: Reports and system analytics
8. **Settings**: System configuration
9. **Audit Logs**: System activity and security logs

## Technical Stack

- React 18+ with TypeScript
- State Management: Redux Toolkit/Zustand
- UI Framework: Material-UI/Ant Design
- HTTP Client: Axios
- Real-time Updates: WebSocket/Server-Sent Events
- Charts: Chart.js/Recharts
- Maps: Leaflet/Google Maps
- Authentication: JWT with refresh tokens

## Security Features

- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- Session management
- Audit logging
- CSRF protection
- XSS protection