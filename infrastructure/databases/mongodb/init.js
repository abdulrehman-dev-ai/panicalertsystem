// MongoDB Database Initialization Script
// Creates collections and indexes for real-time events

// Switch to the panic_events database
db = db.getSiblingDB('panic_events');

// Create collections with validation schemas

// Real-time alert events
db.createCollection('alert_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['alert_id', 'event_type', 'timestamp', 'data'],
      properties: {
        alert_id: {
          bsonType: 'string',
          description: 'UUID of the alert'
        },
        event_type: {
          bsonType: 'string',
          enum: ['created', 'status_changed', 'agent_assigned', 'media_uploaded', 'location_updated', 'resolved'],
          description: 'Type of alert event'
        },
        timestamp: {
          bsonType: 'date',
          description: 'Event timestamp'
        },
        data: {
          bsonType: 'object',
          description: 'Event-specific data'
        },
        user_id: {
          bsonType: 'string',
          description: 'UUID of the user'
        },
        agent_id: {
          bsonType: 'string',
          description: 'UUID of the agent (if applicable)'
        }
      }
    }
  }
});

// Location tracking events
db.createCollection('location_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'location', 'timestamp'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'UUID of the user or agent'
        },
        user_type: {
          bsonType: 'string',
          enum: ['user', 'agent'],
          description: 'Type of user'
        },
        location: {
          bsonType: 'object',
          required: ['lat', 'lng'],
          properties: {
            lat: {
              bsonType: 'double',
              minimum: -90,
              maximum: 90
            },
            lng: {
              bsonType: 'double',
              minimum: -180,
              maximum: 180
            },
            accuracy: {
              bsonType: 'double',
              description: 'Location accuracy in meters'
            },
            address: {
              bsonType: 'string',
              description: 'Human-readable address'
            }
          }
        },
        timestamp: {
          bsonType: 'date',
          description: 'Location update timestamp'
        },
        alert_id: {
          bsonType: 'string',
          description: 'Associated alert ID (if applicable)'
        }
      }
    }
  }
});

// Media upload events
db.createCollection('media_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['alert_id', 'media_type', 'file_path', 'timestamp'],
      properties: {
        alert_id: {
          bsonType: 'string',
          description: 'UUID of the alert'
        },
        media_type: {
          bsonType: 'string',
          enum: ['photo', 'video', 'audio'],
          description: 'Type of media'
        },
        file_path: {
          bsonType: 'string',
          description: 'Path to the media file'
        },
        file_size: {
          bsonType: 'long',
          description: 'File size in bytes'
        },
        duration: {
          bsonType: 'double',
          description: 'Duration in seconds (for video/audio)'
        },
        timestamp: {
          bsonType: 'date',
          description: 'Upload timestamp'
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional media metadata'
        }
      }
    }
  }
});

// Geofencing events
db.createCollection('geofence_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'zone_id', 'event_type', 'timestamp'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'UUID of the user'
        },
        zone_id: {
          bsonType: 'string',
          description: 'UUID of the geofence zone'
        },
        event_type: {
          bsonType: 'string',
          enum: ['entered', 'exited', 'dwelling'],
          description: 'Type of geofence event'
        },
        location: {
          bsonType: 'object',
          required: ['lat', 'lng'],
          properties: {
            lat: { bsonType: 'double' },
            lng: { bsonType: 'double' }
          }
        },
        timestamp: {
          bsonType: 'date',
          description: 'Event timestamp'
        }
      }
    }
  }
});

// System activity logs
db.createCollection('system_logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['level', 'message', 'timestamp'],
      properties: {
        level: {
          bsonType: 'string',
          enum: ['debug', 'info', 'warning', 'error', 'critical'],
          description: 'Log level'
        },
        message: {
          bsonType: 'string',
          description: 'Log message'
        },
        service: {
          bsonType: 'string',
          description: 'Service that generated the log'
        },
        user_id: {
          bsonType: 'string',
          description: 'Associated user ID (if applicable)'
        },
        agent_id: {
          bsonType: 'string',
          description: 'Associated agent ID (if applicable)'
        },
        timestamp: {
          bsonType: 'date',
          description: 'Log timestamp'
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional log data'
        }
      }
    }
  }
});

// Create indexes for better query performance

// Alert events indexes
db.alert_events.createIndex({ 'alert_id': 1 });
db.alert_events.createIndex({ 'timestamp': -1 });
db.alert_events.createIndex({ 'event_type': 1 });
db.alert_events.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.alert_events.createIndex({ 'agent_id': 1, 'timestamp': -1 });

// Location events indexes
db.location_events.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.location_events.createIndex({ 'location': '2dsphere' }); // Geospatial index
db.location_events.createIndex({ 'timestamp': -1 });
db.location_events.createIndex({ 'alert_id': 1 });

// Media events indexes
db.media_events.createIndex({ 'alert_id': 1 });
db.media_events.createIndex({ 'timestamp': -1 });
db.media_events.createIndex({ 'media_type': 1 });

// Geofence events indexes
db.geofence_events.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.geofence_events.createIndex({ 'zone_id': 1, 'timestamp': -1 });
db.geofence_events.createIndex({ 'event_type': 1 });
db.geofence_events.createIndex({ 'location': '2dsphere' });

// System logs indexes
db.system_logs.createIndex({ 'timestamp': -1 });
db.system_logs.createIndex({ 'level': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'service': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'user_id': 1, 'timestamp': -1 });

// Create TTL indexes for automatic data cleanup (optional)
// Remove location events older than 30 days
db.location_events.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 2592000 });

// Remove system logs older than 90 days
db.system_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 7776000 });

print('MongoDB collections and indexes created successfully!');
print('Collections created:');
print('- alert_events');
print('- location_events');
print('- media_events');
print('- geofence_events');
print('- system_logs');