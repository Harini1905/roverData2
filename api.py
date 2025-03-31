from fastapi import FastAPI
import random
import time
import os

app = FastAPI()

# Persistent storage for rover state
rover = {
    "timestamp": time.time(),
    "position": {"x": round(random.uniform(0, 100), 2), "y": round(random.uniform(0, 100), 2)},
    "ultrasonic_distance": round(random.uniform(1.0, 5.0), 2),  # Start with open space
    "ir_signal_strength": 0.0,  # No detection initially
    "rfid_detected": False,  # No survivor detected
    "accelerometer": {"x": 0.0, "y": 0.0, "z": 0.0},
    "battery_level": 100.0,  # Start fully charged
    "communication_status": "Connected",  # Assume good connection initially
    "recharging": False  # Flag to indicate recharging status
}

def update_rover_data():
    """Update rover data realistically over time."""
    rover["timestamp"] = time.time()
    
    # Smooth position change (simulate real movement)
    if not rover["recharging"]:
        rover["position"]["x"] += round(random.uniform(-0.5, 0.5), 2)
        rover["position"]["y"] += round(random.uniform(-0.5, 0.5), 2)
    
    # Simulate ultrasonic sensor detecting obstacles
    rover["ultrasonic_distance"] = max(0.3, min(5.0, rover["ultrasonic_distance"] + round(random.uniform(-0.5, 0.5), 2)))
    
    # IR signal increases if near a survivor (random event)
    if random.random() < 0.1:  # 10% chance of detecting a heat source
        rover["ir_signal_strength"] = round(random.uniform(50, 100), 2)
        rover["rfid_detected"] = random.choice([True, False])  # Possible survivor detection
    else:
        rover["ir_signal_strength"] = max(0, rover["ir_signal_strength"] - 5)
        rover["rfid_detected"] = False
    
    # Simulate rough terrain affecting accelerometer readings
    rover["accelerometer"] = {
        "x": round(random.uniform(-0.2, 0.2), 2),
        "y": round(random.uniform(-0.2, 0.2), 2),
        "z": round(random.uniform(-0.2, 0.2), 2)
    }
    
    # Battery drains realistically
    if not rover["recharging"]:
        rover["battery_level"] = max(0, rover["battery_level"] - round(random.uniform(0.1, 1.0), 2))
    
    # If battery is critically low, start recharging
    if rover["battery_level"] <= 5:
        rover["recharging"] = True
    
    # If recharging, slowly restore battery level
    if rover["recharging"]:
        rover["battery_level"] = min(80, rover["battery_level"] + round(random.uniform(1.0, 3.0), 2))
        if rover["battery_level"] >= 80:  # Stop recharging once it reaches 80%
            rover["recharging"] = False
    
    # Communication status changes based on battery & randomness
    if rover["battery_level"] < 10:
        rover["communication_status"] = "Lost"
    else:
        rover["communication_status"] = random.choice(["Connected", "Intermittent", "Lost"])
    
    return rover

@app.get("/")
def read_root():
    return {"message": "Disaster Rover API is running!"}

@app.get("/api/disaster-rover-data")
def get_rover_data():
    """Fetch realistic rover sensor data"""
    return update_rover_data()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Railway uses PORT env variable
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
