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
        
        # Get all open orders
        cursor.execute('''
            SELECT 
                Contract_ID as position_id,
                Req_ID as req_id,
                Program as program,
                Facility as facility,
                Position_Type as specialty,
                Order_Date_Created as date_added,
                Unit as unit,
                Awarded_Rate as bill_rate,
                Start_Time as shift_time,
                Hiring_Manager as hiring_manager,
                Contract_Status as status
            FROM dhc.B4HealthOrder
            WHERE Contract_Status = 'Open'
            ORDER BY Order_Date_Created DESC
        ''')
        
        columns = [column[0] for column in cursor.description]
        positions = {}
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            position_id = str(row_dict['position_id'])
            
            # Convert dates to ISO format
            if row_dict.get('date_added'):
                row_dict['date_added'] = row_dict['date_added'].isoformat()
            
            # Initialize candidates array
            row_dict['candidates'] = []
            row_dict['ghrSubs'] = 0
            row_dict['avSubs'] = 0
            row_dict['ghrDeclines'] = 0
            row_dict['avDeclines'] = 0
            
            positions[position_id] = row_dict
        
        # Get all submissions for these positions
        position_ids = list(positions.keys())
        if position_ids:
            placeholders = ','.join(['?' for _ in position_ids])
            cursor.execute(f'''
                SELECT 
                    Contract_Assignment_ID as position_id,
                    Agency_Name as agency,
                    Professional as name,
                    Submission_Date as submitDate,
                    Agency_Retracted_Date as agencyRetractedDate,
                    Hospital_Decline_Date as hospDeclineDate,
                    Hospital_Decline_Reason as hospDeclineReason,
                    Offer_Date as offerDate,
                    Agency_Decline_Date as agencyDeclineDate,
                    Offer_Decline_Reason as offerDeclineReason,
                    Date_Awarded as awardedDate,
                    RTO as rto,
                    IsActive as isActive
                FROM dhc.B4Health_Contract_Submissions
                WHERE Contract_Assignment_ID IN ({placeholders})
            ''', position_ids)
            
            sub_columns = [column[0] for column in cursor.description]
            
            for row in cursor.fetchall():
                sub = dict(zip(sub_columns, row))
                position_id = str(sub['position_id'])
                
                if position_id not in positions:
                    continue
                
                # Convert dates to ISO format
                for date_field in ['submitDate', 'agencyRetractedDate', 'hospDeclineDate', 
                                   'offerDate', 'agencyDeclineDate', 'awardedDate']:
                    if sub.get(date_field):
                        sub[date_field] = sub[date_field].isoformat()
                
                # Determine if declined
                is_declined = (
                    sub.get('hospDeclineDate') is not None or
                    sub.get('agencyDeclineDate') is not None or
                    sub.get('agencyRetractedDate') is not None
                )
                
                # Determine decline reason
                decline_reason = None
                if sub.get('hospDeclineDate'):
                    decline_reason = sub.get('hospDeclineReason') or 'Hospital Declined'
                elif sub.get('agencyDeclineDate'):
                    decline_reason = sub.get('offerDeclineReason') or 'Agency Declined'
                elif sub.get('agencyRetractedDate'):
                    decline_reason = 'Agency Retracted'
                
                # Check if GHR or Agency Vendor
                agency_name = str(sub.get('agency') or '').lower()
                is_ghr = 'ghr' in agency_name or 'planet' in agency_name
                
                candidate = {
                    'name': sub.get('name') or 'Unknown',
                    'agency': sub.get('agency') or 'Unknown',
                    'submitDate': sub.get('submitDate'),
                    'offerDate': sub.get('offerDate'),
                    'awardedDate': sub.get('awardedDate'),
                    'rto': sub.get('rto'),
                    'isDeclined': is_declined,
                    'declineReason': decline_reason,
                    'hospDeclineDate': sub.get('hospDeclineDate'),
                    'agencyDeclineDate': sub.get('agencyDeclineDate'),
                    'agencyRetractedDate': sub.get('agencyRetractedDate'),
                    'isGHR': is_ghr,
                    'isActive': bool(sub.get('isActive'))
                }
                
                positions[position_id]['candidates'].append(candidate)
                
                # Update counts
                if is_declined:
                    if is_ghr:
                        positions[position_id]['ghrDeclines'] += 1
                    else:
                        positions[position_id]['avDeclines'] += 1
                else:
                    if is_ghr:
                        positions[position_id]['ghrSubs'] += 1
                    else:
                        positions[position_id]['avSubs'] += 1
        
        conn.close()
        
        data = list(positions.values())
        
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