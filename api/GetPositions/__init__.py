import azure.functions as func
import pyodbc
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Connect to positions database
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ['DB_HOST']};"
            f"DATABASE={os.environ['POSITIONS_DB']};"
            f"UID={os.environ['DB_USER']};"
            f"PWD={os.environ['DB_PASSWORD']}"
        )
        
        cursor = conn.cursor()
        
        # Get open positions with all needed fields
        cursor.execute('''
            SELECT 
                RTRIM(LTRIM(Contract_ID)) AS position_id,
                Req_ID AS req_id,
                Program AS program,
                Facility AS facility,
                Position_Type AS specialty,
                Order_Date_Created AS date_added,
                Unit AS unit,
                Awarded_Rate AS bill_rate,
                Time_Type AS time_type,
                Start_Time AS start_time,
                End_Time AS end_time,
                Hiring_Manager AS hiring_manager,
                Contract_Status AS status
            FROM dhc.B4HealthOrder
            WHERE Contract_Status = 'Open'
            ORDER BY Order_Date_Created DESC
        ''')
        
        columns = [column[0] for column in cursor.description]
        positions = []
        position_ids = []
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            
            # Convert dates to ISO format
            if row_dict.get('date_added'):
                row_dict['date_added'] = row_dict['date_added'].isoformat() if hasattr(row_dict['date_added'], 'isoformat') else str(row_dict['date_added'])
            
            # Convert time fields to strings
            if row_dict.get('start_time'):
                row_dict['start_time'] = str(row_dict['start_time'])
            if row_dict.get('end_time'):
                row_dict['end_time'] = str(row_dict['end_time'])
            
            # Initialize submission counts
            row_dict['ghrSubs'] = 0
            row_dict['avSubs'] = 0
            row_dict['ghrDeclines'] = 0
            row_dict['avDeclines'] = 0
            row_dict['candidates'] = []
            
            positions.append(row_dict)
            if row_dict.get('position_id'):
                position_ids.append(row_dict['position_id'])
        
        # Get submissions for these positions
        if position_ids:
            placeholders = ','.join(['?' for _ in position_ids])
            cursor.execute(f'''
                SELECT 
                    RTRIM(LTRIM(Contract_Assignment_ID)) AS Contract_Assignment_ID,
                    Agency_Name,
                    Professional,
                    Submission_Date,
                    Agency_Retracted_Date,
                    Hospital_Decline_Date,
                    Hospital_Decline_Reason,
                    Offer_Date,
                    Agency_Decline_Date,
                    Offer_Decline_Reason,
                    Date_Awarded,
                    RTO,
                    IsActive
                FROM dhc.B4Health_Contract_Submissions
                WHERE RTRIM(LTRIM(Contract_Assignment_ID)) IN ({placeholders})
            ''', position_ids)
            
            sub_columns = [column[0] for column in cursor.description]
            
            # Create lookup dict for positions
            pos_lookup = {p['position_id']: p for p in positions}
            
            for row in cursor.fetchall():
                sub = dict(zip(sub_columns, row))
                pos_id = sub.get('Contract_Assignment_ID')
                
                if pos_id and pos_id in pos_lookup:
                    position = pos_lookup[pos_id]
                    
                    # Determine if declined
                    is_declined = bool(
                        sub.get('Hospital_Decline_Date') or 
                        sub.get('Agency_Decline_Date') or 
                        sub.get('Agency_Retracted_Date')
                    )
                    
                    # Determine decline reason
                    decline_reason = None
                    if sub.get('Hospital_Decline_Date'):
                        decline_reason = sub.get('Hospital_Decline_Reason') or 'Hospital Declined'
                    elif sub.get('Agency_Decline_Date'):
                        decline_reason = sub.get('Offer_Decline_Reason') or 'Agency Declined'
                    elif sub.get('Agency_Retracted_Date'):
                        decline_reason = 'Agency Retracted'
                    
                    # Determine if GHR
                    agency = str(sub.get('Agency_Name') or '').lower()
                    is_ghr = 'ghr' in agency or 'planet' in agency
                    
                    # Build candidate object
                    candidate = {
                        'name': sub.get('Professional') or 'Unknown',
                        'agency': sub.get('Agency_Name') or 'Unknown',
                        'submitDate': sub.get('Submission_Date').isoformat() if sub.get('Submission_Date') and hasattr(sub.get('Submission_Date'), 'isoformat') else None,
                        'offerDate': sub.get('Offer_Date').isoformat() if sub.get('Offer_Date') and hasattr(sub.get('Offer_Date'), 'isoformat') else None,
                        'awardedDate': sub.get('Date_Awarded').isoformat() if sub.get('Date_Awarded') and hasattr(sub.get('Date_Awarded'), 'isoformat') else None,
                        'rto': sub.get('RTO'),
                        'isDeclined': is_declined,
                        'declineReason': decline_reason,
                        'hospDeclineDate': sub.get('Hospital_Decline_Date').isoformat() if sub.get('Hospital_Decline_Date') and hasattr(sub.get('Hospital_Decline_Date'), 'isoformat') else None,
                        'agencyDeclineDate': sub.get('Agency_Decline_Date').isoformat() if sub.get('Agency_Decline_Date') and hasattr(sub.get('Agency_Decline_Date'), 'isoformat') else None,
                        'agencyRetractedDate': sub.get('Agency_Retracted_Date').isoformat() if sub.get('Agency_Retracted_Date') and hasattr(sub.get('Agency_Retracted_Date'), 'isoformat') else None,
                        'isGHR': is_ghr,
                        'isActive': sub.get('IsActive') or False
                    }
                    
                    position['candidates'].append(candidate)
                    
                    # Update counts
                    if is_declined:
                        if is_ghr:
                            position['ghrDeclines'] += 1
                        else:
                            position['avDeclines'] += 1
                    else:
                        if is_ghr:
                            position['ghrSubs'] += 1
                        else:
                            position['avSubs'] += 1
        
        conn.close()
        
        print(f"Returning {len(positions)} positions")
        
        return func.HttpResponse(
            json.dumps(positions, default=str),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )