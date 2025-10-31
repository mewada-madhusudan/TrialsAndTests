from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, Date, JSON, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import uuid

SQLALCHEMY_DATABASE_URL = "sqlite:///./cardholder_management.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class RoleDelegations(Base):
    __tablename__ = "role_delegations"
    
    delegation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    delegator_sid = Column(String, nullable=False)
    delegate_sid = Column(String, nullable=False)
    role_id = Column(String, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class DataUploads(Base):
    __tablename__ = "data_uploads"
    
    upload_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quarter_id = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_status = Column(String, default="processing")  # processing/completed/failed
    records_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime, nullable=True)

class CardholderData(Base):
    __tablename__ = "cardholder_data"
    
    record_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String, nullable=False)
    quarter_id = Column(String, nullable=False)
    certifier_id = Column(String, nullable=False)
    
    # Employee and Area Information
    area_owner_sid = Column(String, nullable=True)
    area_owner_name = Column(String, nullable=True)
    area_name = Column(String, nullable=True)
    employee_sid = Column(String, nullable=True)
    employee_name = Column(String, nullable=True)
    team = Column(String, nullable=True)
    access_to_area_allowed = Column(Boolean, nullable=True)
    region = Column(String, nullable=True)
    country_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    access_type = Column(String, nullable=True)
    access_from_date = Column(Date, nullable=True)
    access_to_date = Column(Date, nullable=True)
    public_private_designation = Column(String, nullable=True)
    
    # Cost Center Information
    cost_center_code_department_id = Column(String, nullable=True)
    cost_center_name_department_name = Column(String, nullable=True)
    
    # CSH Levels
    csh_level_5_name = Column(String, nullable=True)
    csh_level_6_name = Column(String, nullable=True)
    csh_level_7_name = Column(String, nullable=True)
    csh_level_8_name = Column(String, nullable=True)
    csh_level_9_name = Column(String, nullable=True)
    csh_level_10_name = Column(String, nullable=True)
    
    # Status Fields
    process_owner_status = Column(String, default="pending_review")  # pending_review/pending_certification/certified/reopened
    area_owner_status = Column(String, default="pending_confirmation")  # pending_confirmation/confirmed/reopened
    certifier_status = Column(String, default="pending_review")  # pending_review/certified/reopened
    
    # Comments
    process_owner_comment = Column(Text, nullable=True)
    area_owner_comment = Column(Text, nullable=True)
    certifier_comment = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # History tracking
    history = Column(JSON, nullable=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)
