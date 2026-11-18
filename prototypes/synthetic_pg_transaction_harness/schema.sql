-- STAGE B ONLY. Synthetic disposable harness SQL, NOT an application migration.
-- Stage A does not parse or execute this file against PostgreSQL.
-- Before creating ANY object, require the independently prepared disposable marker.
DO $guard$
DECLARE m record; n integer;
BEGIN
  IF current_database() !~ '^migramind_throttle_synthetic_[0-9a-f]{32}$'
     OR current_user <> 'mm_synthetic_' || right(current_database(),32)
     OR session_user <> current_user OR pg_is_in_recovery()
     OR (SELECT pg_get_userbyid(datdba) FROM pg_catalog.pg_database WHERE datname=current_database()) IS DISTINCT FROM current_user
     OR current_setting('transaction_read_only') <> 'off'
     OR to_regclass('harness_bootstrap.identity') IS NULL THEN
    RAISE EXCEPTION 'Synthetic target guard rejected';
  END IF;
  SELECT count(*) INTO n FROM harness_bootstrap.identity;
  SELECT * INTO STRICT m FROM harness_bootstrap.identity WHERE id=1;
  IF n<>1 OR m.nonce IS DISTINCT FROM right(current_database(),32)
     OR m.classification IS DISTINCT FROM 'SYNTHETIC_ONLY_DISPOSABLE' OR m.synthetic_only IS DISTINCT FROM true
     OR m.db_name IS DISTINCT FROM current_database() OR m.role_name IS DISTINCT FROM current_user
     OR m.schema_tag IS DISTINCT FROM 'migramind-throttle-harness-v1' THEN
    RAISE EXCEPTION 'Synthetic marker guard rejected';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=current_user
             AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
    RAISE EXCEPTION 'Privileged role refused';
  END IF;
END
$guard$;

CREATE SCHEMA synthetic_throttle;
REVOKE ALL ON SCHEMA synthetic_throttle FROM PUBLIC;

CREATE FUNCTION synthetic_throttle.valid_window(scope smallint, values_ms bigint[])
RETURNS boolean LANGUAGE sql IMMUTABLE STRICT SECURITY INVOKER SET search_path=pg_catalog AS $valid$
  SELECT coalesce(scope IN (0,1) AND array_ndims(values_ms)=1 AND array_lower(values_ms,1)=1
    AND cardinality(values_ms) BETWEEN 1 AND CASE WHEN scope=0 THEN 30 ELSE 10 END
    AND NOT EXISTS (SELECT 1 FROM generate_subscripts(values_ms,1) AS g(i)
      WHERE values_ms[i] IS NULL OR values_ms[i]<0 OR values_ms[i]>9223372036853875807
      OR (i>1 AND values_ms[i]<values_ms[i-1])), false)
$valid$;

CREATE TABLE synthetic_throttle.control (
  id smallint PRIMARY KEY CHECK(id=1), nonce text NOT NULL,
  generation text NOT NULL, writer_hint text NOT NULL,
  state text NOT NULL CHECK(state IN ('READY','QUARANTINED')),
  last_db_ms bigint NOT NULL CHECK(last_db_ms BETWEEN 0 AND 9223372036853875807),
  key_count integer NOT NULL CHECK(key_count BETWEEN 0 AND max_keys),
  max_keys integer NOT NULL CHECK(max_keys BETWEEN 2 AND 10000)
);
CREATE TABLE synthetic_throttle.bindings (id integer PRIMARY KEY, valid boolean NOT NULL);
CREATE TABLE synthetic_throttle.windows (
  scope smallint NOT NULL CHECK(scope IN (0,1)),
  digest bytea NOT NULL CHECK(octet_length(digest)=32),
  times_ms bigint[] NOT NULL, expires_ms bigint NOT NULL,
  PRIMARY KEY(scope,digest),
  CHECK(synthetic_throttle.valid_window(scope,times_ms)),
  CHECK(expires_ms=times_ms[cardinality(times_ms)]+900000)
);
CREATE INDEX synthetic_throttle_expiry ON synthetic_throttle.windows(expires_ms);

CREATE FUNCTION synthetic_throttle.reserve_attempt(
  p_action text, p_binding integer, p_ip bytea, p_account bytea,
  p_generation text, p_writer text, p_sample_ms bigint DEFAULT NULL,
  p_guard boolean DEFAULT true, p_time_trusted boolean DEFAULT true,
  p_fresh boolean DEFAULT true, p_fault text DEFAULT NULL)
