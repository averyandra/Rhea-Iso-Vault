import os
import glob
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import pymysql

# Load configuration using pydantic-settings
class Settings(BaseSettings):
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    iso_directory: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

def init_db():
    """
    Initializes the database using schema.sql.
    Connects without specifying the database name to allow creation if it doesn't exist.
    """
    conn = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password
    )
    try:
        with conn.cursor() as cursor:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as file:
                sql_script = file.read()
            
            # Execute multiple statements by splitting them
            for statement in sql_script.split(';'):
                if statement.strip():
                    cursor.execute(statement)
        conn.commit()
        print(f"[{datetime.now()}] Database initialized successfully.")
    except Exception as e:
        print(f"[{datetime.now()}] Database initialization error: {e}")
    finally:
        conn.close()

def get_db_connection():
    """Returns a connection bound to the specific application database."""
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

def sync_iso_directory():
    """Scans the physical directory and synchronizes it with the database."""
    if not os.path.exists(settings.iso_directory):
        print(f"[{datetime.now()}] Directory {settings.iso_directory} not found.")
        return

    search_pattern = os.path.join(settings.iso_directory, "**/*.iso")
    physical_files = glob.glob(search_pattern, recursive=True)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Insert or update existing files
            for filepath in physical_files:
                filename = os.path.basename(filepath)
                size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                
                sql = """
                    INSERT INTO iso_files (filename, filepath, size_mb) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    size_mb = VALUES(size_mb), last_scanned = CURRENT_TIMESTAMP
                """
                cursor.execute(sql, (filename, filepath, size_mb))
            
            # 2. Remove database entries for files that no longer exist on disk
            cursor.execute("SELECT id, filepath FROM iso_files")
            db_records = cursor.fetchall()
            for record in db_records:
                if record['filepath'] not in physical_files:
                    cursor.execute("DELETE FROM iso_files WHERE id = %s", (record['id'],))
            
        conn.commit()
        print(f"[{datetime.now()}] Scan complete. Total physical ISOs: {len(physical_files)}")
    finally:
        conn.close()

# Scheduler setup
scheduler = AsyncIOScheduler()
scheduler.add_job(sync_iso_directory, 'cron', minute=0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Execute DB initialization on first startup (ignored safely on subsequent startups)
    init_db()
    # Start background scheduler
    scheduler.start()
    # Perform initial scan
    sync_iso_directory()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Allow CORS since frontend is served by Apache and API by Uvicorn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/isos")
async def get_isos():
    """Returns the list of ISOs from the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM iso_files ORDER BY filename ASC")
            isos = cursor.fetchall()
            return {"status": "success", "data": isos}
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

@app.post("/api/scan")
async def trigger_scan():
    """Manually triggers the directory scan."""
    try:
        sync_iso_directory()
        return {"status": "success", "message": "Directory scanned and synchronized."}
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)