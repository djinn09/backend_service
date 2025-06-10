from fastapi import FastAPI
from .database import engine, Base, SessionLocal # Added SessionLocal
from .routers import sips
from . import models
import logging # Added logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler # Added APScheduler
from datetime import date, datetime # Added datetime

# Setup logging
logging.basicConfig()
logging.getLogger("apscheduler").setLevel(logging.INFO)

try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables checked/created.")
except Exception as e:
    print(f"Error with database table creation: {e}")

app = FastAPI(
    title="SIP Tracker API",
    description="API for managing Systematic Investment Plans (SIPs)",
    version="0.1.0"
)

scheduler = AsyncIOScheduler()

def get_db_session_for_job(): # Helper to get a DB session for jobs
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def simulate_sip_execution_job():
    """Scheduled job to simulate monthly SIP executions."""
    logger = logging.getLogger(__name__)
    logger.info(f"Running SIP execution simulation job at {datetime.now()}...")
    db_gen = get_db_session_for_job()
    db = next(db_gen)
    try:
        today = date.today()
        active_sips = db.query(models.SIP).filter(models.SIP.start_date <= today).all()

        if not active_sips:
            logger.info("No active SIPs found for potential execution today.")
            return

        sips_executed_count = 0
        for sip_item in active_sips:
            # Execute if the SIP's start day of month matches today's day of month
            if sip_item.start_date.day == today.day:
                logger.info(f"SIMULATING EXECUTION for User ID {sip_item.user_id}: \n"
                            f"  Scheme: {sip_item.scheme_name}, Amount: {sip_item.monthly_amount}, Original Start Date: {sip_item.start_date}")
                sips_executed_count += 1
        logger.info(f"SIP execution job finished. Simulated {sips_executed_count} executions.")
    except Exception as e:
        logger.error(f"Error during SIP execution job: {e}", exc_info=True)
    finally:
        next(db_gen, None) # Ensure db session is closed

@app.on_event("startup")
async def startup_event():
    # Schedule job to run daily at a specific time, e.g., 2:30 AM
    # For testing, can use a shorter interval like every few minutes or seconds.
    # scheduler.add_job(simulate_sip_execution_job, "interval", seconds=60) # Test: Run every 60 seconds
    scheduler.add_job(simulate_sip_execution_job, "cron", hour=2, minute=30) # Run daily at 2:30 AM
    scheduler.start()
    print("APScheduler started. SIP execution job scheduled.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("APScheduler shut down.")

@app.get("/")
async def root():
    return {"message": "Welcome to SIP Tracker API. Visit /docs for API documentation."}

app.include_router(sips.router)
