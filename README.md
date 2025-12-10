# helping-hands-platform
Backend + Sample Website for Helping Hands (Volunteers + PayPal Donations)

# Helping Hands Platform  
A serverless-friendly backend prototype for managing volunteers, donations, and community engagement — built for local development with Python, Pytest, and Moto.

This project is part of the **Helping Hands** initiative and demonstrates how to build and test AWS-style Lambda functions and DynamoDB logic **entirely locally** without requiring cloud resources.

---

## 🚀 Features

### 🧍 Volunteer Management
- Create volunteers (name, email, city, skills, interests)
- Retrieve individual volunteer records
- List all volunteers
- DynamoDB-backed data store (mocked locally via Moto)

### 💳 Donation / PayPal Integration
- Create PayPal orders (sandbox-friendly design)
- Business logic validation (`normalize_amount`)
- API calls fully mocked in unit tests (no network calls)

### 🧪 Professional Test Suite (Pytest)
- Full local execution — **no AWS account required**
- Moto-powered DynamoDB mocks
- Monkeypatched PayPal API calls
- Parameterized tests for validation logic
- Skip-based integration tests (run only when API URL is set)

### 🧱 Clean Project Structure

resources/
lambdas/
create_volunteer_lambda/
get_volunteer_lambda/
list_volunteers_lambda/
create_paypal_order_lambda/

tests/
unit/
api/

## 🛠 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/fenotesb/helping-hands-platform
cd helping-hands-platform
```
2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

🧪 Running Tests

Run all tests (unit + skipped API tests):
pytest -v

Typical output:

Unit tests

PayPal order creation logic (mocked HTTP)

Volunteer Lambdas (mocked DynamoDB)

Validation & error cases

Business logic helpers

Skipped tests

Real PayPal integration

Real deployed API (only runs if env vars set)

Run only unit tests:
pytest tests/unit -v

🏗 Design Principles
1. Testability

All Lambda handlers use:

def get_table():
    table_name = os.environ.get("VOLUNTEER_TABLE", "HelpingHands_Volunteers")
    return dynamo.Table(table_name)


This avoids AWS lookup at import time and enables local mocking.

2. Local-First Development

No AWS resources are required:

DynamoDB → Moto mock

PayPal API → Monkeypatched urllib.request.urlopen

API-level tests → optional, skipped unless URL provided

3. Layered Test Strategy

Unit tests validate pure logic (normalize_amount)

Lambda tests validate event → response flow

Integration tests hit real HTTP endpoints only when configured

4. Avoiding Secrets in Git

The repo includes .gitignore entries to block:

.venv/

.env

AWS credentials

PayPal secrets

📦 Project Components
📁 resources/lambdas/*

Contains AWS Lambda–style Python functions:

create_volunteer_lambda

get_volunteer_lambda

list_volunteers_lambda

create_paypal_order_lambda

Each lambda:

Accepts API Gateway–like events

Returns JSON w/ statusCode

Uses DynamoDB (mocked)

📁 tests/unit/*

Local-only tests using:

pytest

moto

monkeypatch

Fake API Gateway events

📁 tests/api/*

Optional integration tests.

Skipped automatically unless both env vars are set:

export HELPING_HANDS_API_URL=...
export PAYPAL_CLIENT_ID=...
export PAYPAL_SECRET=...

🧹 Git Hygiene

This project ships with a safe .gitignore:

.venv/
.env
__pycache__/
.pytest_cache/
.aws-sam/
.DS_Store


To remove accidentally committed secrets:

git rm -r --cached .venv .env __pycache__ .pytest_cache
git commit -m "Cleanup: remove env files"
git push

🧭 Roadmap
Short-term

Add FastAPI wrapper for local REST testing

Store volunteer hosting/housing capabilities

Extend donations with recurring payments (PayPal Subscriptions)

Long-term

Deploy Lambdas via AWS SAM or Terraform

Add DynamoDB Streams for change notifications

Build a frontend (React or Next.js)

Add volunteer-matching workflows

💬 Contact

Built by Fenote Berhane
For interview prep, serverless learning, and contributions to Helping Hands.

⭐ If this repo helps you, consider starring it on GitHub!
