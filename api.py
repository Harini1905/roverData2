from fastapi import FastAPI
import random
import time

app = FastAPI()

def generate_rover_data():
    """Simulates rover sensor data for disaster scenarios"""
    return {
        "timestamp": time.time(),
        "rover_id": f"RescueRover-{random.randint(100, 999)}",
        "position": {
            "x": round(random.uniform(0, 100), 2),
            "y": round(random.uniform(0, 100), 2)
        },
        "ultrasonic_distance": round(random.uniform(0.5, 5.0), 2),
        "ir_signal_strength": round(random.uniform(0, 100), 2),
        "rfid_detected": random.choice([True, False]),
        "accelerometer": {
            "x": round(random.uniform(-1, 1), 2),
            "y": round(random.uniform(-1, 1), 2),
            "z": round(random.uniform(-1, 1), 2)
        },
        "battery_level": round(random.uniform(10, 100), 2),
        "communication_status": random.choice(["Connected", "Intermittent", "Lost"])
    }

@app.get("/")
def read_root():
    return {"message": "Disaster Rover API is running!"}

@app.get("/api/disaster-rover-data")
def get_rover_data():
    return generate_rover_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
