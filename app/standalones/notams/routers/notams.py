from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Path
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ....deps import get_api_key
from ..helpers.notam_store import save_file
from ..helpers.notam_import import import_xls_bytes_to_notams
from ..notam_model import NOTAMs
from ..helpers.PyNotam.notam import Notam
from ....models import Airport, Regions
from datetime import datetime
from ....api_helpers.common import add_welcome_endpoint
from ..notam_db import get_db_n
from ....db import get_db
from ....helpers.utils_helper import make_polygon_shape

router = APIRouter()

add_welcome_endpoint(
    router,
    summary="NOTAM endpoints",
    description=(
        "Upload and query NOTAMs parsed from user-supplied XML/XLS export files. "
        "Files are stored raw in a small local sqlite DB; selection endpoints parse stored files on demand."
    ),
    tags=["NOTAMs"],
)

def _wrap_for_pynotam(raw_text: str) -> str:
    """
    PyNotam expects a NOTAM wrapped in parentheses and including header/clauses.
    We ensure parentheses, normalize newlines, and strip outer quotes if present.
    """
    if raw_text is None:
        return ""
    s = raw_text.strip()
    # Some exports wrap the whole NOTAM in quotes
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    # Normalize line endings
    s = s.replace("\r\n", "\n").replace("\r", "\n").strip()
    # Ensure outer parentheses as PyNotam grammar requires: root = "(" ... ")"
    if not s.startswith("("):
        s = "(" + s
    if not s.endswith(")"):
        s = s + ")"
    return s

def _pick_notam_text_row(row: Dict[str, Any]) -> str:
    """
    Prefer the full NOTAM text if present; otherwise fall back to the title/condition column.
    Your importer stores raw_text = title, so both are usually identical. This keeps future-proofing.
    """
    txt = row.get("raw_text") or row.get("notam_condition_subject_title") or ""
    return txt or ""

