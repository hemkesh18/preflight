"""
Deterministic generator for Kestrel Pay's 90-day deployment & incident history.
Generates authentic DevOps events, realistic diffs, dynamic incident logs,
planted failure patterns, safe decoys, background incidents, and noisy/safe pattern runs.
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Deterministic random seed
SEED = 42
random.seed(SEED)

SERVICES = [
    "payments-api",
    "ledger-service",
    "auth-service",
    "checkout-web",
    "search-indexer",
    "notification-service",
    "risk-engine",
    "reporting-service",
    "infra-terraform",
]

ENGINEERS = [
    {"name": "Maya Lin", "email": "maya.lin@kestrelpay.internal", "role": "Senior Backend Engineer"},
    {"name": "David Chen", "email": "david.chen@kestrelpay.internal", "role": "Staff Infrastructure Engineer"},
    {"name": "Elena Rostova", "email": "elena.rostova@kestrelpay.internal", "role": "Data Systems Engineer"},
    {"name": "Marcus Brody", "email": "marcus.brody@kestrelpay.internal", "role": "Senior Fullstack Engineer"},
    {"name": "Sarah Jenkins", "email": "sarah.jenkins@kestrelpay.internal", "role": "Security & Auth Engineer"},
    {"name": "Alex Rivera", "email": "alex.rivera@kestrelpay.internal", "role": "Payments Tech Lead"},
    {"name": "Priya Sharma", "email": "priya.sharma@kestrelpay.internal", "role": "Platform / Release Engineer"},
    {"name": "Liam O'Connor", "email": "liam.oconnor@kestrelpay.internal", "role": "Backend Engineer"},
    {"name": "Chloe Bennett", "email": "chloe.bennett@kestrelpay.internal", "role": "Frontend Tech Lead"},
    {"name": "James Wilson", "email": "james.wilson@kestrelpay.internal", "role": "Site Reliability Engineer"},
]

CHANGE_TYPES = ["code", "config", "migration", "dependency-bump", "feature-flag", "infra"]

# 2026-06-01 is a Monday
START_DATE = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)

# Friday Day Offsets: Day 5 (Jun 5), Day 12 (Jun 12), Day 19 (Jun 19), Day 26 (Jun 26),
# Day 33 (Jul 3), Day 40 (Jul 10), Day 47 (Jul 17), Day 54 (Jul 24), Day 61 (Jul 31),
# Day 68 (Aug 7), Day 75 (Aug 14), Day 82 (Aug 21), Day 89 (Aug 28)

PLANTED_PATTERNS = {
    "P1": {
        "name": "Friday-evening payments-api config changes",
        "description": "payments-api config changes deployed on Friday evening (hour >= 16) cause connection pool exhaustion during batch processing.",
        "occurrences": [5, 19, 47, 75], # All strictly Fridays!
        "healthy_override": [75] # Day 75 is a noisy safe run: traffic was routed via canary pool, so it stayed healthy!
    },
    "P2": {
        "name": "ledger-service migration without backfill",
        "description": "ledger-service schema migration omitting column backfill breaks downstream search-indexer and reporting-service.",
        "occurrences": [11, 39, 67], # Thursdays
        "healthy_override": []
    },
    "P3": {
        "name": "auth-service jwt-lib bump breaks checkout",
        "description": "auth-service jwt-lib dependency bump causes clock skew and token verification failures in checkout-web.",
        "occurrences": [16, 44, 72], # Tuesdays
        "healthy_override": []
    },
    "P4": {
        "name": "checkout_v2 flag toggle paired with cache TTL change",
        "description": "Toggling checkout_v2 flag while changing cache TTL causes checkout session state desync and 500 error cascade.",
        "occurrences": [22, 50, 78], # Mondays
        "healthy_override": [78] # Day 78 is a noisy safe run: rolled out to 1% internal test cohort, no customer impact!
    },
    "P5": {
        "name": "Base-image bump breaks CI build",
        "description": "Upgrading base image in Dockerfile introduces incompatible glibc/openssl, failing CI integration suite.",
        "occurrences": [9, 30, 58, 86], # Tuesdays/Fridays
        "healthy_override": []
    },
    "P6": {
        "name": "terraform security-group edit blocks notifications",
        "description": "Terraform security group egress rule change drops outbound SMTP/SES port 587 traffic.",
        "occurrences": [24, 52, 80], # Wednesdays
        "healthy_override": []
    }
}

BACKGROUND_INCIDENTS = [
    {
        "day": 15, # Monday
        "service": "risk-engine",
        "change_type": "code",
        "severity": "SEV-2",
        "title": "risk-engine OOM Crash Loop on Sudden High-Cardinality Payload",
        "root_cause": "An unindexed in-memory merchant reputation cache consumed available heap during a traffic burst from a seasonal merchant promotion.",
        "fix_steps": "Increased JVM heap limit from 2Gi to 4Gi and configured LRU eviction with a maximum size of 50,000 entries.",
        "runbook": "RB-RISK-01: Risk Engine Heap Exhaustion & Cache Eviction"
    },
    {
        "day": 43, # Monday
        "service": "notification-service",
        "change_type": "code",
        "severity": "SEV-2",
        "title": "notification-service Connection Drops to Third-Party SMS Gateway",
        "root_cause": "External SMS aggregator rotated intermediate TLS certificate without root trust bundle inclusion on legacy notification worker instances.",
        "fix_steps": "Injected updated DigiCert Global Root G2 certificate bundle into worker trust store and restarted notification dispatchers.",
        "runbook": "RB-NOTIF-05: Upstream SMS Gateway TLS Handshake Troubleshooting"
    },
    {
        "day": 71, # Monday
        "service": "search-indexer",
        "change_type": "infra",
        "severity": "SEV-2",
        "title": "search-indexer Shard Allocation Rejection on High Disk Watermark",
        "root_cause": "ElasticSearch data node crossed 85% low-watermark threshold, preventing primary shard reallocation after a node replacement.",
        "fix_steps": "Expanded EBS volume from 250GB to 500GB and triggered cluster reroute with retry_failed=true.",
        "runbook": "RB-SEARCH-03: ElasticSearch Storage & Shard Recovery"
    }
]

DECOY_SCHEDULE = {
    4: "payments_thursday_config",       # payments-api config on Thursday morning (healthy)
    12: "friday_other_service",          # Friday deploy to checkout-web code (healthy)
    18: "ledger_migration_backfilled",   # ledger migration WITH backfill (healthy)
    25: "dep_bump_notification",         # requests dependency bump on notification-service (healthy)
    33: "friday_auth_code",              # Friday code change to auth-service (healthy)
    39: "flag_without_cache_ttl",        # checkout_v2 flag toggle WITHOUT cache TTL change (healthy)
    46: "payments_wednesday_config",     # payments-api config on Wednesday afternoon (healthy)
    53: "terraform_iam_update",          # terraform IAM policy update without security groups (healthy)
    61: "friday_reporting_service",      # Friday deploy to reporting-service (healthy)
    68: "ledger_migration_backfilled_2", # second backfilled migration on ledger-service (healthy)
    74: "dep_bump_risk_engine",          # pydantic dependency bump on risk-engine (healthy)
    82: "friday_search_indexer",         # Friday deploy to search-indexer (healthy)
}


def make_realistic_pr_and_diff(service: str, change_type: str, pattern_id: str = None, is_decoy: bool = False, occurrence_idx: int = 0):
    """
    Generates realistic, strictly consistent PR titles, files changed, and code diffs.
    Varies PR titles, diff values, authors and metrics across occurrences of the same pattern.
    """
    if pattern_id == "P1":
        variations = [
            ("fix(payments): update worker buffer thresholds in config",
             ["config/production.yaml", "helm/values-prod.yaml"],
             "--- a/config/production.yaml\n+++ b/config/production.yaml\n@@ -42,6 +42,6 @@\n-  pool_max_connections: 50\n+  pool_max_connections: 15\n-  keepalive_timeout_ms: 3000\n+  keepalive_timeout_ms: 18000\n-  max_overflow: 30\n+  max_overflow: 4"),
            ("perf(payments): tune threadpool and db timeout parameters",
             ["config/database.yaml", "helm/values-prod.yaml"],
             "--- a/config/database.yaml\n+++ b/config/database.yaml\n@@ -38,6 +38,6 @@\n-  pool_max_connections: 55\n+  pool_max_connections: 18\n-  keepalive_timeout_ms: 3500\n+  keepalive_timeout_ms: 16000\n-  max_overflow: 25\n+  max_overflow: 5"),
            ("chore(config): adjust redis retry backoff and pool limits",
             ["config/payments_pool.yaml"],
             "--- a/config/payments_pool.yaml\n+++ b/config/payments_pool.yaml\n@@ -21,6 +21,6 @@\n-  pool_max_connections: 48\n+  pool_max_connections: 16\n-  keepalive_timeout_ms: 2500\n+  keepalive_timeout_ms: 15000\n-  max_overflow: 20\n+  max_overflow: 3"),
            ("chore(payments): refresh downstream gateway connection timeouts with canary",
             ["config/production.yaml"],
             "--- a/config/production.yaml\n+++ b/config/production.yaml\n@@ -42,5 +42,6 @@\n-  pool_max_connections: 50\n+  pool_max_connections: 22\n+  canary_routing_ratio: 0.05")
        ]
        title, files, diff = variations[occurrence_idx % len(variations)]
    elif pattern_id == "P2":
        variations = [
            ("feat(ledger): partition ledger_entries table by currency_code",
             ["migrations/202606_ledger_settlement.sql", "src/models/ledger.py"],
             "--- a/migrations/202606_ledger_settlement.sql\n+++ b/migrations/202606_ledger_settlement.sql\n@@ -15,4 +15,3 @@\n-ALTER TABLE ledger_entries ADD COLUMN settlement_epoch BIGINT;\n+ALTER TABLE ledger_entries DROP COLUMN legacy_settlement_id, ADD COLUMN settlement_epoch BIGINT NOT NULL;"),
            ("refactor(ledger): restructure settlement balance tracking columns",
             ["migrations/202607_ledger_rebalance.sql", "src/models/settlement.py"],
             "--- a/migrations/202607_ledger_rebalance.sql\n+++ b/migrations/202607_ledger_rebalance.sql\n@@ -22,4 +22,3 @@\n-ALTER TABLE ledger_entries RENAME COLUMN legacy_settlement_id TO archived_id;\n+ALTER TABLE ledger_entries DROP COLUMN legacy_settlement_id;"),
            ("feat(ledger): optimize transaction ledger storage layout",
             ["migrations/202608_ledger_compact.sql", "src/models/journal.py"],
             "--- a/migrations/202608_ledger_compact.sql\n+++ b/migrations/202608_ledger_compact.sql\n@@ -10,3 +10,2 @@\n-ALTER TABLE ledger_entries ADD COLUMN compact_ref VARCHAR(32);\n+ALTER TABLE ledger_entries DROP COLUMN legacy_settlement_id;")
        ]
        title, files, diff = variations[occurrence_idx % len(variations)]
    elif pattern_id == "P3":
        variations = [
            ("chore(deps): bump pyjwt and cryptography to latest minor",
             ["requirements.txt", "Pipfile.lock"],
             "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -12,4 +12,4 @@\n-pyjwt==2.8.0\n+pyjwt==2.10.1\n-cryptography==42.0.5\n+cryptography==43.0.1"),
            ("chore(security): upgrade core auth token handling packages",
             ["requirements.txt"],
             "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -12,3 +12,3 @@\n-pyjwt==2.8.0\n+pyjwt==2.10.0"),
            ("chore(deps): update security libraries and token verifier",
             ["pyproject.toml", "poetry.lock"],
             "--- a/pyproject.toml\n+++ b/pyproject.toml\n@@ -28,2 +28,2 @@\n-pyjwt = \"^2.8.0\"\n+pyjwt = \"^2.10.1\"")
        ]
        title, files, diff = variations[occurrence_idx % len(variations)]
    elif pattern_id == "P4":
        variations = [
            ("feat(checkout): activate checkout_v2 cohort with session caching",
             ["config/features.json", "src/services/session_cache.ts"],
             "--- a/config/features.json\n+++ b/config/features.json\n@@ -8,4 +8,4 @@\n-  \"checkout_v2\": false,\n+  \"checkout_v2\": true,\n-  \"session_cache_ttl_sec\": 3600\n+  \"session_cache_ttl_sec\": 60"),
            ("chore(release): flip experiment cohort and tune caching",
             ["config/features.json", "src/middleware/session.ts"],
             "--- a/config/features.json\n+++ b/config/features.json\n@@ -8,4 +8,4 @@\n-  \"checkout_v2\": false,\n+  \"checkout_v2\": true,\n-  \"session_cache_ttl_sec\": 1800\n+  \"session_cache_ttl_sec\": 45"),
            ("feat(checkout): prepare rollout phase for payment sheet",
             ["config/features.json"],
             "--- a/config/features.json\n+++ b/config/features.json\n@@ -8,4 +8,4 @@\n-  \"checkout_v2\": false,\n+  \"checkout_v2\": true,\n-  \"session_cache_ttl_sec\": 3600\n+  \"session_cache_ttl_sec\": 90")
        ]
        title, files, diff = variations[occurrence_idx % len(variations)]
    elif pattern_id == "P5":
        variations = [
            ("chore(ci): update container base image in build pipeline",
             ["Dockerfile", ".github/workflows/ci.yml"],
             "--- a/Dockerfile\n+++ b/Dockerfile\n@@ -1,4 +1,4 @@\n-FROM python:3.11.8-slim-bookworm\n+FROM python:3.12.3-slim-bookworm\n-RUN apt-get install -y libpq-dev\n+RUN apt-get install -y --no-install-recommends libpq-dev"),
            ("chore(docker): bump python base image for security patches",
             ["Dockerfile"],
             "--- a/Dockerfile\n+++ b/Dockerfile\n@@ -1,2 +1,2 @@\n-FROM python:3.11-alpine3.18\n+FROM python:3.12-alpine3.20"),
            ("chore(docker): refresh debian slim base image to v12.6",
             ["Dockerfile"],
             "--- a/Dockerfile\n+++ b/Dockerfile\n@@ -1,2 +1,2 @@\n-FROM debian:12.4-slim\n+FROM debian:12.6-slim"),
            ("build(docker): bump alpine base runner for lighter container",
             ["Dockerfile"],
             "--- a/Dockerfile\n+++ b/Dockerfile\n@@ -1,2 +1,2 @@\n-FROM alpine:3.18\n+FROM alpine:3.20")
        ]
        title, files, diff = variations[occurrence_idx % len(variations)]
    elif pattern_id == "P6":
        variations = [
            ("infra(network): tighten vpc egress firewall rules",
             ["terraform/modules/vpc/security_groups.tf", "terraform/environments/prod/main.tf"],
             "--- a/terraform/modules/vpc/security_groups.tf\n+++ b/terraform/modules/vpc/security_groups.tf\n@@ -28,4 +28,4 @@\n-  egress { from_port = 0, to_port = 0, protocol = '-1', cidr_blocks = ['0.0.0.0/0'] }\n+  egress { from_port = 443, to_port = 443, protocol = 'tcp', cidr_blocks = ['0.0.0.0/0'] }"),
            ("infra(terraform): consolidate default security groups across vpc",
             ["terraform/modules/vpc/security_groups.tf"],
             "--- a/terraform/modules/vpc/security_groups.tf\n+++ b/terraform/modules/vpc/security_groups.tf\n@@ -35,3 +35,3 @@\n-  egress { from_port = 0, to_port = 0, protocol = '-1', cidr_blocks = ['0.0.0.0/0'] }\n+  egress { from_port = 443, to_port = 443, protocol = 'tcp', cidr_blocks = ['10.0.0.0/8'] }"),
            ("infra(secops): apply least-privilege outbound rule matrix",
             ["terraform/modules/vpc/security_groups.tf"],
             "--- a/terraform/modules/vpc/security_groups.tf\n+++ b/terraform/modules/vpc/security_groups.tf\n@@ -40,4 +40,3 @@\n-  egress { from_port = 0, to_port = 65535, protocol = 'tcp', cidr_blocks = ['0.0.0.0/0'] }\n+  egress { from_port = 443, to_port = 443, protocol = 'tcp', cidr_blocks = ['0.0.0.0/0'] }")
        ]
        title, files, diff = variations[occurrence_idx % len(variations)]
    elif is_decoy:
        if service == "payments-api" and change_type == "config":
            title = "chore(config): adjust payments api rate limiter buckets"
            files = ["config/payments.yaml"]
            diff = (
                "--- a/config/payments.yaml\n"
                "+++ b/config/payments.yaml\n"
                "@@ -18,2 +18,2 @@\n"
                "-  rate_limit_burst: 200\n"
                "+  rate_limit_burst: 250"
            )
        elif service == "ledger-service" and change_type == "migration":
            title = "feat(ledger): add index and backfilled audit column"
            files = ["migrations/202607_backfill_audit.sql"]
            diff = (
                "--- a/migrations/202607_backfill_audit.sql\n"
                "+++ b/migrations/202607_backfill_audit.sql\n"
                "@@ -1,2 +1,3 @@\n"
                "+ALTER TABLE ledger_entries ADD COLUMN audit_hash VARCHAR(64) DEFAULT '';\n"
                "+UPDATE ledger_entries SET audit_hash = md5(id::text) WHERE audit_hash = '';"
            )
        elif service == "checkout-web" and change_type == "feature-flag":
            title = "feat(checkout): toggle checkout_v2 beta cohort"
            files = ["config/features.json"]
            diff = (
                "--- a/config/features.json\n"
                "+++ b/config/features.json\n"
                "@@ -8,2 +8,2 @@\n"
                "-  \"checkout_v2\": false\n"
                "+  \"checkout_v2\": true"
            )
        elif service == "infra-terraform":
            title = "infra(iam): update reporting s3 bucket read policy"
            files = ["terraform/modules/iam/reporting.tf"]
            diff = (
                "--- a/terraform/modules/iam/reporting.tf\n"
                "+++ b/terraform/modules/iam/reporting.tf\n"
                "@@ -14,2 +14,3 @@\n"
                "+  actions = ['s3:GetObject', 's3:ListBucket']"
            )
        else:
            title = f"fix({service}): tighten input validation in request handler"
            files = [f"src/{service.replace('-', '_')}/validator.py"]
            diff = (
                f"--- a/src/{service.replace('-', '_')}/validator.py\n"
                f"+++ b/src/{service.replace('-', '_')}/validator.py\n"
                "@@ -10,2 +10,2 @@\n"
                "-  if len(payload) > 50000:\n"
                "+  if len(payload) > 25000:"
            )
    else:
        # Realistic tailored templates per service and change type
        service_templates = {
            "payments-api": {
                "code": ("fix(payments): handle edge case in stripe webhook idempotency",
                         ["src/payments_api/webhook.py"],
                         "--- a/src/payments_api/webhook.py\n+++ b/src/payments_api/webhook.py\n@@ -34,2 +34,4 @@\n+  if redis.exists(idempotency_key):\n+    return Response(status_code=200)"),
                "config": ("chore(config): update datadog apm trace sample rate",
                           ["config/datadog.yaml"],
                           "--- a/config/datadog.yaml\n+++ b/config/datadog.yaml\n@@ -5,2 +5,2 @@\n-  sample_rate: 0.1\n+  sample_rate: 0.25"),
                "migration": ("feat(db): add index on payments_transactions(created_at, status)",
                              ["migrations/2026_pay_idx.sql"],
                              "--- a/migrations/2026_pay_idx.sql\n+++ b/migrations/2026_pay_idx.sql\n@@ -0,0 +1,2 @@\n+CREATE INDEX CONCURRENTLY idx_pay_created_status ON payments_transactions(created_at, status);"),
                "dependency-bump": ("chore(deps): bump requests to 2.32.3",
                                    ["requirements.txt"],
                                    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -8,2 +8,2 @@\n-requests==2.31.0\n+requests==2.32.3"),
                "feature-flag": ("feat(flags): enable apple_pay_direct_checkout cohort",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -12,2 +12,2 @@\n-  \"apple_pay\": false\n+  \"apple_pay\": true"),
                "infra": ("infra(k8s): adjust payments-api deployment resource limits",
                          ["k8s/payments-deployment.yaml"],
                          "--- a/k8s/payments-deployment.yaml\n+++ b/k8s/payments-deployment.yaml\n@@ -22,2 +22,2 @@\n-  cpu: '500m'\n+  cpu: '1000m'")
            },
            "ledger-service": {
                "code": ("feat(ledger): enforce debit-credit sum invariant on journal batches",
                         ["src/ledger/journal.py"],
                         "--- a/src/ledger/journal.py\n+++ b/src/ledger/journal.py\n@@ -45,2 +45,4 @@\n+  if sum(entry.amount for entry in batch) != 0:\n+    raise UnbalancedJournalError()"),
                "config": ("chore(config): tune ledger batch sync commit interval",
                           ["config/ledger.yaml"],
                           "--- a/config/ledger.yaml\n+++ b/config/ledger.yaml\n@@ -10,2 +10,2 @@\n-  sync_interval_ms: 500\n+  sync_interval_ms: 250"),
                "migration": ("feat(db): archive ledger reconciliation entries older than 365 days",
                              ["migrations/2026_archive.sql"],
                              "--- a/migrations/2026_archive.sql\n+++ b/migrations/2026_archive.sql\n@@ -0,0 +1,2 @@\n+CREATE TABLE ledger_archive PARTITION OF ledger_entries FOR VALUES FROM ('2025-01-01') TO ('2025-12-31');"),
                "dependency-bump": ("chore(deps): upgrade psycopg2-binary to 2.9.9",
                                    ["requirements.txt"],
                                    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -4,2 +4,2 @@\n-psycopg2-binary==2.9.7\n+psycopg2-binary==2.9.9"),
                "feature-flag": ("feat(flags): enable multicurrency_settlement_preview",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -15,2 +15,2 @@\n-  \"multicurrency\": false\n+  \"multicurrency\": true"),
                "infra": ("infra(k8s): set ledger-service horizontal pod autoscaler min replicas to 3",
                          ["k8s/ledger-hpa.yaml"],
                          "--- a/k8s/ledger-hpa.yaml\n+++ b/k8s/ledger-hpa.yaml\n@@ -12,2 +12,2 @@\n-  minReplicas: 2\n+  minReplicas: 3")
            },
            "auth-service": {
                "code": ("fix(auth): sanitize redirect uri against open-redirect vulnerabilities",
                         ["src/auth/oauth.py"],
                         "--- a/src/auth/oauth.py\n+++ b/src/auth/oauth.py\n@@ -19,2 +19,4 @@\n+  if not is_allowed_domain(redirect_uri):\n+    raise InvalidRedirectUriError()"),
                "config": ("chore(config): decrease session token expiration from 8h to 4h",
                           ["config/auth.yaml"],
                           "--- a/config/auth.yaml\n+++ b/config/auth.yaml\n@@ -7,2 +7,2 @@\n-  token_ttl_hours: 8\n+  token_ttl_hours: 4"),
                "migration": ("feat(db): add unique constraint on oauth_accounts(provider, provider_user_id)",
                              ["migrations/2026_auth_constraints.sql"],
                              "--- a/migrations/2026_auth_constraints.sql\n+++ b/migrations/2026_auth_constraints.sql\n@@ -0,0 +1,2 @@\n+ALTER TABLE oauth_accounts ADD CONSTRAINT uq_provider_user UNIQUE (provider, provider_user_id);"),
                "dependency-bump": ("chore(deps): bump bcrypt from 4.1.2 to 4.1.3",
                                    ["requirements.txt"],
                                    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -15,2 +15,2 @@\n-bcrypt==4.1.2\n+bcrypt==4.1.3"),
                "feature-flag": ("feat(flags): roll out passkey_authentication_beta",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -20,2 +20,2 @@\n-  \"passkeys\": false\n+  \"passkeys\": true"),
                "infra": ("infra(k8s): configure ingress tls cert-manager issuer for auth",
                          ["k8s/auth-ingress.yaml"],
                          "--- a/k8s/auth-ingress.yaml\n+++ b/k8s/auth-ingress.yaml\n@@ -10,2 +10,2 @@\n-  cert-manager.io/cluster-issuer: 'letsencrypt-staging'\n+  cert-manager.io/cluster-issuer: 'letsencrypt-prod'")
            },
            "checkout-web": {
                "code": ("fix(checkout): prevent duplicate card submit clicks with debouncing",
                         ["src/components/CheckoutButton.tsx"],
                         "--- a/src/components/CheckoutButton.tsx\n+++ b/src/components/CheckoutButton.tsx\n@@ -24,2 +24,3 @@\n+  const [isSubmitting, setIsSubmitting] = useState(false);\n+  if (isSubmitting) return;"),
                "config": ("chore(config): point analytics collector endpoint to prod ingress",
                           ["config/env.production.ts"],
                           "--- a/config/env.production.ts\n+++ b/config/env.production.ts\n@@ -3,2 +3,2 @@\n-  ANALYTICS_URL: 'https://telemetry-stage.kestrelpay.internal'\n+  ANALYTICS_URL: 'https://telemetry.kestrelpay.internal'"),
                "migration": ("feat(db): add local storage schema migration for saved payment methods",
                              ["src/utils/storageMigration.ts"],
                              "--- a/src/utils/storageMigration.ts\n+++ b/src/utils/storageMigration.ts\n@@ -12,2 +12,4 @@\n+  localStorage.setItem('checkout_storage_v2', 'true');"),
                "dependency-bump": ("chore(deps): bump react-query from 5.28.0 to 5.35.1",
                                    ["package.json"],
                                    "--- a/package.json\n+++ b/package.json\n@@ -31,2 +31,2 @@\n-  \"@tanstack/react-query\": \"^5.28.0\"\n+  \"@tanstack/react-query\": \"^5.35.1\""),
                "feature-flag": ("feat(flags): toggle instant_bank_pay_button",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -5,2 +5,2 @@\n-  \"instant_bank_pay\": false\n+  \"instant_bank_pay\": true"),
                "infra": ("infra(cdn): adjust cloudfront cache ttl for static checkout assets",
                          ["terraform/modules/cdn/checkout.tf"],
                          "--- a/terraform/modules/cdn/checkout.tf\n+++ b/terraform/modules/cdn/checkout.tf\n@@ -15,2 +15,2 @@\n-  default_ttl = 86400\n+  default_ttl = 3600")
            },
            "search-indexer": {
                "code": ("feat(search): batch merchant search index updates into 500-item chunks",
                         ["src/indexer/bulk_writer.py"],
                         "--- a/src/indexer/bulk_writer.py\n+++ b/src/indexer/bulk_writer.py\n@@ -18,2 +18,3 @@\n+  for chunk in chunks(records, size=500):\n+    es.bulk(chunk)"),
                "config": ("chore(config): set elasticsearch connection retry backoff to 2000ms",
                           ["config/elasticsearch.yaml"],
                           "--- a/config/elasticsearch.yaml\n+++ b/config/elasticsearch.yaml\n@@ -8,2 +8,2 @@\n-  retry_backoff_ms: 1000\n+  retry_backoff_ms: 2000"),
                "migration": ("feat(db): create elasticsearch index template for 2026 transaction mapping",
                              ["mappings/transactions_2026.json"],
                              "--- a/mappings/transactions_2026.json\n+++ b/mappings/transactions_2026.json\n@@ -0,0 +1,3 @@\n+{ \"mappings\": { \"properties\": { \"settlement_status\": { \"type\": \"keyword\" } } } }"),
                "dependency-bump": ("chore(deps): bump elasticsearch python client from 8.12.0 to 8.13.0",
                                    ["requirements.txt"],
                                    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -6,2 +6,2 @@\n-elasticsearch==8.12.0\n+elasticsearch==8.13.0"),
                "feature-flag": ("feat(flags): enable phonetic_merchant_search_indexer",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -9,2 +9,2 @@\n-  \"phonetic_search\": false\n+  \"phonetic_search\": true"),
                "infra": ("infra(k8s): allocate dedicated node affinity for search-indexer workers",
                          ["k8s/search-indexer-deployment.yaml"],
                          "--- a/k8s/search-indexer-deployment.yaml\n+++ b/k8s/search-indexer-deployment.yaml\n@@ -14,2 +14,4 @@\n+  affinity:\n+    nodeAffinity: { requiredDuringSchedulingIgnoredDuringExecution: { ... } }")
            },
            "notification-service": {
                "code": ("fix(notifications): handle dead-letter queue re-drive on invalid phone format",
                         ["src/notifications/sms.py"],
                         "--- a/src/notifications/sms.py\n+++ b/src/notifications/sms.py\n@@ -28,2 +28,4 @@\n+  if not is_valid_e164(phone):\n+    dlq.publish(msg, reason='INVALID_E164')"),
                "config": ("chore(config): adjust twilio dispatch rate limit to 80 rps",
                           ["config/sms.yaml"],
                           "--- a/config/sms.yaml\n+++ b/config/sms.yaml\n@@ -4,2 +4,2 @@\n-  dispatch_rate_limit: 50\n+  dispatch_rate_limit: 80"),
                "migration": ("feat(db): partition notification_audit_log by month",
                              ["migrations/2026_notification_partition.sql"],
                              "--- a/migrations/2026_notification_partition.sql\n+++ b/migrations/2026_notification_partition.sql\n@@ -0,0 +1,2 @@\n+CREATE TABLE notification_log_2026_06 PARTITION OF notification_audit_log FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');"),
                "dependency-bump": ("chore(deps): bump twilio python sdk from 9.0.0 to 9.0.4",
                                    ["requirements.txt"],
                                    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -9,2 +9,2 @@\n-twilio==9.0.0\n+twilio==9.0.4"),
                "feature-flag": ("feat(flags): enable whatsapp_business_notifications_cohort",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -14,2 +14,2 @@\n-  \"whatsapp_enabled\": false\n+  \"whatsapp_enabled\": true"),
                "infra": ("infra(k8s): add pod disruption budget for notification-service",
                          ["k8s/notification-pdb.yaml"],
                          "--- a/k8s/notification-pdb.yaml\n+++ b/k8s/notification-pdb.yaml\n@@ -0,0 +1,4 @@\n+apiVersion: policy/v1\n+kind: PodDisruptionBudget\n+spec:\n+  minAvailable: 2")
            },
            "risk-engine": {
                "code": ("feat(risk): add geo-velocity check for cross-border card transactions",
                         ["src/risk/velocity.py"],
                         "--- a/src/risk/velocity.py\n+++ b/src/risk/velocity.py\n@@ -19,2 +19,4 @@\n+  if calculate_speed_kmh(prev_tx, curr_tx) > 900:\n+    return RiskScore.HIGH"),
                "config": ("chore(config): adjust fraud threshold score from 85 to 82",
                           ["config/risk_rules.yaml"],
                           "--- a/config/risk_rules.yaml\n+++ b/config/risk_rules.yaml\n@@ -6,2 +6,2 @@\n-  fraud_cutoff_score: 85\n+  fraud_cutoff_score: 82"),
                "migration": ("feat(db): add gin index on merchant_risk_profiles(risk_tags)",
                              ["migrations/2026_risk_tags.sql"],
                              "--- a/migrations/2026_risk_tags.sql\n+++ b/migrations/2026_risk_tags.sql\n@@ -0,0 +1,2 @@\n+CREATE INDEX idx_merchant_risk_tags ON merchant_risk_profiles USING gin(risk_tags);"),
                "dependency-bump": ("chore(deps): upgrade numpy from 1.26.4 to 2.0.0",
                                    ["requirements.txt"],
                                    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -11,2 +11,2 @@\n-numpy==1.26.4\n+numpy==2.0.0"),
                "feature-flag": ("feat(flags): enable realtime_device_fingerprinting_model",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -17,2 +17,2 @@\n-  \"device_fingerprint_v2\": false\n+  \"device_fingerprint_v2\": true"),
                "infra": ("infra(k8s): scale risk-engine deployment cpu request to 2000m",
                          ["k8s/risk-engine-deployment.yaml"],
                          "--- a/k8s/risk-engine-deployment.yaml\n+++ b/k8s/risk-engine-deployment.yaml\n@@ -18,2 +18,2 @@\n-  cpu: '1500m'\n+  cpu: '2000m'")
            },
            "reporting-service": {
                "code": ("fix(reports): handle daylight savings shift in daily settlement rollup",
                         ["src/reports/settlement.py"],
                         "--- a/src/reports/settlement.py\n+++ b/src/reports/settlement.py\n@@ -22,2 +22,3 @@\n+  dt_start = dt_start.astimezone(timezone.utc)\n+  dt_end = dt_end.astimezone(timezone.utc)"),
                "config": ("chore(config): shift daily reporting cron from 02:00 UTC to 03:00 UTC",
                           ["config/schedule.yaml"],
                           "--- a/config/schedule.yaml\n+++ b/config/schedule.yaml\n@@ -3,2 +3,2 @@\n-  daily_report_cron: '0 2 * * *'\n+  daily_report_cron: '0 3 * * *'"),
                "migration": ("feat(db): create materialized view for quarterly merchant tax summaries",
                              ["migrations/2026_merchant_tax_mv.sql"],
                              "--- a/migrations/2026_merchant_tax_mv.sql\n+++ b/migrations/2026_merchant_tax_mv.sql\n@@ -0,0 +1,3 @@\n+CREATE MATERIALIZED VIEW mv_merchant_tax_summary AS\n+SELECT merchant_id, date_trunc('quarter', created_at), sum(tax_amount) FROM transactions GROUP BY 1, 2;"),
                "dependency-bump": ("chore(deps): bump pandas from 2.2.1 to 2.2.2",
                                    ["requirements.txt"],
                                    "--- a/requirements.txt\n+++ b/requirements.txt\n@@ -7,2 +7,2 @@\n-pandas==2.2.1\n+pandas==2.2.2"),
                "feature-flag": ("feat(flags): enable pdf_statement_generator_v2",
                                 ["config/flags.json"],
                                 "--- a/config/flags.json\n+++ b/config/flags.json\n@@ -11,2 +11,2 @@\n-  \"pdf_engine_v2\": false\n+  \"pdf_engine_v2\": true"),
                "infra": ("infra(k8s): assign reporting-service batch job to spot instances",
                          ["k8s/reporting-cronjob.yaml"],
                          "--- a/k8s/reporting-cronjob.yaml\n+++ b/k8s/reporting-cronjob.yaml\n@@ -25,2 +25,3 @@\n+  nodeSelector:\n+    karpenter.sh/capacity-type: 'spot'")
            },
            "infra-terraform": {
                "code": ("feat(terraform): add automated tag propagation for aws resources",
                         ["terraform/modules/tags/main.tf"],
                         "--- a/terraform/modules/tags/main.tf\n+++ b/terraform/modules/tags/main.tf\n@@ -8,2 +8,4 @@\n+  default_tags {\n+    tags = { Environment = var.env, ManagedBy = \"Terraform\" }\n+  }"),
                "config": ("chore(terraform): update remote s3 backend lock timeout to 20m",
                           ["terraform/backend.tf"],
                           "--- a/terraform/backend.tf\n+++ b/terraform/backend.tf\n@@ -5,2 +5,2 @@\n-  lock_timeout = \"10m\"\n+  lock_timeout = \"20m\""),
                "migration": ("infra(terraform): import existing nat gateway resources into state",
                              ["terraform/modules/vpc/imports.tf"],
                              "--- a/terraform/modules/vpc/imports.tf\n+++ b/terraform/modules/vpc/imports.tf\n@@ -0,0 +1,2 @@\n+import { to = aws_nat_gateway.main, id = \"nat-08a9bc72d1\" }"),
                "dependency-bump": ("chore(deps): upgrade terraform aws provider from 5.48.0 to 5.50.0",
                                    ["terraform/versions.tf"],
                                    "--- a/terraform/versions.tf\n+++ b/terraform/versions.tf\n@@ -4,2 +4,2 @@\n-    aws = { source = \"hashicorp/aws\", version = \"~> 5.48.0\" }\n+    aws = { source = \"hashicorp/aws\", version = \"~> 5.50.0\" }"),
                "feature-flag": ("feat(flags): enable terraform cloud remote execution for staging",
                                 ["terraform/cloud.tf"],
                                 "--- a/terraform/cloud.tf\n+++ b/terraform/cloud.tf\n@@ -8,2 +8,2 @@\n-  execution_mode = \"local\"\n+  execution_mode = \"remote\""),
                "infra": ("infra(rds): enable performance insights on production aurora cluster",
                          ["terraform/modules/rds/main.tf"],
                          "--- a/terraform/modules/rds/main.tf\n+++ b/terraform/modules/rds/main.tf\n@@ -34,2 +34,3 @@\n+  performance_insights_enabled = true\n+  performance_insights_retention_period = 7")
            }
        }
        item = service_templates.get(service, {}).get(change_type)
        if item:
            title, files, diff = item
        else:
            title = f"fix({service}): tighten input validation and exception handling"
            files = [f"src/{service.replace('-', '_')}/core.py"]
            diff = f"--- a/src/{service.replace('-', '_')}/core.py\n+++ b/src/{service.replace('-', '_')}/core.py\n@@ -15,2 +15,4 @@\n+  if not data:\n+    return None"

    return title, diff, files


def make_dynamic_incident(deploy_time: datetime, service: str, pattern_id: str = None, bg_incident: dict = None, occurrence_idx: int = 0):
    """
    Constructs an authentic incident record where log timestamps fall STRICTLY
    between deploy_time and detected_at, with MTTR matching impact duration exactly.
    Parameters match the specific PR diff variation of that occurrence.
    """
    delay_min = random.randint(18, 65)
    det_time = deploy_time + timedelta(minutes=delay_min)
    mttr_min = random.randint(35, 95)
    res_time = det_time + timedelta(minutes=mttr_min)

    # Dynamic log timestamps strictly between deploy_time and det_time
    log_t1 = deploy_time + timedelta(minutes=random.randint(5, delay_min // 2))
    log_t2 = deploy_time + timedelta(minutes=random.randint(delay_min // 2 + 1, delay_min - 2))
    log_t3 = det_time - timedelta(minutes=1)

    t1_str = log_t1.strftime("%Y-%m-%d %H:%M:%S")
    t2_str = log_t2.strftime("%Y-%m-%d %H:%M:%S")
    t3_str = log_t3.strftime("%Y-%m-%d %H:%M:%S")
    det_date_str = det_time.strftime("%Y-%m-%d")

    if pattern_id == "P1":
        p1_params = [
            {"orig_pool": 50, "reduced_pool": 15, "orig_timeout": 3000, "new_timeout": 18000, "5xx": "16.4%", "p99": 6420},
            {"orig_pool": 55, "reduced_pool": 18, "orig_timeout": 3500, "new_timeout": 16000, "5xx": "19.2%", "p99": 7150},
            {"orig_pool": 48, "reduced_pool": 16, "orig_timeout": 2500, "new_timeout": 15000, "5xx": "17.8%", "p99": 6680},
        ]
        params = p1_params[occurrence_idx % len(p1_params)]
        orig_p = params["orig_pool"]
        red_p = params["reduced_pool"]
        orig_t = params["orig_timeout"]
        new_t = params["new_timeout"]

        return {
            "severity": "SEV-1",
            "title": f"payments-api Connection Pool Starvation and Spike in 504 Gateway Timeouts ({det_date_str})",
            "detected_at": det_time.isoformat(),
            "resolved_at": res_time.isoformat(),
            "mttr_minutes": mttr_min,
            "impact": f"Payment processing halted for {mttr_min} minutes; {random.randint(900, 1600)} checkout attempts failed with HTTP 504; p99 latency spiked to {params['p99']}ms.",
            "metrics": {
                "http_5xx_rate": params["5xx"],
                "p99_latency_ms": params["p99"],
                "error_budget_burn": f"{random.randint(35, 48)}%",
                "affected_rps": random.randint(280, 360)
            },
            "error_logs": [
                f"ERROR {t1_str} payments-api.pool: sqlalchemy.exc.TimeoutError: QueuePool limit of size {red_p} overflow 5 reached, connection timed out, timeout {new_t/1000:.2f}",
                f"FATAL {t2_str} payments-api.gateway: [CheckoutGate] upstream payments-api worker exhausted, returning HTTP 504",
                f"WARN  {t3_str} payments-api.health: liveness probe failed: HTTP 503 connection refused"
            ],
            "root_cause": f"Friday evening batch settlement traffic on {det_date_str} coincided with reduced pool_max_connections (decreased from {orig_p} to {red_p}) and high keepalive_timeout_ms ({new_t}ms), preventing worker connections from recycling.",
            "fix_steps": f"Reverted pool_max_connections to {orig_p}, decreased keepalive timeout to {orig_t}ms, and performed rolling restart of payments-api pods.",
            "runbook": "RB-PAY-04: Database Connection Pool Exhaustion & Recovery"
        }
    elif pattern_id == "P2":
        return {
            "severity": "SEV-1",
            "title": f"search-indexer and reporting-service Crash Loop on Dropped Ledger Column ({det_date_str})",
            "detected_at": det_time.isoformat(),
            "resolved_at": res_time.isoformat(),
            "mttr_minutes": mttr_min,
            "impact": f"Merchant transaction search offline for {mttr_min} minutes; overnight reporting pipeline halted; 12,000 ledger events queued in Kafka DLQ.",
            "metrics": {
                "http_5xx_rate": "12.1%",
                "p99_latency_ms": 4250,
                "error_budget_burn": "28%",
                "affected_rps": 180
            },
            "error_logs": [
                f"CRITICAL {t1_str} search-indexer.consumer: KeyError: 'legacy_settlement_id' missing from CDC event payload",
                f"ERROR {t2_str} reporting-service.pipeline: psycopg2.errors.UndefinedColumn: column ledger_entries.legacy_settlement_id does not exist",
                f"FATAL {t3_str} search-indexer: ConsumerGroupOffsetExpiredException: max retry limit exceeded on topic ledger.events"
            ],
            "root_cause": f"Destructive schema migration in ledger-service on {det_date_str} dropped legacy_settlement_id immediately without a multi-phase deprecation or backfill phase, crashing downstream consumers.",
            "fix_steps": "Executed hotfix migration adding back legacy_settlement_id as a generated column aliased to settlement_epoch, resumed Kafka consumer offsets.",
            "runbook": "RB-DB-02: Zero-Downtime Schema Evolution & Consumer Recovery"
        }
    elif pattern_id == "P3":
        return {
            "severity": "SEV-2",
            "title": f"checkout-web HTTP 401 Unauthorized Spike Following Auth JWT Upgrade ({det_date_str})",
            "detected_at": det_time.isoformat(),
            "resolved_at": res_time.isoformat(),
            "mttr_minutes": mttr_min,
            "impact": f"Valid logged-in users rejected at checkout page with 'Session Expired' for {mttr_min} minutes; {random.randint(2500, 4200)} checkout abandonments.",
            "metrics": {
                "http_5xx_rate": "1.2%",
                "http_401_rate": "34.7%",
                "p99_latency_ms": 840,
                "error_budget_burn": "19%",
                "affected_rps": 410
            },
            "error_logs": [
                f"WARN  {t1_str} checkout-web.auth: jwt.exceptions.InvalidAlgorithmError: The specified alg 'RS256' requires strict key format validation in pyjwt>=2.10",
                f"ERROR {t2_str} checkout-web.session: Failed to decode user session token from Authorization header: verification failed",
                f"INFO  {t3_str} auth-service: Rejected token issue: clock skew tolerance exceeded (0s threshold)"
            ],
            "root_cause": f"auth-service pyjwt dependency upgrade on {det_date_str} enforced strict asymmetric key formatting and zero leeway on clock skew, rejecting valid JWT tokens issued by older client instances.",
            "fix_steps": "Configured jwt.decode leeway=10s and aligned public key PEM header formatting; rolled back auth-service to pyjwt 2.8.0 pending client rollout.",
            "runbook": "RB-SEC-09: JWT Token Invalidation & Algorithm Rotation"
        }
    elif pattern_id == "P4":
        return {
            "severity": "SEV-1",
            "title": f"checkout-web Cart State Desync and Payment Submission 500 Cascade ({det_date_str})",
            "detected_at": det_time.isoformat(),
            "resolved_at": res_time.isoformat(),
            "mttr_minutes": mttr_min,
            "impact": f"Cart checkout broken for {mttr_min} minutes; users charged twice or seeing empty carts on payment confirmation; gateway double-submission alerts triggered.",
            "metrics": {
                "http_5xx_rate": "24.6%",
                "p99_latency_ms": 5400,
                "error_budget_burn": "38%",
                "affected_rps": 560
            },
            "error_logs": [
                f"ERROR {t1_str} checkout-web.session: CartSessionMismatchError: active cart session expired while payment confirmation pending",
                f"FATAL {t2_str} payments-api.intent: Duplicate payment idempotency key with mismatching payload hash",
                f"ERROR {t3_str} checkout-web.frontend: Uncaught (in promise) Error: HTTP 500 Internal Server Error at CheckoutContainer.tsx:142"
            ],
            "root_cause": f"Simultaneous activation of checkout_v2 feature flag and reduction of session cache TTL from 3600s to 60s on {det_date_str} caused cart sessions to vanish midway through 3D-Secure payment handoffs.",
            "fix_steps": "Restored session_cache_ttl_sec to 3600, disabled checkout_v2 feature flag, executed automated refund reconciliation script.",
            "runbook": "RB-FE-01: Feature Flag Rollback & Stale State Eviction"
        }
    elif pattern_id == "P6":
        return {
            "severity": "SEV-2",
            "title": f"notification-service Egress Timeout & Queue Overflow on Blocked Port 587 ({det_date_str})",
            "detected_at": det_time.isoformat(),
            "resolved_at": res_time.isoformat(),
            "mttr_minutes": mttr_min,
            "impact": f"Payment confirmation receipts, 2FA OTP codes, and fraud alerts delayed by up to {mttr_min} minutes.",
            "metrics": {
                "http_5xx_rate": "8.9%",
                "p99_latency_ms": 3100,
                "error_budget_burn": "15%",
                "affected_rps": 120
            },
            "error_logs": [
                f"ERROR {t1_str} notification-service.mailer: OSError: [Errno 110] Connection timed out while connecting to email-smtp.us-east-1.amazonaws.com:587",
                f"WARN  {t2_str} notification-service.queue: Redis queue 'email_notifications' exceeded 25,000 pending items",
                f"ERROR {t3_str} notification-service.worker: MaxRetryError: SQS message failed 5 times, sending to dead_letter_queue"
            ],
            "root_cause": f"Terraform security group update on {det_date_str} tightened default egress to port 443 only, inadvertently dropping outbound TCP traffic on port 587 needed by notification-service.",
            "fix_steps": "Added explicit egress rule in terraform security_groups.tf allowing outbound TCP port 587 to AWS SES CIDR ranges; ran terraform apply and flushed delayed queue.",
            "runbook": "RB-INFRA-07: VPC Security Group & Egress Connectivity Troubleshooting"
        }
    elif bg_incident:
        return {
            "severity": bg_incident["severity"],
            "title": f"{bg_incident['title']} ({det_date_str})",
            "detected_at": det_time.isoformat(),
            "resolved_at": res_time.isoformat(),
            "mttr_minutes": mttr_min,
            "impact": f"{service} operational degradation for {mttr_min} minutes; background incident unrelated to CI/CD pipeline pattern.",
            "metrics": {
                "http_5xx_rate": "6.5%",
                "p99_latency_ms": 2800,
                "error_budget_burn": "11%",
                "affected_rps": 95
            },
            "error_logs": [
                f"WARN  {t1_str} {service}.monitor: Resource threshold exceeded warning on cluster worker node",
                f"ERROR {t2_str} {service}.core: Unexpected runtime failure: {bg_incident['title']}",
                f"FATAL {t3_str} {service}.supervisor: Worker heartbeats missed, triggering automated alert"
            ],
            "root_cause": f"{bg_incident['root_cause']} Occurred on {det_date_str}.",
            "fix_steps": bg_incident["fix_steps"],
            "runbook": bg_incident["runbook"]
        }
    return None


def generate_history():
    deploys = []
    ground_truth = []
    deploy_counter = 100

    # Build planted pattern schedule: day -> pattern_id
    pattern_schedule = {}
    healthy_overrides = {}
    for pid, pdata in PLANTED_PATTERNS.items():
        for d in pdata["occurrences"]:
            pattern_schedule[d] = pid
        for h in pdata.get("healthy_override", []):
            healthy_overrides[h] = pid

    bg_schedule = {b["day"]: b for b in BACKGROUND_INCIDENTS}

    pattern_counts = {p: 0 for p in PLANTED_PATTERNS}
    total_days = 90
    for day in range(1, total_days + 1):
        day_date = START_DATE + timedelta(days=day - 1)
        weekday = day_date.strftime("%A")
        is_weekend = weekday in ["Saturday", "Sunday"]

        # Requirement 4: Weight deploys heavily toward weekdays (90% weekday volume)
        if is_weekend:
            # 0 to 1 deploy on weekends
            deploys_today = 1 if (random.random() < 0.35) else 0
        else:
            # 1 to 3 deploys on weekdays
            deploys_today = random.randint(1, 3)

        # If a pattern or background incident falls today, ensure at least 1 deploy
        today_pattern = pattern_schedule.get(day)
        today_bg = bg_schedule.get(day)
        today_decoy = DECOY_SCHEDULE.get(day)

        if (today_pattern or today_bg or today_decoy) and deploys_today == 0:
            deploys_today = 1

        for deploy_idx in range(deploys_today):
            deploy_counter += 1
            deploy_id = f"dep-{deploy_counter}"
            author = random.choice(ENGINEERS)

            is_pattern = (today_pattern is not None and deploy_idx == 0)
            is_bg = (not is_pattern and today_bg is not None and deploy_idx == 0)
            is_decoy = (not is_pattern and not is_bg and today_decoy is not None and deploy_idx == 0)

            cur_occ_idx = 0
            if is_pattern:
                pid = today_pattern
                cur_occ_idx = pattern_counts[pid]
                if pid == "P1":
                    service = "payments-api"
                    change_type = "config"
                    # Strictly Friday evening (hour >= 16)
                    hour = random.randint(16, 19)
                    minute = random.randint(10, 50)
                elif pid == "P2":
                    service = "ledger-service"
                    change_type = "migration"
                    hour = random.randint(10, 15)
                    minute = random.randint(0, 59)
                elif pid == "P3":
                    service = "auth-service"
                    change_type = "dependency-bump"
                    hour = random.randint(11, 16)
                    minute = random.randint(0, 59)
                elif pid == "P4":
                    service = "checkout-web"
                    change_type = "feature-flag"
                    hour = random.randint(13, 17)
                    minute = random.randint(0, 59)
                elif pid == "P5":
                    service = random.choice(["payments-api", "ledger-service", "auth-service"])
                    change_type = "dependency-bump"
                    hour = random.randint(9, 14)
                    minute = random.randint(0, 59)
                elif pid == "P6":
                    service = "infra-terraform"
                    change_type = "infra"
                    hour = random.randint(14, 18)
                    minute = random.randint(0, 59)

                title, diff, files = make_realistic_pr_and_diff(service, change_type, pattern_id=pid, occurrence_idx=cur_occ_idx)
                pattern_counts[pid] += 1
            elif is_bg:
                pid = None
                service = today_bg["service"]
                change_type = today_bg["change_type"]
                hour = random.randint(10, 15)
                minute = random.randint(0, 59)
                title, diff, files = make_realistic_pr_and_diff(service, change_type)
            elif is_decoy:
                pid = None
                dtype = today_decoy
                if dtype.startswith("payments_"):
                    service = "payments-api"
                    change_type = "config"
                    # Thursday or Wednesday morning/afternoon (safe)
                    hour = random.randint(10, 14)
                elif dtype == "friday_other_service":
                    service = "checkout-web"
                    change_type = "code"
                    hour = random.randint(16, 18)
                elif dtype.startswith("ledger_migration_backfilled"):
                    service = "ledger-service"
                    change_type = "migration"
                    hour = random.randint(11, 14)
                elif dtype.startswith("dep_bump_"):
                    service = "notification-service" if "notification" in dtype else "risk-engine"
                    change_type = "dependency-bump"
                    hour = random.randint(11, 15)
                elif dtype == "flag_without_cache_ttl":
                    service = "checkout-web"
                    change_type = "feature-flag"
                    hour = random.randint(13, 15)
                elif dtype == "terraform_iam_update":
                    service = "infra-terraform"
                    change_type = "infra"
                    hour = random.randint(10, 14)
                else:
                    service = random.choice(SERVICES)
                    change_type = "code"
                    hour = random.randint(10, 16)

                minute = random.randint(0, 59)
                title, diff, files = make_realistic_pr_and_diff(service, change_type, is_decoy=True)
            else:
                pid = None
                service = random.choice(SERVICES)
                change_type = random.choice(CHANGE_TYPES)
                hour = random.randint(9, 17)
                minute = random.randint(0, 59)
                title, diff, files = make_realistic_pr_and_diff(service, change_type)

            timestamp = day_date.replace(hour=hour, minute=minute, second=0)

            deploy_record = {
                "deploy_id": deploy_id,
                "timestamp": timestamp.isoformat(),
                "day_of_week": weekday,
                "day_offset": day,
                "service": service,
                "environment": "production",
                "change_type": change_type,
                "author": author["name"],
                "author_email": author["email"],
                "pr_title": title,
                "diff_summary": diff,
                "files_changed": files,
            }

            # Determine outcome
            is_pattern_healthy_override = (is_pattern and day in healthy_overrides)

            if is_pattern and not is_pattern_healthy_override:
                if pid == "P5":
                    outcome_type = "build_failure"
                    ci_error = {
                        "failed_stage": "integration-tests",
                        "error_message": "glibc mismatch in base runner: undefined symbol: __pthread_getspecific, version GLIBC_2.34",
                        "duration_sec": 312,
                        "exit_code": 139,
                    }
                    deploy_record["ci_status"] = "failed"
                    deploy_record["ci_details"] = ci_error
                    deploy_record["outcome"] = "build_failure"
                else:
                    outcome_type = "incident"
                    incident_data = make_dynamic_incident(timestamp, service, pattern_id=pid, occurrence_idx=cur_occ_idx)
                    deploy_record["ci_status"] = "passed"
                    deploy_record["outcome"] = "incident"
                    deploy_record["incident"] = incident_data
            elif is_bg:
                outcome_type = "incident"
                incident_data = make_dynamic_incident(timestamp, service, bg_incident=today_bg)
                deploy_record["ci_status"] = "passed"
                deploy_record["outcome"] = "incident"
                deploy_record["incident"] = incident_data
            else:
                # Normal, decoy, or pattern healthy override
                # Add random transient CI flakes (~15% on normal deploys, but decoys & pattern overrides strictly healthy)
                is_flake = (not is_decoy and not is_pattern_healthy_override and random.random() < 0.15)
                if is_flake:
                    outcome_type = "build_failure"
                    ci_error = {
                        "failed_stage": "lint-and-unit-tests",
                        "error_message": "Flaky test timeout in TestGatewayConnectivity::test_reconnect (exceeded 60s)",
                        "duration_sec": 84,
                        "exit_code": 1,
                    }
                    deploy_record["ci_status"] = "failed"
                    deploy_record["ci_details"] = ci_error
                    deploy_record["outcome"] = "build_failure"
                else:
                    outcome_type = "healthy"
                    deploy_record["ci_status"] = "passed"
                    deploy_record["outcome"] = "healthy"

            deploys.append(deploy_record)

            # Ground truth record (never exposed to agent or memory)
            gt_record = {
                "deploy_id": deploy_id,
                "timestamp": timestamp.isoformat(),
                "service": service,
                "change_type": change_type,
                "outcome": outcome_type,
                "is_pattern": is_pattern,
                "pattern_id": pid if is_pattern else None,
                "pattern_name": PLANTED_PATTERNS[pid]["name"] if is_pattern else None,
                "is_pattern_healthy_override": is_pattern_healthy_override,
                "is_background_incident": is_bg,
                "is_decoy": is_decoy,
                "decoy_type": today_decoy if is_decoy else None,
                "caused_incident": (outcome_type == "incident"),
                "caused_build_failure": (outcome_type == "build_failure"),
                "explanation": (
                    f"Planted {pid} (Noisy Safe Run - canary passed)" if is_pattern_healthy_override
                    else f"Planted {pid}: {PLANTED_PATTERNS[pid]['description']}" if is_pattern
                    else f"Background Incident: {today_bg['title']}" if is_bg
                    else f"Decoy {today_decoy}: safe execution despite matching surface features" if is_decoy
                    else "Routine benign deployment"
                )
            }
            ground_truth.append(gt_record)

    return deploys, ground_truth


def main():
    deploys, ground_truth = generate_history()

    # Sort strictly chronologically
    deploys.sort(key=lambda d: d["timestamp"])
    ground_truth.sort(key=lambda g: g["timestamp"])

    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    history_path = data_dir / "history.json"
    ground_truth_path = data_dir / "ground_truth.json"

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(deploys, f, indent=2)

    with open(ground_truth_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Generated {len(deploys)} deployment records to {history_path}")
    print(f"Generated {len(ground_truth)} ground truth records to {ground_truth_path}")

    incidents = [d for d in deploys if d.get("outcome") == "incident"]
    failures = [d for d in deploys if d.get("outcome") == "build_failure"]
    healthy = [d for d in deploys if d.get("outcome") == "healthy"]

    print(f"Total Deploys: {len(deploys)}")
    print(f"Healthy: {len(healthy)}")
    print(f"CI Build Failures: {len(failures)}")
    print(f"Incidents: {len(incidents)}")


if __name__ == "__main__":
    main()
