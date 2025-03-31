from fastapi import FastAPI
import random
import time
import uuid
import threading

app = FastAPI()

sessions = {}

# Define a fixed 2D map with obstacles and RFID points
MAP_SIZE = (20, 20)
OBSTACLES = {(5, 5), (10, 10), (15, 15)}  # Obstacles at fixed positions
RFID_POINTS = {(3, 3), (12, 8), (18, 18)}  # RFID detection points

MOVEMENT_DELTAS = {
    "forward": (0, 1),
    "backward": (0, -1),
    "left": (-1, 0),
    "right": (1, 0)
}

def generate_sensor_data(rover_id, position, battery_level):
    """Generates realistic sensor data based on map conditions."""
    x, y = position
    obstacle_detected = (x, y) in OBSTACLES
    rfid_detected = (x, y) in RFID_POINTS
    
    accelerometer = {
        "x": round(random.uniform(-0.2, 0.2), 2),
        "y": round(random.uniform(-0.2, 0.2), 2),
        "z": round(random.uniform(-0.5, 0.5), 2)
    }
    
    return {
        "timestamp": time.time(),
        "position": {"x": x, "y": y},
        "ultrasonic_distance": 0 if obstacle_detected else round(random.uniform(1.0, 10.0), 2),
        "ir_signal_strength": 1 if obstacle_detected else 0,
        "rfid_detected": rfid_detected,
        "accelerometer": accelerometer,
        "battery_level": round(battery_level, 2),
        "communication_status": "Active" if battery_level > 10 else "Intermittent",
        "recharging": battery_level < 80 and battery_level > 5
    }

def move_rover_continuously(session_id, rover_id, direction):
    """Moves the rover, stops if an obstacle is detected."""
    while sessions[session_id][rover_id]["status"] == f"Moving {direction}":
        dx, dy = MOVEMENT_DELTAS[direction]
        x, y = sessions[session_id][rover_id]["coordinates"]
        new_position = (x + dx, y + dy)
        
        if new_position in OBSTACLES:
            sessions[session_id][rover_id]["status"] = "Stopped - Obstacle Detected"
            return
        
        sessions[session_id][rover_id]["coordinates"] = new_position
        time.sleep(1)

@app.post("/api/session/start")
def start_session():
    """Creates a new session with a fleet."""
    session_id = str(uuid.uuid4())
    fleet_status = {}
    
    for i in range(1, 6):
        new_position = (random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1))
        while new_position in OBSTACLES:
            new_position = (random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1))
        
        fleet_status[f"Rover-{i}"] = {
            "status": "idle", 
            "battery": random.randint(50, 100), 
            "coordinates": new_position,
        }
    
    sessions[session_id] = fleet_status
    return {"session_id": session_id, "message": "Session started. Use this ID for API calls."}

@app.post("/api/rover/{rover_id}/stop")
def stop_rover(session_id: str, rover_id: str):
    """Stops the movement of a specific rover."""
    if session_id in sessions and rover_id in sessions[session_id]:
        sessions[session_id][rover_id]["status"] = "idle"
        return {"message": f"{rover_id} has stopped."}
    return {"error": "Invalid session or rover ID"}

@app.post("/api/rover/{rover_id}/move")
def move_rover(session_id: str, rover_id: str, direction: str):
    """Moves the rover if no obstacle is detected."""
    if session_id in sessions and rover_id in sessions[session_id]:
        if direction not in MOVEMENT_DELTAS:
            return {"error": "Invalid direction. Use forward, backward, left, or right."}
        
        sessions[session_id][rover_id]["status"] = f"Moving {direction}"
        threading.Thread(target=move_rover_continuously, args=(session_id, rover_id, direction), daemon=True).start()
        return {"message": f"{rover_id} started moving {direction}"}
    return {"error": "Invalid session or rover ID"}

@app.get("/api/rover/{rover_id}/sensor-data")
def get_sensor_data(session_id: str, rover_id: str):
    """Fetches realistic sensor data based on the rover's current position."""
    if session_id in sessions and rover_id in sessions[session_id]:
        position = sessions[session_id][rover_id]["coordinates"]
        battery_level = sessions[session_id][rover_id]["battery"]
        return generate_sensor_data(rover_id, position, battery_level)
    return {"error": "Invalid session or rover ID"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
