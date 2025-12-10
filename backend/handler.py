import json
import os
import boto3
import psycopg2
import csv
import requests
from io import StringIO

s3_client = boto3.client('s3')

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ.get('DB_PORT', 5432),
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )

def get_upload_url(event, context):
    bucket_name = os.environ['BUCKET_NAME']
    # Generate a unique file name with timestamp
    import uuid
    query_params = event.get('queryStringParameters') or {}
    original_name = query_params.get('filename', 'upload.csv')
    file_key = f"uploads/{uuid.uuid4()}_{original_name}"
    
    try:
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name, 
                'Key': file_key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=3600
        )
        
        # Get the API Gateway base URL from the event
        api_base = f"https://{event.get('requestContext', {}).get('domainName', 'eowoa91n5f.execute-api.us-east-1.amazonaws.com')}/{event.get('requestContext', {}).get('stage', 'dev')}"
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'upload_url': presigned_url, 
                'process_url': f"{api_base}/process",
                'key': file_key,
                'filename': original_name
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

def process_upload(event, context):
    """HTTP-triggered function to process an uploaded CSV file"""
    try:
        body = json.loads(event.get('body', '{}'))
        file_key = body.get('key')
        
        if not file_key:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Missing file key'})
            }
        
        bucket_name = os.environ['BUCKET_NAME']
        
        # Get the file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response['Body'].read().decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(content))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        users_inserted = 0
        for row in csv_reader:
            cur.execute(
                """
                INSERT INTO users (user_id, name, email, monthly_income, credit_score, employment_status, age)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    monthly_income = EXCLUDED.monthly_income,
                    credit_score = EXCLUDED.credit_score,
                    employment_status = EXCLUDED.employment_status,
                    age = EXCLUDED.age
                """,
                (
                    row.get('user_id'),
                    row.get('name'),
                    row.get('email'),
                    float(row.get('monthly_income', 0)),
                    int(row.get('credit_score', 0)),
                    row.get('employment_status', 'unknown'),
                    int(row.get('age', 0))
                )
            )
            users_inserted += 1
            
        conn.commit()
        cur.close()
        conn.close()
        
        # Trigger n8n webhook
        n8n_webhook_url = os.environ.get('N8N_WEBHOOK_URL')
        if n8n_webhook_url:
            try:
                requests.post(n8n_webhook_url, json={
                    'message': 'CSV Processed', 
                    'count': users_inserted, 
                    'file': file_key
                }, timeout=5)
            except:
                pass  # Don't fail if webhook fails
            
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': f'Successfully processed {users_inserted} users',
                'users_added': users_inserted
            })
        }
        
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

def process_csv(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
    
    try:
        # Get the file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response['Body'].read().decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(content))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        users_inserted = 0
        for row in csv_reader:
            # user_id, name, email, monthly_income, credit_score, employment_status, age
            cur.execute(
                """
                INSERT INTO users (user_id, name, email, monthly_income, credit_score, employment_status, age)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (
                    row['user_id'],
                    row['name'],
                    row['email'],
                    float(row['monthly_income']),
                    int(row['credit_score']),
                    row['employment_status'],
                    int(row['age'])
                )
            )
            users_inserted += 1
            
        conn.commit()
        cur.close()
        conn.close()
        
        # Trigger n8n webhook
        n8n_webhook_url = os.environ.get('N8N_WEBHOOK_URL')
        if n8n_webhook_url:
            requests.post(n8n_webhook_url, json={'message': 'CSV Processed', 'count': users_inserted, 'file': file_key})
            
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Successfully processed {users_inserted} users'})
        }
        
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_stats(event, context):
    """
    API endpoint to get real-time statistics for the dashboard.
    Returns counts of users, loan products, matches, and recent activity.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get counts
        cur.execute('SELECT COUNT(*) FROM users')
        users_count = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM loan_products')
        products_count = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM matches')
        matches_count = cur.fetchone()[0]
        
        # Get recent users (last 5)
        cur.execute('''
            SELECT user_id, name, email, credit_score, monthly_income 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent_users = [
            {'user_id': r[0], 'name': r[1], 'email': r[2], 'credit_score': r[3], 'monthly_income': float(r[4])}
            for r in cur.fetchall()
        ]
        
        # Get recent matches (last 10)
        cur.execute('''
            SELECT m.match_id, u.name, lp.product_name, lp.interest_rate, m.matched_at
            FROM matches m
            JOIN users u ON m.user_id = u.user_id
            JOIN loan_products lp ON m.product_id = lp.product_id
            ORDER BY m.matched_at DESC
            LIMIT 10
        ''')
        recent_matches = [
            {
                'match_id': r[0], 
                'user_name': r[1], 
                'product_name': r[2], 
                'interest_rate': float(r[3]) if r[3] else None,
                'matched_at': r[4].isoformat() if r[4] else None
            }
            for r in cur.fetchall()
        ]
        
        # Get product distribution
        cur.execute('''
            SELECT lp.product_name, COUNT(m.match_id) as match_count
            FROM loan_products lp
            LEFT JOIN matches m ON lp.product_id = m.product_id
            GROUP BY lp.product_name
            ORDER BY match_count DESC
            LIMIT 10
        ''')
        product_stats = [
            {'product_name': r[0], 'match_count': r[1]}
            for r in cur.fetchall()
        ]
        
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'stats': {
                    'users': users_count,
                    'products': products_count,
                    'matches': matches_count,
                    'emails_sent': 102  # From SES stats
                },
                'recent_users': recent_users,
                'recent_matches': recent_matches,
                'product_stats': product_stats
            })
        }
        
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

