_# Design Document: Mini SIP Tracker_

_This document outlines the design considerations for the Mini SIP Tracker application, focusing on scalability, new features, and architectural choices._

_## 1. Introduction_

_The Mini SIP Tracker allows users to manage and track their Systematic Investment Plans (SIPs). This document details the current system and proposes strategies for future growth and feature enhancements._

_## 2. Current System Overview_

_*Tech Stack*_
- _Backend: FastAPI (Python)_
- _Authentication: Supabase JWT_
- _Database: PostgreSQL (via Supabase, and direct SQLAlchemy connection for app data)_
- _ORM: SQLAlchemy_
- _Background Tasks: APScheduler (for SIP execution simulation)_

_*Core Features Implemented*_
- _User Authentication (Supabase JWT, local user mirroring)_
- _Create SIP Plan (`POST /sips/`)_
- _Get SIP Summary (`GET /sips/summary`)_
- _Simulated monthly SIP execution (logging via APScheduler)_

_## 3. Database Schema_

_*Users Table (`users`)*_
- `id` (String, PK): Supabase User ID (UUID).
- `email` (String, Unique): User_s email address.

_*SIPs Table (`sips`)*_
- `id` (Integer, PK): Auto-incrementing primary key for the SIP entry.
- `user_id` (String, FK to users.id): The ID of the user who owns this SIP.
- `scheme_name` (String): Name of the mutual fund scheme.
- `monthly_amount` (Float): The amount invested monthly.
- `start_date` (Date): The date the SIP started or will start.
- `created_at` (DateTime): Timestamp of SIP creation.

_## 4. APIs and Endpoints_

_*Authentication*_
- _Implicitly handled by Supabase for user sign-up/login._
- _All protected endpoints expect a Supabase JWT in the `Authorization: Bearer <token>` header._

_*SIP Management*_
- _`POST /sips/`_: Creates a new SIP plan for the authenticated user.
  - _Request Body: `{ "scheme_name": "...", "monthly_amount": ..., "start_date": "YYYY-MM-DD" }`_
  - _Response: Created SIP object._
- _`GET /sips/summary`_: Retrieves SIPs grouped by scheme, showing total invested and months invested.
  - _Response: `[ { "scheme_name": "...", "total_invested": ..., "months_invested": ... } ]`_

_## 5. Scaling the System (10 Million Users)_

_*Database Scaling*_
- _**Read Replicas**_: Utilize PostgreSQL read replicas to distribute read load for summary calculations and user data retrieval. Supabase may offer this as part of its higher-tier plans, or if self-managing PostgreSQL._
- _**Connection Pooling**_: Implement robust connection pooling (e.g., PgBouncer) if direct DB connections become a bottleneck. FastAPI_s dependency injection with SQLAlchemy sessions helps, but external poolers are vital at scale._
- _**Database Sharding**_: If write loads become extremely high or data size per tenant is massive, consider sharding the database based on `user_id` or a geographical key. This is a complex operation and a last resort._
- _**Archiving Old Data**_: For very old, inactive SIPs or user data, implement an archiving strategy to move data to slower, cheaper storage, keeping the primary database performant._

_*Application Layer Scaling*_
- _**Stateless Application Servers**_: Ensure FastAPI application instances are stateless. User session information is derived from JWTs, and any other state should be in the DB or a distributed cache._
- _**Horizontal Scaling**_: Run multiple instances of the FastAPI application behind a load balancer (e.g., Nginx, AWS ALB, Google Cloud Load Balancing)._
- _**Asynchronous Operations**_: Leverage FastAPI_s async capabilities fully. For longer, non-CPU-bound tasks not suitable for async (like complex report generation if added later), offload to background workers._

_*Supabase Scaling*_
- _Supabase itself is designed for scale. Monitor usage and upgrade Supabase plan tiers as needed for database resources, authentication limits, and other features._
- _Be mindful of API rate limits imposed by Supabase and optimize client-side interactions._

_## 6. Integrating Real-Time NAV APIs_

_*NAV Data Storage*_
- _Create a new table, e.g., `scheme_navs`, to store historical NAV data:_
  - `scheme_identifier` (String, FK/Index): A unique ID for the scheme (e.g., AMFI code).
  - `nav_date` (Date): The date of the NAV.
  - `nav_value` (Float): The NAV for that date.
  - _Primary Key: (`scheme_identifier`, `nav_date`)_

_*NAV Data Fetching*_
- _**Background Task**_: Use a reliable background task runner (e.g., Celery with a message broker like RabbitMQ/Redis, or a more robust setup for APScheduler if it can handle distributed nature and persistence) to fetch NAVs daily from the external API (e.g., AMFI or commercial providers)._
- _**Idempotency**_: Ensure the fetching job is idempotent and can handle API failures/retries._
- _**Rate Limiting**_: Respect the external NAV API_s rate limits._

_*SIP Unit Calculation*_
- _When an SIP is "executed" (either simulated or actually transacted), calculate units purchased: `units = monthly_amount / nav_for_execution_date`._
- _Store these transactions: Create a `sip_transactions` table:_
  - `id` (Integer, PK)_
  - `sip_id` (Integer, FK to `sips.id`)_
  - `transaction_date` (Date)_
  - `amount_invested` (Float)_
  - `nav_value` (Float)_
  - `units_allotted` (Float)_
  - `status` (String, e.g., "processed", "pending")_

_*Impact on Summary/Portfolio*_
- _The `GET /sips/summary` would need to use the `sip_transactions` table to calculate `total_invested` accurately if actual transactions are logged._
- _Current portfolio value would be `total_units_for_scheme * latest_nav_for_scheme`._

_## 7. Portfolio Graphs and Analytics_

