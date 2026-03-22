# Changelog

All notable changes to the Universal API Template project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Universal API Template Release

### Added
- **Tier-Based Authentication System**:
  - 4 configurable tiers (Free, Pro, Premium, Enterprise)
  - Tier-specific rate limits (10, 100, 1000, unlimited req/s)
  - Max burst configuration per tier
  - TierEnum and TIER_CONFIG for easy customization

- **Rate Limiting**:
  - Sliding-window rate limiter with 1-second precision
  - Per-API-key rate limit tracking
  - Automatic cleanup of expired rate limit buckets
  - Detailed rate limit info in responses (Remaining, Reset)

- **API Key Management**:
  - AdminKeyManager class with 7 lifecycle operations
  - Create, list, update tier, deactivate, reactivate keys
  - Usage statistics and key information endpoints
  - Extended APIKey model with owner metadata

- **Example Routers**:
  - `template.py` with 8 endpoint pattern examples
  - `airports.py` for real-world database integration
  - Full CRUD patterns, search, filtering, and error handling

- **Comprehensive Documentation**:
  - DEVELOPER_QUICKSTART.md (5-minute start guide)
  - QUICK_REFERENCE.md (quick lookup of common tasks)
  - API_TEMPLATE_GUIDE.md (complete setup and usage)
  - ROUTER_MIGRATION_GUIDE.md (guide for creating routers)
  - PROJECT_STRUCTURE.md (detailed project overview)

- **Generic Data Models**:
  - `generic_models.py` with base model templates
  - GenericResource, GenericLocation, GenericEvent examples
  - Polymorphic inheritance patterns for extensibility

- **Production-Ready Features**:
  - CORS middleware with configurable origins
  - Request logging middleware
  - Health check endpoint (`/health`)
  - Root info endpoint (`/`)
  - Environment-based configuration

### Changed
- **Refactored from AIRAC API to Universal Template**:
  - Removed 10 specialized aviation routers
  - Removed 18 specialized helper modules
  - Removed C++ helper directories
  - Streamlined to 3 example routers and 1 utility helper
  - Updated terminology throughout (AIRAC → Universal)
  - Renamed from "AIRAC API Service" to "Universal API Template"

- **Enhanced Authentication**:
  - `get_api_key()` now returns tuple with (api_key, tier, rate_limit_info)
  - Improved rate limit info structure with comprehensive details
  - Better error messages on rate limit exceeded (429)

- **Updated Configuration**:
  - Renamed AIRAC_DB_URL → DATABASE_URL
  - Renamed AUTH_DB_URL → AUTH_DATABASE_URL
  - Added CORS_ORIGINS configuration
  - Added LOG_LEVEL configuration
  - Removed IVAO-specific variables

- **Project Structure**:
  - Simplified from 40+ files to ~20 core files
  - Updated documentation links throughout
  - Reorganized helpers to emphasis reusability

### Fixed
- Removed all AIRAC and IVAO-specific code
- Removed tightly-coupled aviation data references
- Eliminated specialized geospatial operations not needed for generic API

### Removed
- **Routers (10)**:
  - airspace.py, enroute.py, maps.py, maps_view.py, navaids.py
  - poly_search.py, procedures.py, sectorfile.py, utils.py, webeye.py

- **Helpers (18)**:
  - airport_data_helper.py, airspace_helper.py, coordinates_converter.py
  - enhanced_procedure_helper.py, geo_helper.py, geoairac.py, geoairac_2.py
  - holding_helper.py, path_helper.py, poly_search_helper.py
  - procedure_helper.py, procedures_data.py, process_procedures.py
  - process_sids.py, process_stars.py, sectorfile_metadata.py
  - sectorfile_zip_helper.py, utils_helper.py

- **Directories (3)**:
  - cpp/ (C++ build artifacts)
  - helpers_cpp/ (C++ helper implementations)
  - helpers_py/ (Python helper alternatives)

- **IVAO Integration**:
  - IVAO client and authentication code
  - IVAO NOTAM fetching service (optional in standalones)
  - IVAO-specific configuration variables

### Technical Details
- **Framework**: FastAPI 1.0.0
- **ORM**: SQLAlchemy with declarative base
- **Databases**: SQLite (default) or PostgreSQL/MySQL
- **Python**: 3.8+
- **Architecture Pattern**: Dependency injection with FastAPI Depends
- **Rate Limiting**: In-memory sliding-window (upgradeable to Redis)
- **Authentication**: API key-based with tier validation

### Migration Notes
To upgrade from AIRAC API to Universal Template:
1. See ROUTER_MIGRATION_GUIDE.md for updating existing routers
2. Update `get_api_key()` usage to unpack new tuple return value
3. Review template.py for 8+ endpoint pattern examples
4. Use TIER_CONFIG for customizing rate limits
5. Read DEVELOPER_QUICKSTART.md for quick start

### Version History
- **1.0.0** (2026-03-21): Universal API Template - Major refactor from specialized AIRAC API to generic, extensible template