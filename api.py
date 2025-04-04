from fastapi import FastAPI
import random
import time
import uuid
import threading

app = FastAPI()

sessions = {}
MAP_SIZE = (250, 250)  # Larger grid-based space
OBSTACLE_COUNT = 20  # Number of obstacles per session

MOVEMENT_DELTAS = {
    "forward": (0, 1),
    "backward": (0, -1),
    "left": (-1, 0),
    "right": (1, 0)
}

def generate_obstacles():
    """Generates random obstacles in a grid-based space."""
    return {(random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1)) for _ in range(OBSTACLE_COUNT)}

def generate_sensor_data(position, battery_level, session_id):
    """Generates realistic sensor data based on map conditions."""
    x, y = position
    accelerometer = {
        "x": round(random.uniform(-0.2, 0.2), 2),
        "y": round(random.uniform(-0.2, 0.2), 2),
        "z": round(random.uniform(-0.5, 0.5), 2)
    }
    
    # Detect obstacles in proximity for ultrasonic and IR
    obstacles = sessions[session_id]["obstacles"]
    nearby_obstacle = any(
        abs(x - ox) <= 3 and abs(y - oy) <= 3 for ox, oy in obstacles
    )
    
    ultrasonic = {
        "distance": round(random.uniform(0.1, 3.0), 2) if nearby_obstacle else None,
        "detection": nearby_obstacle
    }
    
    ir = {
        "reflection": random.choice([True, False]) if nearby_obstacle else False
    }
    
    # Simulating RFID detection when near another rover
    other_rovers = [s for sid, s in sessions.items() if sid != session_id]
    rfid_detected = any(
        abs(x - r["coordinates"][0]) <= 2 and abs(y - r["coordinates"][1]) <= 2 for r in other_rovers
    )
    
    rfid = {
        "tag_detected": rfid_detected
    }
    
    return {
        "timestamp": time.time(),
        "position": {"x": x, "y": y},
        "accelerometer": accelerometer,
        "battery_level": round(battery_level, 2),
        "communication_status": "Active" if battery_level > 10 else "Intermittent",
        "recharging": battery_level < 80 and battery_level > 5,
        "ultrasonic": ultrasonic,
        "ir": ir,
        "rfid": rfid
    }

def move_rover_continuously(session_id, direction):
    """Moves the rover, stops if an obstacle is detected."""
    while sessions[session_id]["status"] == f"Moving {direction}" and sessions[session_id]["battery"] > 0:
        dx, dy = MOVEMENT_DELTAS[direction]
        x, y = sessions[session_id]["coordinates"]
        new_position = (x + dx, y + dy)
        
        if new_position in sessions[session_id]["obstacles"]:
            sessions[session_id]["status"] = "Stopped - Obstacle Detected"
            return
        
        sessions[session_id]["coordinates"] = new_position
        sessions[session_id]["battery"] -= 1  # Battery drains with movement
        
        if sessions[session_id]["battery"] <= 0:
            sessions[session_id]["status"] = "Stopped - Battery Depleted"
            return
        
        time.sleep(1)

@app.post("/api/rover/charge")
def charge_rover(session_id: str):
    """Charges the rover battery over time."""
    if session_id in sessions:
        sessions[session_id]["status"] = "Charging"
        while sessions[session_id]["battery"] < 100:
            sessions[session_id]["battery"] += 10
            time.sleep(1)
        sessions[session_id]["status"] = "Idle"
        return {"message": "Rover fully charged."}
    return {"error": "Invalid session ID"}

@app.post("/api/session/start")
def start_session():
    """Creates a new session."""
    session_id = str(uuid.uuid4())
    obstacles = generate_obstacles()
    
    start_position = (random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1))
    while start_position in obstacles:
        start_position = (random.randint(0, MAP_SIZE[0] - 1), random.randint(0, MAP_SIZE[1] - 1))
    
    sessions[session_id] = {
        "status": "idle",
        "battery": random.randint(50, 100),
        "coordinates": start_position,
        "obstacles": obstacles
    }
    return {"session_id": session_id, "message": "Session started. Use this ID for API calls."}

@app.get("/api/rover/status")
def get_rover_status(session_id: str):
    """Returns the status of the rover without obstacle coordinates."""
    if session_id in sessions:
        rover_status = sessions[session_id].copy()
        del rover_status["obstacles"]
        return rover_status
    return {"error": "Invalid session ID"}

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
        return generate_sensor_data(position, battery_level, session_id)
    return {"error": "Invalid session ID"}
