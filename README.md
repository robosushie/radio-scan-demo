# Radio Scan Demo

A real-time radio frequency spectrum analyzer and distance measurement system using PlutoSDR hardware. This project consists of a FastAPI backend for SDR processing and a Next.js frontend for visualization.

## 🚀 Features

- **Real-time FFT Spectrum Analysis**: Live frequency spectrum visualization
- **Distance Calculation**: RSSI-based distance measurement using free-space path loss model
- **Interactive Map**: Visual distance mapping with Leaflet
- **Live Measurements**: Real-time plotting of distance and signal strength
- **WebSocket Streaming**: Low-latency data streaming from backend to frontend
- **GPU Acceleration**: Optional CuPy/CUDA support for faster FFT processing
- **Centralized Configuration**: Single `frontend/constants.json` file for all settings

## 📁 Project Structure

```
radio-scan-demo/
├── frontend/                   # Next.js frontend application
│   ├── constants.json         # Central configuration file
│   ├── src/
│   │   ├── app/              # Next.js app router
│   │   │   ├── api/          # API routes (proxy to backend)
│   │   │   └── page.tsx      # Main application page
│   │   ├── components/       # React components
│   │   │   ├── ControlPanel.tsx
│   │   │   ├── DistanceMap.tsx
│   │   │   ├── LiveMeasurements.tsx
│   │   │   ├── SpectrumDataInfo.tsx
│   │   │   ├── SpectrumPlot.tsx
│   │   │   └── ConnectionStatus.tsx
│   │   ├── lib/              # Utility libraries
│   │   │   ├── constants.ts  # Constants import
│   │   │   ├── api.ts        # API service
│   │   │   └── websocket.ts  # WebSocket service
│   │   └── types/            # TypeScript type definitions
│   └── package.json
├── src/                       # Python backend
│   ├── main.py               # FastAPI server
│   └── utils/
│       ├── constants.py      # Constants loader
│       ├── device.py         # Device utilities
│       ├── pluto.py          # PlutoSDR interface
│       └── spectrum.py       # FFT processing
├── tests/                     # Backend tests
│   ├── scan_freq.py
│   ├── scan_samples.py
│   └── stitch.py
├── pyproject.toml            # Python dependencies
└── README.md                 # This file
```

## 🛠️ Prerequisites

- **Python 3.12+**
- **Node.js 18+** (for frontend)
- **PlutoSDR hardware** (or compatible SDR)
- **CUDA-capable GPU** (optional, for GPU acceleration)

## 📦 Installation

### Backend Setup

1. **Install Python dependencies:**

   ```bash
   # Using Poetry (recommended)
   poetry install

   # Or using pip
   pip install -r requirements.txt
   ```

2. **Install PlutoSDR drivers:**

   ```bash
   # Follow official PlutoSDR documentation
   # https://wiki.analog.com/university/courses/electronics/m1k-2.0
   ```

3. **Configure constants:**
   - Edit `frontend/constants.json` to match your PlutoSDR IP address
   - Update map center coordinates if needed
   - Adjust frequency and hardware settings

### Frontend Setup

1. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   # or
   yarn install
   # or
   bun install
   ```

## 🚀 Running the Application

### Development Mode

1. **Start the backend:**

   ```bash
   # From project root
   python src/main.py
   # or
   poetry run python src/main.py
   ```

2. **Start the frontend:**

   ```bash
   cd frontend
   npm run dev
   # or
   yarn dev
   # or
   bun dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Production Mode

1. **Build the frontend:**

   ```bash
   cd frontend
   npm run build
   npm start
   ```

2. **Run backend with production server:**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

All configuration is centralized in `frontend/constants.json`. Key sections:

- **`pluto`**: SDR hardware settings and connection
- **`map`**: Map center coordinates and zoom level
- **`distance`**: RSSI reference and distance calculation parameters
- **`endpoints`**: Server URLs and API paths
- **`cors`**: Cross-origin resource sharing settings

See [Constants.md](./Constants.md) for detailed configuration documentation.

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/scan_freq.py
python tests/scan_samples.py
python tests/stitch.py
```

### Frontend Tests

```bash
cd frontend
npm run lint
```

## 📊 API Endpoints

### Backend API (FastAPI)

- `GET /` - API information
- `GET /get_config` - Get current configuration
- `POST /set_rssi_ref` - Update RSSI reference value
- `POST /toggle_streaming` - Start/stop SDR streaming
- `WS /ws/stream` - WebSocket for real-time data

### Frontend API (Next.js proxy)

- `GET /api/get-config` - Proxy to backend config
- `POST /api/rssi-ref` - Proxy to backend RSSI update
- `POST /api/toggle-streaming` - Proxy to backend streaming control

## 🔄 Constants Management

The project uses a centralized constants system:

- **Backend**: Imports from `src/utils/constants.py` (loads from `frontend/constants.json`)
- **Frontend**: Imports from `frontend/src/lib/constants.ts` (loads from `frontend/constants.json`)
- **File**: Single `frontend/constants.json` file for all configuration

To update constants:

1. Edit `frontend/constants.json`
2. Restart both backend and frontend

## 🎯 Usage

1. **Connect PlutoSDR**: Ensure your PlutoSDR is connected and accessible
2. **Start the application**: Run both backend and frontend
3. **Configure RSSI Reference**: Set the reference RSSI value for distance calculation
4. **Start Streaming**: Click "Start Streaming" to begin data collection
5. **Monitor**: View real-time spectrum, distance measurements, and map visualization

## 🛠️ Troubleshooting

### Common Issues

1. **PlutoSDR Connection Failed**

   - Check IP address in `frontend/constants.json`
   - Ensure PlutoSDR is powered and connected
   - Verify network connectivity

2. **Frontend Can't Connect to Backend**

   - Check backend is running on correct port
   - Verify CORS settings in `frontend/constants.json`
   - Check firewall settings

3. **GPU Acceleration Not Working**
   - Install CuPy: `pip install cupy-cuda12x`
   - Verify CUDA installation
   - Check GPU compatibility

### Debug Mode

Enable debug logging in `frontend/constants.json`:

```json
{
  "system": {
    "debug": true,
    "log_level": "DEBUG"
  }
}
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Update constants documentation if needed
5. Submit a pull request

## 📚 Additional Resources

- [PlutoSDR Documentation](https://wiki.analog.com/university/courses/electronics/m1k-2.0)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Leaflet Documentation](https://leafletjs.com/)
- [Plotly.js Documentation](https://plotly.com/javascript/)
