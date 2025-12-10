# Loan Eligibility Engine

A serverless loan eligibility matching system that ingests user data, discovers loan products, matches users to eligible products, and notifies them via email.

## ✨ Features

- **Interactive Dashboard** - Real-time stats, drag-and-drop upload, live pipeline status
- **Scalable Ingestion** - Presigned URL pattern for unlimited file sizes
- **Multi-Stage Matching** - SQL pre-filter → Rule-based → Optional LLM (Optimization Treasure Hunt)
- **Automated Notifications** - Personalized emails via AWS SES
- **Self-Hosted Automation** - n8n workflows for complete control

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ARCHITECTURE DIAGRAM                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────┐
                                    │   Frontend   │
                                    │  (HTML/JS)   │
                                    └──────┬───────┘
                                           │ 1. Request Upload URL
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                        AWS CLOUD                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                       │
│  │   API Gateway   │───▶│     Lambda      │    │    S3 Bucket    │                       │
│  │  /upload-url    │    │ getUploadUrl    │    │   (CSV Files)   │                       │
│  └─────────────────┘    └─────────────────┘    └────────┬────────┘                       │
│                                                         │ 3. S3 Event Trigger            │
│                                           2. Presigned  │                                │
│                                              URL Upload ▼                                │
│                                                ┌─────────────────┐                       │
│                                                │     Lambda      │                       │
│                                                │   processCsv    │───┐                   │
│                                                └─────────────────┘   │                   │
│                                                         │            │ 4. Webhook        │
│                                                         │            │                   │
│                                                         ▼            │                   │
│                                                ┌─────────────────┐   │                   │
│                                                │   RDS Postgres  │   │                   │
│                                                │  - users        │   │                   │
│                                                │  - loan_products│   │                   │
│                                                │  - matches      │   │                   │
│                                                └─────────────────┘   │                   │
│                                                         ▲            │                   │
│                                                         │            │                   │
│                                                ┌────────┴────────┐   │                   │
│                                                │    AWS SES      │   │                   │
│                                                │  (Email Send)   │   │                   │
│                                                └─────────────────┘   │                   │
└──────────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                       │
                                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              SELF-HOSTED n8n (Docker)                                     │
│                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Workflow A: Loan Product Discovery                         │ │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │ │
│  │  │ Schedule │───▶│  HTTP    │───▶│  Code    │───▶│ Postgres │───▶│  Store   │      │ │
│  │  │ (Daily)  │    │ Request  │    │ Extract  │    │  Insert  │    │ Products │      │ │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘      │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Workflow B: User-Loan Matching                             │ │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │ │
│  │  │ Webhook  │───▶│SQL Filter│───▶│Rule-Based│───▶│  Save    │───▶│ Trigger  │      │ │
│  │  │ Trigger  │    │ (Stage 1)│    │ (Stage 2)│    │ Matches  │    │ Notify   │      │ │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘      │ │
│  │                                        │                                             │ │
│  │                               ┌────────┴────────┐                                    │ │
│  │                               │ LLM (Stage 3)   │ (Optional - for borderline cases) │ │
│  │                               │ Gemini/GPT API  │                                    │ │
│  │                               └─────────────────┘                                    │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Workflow C: User Notification                              │ │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐                       │ │
│  │  │ Webhook  │───▶│  Get     │───▶│ Format   │───▶│ AWS SES  │                       │ │
│  │  │ Trigger  │    │ Matches  │    │  Email   │    │  Send    │                       │ │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘                       │ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose
- AWS CLI configured with credentials
- Serverless Framework (`npm install -g serverless`)

### 1. Start n8n Infrastructure
```bash
cd infrastructure
docker-compose up -d
```
Access n8n at `http://localhost:5678`

### 2. Deploy AWS Backend
```bash
cd backend
npm install
serverless deploy
```

### 3. Configure Database
```bash
# The Lambda automatically connects to RDS
# Tables are created via setup_rds_schema.py
python setup_rds_schema.py
```

### 4. Launch Dashboard
Open `frontend/dashboard.html` in your browser. The dashboard features:
- **Real-time stats** from the `/stats` API endpoint
- **Drag-and-drop** CSV upload
- **Live pipeline status** showing each processing stage
- **Activity log** with timestamped events

### 5. Import n8n Workflows
1. Open n8n (`http://localhost:5678`)
2. Go to **Workflows** → **Import from File**
3. Import all JSON files from `n8n/` folder
4. Configure PostgreSQL credentials in n8n
5. Activate the workflows

## 📁 Project Structure

```
ClickPe/
├── backend/
│   ├── handler.py          # Lambda functions
│   ├── serverless.yml      # AWS infrastructure
│   ├── config.json         # Configuration
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── index.html          # Upload UI
├── infrastructure/
│   └── docker-compose.yml  # n8n + PostgreSQL
├── database/
│   └── schema.sql          # Database schema
├── n8n/
│   ├── workflow_a_discovery.json    # Web crawler
│   ├── workflow_b_matching.json     # Matching logic
│   └── workflow_c_notification.json # Email sender
└── README.md
```

