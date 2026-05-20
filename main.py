from fastapi import FastAPI, UploadFile, File, Form, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from groq import Groq
import base64
import json

# ==================================================
# 🚀 FASTAPI APP
# ==================================================
app = FastAPI()

# ==================================================
# 🤖 GROQ CONFIG
# ==================================================
client = Groq(
    api_key="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"
)

# ==================================================
# 💾 SQLITE DATABASE
# ==================================================
DATABASE_URL = "sqlite:///./smartdiab.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# ==================================================
# 📜 TABLE HISTORY
# ==================================================
class ScanHistory(Base):

    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)

    meal_name = Column(String)

    carbs = Column(Float)

    verdict = Column(String)

    recommendation = Column(String)

    diabete_type = Column(String)

    timestamp = Column(DateTime, default=datetime.utcnow)

# ==================================================
# 🛠 CREATE TABLES
# ==================================================
Base.metadata.create_all(bind=engine)

# ==================================================
# 🔥 DATABASE SESSION
# ==================================================
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# ==================================================
# 🍽️ ANALYZE MEAL WITH GROQ AI
# ==================================================
@app.post("/analyze-meal")
async def analyze_meal(

        diabete_type: str = Form(...),

        file: UploadFile = File(...),

        db: Session = Depends(get_db)
):

    # =========================
    # READ IMAGE
    # =========================
    image_bytes = await file.read()

    # =========================
    # IMAGE → BASE64
    # =========================
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # =========================
    # AI REQUEST
    # =========================
    response = client.chat.completions.create(

        model="meta-llama/llama-4-scout-17b-16e-instruct",

        messages=[
            {
                "role": "user",

                "content": [

                    {
                        "type": "text",

                        "text": f"""
                        Tu es un assistant médical spécialisé pour diabétiques.

                        Analyse cette image de repas.

                        Réponds STRICTEMENT en JSON.

                        Format attendu :

                        {{
                          "meal": "nom du plat",
                          "carbs": nombre,
                          "verdict": "Autorisé / Modéré / À éviter",
                          "recommendation": "explication courte"
                        }}

                        Type de diabète :
                        {diabete_type}
                        """
                    },

                    {
                        "type": "image_url",

                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    )

    # =========================
    # GET AI RESPONSE
    # =========================
    ai_result = response.choices[0].message.content

    # =========================
    # PARSE JSON RESPONSE
    # =========================
    try:

        result_json = json.loads(ai_result)

        meal_name = result_json["meal"]

        carbs = result_json["carbs"]

        verdict = result_json["verdict"]

        recommendation = result_json["recommendation"]

    except Exception as e:

        meal_name = "Inconnu"

        carbs = 0

        verdict = "Erreur"

        recommendation = ai_result

    # =========================
    # SAVE TO DATABASE
    # =========================
    new_entry = ScanHistory(

        meal_name=meal_name,

        carbs=carbs,

        verdict=verdict,

        recommendation=recommendation,

        diabete_type=diabete_type
    )

    db.add(new_entry)

    db.commit()

    # =========================
    # RETURN RESPONSE
    # =========================
    return {

        "meal": meal_name,

        "carbs": carbs,

        "verdict": verdict,

        "recommendation": recommendation
    }

# ==================================================
# 🤖 AI MEDICAL CHATBOT
# ==================================================
@app.post("/ask-ai")
async def ask_ai(question: str = Form(...)):

    response = client.chat.completions.create(

        model="llama3-8b-8192",

        messages=[
            {
                "role": "user",

                "content": f"""
                Tu es un assistant médical spécialisé pour diabétiques.

                Réponds simplement à cette question :

                {question}
                """
            }
        ]
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer
    }

# ==================================================
# 📜 GET HISTORY
# ==================================================
@app.get("/history")
def get_history(db: Session = Depends(get_db)):

    history = db.query(ScanHistory).all()

    return history

# ==================================================
# ❤️ ROOT
# ==================================================
@app.get("/")
def root():

    return {
        "message": "SmartDiab API fonctionne ✔"
    }