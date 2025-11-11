-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.ad_accounts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  project_id uuid NOT NULL,
  channel_id uuid NOT NULL,
  assigned_user_id uuid,
  status text NOT NULL DEFAULT 'new'::text,
  dead_reason text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT ad_accounts_pkey PRIMARY KEY (id),
  CONSTRAINT ad_accounts_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id),
  CONSTRAINT ad_accounts_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id),
  CONSTRAINT ad_accounts_assigned_user_id_fkey FOREIGN KEY (assigned_user_id) REFERENCES public.users(id)
);
CREATE TABLE public.ad_spend_daily (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  ad_account_id uuid NOT NULL,
  user_id uuid NOT NULL,
  date date NOT NULL,
  spend numeric NOT NULL DEFAULT 0,
  leads_count integer NOT NULL DEFAULT 0,
  cost_per_lead numeric NOT NULL DEFAULT 0,
  anomaly_flag boolean NOT NULL DEFAULT false,
  anomaly_reason text,
  note text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT ad_spend_daily_pkey PRIMARY KEY (id),
  CONSTRAINT ad_spend_daily_ad_account_id_fkey FOREIGN KEY (ad_account_id) REFERENCES public.ad_accounts(id),
  CONSTRAINT ad_spend_daily_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.channels (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  service_fee_type text NOT NULL DEFAULT 'percent'::text,
  service_fee_value numeric NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT channels_pkey PRIMARY KEY (id)
);
CREATE TABLE public.import_jobs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  type text NOT NULL,
  status text NOT NULL DEFAULT 'pending'::text,
  file_path text,
  error_log jsonb,
  created_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT import_jobs_pkey PRIMARY KEY (id),
  CONSTRAINT import_jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id)
);
CREATE TABLE public.ledgers (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  type text NOT NULL,
  project_id uuid,
  channel_id uuid,
  ad_account_id uuid,
  amount numeric NOT NULL,
  currency text NOT NULL DEFAULT 'USD'::text,
  occurred_at timestamp with time zone NOT NULL,
  remark text,
  created_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT ledgers_pkey PRIMARY KEY (id),
  CONSTRAINT ledgers_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id),
  CONSTRAINT ledgers_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id),
  CONSTRAINT ledgers_ad_account_id_fkey FOREIGN KEY (ad_account_id) REFERENCES public.ad_accounts(id),
  CONSTRAINT ledgers_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id)
);
CREATE TABLE public.logs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  actor_id uuid,
  action text NOT NULL,
  target_table text,
  target_id uuid,
  before_data jsonb,
  after_data jsonb,
  ip text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT logs_pkey PRIMARY KEY (id),
  CONSTRAINT logs_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.users(id)
);
CREATE TABLE public.projects (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  client_name text,
  currency text NOT NULL DEFAULT 'USD'::text,
  status text NOT NULL DEFAULT 'active'::text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT projects_pkey PRIMARY KEY (id)
);
CREATE TABLE public.reconciliations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  ledger_id uuid NOT NULL,
  ad_spend_id uuid NOT NULL,
  match_score numeric NOT NULL DEFAULT 1,
  matched_by text NOT NULL,
  remark text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT reconciliations_pkey PRIMARY KEY (id),
  CONSTRAINT reconciliations_ledger_id_fkey FOREIGN KEY (ledger_id) REFERENCES public.ledgers(id),
  CONSTRAINT reconciliations_ad_spend_id_fkey FOREIGN KEY (ad_spend_id) REFERENCES public.ad_spend_daily(id)
);
CREATE TABLE public.topups (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  ad_account_id uuid NOT NULL,
  project_id uuid NOT NULL,
  channel_id uuid NOT NULL,
  requested_by uuid NOT NULL,
  amount numeric NOT NULL,
  service_fee_amount numeric,
  status text NOT NULL DEFAULT 'pending'::text,
  remark text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT topups_pkey PRIMARY KEY (id),
  CONSTRAINT topups_ad_account_id_fkey FOREIGN KEY (ad_account_id) REFERENCES public.ad_accounts(id),
  CONSTRAINT topups_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id),
  CONSTRAINT topups_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels(id),
  CONSTRAINT topups_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id)
);
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  email text UNIQUE,
  name text,
  role text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id)
);