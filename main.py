import time
from fastapi import FastAPI
from long_bot import monitor_pairs  # Import your function

# Create FastAPI app instance
app = FastAPI()

# Define a simple route to ensure the app is running
@app.get("/")
async def root():
    return {"message": "Bot is running!"}

# If you want to run the monitor_pairs function as a background task, you can define it this way
@app.on_event("startup")
async def startup_event():
    # Call monitor_pairs function as background task (example)
    from threading import Thread
    def monitor():
        while True:
            monitor_pairs()
            time.sleep(60)
    
    Thread(target=monitor).start()
