from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from translator import get_build
import time

class TranslationRequest(BaseModel):
    text: str
    src: str
    trg: str

app = FastAPI()

# Initialize the model once when the application starts
tl = None

@app.on_event("startup")
async def startup_event():
    global tl
    translator_client = await get_build()
    tl = await translator_client.__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    await tl.__aexit__(None, None, None)


@app.post("/translate")
async def translate(request: TranslationRequest):
    try:
        start = time.time()
        translation = await tl.translate(request.text, src=request.src, trg=request.trg)
        end = time.time()
        print(f"Translation took {end - start} seconds")
        return {"translated_text": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn api:app --host 0.0.0.0 --port 7725 --workers 4
