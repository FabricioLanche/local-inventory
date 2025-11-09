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
        # Parseo seguro del body (API GW o tests)
        body_raw = event.get("body")
        if isinstance(body_raw, str):
            body = json.loads(body_raw or "{}")
        elif isinstance(body_raw, dict):
            body = body_raw
        else:
            body = {}

        # Log con contraseña enmascarada
        body_for_log = _mask_password(body)
        logger.info("Event (masked body): %s", json.dumps({**event, "body": body_for_log})[:2000])

        # Extraer campos esperados
        # NOTA: id SIEMPRE se genera; no se usa body['local_id'] para id
        direccion = body.get("direccion")
        telefono = body.get("telefono")
        hora_apertura = body.get("hora_apertura")
        hora_finalizacion = body.get("hora_finalizacion")
        local_id_opt = body.get("local_id")  # opcional, se guarda como campo aparte

        gerente = body.get("gerente") or {}
        gerente_nombre = (gerente.get("nombre") if isinstance(gerente, dict) else None)
        gerente_correo = (gerente.get("correo") if isinstance(gerente, dict) else None)
        gerente_contrasena = (gerente.get("contrasena") if isinstance(gerente, dict) else None)

        # Validación mínima
        if not direccion:
            return _resp(400, {"message": "El campo 'direccion' es obligatorio."})

        # Normalizaciones
        if telefono is not None:
            telefono = str(telefono).strip()
        if gerente_correo:
            gerente_correo = str(gerente_correo).strip().lower()

        # Verificar tabla
        _ = table.table_status

        # Construir item
        item = {
            "id": str(uuid.uuid4()),          # SIEMPRE generado
            "local_id": str(local_id_opt) if local_id_opt else None,  # opcional
            "direccion": direccion,
            "telefono": telefono,
            "hora_apertura": hora_apertura,
            "hora_finalizacion": hora_finalizacion,
            "gerente": {
                "nombre": gerente_nombre,
                "correo": gerente_correo,
                "contrasena": gerente_contrasena,  # considera hashear/omitir en prod
            },
        }

        # Quitar None para dejar el item limpio
        item = _prune_nones(item)

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

def _mask_password(body: dict):
    try:
        b = json.loads(json.dumps(body))  # deep copy
        if isinstance(b.get("gerente"), dict) and "contrasena" in b["gerente"]:
            b["gerente"]["contrasena"] = "***"
        return b
    except Exception:
        return {"_unloggable_body": True}

def _prune_nones(obj):
    if isinstance(obj, dict):
        return {k: _prune_nones(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_prune_nones(v) for v in obj]
    return obj
