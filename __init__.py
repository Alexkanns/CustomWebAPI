import logging
import json
import http.client
import numpy as np

from azure.functions import HttpRequest, HttpResponse


def main(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Überprüfe den "api-key" Header
    api_key = req.headers.get('api-key')
    if not api_key:
        logging.error("Missing 'api-key' header.")
        return HttpResponse("Missing 'api-key' header.", status_code=400)

    # Versuche, den JSON-Body zu parsen
    try:
        req_body = req.get_json()
    except ValueError as e:
        logging.error(f"Invalid JSON: {e}")
        return HttpResponse("Bad Request. Invalid JSON.", status_code=400)

    # Überprüfe, ob "values" im JSON-Body vorhanden ist
    values = req_body.get('values')
    if not values:
        logging.error("The 'values' field is required.")
        return HttpResponse("Bad Request. The 'values' field is required.", status_code=400)

    # Überprüfe, ob "text" in jedem Datensatz vorhanden ist
    for value in values:
        data = value.get('data')
        if not data or 'text' not in data:
            logging.error("The 'text' parameter is required in each record.")
            return HttpResponse("Bad Request. The 'text' parameter is required in each record.", status_code=400)

    # Verarbeite die Eingaben und erstelle die Antwort
    response_values = []
    for value in values:
            record_id = value.get('recordId')
            input_text = value['data']['text']
            logging.info(f"Processing recordId: {record_id}, input: {input_text}")

            ### API-Aufruf, um Embedding zu erhalten
            # Hostname und Pfad der API
            host = "xxxyyyzzz"
            path = "/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-05-15"

            # Verbindung herstellen
            conn = http.client.HTTPSConnection(host)

            # POST-Body + Header zusammenstellen
            payload = json.dumps({"input": input_text})
            headers = {
                'Content-Type': 'application/json',
                'api-key': api_key
            }

            # POST-Anfrage senden + Anwort verarbeiten
            conn.request("POST", path, body=payload, headers=headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            
            # JSON-Antwort parsen
            response_json = json.loads(data)
            embedding = response_json['data'][0]['embedding']
            embedding_float32 = np.array(embedding, dtype=np.float32).tolist()

            ### Embedding als JSON zurückgeben
            response_values.append({
                "recordId": record_id,
                "data": {
                    "embedding": embedding_float32
                },
                "errors": [],
                "warnings": []
            })

    response_body = {
        "values": response_values
    }
    
    return HttpResponse(json.dumps(response_body), status_code=200, mimetype="application/json")