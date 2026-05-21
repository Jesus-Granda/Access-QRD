import os
import uuid

from werkzeug.utils import secure_filename


def guardar_imagen(archivo, subcarpeta):
    if not archivo or not archivo.filename:
        return None

    nombre = f"{uuid.uuid4().hex}_{secure_filename(archivo.filename)}"
    carpeta = os.path.join("static", "uploads", subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    archivo.save(ruta)
    return f"/static/uploads/{subcarpeta}/{nombre}"
