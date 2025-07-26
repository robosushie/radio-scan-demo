#!/usr/bin/env python3
"""
Single frequency FFT streaming demo with distance calculation.
FastAPI server for PlutoSDR with live FFT data and peak RSSI-based distance.
"""

import asyncio
import json
import os
import numpy as np
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.spectrum import SpectrumProcessor
from utils.device import connect_to_plutosdr, disconnect_from_plutosdr
from utils.constants import CONSTANTS

app = FastAPI(title="PlutoSDR Single Frequency Demo", version="1.0.0")

# Load constants from constants.json
# with open(os.path.join(os.path.dirname(__file__), '../constants.json'), 'r') as f:
#     CONSTANTS = json.load(f)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONSTANTS["cors"]["allow_origins"],
    allow_credentials=CONSTANTS["cors"]["allow_credentials"],
    allow_methods=CONSTANTS["cors"]["allow_methods"],
    allow_headers=CONSTANTS["cors"]["allow_headers"],
)

# Configuration for single frequency operation
pluto_hw = CONSTANTS["pluto"]["hardware"]
pluto_spectrum = CONSTANTS["pluto"]["spectrum"]
config = {
    "center_frequency": pluto_spectrum["center_frequency"],
    "sample_rate": pluto_hw["sample_rate"],
    "rx_rf_bandwidth": pluto_hw["rx_rf_bandwidth"],
    "rx_buffer_size": pluto_hw["rx_buffer_size"],
    "fft_size": pluto_spectrum["fft_size"],
    "gain_control_mode": pluto_hw["gain_control_mode"],
    "rx_hardwaregain": pluto_hw["rx_hardwaregain"]
}

# RSSI reference for distance calculation (default from constants)
distance_cfg = CONSTANTS["distance"]
RSSI_REF = distance_cfg["rssi_ref_default"]

# Global streaming state
streaming_enabled = False
pluto_sdr = None
spectrum_processor = None

# WebSocket connections
active_connections: Dict[WebSocket, bool] = {}
streaming_task: Optional[asyncio.Task] = None

class RSSIReference(BaseModel):
    rssi_ref: float

class StreamingToggle(BaseModel):
    streaming: bool

@app.get("/")
async def root():
    return {"message": "PlutoSDR Single Frequency Demo API"}

@app.post("/set_rssi_ref")
async def set_rssi_ref(rssi_ref: RSSIReference):
    """Set RSSI reference value for distance calculation"""
    global RSSI_REF
    try:
        RSSI_REF = rssi_ref.rssi_ref
        return {
            "status": "success",
            "message": f"RSSI reference updated to {RSSI_REF} dBm",
            "rssi_ref": RSSI_REF
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_config")
async def get_config():
    """Get current configuration"""
    return {
        "config": config,
        "rssi_ref": RSSI_REF
    }

@app.post("/toggle_streaming")
async def toggle_streaming(toggle: StreamingToggle):
    """Toggle PlutoSDR streaming on/off"""
    global streaming_enabled, pluto_sdr, spectrum_processor, streaming_task
    
    try:
        streaming_enabled = toggle.streaming
        
        if streaming_enabled:
            # Connect to PlutoSDR
            pluto_conn = CONSTANTS["pluto"]["connection"]
            pluto_sdr = connect_to_plutosdr(pluto_conn["uri"])
            if pluto_sdr:
                # Configure PlutoSDR for single frequency operation
                pluto_config = {
                    'sample_rate': config["sample_rate"],
                    'rx_rf_bandwidth': config["rx_rf_bandwidth"],
                    'rx_buffer_size': config["rx_buffer_size"],
                    'gain_control_mode': config["gain_control_mode"],
                    'rx_hardwaregain': config["rx_hardwaregain"]
                }
                pluto_sdr.set_configs(pluto_config)
                pluto_sdr.set_frequency(config["center_frequency"])
                
                # Initialize spectrum processor
                spectrum_processor = SpectrumProcessor(
                    fft_size=config["fft_size"],
                    sample_rate=config["sample_rate"],
                    center_frequency=config["center_frequency"]
                )
                
                # Start streaming task if we have connections
                if active_connections and (streaming_task is None or streaming_task.done()):
                    streaming_task = asyncio.create_task(spectrum_streaming_task())
                
                return {"status": "success", "streaming": True, "message": "PlutoSDR connected and streaming started"}
            else:
                streaming_enabled = False
                return {"status": "error", "streaming": False, "message": "Failed to connect to PlutoSDR"}
        else:
            # Stop streaming task
            if streaming_task and not streaming_task.done():
                streaming_task.cancel()
            
            # Disconnect from PlutoSDR
            if pluto_sdr:
                disconnect_from_plutosdr(pluto_sdr)
                pluto_sdr = None
                spectrum_processor = None
            return {"status": "success", "streaming": False, "message": "PlutoSDR disconnected and streaming stopped"}
            
    except Exception as e:
        streaming_enabled = False
        raise HTTPException(status_code=500, detail=str(e))

async def spectrum_streaming_task():
    """Background task for continuous FFT streaming and distance calculation"""
    global pluto_sdr, spectrum_processor
    
    while active_connections and streaming_enabled:
        try:
            if pluto_sdr and spectrum_processor and streaming_enabled:
                # Capture IQ samples
                iq_samples = pluto_sdr.capture_samples(config["rx_buffer_size"])
                
                # Process FFT and get peak RSSI
                frequencies, fft_data, peak_rssi = spectrum_processor.process_fft(iq_samples)
                
                # Calculate distance using the formula: distance = 10^((peak_rssi - RSSI_REF) / 20)
                distance = 10 ** ((peak_rssi - RSSI_REF) / 20)
                
                # Prepare data for streaming
                data = {
                    "frequencies": frequencies.tolist(),
                    "fft_data": fft_data.tolist(),
                    "peak_rssi": float(peak_rssi),
                    "distance": float(distance),
                    "rssi_ref": RSSI_REF,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                # Send to all connected clients
                disconnected = []
                for websocket in list(active_connections.keys()):
                    try:
                        await websocket.send_text(json.dumps(data))
                    except:
                        disconnected.append(websocket)
                
                # Remove disconnected clients
                for ws in disconnected:
                    active_connections.pop(ws, None)
            
            # Wait before next capture (approximately 20 FPS)
            await asyncio.sleep(0.05)
            
        except Exception as e:
            print(f"Error in streaming task: {e}")
            await asyncio.sleep(1.0)

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming FFT data"""
    global streaming_task
    
    await websocket.accept()
    active_connections[websocket] = True
    
    # Start streaming task if this is the first connection and streaming is enabled
    if len(active_connections) == 1 and streaming_enabled and (streaming_task is None or streaming_task.done()):
        streaming_task = asyncio.create_task(spectrum_streaming_task())
    
    try:
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.pop(websocket, None)
        
        # Stop streaming task if no more connections
        if len(active_connections) == 0 and streaming_task:
            streaming_task.cancel()

if __name__ == "__main__":
    import uvicorn
    backend_cfg = CONSTANTS["endpoints"]["backend"]
    uvicorn.run(app, host=backend_cfg["host"], port=backend_cfg["port"])