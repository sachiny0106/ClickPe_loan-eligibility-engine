# Loan Eligibility Engine - Project Guide

## Overview
This project is a serverless loan eligibility matching system built with:
- **Backend**: Python 3.9, AWS Lambda, Serverless Framework
- **Database**: Amazon RDS PostgreSQL
- **Automation**: n8n (self-hosted via Docker)
- **Cloud**: AWS (S3, Lambda, API Gateway, SES)

## Project Structure
```
ClickPe/
├── backend/           # Lambda functions and serverless config
├── frontend/          # HTML upload interface
├── infrastructure/    # Docker Compose for n8n
├── database/          # SQL schema
└── n8n/              # Workflow JSON files
```

## Key Commands

### Start n8n
```bash
cd infrastructure
docker-compose up -d
```

### Deploy to AWS
```bash
cd backend
serverless deploy
```

### Run Database Setup
```bash
cd backend
python setup_rds_schema.py
```

### Expose n8n via ngrok (for Lambda webhook)
```bash
ngrok http 5678
```

## Configuration Files
- `backend/config.json` - Database credentials and webhook URL
- `backend/serverless.yml` - AWS infrastructure definition
- `infrastructure/docker-compose.yml` - n8n and PostgreSQL containers

## Architecture Highlights
1. **Presigned URL Pattern** - Scalable CSV uploads via S3
2. **Multi-Stage Matching** - SQL filter → Rule-based → Optional LLM
3. **n8n Workflows** - Web crawling, matching, and email notification
