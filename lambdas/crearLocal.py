import os
import json
import uuid
import boto3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TABLE_LOCALES = os.environ.get("TABLE_LOCALES", "ChinaWok-Locales")
TABLE_USUARIOS = os.environ.get("TABLE_USUARIOS", "ChinaWok-Usuarios")
dynamodb = boto3.resource("dynamodb")
table_locales = dynamodb.Table(TABLE_LOCALES)
table_usuarios = dynamodb.Table(TABLE_USUARIOS)

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
        direccion = body.get("direccion")
        telefono = body.get("telefono")
        hora_apertura = body.get("hora_apertura")
        hora_finalizacion = body.get("hora_finalizacion")

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

        # Validar que el gerente existe en tabla de usuarios con rol "Gerente"
        if gerente_correo:
            try:
                user_resp = table_usuarios.get_item(Key={"correo": gerente_correo})
                user = user_resp.get("Item")
                
                if not user:
                    return _resp(400, {"message": f"El usuario con correo '{gerente_correo}' no existe."})
                
                if user.get("role") != "Gerente":
                    return _resp(400, {"message": f"El usuario '{gerente_correo}' no tiene el rol de Gerente."})
                
                # Usar información del usuario existente
                gerente_nombre = user.get("nombre")
                gerente_contrasena = user.get("contrasena")
                
            except Exception as e:
                logger.error(f"Error al validar gerente: {str(e)}")
                return _resp(500, {"message": "Error al validar el gerente", "error": str(e)})

        # Verificar tabla
        _ = table_locales.table_status
        logger.info(f"Key schema de tabla locales: {table_locales.key_schema}")

        # Construir item (local_id siempre generado automáticamente con UUID)
        item = {
            "local_id": str(uuid.uuid4()),
            "direccion": direccion,
            "telefono": telefono,
            "hora_apertura": hora_apertura,
            "hora_finalizacion": hora_finalizacion,
            "gerente": {
                "nombre": gerente_nombre,
                "correo": gerente_correo,
                "contrasena": gerente_contrasena,
            },
        }

        # Quitar None para dejar el item limpio
        item = _prune_nones(item)

        logger.info(f"Creando local con local_id: {item.get('local_id')}")
        table_locales.put_item(Item=item)
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