_*Data Requirements*_
- _Requires historical NAV data (`scheme_navs`)._
- _Requires SIP transaction data (`sip_transactions`) to know units held over time._

_*Portfolio Value Over Time*_
- _To plot portfolio value: For each point in time (e.g., daily/monthly), calculate total units held per scheme and multiply by the NAV of that scheme on that day._
- _This can be computationally intensive. Pre-aggregate daily/monthly portfolio snapshots for each user in a separate table if performance is an issue, or calculate on-demand for smaller time ranges._

_*Analytics Examples*_
- _Scheme-wise allocation (pie chart)._
- _Growth charts (line graphs of portfolio value vs. time)._
- _XIRR (internal rate of return) calculation for overall portfolio or specific SIPs._

_*API Endpoints for Analytics*_
- _`GET /portfolio/value_history?range=1Y`_: Returns time-series data for portfolio value._
- _`GET /portfolio/allocation`_: Returns current scheme allocation._

_*Technology*_
- _Backend calculations in Python._
- _Consider a dedicated analytics database or view if queries become too complex for the primary OLTP database (e.g., a denormalized table or a data warehouse for very large scale)._

_## 8. Caching Strategies_

- _**User SIP Summary (`GET /sips/summary`)**_: This data changes less frequently (when a SIP is created, or once a month as `months_invested` increments). Cache this per user._
  - _Tool: Redis or Memcached._
  - _Cache Key: `user:{user_id}:sips_summary`._
  - _Invalidation: On new SIP creation for the user, or use a TTL (e.g., 1 hour to daily)._
- _**Scheme NAVs**_: Latest NAV for schemes can be cached application-wide as it_s the same for all users._
  - _Cache Key: `scheme:{scheme_identifier}:latest_nav`._
  - _Invalidation: When the NAV fetching background job updates NAVs._
- _**Portfolio Analytics Data**_: Pre-calculated portfolio snapshots or frequently requested analytics can be cached per user._
- _**Caching Layer**_: Implement caching within FastAPI route dependencies or dedicated utility functions._

_## 9. Background Tasks_

- _**Current (APScheduler)**_: Simulates SIP execution. For a single-node deployment or simple tasks, this is adequate._
- _**Scaling (Celery)**_: For a distributed, multi-node application deployment and more complex background tasks (NAV fetching, report generation, email notifications), transition to Celery with a robust message broker (RabbitMQ/Redis)._
  - _**Task Queues**_: Separate queues for different task priorities (e.g., high-priority for NAV fetching, low-priority for analytics pre-computation)._
  - _**Workers**_: Dedicated Celery worker processes that can be scaled independently of the API servers._
  - _**Monitoring**_: Tools like Flower for Celery monitoring._

_## 10. Security & Multi-tenant Architecture_

_*Security*_
- _**Authentication**_: Supabase JWTs provide robust authentication. Ensure tokens are validated on every request to protected endpoints._
- _**Authorization**_: All data access must be strictly scoped by `user_id`. CRUD operations must ensure a user can only access/modify their own data. This is currently handled by filtering queries by `user_id` obtained from the JWT._
- _**Input Validation**_: Pydantic schemas validate request data, preventing many common injection-type vulnerabilities at the application layer._
- _**HTTPS**_: Enforce HTTPS for all communication._
- _**Dependency Security**_: Regularly scan dependencies for vulnerabilities (e.g., using `pip-audit` or GitHub Dependabot)._
- _**Secrets Management**_: Use environment variables for secrets (DB URL, Supabase keys, JWT secrets if any were self-managed). For production, use a secrets management system (e.g., HashiCorp Vault, AWS Secrets Manager)._

_*Multi-tenancy*_
- _The current design is logically multi-tenant at the data layer: each SIP record is tied to a `user_id`. All database queries for user-specific data must include a `WHERE user_id = :current_user_id` clause._
- _No data should be accessible without proper `user_id` scoping. This is critical and needs to be enforced in all database interaction logic (CRUD functions)._
- _Supabase handles user isolation at the authentication level._

_## 11. Microservices Layout (Bonus for Larger Scale)_

_*Rationale*_
- _As the system grows significantly in complexity and team size, a microservices architecture might become beneficial for independent scaling, deployment, and development._

_*Potential Services*_
- _**User Service**: Manages user profiles, preferences (if expanded beyond Supabase). Could be a thin wrapper if Supabase handles most user data._
- _**SIP Management Service**: Handles CRUD for SIP plans (`/sips/` endpoints)._
- _**NAV Service**: Responsible for fetching, storing, and providing NAV data. Exposes an internal API for other services._
- _**Portfolio & Analytics Service**: Calculates portfolio values, generates analytics, and serves related API endpoints. Consumes data from SIP Service and NAV Service._
- _**Notification Service**: Manages sending emails, push notifications (e.g., SIP execution confirmations)._
- _**Scheduler Service**: Manages and executes scheduled tasks (could wrap Celery workers for specific domains like NAV fetching or SIP processing)._

_*Communication*_
- _Synchronous: REST APIs (HTTP) or gRPC for inter-service communication._
- _Asynchronous: Event-driven using a message bus (e.g., Kafka, RabbitMQ) for events like "SIPCreated", "NAVFetched"._

_*Data Management*_
- _Each service would own its database schema. This can introduce data consistency challenges, often handled by eventual consistency or distributed transaction patterns (complex)._

_*Deployment & Orchestration*_
- _Docker containers for each service._
- _Kubernetes for orchestration, scaling, and management._

_*API Gateway*_
- _A single entry point for client applications, routing requests to appropriate microservices. Handles concerns like authentication (can verify JWTs and pass user info downstream), rate limiting, and request aggregation._

_This transition would be a significant undertaking, justified when the monolithic application becomes a bottleneck to development velocity or independent scaling of components._
