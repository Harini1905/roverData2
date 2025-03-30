from fastapi import FastAPI
import random
import time
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Disaster Rover API is running!"}

def generate_rover_data():
    """Simulates autonomous rescue rover sensor data in disaster zones"""
    return {
        "timestamp": time.time(),
        "rover_id": f"RescueRover-{random.randint(100, 999)}",
        "position": {
            "x": round(random.uniform(0, 100), 2),  # Self-localized position
            "y": round(random.uniform(0, 100), 2)
        },
        "ultrasonic_distance": round(random.uniform(0.5, 5.0), 2),  # Obstacle detection
        "ir_signal_strength": round(random.uniform(0, 100), 2),  # Heat signature detection
        "rfid_detected": random.choice([True, False]),  # Survivor identification
        "accelerometer": {
            "x": round(random.uniform(-1, 1), 2),
            "y": round(random.uniform(-1, 1), 2),
            "z": round(random.uniform(-1, 1), 2)
        },
        "battery_level": round(random.uniform(10, 100), 2),  # Energy constraints
        "communication_status": random.choice(["Connected", "Intermittent", "Lost"])  # Limited communication
    }

@app.get("/api/disaster-rover-data")
def get_rover_data():
    return generate_rover_data()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Railway uses PORT env variable
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
