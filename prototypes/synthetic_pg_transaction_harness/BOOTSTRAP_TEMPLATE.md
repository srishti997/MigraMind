# Non-owner bootstrap template — unapplied, not executable

**Review artifact only.** Do not paste or execute. Angle-bracket fields are
deliberately unresolved identifiers or values. No application migrations or
application configuration participate. No server or container is provisioned.

For each of the 17 methods in `case_contract.CASE_NAMES`, an independently
controlled bootstrap authority must derive the exact `Case(nonce, ordinal)`
database, fixture, maintenance and owner names. The same independently
generated 32-hex run nonce and distinct ordinal 001–017 identify each case.
The owner is separate from all fixture and maintenance roles. Before any
creation the provisioner must independently verify a fresh disposable instance,
reject every collision or partial state, use identifier-aware quoting, and not
reuse an interrupted case. No executable provisioner is provided.

```sql
-- UNAPPLIED TEMPLATE. NOT VALID SQL: placeholders intentionally unresolved.
CREATE ROLE <owner> NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT;
CREATE ROLE <fixture> LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT;
CREATE ROLE <maintenance> LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT;
CREATE DATABASE <case_database> OWNER <owner>;
-- Independently controlled bootstrap must perform the following as <owner>
-- via a separately reviewed authority; fixture and maintenance never SET ROLE.
CREATE SCHEMA harness_bootstrap AUTHORIZATION <owner>;
CREATE TABLE harness_bootstrap.identity (
  id smallint PRIMARY KEY CHECK(id=1),
  nonce text NOT NULL CHECK(nonce ~ '^[0-9a-f]{32}$'),
  case_ordinal smallint NOT NULL CHECK(case_ordinal BETWEEN 1 AND 17),
  classification text NOT NULL CHECK(classification='SYNTHETIC_ONLY_DISPOSABLE'),
  synthetic_only boolean NOT NULL CHECK(synthetic_only),
  db_name text NOT NULL, owner_name text NOT NULL,
  fixture_role text NOT NULL, maintenance_role text NOT NULL,
  schema_tag text NOT NULL CHECK(schema_tag='migramind-throttle-harness-v1')
);
INSERT INTO harness_bootstrap.identity VALUES
 (1, <nonce_value>, <ordinal_value>, 'SYNTHETIC_ONLY_DISPOSABLE', true,
  <database_value>, <owner_value>, <fixture_value>, <maintenance_value>,
  'migramind-throttle-harness-v1');
-- As owner, install independently reviewed schema.sql and initialize control
-- using the exact same marker nonce, plus one synthetic binding. This is
-- intentionally a separate reviewed bootstrap step, not a runner operation.
REVOKE ALL ON DATABASE <case_database> FROM PUBLIC;
GRANT CONNECT ON DATABASE <case_database> TO <fixture>, <maintenance>;
REVOKE ALL ON SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
GRANT USAGE ON SCHEMA harness_bootstrap, synthetic_throttle TO <fixture>, <maintenance>;
REVOKE ALL ON ALL TABLES IN SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA harness_bootstrap, synthetic_throttle FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA synthetic_throttle FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE <owner> REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
GRANT SELECT ON harness_bootstrap.identity TO <fixture>, <maintenance>;
GRANT SELECT, UPDATE ON synthetic_throttle.control TO <fixture>, <maintenance>;
GRANT SELECT, UPDATE ON synthetic_throttle.bindings TO <fixture>;
GRANT SELECT, INSERT, UPDATE ON synthetic_throttle.windows TO <fixture>;
GRANT SELECT, UPDATE, DELETE ON synthetic_throttle.windows TO <maintenance>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.valid_window(smallint,bigint[]) TO <fixture>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.reserve_attempt(text,integer,bytea,bytea,text,text,bigint,boolean,boolean,boolean,text) TO <fixture>;
GRANT EXECUTE ON FUNCTION synthetic_throttle.cleanup(bigint,bigint,integer,text,text,text,boolean,boolean) TO <maintenance>;
```

No direct fixture DELETE, TRUNCATE, CREATE, ownership, sequence rights or role
membership is intended. No SECURITY DEFINER or RLS. Effective privileges,
PUBLIC/default ACLs, database/template access, role memberships, all object
ownership and exact function signatures require version-specific independent
verification. The template cannot establish target isolation or its own safe
execution. In particular, an independent bootstrap authority must have a safe
way to act as the NOLOGIN owner without granting fixture or maintenance role
membership; this workflow is not implemented or reviewed. `CREATE DATABASE`
cannot be treated as part of a single atomic transaction with the role and
per-database bootstrap. Record partial creation and refuse automatic retry or
deletion. The maintenance role's UPDATE and DELETE can bypass cleanup policy;
separate credentials and an explicit synthetic-only risk decision are required.
