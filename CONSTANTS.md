# Constants Configuration

This document provides detailed documentation for all configuration options in `frontend/constants.json`. The constants system is designed to provide centralized configuration for both frontend and backend components.

## 📁 File Locations

- **Primary**: `frontend/constants.json` - Central configuration file
- **Backend**: `src/utils/constants.py` - Python constants loader

## 🔄 Import Methods

### Frontend (TypeScript)

```typescript
import {
  SYSTEM_CONFIG,
  PLUTO_CONFIG,
  MAP_CONFIG,
  DISTANCE_CONFIG,
  ENDPOINTS_CONFIG,
  CORS_CONFIG,
} from "@/lib/constants";
import constants from "@/lib/constants"; // Full constants object
```

### Backend (Python)

```python
from utils.constants import CONSTANTS

# Access specific sections
pluto_config = CONSTANTS["pluto"]
map_config = CONSTANTS["map"]
```

## 📋 Configuration Sections

### 🖥️ System Configuration

```json
{
  "system": {
    "app_title": "Radio Scan Demo",
    "version": "1.0.0",
    "debug": false,
    "log_level": "INFO"
  }
}
```

| Field       | Type    | Default           | Description                                 |
| ----------- | ------- | ----------------- | ------------------------------------------- |
| `app_title` | string  | "Radio Scan Demo" | Application title displayed in UI           |
| `version`   | string  | "1.0.0"           | Application version for tracking            |
| `debug`     | boolean | false             | Enable debug mode for verbose logging       |
| `log_level` | string  | "INFO"            | Logging level (DEBUG, INFO, WARNING, ERROR) |

**Usage Examples:**

- Frontend: `SYSTEM_CONFIG.app_title` for page titles
- Backend: `CONSTANTS["system"]["debug"]` for conditional logging

### 📡 PlutoSDR Configuration

```json
{
  "pluto": {
    "connection": {
      "uri": "ip:192.168.2.1",
      "timeout": 5000
    },
    "hardware": {
      "sample_rate": 61440000,
      "rx_rf_bandwidth": 56000000,
      "rx_buffer_size": 16384,
      "gain_control_mode": "slow_attack",
      "rx_hardwaregain": 10
    },
    "spectrum": {
      "fft_size": 4096,
      "center_frequency": 155000000
    }
  }
}
```

#### Connection Settings

| Field     | Type   | Default          | Description                        |
| --------- | ------ | ---------------- | ---------------------------------- |
| `uri`     | string | "ip:192.168.2.1" | PlutoSDR connection URI            |
| `timeout` | number | 5000             | Connection timeout in milliseconds |

**Usage Examples:**

- Backend: `CONSTANTS["pluto"]["connection"]["uri"]` in `src/utils/pluto.py`
- Frontend: `PLUTO_CONFIG.connection.uri` for connection status display

#### Hardware Settings

| Field               | Type   | Default       | Description                      |
| ------------------- | ------ | ------------- | -------------------------------- |
| `sample_rate`       | number | 61440000      | Sampling rate in Hz (61.44 MSPS) |
| `rx_rf_bandwidth`   | number | 56000000      | RF bandwidth in Hz (56 MHz)      |
| `rx_buffer_size`    | number | 16384         | Number of samples per capture    |
| `gain_control_mode` | string | "slow_attack" | AGC mode for gain control        |
| `rx_hardwaregain`   | number | 10            | Hardware gain setting in dB      |

**Usage Examples:**

- Backend: Used in `src/main.py` for PlutoSDR configuration
- Frontend: `PLUTO_CONFIG.hardware.sample_rate` for spectrum display

#### Spectrum Settings

| Field              | Type   | Default   | Description                      |
| ------------------ | ------ | --------- | -------------------------------- |
| `fft_size`         | number | 4096      | FFT size for spectrum analysis   |
| `center_frequency` | number | 155000000 | Center frequency in Hz (155 MHz) |

**Usage Examples:**

- Backend: Used in `src/utils/spectrum.py` for FFT processing
- Frontend: `PLUTO_CONFIG.spectrum.center_frequency` for frequency axis

### 🗺️ Map Configuration

```json
{
  "map": {
    "center": {
      "latitude": 37.7749,
      "longitude": -122.4194
    },
    "zoom": 13
  }
}
```

| Field              | Type   | Default   | Description                          |
| ------------------ | ------ | --------- | ------------------------------------ |
| `center.latitude`  | number | 37.7749   | Map center latitude (San Francisco)  |
| `center.longitude` | number | -122.4194 | Map center longitude (San Francisco) |
| `zoom`             | number | 13        | Initial map zoom level (1-18)        |

**Usage Examples:**

- Frontend: `MAP_CONFIG.center.latitude` in `DistanceMap.tsx`
- Backend: Available via `/get_config` API endpoint

### 📏 Distance Configuration

```json
{
  "distance": {
    "rssi_ref_default": -50.0,
    "max_distance": 1000,
    "history_duration": 30000
  }
}
```

| Field              | Type   | Default | Description                                |
| ------------------ | ------ | ------- | ------------------------------------------ |
| `rssi_ref_default` | number | -50.0   | Default RSSI reference in dBm at 1 meter   |
| `max_distance`     | number | 1000    | Maximum distance for plot ranges in meters |
| `history_duration` | number | 30000   | Distance history duration in milliseconds  |

**Usage Examples:**

- Frontend: `DISTANCE_CONFIG.rssi_ref_default` in `page.tsx` for initial RSSI value
- Frontend: `DISTANCE_CONFIG.max_distance` in `LiveMeasurements.tsx` for plot range
- Frontend: `DISTANCE_CONFIG.history_duration` in `page.tsx` for data filtering
- Backend: Used in distance calculation formula