RETURNS text LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $reserve$
DECLARE c synthetic_throttle.control%ROWTYPE; r record; v_valid boolean;
  ip_values bigint[]:=ARRAY[]::bigint[]; account_values bigint[]:=ARRAY[]::bigint[];
  ip_found boolean:=false; account_found boolean:=false;
  v_now bigint; v_missing integer; v_count integer;
BEGIN
  IF p_action IS NULL OR p_action NOT IN ('login','register') OR octet_length(p_ip)<>32 OR octet_length(p_account)<>32
     OR p_ip IS NULL OR p_account IS NULL THEN RAISE EXCEPTION 'Invalid synthetic request'; END IF;
  IF p_guard IS DISTINCT FROM true THEN RETURN 'guard_rejected'; END IF;
  -- LOCK ORDER 1: synthetic binding only; no app session/CSRF implementation.
  SELECT valid INTO v_valid FROM synthetic_throttle.bindings WHERE id=p_binding FOR SHARE;
  IF v_valid IS DISTINCT FROM true THEN RETURN 'guard_rejected'; END IF;
  -- LOCK ORDER 2: global gate, including missing-key creation and maintenance.
  SELECT * INTO c FROM synthetic_throttle.control WHERE id=1 FOR UPDATE;
  IF NOT FOUND THEN RETURN 'unavailable'; END IF;
  IF c.nonce<>right(current_database(),32) OR c.state<>'READY' THEN RETURN 'unavailable'; END IF;
  IF c.generation IS DISTINCT FROM p_generation OR c.writer_hint IS DISTINCT FROM p_writer OR p_time_trusted IS DISTINCT FROM true
     OR p_fresh IS DISTINCT FROM true THEN
    UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;
    RETURN 'unavailable';
  END IF;
  -- LOCK ORDER 3: existing keys only. Missing rows remain in memory until allowed.
  FOR r IN SELECT * FROM synthetic_throttle.windows
    WHERE (scope=0 AND digest=p_ip) OR (scope=1 AND digest=p_account)
    ORDER BY scope,digest FOR UPDATE
  LOOP
    IF r.scope=0 THEN ip_values:=r.times_ms;ip_found:=true;
    ELSE account_values:=r.times_ms;account_found:=true;END IF;
    IF r.times_ms[cardinality(r.times_ms)]>c.last_db_ms THEN
      UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;RETURN 'unavailable';
    END IF;
  END LOOP;
  -- Test-only p_sample_ms is legal only in this marker-gated synthetic schema.
  v_now:=coalesce(p_sample_ms,floor(extract(epoch FROM clock_timestamp())*1000)::bigint);
  IF v_now<0 OR v_now>9223372036853875807 OR v_now<c.last_db_ms THEN
    UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;RETURN 'unavailable';
  END IF;
  SELECT count(*) INTO v_count FROM (SELECT 1 FROM synthetic_throttle.windows LIMIT 10001) bounded;
  IF v_count<>c.key_count THEN
    UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;RETURN 'unavailable';
  END IF;
  SELECT coalesce(array_agg(v ORDER BY n),ARRAY[]::bigint[]) INTO ip_values
    FROM unnest(ip_values) WITH ORDINALITY AS a(v,n) WHERE v>v_now-900000;
  SELECT coalesce(array_agg(v ORDER BY n),ARRAY[]::bigint[]) INTO account_values
    FROM unnest(account_values) WITH ORDINALITY AS a(v,n) WHERE v>v_now-900000;
  IF cardinality(ip_values)>=30 OR cardinality(account_values)>=10 THEN
    UPDATE synthetic_throttle.control SET last_db_ms=v_now WHERE id=1;RETURN 'limited';
  END IF;
  v_missing:=(CASE WHEN ip_found THEN 0 ELSE 1 END)+(CASE WHEN account_found THEN 0 ELSE 1 END);
  IF c.key_count+v_missing>c.max_keys THEN RETURN 'unavailable'; END IF;
  ip_values:=array_append(ip_values,v_now);account_values:=array_append(account_values,v_now);
  IF ip_found THEN UPDATE synthetic_throttle.windows SET times_ms=ip_values,expires_ms=v_now+900000 WHERE scope=0 AND digest=p_ip;
  ELSE INSERT INTO synthetic_throttle.windows VALUES(0,p_ip,ip_values,v_now+900000);END IF;
  IF p_fault='after_ip_write' THEN RAISE EXCEPTION 'Synthetic injected abort';END IF;
  IF account_found THEN UPDATE synthetic_throttle.windows SET times_ms=account_values,expires_ms=v_now+900000 WHERE scope=1 AND digest=p_account;
  ELSE INSERT INTO synthetic_throttle.windows VALUES(1,p_account,account_values,v_now+900000);END IF;
  UPDATE synthetic_throttle.control SET key_count=key_count+v_missing,last_db_ms=v_now WHERE id=1;
  IF p_fault='before_commit' THEN RAISE EXCEPTION 'Synthetic injected abort';END IF;
  RETURN 'allowed'; -- Caller must COMMIT before treating this as confirmed.
