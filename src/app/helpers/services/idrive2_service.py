import uuid
import boto3
from botocore.config import Config
from flask import current_app
from ..storage import allowed_file


def get_s3_client():
    """Crea un cliente S3 apuntando a IDrive e2."""
    return boto3.client(
        "s3",
        endpoint_url=current_app.config['IDRIVE_ENDPOINT'],
        aws_access_key_id=current_app.config['IDRIVE_ACCESS_KEY'],
        aws_secret_access_key=current_app.config['IDRIVE_SECRET_KEY'],
        config=Config(signature_version="s3v4"),
    )

def upload_files_to_idrive(files, post_id):
    """
    Sube uno o varios archivos a IDrive e2 (no toca la BD).
    files: lista de FileStorage -> request.files.getlist('archivos')
    post_id: id del post al que pertenecen

    Retorna (subidos, errores):
      subidos: lista de dicts listos para insertar en post_media
      errores: lista de strings con los archivos que fallaron
    """
    s3 = get_s3_client()
    bucket = current_app.config['IDRIVE_BUCKET']

    subidos = []
    errores = []

    for file in files:
        if not file or file.filename == '':
            continue

        if not allowed_file(file.filename):
            errores.append(f"{file.filename}: solo se permiten archivos PDF o TXT")
            continue

        ext = file.filename.rsplit('.', 1)[1].lower()
        nombre_unico = f"{uuid.uuid4().hex}.{ext}"
        key = f"{post_id}/{nombre_unico}"

        content_type = 'application/pdf' if ext == 'pdf' else 'text/plain'

        try:
            s3.upload_fileobj(
                file,
                bucket,
                key,
                ExtraArgs={'ContentType': content_type}
            )
        except Exception as e:
            errores.append(f"{file.filename}: error al subir a IDrive e2 - {str(e)}")
            continue

        file_url = f"{current_app.config['IDRIVE_ENDPOINT']}/{bucket}/{key}"

        subidos.append({
            'post_id': post_id,
            'file_url': file_url,
            'file_type': ext,
            'nombre_original': file.filename
        })

    return subidos, errores