### 🌐 Endpoints Configuration

```json
{
  "endpoints": {
    "backend": {
      "host": "localhost",
      "port": 8000,
      "protocol": "http"
    },
    "websocket": {
      "host": "localhost",
      "port": 8000,
      "protocol": "ws",
      "path": "/ws/stream"
    },
    "frontend": {
      "host": "localhost",
      "port": 3000,
      "protocol": "http"
    },
    "api": {
      "rssi_ref": "/api/rssi-ref",
      "toggle_streaming": "/api/toggle-streaming",
      "get_config": "/api/get-config"
    }
  }
}
```

#### Backend Server

| Field      | Type   | Default     | Description             |
| ---------- | ------ | ----------- | ----------------------- |
| `host`     | string | "localhost" | Backend server hostname |
| `port`     | number | 8000        | Backend server port     |
| `protocol` | string | "http"      | Backend server protocol |

**Usage Examples:**

- Backend: `CONSTANTS["endpoints"]["backend"]` in `src/main.py` for server startup
- Frontend: Used for API proxy configuration

#### WebSocket Connection

| Field      | Type   | Default      | Description               |
| ---------- | ------ | ------------ | ------------------------- |
| `host`     | string | "localhost"  | WebSocket server hostname |
| `port`     | number | 8000         | WebSocket server port     |
| `protocol` | string | "ws"         | WebSocket protocol        |
| `path`     | string | "/ws/stream" | WebSocket endpoint path   |

**Usage Examples:**

- Frontend: `ENDPOINTS_CONFIG.websocket` in `page.tsx` for WebSocket connection
- Backend: Used for WebSocket endpoint configuration

#### Frontend Server

| Field      | Type   | Default     | Description              |
| ---------- | ------ | ----------- | ------------------------ |
| `host`     | string | "localhost" | Frontend server hostname |
| `port`     | number | 3000        | Frontend server port     |
| `protocol` | string | "http"      | Frontend server protocol |

#### API Routes

| Field              | Type   | Default                 | Description                      |
| ------------------ | ------ | ----------------------- | -------------------------------- |
| `rssi_ref`         | string | "/api/rssi-ref"         | RSSI reference update endpoint   |
| `toggle_streaming` | string | "/api/toggle-streaming" | Streaming control endpoint       |
| `get_config`       | string | "/api/get-config"       | Configuration retrieval endpoint |

**Usage Examples:**

- Frontend: Used in `frontend/src/lib/api.ts` for API calls
- Backend: Used for API endpoint routing

### 🔒 CORS Configuration

```json
{
  "cors": {
    "allow_origins": ["http://localhost:3000"],
    "allow_credentials": true,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
  }
}
```

| Field               | Type    | Default                   | Description                        |
| ------------------- | ------- | ------------------------- | ---------------------------------- |
| `allow_origins`     | array   | ["http://localhost:3000"] | Allowed CORS origins               |
| `allow_credentials` | boolean | true                      | Allow credentials in CORS requests |
| `allow_methods`     | array   | ["*"]                     | Allowed HTTP methods               |
| `allow_headers`     | array   | ["*"]                     | Allowed HTTP headers               |

**Usage Examples:**

- Backend: `CONSTANTS["cors"]` in `src/main.py` for CORS middleware configuration

## 🔧 Updating Constants

### Method 1: Direct Edit

1. Edit `frontend/constants.json`
2. Restart both backend and frontend

### Method 2: Environment-Specific Files (Optional)

For different environments, you can create copies:

```bash
# Development
cp frontend/constants.json frontend/constants.dev.json

# Production
cp frontend/constants.json frontend/constants.prod.json
```

### Method 3: Build Process

Add to your build process:

```json
// package.json
{
  "scripts": {
    "update-constants": "echo 'Edit frontend/constants.json and restart services'"
  }
}
```

## 🎯 Common Configuration Scenarios

### Changing PlutoSDR IP Address

```json
{
  "pluto": {
    "connection": {
      "uri": "ip:192.168.1.100"
    }
  }
}
```

### Updating Map Location

```json
{
  "map": {
    "center": {
      "latitude": 40.7128,
      "longitude": -74.006
    },
    "zoom": 15
  }
}
```

### Adjusting Frequency Range

```json
{
  "pluto": {
    "spectrum": {
      "center_frequency": 2400000000
    }
  }
}
```

### Modifying Distance Parameters

```json
{
  "distance": {
    "rssi_ref_default": -60.0,
    "max_distance": 500,
    "history_duration": 60000
  }
}
```

## 🔍 Validation

### JSON Schema Validation

```json
{
  "type": "object",
  "properties": {
    "system": { "type": "object" },
    "pluto": { "type": "object" },
    "map": { "type": "object" },
    "distance": { "type": "object" },
    "endpoints": { "type": "object" },
    "cors": { "type": "object" }
  },
  "required": ["system", "pluto", "map", "distance", "endpoints", "cors"]
}
```

### TypeScript Types

```typescript
interface Constants {
  system: SystemConfig;
  pluto: PlutoConfig;
  map: MapConfig;
  distance: DistanceConfig;
  endpoints: EndpointsConfig;
  cors: CorsConfig;
}
```

## 🚨 Important Notes

1. **Single Source of Truth**: All configuration is in `frontend/constants.json`
2. **Restart Required**: Changes require restarting both backend and frontend
3. **Validation**: Invalid JSON will cause application startup failures
4. **Backup**: Consider backing up your constants before major changes
5. **Environment**: Different constants files for different environments (dev/prod)

## 📚 Related Files

- `src/utils/constants.py` - Backend constants loader
- `frontend/src/lib/constants.ts` - Frontend constants importer
- `src/main.py` - Backend usage examples
- `frontend/src/app/page.tsx` - Frontend usage examples
