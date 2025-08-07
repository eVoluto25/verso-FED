# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Literal
from supabase import create_client, Client
import os
import datetime
import logging

# --- Logger ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verso-fed")

# --- Prompt VERSO F.E.D. (da modulo esterno) ---
from prompt_fed import prompt_fed

# --- Configurazione Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_NAME_FED = os.getenv("SUPABASE_TABLE_NAME_FED")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Init App ---
app = FastAPI()

# --- Schema delle risposte F.E.D. ---
class RisposteFED(BaseModel):
    orario_allenamento: str
    orari_pasti: str
    tipo_lavoro: str
    intolleranze: str
    stile_alimentare: str
    integrazione: str
    difficolta_pasti: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def uppercase_fields(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("*")
    @classmethod
    def validate_value(cls, v, info):
        validi = {
            "orario_allenamento": ['A', 'B', 'C', 'D', 'E', 'F'],
            "orari_pasti": ['A', 'B', 'C', 'D'],
            "tipo_lavoro": ['A', 'B', 'C', 'D'],
            "intolleranze": ['A', 'B', 'C', 'D', 'E'],
            "stile_alimentare": ['A', 'B', 'C', 'D'],
            "integrazione": ['A', 'B', 'C', 'D', 'E', 'F'],
            "difficolta_pasti": ['A', 'B', 'C', 'D', 'E'],
        }
        field_name = info.field_name
        if v not in validi[field_name]:
            raise ValueError(f"Valore non valido per {field_name}: {v}")
        return v

@app.get("/")
def root():
    return {"status": "VERSO F.E.D. attivo"}

# --- Endpoint per ricevere e salvare le risposte F.E.D. ---
@app.post("/onboarding_fed")
async def salva_risposte_fed(risposte: RisposteFED):
    try:
        data = risposte.dict()
        data["created_at"] = datetime.datetime.utcnow().isoformat()
        logger.info(f"[F.E.D.] Risposte ricevute: {data}")

        response = supabase.table(SUPABASE_TABLE_NAME_FED).insert(data).execute()
        logger.info(f"[F.E.D.] Risposta Supabase: {response}")

        return JSONResponse(
            status_code=200,
            content={"prompt_fed": prompt_fed.strip()}
        )
    except Exception as e:
        logger.error(f"[F.E.D.] Errore durante il salvataggio: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"errore": "Errore imprevisto", "dettaglio": str(e)}
        )
