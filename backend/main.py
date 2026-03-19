from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from .models import Base
from .processor import GeneticDataProcessor
import os
import io

app = FastAPI(title="Melhora+ Genetic Data Unifier API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup (using SQLite for local dev if no POSTGRES_URL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)

# Create tables if using SQLite
if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)

def get_db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "melhoramais-backend"}

@app.post("/process-genetic-data")
async def process_genetic_data(
    source_system: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint that receives a raw genetic file, applies mapping and returns a clean Excel.
    """
    try:
        content = await file.read()
        processor = GeneticDataProcessor(db)
        
        # 1. Pipeline execution
        df_cleaned = processor.process_file(content, file.filename, source_system)
        
        # 2. Export to Excel
        excel_data = processor.generate_formatted_excel(df_cleaned)
        
        # 3. Stream back the response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=output_tratado_{source_system}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
