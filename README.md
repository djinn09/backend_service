_# Mini SIP Tracker API_

_A FastAPI backend application to help users set up and track their monthly mutual fund Systematic Investment Plans (SIPs)._

_## Tech Stack_

- _**Backend**_: FastAPI (Python)_
- _**Authentication**_: Supabase JWT
- _**Database**_: PostgreSQL (managed by Supabase, accessed via SQLAlchemy for application data)
- _**ORM**_: SQLAlchemy
- _**Background Tasks**_: APScheduler (for simulated SIP executions)_
- _**Testing**_: Pytest

_## Features_

- _User authentication using Supabase JWTs._
- _Creation of SIP plans (`POST /sips/`)._
- _Retrieval of SIP summaries grouped by scheme (`GET /sips/summary`), including total invested and months invested._
- _Automated (simulated) monthly SIP execution logging._
- _Unit tests for API endpoints and authentication logic._

_## Project Structure_

```
app/
├── __init__.py
├── auth.py         # Authentication logic, Supabase JWT handling
├── crud.py         # Database Create, Read, Update, Delete operations
├── database.py     # Database connection and session management (SQLAlchemy)
├── main.py         # FastAPI application instance, startup/shutdown events, scheduler
├── models.py       # SQLAlchemy database models
├── schemas.py      # Pydantic schemas for request/response validation
├── routers/        # API route definitions
│   ├── __init__.py
│   └── sips.py     # SIP related endpoints
└── tests/          # Unit and integration tests
    ├── __init__.py
    ├── conftest.py   # Pytest fixtures and test configuration
    ├── test_auth.py  # Authentication tests
    └── test_sips_api.py # SIP API tests
design.md           # System design document
requirements.txt    # Python dependencies
.env.example        # Example environment variables file
README.md           # This file
```

_## Setup Instructions_

_1. **Clone the Repository**_
```bash
git clone <repository-url>
cd mini-sip-tracker
```

_2. **Create and Activate a Python Virtual Environment**_
```bash
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate
```

_3. **Install Dependencies**_
```bash
pip install -r requirements.txt
```

_4. **Set up Supabase**_
   - _Go to [Supabase](https://supabase.com/) and create a new project._
   - _In your Supabase project, navigate to **Project Settings > API**._
     - _Find your **Project URL** (this is your `SUPABASE_URL`)._
     - _Find your **anon public** key (this can be your `SUPABASE_KEY` for client-side operations, or use the **service_role** key if you need to bypass RLS for server-to-server admin tasks, but for JWT validation by this app, the `SUPABASE_KEY` is typically the JWT secret if you were to decode manually, however, we use `supabase.auth.get_user(token)` which relies on the public URL and the provided token). For the `SUPABASE_KEY` in `.env` for this app, it should be the **anon public key** if you are using it with the Supabase client library as configured in `app/auth.py` for `create_client`._
   - _Navigate to **Authentication > Providers** and ensure Email is enabled. You might want to configure other providers if needed._
   - _The database schema (`users`, `sips` tables) will be created automatically by the FastAPI application on its first startup, based on SQLAlchemy models in `app/models.py`._

_5. **Configure Environment Variables**_
   - _Copy the `.env.example` file to a new file named `.env`._
   ```bash
   cp .env.example .env
   ```
   - _Edit `.env` with your actual Supabase credentials and your desired PostgreSQL connection string for SQLAlchemy:_
     ```env
     SUPABASE_URL="your_supabase_project_url" # e.g., https://xyz.supabase.co
     SUPABASE_KEY="your_supabase_anon_public_key"

     # Direct PostgreSQL connection string for SQLAlchemy
     # This usually comes from Supabase -> Project Settings -> Database -> Connection string (URI tab)
     # Ensure you use the format: postgresql://postgres:[YOUR-PASSWORD]@[AWS-ENDPOINT].supabase.co:[PORT]/postgres
     DATABASE_URL="postgresql://user:password@host:port/dbname"
     ```
   - _**Important for `DATABASE_URL`**: Use the direct PostgreSQL connection string provided by Supabase. The application uses SQLAlchemy to interact with this database for SIP and local user data._

_6. **Run the Application**_
```bash
uvicorn app.main:app --reload
```
_The API will be accessible at `http://127.0.0.1:8000`._

_## API Usage Examples_

_*Authentication*_
- _Authentication is handled via JWTs obtained from your Supabase project. Your client application (e.g., frontend, mobile app) will use a Supabase client library to sign up/log in users and get a JWT._
- _All API requests below require an `Authorization` header: `Authorization: Bearer YOUR_SUPABASE_JWT`._

_*1. Create a new SIP Plan*_
```bash
curl -X POST "http://127.0.0.1:8000/sips/" \
-H "Authorization: Bearer YOUR_SUPABASE_JWT" \
-H "Content-Type: application/json" \
-d '{
  "scheme_name": "Parag Parikh Flexi Cap",
  "monthly_amount": 5000,
  "start_date": "2024-01-15"
}'
```
_**Example Response (201 Created):**_
```json
{
  "scheme_name": "Parag Parikh Flexi Cap",
  "monthly_amount": 5000.0,
  "start_date": "2024-01-15",
  "id": 1,
  "user_id": "your-supabase-user-uuid",
  "created_at": "2024-07-15T10:00:00.000Z"
}
```

_*2. Get SIP Summary*_
```bash
curl -X GET "http://127.0.0.1:8000/sips/summary" \
-H "Authorization: Bearer YOUR_SUPABASE_JWT"
```
_**Example Response (200 OK):**_
```json
[
  {
    "scheme_name": "Parag Parikh Flexi Cap",
    "total_invested": 35000.0,  // Example: 5000 * 7 months
    "months_invested": 7
  },
  {
    "scheme_name": "Axis Small Cap Fund",
    "total_invested": 15000.0,  // Example: 3000 * 5 months
    "months_invested": 5
  }
]
```

_## Running Tests_

_To run the unit tests, ensure you have installed `pytest` (it_s in `requirements.txt`)._
_From the project root directory:_
```bash
# If your app directory is not automatically in PYTHONPATH:
export PYTHONPATH=.
# Or on Windows: set PYTHONPATH=.

pytest
```

_This will discover and run tests in the `app/tests` directory._
