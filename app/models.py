from sqlalchemy import Column, Integer, Text, Double
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AirportComms(Base):
    __tablename__ = 'tbl_airport_communication'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2))
    airport_identifier = Column('airport_identifier', Text(4))
    communication_type = Column('communication_type', Text(3))
    communication_frequency = Column('communication_frequency', Double(7))
    frequency_units = Column('frequency_units', Text(1))
    service_indicator = Column('service_indicator', Text(3))
    callsign = Column('callsign', Text(25))
    latitude = Column('latitude', Double(9))
    longitude = Column('longitude', Double(10))


class AirportMSA(Base):
    __tablename__ = 'tbl_airport_msa'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2))
    airport_identifier = Column('airport_identifier', Text(4))
    msa_center = Column('msa_center', Text(5))
    msa_center_latitude = Column('msa_center_latitude', Double(9))
    msa_center_longitude = Column('msa_center_longitude', Double(10))
    magnetic_true_indicator = Column('magnetic_true_indicator', Text(1))
    multiple_code = Column('multiple_code', Text(1))
    radius_limit = Column('radius_limit', Integer)
    sector_bearing_1 = Column('sector_bearing_1', Integer)
    sector_altitude_1 = Column('sector_altitude_1', Integer)
    sector_bearing_2 = Column('sector_bearing_2', Integer)
    sector_altitude_2 = Column('sector_altitude_2', Integer)
    sector_bearing_3 = Column('sector_bearing_3', Integer)
    sector_altitude_3 = Column('sector_altitude_3', Integer)
    sector_bearing_4 = Column('sector_bearing_4', Integer)
    sector_altitude_4 = Column('sector_altitude_4', Integer)
    sector_bearing_5 = Column('sector_bearing_5', Integer)
    sector_altitude_5 = Column('sector_altitude_5', Integer)


class Airport(Base):
    __tablename__ = 'tbl_airports'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2), nullable=False)
    airport_identifier = Column('airport_identifier', Text(4), nullable=False)
    airport_identifier_3letter = Column('airport_identifier_3letter', Text(3))
    airport_name = Column('airport_name', Text(3))
    airport_ref_latitude = Column('airport_ref_latitude', Double(9))
    airport_ref_longitude = Column('airport_ref_longitude', Double(10))
    ifr_capability = Column('ifr_capability', Text(1))
    longest_runway_surface_code = Column('longest_runway_surface_code', Text(1))
    elevation = Column('elevation', Integer)
    transition_altitude = Column('transition_altitude', Integer)
    transition_level = Column('transition_level', Integer)
    speed_limit = Column('speed_limit', Integer)
    speed_limit_altitude = Column('speed_limit_altitude', Integer)
    iata_ata_designator = Column('iata_ata_designator', Text(3))
    id = Column('id', Text(15))


class ControlledAirspace(Base):
    __tablename__ = 'tbl_controlled_airspace'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2))
    airspace_center = Column('airspace_center', Text(5))
    controlled_airspace_name = Column('controlled_airspace_name', Text(30))
    airspace_type = Column('airspace_type', Text(1))
    airspace_classification = Column('airspace_classification', Text(1))
    multiple_code = Column('multiple_code', Text(1))
    time_code = Column('time_code', Text(1))
    seqno = Column('seqno', Integer)
    flightlevel = Column('flightlevel', Text(1))
    boundary_via = Column('boundary_via', Text(2))
    latitude = Column('latitude', Double(9))
    longitude = Column('longitude', Double(10))
    arc_origin_latitude = Column('arc_origin_latitude', Double(9))
    arc_origin_longitude = Column('arc_origin_longitude', Double(10))
    arc_distance = Column('arc_distance', Double(5))
    arc_bearing = Column('arc_bearing', Double(5))
    unit_indicator_lower_limit = Column('unit_indicator_lower_limit', Text(1))
    lower_limit = Column('lower_limit', Text(5))
    unit_indicator_upper_limit = Column('unit_indicator_upper_limit', Text(1))
    upper_limit = Column('upper_limit', Text(5))


