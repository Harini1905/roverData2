from fastapi import FastAPI
import random
import time
import uuid
import threading

app = FastAPI()

sessions = {}
MAP_SIZE = (200, 200)  # Larger continuous space
OBSTACLE_COUNT = 15  # Number of obstacles per session

MOVEMENT_DELTAS = {
    "forward": (0, 1),
    "backward": (0, -1),
    "left": (-1, 0),
    "right": (1, 0)
}

def generate_obstacles():
    """Generates random obstacles in a continuous space."""
    return {(random.uniform(0, MAP_SIZE[0]), random.uniform(0, MAP_SIZE[1])) for _ in range(OBSTACLE_COUNT)}

def generate_sensor_data(position, battery_level, obstacles):
    """Generates realistic sensor data based on map conditions."""
    x, y = position
    obstacle_detected = any(abs(x - ox) < 1 and abs(y - oy) < 1 for ox, oy in obstacles)
    
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
        "accelerometer": accelerometer,
        "battery_level": round(battery_level, 2),
        "communication_status": "Active" if battery_level > 10 else "Intermittent",
        "recharging": battery_level < 80 and battery_level > 5
    }

def move_rover_continuously(session_id, direction):
    """Moves the rover, stops if an obstacle is detected."""
    while sessions[session_id]["status"] == f"Moving {direction}":
        dx, dy = MOVEMENT_DELTAS[direction]
        x, y = sessions[session_id]["coordinates"]
        new_position = (x + dx, y + dy)
        
        if any(abs(new_position[0] - ox) < 1 and abs(new_position[1] - oy) < 1 for ox, oy in sessions[session_id]["obstacles"]):
            sessions[session_id]["status"] = "Stopped - Obstacle Detected"
            return
        
        sessions[session_id]["coordinates"] = new_position
        sessions[session_id]["battery"] -= 1  # Battery drains with movement
        time.sleep(1)

@app.post("/api/session/start")
def start_session():
    """Creates a new session."""
    session_id = str(uuid.uuid4())
    obstacles = generate_obstacles()
    
    start_position = (random.uniform(0, MAP_SIZE[0]), random.uniform(0, MAP_SIZE[1]))
    while any(abs(start_position[0] - ox) < 1 and abs(start_position[1] - oy) < 1 for ox, oy in obstacles):
        start_position = (random.uniform(0, MAP_SIZE[0]), random.uniform(0, MAP_SIZE[1]))
    
    sessions[session_id] = {
        "status": "idle",
        "battery": random.randint(50, 100),
        "coordinates": start_position,
        "obstacles": obstacles
    }
    return {"session_id": session_id, "message": "Session started. Use this ID for API calls."}

@app.get("/api/rover/status")
def get_rover_status(session_id: str):
    """Returns the status of the rover."""
    return sessions.get(session_id, {"error": "Invalid session ID"})

@app.post("/api/rover/stop")
def stop_rover(session_id: str):
    """Stops the rover."""
    if session_id in sessions:
        sessions[session_id]["status"] = "idle"
        return {"message": "Rover has stopped."}
    return {"error": "Invalid session ID"}

@app.post("/api/rover/move")
def move_rover(session_id: str, direction: str):
    """Moves the rover if no obstacle is detected."""
    if session_id in sessions:
        if direction not in MOVEMENT_DELTAS:
            return {"error": "Invalid direction. Use forward, backward, left, or right."}
        
        sessions[session_id]["status"] = f"Moving {direction}"
        threading.Thread(target=move_rover_continuously, args=(session_id, direction), daemon=True).start()
        return {"message": f"Rover started moving {direction}"}
    return {"error": "Invalid session ID"}

@app.get("/api/rover/sensor-data")
def get_sensor_data(session_id: str):
    """Fetches sensor data based on the rover's current position."""
    if session_id in sessions:
        position = sessions[session_id]["coordinates"]
        battery_level = sessions[session_id]["battery"]
        obstacles = sessions[session_id]["obstacles"]
        return generate_sensor_data(position, battery_level, obstacles)
    return {"error": "Invalid session ID"}
