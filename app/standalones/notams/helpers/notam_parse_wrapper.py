import re
from typing import Tuple, Optional, Dict, Any, List

# Try to import richer parser from NOTAMs-CO-SQL if you copy it into app/helpers/notam_tools/
USE_PYNOTAM = False
try:
    from notam_from_nic import decode_notam as _decode_notam
    from .PyNotam.notam import Notam as _PyNotam_Notam
    USE_PYNOTAM = True
except Exception:
    USE_PYNOTAM = False

def parse_notam_text(text: str) -> Dict[str, Any]:
    """
    Return:
    {
      'notam_id': 'C0123/23',
      'location': 'SKBO',
      'parsed_notam': 'human readable parsed text' (string),
      'original_notam': 'original text' (string),
      'area': { 'lat': <float>, 'lon': <float>, 'radius_nm': <float> } or None
    }
    """
    # Prefer richer parser if available
    if USE_PYNOTAM:
        try:
            decoded = _decode_notam(text)
            parsed = decoded.get('description') or decoded.get('decoded') or ''
            area = None
            if decoded.get('area'):
                a = decoded['area']
                # NOTAMs-CO-SQL stores 'lat'/'long' possibly as strings (4809N); conversion not attempted here.
                try:
                    lat = float(a.get('lat')) if a.get('lat') is not None else None
                    lon = float(a.get('long')) if a.get('long') is not None else None
                except Exception:
                    lat = None
                    lon = None
                radius = a.get('radius')
                if lat is not None and lon is not None:
                    area = {'lat': lat, 'lon': lon, 'radius_nm': radius}
            return {
                'notam_id': decoded.get('notam_id') or '',
                'location': ''.join(decoded.get('location') or '') if decoded.get('location') else decoded.get('location') or '',
                'parsed_notam': parsed,
                'original_notam': text,
                'area': area
            }
        except Exception:
            pass

    # Fallback simple parser
    nid = _simple_extract_notam_id(text)
    loc = _simple_extract_a_clause(text)
    parsed = _simple_build_parsed(text)
    area = None
    m = re.search(r'PSN[:\s]*([0-9NS\.\s]+)\s*([0-9EW\.\s]+)\s*RADIUS[^\d]*([\d\.]+)\s*NM', text, re.IGNORECASE)
    if m:
        lat_s = m.group(1).strip()
        lon_s = m.group(2).strip()
        try:
            lat = _dms_text_to_decimal(lat_s)
            lon = _dms_text_to_decimal(lon_s)
            radius = float(m.group(3))
            area = {'lat': lat, 'lon': lon, 'radius_nm': radius}
        except Exception:
            area = None

    return {
        'notam_id': nid or '',
        'location': (loc or '').upper(),
        'parsed_notam': parsed,
        'original_notam': text,
        'area': area
    }

def _simple_extract_notam_id(text: str) -> Optional[str]:
    m = re.search(r'\(?([A-Z][0-9]{4}/[0-9]{2})', text)
    return m.group(1) if m else None

def _simple_extract_a_clause(text: str) -> Optional[str]:
    m = re.search(r'A\)\s*([A-Z0-9]{3,5})', text)
    return m.group(1) if m else None

def _simple_build_parsed(text: str) -> str:
    m = re.search(r'E\)\s*(.*)', text, re.IGNORECASE | re.DOTALL)
    e = m.group(1).strip() if m else None
    header = _simple_extract_notam_id(text) or ''
    a = _simple_extract_a_clause(text) or ''
    parts = []
    if header:
        parts.append(f"NOTAM {header}")
    if a:
        parts.append(f"Affects: {a}")
    if e:
        parts.append(f"Description: {e}")
    return "\n".join(parts) if parts else text.strip()

def _dms_text_to_decimal(s: str) -> float:
    s = s.strip().upper()
    m = re.match(r'(\d{2,3})(\d{2})(\d{2})?([NSWE])', s)
    if m:
        deg = int(m.group(1))
        min_ = int(m.group(2))
        sec = int(m.group(3)) if m.group(3) else 0
        hem = m.group(4)
        dec = deg + min_ / 60.0 + sec / 3600.0
        if hem in ('S', 'W'):
            dec = -dec
        return dec
    m = re.match(r'([0-9\.\-]+)\s*([NSWE])', s)
    if m:
        dec = float(m.group(1))
        if m.group(2) in ('S', 'W'):
            dec = -dec
        return dec
    return float(s)