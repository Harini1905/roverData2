from fastapi import FastAPI
import random
import time
import uuid
import threading

app = FastAPI()

sessions = {}

# Movement deltas for coordinate updates
MOVEMENT_DELTAS = {
    "forward": (0, 1),
    "backward": (0, -1),
    "left": (-1, 0),
    "right": (1, 0)
}

# Fixed map (2D grid) with obstacles (1) and RFID tags (2)
MAP_GRID = {
    (0, 0): "Free", (1, 0): "Obstacle", (2, 0): "Free", (3, 0): "Free", (4, 0): "Free",
    (0, 1): "Free", (1, 1): "Free", (2, 1): "Free", (3, 1): "Obstacle", (4, 1): "Free",
    (0, 2): "RFID", (1, 2): "Free", (2, 2): "Free", (3, 2): "Free", (4, 2): "Free",
    (0, 3): "Free", (1, 3): "Free", (2, 3): "Free", (3, 3): "Free", (4, 3): "Obstacle",
    (0, 4): "Free", (1, 4): "Free", (2, 4): "Free", (3, 4): "Free", (4, 4): "Free"
}

def generate_sensor_data(rover_id, position, battery_level):
    """Simulates rover sensor data based on a fixed map"""
    x, y = position
    
    # Check if the position is an obstacle or RFID tag
    current_cell = MAP_GRID.get((x, y), "Free")
    obstacle_detected = current_cell == "Obstacle"
    rfid_detected = current_cell == "RFID"
    
    # Simulate sensor data based on obstacles or RFID detection
    ultrasonic_distance = round(random.uniform(0.5, 10.0), 2) if not obstacle_detected else 0
    ir_signal_strength = random.choice([0, 1]) if not obstacle_detected else 0

    accelerometer = {
        "x": round(random.uniform(-0.2, 0.2), 2),
        "y": round(random.uniform(-0.2, 0.2), 2),
        "z": round(random.uniform(-0.5, 0.5), 2)  # Simulating terrain elevation changes
    }
    
    # Adjust movement speed based on terrain elevation changes (z-axis)
    terrain_factor = max(0.5, 1 - abs(accelerometer["z"]))  # Speed reduces with rough terrain
    
    return {
        "timestamp": time.time(),
        "position": {"x": round(position[0] + random.uniform(-0.5, 0.5) * terrain_factor, 2), 
                      "y": round(position[1] + random.uniform(-0.5, 0.5) * terrain_factor, 2)},
        "ultrasonic_distance": ultrasonic_distance,
        "ir_signal_strength": ir_signal_strength,
        "rfid_detected": rfid_detected,
        "accelerometer": accelerometer,
        "battery_level": round(battery_level, 2),
        "communication_status": "Active" if battery_level > 10 else "Intermittent",
        "recharging": battery_level < 80 and battery_level > 5
    }

def update_map(position, obstacle_detected, rfid_detected):
    """Updates the map (though the map is static in this example, here we show where the rover is moving."""
    MAP_GRID[position] = "Obstacle" if obstacle_detected else "Free"
    if rfid_detected:
        MAP_GRID[position] = "RFID"

def move_rover_continuously(session_id, rover_id, direction):
    """Moves the rover continuously in the given direction over time, adapting to terrain"""
    while sessions[session_id][rover_id]["status"] == f"Moving {direction}":
        dx, dy = MOVEMENT_DELTAS[direction]
        x, y = sessions[session_id][rover_id]["coordinates"]
        
        # Simulate terrain adaptation with accelerometer z-axis affecting movement speed
        accelerometer = generate_sensor_data(rover_id, (x, y), sessions[session_id][rover_id]["battery"])["accelerometer"]
        terrain_factor = max(0.5, 1 - abs(accelerometer["z"]))  # Slower movement on rough terrain
        
        # Calculate the new coordinates with terrain adjustment
        new_x, new_y = (x + dx * terrain_factor, y + dy * terrain_factor)
        
        # Check for obstacles or RFID detection at the new position
        obstacle_detected = MAP_GRID.get((new_x, new_y), "Free") == "Obstacle"
        rfid_detected = MAP_GRID.get((new_x, new_y), "Free") == "RFID"
        
        # Update the map based on the rover's new position
        update_map((new_x, new_y), obstacle_detected, rfid_detected)
        
        # Update the rover's position
        sessions[session_id][rover_id]["coordinates"] = (new_x, new_y)
        time.sleep(1)  # Increment position every second

@app.post("/api/session/start")
def start_session():
    """Creates a new session with an isolated fleet"""
    session_id = str(uuid.uuid4())
    occupied_positions = set()
    fleet_status = {}
    
    for i in range(1, 6):
        while True:
            new_position = (random.randint(0, 4), random.randint(0, 4))  # Limited to the map size
            if new_position not in occupied_positions:
                occupied_positions.add(new_position)
                break
        
        fleet_status[f"Rover-{i}"] = {
            "status": "idle", 
            "battery": random.randint(50, 100), 
            "coordinates": new_position,
        }
    
    sessions[session_id] = fleet_status
    return {"session_id": session_id, "message": "Session started. Use this ID for API calls."}

@app.post("/api/rover/{rover_id}/stop")
def stop_rover(session_id: str, rover_id: str):
    """Stops the movement of a specific rover (per session)"""
    if session_id in sessions and rover_id in sessions[session_id]:
        sessions[session_id][rover_id]["status"] = "idle"
        return {"message": f"{rover_id} has stopped."}
    return {"error": "Invalid session or rover ID"}

@app.get("/api/rover/{rover_id}/sensor-data")
def get_sensor_data(session_id: str, rover_id: str):
    """Fetch sensor data from a specific rover (per session)"""
    if session_id in sessions and rover_id in sessions[session_id]:
        position = sessions[session_id][rover_id]["coordinates"]
        battery_level = sessions[session_id][rover_id]["battery"]
        return generate_sensor_data(rover_id, position, battery_level)
    return {"error": "Invalid session or rover ID"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Railway uses PORT env variable
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
