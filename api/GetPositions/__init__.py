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
            f"PWD={os.environ['DB_PASSWORD']}"
        )
        
        cursor = conn.cursor()
        # ⚠️ TODO: Update table name if different
        cursor.execute('''
            SELECT 
                Req_ID as position_id,
                Program as program,
                Facility as facility,
                Position_Type as specialty,
                Order_Date_Created as date_added,
                Unit as unit,
                Awarded_Rate as bill_rate,
                Start_Time as shift_time,
                Hiring_Manager as hiring_manager,
                Contract_Status as status
            FROM B4HealthOrder
            WHERE Contract_Status = 'Open'
            ORDER BY Order_Date_Created DESC
        ''')
        
        columns = [column[0] for column in cursor.description]
        data = []
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            # Convert dates to ISO format
            for key in ['date_added', 'created_date']:
                if key in row_dict and row_dict[key]:
                    row_dict[key] = row_dict[key].isoformat()
            data.append(row_dict)
        
        conn.close()
        return func.HttpResponse(
            json.dumps(data, default=str),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )