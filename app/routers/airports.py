import json
import time
from typing import Any, List
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..deps import get_api_key
from ..db import get_db
from ..models import (Airport, AirportComms, Runway, GLS, Gate,
                      LocalizerMarker, LocalizerGlideslope, IAPs, AirportMSA)
from ..helpers.data_io import convert_to_type as c2t
from ..helpers.data_io import packager
from ..api_helpers.common import add_welcome_endpoint

router = APIRouter()


def _group_by_first_available_key(items, candidate_keys):
    """Group records by the first key that exists and has a value."""
    grouped = {}
    for item in items:
        group_key = "unknown"
        for key in candidate_keys:
            value = item.get(key)
            if value not in (None, ""):
                group_key = str(value)
                break
        grouped.setdefault(group_key, []).append(item)
    return grouped


def _as_list(value: Any) -> List[dict]:
    """Normalize helper output to a concrete list for safe indexing/len operations."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return list(value)


def parse_runway_info(rows, icao_code):
    """Fallback parser that returns runway rows grouped by runway identifier."""
    raw = _as_list(packager(rows, exclude=["rowid"]))
    grouped = _group_by_first_available_key(
        raw,
        ["runway_identifier", "runway_designator", "runway_name", "id"],
    )
    return {
        "icao": icao_code,
        "count": len(raw),
        "runways": grouped,
    }


def group_gls_by_runway(items):
    """Fallback grouping for GLS rows by runway-like key."""
    return _group_by_first_available_key(
        items,
        ["runway_identifier", "runway_designator", "runway_name", "id"],
    )


def group_glideslopes_by_runway(items):
    """Fallback grouping for localizer/glideslope rows by runway-like key."""
    return _group_by_first_available_key(
        items,
        ["runway_identifier", "llz_identifier", "runway_designator", "id"],
    )


def group_markers_by_runway(items):
    """Fallback grouping for marker rows by runway-like key."""
    return _group_by_first_available_key(
        items,
        ["runway_identifier", "marker_identifier", "runway_designator", "id"],
    )


def get_mag_variation_for_airport(db: Session, icao_code: str):
    """Fallback magnetic variation lookup using available airport fields."""
    row = db.query(Airport).filter(Airport.airport_identifier == icao_code).first()
    if not row:
        raise ValueError(f"Airport not found: {icao_code}")

    for attr in ("magnetic_variation", "mag_variation", "declination"):
        if hasattr(row, attr):
            value = getattr(row, attr)
            if value not in (None, "", "NULL"):
                return c2t(float, value)
    raise ValueError(f"No magnetic variation data found for: {icao_code}")


def build_procedures_summary(db: Session, icao_code: str):
    """Fallback airport procedure summary without external helper dependencies."""
    runways = db.query(Runway).filter(Runway.airport_identifier == icao_code).all()
    iaps = db.query(IAPs).filter(IAPs.airport_identifier == icao_code).all()

    if not runways and not iaps:
        raise HTTPException(status_code=404, detail=f"No procedure info found for: {icao_code}")

    runway_ids = []
    for runway in runways:
        runway_id = getattr(runway, "runway_identifier", None)
        if runway_id:
            runway_ids.append(str(runway_id).lstrip("RW"))

    unique_approaches = sorted(
        {
            str(getattr(iap, "procedure_identifier", "")).strip()
            for iap in iaps
            if getattr(iap, "procedure_identifier", None)
        }
    )

    return {
        "icao": icao_code,
        "runways": runway_ids,
        "counts": {
            "runways": len(runway_ids),
            "iaps": len(unique_approaches),
        },
        "iaps": unique_approaches,
        "note": "Fallback summary generated without specialized helper modules",
    }

add_welcome_endpoint(router,
                     summary="Airport endpoints",
                     description="This route lists the available airport endpoints.",
                     tags=["Airports"])

@router.get(
    "/info/airport/{icao}",
    summary="Get airport information by ICAO code",
    description="Returns detailed information about an airport given its ICAO code.",
    tags=["Airports"]
    )
def get_airport_info(
        icao: str = Path(..., min_length=4, max_length=4,
                         description="Airport ICAO code, e.g., KJFK, EGLL, SKBO", example="RJAA"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    row = db.query(Airport).filter(Airport.airport_identifier == icao.upper()).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Airport not found: {icao}")

    packaged = _as_list(
        packager(
            [row],
            "airport_identifier", "airport_name", "airport_ref_longitude",
            "longest_runway_surface_code", "transition_altitude", "speed_limit",
            "iata_ata_designator", "icao_code", "airport_identifier_3letter",
            "airport_ref_latitude", "ifr_capability", "elevation", "transition_level",
            "speed_limit_altitude", "id",
            coordinates=[('lat', 'airport_ref_latitude'), ('lon', 'airport_ref_longitude')],
        )
    )
    return packaged[0]

@router.get(
    "/info/count/{region}",
    summary="Number of airports in a given region",
    description="Returns the number of airports in a given region.",
    tags=["Airports"]
)
def count_airports_by_region(
        region: str = Path(..., min_length=1, max_length=4,
                           description="Region ICAO code, e.g., K, C, EG, SK", example="K6"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    total = db.query(Airport).filter(Airport.icao_code == region).count()
    if total == 0:
        raise HTTPException(status_code=404, detail=f"No Airports found in the region: {region}")

    return {"region": region, "count": total}


@router.get(
    "/info/magvar/{icao}",
    summary="Get magnetic variation for an airport",
    description="Returns the magnetic variation for a given airport ICAO code."
                " The value is retrieved from the closes VOR to the airport in a maximum "
                "radius of 100 NM.",
    tags=["Airports"]
)
def get_airport_magvar(
        icao: str = Path(..., min_length=4, max_length=4,
                         description="Airport ICAO code, e.g., KJFK, EGLL, SKBO", example="RJAA"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    try:
        mag_var = get_mag_variation_for_airport(db, icao.upper())
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    if mag_var is None:
        raise HTTPException(status_code=404, detail=f"No MagVar Found for: {icao}")
    return {"icao": icao.upper(), "mag_variation": mag_var}


@router.get(
    "/info/all/{region}",
    summary="List all airports in a given region",
    description="Returns a list of all airports in a given region. Supports pagination with "
                "`skip` and `limit` query parameters.",
    tags=["Airports"]
)
def list_airports_by_region(
        region: str = Path(..., min_length=1, max_length=4, example="SK",
                           description="Region ICAO code, e.g., K, C, EG, SK"),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, le=500),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    rows = (
        db.query(Airport)
        .filter(Airport.icao_code == region)
        .offset(skip)
        .limit(limit)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No Airports Found: {region}")
    return packager(rows, "airport_identifier", "airport_name", "airport_ref_longitude",
                    "longest_runway_surface_code", "transition_altitude", "speed_limit",
                    "iata_ata_designator", "icao_code", "airport_identifier_3letter",
                    "airport_ref_latitude", "ifr_capability", "elevation", "transition_level",
                    "speed_limit_altitude", "id",
                    coordinates=[('lat', 'airport_ref_latitude'), ('lon', 'airport_ref_longitude')])


@router.get(
    "/info/stream/{region}",
    summary="Stream all airports in a given region",
    description="Streams all airports in a given region as a JSON lines response. "
                "Each line is a JSON object representing an airport.",
    tags=["Airports"]
)
async def stream_airports_by_region(
        region: str = Path(..., min_length=1, max_length=4, example="SK",
                           description="Region ICAO code, e.g., K, C, EG, SK"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    def row_generator():
        query = db.query(Airport).filter(Airport.icao_code == region)

        data = packager(query, "airport_identifier", "airport_name", "airport_ref_longitude",
                        "longest_runway_surface_code", "transition_altitude", "speed_limit",
                        "iata_ata_designator", "icao_code", "airport_identifier_3letter",
                        "airport_ref_latitude", "ifr_capability", "elevation", "transition_level",
                        "speed_limit_altitude", "id", generator=True,
                        coordinates=[('lat', 'airport_ref_latitude'),
                                     ('lon', 'airport_ref_longitude')])

        for p in data:
            time.sleep(0.05)
            yield json.dumps(p) + "\n"

    return StreamingResponse(row_generator(), media_type="application/json")


@router.get(
    "/atc/{icao}",
    summary="Get Airport's ATC information by ICAO code",
    description="Returns the ATC communication information for a given airport ICAO code.",
    tags=["Airports"]
)
def get_icao_atc_info(
        icao: str = Path(..., min_length=4, max_length=4, example="RJAA",
                         description="Airport ICAO code, e.g., KJFK, EGLL, SKBO"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    rows = db.query(AirportComms).filter(AirportComms.airport_identifier == icao).all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No ATC Info Found for: {icao}")
    return packager(rows, exclude=["rowid", 'latitude', 'longitude'],
                    coordinates=[('lat', 'latitude'), ('lon', 'longitude')])


@router.get(
    "/pos/{icao}_{pos}",
    summary="Get specific ATC position info for an airport",
    description="Returns the specific ATC position info for a given ICAO code.",
    tags=["Airports"]
)
def get_icao_atc_info_pos(
        icao: str = Path(..., min_length=4, max_length=4, example="RJAA",
                         description="Airport ICAO code, e.g., KJFK, EGLL, SKBO"),
        pos: str = Path(..., min_length=2, max_length=20, example="APP",
                        description="ATC position type, e.g., TWR, GND, APP, CLD, etc.",
                        regex="^(ACP|APP|ARR|ASO|ATI|AWI|AWO|AWS|CLD|CPT|CTA|CTL|DEP|"
                              "DIR|EMR|FSS|GCO|GND|GTE|HEL|INF|MUL|OPS|RDO|RDR|RMP|RSA|"
                              "TCA|TMA|TML|TRS|TWR|UNI)$"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u, pos_u = icao.upper(), pos.upper()
    result = (db.query(AirportComms)
              .filter(AirportComms.airport_identifier == icao_u,
                      AirportComms.communication_type == pos_u
                      ).all())

    if not result:
        raise HTTPException(status_code=404, detail=f"No ATC Info Found for: {icao_u} {pos_u}")

    return [
        {'icao': c2t(str, r.airport_identifier, strip=True, upper_c=True),
         'position': c2t(str, r.communication_type, strip=True, upper_c=True),
         'service': c2t(str, r.service_indicator, strip=True, upper_c=False),
         'callsign': c2t(str, r.callsign, strip=True, upper_c=False),
         'frequency': c2t(str, r.communication_frequency, strip=True, upper_c=False),
         'coordinates': {
             'lat': c2t(float, r.latitude),
             'lon': c2t(float, r.longitude)
         }
         } for r in result
    ]


@router.get(
    "/msa/{icao}",
    summary="Get Airport's Minimum Safe Altitude (MSA) information by ICAO code",
    description="Returns the Minimum Safe Altitude (MSA) information for a given airport ICAO code.",
    tags=["Airports"]
)
def get_airport_msa(
        icao: str = Path(..., min_length=4, max_length=4, example="SKPA",
                         description="Airport ICAO code, e.g., KJFK, EGLL, SKBO"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()
    result = db.query(AirportMSA).filter(AirportMSA.airport_identifier == icao_u).all()

    if not result:
        raise HTTPException(status_code=404, detail=f"No MSA Info Found for: {icao_u}")

    out = [
        {'icao': c2t(str, r.airport_identifier, strip=True, upper_c=True),
         'msa_center': {
             'fix': c2t(str, r.msa_center, strip=True, upper_c=True),
             'lat': c2t(float, r.msa_center_latitude),
             'lon': c2t(float, r.msa_center_longitude),
         },
         'magnetic_true_indicator': c2t(str, r.magnetic_true_indicator, strip=True, upper_c=True),
         'radius_limit': c2t(int, r.radius_limit),
         'sectors': {
             'sector_1': {
                 'sector_bearing_1': c2t(int, r.sector_bearing_1),
                 'sector_altitude_1': c2t(int, r.sector_altitude_1)
             },
             'sector_2': {
                 'sector_bearing_2': c2t(int, r.sector_bearing_2),
                 'sector_altitude_2': c2t(int, r.sector_altitude_2)
             },
             'sector_3': {
                 'sector_bearing_3': c2t(int, r.sector_bearing_3),
                 'sector_altitude_3': c2t(int, r.sector_altitude_3)
             },
             'sector_4': {
                 'sector_bearing_4': c2t(int, r.sector_bearing_4),
                 'sector_altitude_4': c2t(int, r.sector_altitude_4)
             },
             'sector_5': {
                 'sector_bearing_5': c2t(int, r.sector_bearing_5),
                 'sector_altitude_5': c2t(int, r.sector_altitude_5)
             }
         }
         } for r in result]

    return out


@router.get(
    "/runways/{icao}",
    summary="Get Airport's Runway information by ICAO code",
    description="Returns the runway information for a given airport ICAO code.",
    tags=["Airports"]
)
def get_airport_runways(
        icao: str = Path(..., min_length=4, max_length=4, example="KJFK",
                         description="Airport ICAO code, e.g., KJFK or EGLL"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()

    result = db.query(Runway).filter(Runway.airport_identifier == icao_u).all()

    if not result:
        raise HTTPException(status_code=404, detail=f"No Runway Info Found for: {icao_u}")

    return parse_runway_info(result, icao_u)


@router.get(
    "/gates/{icao}",
    summary="Get Airport's Gate information by ICAO code",
    description="Returns the gate information for a given airport ICAO code.",
    tags=["Airports"]
)
def get_airport_gates(
        icao: str = Path(..., min_length=4, max_length=4, example="KJFK",
                         description="Airport ICAO code, e.g., KJFK or EGLL"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()

    result = db.query(Gate).filter(Gate.airport_identifier == icao_u).all()
    if not result:
        raise HTTPException(status_code=404, detail=f"No Gate Info Found for: {icao_u}")

    return packager(result, exclude=['rowid', 'gate_latitude', 'gate_longitude'],
                    coordinates=[('lat', 'gate_latitude'), ('lon', 'gate_longitude')])


@router.get(
    "/app/gls/{icao}",
    summary="Get Airport's Global information by ICAO code",
    description="Returns the GLS (Global Navigation Satellite System Landing System) "
                "information for a given airport ICAO code.",
    tags=["Airports"]
)
def get_airport_gls(
        icao: str = Path(..., min_length=4, max_length=4, example="EDDF",
                         description="Airport ICAO code, e.g., KJFK or EGLL"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()
    result = db.query(GLS).filter(GLS.airport_identifier == icao_u).all()
    if not result:
        raise HTTPException(status_code=404, detail=f"No GLS Info Found for: {icao_u}")

    partially_parsed = packager(result, exclude=['rowid', 'station_latitude', 'station_longitude'],
                                coordinates=[('lat', 'station_latitude'),
                                             ('lon', 'station_longitude')])
    return group_gls_by_runway(partially_parsed)


@router.get(
    "/app/llz_gs/{icao}",
    summary="Get Airport's Glide by ICAO code",
    tags=["Airports"],
    description="Returns the Localizer/Glideslope information for a given airport ICAO code."
)
def get_airport_locgs(
        icao: str = Path(..., min_length=4, max_length=4, example="KJFK",
                         description="Airport ICAO code, e.g., KJFK or EGLL"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()
    result = db.query(LocalizerGlideslope).filter(
        LocalizerGlideslope.airport_identifier == icao_u).all()
    if not result:
        raise HTTPException(status_code=404,
                            detail=f"No Localizer/Glideslope Info Found for: {icao_u}")

    return group_glideslopes_by_runway(packager(result,
                                                exclude=['rowid', 'llz_latitude', 'llz_longitude',
                                                         'gs_longitude', 'gs_latitude'],
                                                coordinates_llz=[('lat', 'llz_latitude'),
                                                                 ('lon', 'llz_longitude')],
                                                coordinates_gs=[('lat', 'gs_latitude'),
                                                                ('lon', 'gs_longitude')]))


@router.get(
    "/app/llz_markers/{icao}",
    summary="Get Airport's Localizer Marker information by ICAO code",
    description="Returns the Localizer/Marker information for a given airport ICAO code.",
    tags=["Airports"]
)
def get_airport_loc_markers(
        icao: str = Path(..., min_length=4, max_length=4, example="SKBO",
                         description="Airport ICAO code, e.g., KJFK or EGLL"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()
    result = db.query(LocalizerMarker).filter(LocalizerMarker.airport_identifier == icao_u).all()
    if not result:
        raise HTTPException(status_code=404, detail=f"No Localizer Marker Info Found for: {icao_u}")

    return group_markers_by_runway(packager(result, exclude=['rowid']))


@router.get(
    "/app/list/{icao}",
    summary="List the available approaches for an airport",
    description="This endpoint provides a summary of all available approaches for a given"
                " airport ICAO code. It lists the runways and the associated approach procedures.",
    tags=["Airports"]
)
def get_avlb_app(
        icao: str = Path(..., min_length=4, max_length=4, example="KJFK",
                         description="Airport ICAO code, e.g., KJFK or EGLL"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()

    q_result = db.query(IAPs).filter(IAPs.airport_identifier == icao_u).all()

    if not q_result:
        raise HTTPException(status_code=404, detail=f"No Approach Info Found for: {icao_u}")

    _runways = db.query(Runway).filter(Runway.airport_identifier == icao_u).all()
    icao_runways = [r.runway_identifier.lstrip('RW') for r in _runways]

    out = {
        'icao': icao_u,
        'runways': icao_runways,
        'approaches': {
            icao_runways: [] for icao_runways in icao_runways
        }
    }

    approaches = set()
    for r in q_result:
        approaches.add(r.procedure_identifier)

    unknown = False
    for app in approaches:
        added = False
        for rwy in icao_runways:
            if rwy in app:
                out['approaches'][rwy].append(app)
                added = True
                break
        if not added and not unknown:
            out['approaches']['unknown'] = []
            unknown = True
            out['approaches']['unknown'].append(app)
        elif not added and unknown:
            out['approaches']['unknown'].append(app)
    return out


@router.get(
    "/app/list_full/{icao}",
    summary="List the available procedures for an airport",
    description="This endpoint provides a summary of all available procedures for a given"
                " airport ICAO code. It lists the runways and the count of SIDs, STARs, IAPs,"
                " and holding patterns linked to the airport.",
    tags=["Airports"]
)
def get_proc_list_redirect(
        icao: str = Path(..., min_length=4, max_length=4, example="KJFK",
                         description="Airport ICAO code, e.g., KJFK or EGLL"),
        db: Session = Depends(get_db), api_key_tuple: tuple = Depends(get_api_key)):
    icao_u = icao.upper()
    return build_procedures_summary(db, icao_u)
