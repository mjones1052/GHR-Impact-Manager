import azure.functions as func
import pyodbc
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ['DB_HOST']};"
            f"DATABASE={os.environ['POSITIONS_DB']};"
            f"UID={os.environ['DB_USER']};"
            f"PWD={os.environ['DB_PASSWORD']}"
        )
        
        cursor = conn.cursor()
        
        # Active Assignments
        cursor.execute('''
            SELECT 
                Agency,
                Program AS system,
                Facility AS facility,
                Position_Type AS specialty,
                Start_Date AS startDate,
                End_Date AS endDate
            FROM dhc.B4HealthOrder
            WHERE GETDATE() BETWEEN Start_Date AND End_Date
              AND Contract_Status = 'Active'
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
        
        # Upcoming Starts
        cursor.execute('''
            SELECT 
                Program AS system,
                Facility AS facility,
                Position_Type AS specialty,
                Start_Date AS startDate
            FROM B4HealthOrder
            WHERE Start_Date > GETDATE()
              AND Start_Date <= DATEADD(month, 3, GETDATE())
              AND Contract_Status IN ('Active', 'Awarded', 'Pending')
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
        
        return func.HttpResponse(
            json.dumps({
                'onAssignment': onAssignment,
                'upcoming': upcoming
            }, default=str),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )