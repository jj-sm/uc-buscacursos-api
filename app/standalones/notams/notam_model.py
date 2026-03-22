from sqlalchemy import Column, Integer, Text, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class NOTAMs(Base):
    __tablename__ = 'notams'
    id = Column(Integer, primary_key=True)

    location = Column('location', Text)
    notam_lta_number = Column('notam_lta_number', Text)
    klass = Column('class', Text)
    issue_date_utc = Column('issue_date_utc', Text)
    effective_date_utc = Column('effective_date_utc', Text)
    expiration_date_utc = Column('expiration_date_utc', Text)
    notam_condition_subject_title = Column('notam_condition_subject_title', Text)
    raw_text = Column('raw_text', Text)
    uploaded_at = Column('uploaded_at', Text)
    ivao_active = Column('ivao_active', Boolean, nullable=False, default=False, server_default="0")
    data_source = Column('data_source', Text)
