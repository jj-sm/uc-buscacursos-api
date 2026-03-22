"""
Course-centric SQLAlchemy models.

The API queries the courses database directly via sqlite3 because semester
tables are created dynamically (semester_YYYY_N).  This module provides a
canonical schema definition for those tables so documentation, admin tools,
and migrations have a single source of truth.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Course(Base):
    """
    Canonical course schema used by all semester tables (semester_YYYY_N).

    Note: The actual tables are created dynamically by the upstream scraper /
    updater.  This model mirrors that structure for reference and tooling.
    """

    __tablename__ = "courses_template"

    # Core identifiers
    id = Column(Text, primary_key=True)  # e.g. "IIC2233-1"
    initials = Column(Text, nullable=False)
    section = Column(Integer, nullable=False)
    nrc = Column(Text, nullable=False)

    # Descriptive fields
    name = Column(Text)
    credits = Column(Integer)
    req = Column(Text)    # requisitos
    conn = Column(Text)   # correquisitos
    restr = Column(Text)  # restricciones
    equiv = Column(Text)  # equivalencias
    program = Column(Text)
    school = Column(Text)
    area = Column(Text)
    category = Column(Text)
    teachers = Column(Text)  # JSON string of teachers
    schedule_json = Column(Text)  # JSON string of schedules
    format = Column(Text)
    campus = Column(Text)

    # Flags
    is_english = Column(Integer, default=0)
    is_removable = Column(Integer, default=0)
    is_special = Column(Integer, default=0)

    # Quotas
    total_quota = Column(Integer)
    quota_json = Column(Text)  # JSON string of quotas per category

    # Metadata
    updated_at = Column(DateTime, default=datetime.utcnow)