END
$reserve$;

CREATE FUNCTION synthetic_throttle.cleanup(p_sample_ms bigint DEFAULT NULL,p_after_ms bigint DEFAULT NULL,
  p_batch integer DEFAULT 100,p_fault text DEFAULT NULL,p_generation text DEFAULT NULL,
  p_writer text DEFAULT NULL,p_time_trusted boolean DEFAULT NULL,p_fresh boolean DEFAULT NULL)
RETURNS integer LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $cleanup$
DECLARE c synthetic_throttle.control%ROWTYPE;r record;v_first bigint;v_now bigint;
  scopes smallint[]:=ARRAY[]::smallint[];digests bytea[]:=ARRAY[]::bytea[];
  i integer;removed integer:=0;n integer;v_count integer;
BEGIN
  IF p_batch NOT BETWEEN 1 AND 100 OR p_batch IS NULL THEN RAISE EXCEPTION 'Bounded synthetic batch required';END IF;
  SELECT * INTO c FROM synthetic_throttle.control WHERE id=1 FOR UPDATE;
  IF NOT FOUND OR c.state<>'READY' OR c.nonce<>right(current_database(),32) THEN RETURN -1;END IF;
  -- Caller assertions are required for maintenance as well as admission.
  IF c.generation IS DISTINCT FROM p_generation OR c.writer_hint IS DISTINCT FROM p_writer
     OR p_time_trusted IS DISTINCT FROM true OR p_fresh IS DISTINCT FROM true THEN
    UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;RETURN -1;END IF;
  SELECT count(*) INTO v_count FROM (SELECT 1 FROM synthetic_throttle.windows LIMIT 10001) bounded;
  IF v_count<>c.key_count THEN
    UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;RETURN -1;END IF;
  v_first:=coalesce(p_sample_ms,floor(extract(epoch FROM clock_timestamp())*1000)::bigint);
  IF v_first<c.last_db_ms OR v_first<0 OR v_first>9223372036853875807 THEN
    UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;RETURN -1;END IF;
  FOR r IN SELECT w.scope,w.digest FROM synthetic_throttle.windows w
    JOIN (SELECT scope,digest FROM synthetic_throttle.windows WHERE expires_ms<=v_first
          ORDER BY expires_ms,scope,digest LIMIT p_batch) candidates USING(scope,digest)
    ORDER BY w.scope,w.digest FOR UPDATE OF w
  LOOP scopes:=array_append(scopes,r.scope);digests:=array_append(digests,r.digest);END LOOP;
  v_now:=coalesce(p_after_ms,p_sample_ms,floor(extract(epoch FROM clock_timestamp())*1000)::bigint);
  IF v_now<v_first OR v_now<c.last_db_ms OR v_now>9223372036853875807 THEN
    UPDATE synthetic_throttle.control SET state='QUARANTINED' WHERE id=1;RETURN -1;END IF;
  FOR i IN 1..coalesce(cardinality(scopes),0) LOOP
    DELETE FROM synthetic_throttle.windows WHERE scope=scopes[i] AND digest=digests[i] AND expires_ms<=v_now;
    GET DIAGNOSTICS n=ROW_COUNT;removed:=removed+n;
  END LOOP;
  UPDATE synthetic_throttle.control SET key_count=key_count-removed,last_db_ms=v_now WHERE id=1;
  IF p_fault='before_commit' THEN RAISE EXCEPTION 'Synthetic injected abort';END IF;
  RETURN removed;
END
$cleanup$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA synthetic_throttle FROM PUBLIC;
-- No COMMIT inside functions: test caller owns commit/rollback boundaries.
-- No DROP, database creation, credentials, app schema or recovery/reset command.