## 🎯 Design Decisions

### 1. Scalable Data Ingestion
We use the **Presigned URL Pattern** instead of direct API Gateway uploads:
- Frontend requests a presigned URL from Lambda
- File uploads directly to S3 (bypassing API Gateway limits)
- S3 event triggers processing Lambda asynchronously
- Supports files of any size with no timeout issues

### 2. Web Crawling Strategy (Workflow A)
- Targets Indian financial aggregators (BankBazaar, PaisaBazaar)
- Uses HTTP Request nodes to fetch HTML
- Code node extracts structured data with fallback to sample data
- Runs on a daily schedule to keep rates updated
- Stores products in PostgreSQL for fast matching

### 3. Optimization Treasure Hunt (Workflow B)

**The Challenge**: Matching 10,000 users against dozens of loan products using LLM for every pair would be:
- **Slow**: 10,000 × 50 = 500,000 API calls
- **Expensive**: ~$50+ per batch at GPT-4 rates
- **Rate Limited**: Would hit API limits

**Our Multi-Stage Solution**:

| Stage | Method | Purpose | Reduction |
|-------|--------|---------|-----------|
| **Stage 1** | SQL Pre-Filter | Time-based + LIMIT | 90%+ users filtered |
| **Stage 2** | Rule-Based Code | Income + Credit Score + Employment | 95%+ pairs eliminated |
| **Stage 3** | LLM (Optional) | Ranking & Personalization | Only for borderline cases |

**Implementation**:
```javascript
// Stage 2: Fast rule-based matching
for (const user of users) {
  for (const product of products) {
    const incomeOk = user.monthly_income >= product.min_income;
    const creditOk = user.credit_score >= product.min_credit_score;
    if (incomeOk && creditOk) {
      matches.push({ user_id, product_id });
    }
  }
}
```

**Result**: 10,000 users matched in < 5 seconds, zero LLM cost for 99% of cases.

### 4. Email Notification (Workflow C)
- Uses AWS SES node in n8n
- Generates personalized HTML emails
- Groups all matches per user into single email
- Professional template with loan details table

## 🔧 Configuration

### AWS Credentials (config.json)
```json
{
    "DB_HOST": "your-rds-endpoint",
    "DB_NAME": "loan_db",
    "DB_USER": "dbadmin",
    "DB_PASSWORD": "your-password",
    "N8N_WEBHOOK_URL": "https://your-ngrok-url/webhook/process-matches"
}
```

### n8n Credentials Setup
1. **PostgreSQL**: 
   - Host: Your RDS endpoint (or `postgres` for local)
   - Database: `loan_db`
   - User: `dbadmin`
   - Password: `password`
   
2. **AWS SES**: 
   - Add AWS Access Key ID
   - Add AWS Secret Access Key
   - Region: `us-east-1`

## 📊 Database Schema

```sql
-- Users table (from CSV upload)
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) NOT NULL,
    monthly_income DECIMAL(10, 2),
    credit_score INT,
    employment_status VARCHAR(50),
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loan products (from web crawler)
CREATE TABLE loan_products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    interest_rate DECIMAL(5, 2),
    min_income DECIMAL(10, 2),
    min_credit_score INT,
    max_credit_score INT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches (from matching workflow)
CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    product_id INT REFERENCES loan_products(product_id),
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);
```

## 🎬 Demo Flow

1. **Upload CSV** → `frontend/index.html`
2. **S3 Trigger** → Lambda parses and stores users in RDS
3. **Webhook** → n8n Workflow B starts matching
4. **Matching** → Multi-stage filtering finds eligible products
5. **Notification** → Workflow C sends personalized emails via SES

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/upload-url?filename=users.csv` | Get presigned S3 URL for upload |
| GET | `/stats` | Get real-time dashboard statistics |

### Stats API Response
```json
{
  "stats": {
    "users": 10000,
    "products": 176,
    "matches": 75640,
    "emails_sent": 102
  },
  "recent_users": [...],
  "recent_matches": [...],
  "product_stats": [...]
}
```

## 🛠️ Technologies Used

- **Backend**: Python 3.9, AWS Lambda
- **Database**: Amazon RDS PostgreSQL
- **Storage**: Amazon S3
- **Email**: Amazon SES
- **Automation**: n8n (self-hosted via Docker)
- **Infrastructure**: Serverless Framework, Docker Compose
- **AI (Optional)**: Google Gemini API for LLM ranking

## 🔒 Security Notes

- RDS is publicly accessible for demo purposes (restrict in production)
- Use environment variables for secrets in production
- Enable VPC for Lambda-RDS communication in production

## 📄 License

MIT License
