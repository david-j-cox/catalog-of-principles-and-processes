from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from models import Article, Principle, Procedure, MathModel
from schemas import ArticleCreate, PrincipleCreate, ProcedureCreate, MathModelCreate

# Article CRUD operations
def get_articles(db: Session, skip: int = 0, limit: int = 100) -> List[Article]:
    return db.query(Article).offset(skip).limit(limit).all()

def get_article_by_id(db: Session, article_id: int) -> Optional[Article]:
    return db.query(Article).filter(Article.id == article_id).first()

def create_article(db: Session, article: ArticleCreate) -> Article:
    db_article = Article(**article.dict())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def get_articles_by_principle(db: Session, principle: str, skip: int = 0, limit: int = 100) -> List[Article]:
    return db.query(Article).join(Principle).filter(Principle.name.ilike(f"%{principle}%")).offset(skip).limit(limit).all()

def get_articles_by_year_range(db: Session, year_start: Optional[int] = None, year_end: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Article]:
    query = db.query(Article)
    
    if year_start and year_end:
        query = query.filter(and_(Article.year >= year_start, Article.year <= year_end))
    elif year_start:
        query = query.filter(Article.year >= year_start)
    elif year_end:
        query = query.filter(Article.year <= year_end)
    
    return query.offset(skip).limit(limit).all()

def search_articles(db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[Article]:
    return db.query(Article).filter(
        Article.title.ilike(f"%{search_term}%") |
        Article.authors.ilike(f"%{search_term}%") |
        Article.abstract.ilike(f"%{search_term}%")
    ).offset(skip).limit(limit).all()

# Principle CRUD operations
def get_principles(db: Session, skip: int = 0, limit: int = 100) -> List[Principle]:
    return db.query(Principle).offset(skip).limit(limit).all()

def get_principle_by_id(db: Session, principle_id: int) -> Optional[Principle]:
    return db.query(Principle).filter(Principle.id == principle_id).first()

def create_principle(db: Session, principle: PrincipleCreate) -> Principle:
    db_principle = Principle(**principle.dict())
    db.add(db_principle)
    db.commit()
    db.refresh(db_principle)
    return db_principle

def get_principles_by_category(db: Session, category: str) -> List[Principle]:
    return db.query(Principle).filter(Principle.category == category).all()

# Procedure CRUD operations
def get_procedures(db: Session, skip: int = 0, limit: int = 100) -> List[Procedure]:
    return db.query(Procedure).offset(skip).limit(limit).all()

def get_procedure_by_id(db: Session, procedure_id: int) -> Optional[Procedure]:
    return db.query(Procedure).filter(Procedure.id == procedure_id).first()

def create_procedure(db: Session, procedure: ProcedureCreate) -> Procedure:
    db_procedure = Procedure(**procedure.dict())
    db.add(db_procedure)
    db.commit()
    db.refresh(db_procedure)
    return db_procedure

def get_procedures_by_organism(db: Session, organism: str) -> List[Procedure]:
    return db.query(Procedure).filter(Procedure.organism == organism).all()

# MathModel CRUD operations
def get_math_models(db: Session, skip: int = 0, limit: int = 100) -> List[MathModel]:
    return db.query(MathModel).offset(skip).limit(limit).all()

def get_math_model_by_id(db: Session, math_model_id: int) -> Optional[MathModel]:
    return db.query(MathModel).filter(MathModel.id == math_model_id).first()

def create_math_model(db: Session, math_model: MathModelCreate) -> MathModel:
    db_math_model = MathModel(**math_model.dict())
    db.add(db_math_model)
    db.commit()
    db.refresh(db_math_model)
    return db_math_model

def get_math_models_by_type(db: Session, model_type: str) -> List[MathModel]:
    return db.query(MathModel).filter(MathModel.type == model_type).all()

# Statistics
def get_stats(db: Session) -> Dict[str, Any]:
    # Get basic counts
    total_articles = db.query(Article).count()
    total_principles = db.query(Principle).count()
    total_procedures = db.query(Procedure).count()
    total_math_models = db.query(MathModel).count()
    
    # Articles by decade
    articles_by_decade = db.query(
        func.floor(Article.year / 10) * 10,
        func.count(Article.id)
    ).group_by(func.floor(Article.year / 10)).all()
    
    articles_by_decade_dict = {f"{decade}s": count for decade, count in articles_by_decade}
    
    # Principles by category
    principles_by_category = db.query(
        Principle.category,
        func.count(Principle.id)
    ).group_by(Principle.category).all()
    
    principles_by_category_dict = {category: count for category, count in principles_by_category if category}
    
    return {
        "total_articles": total_articles,
        "total_principles": total_principles,
        "total_procedures": total_procedures,
        "total_math_models": total_math_models,
        "articles_by_decade": articles_by_decade_dict,
        "principles_by_category": principles_by_category_dict
    } 