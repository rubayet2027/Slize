# Slize

Slize is a single-file Streamlit app for turning long videos into vertical shorts with Supabase-backed Google auth, per-user history, and a neon creator UI.

## What Changed

- `app.py` now owns the full app flow: auth, routing, upload, slicing, and history.
- Supabase OAuth is handled with PKCE and a session-backed storage layer, so login redirects back into the app without a refresh loop.
- `st.navigation` is used once, after auth is resolved, so pages do not render twice.
- Old helper scripts were removed to keep the repo minimal.

## File Layout

- `app.py` - the complete app.
- `requirements.txt` - Python dependencies.
- `.streamlit/secrets.example.toml` - example config.
- `README.md` - setup and troubleshooting.
- `packages.txt` - keeps FFmpeg available on Streamlit Cloud.

## Local Setup

1. Install Python dependencies.

   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example secrets file.

   ```bash
   copy .streamlit\secrets.example.toml .streamlit\secrets.toml
   ```

3. Fill in your Supabase project URL and anon key.

4. Run the app.

   ```bash
   streamlit run app.py
   ```

## Supabase Setup

### 1. Enable Google Auth

In the Supabase Dashboard:

- Open `Authentication` -> `Providers` -> `Google`.
- Add your Google OAuth client ID and client secret there.
- Keep the app secrets focused on the Supabase URL and anon key only.

### 2. Set Redirect URLs

In `Authentication` -> `URL Configuration` add:

- `http://localhost:8501`
- `https://YOUR-STREAMLIT-APP.streamlit.app`

Set the site URL to your deployed Streamlit app URL in production.

### 3. Create Tables

Run this SQL in the Supabase SQL editor:

```sql
create extension if not exists pgcrypto;

create table if not exists public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null unique,
    name text,
    avatar_url text,
    created_at timestamptz not null default now(),
    last_login timestamptz not null default now()
);

create table if not exists public.user_shorts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    email text not null,
    clip_name text not null,
    original_video text not null,
    output_path text,
    start_time numeric not null,
    end_time numeric not null,
    aspect_ratio text not null,
    speed numeric not null default 1,
    caption text,
    created_at timestamptz not null default now()
);

alter table public.users enable row level security;
alter table public.user_shorts enable row level security;

drop policy if exists "users_manage_own_profile" on public.users;
create policy "users_manage_own_profile"
on public.users
for all
using (auth.uid() = id)
with check (auth.uid() = id);

drop policy if exists "shorts_select_own" on public.user_shorts;
create policy "shorts_select_own"
on public.user_shorts
for select
using (auth.uid() = user_id);

drop policy if exists "shorts_insert_own" on public.user_shorts;
create policy "shorts_insert_own"
on public.user_shorts
for insert
with check (auth.uid() = user_id);

drop policy if exists "shorts_update_own" on public.user_shorts;
create policy "shorts_update_own"
on public.user_shorts
for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "shorts_delete_own" on public.user_shorts;
create policy "shorts_delete_own"
on public.user_shorts
for delete
using (auth.uid() = user_id);
```

## Example `secrets.toml`

```toml
[supabase]
url = "https://YOUR-PROJECT.supabase.co"
key = "YOUR_SUPABASE_ANON_KEY"

[auth]
redirect_uri = "http://localhost:8501"
```

Google OAuth is configured in the Supabase dashboard, not in Streamlit secrets.

## Troubleshooting

- If login redirects but the app stays on the login screen, confirm the redirect URL in Supabase matches the exact deployment URL.
- If the app loops after sign-in, clear browser cookies, stop the Streamlit server, and retry with a fresh auth code.
- If video export fails, verify FFmpeg is installed locally and that `packages.txt` is present on Streamlit Cloud.
- If the history page is empty, confirm the `user_shorts` RLS policies are applied and the user generated clips after logging in.
- If user rows are missing, check that the `users` table primary key is `auth.users.id` and that `last_login` is writable.

## Recommended Login Hero Images

These work well if you want to add a custom background later:

- `https://images.unsplash.com/photo-1516321497487-e288fb19713f`
- `https://images.unsplash.com/photo-1492684223066-81342ee5ff30`
- `https://images.unsplash.com/photo-1515378791036-0648a3ef77b2`
- `https://images.unsplash.com/photo-1517245386807-bb43f82c33c4`
- `https://images.unsplash.com/photo-1498050108023-c5249f4df085`