class CruisingAltitude(Base):
    __tablename__ = 'tbl_cruising_tables'
    rowid = Column(Integer, primary_key=True)

    cruise_table_identifier = Column('cruise_table_identifier', Text(2))
    seqno = Column('seqno', Integer)
    course_from = Column('course_from', Double(5))
    course_to = Column('course_to', Double(5))
    mag_true = Column('mag_true', Text(1))
    cruise_level_from1 = Column('cruise_level_from1', Integer)
    vertical_separation1 = Column('vertical_separation1', Integer)
    cruise_level_to1 = Column('cruise_level_to1', Integer)
    cruise_level_from2 = Column('cruise_level_from2', Integer)
    vertical_separation2 = Column('vertical_separation2', Integer)
    cruise_level_to2 = Column('cruise_level_to2', Integer)
    cruise_level_from3 = Column('cruise_level_from3', Integer)
    vertical_separation3 = Column('vertical_separation3', Integer)
    cruise_level_to3 = Column('cruise_level_to3', Integer)
    cruise_level_from4 = Column('cruise_level_from4', Integer)
    vertical_separation4 = Column('vertical_separation4', Integer)
    cruise_level_to4 = Column('cruise_level_to4', Integer)


class EnrouteAirwayRestriction(Base):
    __tablename__ = 'tbl_enroute_airway_restriction'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    route_identifier = Column('route_identifier', Text(5))
    restriction_identifier = Column('restriction_identifier', Integer)
    restriction_type = Column('restriction_type', Text(2))
    start_waypoint_identifier = Column('start_waypoint_identifier', Text(5))
    start_waypoint_latitude = Column('start_waypoint_latitude', Double(9))
    start_waypoint_longitude = Column('start_waypoint_longitude', Double(10))
    end_waypoint_identifier = Column('end_waypoint_identifier', Text(5))
    end_waypoint_latitude = Column('end_waypoint_latitude', Double(9))
    end_waypoint_longitude = Column('end_waypoint_longitude', Double(10))
    start_date = Column('start_date', Text(7))
    end_date = Column('end_date', Text(7))
    units_of_altitude = Column('units_of_altitude', Text(1))
    restriction_altitude1 = Column('restriction_altitude1', Integer)
    block_indicator1 = Column('block_indicator1', Text(1))
    restriction_altitude2 = Column('restriction_altitude2', Integer)
    block_indicator2 = Column('block_indicator2', Text(1))
    restriction_altitude3 = Column('restriction_altitude3', Integer)
    block_indicator3 = Column('block_indicator3', Text(1))
    restriction_altitude4 = Column('restriction_altitude4', Integer)
    block_indicator4 = Column('block_indicator4', Text(1))
    restriction_altitude5 = Column('restriction_altitude5', Integer)
    block_indicator5 = Column('block_indicator5', Text(1))
    restriction_altitude6 = Column('restriction_altitude6', Integer)
    block_indicator6 = Column('block_indicator6', Text(1))
    restriction_altitude7 = Column('restriction_altitude7', Integer)
    block_indicator7 = Column('block_indicator7', Text(1))
    restriction_notes = Column('restriction_notes', Text(69))


class EnrouteAirway(Base):
    __tablename__ = 'tbl_enroute_airways'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    route_identifier = Column('route_identifier', Text(6))
    seqno = Column('seqno', Integer)
    icao_code = Column('icao_code', Text(2))
    waypoint_identifier = Column('waypoint_identifier', Text(5))
    waypoint_latitude = Column('waypoint_latitude', Double(9))
    waypoint_longitude = Column('waypoint_longitude', Double(10))
    waypoint_description_code = Column('waypoint_description_code', Text(4))
    route_type = Column('route_type', Text(1))
    flightlevel = Column('flightlevel', Text(1))
    direction_restriction = Column('direction_restriction', Text(1))
    crusing_table_identifier = Column('crusing_table_identifier', Text(2))
    minimum_altitude1 = Column('minimum_altitude1', Integer)
    minimum_altitude2 = Column('minimum_altitude2', Integer)
    maximum_altitude = Column('maximum_altitude', Integer)
    outbound_course = Column('outbound_course', Double(5))
    inbound_course = Column('inbound_course', Double(5))
    inbound_distance = Column('inbound_distance', Double(5))
    id = Column('id', Text(15))


class EnrouteComms(Base):
    __tablename__ = 'tbl_enroute_communication'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    fir_rdo_ident = Column('fir_rdo_ident', Text(4))
    fir_uir_indicator = Column('fir_uir_indicator', Text(1))
    communication_type = Column('communication_type', Text(3))
    communication_frequency = Column('communication_frequency', Double(5))
    frequency_units = Column('frequency_units', Text(1))
    service_indicator = Column('service_indicator', Text(3))
    remote_name = Column('remote_name', Text(25))
    callsign = Column('callsign', Text(30))
    latitude = Column('latitude', Double(9))
    longitude = Column('longitude', Double(10))


class EnrouteNDBNavaids(Base):
    __tablename__ = 'tbl_enroute_ndbnavaids'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2), nullable=False)
    ndb_identifier = Column('ndb_identifier', Text(4), nullable=False)
    ndb_name = Column('ndb_name', Text(30))
    ndb_frequency = Column('ndb_frequency', Double(5))
    navaid_class = Column('navaid_class', Text(5))
    ndb_latitude = Column('ndb_latitude', Double(9))
    ndb_longitude = Column('ndb_longitude', Double(10))
    range = Column('range', Integer)
    id = Column('id', Text(15))


class EnrouteWaypoint(Base):
    __tablename__ = 'tbl_enroute_waypoints'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2), nullable=False)
    waypoint_identifier = Column('waypoint_identifier', Text(5), nullable=False)
    waypoint_name = Column('waypoint_name', Text(25))
    waypoint_type = Column('waypoint_type', Text(3))
    waypoint_usage = Column('waypoint_usage', Text(2))
    waypoint_latitude = Column('waypoint_latitude', Double(9))
    waypoint_longitude = Column('waypoint_longitude', Double(10))
    id = Column('id', Text(15))


class Regions(Base):
    __tablename__ = 'tbl_fir_uir'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    fir_uir_identifier = Column('fir_uir_identifier', Text(4))
    fir_uir_address = Column('fir_uir_address', Text(4))
    fir_uir_name = Column('fir_uir_name', Text(25))
    fir_uir_indicator = Column('fir_uir_indicator', Text(1))
    seqno = Column('seqno', Integer)
    boundary_via = Column('boundary_via', Text(2))
    adjacent_fir_identifier = Column('adjacent_fir_identifier', Text(4))
    adjacent_uir_identifier = Column('adjacent_uir_identifier', Text(4))
    reporting_units_speed = Column('reporting_units_speed', Integer)
    reporting_units_altitude = Column('reporting_units_altitude', Integer)
    fir_uir_latitude = Column('fir_uir_latitude', Double(9))
    fir_uir_longitude = Column('fir_uir_longitude', Double(10))
    arc_origin_latitude = Column('arc_origin_latitude', Double(9))
    arc_origin_longitude = Column('arc_origin_longitude', Double(10))
    arc_distance = Column('arc_distance', Double(5))
    arc_bearing = Column('arc_bearing', Double(5))
    fir_upper_limit = Column('fir_upper_limit', Text(5))
    uir_lower_limit = Column('uir_lower_limit', Text(5))
    uir_upper_limit = Column('uir_upper_limit', Text(5))
    cruise_table_identifier = Column('cruise_table_identifier', Text(2))


