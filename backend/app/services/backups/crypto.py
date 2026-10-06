"""Formato OBRATEC1: cabecera autenticada, AES-256-GCM en streaming y tag final."""
import hashlib
import json
import os
import struct
from pathlib import Path
from .settings import BackupError

MAGIC = b'OBRATEC1\n'
CHUNK = 1024*1024


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b''):
            digest.update(chunk)
    return digest.hexdigest()


def encrypt(source, destination, key_id, key, identifier, max_bytes):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    if len(key) != 32:
        raise BackupError('La clave AES debe tener 32 bytes.')
    nonce = os.urandom(12)
    metadata = {'version': 1, 'key_id': key_id, 'nonce': nonce.hex(), 'id': str(identifier)}
    encoded = json.dumps(metadata, sort_keys=True, separators=(',', ':')).encode()
    header = MAGIC+struct.pack('>I', len(encoded))+encoded
    engine = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    engine.authenticate_additional_data(header)
    total = len(header)+16
    try:
        with open(source, 'rb') as src, open(destination, 'xb') as dst:
            os.chmod(destination, 0o600)
            dst.write(header)
            for chunk in iter(lambda: src.read(CHUNK), b''):
                total += len(chunk)
                if total > max_bytes:
                    raise BackupError('El respaldo supera el tamaño máximo configurado.')
                dst.write(engine.update(chunk))
            dst.write(engine.finalize())
            dst.write(engine.tag)
            dst.flush()
            os.fsync(dst.fileno())
    except Exception:
        Path(destination).unlink(missing_ok=True)
        raise
    return metadata


def decrypt(source, destination, keys, max_bytes):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    try:
        size = Path(source).stat().st_size
        if size > max_bytes or size < len(MAGIC)+4+16:
            raise ValueError()
        with open(source, 'rb') as src:
            if src.read(len(MAGIC)) != MAGIC:
                raise ValueError()
            raw_length = src.read(4)
            length = struct.unpack('>I', raw_length)[0]
            if not 1 <= length <= 16384:
                raise ValueError()
            encoded = src.read(length)
            header = MAGIC+raw_length+encoded
            metadata = json.loads(encoded)
            key = keys.get(metadata['key_id'])
            if key is None:
                raise BackupError('No está disponible la clave de este respaldo. Recupera su key_id desde el depósito seguro.', 'BACKUP_KEY_MISSING')
            if metadata['version'] != 1 or len(bytes.fromhex(metadata['nonce'])) != 12:
                raise ValueError()
            remaining = size-len(header)-16
            if remaining < 0:
                raise ValueError()
            src.seek(-16, 2)
            tag = src.read(16)
            src.seek(len(header))
            engine = Cipher(algorithms.AES(key), modes.GCM(bytes.fromhex(metadata['nonce']), tag)).decryptor()
            engine.authenticate_additional_data(header)
            with open(destination, 'xb') as dst:
                os.chmod(destination, 0o600)
                while remaining:
                    chunk = src.read(min(CHUNK, remaining))
                    if not chunk:
                        raise ValueError()
                    remaining -= len(chunk)
                    dst.write(engine.update(chunk))
                # El archivo solo se retorna tras autenticar TODO el ciphertext.
                dst.write(engine.finalize())
                dst.flush()
                os.fsync(dst.fileno())
        return metadata
    except BackupError:
        Path(destination).unlink(missing_ok=True)
        raise
    except (ValueError, KeyError, TypeError, struct.error, InvalidTag, json.JSONDecodeError) as exc:
        Path(destination).unlink(missing_ok=True)
        raise BackupError('El paquete está dañado, fue alterado o no es un respaldo OBRATEC autenticado.', 'BACKUP_INVALID_PACKAGE') from exc
