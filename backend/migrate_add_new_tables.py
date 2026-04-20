import sys
sys.path.append('/home/kauanmassuia/projeto-melhoramais')

from backend.database import engine, IS_SQLITE
from sqlalchemy import text, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class ReportJob(Base):
    __tablename__ = "report_jobs"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, index=True)
    report_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    file_path = Column(String(500))
    parameters = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    created_by = Column(Integer)


class UploadSession(Base):
    __tablename__ = "upload_sessions"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, nullable=False, index=True)
    source_system = Column(String(50), nullable=False)
    filename = Column(String(255))
    processing_log_id = Column(Integer, index=True)
    total_rows = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    status = Column(String(20), default="started")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class AnimalRanking(Base):
    __tablename__ = "animal_rankings"
    __table_args__ = (
        UniqueConstraint("id_farm", "source_system", "characteristic", "animal_id", name="uix_ranking"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, index=True)
    animal_id = Column(Integer, index=True)
    source_system = Column(String(50), nullable=False)
    characteristic = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    rank = Column(Integer)
    percentile = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class BenchmarkGroup(Base):
    __tablename__ = "benchmark_groups"
    __table_args__ = ({"schema": "silver"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    id_farm = Column(Integer, index=True)
    source_system = Column(String(50), nullable=False)
    characteristic = Column(String(50), nullable=False)
    group_name = Column(String(100), nullable=False)
    group_type = Column(String(20), nullable=False)
    average_value = Column(Float)
    animal_count = Column(Integer, default=0)
    farm_count = Column(Integer, default=0)
    std_dev = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReportTemplate(Base):
    __tablename__ = "report_templates"
    __table_args__ = (
        UniqueConstraint("report_type", "name", name="uix_template_type_name"),
        {"schema": "silver"} if not IS_SQLITE else {},
    )

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    template_data = Column(JSON)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserActivity(Base):
    __tablename__ = "user_activity"
    __table_args__ = ({"schema": "audit"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ApiRequest(Base):
    __tablename__ = "api_requests"
    __table_args__ = ({"schema": "audit"} if not IS_SQLITE else {})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    status_code = Column(Integer)
    duration_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def run_migration():
    print("Running database migration for new tables...")
    
    with engine.connect() as conn:
        if not IS_SQLITE:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
            conn.commit()
        
        for table_class in [
            ReportJob, UploadSession, AnimalRanking, BenchmarkGroup,
            ReportTemplate, UserActivity, ApiRequest
        ]:
            table_name = f"{table_class.__table__.schema}.{table_class.__tablename__}" if not IS_SQLITE else table_class.__tablename__
            print(f"Creating table: {table_name}")
            table_class.__table__.create(bind=engine, checkfirst=True)
        
        conn.commit()
    
    print("Migration completed successfully!")
    print("\nNew tables created:")
    print("  - silver.report_jobs")
    print("  - silver.upload_sessions")
    print("  - silver.animal_rankings")
    print("  - silver.benchmark_groups")
    print("  - silver.report_templates")
    print("  - audit.user_activity")
    print("  - audit.api_requests")


if __name__ == "__main__":
    run_migration()
