import azure.functions as func
import pyodbc
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.environ['DB_HOST']};"
            f"DATABASE={os.environ['POSITIONS_DB']};"
            f"UID={os.environ['DB_USER']};"
            f"PWD={os.environ['DB_PASSWORD']};"
            f"TrustServerCertificate=yes"
        )
        
        cursor = conn.cursor()
        
        # Active Assignments (currently on assignment)
        cursor.execute('''
            SELECT 
                Agency,
                Program AS system,
                Facility AS facility,
                Position_Type AS specialty,
                Start_Date AS startDate,
                End_Date AS endDate
            FROM dhc.B4HealthOrder
            WHERE Contract_Status = 'Closed And Awarded'
              AND GETDATE() BETWEEN Start_Date AND End_Date
            ORDER BY Start_Date DESC
        ''')
        
        columns = [column[0] for column in cursor.description]
        onAssignment = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            if row_dict.get('startDate'):
                row_dict['startDate'] = row_dict['startDate'].isoformat()
            if row_dict.get('endDate'):
                row_dict['endDate'] = row_dict['endDate'].isoformat()
            onAssignment.append(row_dict)
        
        # Upcoming Starts (awarded but not started yet)
        cursor.execute('''
            SELECT 
                Agency,
                Program AS system,
                Facility AS facility,
                Position_Type AS specialty,
                Start_Date AS startDate
            FROM dhc.B4HealthOrder
            WHERE Contract_Status = 'Closed And Awarded'
              AND Start_Date > GETDATE()
            ORDER BY Start_Date ASC
        ''')
        
        columns = [column[0] for column in cursor.description]
        upcoming = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            if row_dict.get('startDate'):
                row_dict['startDate'] = row_dict['startDate'].isoformat()
            upcoming.append(row_dict)
        
        conn.close()
        
        print(f"Returning {len(onAssignment)} active, {len(upcoming)} upcoming")
        
        return func.HttpResponse(
            json.dumps({
                'onAssignment': onAssignment,
                'upcoming': upcoming
            }, default=str),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        print(f"Stats error: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )