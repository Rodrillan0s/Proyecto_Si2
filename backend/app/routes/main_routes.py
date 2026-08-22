from fastapi import APIRouter, Body

router = APIRouter(tags=["Principal"])

@router.get("/")
def index():
    return {
        "sistema": "Plataforma Base OBRATEC",
        "estado": "En línea",
        "version": "1.0.0"
    }