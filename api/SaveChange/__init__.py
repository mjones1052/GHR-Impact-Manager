import azure.functions as func
import pyodbc
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        change = req.get_json()
        
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ['DB_HOST']};"
            f"DATABASE={os.environ['CHANGES_DB']};"
            f"UID={os.environ['DB_USER']};"
            f"PWD={os.environ['DB_PASSWORD']}"
        )
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ghr_changes (id, timestamp, jobId, type, data, user_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            change['id'],
            change['timestamp'],
            change['jobId'],
            change['type'],
            json.dumps(change['data']),
            change.get('user', 'Unknown')
        ))
        
        conn.commit()
        conn.close()
        
        return func.HttpResponse(
            json.dumps({'success': True}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )