"""
Generic SQLAlchemy models for template use.
These are base models that can be extended for your specific API use case.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GenericResource(Base):
    """
    Generic resource model template.
    Extend this for your specific data types.
    """
    __tablename__ = 'generic_resources'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    resource_type = Column(String, nullable=False, index=True)
    external_id = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class GenericLocation(Base):
    """
    Generic location model with coordinates.
    Suitable for airports, points of interest, etc.
    """
    __tablename__ = 'generic_locations'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Integer, nullable=True)
    country = Column(String(3), nullable=True)
    region = Column(String(3), nullable=True)
    description = Column(Text, nullable=True)


class GenericEvent(Base):
    """
    Generic event/notification model.
    Track system events, notifications, or occurrences.
    """
    __tablename__ = 'generic_events'
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    event_date = Column(Date, nullable=False)
    severity = Column(String, default="info")  # info, warning, critical
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    affected_codes = Column(String, nullable=True)  # comma-separated
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)


# Example extension patterns:
# 
# class Airport(GenericLocation):
#     __tablename__ = 'airports'
#     id = Column(Integer, ForeignKey('generic_locations.id'), primary_key=True)
#     ifr_capable = Column(Boolean, default=False)
#     runway_count = Column(Integer)
#     __mapper_args__ = {'polymorphic_identity': 'airport'}
#
# class Navaid(GenericLocation):
#     __tablename__ = 'navaids'
#     id = Column(Integer, ForeignKey('generic_locations.id'), primary_key=True)
#     frequency = Column(Float)
#     navaid_type = Column(String)  # NDB, VOR, DVOR, DME
#     __mapper_args__ = {'polymorphic_identity': 'navaid'}