class Gate(Base):
    __tablename__ = 'tbl_gate'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4))
    icao_code = Column('icao_code', Text(2))
    gate_identifier = Column('gate_identifier', Text(5))
    gate_latitude = Column('gate_latitude', Double(9))
    gate_longitude = Column('gate_longitude', Double(10))
    name = Column('name', Text(25))


class GLS(Base):
    __tablename__ = 'tbl_gls'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4))
    icao_code = Column('icao_code', Text(2))
    gls_ref_path_identifier = Column('gls_ref_path_identifier', Text(4))
    gls_category = Column('gls_category', Text(1))
    gls_channel = Column('gls_channel', Integer)
    runway_identifier = Column('runway_identifier', Text(5))
    gls_approach_bearing = Column('gls_approach_bearing', Double(5))
    station_latitude = Column('station_latitude', Double(9))
    station_longitude = Column('station_longitude', Double(10))
    gls_station_ident = Column('gls_station_ident', Text(4))
    gls_approach_slope = Column('gls_approach_slope', Double(4))
    magentic_variation = Column('magentic_variation', Double(6))
    station_elevation = Column('station_elevation', Integer)
    station_type = Column('station_type', Text(3))
    id = Column('id', Text(15))


class GridMora(Base):
    __tablename__ = 'tbl_grid_mora'
    rowid = Column(Integer, primary_key=True)

    starting_latitude = Column('starting_latitude', Integer)
    starting_longitude = Column('starting_longitude', Integer)
    mora01 = Column('mora01', Text(3))
    mora02 = Column('mora02', Text(3))
    mora03 = Column('mora03', Text(3))
    mora04 = Column('mora04', Text(3))
    mora05 = Column('mora05', Text(3))
    mora06 = Column('mora06', Text(3))
    mora07 = Column('mora07', Text(3))
    mora08 = Column('mora08', Text(3))
    mora09 = Column('mora09', Text(3))
    mora10 = Column('mora10', Text(3))
    mora11 = Column('mora11', Text(3))
    mora12 = Column('mora12', Text(3))
    mora13 = Column('mora13', Text(3))
    mora14 = Column('mora14', Text(3))
    mora15 = Column('mora15', Text(3))
    mora16 = Column('mora16', Text(3))
    mora17 = Column('mora17', Text(3))
    mora18 = Column('mora18', Text(3))
    mora19 = Column('mora19', Text(3))
    mora20 = Column('mora20', Text(3))
    mora21 = Column('mora21', Text(3))
    mora22 = Column('mora22', Text(3))
    mora23 = Column('mora23', Text(3))
    mora24 = Column('mora24', Text(3))
    mora25 = Column('mora25', Text(3))
    mora26 = Column('mora26', Text(3))
    mora27 = Column('mora27', Text(3))
    mora28 = Column('mora28', Text(3))
    mora29 = Column('mora29', Text(3))
    mora30 = Column('mora30', Text(3))


class AiracInfo(Base):
    __tablename__ = 'tbl_header'
    rowid = Column(Integer, primary_key=True)

    version = Column('version', Text(5), nullable=False)
    arincversion = Column('arincversion', Text(6), nullable=False)
    record_set = Column('record_set', Text(8), nullable=False)
    current_airac = Column('current_airac', Text(4), nullable=False)
    revision = Column('revision', Text(3), nullable=False)
    effective_fromto = Column('effective_fromto', Text(10), nullable=False)
    previous_airac = Column('previous_airac', Text(4), nullable=False)
    previous_fromto = Column('previous_fromto', Text(10), nullable=False)
    parsed_at = Column('parsed_at', Text(22), nullable=False)


class Holdings(Base):
    __tablename__ = 'tbl_holdings'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    region_code = Column('region_code', Text(4))
    icao_code = Column('icao_code', Text(2))
    waypoint_identifier = Column('waypoint_identifier', Text(5))
    holding_name = Column('holding_name', Text(25))
    waypoint_latitude = Column('waypoint_latitude', Double(9))
    waypoint_longitude = Column('waypoint_longitude', Double(10))
    duplicate_identifier = Column('duplicate_identifier', Integer)
    inbound_holding_course = Column('inbound_holding_course', Double(5))
    turn_direction = Column('turn_direction', Text(1))
    leg_length = Column('leg_length', Double(4))
    leg_time = Column('leg_time', Double(3))
    minimum_altitude = Column('minimum_altitude', Integer)
    maximum_altitude = Column('maximum_altitude', Integer)
    holding_speed = Column('holding_speed', Integer)


class IAPs(Base):
    __tablename__ = 'tbl_iaps'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4))
    procedure_identifier = Column('procedure_identifier', Text(6))
    route_type = Column('route_type', Text(1))
    transition_identifier = Column('transition_identifier', Text(5))
    seqno = Column('seqno', Integer)
    waypoint_icao_code = Column('waypoint_icao_code', Text(2))
    waypoint_identifier = Column('waypoint_identifier', Text(5))
    waypoint_latitude = Column('waypoint_latitude', Double(9))
    waypoint_longitude = Column('waypoint_longitude', Double(10))
    waypoint_description_code = Column('waypoint_description_code', Text(4))
    turn_direction = Column('turn_direction', Text(1))
    rnp = Column('rnp', Double(4))
    path_termination = Column('path_termination', Text(2))
    recommanded_navaid = Column('recommanded_navaid', Text(4))
    recommanded_navaid_latitude = Column('recommanded_navaid_latitude', Double(9))
    recommanded_navaid_longitude = Column('recommanded_navaid_longitude', Double(10))
    arc_radius = Column('arc_radius', Double(7))
    theta = Column('theta', Double(5))
    rho = Column('rho', Double(5))
    magnetic_course = Column('magnetic_course', Double(5))
    route_distance_holding_distance_time = Column('route_distance_holding_distance_time', Double(5))
    distance_time = Column('distance_time', Text(1))
    altitude_description = Column('altitude_description', Text(1))
    altitude1 = Column('altitude1', Integer)
    altitude2 = Column('altitude2', Integer)
    transition_altitude = Column('transition_altitude', Integer)
    speed_limit_description = Column('speed_limit_description', Text(1))
    speed_limit = Column('speed_limit', Integer)
    vertical_angle = Column('vertical_angle', Double(4))
    center_waypoint = Column('center_waypoint', Text(5))
    center_waypoint_latitude = Column('center_waypoint_latitude', Double(9))
    center_waypoint_longitude = Column('center_waypoint_longitude', Double(10))
    aircraft_category = Column('aircraft_category', Text(1))
    id = Column('id', Text(15))
    recommanded_id = Column('recommanded_id', Text(15))
    center_id = Column('center_id', Text(15))


class LocalizerMarker(Base):
    __tablename__ = 'tbl_localizer_marker'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3), nullable=False)
    icao_code = Column('icao_code', Text(2), nullable=False)
    airport_identifier = Column('airport_identifier', Text(4), nullable=False)
    runway_identifier = Column('runway_identifier', Text(5), nullable=False)
    llz_identifier = Column('llz_identifier', Text(4), nullable=False)
    marker_identifier = Column('marker_identifier', Text(5), nullable=False)
    marker_type = Column('marker_type', Text(3), nullable=False)
    marker_latitude = Column('marker_latitude', Double(9), nullable=False)
    marker_longitude = Column('marker_longitude', Double(10), nullable=False)
    id = Column('id', Text(15))