@router.post(
    "/upload/notams",
    summary="Upload NOTAM XML/XLS-export file",
    description=(
        "Store the uploaded file (XML or XLS-export text). The file's raw content is saved to a local sqlite DB. "
        "For XLS/XLSX files we also parse rows and populate the 'notams' table so legacy consumers can query immediately."
    ),
)
async def upload_notams(file: UploadFile = File(...), _api_key: str = Depends(get_api_key)):
    content_bytes = await file.read()
    # Store raw bytes (BLOB)
    file_id = save_file(file.filename, content_bytes)

    # Parse and populate notams (map by exact column index order)
    try:
        inserted = import_xls_bytes_to_notams(content_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import NOTAMs from file: {str(e)}")

    return {"detail": "File stored", "file_id": file_id, "notams_inserted": inserted}

@router.get(
    "/select/{region}",
    summary="Select NOTAMs by region",
    description=(
        "Return NOTAMs for the region. Optionally limit with selected_notams. "
        "In case of duplicates upstream, keep your selection explicit."
    ),
)
async def select_notams(
    region: str = Path(..., description="Region code e.g. SK, SC, K9", min_length=1, max_length=3),
    polygon: bool = Query(True),
    polygon_n_sides: int = Query(6),
    polygon_radius_nm: float = Query(1.5),
    center_lat: Optional[float] = Query(None),
    center_lon: Optional[float] = Query(None),
    selected_notams: Optional[str] = Query(None, description="Comma-separated NOTAM ids (e.g., C01239/23,C1909/11)"),
    _api_key: str = Depends(get_api_key),
    db_n: Session = Depends(get_db_n),
    db: Session = Depends(get_db)
):
    region_u = region.upper()
    selected_set = {s.strip().upper() for s in (selected_notams or "").split(",") if s.strip()}

    # Build query: region filter always, selected filter only if provided
    q = db_n.query(NOTAMs).filter(NOTAMs.location.startswith(region_u))
    if selected_set:
        q = q.filter(NOTAMs.notam_lta_number.in_(list(selected_set)))
    rows = q.all()
    # If nothing selected and no selected_notams filter provided, you might want to return nothing by design.
    # If you want all region notams when selected_notams is empty, the code above already does that.

    out = []
    for r in rows:
        rd = r.__dict__

        # Determine center
        c_lat, c_lon = 0.0, 0.0
        try:
            if center_lat is not None and center_lon is not None:
                c_lat = float(center_lat)
                c_lon = float(center_lon)
            else:
                # Airports table uses airport_identifier for 4-letter ICAO (e.g., SKBO)
                apt = db.query(Airport).filter(Airport.airport_identifier == rd["location"]).first()
                if apt:
                    c_lat = float(apt.airport_ref_latitude)
                    c_lon = float(apt.airport_ref_longitude)
                else:
                    # Regions table for FIR/centers like SKED, SKEC
                    fir = db.query(Regions).filter(Regions.fir_uir_identifier == rd["location"]).first()
                    if fir:
                        c_lat = float(fir.fir_uir_latitude)
                        c_lon = float(fir.fir_uir_longitude)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error determining center coordinates: {str(e)}")

        geojson, webeye = {}, {}
        if polygon:
            try:
                geojson = make_polygon_shape(
                    center=(c_lat, c_lon),
                    sides=polygon_n_sides,
                    radius_nm=polygon_radius_nm,
                    inclination=0.0,
                    output_format="geojson",
                )
                webeye = make_polygon_shape(
                    center=(c_lat, c_lon),
                    sides=polygon_n_sides,
                    radius_nm=polygon_radius_nm,
                    inclination=0.0,
                    output_format="webeye",
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error generating polygon: {str(e)}")

        # Parse NOTAM with PyNotam (ensure parentheses and normalized text)
        raw_for_parse = _pick_notam_text_row(rd)
        parsed_text: List[str] = []
        try:
            s = _wrap_for_pynotam(raw_for_parse)
            if s:
                _notam_obj = Notam.from_str(s)
                parsed_text = _notam_obj.decoded().split("\n")
            else:
                parsed_text = []
        except Exception:
            # Keep empty list if cannot parse; do not fail the entire request
            parsed_text = []

        out.append({
            "notam_icao": rd.get("location"),
            "notam_id": rd.get("notam_lta_number"),
            "original_notam": raw_for_parse,
            "parsed_notam": parsed_text,
            "polygons": {"geojson": geojson, "webeye": webeye},
            "center_lat": c_lat,
            "center_lon": c_lon,
            "issue_date": rd.get("issue_date_utc"),
            "effective_date": rd.get("effective_date_utc"),
            "expiration_date": rd.get("expiration_date_utc"),
            "file_uploaded_at": rd.get("uploaded_at"),
        })

    sel = [s.strip() for s in (selected_notams or "").split(",") if s.strip()]
    return {"center": region_u, "selected_notams": sel, "notams": out}

@router.get(
    "/parse/{icao}",
    summary="Return parsed NOTAM(s) for an ICAO",
    description="Parse stored files on-demand and return parsed/original for ICAO. Optional notam_id filters the result.",
)
def parse_route(
    icao: str = Path(..., description="Airport ICAO, e.g. SKBO"),
    notam_id: Optional[str] = Query(None, description="NOTAM id, e.g. C01239/23"),
    _api_key: str = Depends(get_api_key),
    db_n: Session = Depends(get_db_n),
):
    q = db_n.query(NOTAMs).filter(NOTAMs.location == icao.upper())
    if notam_id:
        q = q.filter(NOTAMs.notam_lta_number == notam_id.upper())
    rows = q.all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No NOTAMs found for {icao} {notam_id or ''}")

    out = []
    for r in rows:
        rd = r.__dict__
        raw_for_parse = _pick_notam_text_row(rd)
        parsed_text: List[str] = []
        try:
            s = _wrap_for_pynotam(raw_for_parse)
            if s:
                _notam_obj = Notam.from_str(s)
                parsed_text = _notam_obj.decoded().split("\n")
            else:
                parsed_text = []
        except Exception:
            parsed_text = []

        out.append({
            "notam_icao": icao.upper(),
            "notam_id": rd.get("notam_lta_number"),
            "parsed_notam": parsed_text,
            "original_notam": raw_for_parse,
        })
    return out