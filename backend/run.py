import importlib.util
import os
import sys
from pathlib import Path


# Si el comando se ejecuta con el Python global, reutiliza automáticamente
# el entorno virtual local que contiene las dependencias del backend.
if importlib.util.find_spec("uvicorn") is None:
    venv_python = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        os.execv(str(venv_python), [str(venv_python), *sys.argv])

import uvicorn
from app import create_app

# Instanciamos la aplicación llamando a la fábrica
app = create_app()

if __name__ == "__main__":
    
    uvicorn.run("run:app", host="127.0.0.1", port=5000, reload=True)
