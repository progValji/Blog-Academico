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

def eliminar_archivos_post_idrive(post_id):
    """
    Elimina TODOS los archivos de un post en IDrive e2, usando el prefijo {post_id}/

    Retorna (eliminados, error):
      eliminados: cantidad de archivos borrados
      error: string con el mensaje de error, o None si todo salió bien
    """
    s3 = get_s3_client()
    bucket = current_app.config['IDRIVE_BUCKET']
    prefix = f"{post_id}/"

    try:
        # 1. Listar todos los objetos bajo ese prefijo
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objetos = response.get('Contents', [])

        if not objetos:
            return 0, None

        # 2. Armar la lista de keys a eliminar (delete_objects acepta hasta 1000 por llamada)
        keys_a_borrar = [{'Key': obj['Key']} for obj in objetos]

        s3.delete_objects(
            Bucket=bucket,
            Delete={'Objects': keys_a_borrar}
        )

        return len(keys_a_borrar), None

    except Exception as e:
        current_app.logger.error(
            f"Error al eliminar archivos del post {post_id} en IDrive e2: {e}",
            exc_info=True
        )
        return 0, str(e)