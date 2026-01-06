import azure.functions as func
import pyodbc
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.environ['DB_HOST']};"
            f"DATABASE={os.environ['CHANGES_DB']};"
            f"UID={os.environ['DB_USER']};"
            f"PWD={os.environ['DB_PASSWORD']}"
        )
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT TOP 100 id, timestamp, changeCount, snapshot_data
            FROM ghr_history_snapshots
            ORDER BY timestamp DESC
        ''')
        
        snapshots = []
        for row in cursor.fetchall():
            snapshot = {
                'id': row[0],
                'timestamp': row[1].isoformat() if row[1] else None,
                'changeCount': row[2],
                'data': json.loads(row[3]) if row[3] else {}
            }
            snapshots.append(snapshot)
        
        conn.close()
        return func.HttpResponse(
            json.dumps(snapshots),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )