import azure.functions as func
import pyodbc
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ['DB_HOST']};"
            f"DATABASE={os.environ['CHANGES_DB']};"
            f"UID={os.environ['DB_USER']};"
            f"PWD={os.environ['DB_PASSWORD']}"
        )
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, jobId, type, data, user_name
            FROM ghr_changes
            ORDER BY timestamp ASC
        ''')
        
        changes = []
        for row in cursor.fetchall():
            change = {
                'id': row[0],
                'timestamp': row[1].isoformat() if row[1] else None,
                'jobId': row[2],
                'type': row[3],
                'data': json.loads(row[4]) if row[4] else {},
                'user': row[5]
            }
            changes.append(change)
        
        conn.close()
        return func.HttpResponse(
            json.dumps({'changes': changes}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e), 'changes': []}),
            mimetype="application/json",
            status_code=200
        )