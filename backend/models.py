from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    authors = Column(String(1000), nullable=False)
    year = Column(Integer, nullable=False, index=True)
    volume = Column(Integer)
    issue = Column(Integer)
    pages = Column(String(50))
    doi = Column(String(200))
    abstract = Column(Text)
    principle_id = Column(Integer, ForeignKey("principles.id"))
    procedure_id = Column(Integer, ForeignKey("procedures.id"))
    math_model_id = Column(Integer, ForeignKey("math_models.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    principle = relationship("Principle", back_populates="articles")
    procedure = relationship("Procedure", back_populates="articles")
    math_model = relationship("MathModel", back_populates="articles")

class Principle(Base):
    __tablename__ = "principles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text)
    category = Column(String(100))  # e.g., "reinforcement", "punishment", "extinction"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="principle")

class Procedure(Base):
    __tablename__ = "procedures"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text)
    organism = Column(String(100))  # e.g., "pigeon", "rat", "human"
    apparatus = Column(String(200))
    parameters = Column(Text)  # JSON string of experimental parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="procedure")

class MathModel(Base):
    __tablename__ = "math_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    type = Column(String(50))  # "static" or "recursive"
    latex_equation = Column(Text)
    description = Column(Text)
    parameters = Column(Text)  # JSON string of model parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="math_model") 