import os, json, boto3

dynamodb = boto3.resource('dynamodb')
table_locales = dynamodb.Table(os.environ.get('TABLE_LOCALES', 'ChinaWok-Locales'))
table_usuarios = dynamodb.Table(os.environ.get('TABLE_USUARIOS', 'ChinaWok-Usuarios'))

def lambda_handler(event, context):
    try:
        # Path param (este es el ID del local)
        _id = event.get('pathParameters', {}).get('id')
        if not _id:
            return _resp(400, {"message": "Falta path parameter 'id'."})

        # Body seguro (string o dict)
        body_raw = event.get("body")
        if isinstance(body_raw, str):
            try:
                body = json.loads(body_raw or "{}")
            except Exception:
                return _resp(400, {"message": "Body inválido; se esperaba JSON"})
        elif isinstance(body_raw, dict):
            body = body_raw
        else:
            body = {}

        # Normalizaciones
        if "telefono" in body and body["telefono"] is not None:
            body["telefono"] = str(body["telefono"]).strip()

        gerente = body.get("gerente")
        if isinstance(gerente, dict) and "correo" in gerente and gerente["correo"] is not None:
            gerente["correo"] = str(gerente["correo"]).strip().lower()
            
            # Validar que el nuevo gerente existe y tiene rol "Gerente"
            try:
                user_resp = table_usuarios.get_item(Key={"correo": gerente["correo"]})
                user = user_resp.get("Item")
                
                if not user:
                    return _resp(400, {"message": f"El usuario con correo '{gerente['correo']}' no existe."})
                
                if user.get("role") != "Gerente":
                    return _resp(400, {"message": f"El usuario '{gerente['correo']}' no tiene el rol de Gerente."})
                
                # Actualizar con información del usuario existente
                gerente["nombre"] = user.get("nombre")
                gerente["contrasena"] = user.get("contrasena")
                
            except Exception as e:
                return _resp(500, {"message": "Error al validar el gerente", "error": str(e)})

        # Construcción dinámica del UpdateExpression
        set_clauses, expr_vals, expr_names = [], {}, {}

        def set_attr(path_tokens, value):
            name_parts = []
            # alias seguros para cada token del path
            for i, t in enumerate(path_tokens):
                key = f"#n_{'_'.join(path_tokens[:i+1])}" if len(path_tokens) > 1 else f"#n_{t}"
                expr_names[key] = t
                name_parts.append(key)
            name_ref = ".".join(name_parts)
            val_key = f":v_{'_'.join(path_tokens)}"
            expr_vals[val_key] = value
            set_clauses.append(f"{name_ref} = {val_key}")

        # Campos de primer nivel (eliminamos local_id del body)
        for k in ["direccion", "telefono", "hora_apertura", "hora_finalizacion"]:
            if k in body and body[k] is not None:
                set_attr([k], body[k])

        # Campos anidados de gerente
        if isinstance(gerente, dict):
            for gk in ["nombre", "correo", "contrasena"]:
                if gk in gerente and gerente[gk] is not None:
                    set_attr(["gerente", gk], gerente[gk])

        if not set_clauses:
            return _resp(400, {"message": "Nada que actualizar"})

        # Ejecutar update
        resp = table_locales.update_item(
            Key={"id": _id},
            UpdateExpression="SET " + ", ".join(set_clauses),
            ExpressionAttributeValues=expr_vals,
            ExpressionAttributeNames=expr_names,
            ReturnValues="UPDATED_NEW"
        )

        return _resp(200, {"message": "Local actualizado", "updated": resp.get("Attributes")})

    except Exception as e:
        return _resp(500, {"message": "Error interno", "error": str(e)})

def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }
