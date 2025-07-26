#!/usr/bin/env python3
"""
FastAPI server for PlutoSDR spectrum scanning with WebSocket streaming.
"""

import asyncio
import json
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from utils.spectrum import scan_and_stitch_spectrum
from utils.pluto import PlutoSDR

app = FastAPI(title="PlutoSDR Spectrum Scanner", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global configuration
current_config = {
    "pluto_config": {
        'sample_rate': int(61.44e6),
        'rx_rf_bandwidth': int(30e6),
        'rx_buffer_size': 8192,
        'gain_control_mode': 'manual',
        'rx_hardwaregain': 10
    },
    "scan_config": {
        'start_frequency': int(1.4e9),
        'end_frequency': int(1.9e9),
        'step_frequency': int(20e6),
        'dwell_time': 0.05
    },
    "fft_config": {
        'fft_size': 2048,
        'min_peak_height': -40.0,
        'peak_threshold_db': 25.0,
        'window_size_divisor': 100,
        'min_window_size': 5,
        'max_peaks_per_band': 10
    }
}

# Global streaming state
streaming_enabled = False
pluto_sdr = None

# WebSocket connections
active_connections: Dict[WebSocket, bool] = {}
streaming_task: Optional[asyncio.Task] = None

class ScanParams(BaseModel):
    start_frequency: int
    end_frequency: int  
    step_frequency: int = int(20e6)
    gain: int = 10
    dwell_time: float = 0.05

class PlutoParams(BaseModel):
    sample_rate: int = int(61.44e6)
    rx_rf_bandwidth: int = int(30e6)
    rx_buffer_size: int = 8192
    gain_control_mode: str = 'manual'
    rx_hardwaregain: int = 10

class StreamingToggle(BaseModel):
    streaming: bool

@app.get("/")
async def root():
    return {"message": "PlutoSDR Spectrum Scanner API"}

@app.post("/set_scan_params")
async def set_scan_params(params: ScanParams):
    """Set scanning parameters"""
    try:
        current_config["scan_config"].update({
            'start_frequency': params.start_frequency,
            'end_frequency': params.end_frequency,
            'step_frequency': params.step_frequency,
            'dwell_time': params.dwell_time
        })
        current_config["pluto_config"]["rx_hardwaregain"] = params.gain
        
        return {
            "status": "success",
            "message": "Scan parameters updated",
            "config": current_config["scan_config"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/set_pluto_params")
async def set_pluto_params(params: PlutoParams):
    """Set PlutoSDR hardware parameters"""
    try:
        current_config["pluto_config"].update(params.dict())
        
        return {
            "status": "success", 
            "message": "PlutoSDR parameters updated",
            "config": current_config["pluto_config"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_config")
async def get_config():
    """Get current configuration"""
    return current_config

@app.post("/toggle_streaming")
async def toggle_streaming(toggle: StreamingToggle):
    """Toggle PlutoSDR streaming on/off"""
    global streaming_enabled, pluto_sdr, streaming_task
    
    try:
        streaming_enabled = toggle.streaming
        
        if streaming_enabled:
            # Connect to PlutoSDR
            from utils.device import connect_to_plutosdr
            pluto_sdr = connect_to_plutosdr("ip:192.168.2.1")
            if pluto_sdr:
                pluto_sdr.set_configs(current_config["pluto_config"])
                
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
                from utils.device import disconnect_from_plutosdr
                disconnect_from_plutosdr(pluto_sdr)
                pluto_sdr = None
            return {"status": "success", "streaming": False, "message": "PlutoSDR disconnected and streaming stopped"}
            
    except Exception as e:
        streaming_enabled = False
        raise HTTPException(status_code=500, detail=str(e))

async def spectrum_streaming_task():
    """Background task for continuous spectrum scanning and streaming"""
    global pluto_sdr
    
    while active_connections and streaming_enabled:
        try:
            if pluto_sdr and streaming_enabled:
                # Perform spectrum scan with existing connection
                from utils.spectrum import scan_and_stitch_spectrum_with_connection
                frequencies, power_spectrum = scan_and_stitch_spectrum_with_connection(
                    pluto_sdr,
                    current_config["fft_config"], 
                    current_config["scan_config"]
                )
                
                if len(frequencies) > 0:
                    # Prepare data for streaming
                    data = {
                        "frequencies": frequencies.tolist(),
                        "power_spectrum": power_spectrum.tolist(),
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
            
            # Wait before next scan
            await asyncio.sleep(1.0)
            
        except Exception as e:
            print(f"Error in streaming task: {e}")
            await asyncio.sleep(2.0)

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
    uvicorn.run(app, host="0.0.0.0", port=8000)