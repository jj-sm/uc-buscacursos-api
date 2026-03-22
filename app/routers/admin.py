import secrets
import os
import airac_tools.cycle as airac_c
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, inspect
from ..auth_db import get_auth_db
from ..db import get_db, DATABASE_URL
from ..auth_models import APIKey
from ..models import AiracInfo
from ..api_helpers.common import add_welcome_endpoint
from ..deps import get_api_key
from dotenv import load_dotenv
from ..docs.responses import admin as r_admin

load_dotenv()
HIDE_ADMIN_ENDPOINTS = os.getenv("DEBUG", "0") == "1"

REQUIRED_TABLES = [
    "tbl_airport_communication",
    "tbl_airport_msa",
    "tbl_airports",
    "tbl_controlled_airspace",
    "tbl_cruising_tables",
    "tbl_enroute_airway_restriction",
    "tbl_enroute_airways",
    "tbl_enroute_communication",
    "tbl_enroute_ndbnavaids",
    "tbl_enroute_waypoints",
    "tbl_fir_uir",
    "tbl_gate",
    "tbl_gls",
    "tbl_grid_mora",
    "tbl_header",
    "tbl_holdings",
    "tbl_iaps",
    "tbl_localizer_marker",
    "tbl_localizers_glideslopes",
    "tbl_pathpoints",
    "tbl_restrictive_airspace",
    "tbl_runways",
    "tbl_sids",
    "tbl_stars",
    "tbl_terminal_ndbnavaids",
    "tbl_terminal_waypoints",
    "tbl_vhfnavaids",
]

def get_db_path():
    # Parse from SQLAlchemy URL (sqlite:///...)
    db_url = DATABASE_URL
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    raise RuntimeError("Non-sqlite databases not supported for update.")


router = APIRouter()

add_welcome_endpoint(router,
                     summary="Admin endpoints",
                     description="This route lists the available admin endpoints.",
                     tags=["Admin"])

@router.get(
    "/airac",
    summary="Airac Info",
    description="Get current AIRAC cycle information",
    responses=r_admin.GET_AIRAC_CYCLE_INFO,
)
def get_airac_cycle(db: Session = Depends(get_db)):
    cycle = airac_c.get_current_cycle()
    db_cycle = db.query(AiracInfo).one()
    db_c_cycle = db_cycle.current_airac if db_cycle else None
    return {'current_cycle': cycle,
            'valid_from': airac_c.get_cycle_start_date(cycle),
            'valid_to': airac_c.get_cycle_end_date(cycle),
            'updated': db_c_cycle == cycle,
            'db_cycle': db_c_cycle
            }


@router.post(
    "/update/airac",
    summary="Update AIRAC cycle",
    description="Update current AIRAC cycle database by uploading a new .s3db file.",
    responses={
        200: {"description": "Database updated successfully."},
        400: {"description": "Invalid file or missing tables."},
        500: {"description": "Server error during update."},
    },
    tags=["Admin"],
)
async def update_airac_cycle_db(
    file: UploadFile = File(...),
    api_key_tuple: tuple = Depends(get_api_key),
):
    """Upload a new AIRAC SQLite DB, validate, and replace the existing DB file."""
    db_path = get_db_path()
    temp_path = db_path + ".upload_tmp"

    try:
        # Save uploaded file to a temp path
        with open(temp_path, "wb") as out_file:
            content = await file.read()
            out_file.write(content)

        # Validate tables in uploaded DB
        engine = create_engine(f"sqlite:///{temp_path}")
        inspector = inspect(engine)
        found_tables = inspector.get_table_names()
        missing = [t for t in REQUIRED_TABLES if t not in found_tables]

        if missing:
            os.remove(temp_path)
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded DB is missing required tables: {', '.join(missing)}",
            )

        # Replace the existing DB file (ensure atomicity)
        backup_path = db_path + ".bak"
        if os.path.exists(db_path):
            os.replace(db_path, backup_path)
            engine.dispose()
        os.replace(temp_path, db_path)

        return {"detail": "Database updated successfully."}

    except HTTPException:
        raise
    except Exception as e:
        # Remove temp file if exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update database: {str(e)}",
        )

@router.post(
    "/keys",
    responses=r_admin.POST_ADMIN_KEYS,
    summary="Create API key (for admin use only)",
    include_in_schema=HIDE_ADMIN_ENDPOINTS
)
def create_api_key(name: str, db: Session = Depends(get_auth_db),
                   api_key_tuple: tuple = Depends(get_api_key)):
    new_key = secrets.token_urlsafe(32)
    key_obj = APIKey(key=new_key, name=name)
    db.add(key_obj)
    db.commit()
    db.refresh(key_obj)
    return {"key": key_obj.key, "name": key_obj.name}


@router.get(
    "/keys/list",
    responses=r_admin.GET_ADMIN_KEYS_LIST,
    summary="List API keys (for admin use only)",
    include_in_schema=HIDE_ADMIN_ENDPOINTS
)
def list_api_keys(db: Session = Depends(get_auth_db), api_key_tuple: tuple = Depends(get_api_key)):
    keys = db.query(APIKey).all()
    return [{"id": k.id, "key": k.key, "name": k.name, "active": k.active} for k in keys]


@router.patch(
    "/keys/{key_name}",
    responses=r_admin.PATCH_ADMIN_KEYS_KEYNAME,
    summary="Deactivate API key (for admin use only)",
    include_in_schema=HIDE_ADMIN_ENDPOINTS
)
def deactivate_api_key(key_name: str, db: Session = Depends(get_auth_db),
                       api_key_tuple: tuple = Depends(get_api_key)):
    try:
        if key_name.isdigit():
            key_obj = db.query(APIKey).filter(APIKey.id == int(key_name)).first()
        else:
            key_obj = db.query(APIKey).filter(APIKey.name == key_name).first()

        if key_obj:
            key_obj.active = False
            db.commit()
            return {"status": "deactivated"}

        return HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.get(
    "/authenticated",
    responses=r_admin.GET_ADMIN_AUTHENTICATED,
    summary="Check for user authentication"
)
def authenticated(api_key_tuple: tuple = Depends(get_api_key)):
    if _api_key:
        return {"status": "authenticated"}
    raise HTTPException(status_code=401, detail="Invalid API Key")
