## About the Project

FreshReceipt helps users track household groceries and receipts, organize members in households, and detect items that are expiring or need attention. It combines a React Native (Expo) front end with a Python FastAPI backend and Postgres/Supabase for data, auth, and storage.

Key goals:

- Make it fast to scan and record purchase receipts.
- Keep household members synchronized with simple permissions and roles.
- Provide a privacy-first design where secrets live in environment variables and RLS enforces row-level access.

This repository contains the Expo app UI, API server (FastAPI), database helpers, and RLS policy migrations used to run the project locally or on Supabase/EAS.

## Built With

- Expo / React Native (app/) — UI, navigation (expo-router), mobile-first UX
- TypeScript — frontend code
- FastAPI (api/app/) — backend HTTP API and business logic (Python)
- Supabase / Postgres — database, auth, RLS policies, and RPC functions
- asyncio + asyncio.to_thread — safe use of synchronous Supabase Python client inside async FastAPI handlers
- EAS / eas.json — build and CI configuration

## User Flow

1. User signs up or logs in via the mobile app (Supabase Auth).
2. On first sign-in, the backend ensures the user has a primary household (RPC creates household + member atomically).
3. User can scan receipts or manually add items; items are associated with a household and tracked for expiration.
4. Household members (owner/admin/member roles) can invite others, view members, and manage items.
5. Security: Row-Level Security (RLS) policies restrict data access to authenticated users and household members. A SECURITY DEFINER RPC is used for privileged operations that must bypass RLS safely.

## Roadmap

Planned improvements and next steps:

- Finish and test RLS policies and SECURITY DEFINER helpers (already included under db/policies/).
- Add end-to-end tests for critical flows (auth, household creation, item scanning).
- Improve offline support and syncing for the mobile app.
- Add image OCR & ML integration for receipt parsing and auto-categorization.
- CI: Add automated policy checks and a migration test harness.
- UX: Add household settings, member notifications, and item recommendations.