class LocalizerGlideslope(Base):
    __tablename__ = 'tbl_localizers_glideslopes'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2))
    airport_identifier = Column('airport_identifier', Text(4), nullable=False)
    runway_identifier = Column('runway_identifier', Text(3))
    llz_identifier = Column('llz_identifier', Text(4), nullable=False)
    llz_latitude = Column('llz_latitude', Double(9))
    llz_longitude = Column('llz_longitude', Double(10))
    llz_frequency = Column('llz_frequency', Double(6))
    llz_bearing = Column('llz_bearing', Double(6))
    llz_width = Column('llz_width', Double(6))
    ils_mls_gls_category = Column('ils_mls_gls_category', Text(1))
    gs_latitude = Column('gs_latitude', Double(9))
    gs_longitude = Column('gs_longitude', Double(10))
    gs_angle = Column('gs_angle', Double(4))
    gs_elevation = Column('gs_elevation', Integer)
    station_declination = Column('station_declination', Double(5))
    id = Column('id', Text(15))


class PathPoints(Base):
    __tablename__ = 'tbl_pathpoints'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4))
    icao_code = Column('icao_code', Text(2))
    approach_procedure_ident = Column('approach_procedure_ident', Text(6))
    runway_identifier = Column('runway_identifier', Text(5))
    sbas_service_provider_identifier = Column('sbas_service_provider_identifier', Integer)
    reference_path_identifier = Column('reference_path_identifier', Text(2))
    landing_threshold_latitude = Column('landing_threshold_latitude', Double(9))
    landing_threshold_longitude = Column('landing_threshold_longitude', Double(10))
    ltp_ellipsoid_height = Column('ltp_ellipsoid_height', Double(6))
    glidepath_angle = Column('glidepath_angle', Double(4))
    flightpath_alignment_latitude = Column('flightpath_alignment_latitude', Double(9))
    flightpath_alignment_longitude = Column('flightpath_alignment_longitude', Double(10))
    course_width_at_threshold = Column('course_width_at_threshold', Double(5))
    length_offset = Column('length_offset', Integer)
    path_point_tch = Column('path_point_tch', Integer)
    tch_units_indicator = Column('tch_units_indicator', Text(1))
    hal = Column('hal', Integer)
    val = Column('val', Integer)
    fpap_ellipsoid_height = Column('fpap_ellipsoid_height', Double(6))
    fpap_orthometric_height = Column('fpap_orthometric_height', Double(6))
    ltp_orthometric_height = Column('ltp_orthometric_height', Double(6))
    approach_type_identifier = Column('approach_type_identifier', Text(10))
    gnss_channel_number = Column('gnss_channel_number', Integer)


class AirspaceRestrictions(Base):
    __tablename__ = 'tbl_restrictive_airspace'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2))
    restrictive_airspace_designation = Column('restrictive_airspace_designation', Text(10))
    restrictive_airspace_name = Column('restrictive_airspace_name', Text(30))
    restrictive_type = Column('restrictive_type', Text(1))
    multiple_code = Column('multiple_code', Text(1))
    seqno = Column('seqno', Integer)
    boundary_via = Column('boundary_via', Text(2))
    flightlevel = Column('flightlevel', Text(1))
    latitude = Column('latitude', Double(9))
    longitude = Column('longitude', Double(10))
    arc_origin_latitude = Column('arc_origin_latitude', Double(9))
    arc_origin_longitude = Column('arc_origin_longitude', Double(10))
    arc_distance = Column('arc_distance', Double(5))
    arc_bearing = Column('arc_bearing', Double(5))
    unit_indicator_lower_limit = Column('unit_indicator_lower_limit', Text(1))
    lower_limit = Column('lower_limit', Text(5))
    unit_indicator_upper_limit = Column('unit_indicator_upper_limit', Text(1))
    upper_limit = Column('upper_limit', Text(5))


