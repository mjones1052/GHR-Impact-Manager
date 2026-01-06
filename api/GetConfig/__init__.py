import azure.functions as func
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        config = {
            'defaultMargin': os.environ.get('DEFAULT_MARGIN', '25')
        }
        
        return func.HttpResponse(
            json.dumps(config),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )