import os, json, boto3, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_LOCALES', 'ChinaWok-Locales'))

def lambda_handler(event, context):
    try:
        local_id = event.get('pathParameters', {}).get('local_id')
        
        if not local_id:
            return _resp(400, {"message": "Falta el parámetro 'local_id' en el path"})
        
        logger.info(f"Eliminando local con local_id: {local_id}")
        logger.info(f"Key schema: {table.key_schema}")
        
        table.delete_item(Key={"local_id": local_id})
        return _resp(204, {"message": "Local eliminado"})
        
    except Exception as e:
        logger.exception(f"Error al eliminar local: {str(e)}")
        return _resp(500, {"message": "Error al eliminar el local", "error": str(e)})

def _resp(status, body):
    return {"statusCode": status, "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"}, "body": json.dumps(body, ensure_ascii=False)}
