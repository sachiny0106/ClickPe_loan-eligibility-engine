import psycopg2

# AWS RDS Credentials (from config.json and AWS deployment)
DB_HOST = "loan-eligibility-engine-dev-loandatabase-1usfrjymlmtg.cw3ukee204sf.us-east-1.rds.amazonaws.com"
DB_NAME = "loan_db"
DB_USER = "dbadmin"
DB_PASSWORD = "password"
DB_PORT = 5432

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) NOT NULL,
    monthly_income DECIMAL(10, 2),
    credit_score INT,
    employment_status VARCHAR(50),
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    interest_rate DECIMAL(5, 2),
    min_income DECIMAL(10, 2),
    min_credit_score INT,
    max_credit_score INT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matches (
    match_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    product_id INT REFERENCES loan_products(product_id),
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);
"""

def main():
    print(f"Connecting to {DB_HOST}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Connected successfully!")
        
        cur = conn.cursor()
        
        # Check user count
        cur.execute("SELECT COUNT(*) FROM users;")
        count = cur.fetchone()[0]
        print(f"Users in database: {count}")
        
        cur.close()
        conn.close()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
