from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import requests
from datetime import datetime

# DB Setup
DATABASE_URL = "sqlite:///./smartdiab.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ScanHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    meal_name = Column(String)
    carbs = Column(Float)
    verdict = Column(String)
    diabete_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.post("/analyze-meal")
async def analyze_meal(diabete_type: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Simulation/Appel API Spoonacular (Clé de Wissal)
    url = f"https://api.spoonacular.com/food/images/analyze?apiKey=b597ac1aa1a541e98f3957b6cc860f28"
    image_data = await file.read()
    response = requests.post(url, files={"file": (file.filename, image_data)})
    data = response.json()
    
    meal_name = data.get("category", {}).get("name", "Plat inconnu")
    carbs = data.get("nutrition", {}).get("carbs", {}).get("value", 0)
    
    # Logique de verdict
    verdict = "Autorisé"
    if (diabete_type == "Type 1" and carbs > 15) or (diabete_type == "Type 2" and carbs > 25):
        verdict = "Attention : Trop de glucides"

    new_entry = ScanHistory(meal_name=meal_name, carbs=carbs, verdict=verdict, diabete_type=diabete_type)
    db.add(new_entry)
    db.commit()
    
    return {"meal": meal_name, "carbs": carbs, "verdict": verdict}
# Ajoute ceci à ton main.py
@app.post("/ask-ai")
async def ask_ai(question: str = Form(...)):
    # Ici, tu peux intégrer une bibliothèque comme 'transformers' 
    # pour charger TinyLlama localement sur ton PC
    
    # Simulation d'une réponse d'IA médicale
    ai_answer = f"Réponse à '{question}': Privilégiez les fibres pour stabiliser votre taux de sucre."
    
    return {"answer": ai_answer}
@app.post("/ask-ai")
async def ask_ai(question: str = Form(...)):
    # Simulation de TinyLlama
    reponse = f"Conseil SmartDiab : Pour votre question '{question}', je suggère de privilégier les aliments à index glycémique bas."
    return {"answer": reponse}