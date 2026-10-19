# Deployment Guide — Knowledge AI

This guide details how to deploy Knowledge AI to production using **Supabase** (Database + pgvector + Auth), **Render / Railway** (FastAPI Backend), and **Vercel** (React Frontend).

---

## 1. Database & Supabase Setup

1. Create a new project in [Supabase](https://supabase.com).
2. In the Supabase SQL Editor, run the pgvector extension activation:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Run the migrations script from `backend/migrations/` or via Alembic:
   ```bash
   cd backend
   alembic upgrade head
   ```
4. Note your:
   - Project URL (`https://<project-ref>.supabase.co`)
   - Anon public key
   - JWT Secret (found under **Project Settings > API > JWT Settings**)
   - Connection string (`postgresql+asyncpg://postgres:[password]@db.<project-ref>.supabase.co:5432/postgres`)

---

## 2. Backend Deployment (Render or Railway)

### Using Render
1. Create a **New Web Service** pointing to your repository.
2. Root Directory: `backend`.
3. Runtime: **Docker** (using `backend/Dockerfile`) or **Python 3.11**.
4. Set Environment Variables:
   - `ENVIRONMENT=production`
   - `PORT=8000`
   - `DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`
   - `GEMINI_API_KEY=your-gemini-api-key`
   - `SUPABASE_URL=https://[PROJECT].supabase.co`
   - `SUPABASE_JWT_SECRET=your-jwt-secret`
   - `CORS_ORIGINS=https://your-frontend.vercel.app`
5. Health Check Path: `/health`.

---

## 3. Frontend Deployment (Vercel)

1. Import repository in [Vercel](https://vercel.com).
2. Framework Preset: **Vite**.
3. Root Directory: `frontend`.
4. Build Command: `npm run build`.
5. Output Directory: `dist`.
6. Environment Variables:
   - `VITE_API_BASE_URL=https://your-backend.onrender.com`
   - `VITE_SUPABASE_URL=https://[PROJECT].supabase.co`
   - `VITE_SUPABASE_ANON_KEY=your-supabase-anon-key`
7. In Supabase Auth Settings, add `https://your-frontend.vercel.app` to **Site URL** and **Redirect URLs**.

---

## 4. Post-Deployment Verification Checklist

- [ ] `GET https://your-backend/health` returns `{"status": "healthy"}`.
- [ ] `GET https://your-backend/ready` returns `{"status": "ready"}`.
- [ ] Sign up new test user in frontend.
- [ ] Create a collection.
- [ ] Upload a test PDF and verify `INDEXED` status.
- [ ] Query the document and confirm citations and evidence sufficiency.
