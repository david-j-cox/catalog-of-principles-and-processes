#!/usr/bin/env python3
"""
Sample data population script for JEAB Catalog database.
This script creates sample articles, principles, procedures, and math models.
"""

import asyncio
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Article, Principle, Procedure, MathModel
from schemas import ArticleCreate, PrincipleCreate, ProcedureCreate, MathModelCreate
from crud import create_article, create_principle, create_procedure, create_math_model

def create_sample_data():
    """Create sample data for the JEAB database."""
    db = SessionLocal()
    
    try:
        # Create sample principles
        principles = [
            PrincipleCreate(
                name="Positive Reinforcement",
                description="The presentation of a stimulus following a response that increases the probability of that response occurring again.",
                category="reinforcement"
            ),
            PrincipleCreate(
                name="Negative Reinforcement",
                description="The removal of an aversive stimulus following a response that increases the probability of that response occurring again.",
                category="reinforcement"
            ),
            PrincipleCreate(
                name="Extinction",
                description="The discontinuation of reinforcement for a previously reinforced response, resulting in a decrease in response frequency.",
                category="extinction"
            ),
            PrincipleCreate(
                name="Stimulus Control",
                description="The differential responding in the presence of different stimuli due to differential reinforcement.",
                category="stimulus_control"
            ),
            PrincipleCreate(
                name="Matching Law",
                description="The relative rate of responding matches the relative rate of reinforcement.",
                category="matching"
            )
        ]
        
        created_principles = []
        for principle in principles:
            created_principles.append(create_principle(db, principle))
        
        # Create sample procedures
        procedures = [
            ProcedureCreate(
                name="Multiple Schedule",
                description="A schedule in which two or more component schedules are presented in sequence, each associated with a different stimulus.",
                organism="pigeon",
                apparatus="Operant chamber with key peck response",
                parameters='{"components": ["VI 30s", "VI 120s"], "stimuli": ["red", "green"]}'
            ),
            ProcedureCreate(
                name="Concurrent Schedule",
                description="Two or more independent schedules operating simultaneously, each associated with a different response option.",
                organism="rat",
                apparatus="Two-lever operant chamber",
                parameters='{"schedules": ["VI 30s", "VI 60s"], "levers": ["left", "right"]}'
            ),
            ProcedureCreate(
                name="Delay Discounting",
                description="A procedure in which subjects choose between smaller immediate rewards and larger delayed rewards.",
                organism="human",
                apparatus="Computer-based choice task",
                parameters='{"immediate_rewards": [1, 5, 10], "delayed_rewards": [10, 50, 100], "delays": [1, 7, 30, 90]}'
            )
        ]
        
        created_procedures = []
        for procedure in procedures:
            created_procedures.append(create_procedure(db, procedure))
        
        # Create sample math models
        math_models = [
            MathModelCreate(
                name="Herrnstein's Hyperbola",
                type="static",
                latex_equation="R = \\frac{kR_H}{R_H + R_E}",
                description="A hyperbolic function describing response rate as a function of reinforcement rate.",
                parameters='{"k": "asymptotic response rate", "R_H": "reinforcement rate", "R_E": "extraneous reinforcement"}'
            ),
            MathModelCreate(
                name="Generalized Matching Law",
                type="static",
                latex_equation="\\log\\left(\\frac{B_1}{B_2}\\right) = a\\log\\left(\\frac{r_1}{r_2}\\right) + \\log c",
                description="A logarithmic form of the matching law with bias and sensitivity parameters.",
                parameters='{"a": "sensitivity", "c": "bias", "B_1/B_2": "response ratio", "r_1/r_2": "reinforcement ratio"}'
            ),
            MathModelCreate(
                name="Exponential Discounting",
                type="recursive",
                latex_equation="V = A \\cdot e^{-kD}",
                description="A model of temporal discounting where value decreases exponentially with delay.",
                parameters='{"V": "discounted value", "A": "amount", "k": "discount rate", "D": "delay"}'
            ),
            MathModelCreate(
                name="Hyperbolic Discounting",
                type="recursive",
                latex_equation="V = \\frac{A}{1 + kD}",
                description="A hyperbolic model of temporal discounting that better fits empirical data.",
                parameters='{"V": "discounted value", "A": "amount", "k": "discount rate", "D": "delay"}'
            )
        ]
        
        created_math_models = []
        for math_model in math_models:
            created_math_models.append(create_math_model(db, math_model))
        
        # Create sample articles
        articles = [
            ArticleCreate(
                title="On the Law of Effect",
                authors="B.F. Skinner",
                year=1938,
                volume=1,
                issue=1,
                pages="1-15",
                abstract="This paper introduces the law of effect and its implications for understanding operant behavior.",
                principle_id=created_principles[0].id,  # Positive Reinforcement
                procedure_id=created_procedures[0].id,  # Multiple Schedule
                math_model_id=created_math_models[0].id  # Herrnstein's Hyperbola
            ),
            ArticleCreate(
                title="The Matching Law: A Research Review",
                authors="Richard J. Herrnstein",
                year=1970,
                volume=14,
                issue=2,
                pages="159-199",
                abstract="A comprehensive review of the matching law and its applications across different species and procedures.",
                principle_id=created_principles[4].id,  # Matching Law
                procedure_id=created_procedures[1].id,  # Concurrent Schedule
                math_model_id=created_math_models[1].id  # Generalized Matching Law
            ),
            ArticleCreate(
                title="Temporal Discounting in Pigeons",
                authors="Howard Rachlin, Leonard Green",
                year=1972,
                volume=17,
                issue=1,
                pages="1-13",
                abstract="An experimental investigation of temporal discounting using a choice procedure with pigeons.",
                principle_id=created_principles[0].id,  # Positive Reinforcement
                procedure_id=created_procedures[2].id,  # Delay Discounting
                math_model_id=created_math_models[2].id  # Exponential Discounting
            ),
            ArticleCreate(
                title="Hyperbolic Discounting and Self-Control",
                authors="George Ainslie",
                year=1975,
                volume=23,
                issue=2,
                pages="67-145",
                abstract="A theoretical analysis of hyperbolic discounting and its implications for self-control.",
                principle_id=created_principles[0].id,  # Positive Reinforcement
                procedure_id=created_procedures[2].id,  # Delay Discounting
                math_model_id=created_math_models[3].id  # Hyperbolic Discounting
            ),
            ArticleCreate(
                title="Stimulus Control and Discrimination Learning",
                authors="Murray Sidman",
                year=1960,
                volume=3,
                issue=1,
                pages="1-27",
                abstract="An experimental analysis of stimulus control and discrimination learning in pigeons.",
                principle_id=created_principles[3].id,  # Stimulus Control
                procedure_id=created_procedures[0].id,  # Multiple Schedule
                math_model_id=None
            )
        ]
        
        for article in articles:
            create_article(db, article)
        
        print("✅ Sample data created successfully!")
        print(f"📊 Created {len(created_principles)} principles")
        print(f"🔬 Created {len(created_procedures)} procedures")
        print(f"📐 Created {len(created_math_models)} math models")
        print(f"📄 Created {len(articles)} articles")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create sample data
    create_sample_data() 