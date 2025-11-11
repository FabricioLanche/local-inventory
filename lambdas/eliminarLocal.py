import os, json, boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_LOCALES', 'ChinaWok-Locales'))

def lambda_handler(event, context):
    _id = event['pathParameters']['id']

    try:
        table.delete_item(Key={"id": _id})
        return _resp(204, {"message": "Local eliminado"})
    except Exception as e:
        return _resp(500, {"message": "Error al eliminar el local", "error": str(e)})

def _resp(status, body):
    return {"statusCode": status, "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"}, "body": json.dumps(body, ensure_ascii=False)}
