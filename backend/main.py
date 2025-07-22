from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from database import get_db, engine
from models import Base
from schemas import ArticleCreate, ArticleResponse, PrincipleResponse, MathModelResponse
from crud import (
    get_articles, create_article, get_article_by_id,
    get_principles, get_math_models, get_articles_by_principle,
    get_articles_by_year_range
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JEAB Article Database",
    description="Interactive platform for reviewing Journal of the Experimental Analysis of Behavior articles",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "JEAB Article Database API", "version": "1.0.0"}

@app.get("/api/articles", response_model=List[ArticleResponse])
async def read_articles(
    skip: int = 0,
    limit: int = 100,
    principle: Optional[str] = None,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all articles with optional filtering"""
    if principle:
        return get_articles_by_principle(db, principle, skip=skip, limit=limit)
    elif year_start or year_end:
        return get_articles_by_year_range(db, year_start, year_end, skip=skip, limit=limit)
    else:
        return get_articles(db, skip=skip, limit=limit)

@app.get("/api/articles/{article_id}", response_model=ArticleResponse)
async def read_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific article by ID"""
    article = get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.post("/api/articles", response_model=ArticleResponse)
async def create_new_article(article: ArticleCreate, db: Session = Depends(get_db)):
    """Create a new article"""
    return create_article(db, article)

@app.get("/api/principles", response_model=List[PrincipleResponse])
async def read_principles(db: Session = Depends(get_db)):
    """Get all behavioral principles"""
    return get_principles(db)

@app.get("/api/math", response_model=List[MathModelResponse])
async def read_math_models(db: Session = Depends(get_db)):
    """Get all mathematical models"""
    return get_math_models(db)

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    from crud import get_stats as get_db_stats
    return get_db_stats(db)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 