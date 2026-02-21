# Mealframe -- Authentication & Multi-User Architecture PRD

## 1. Objective

Transform Mealframe from: - Single-user, unsecured access - Shared
backend state - No authentication

Into: - Fully authenticated application - Strict per-user data
isolation - Secure credential handling - Scalable foundation for
subscriptions & OpenAI metering - Future-ready for sharing/marketplace
features

------------------------------------------------------------------------

## 2. Scope (MVP)

### Included

-   Email/password authentication
-   OAuth (Google)
-   Secure session management
-   Password reset flow
-   Email verification
-   Per-user data isolation
-   User settings page
-   OpenAI usage abstraction (system key)
-   Basic usage metering structure (internal only)

### Excluded (Future)

-   Sharing between users
-   Marketplace
-   Role-based access
-   Billing system
-   Team accounts
-   Social login beyond Google

------------------------------------------------------------------------

## 3. User Model (MVP)

### Core Principle

Each account = completely isolated sandbox.

No cross-user access.\
No shared templates.\
No visibility into other users.

------------------------------------------------------------------------

## 4. Database Schema (High-Level)

### users

-   id (UUID, PK)
-   email (unique, indexed)
-   password_hash (Argon2id)
-   email_verified (bool)
-   created_at
-   updated_at
-   openai_usage_tokens (int)
-   subscription_status (nullable)
-   is_active (bool)

### meals

-   id
-   user_id (FK → users.id, indexed)
-   name
-   structure_json
-   created_at

### templates

-   id
-   user_id (FK)
-   name
-   structure_json
-   created_at

All queries MUST be filtered by `user_id`.

------------------------------------------------------------------------

## 5. Authentication Architecture

### Recommended Approach

Use OAuth 2.0 / OpenID Connect with JWT-based session tokens.

#### Preferred: Managed Identity Provider

Examples: - Auth0 - Supabase Auth - Firebase Auth - Clerk

Benefits: - Secure password handling - Email verification built-in -
Password reset flows - OAuth integrations - Reduced attack surface

#### Alternative: Self-Managed

-   FastAPI OAuth2
-   Argon2id password hashing
-   JWT issuance & validation
-   Email service integration

Higher engineering and security burden.

------------------------------------------------------------------------

## 6. Authentication Flows

### Sign Up

1.  User submits email/password
2.  Password hashed with Argon2id
3.  Verification email sent
4.  Account activated upon verification

### Login

1.  Credentials validated
2.  Short-lived JWT issued
3.  Refresh token stored in HTTP-only cookie
4.  Token rotation enabled

### Password Reset

1.  User requests reset
2.  Time-limited token emailed
3.  Password updated securely
4.  Sessions invalidated

### Google OAuth

1.  Redirect to Google
2.  OIDC validation
3.  Verified email used
4.  Local user record created

------------------------------------------------------------------------

## 7. Session Security Requirements

-   HTTPS only
-   HTTP-only cookies
-   Secure flag enabled
-   CSRF protection
-   Access token expiry ≤ 15 minutes
-   Refresh token rotation
-   Rate limiting on auth endpoints
-   Brute force mitigation
-   Session invalidation capability

------------------------------------------------------------------------

## 8. OpenAI Integration Model

### Recommended: System OpenAI Key

-   Stored in secure backend environment variable
-   All requests proxied through backend
-   Users never see API keys
-   Per-user usage tracking implemented

### Usage Tracking Table

#### openai_usage

-   id
-   user_id
-   model
-   tokens_prompt
-   tokens_completion
-   cost_estimate
-   timestamp

Future-ready for subscription or credit model.

------------------------------------------------------------------------

## 9. Settings Page (MVP)

Sections: - Profile (email, change password) - Session management
(logout all devices) - Delete account - Optional usage summary

------------------------------------------------------------------------

## 10. Security Requirements

### Password Handling

-   Argon2id hashing
-   Unique salt
-   Never log credentials
-   Avoid account enumeration leaks

### Data Protection

-   Auth middleware on all routes
-   Strict user_id filtering
-   Backend ownership validation
-   No client-side trust

### Infrastructure

-   Secure CORS policy
-   Structured logging (no sensitive data)
-   SQL injection protection via ORM

------------------------------------------------------------------------

## 11. Threat Model Overview

  Threat                 Mitigation
  ---------------------- -------------------------------
  Brute force login      Rate limiting
  Token theft            HTTP-only cookies
  XSS                    CSP + sanitization
  CSRF                   CSRF tokens
  SQL injection          Parameterized queries
  Cross-user data leak   Mandatory user_id enforcement

------------------------------------------------------------------------

## 12. Data Isolation Strategy

### MVP Approach: Row-Level Isolation

-   Single database
-   Strict filtering by user_id
-   Enforced at backend layer

Future-compatible with shared resources via explicit permission models.

------------------------------------------------------------------------

## 13. Account Deletion Policy

On account deletion: - Cascade delete meals/templates - Invalidate all
sessions - Remove usage records if required for compliance

GDPR-aligned deletion workflow recommended.

------------------------------------------------------------------------

## 14. Observability

-   Audit logs for:
    -   Login attempts
    -   Password resets
    -   Account deletions
-   Internal admin dashboard (future)

------------------------------------------------------------------------

## 15. Migration Plan

1.  Create users table
2.  Add user_id to existing tables
3.  Backfill existing data to admin user
4.  Implement auth middleware
5.  Deploy behind feature flag

------------------------------------------------------------------------

## 16. Future Compatibility

Architecture must support: - Shared templates - Public/private flags -
Marketplace - Subscription tiers - Team accounts - Admin roles

Ownership must remain explicit and enforceable at database and API
layers.
