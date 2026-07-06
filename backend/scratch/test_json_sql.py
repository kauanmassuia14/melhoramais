import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, JSON, Text, select, cast, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_json_table'
    id = Column(Integer, primary_key=True)
    # Using JSON instead of Text
    data = Column(JSON)

def main():
    # SQLite in-memory database
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add test data
    session.add(TestModel(data={"PD-EDg": {"dep": 12.5, "acc": 80}}))
    session.add(TestModel(data={"PD-EDg": {"dep": -1.2, "acc": 75}}))
    session.commit()

    # Query using SQLAlchemy path extraction
    # This should translate to json_extract on SQLite
    query = session.query(TestModel).filter(
        TestModel.data['PD-EDg']['dep'].as_float() > 0.0
    )
    results = query.all()
    print(f"Results: {len(results)}")
    for r in results:
        print(f"ID: {r.id}, data: {r.data}")

if __name__ == '__main__':
    main()