class Runway(Base):
    __tablename__ = 'tbl_runways'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    icao_code = Column('icao_code', Text(2))
    airport_identifier = Column('airport_identifier', Text(4), nullable=False)
    runway_identifier = Column('runway_identifier', Text(3), nullable=False)
    runway_latitude = Column('runway_latitude', Double(9))
    runway_longitude = Column('runway_longitude', Double(10))
    runway_gradient = Column('runway_gradient', Double(5))
    runway_magnetic_bearing = Column('runway_magnetic_bearing', Double(6))
    runway_true_bearing = Column('runway_true_bearing', Double(7))
    landing_threshold_elevation = Column('landing_threshold_elevation', Integer)
    displaced_threshold_distance = Column('displaced_threshold_distance', Integer)
    threshold_crossing_height = Column('threshold_crossing_height', Integer)
    runway_length = Column('runway_length', Integer)
    runway_width = Column('runway_width', Integer)
    llz_identifier = Column('llz_identifier', Text(4))
    llz_mls_gls_category = Column('llz_mls_gls_category', Text(1))
    surface_code = Column('surface_code', Integer)
    id = Column('id', Text(15))


class SIDs(Base):
    __tablename__ = 'tbl_sids'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4))
    procedure_identifier = Column('procedure_identifier', Text(6))
    route_type = Column('route_type', Text(1))
    transition_identifier = Column('transition_identifier', Text(5))
    seqno = Column('seqno', Integer)
    waypoint_icao_code = Column('waypoint_icao_code', Text(2))
    waypoint_identifier = Column('waypoint_identifier', Text(5))
    waypoint_latitude = Column('waypoint_latitude', Double(9))
    waypoint_longitude = Column('waypoint_longitude', Double(10))
    waypoint_description_code = Column('waypoint_description_code', Text(4))
    turn_direction = Column('turn_direction', Text(1))
    rnp = Column('rnp', Double(4))
    path_termination = Column('path_termination', Text(2))
    recommanded_navaid = Column('recommanded_navaid', Text(4))
    recommanded_navaid_latitude = Column('recommanded_navaid_latitude', Double(9))
    recommanded_navaid_longitude = Column('recommanded_navaid_longitude', Double(10))
    arc_radius = Column('arc_radius', Double(7))
    theta = Column('theta', Double(5))
    rho = Column('rho', Double(5))
    magnetic_course = Column('magnetic_course', Double(5))
    route_distance_holding_distance_time = Column('route_distance_holding_distance_time', Double(5))
    distance_time = Column('distance_time', Text(1))
    altitude_description = Column('altitude_description', Text(1))
    altitude1 = Column('altitude1', Integer)
    altitude2 = Column('altitude2', Integer)
    transition_altitude = Column('transition_altitude', Integer)
    speed_limit_description = Column('speed_limit_description', Text(1))
    speed_limit = Column('speed_limit', Integer)
    vertical_angle = Column('vertical_angle', Double(4))
    center_waypoint = Column('center_waypoint', Text(5))
    center_waypoint_latitude = Column('center_waypoint_latitude', Double(9))
    center_waypoint_longitude = Column('center_waypoint_longitude', Double(10))
    aircraft_category = Column('aircraft_category', Text(1))
    id = Column('id', Text(15))
    recommanded_id = Column('recommanded_id', Text(15))
    center_id = Column('center_id', Text(15))


