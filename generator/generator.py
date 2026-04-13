import asyncio
import httpx
import random
import time
import uuid
import sys
from datetime import datetime

API_URL = "http://localhost:8000/api/v1/ingest"
TARGET_RPS = 1000  # Requests per second we want to simulate
CONCURRENCY_LIMIT = 200 # Semaphore to limit active connections

def generate_sensor_event():
    # Mostly normal data, sometimes anomalous
    is_anomaly = random.random() < 0.05
    
    if not is_anomaly:
        return {
            "event_id": str(uuid.uuid4()),
            "sensor_id": f"sensor-{random.randint(1, 100)}",
            "temperature": round(random.uniform(15.0, 35.0), 2),
            "humidity": round(random.uniform(30.0, 70.0), 2),
            "traffic_count": random.randint(10, 60),
            "pollution_level": round(random.uniform(5.0, 40.0), 2)
        }
    else:
        # Generate anomalous data
        anom_type = random.choice(["heatwave", "traffic_jam", "pollution_spike"])
        event = {
            "event_id": str(uuid.uuid4()),
            "sensor_id": f"sensor-{random.randint(1, 100)}",
        }
        if anom_type == "heatwave":
            event.update({"temperature": round(random.uniform(45.0, 60.0), 2), "humidity": 15.0, "traffic_count": 20, "pollution_level": 30.0})
        elif anom_type == "traffic_jam":
            event.update({"temperature": 25.0, "humidity": 50.0, "traffic_count": random.randint(200, 500), "pollution_level": 150.0})
        else: # pollution spike
            event.update({"temperature": 20.0, "humidity": 60.0, "traffic_count": 40, "pollution_level": round(random.uniform(200.0, 500.0), 2)})
            
        return event

async def send_event(client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
    async with semaphore:
        event = generate_sensor_event()
        try:
            # Short timeout to avoid piling up if server slows down
            resp = await client.post(API_URL, json=event, timeout=2.0)
            return resp.status_code
        except Exception as e:
            # print(f"Error: {e}")
            return 500

async def main():
    print(f"Starting data generator against {API_URL}")
    print(f"Targeting {TARGET_RPS} requests per second with {CONCURRENCY_LIMIT} max concurrency.")
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Test mode: Running 1 batch of 10 requests and exiting.")
        events_to_send = 10
    else:
        events_to_send = 1000000 # Just run for a very long time
        
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    # We use limits to allow high concurrency
    limits = httpx.Limits(max_connections=500, max_keepalive_connections=100)
    
    async with httpx.AsyncClient(limits=limits) as client:
        start_time = time.time()
        successes = 0
        failures = 0
        tasks = []
        
        for i in range(events_to_send):
            # Throttle the task generation to approximate TARGET_RPS
            # If we just launched them all, we'd overwhelm concurrency limits instantly.
            # We want steady generation.
            
            # Note: A real precise load generator (like locust/vegeta) is better, but this works
            # for testing basic backpressure and throughput.
            task = asyncio.create_task(send_event(client, semaphore))
            tasks.append(task)
            
            # Simple rate limiting mechanism
            if len(tasks) >= TARGET_RPS / 10: # Check roughly every 100ms
                results = await asyncio.gather(*tasks)
                for r in results:
                    if r == 202 or r == 200:
                        successes += 1
                    else:
                        failures += 1
                tasks = []
                
                # Check how much time passed, if we were too fast, sleep
                elapsed = time.time() - start_time
                expected_time = (successes + failures) / TARGET_RPS
                if elapsed < expected_time:
                    await asyncio.sleep(expected_time - elapsed)
                    
                if (successes + failures) % 2000 == 0:
                    print(f"Stats: {successes} successful, {failures} failed. RPS: {round((successes+failures)/elapsed,2)}")

        # Await remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks)
            for r in results:
                if r == 202 or r == 200:
                    successes += 1
                else:
                    failures += 1
                    
        total_time = time.time() - start_time
        print(f"Finished. Total Requests: {successes + failures}. Success: {successes}, Fail: {failures}. Time: {round(total_time,2)}s. RPS: {round((successes+failures)/total_time,2)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
