import os, json, uuid, boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['LOCAL_TABLE'])

def lambda_handler(event, context):
    body_raw = event.get("body")
    body = body_raw if isinstance(body_raw, dict) else json.loads(body_raw or "{}")

    nombre = body.get("nombre")
    direccion = body.get("direccion")
    distrito = body.get("distrito")
    telefono = body.get("telefono")

    if not nombre or not direccion:
        return _resp(400, {"message": "nombre y direccion son obligatorios"})

    item = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "direccion": direccion,
        "distrito": distrito,
        "telefono": telefono,
    }
    table.put_item(Item=item)
    return _resp(201, item)

def _resp(status, body):
    return {"statusCode": status, "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"}, "body": json.dumps(body, ensure_ascii=False)}
