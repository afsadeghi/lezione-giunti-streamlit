# Salvataggio permanente dei percorsi

## 1. Creare la tabella in Supabase

Aprire **SQL Editor** nel progetto Supabase, incollare il codice seguente e premere **Run**.

```sql
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.lesson_progress (
  student_code_hash text primary key,
  progress jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.lesson_progress enable row level security;

-- Nessuna policy diretta: l'utente anonimo non può elencare o leggere la tabella.

create or replace function public.set_lesson_progress_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists lesson_progress_updated_at on public.lesson_progress;
create trigger lesson_progress_updated_at
before update on public.lesson_progress
for each row execute function public.set_lesson_progress_updated_at();

create or replace function public.get_lesson_progress(p_student_code text)
returns jsonb
language sql
security definer
set search_path = public, extensions
as $$
  select progress
  from public.lesson_progress
  where student_code_hash = encode(digest(upper(trim(p_student_code)), 'sha256'), 'hex');
$$;

create or replace function public.save_lesson_progress(
  p_student_code text,
  p_progress jsonb
)
returns void
language plpgsql
security definer
set search_path = public, extensions
as $$
begin
  insert into public.lesson_progress(student_code_hash, progress)
  values (
    encode(digest(upper(trim(p_student_code)), 'sha256'), 'hex'),
    p_progress
  )
  on conflict (student_code_hash)
  do update set progress = excluded.progress;
end;
$$;

revoke all on function public.get_lesson_progress(text) from public;
revoke all on function public.save_lesson_progress(text, jsonb) from public;
grant execute on function public.get_lesson_progress(text) to anon, authenticated;
grant execute on function public.save_lesson_progress(text, jsonb) to anon, authenticated;
```

La tabella contiene soltanto l'impronta crittografica del codice e i dati della lezione. Il codice non è memorizzato in chiaro e la tabella non è accessibile direttamente. Non usare comunque nome, cognome o data di nascita nel codice.

## 2. Inserire i segreti in Streamlit Cloud

Aprire **Manage app → Settings → Secrets** e inserire:

```toml
[supabase]
url = "https://ID-PROGETTO.supabase.co"
anon_key = "CHIAVE-ANON-PUBBLICA"
```

I due valori si trovano in Supabase in **Project Settings → API**.

Non aggiungere la chiave `service_role`: nell'app va usata esclusivamente la chiave pubblica `anon`.
