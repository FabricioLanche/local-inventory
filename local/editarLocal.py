import os, json, boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['LOCAL_TABLE'])

def lambda_handler(event, context):
    _id = event['pathParameters']['id']
    body_raw = event.get("body")
    body = body_raw if isinstance(body_raw, dict) else json.loads(body_raw or "{}")

    update_expr = []
    expr_vals = {}
    for k in ["nombre", "direccion", "distrito", "telefono"]:
        if k in body and body[k] is not None:
            update_expr.append(f"{k} = :{k}")
            expr_vals[f":{k}"] = body[k]

    if not update_expr:
        return _resp(400, {"message": "Nada que actualizar"})

    table.update_item(
        Key={"id": _id},
        UpdateExpression="SET " + ", ".join(update_expr),
        ExpressionAttributeValues=expr_vals
    )
    return _resp(200, {"message": "Local actualizado"})

def _resp(status, body):
    return {"statusCode": status, "headers": {"Content-Type":"application/json","Access-Control-Allow-Origin":"*"}, "body": json.dumps(body, ensure_ascii=False)}