class STARs(Base):
    __tablename__ = 'tbl_stars'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4))
    procedure_identifier = Column('procedure_identifier', Text(6))
    route_type = Column('route_type', Text(1))
    transition_identifier = Column('transition_identifier', Text(5))
    seqno = Column('seqno', Integer)
    waypoint_icao_code = Column('waypoint_icao_code', Text(2))
    waypoint_identifier = Column('waypoint_identifier', Text(5))
    waypoint_latitude = Column('waypoint_latitude', Double(9))
    waypoint_longitude = Column('waypoint_longitude', Double(10))
    waypoint_description_code = Column('waypoint_description_code', Text(4))
    turn_direction = Column('turn_direction', Text(1))
    rnp = Column('rnp', Double(4))
    path_termination = Column('path_termination', Text(2))
    recommanded_navaid = Column('recommanded_navaid', Text(4))
    recommanded_navaid_latitude = Column('recommanded_navaid_latitude', Double(9))
    recommanded_navaid_longitude = Column('recommanded_navaid_longitude', Double(10))
    arc_radius = Column('arc_radius', Double(7))
    theta = Column('theta', Double(5))
    rho = Column('rho', Double(5))
    magnetic_course = Column('magnetic_course', Double(5))
    route_distance_holding_distance_time = Column('route_distance_holding_distance_time', Double(5))
    distance_time = Column('distance_time', Text(1))
    altitude_description = Column('altitude_description', Text(1))
    altitude1 = Column('altitude1', Integer)
    altitude2 = Column('altitude2', Integer)
    transition_altitude = Column('transition_altitude', Integer)
    speed_limit_description = Column('speed_limit_description', Text(1))
    speed_limit = Column('speed_limit', Integer)
    vertical_angle = Column('vertical_angle', Double(4))
    center_waypoint = Column('center_waypoint', Text(5))
    center_waypoint_latitude = Column('center_waypoint_latitude', Double(9))
    center_waypoint_longitude = Column('center_waypoint_longitude', Double(10))
    aircraft_category = Column('aircraft_category', Text(1))
    id = Column('id', Text(15))
    recommanded_id = Column('recommanded_id', Text(15))
    center_id = Column('center_id', Text(15))


class TerminalNDBNavaids(Base):
    __tablename__ = 'tbl_terminal_ndbnavaids'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4), nullable=False)
    icao_code = Column('icao_code', Text(2), nullable=False)
    ndb_identifier = Column('ndb_identifier', Text(4), nullable=False)
    ndb_name = Column('ndb_name', Text(30))
    ndb_frequency = Column('ndb_frequency', Double(5))
    navaid_class = Column('navaid_class', Text(5))
    ndb_latitude = Column('ndb_latitude', Double(9))
    ndb_longitude = Column('ndb_longitude', Double(10))
    range = Column('range', Integer)
    id = Column('id', Text(15))


class TerminalWaypoint(Base):
    __tablename__ = 'tbl_terminal_waypoints'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    region_code = Column('region_code', Text(4), nullable=False)
    icao_code = Column('icao_code', Text(2), nullable=False)
    waypoint_identifier = Column('waypoint_identifier', Text(5), nullable=False)
    waypoint_name = Column('waypoint_name', Text(25))
    waypoint_type = Column('waypoint_type', Text(3))
    waypoint_latitude = Column('waypoint_latitude', Double(9))
    waypoint_longitude = Column('waypoint_longitude', Double(10))
    id = Column('id', Text(15))


class TerminalVHFNavaids(Base):
    __tablename__ = 'tbl_vhfnavaids'
    rowid = Column(Integer, primary_key=True)

    area_code = Column('area_code', Text(3))
    airport_identifier = Column('airport_identifier', Text(4), nullable=False)
    icao_code = Column('icao_code', Text(2), nullable=False)
    vor_identifier = Column('vor_identifier', Text(4), nullable=False)
    vor_name = Column('vor_name', Text(30))
    vor_frequency = Column('vor_frequency', Double(5))
    navaid_class = Column('navaid_class', Text(5))
    vor_latitude = Column('vor_latitude', Double(9))
    vor_longitude = Column('vor_longitude', Double(10))
    dme_ident = Column('dme_ident', Text(4))
    dme_latitude = Column('dme_latitude', Double(9))
    dme_longitude = Column('dme_longitude', Double(10))
    dme_elevation = Column('dme_elevation', Integer)
    ilsdme_bias = Column('ilsdme_bias', Double(3))
    range = Column('range', Integer)
    station_declination = Column('station_declination', Double(5))
    magnetic_variation = Column('magnetic_variation', Double(5))
    id = Column('id', Text(15))
