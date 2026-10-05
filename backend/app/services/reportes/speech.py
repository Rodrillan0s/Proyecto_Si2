import os
import tempfile
import threading
from fastapi import HTTPException
from app.config import Config

_model = None
_lock = threading.Lock()


def transcribe(content):
    """STT independiente del LLM; audio temporal sin retención."""
    if Config.SPEECH_PROVIDER!='whisper':
        raise HTTPException(503,'La transcripción del servidor no está activada. Usa texto o el micrófono del dispositivo.')
    global _model
    with _lock:
        if _model is None:
            try:
                from faster_whisper import WhisperModel
                _model = WhisperModel(Config.WHISPER_MODEL,device='cpu',compute_type='int8',local_files_only=True)
            except (ImportError,RuntimeError,OSError):
                raise HTTPException(503,'El modelo local de transcripción todavía no está instalado.')
        path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.audio',delete=False) as audio:
                path = audio.name
                audio.write(content)
            segments,info = _model.transcribe(path,language='es',vad_filter=True)
            if info.duration>60:
                raise HTTPException(422,'El comando de voz debe durar hasta 60 segundos.')
            text = ' '.join(segment.text.strip() for segment in segments)
            if not text:
                raise HTTPException(422,'La grabación está vacía. Puedes escribir tu solicitud.')
            return {'texto':text[:2000]}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(422,'No se pudo leer esta grabación. Usa audio válido o escribe la solicitud.')
        finally:
            if path:
                os.unlink(path)
