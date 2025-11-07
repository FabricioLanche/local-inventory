import os, json, boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['LOCAL_TABLE'])

def lambda_handler(event, context):
    _id = event['pathParameters']['id']

    try:
        resp = table.get_item(Key={"id": _id})
        item = resp.get("Item")
        if not item:
            return _resp(404, {"message": "Local no encontrado"})
        return _resp(200, item)
    except Exception as e:
        return _resp(500, {"message": "Error al obtener el local", "error": str(e)})

def _resp(status, body):
    return {"statusCode": status, "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"}, "body": json.dumps(body, ensure_ascii=False)}
