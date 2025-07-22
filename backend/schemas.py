from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Base schemas
class PrincipleBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None

class ProcedureBase(BaseModel):
    name: str
    description: Optional[str] = None
    organism: Optional[str] = None
    apparatus: Optional[str] = None
    parameters: Optional[str] = None

class MathModelBase(BaseModel):
    name: str
    type: Optional[str] = None
    latex_equation: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[str] = None

class ArticleBase(BaseModel):
    title: str
    authors: str
    year: int
    volume: Optional[int] = None
    issue: Optional[int] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    principle_id: Optional[int] = None
    procedure_id: Optional[int] = None
    math_model_id: Optional[int] = None

# Create schemas
class ArticleCreate(ArticleBase):
    pass

class PrincipleCreate(PrincipleBase):
    pass

class ProcedureCreate(ProcedureBase):
    pass

class MathModelCreate(MathModelBase):
    pass

# Response schemas
class PrincipleResponse(PrincipleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProcedureResponse(ProcedureBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MathModelResponse(MathModelBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ArticleResponse(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    principle: Optional[PrincipleResponse] = None
    procedure: Optional[ProcedureResponse] = None
    math_model: Optional[MathModelResponse] = None
    
    class Config:
        from_attributes = True

# Stats schema
class StatsResponse(BaseModel):
    total_articles: int
    total_principles: int
    total_procedures: int
    total_math_models: int
    articles_by_decade: dict
    principles_by_category: dict 