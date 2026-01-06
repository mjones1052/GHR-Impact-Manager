import azure.functions as func
import pyodbc
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        snapshot = req.get_json()
        
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ['DB_HOST']};"
            f"DATABASE={os.environ['CHANGES_DB']};"
            f"UID={os.environ['DB_USER']};"
            f"PWD={os.environ['DB_PASSWORD']}"
        )
        
        cursor = conn.cursor()
        
        # Insert new snapshot
        cursor.execute('''
            INSERT INTO ghr_history_snapshots (timestamp, changeCount, snapshot_data)
            VALUES (?, ?, ?)
        ''', (
            snapshot['timestamp'],
            snapshot['changeCount'],
            json.dumps(snapshot['data'])
        ))
        
        # Keep only last 100 snapshots
        cursor.execute('''
            DELETE FROM ghr_history_snapshots
            WHERE id NOT IN (
                SELECT TOP 100 id
                FROM ghr_history_snapshots
                ORDER BY timestamp DESC
            )
        ''')
        
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