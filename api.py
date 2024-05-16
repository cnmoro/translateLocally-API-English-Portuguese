from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from translator import get_build
import time, re

def replace_common_ptpt_to_ptbr(text):
    replacements = {
        'contactar': 'contatar',
        'contacto': 'contato',
        'contactando': 'contatando',
        'adereceção': 'adereção',
        ' controlo ': ' controle ',
        ' acto ': ' ato ',
        'actividade': 'atividade',
        'adoptar': 'adotar',
        'adopç': 'adoç',
        ' objectivo': ' objetivo',
        'acadé': 'acadê',
        'antón': 'antôn',
        'conceção': 'concepção',
        'receção': 'recepção',
        'deceção': 'decepção',
        'excecional': 'excepcional',
        'infeção': 'infecção',
        'académico': 'acadêmico',
        'bebé': 'bebê',
        'bónus': 'bônus',
        'colónia': 'colônia',
        'cómico': 'cômico',
        'croché': 'crochê',
        'eletrónico': 'eletrônico',
        'fémur': 'fêmur',
        'fenómeno': 'fenômeno',
        'género': 'gênero',
        'incómodo': 'incômodo',
        'nómade': 'nômade',
        'polémico': 'polêmico',
        'prémio': 'prêmio',
        'puré': 'purê',
        'sinónimo': 'sinônimo',
        'ténis': 'tênis',
        'tectónico': 'tectônico',
        'tónico': 'tônico',
        'telemóvel': 'celular',
        'autocarro': 'ônibus',
        'chávena': 'xícara',
        'passadeira': 'faixa de pedestre',
        'hospedeira de bordo': 'aeromoça',
        'rebuçado': 'bala',
        'cartão de cidadão': 'carteira de identidade',
        'carta de condução': 'carteira de motorista',
        'descapotável': 'conversível',
        'uma casa de banho': 'um banheiro',
        'a casa de banho': 'o banheiro',
        'casa de banho': 'banheiro',
        'agrafador': 'grampeador',
        'banda desenhada': 'história em quadrinhos',
        'pargema': 'ponto de ônibus',
        'montra': 'vitrine',
        'fiambre': 'presunto',
        'fato de banho': 'maiô',
        'oxigénio': 'oxigênio',
        'papel higiénico': 'papel higiênico',
        'pasta dos dentes': 'pasta de dente',
        'peúga': 'meia',
        'piscina insuflável': 'piscina inflável',
        'piscina de plástico': 'piscina inflável',
        'hidrogénio': 'hidrogênio',
        'biberão': 'mamadeira',
        'biberões': 'mamadeiras',
        'biberon': 'mamadeira',
        'biberons': 'mamadeiras',
        'pequeno-almoço': 'café da manhã',
        'tasca': 'boteco',
        'lixívia': 'água sanitária',
        ' portagem': ' pedágio',
        'rés do chão': 'térreo',
        ' duas equipas': 'dois times',
        ' estas equipas': 'estes times',
        ' esta equipa': 'este time',
        ' sua equipa': 'seu time',
        ' a equipa ': ' o time ',
        ' uma equipa ': 'um time ',
        ' as equipas ': 'os times ',
        ' a equipa ': ' o time ',
        ' equipa ': ' time ',
        ' equipas ': ' times ',
        ' na equipa': 'no time',
        ' dobragem': ' dublagem',
        ' sanita ': ' privada ',
        ' retrete': ' vaso sanitário',
        'Pai Natal': 'Papai Noel',
        'esferovite': 'isopor',
        'guarda-redes': 'goleiro',
        ' travão': ' freio',
        ' talho': ' açougue',
        ' sida ': ' aids ',
        ' sida.': ' aids.',
        ' berma ': ' acostamento ',
        'camisa de dormir': 'camisola',
        'cancro': 'câncer',
        'dióspiro': 'caqui',
        'boleia': 'carona',
        'fita-cola': 'durex',
        ' penso rápido': ' band-aid',
        'matrecos': 'pebolim',
        'ao ginásio': 'a academia',
        'o ginásio': 'a academia',
        'palhinha': 'canudo',
        'piropo': 'cantada',
        'rotunda': 'rotatória',
        'tosta mista': 'misto quente',
        't-shirt': 'camiseta',
        'arrendar': 'alugar',
        'autoclismo': 'descarga',
        'de ecrã': 'de tela',
        'do ecrã': 'da tela',
        'da ecrã': 'da tela',
        'o ecrã': 'a tela',
        'e ecrã': 'a tela',
        'es ecrã': 'telas',
        'ecrã': 'tela',
        'chumbar': 'reprovar',
        ' desporto ': ' esporte ',
        'amiúdo': 'reforço',
        'miúdo': 'criança',
        'azeiteiro': 'brega',
        'mulher maravilhoso': 'mulher maravilhosa',
        'comer vitamina': 'tomar vitamina',
        'do condado do condado': 'do condado',
    }

    for k, v in replacements.items():
        # Check if "k" exists, ignoring case
        match = re.search(k, text, re.IGNORECASE)
        if match:
            # Replace "k" with "v", preserving the case of the original word
            def replace(match_obj):
                start, end = match_obj.span()
                original_text = text[start:end]
                if original_text.isupper():
                    return v.upper()
                elif original_text.islower():
                    return v.lower()
                else:
                    return v.capitalize()

            text = re.sub(k, replace, text, flags=re.IGNORECASE)

    return text

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
        if request.src == 'en' and request.trg == 'pt':
            translation = replace_common_ptpt_to_ptbr(translation)
        end = time.time()
        print(f"Translation took {end - start} seconds")
        return {"translated_text": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn api:app --host 0.0.0.0 --port 7725 --workers 4
