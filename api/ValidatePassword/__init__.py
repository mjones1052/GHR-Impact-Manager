import azure.functions as func
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validates the admin password for disabling privacy mode.
    Password is stored in PRIVACY_PASSWORD environment variable.
    """
    try:
        body = req.get_json()
        submitted_password = body.get('password', '')
        
        # Get password from environment variable (default to '2026' if not set)
        correct_password = os.environ.get('PRIVACY_PASSWORD', '2026')
        
        is_valid = submitted_password == correct_password
        
        return func.HttpResponse(
            json.dumps({'valid': is_valid}),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'valid': False, 'error': str(e)}),
            mimetype="application/json",
            status_code=400
        )