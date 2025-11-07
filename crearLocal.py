import os
import json
import uuid
import boto3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TABLE = os.environ.get("LOCAL_TABLE", "chinawok_local")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)

def lambda_handler(event, context):
    try:
        logger.info("Event: %s", json.dumps(event)[:2000])

        # Body puede venir como string (API GW) o dict (tests)
        body_raw = event.get("body")
        if isinstance(body_raw, str):
            body = json.loads(body_raw or "{}")
        elif isinstance(body_raw, dict):
            body = body_raw
        else:
            body = {}

        nombre = body.get("nombre")
        direccion = body.get("direccion")
        distrito = body.get("distrito")
        telefono = body.get("telefono")

        if not nombre or not direccion:
            return _resp(400, {"message": "nombre y direccion son obligatorios"})

        # Normaliza a string para evitar sorpresas posteriores
        if telefono is not None:
            telefono = str(telefono)

        # Verifica que la tabla exista (lanza si no)
        _ = table.table_status

        item = {
            "id": str(uuid.uuid4()),
            "nombre": nombre,
            "direccion": direccion,
            "distrito": distrito,
            "telefono": telefono,
        }

        table.put_item(Item=item)
        return _resp(201, item)

    except Exception as e:
        logger.exception("Fallo en local/crear")
        return _resp(500, {"message": "Error interno", "error": str(e)})

def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, ensure_ascii=False) if body != "" else ""
    }
