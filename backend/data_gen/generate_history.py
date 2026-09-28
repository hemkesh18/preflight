"""
Deterministic generator for Kestrel Pay's 90-day deployment & incident history.
Generates realistic DevOps events, hidden failure patterns, decoys, and post-mortems.
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

START_DATE = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)

# 6 Planted Patterns Specification
PLANTED_PATTERNS = {
    "P1": {
        "name": "Friday-evening payments-api config changes",
        "description": "payments-api config changes deployed on Friday evening cause connection pool exhaustion during weekend batch prep.",
        "occurrences": [7, 28, 49, 70],  # Days into timeline (Fridays: Day 5=Fri Jun 5, Day 12=Fri Jun 12, etc.)
    },
    "P2": {
        "name": "ledger-service migration without backfill",
        "description": "ledger-service schema migration omitting column backfill breaks downstream search-indexer and reporting-service.",
        "occurrences": [11, 35, 62],
    },
    "P3": {
        "name": "auth-service jwt-lib bump breaks checkout",
        "description": "auth-service jwt-lib dependency bump causes clock skew and token verification failures in checkout-web.",
        "occurrences": [18, 44, 75],
    },
    "P4": {
        "name": "checkout_v2 flag toggle paired with cache TTL change",
        "description": "Toggling checkout_v2 flag while changing cache TTL causes checkout session state desync and 500 error cascade.",
        "occurrences": [22, 53, 81],
    },
    "P5": {
        "name": "Base-image bump breaks CI build",
        "description": "Upgrading alpine/debian base image in Dockerfile introduces incompatible glibc/openssl, failing CI integration suite.",
        "occurrences": [14, 39, 67, 85],
    },
    "P6": {
        "name": "terraform security-group edit blocks notifications",
        "description": "Terraform security group egress rule change inadvertently drops outbound SMTP/SES port 587 traffic.",
        "occurrences": [25, 58, 78],
    }
}


def make_pr_info(service, change_type, pattern_id=None, is_decoy=False):
    """Generate realistic PR title, files changed, and diff summary without revealing the failure cause in title."""
    if pattern_id == "P1":
        titles = [
            "perf(payments): tune threadpool and db timeout parameters",
            "chore(payments): adjust redis retry backoff and pool limits",
            "fix(payments): update worker buffer thresholds in config",
            "chore(config): refresh downstream gateway connection timeouts"
        ]
        diff = "- pool_max_connections: 50\n+ pool_max_connections: 20\n- keepalive_timeout_ms: 3000\n+ keepalive_timeout_ms: 15000\n- max_overflow: 30\n+ max_overflow: 5"
        files = ["config/production.yaml", "helm/values-prod.yaml"]
    elif pattern_id == "P2":
        titles = [
            "feat(ledger): optimize transaction ledger storage layout",
            "feat(ledger): partition ledger_entries table by currency_code",
            "refactor(ledger): restructure settlement balance tracking columns"
        ]
        diff = "- ALTER TABLE ledger_entries ADD COLUMN settlement_epoch BIGINT;\n+ ALTER TABLE ledger_entries DROP COLUMN legacy_settlement_id, ADD COLUMN settlement_epoch BIGINT NOT NULL;"
        files = ["migrations/202606_ledger_settlement.sql", "src/models/ledger.py"]
    elif pattern_id == "P3":
        titles = [
            "chore(deps): update security libraries and token verifier",
            "chore(deps): bump pyjwt and cryptography to latest minor",
            "chore(security): upgrade core auth token handling packages"
        ]
        diff = "- pyjwt==2.8.0\n+ pyjwt==2.10.1\n- cryptography==42.0.5\n+ cryptography==43.0.1"
        files = ["requirements.txt", "Pipfile.lock"]
    elif pattern_id == "P4":
        titles = [
            "feat(checkout): prepare rollout phase for payment sheet",
            "chore(release): flip experiment cohort and tune caching",
            "feat(checkout): activate checkout_v2 cohort with session caching"
        ]
        diff = "- flags.checkout_v2: false\n+ flags.checkout_v2: true\n- session_cache_ttl_sec: 3600\n+ session_cache_ttl_sec: 60"
        files = ["config/features.json", "src/services/session_cache.ts"]
    elif pattern_id == "P5":
        titles = [
            "chore(docker): bump python base image for security patches",
            "chore(ci): update container base image in build pipeline",
            "chore(docker): refresh debian slim base image to v12.6",
            "build(docker): bump alpine base runner for lighter container"
        ]
        diff = "- FROM python:3.11.8-slim-bookworm\n+ FROM python:3.12.3-slim-bookworm\n- RUN apt-get install -y libpq-dev\n+ RUN apt-get install -y --no-install-recommends libpq-dev"
        files = ["Dockerfile", ".github/workflows/ci.yml"]
    elif pattern_id == "P6":
        titles = [
            "infra(network): tighten vpc egress firewall rules",
            "infra(terraform): consolidate default security groups across vpc",
            "infra(secops): apply least-privilege outbound rule matrix"
        ]
        diff = "- egress { from_port = 0, to_port = 0, protocol = '-1', cidr_blocks = ['0.0.0.0/0'] }\n+ egress { from_port = 443, to_port = 443, protocol = 'tcp', cidr_blocks = ['0.0.0.0/0'] }"
        files = ["terraform/modules/vpc/security_groups.tf", "terraform/environments/prod/main.tf"]
    elif is_decoy:
        # Decoys: look like patterns but have safe parameters
        if service == "payments-api" and change_type == "config":
            # Decoy: config change on Tuesday morning
            titles = ["chore(config): adjust payments api rate limiter buckets"]
            diff = "- max_burst: 200\n+ max_burst: 250"
            files = ["config/payments.yaml"]
        elif service == "ledger-service" and change_type == "migration":
            # Decoy: migration WITH safe backfill
            titles = ["feat(ledger): add index and backfilled audit column"]
            diff = "+ ALTER TABLE ledger_entries ADD COLUMN audit_hash VARCHAR(64) DEFAULT '';\n+ UPDATE ledger_entries SET audit_hash = md5(id::text) WHERE audit_hash = '';"
            files = ["migrations/202607_backfill_audit.sql"]
        elif change_type == "feature-flag" and service == "checkout-web":
            # Decoy: checkout_v2 toggled WITHOUT cache TTL change
            titles = ["feat(checkout): toggle checkout_v2 beta cohort"]
            diff = "- flags.checkout_v2: false\n+ flags.checkout_v2: true"
            files = ["config/features.json"]
        elif service == "infra-terraform":
            # Decoy: terraform s3 or iam change without security groups
            titles = ["infra(iam): update reporting s3 bucket read policy"]
            diff = "+ actions = ['s3:GetObject', 's3:ListBucket']"
            files = ["terraform/modules/iam/reporting.tf"]
        else:
            titles = [f"chore({service}): routine maintenance and minor fix"]
            diff = "- debug: false\n+ debug: false"
            files = ["src/config.py"]
    else:
        # Routine realistic PRs
        templates = {
            "code": [
                f"feat({service}): implement idempotency token validation",
                f"fix({service}): resolve race condition in webhook dispatcher",
                f"refactor({service}): optimize memory allocation in deserializer",
                f"feat({service}): add structured request trace logging",
                f"fix({service}): handle edge case in customer currency conversion",
                f"feat({service}): add circuit breaker for downstream gateway calls"
            ],
            "config": [
                f"chore(config): update log level from debug to info in {service}",
                f"chore(config): refresh datadog apm sampler rates",
                f"chore(config): adjust prometheus scraping interval"
            ],
            "migration": [
                f"feat(db): add composite index on (created_at, status) in {service}",
                f"feat(db): archive stale transaction records older than 180 days"
            ],
            "dependency-bump": [
                f"chore(deps): bump requests from 2.31.0 to 2.32.3 in {service}",
                f"chore(deps): upgrade redis-py client library to 5.0.4",
                f"chore(deps): bump pydantic to 2.7.4 for bug fixes"
            ],
            "feature-flag": [
                f"feat(flags): enable new_fraud_scoring_model in risk-engine",
                f"feat(flags): enable dark_mode_beta cohort for web users"
            ],
            "infra": [
                f"infra(k8s): increase memory request for {service} pods",
                f"infra(alb): tune idle timeout to 60 seconds on load balancer"
            ]
        }
        titles = templates.get(change_type, [f"chore({service}): general update"])
        diff = f"// Routine updates to {service} logic\n- timeout_ms = 5000\n+ timeout_ms = 4500"
        files = [f"src/{service.replace('-', '_')}/core.py", f"tests/test_core.py"]

    title = random.choice(titles)
    return title, diff, files


def make_incident_postmortem(deploy, pattern_id):
    """Generate realistic incident details, stack traces, metrics, root cause, and fix."""
    delay_minutes = random.randint(15, 85)
    detection_time = (deploy["timestamp"] + timedelta(minutes=delay_minutes)).isoformat()
    mttr_minutes = random.randint(35, 110)
    resolved_time = (deploy["timestamp"] + timedelta(minutes=delay_minutes + mttr_minutes)).isoformat()

    if pattern_id == "P1":
        return {
            "severity": "SEV-1",
            "title": "payments-api Connection Pool Starvation and Spike in 504 Gateway Timeouts",
            "detected_at": detection_time,
            "resolved_at": resolved_time,
            "mttr_minutes": mttr_minutes,
            "impact": "Payment processing halted for 42 minutes; 1,420 checkout attempts failed with HTTP 504; p99 latency spiked to 6,800ms.",
            "metrics": {
                "http_5xx_rate": "18.4%",
                "p99_latency_ms": 6820,
                "error_budget_burn": "42%",
                "affected_rps": 320
            },
            "error_logs": [
                "ERROR 2026-06-05 19:42:11 payments-api.pool: sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 5 reached, connection timed out, timeout 15.00",
                "FATAL 2026-06-05 19:42:15 payments-api.gateway: [CheckoutGate] upstream payments-api worker exhausted, returning HTTP 504",
                "WARN  2026-06-05 19:43:02 payments-api.health: liveness probe failed: HTTP 503 connection refused"
            ],
            "root_cause": "Friday evening batch settlement traffic coincided with reduced pool_max_connections (decreased from 50 to 20) and high keepalive_timeout_ms (15s), preventing worker connections from recycling.",
            "fix_steps": "Reverted pool_max_connections to 60, decreased keepalive timeout to 3000ms, and performed rolling restart of payments-api pods.",
            "runbook": "RB-PAY-04: Database Connection Pool Exhaustion & Recovery"
        }
    elif pattern_id == "P2":
        return {
            "severity": "SEV-1",
            "title": "search-indexer and reporting-service Crash Loop on Dropped Ledger Column",
            "detected_at": detection_time,
            "resolved_at": resolved_time,
            "mttr_minutes": mttr_minutes,
            "impact": "Merchant transaction search offline; overnight reporting aggregation pipeline halted; 12,000 ledger events queued in Kafka DLQ.",
            "metrics": {
                "http_5xx_rate": "12.1%",
                "p99_latency_ms": 4250,
                "error_budget_burn": "28%",
                "affected_rps": 180
            },
            "error_logs": [
                "CRITICAL 2026-06-12 11:24:08 search-indexer.consumer: KeyError: 'legacy_settlement_id' missing from CDC event payload",
                "ERROR 2026-06-12 11:24:12 reporting-service.pipeline: psycopg2.errors.UndefinedColumn: column ledger_entries.legacy_settlement_id does not exist",
                "FATAL 2026-06-12 11:24:19 search-indexer: ConsumerGroupOffsetExpiredException: max retry limit exceeded on topic ledger.events"
            ],
            "root_cause": "Destructive schema migration in ledger-service dropped legacy_settlement_id immediately without a multi-phase deprecation or backfill phase, crashing downstream consumers.",
            "fix_steps": "Executed hotfix migration adding back legacy_settlement_id as a generated column aliased to settlement_epoch, resumed Kafka consumer offsets.",
            "runbook": "RB-DB-02: Zero-Downtime Schema Evolution & Consumer Recovery"
        }
    elif pattern_id == "P3":
        return {
            "severity": "SEV-2",
            "title": "checkout-web Widespread HTTP 401 Unauthorized Spike Following Auth JWT Upgrade",
            "detected_at": detection_time,
            "resolved_at": resolved_time,
            "mttr_minutes": mttr_minutes,
            "impact": "Valid logged-in users rejected at checkout page with 'Session Expired'; 3,800 checkout abandonments.",
            "metrics": {
                "http_5xx_rate": "1.2%",
                "http_401_rate": "34.7%",
                "p99_latency_ms": 840,
                "error_budget_burn": "19%",
                "affected_rps": 410
            },
            "error_logs": [
                "WARN 2026-06-19 14:15:33 checkout-web.auth: jwt.exceptions.InvalidAlgorithmError: The specified alg 'RS256' requires strict key format validation in pyjwt>=2.10",
                "ERROR 2026-06-19 14:15:38 checkout-web.session: Failed to decode user session token from Authorization header: verification failed",
                "INFO 2026-06-19 14:15:42 auth-service: Rejected token issue: clock skew tolerance exceeded (0s threshold)"
            ],
            "root_cause": "auth-service pyjwt dependency upgrade enforced strict asymmetric key formatting and zero leeway on clock skew, rejecting valid JWT tokens issued by older client instances.",
            "fix_steps": "Configured jwt.decode leeway=10s and aligned public key PEM header formatting; rolled back auth-service to pyjwt 2.8.0 pending client rollout.",
            "runbook": "RB-SEC-09: JWT Token Invalidation & Algorithm Rotation"
        }
    elif pattern_id == "P4":
        return {
            "severity": "SEV-1",
            "title": "checkout-web Cart State Desync and Payment Submission 500 Cascade",
            "detected_at": detection_time,
            "resolved_at": resolved_time,
            "mttr_minutes": mttr_minutes,
            "impact": "Users charged twice or seeing empty carts on payment confirmation; payment gateway double-submission alert triggered.",
            "metrics": {
                "http_5xx_rate": "24.6%",
                "p99_latency_ms": 5400,
                "error_budget_burn": "38%",
                "affected_rps": 560
            },
            "error_logs": [
                "ERROR 2026-06-23 16:32:01 checkout-web.session: CartSessionMismatchError: active cart session 8f72a expired while payment confirmation pending",
                "FATAL 2026-06-23 16:32:05 payments-api.intent: Duplicate payment idempotency key with mismatching payload hash",
                "ERROR 2026-06-23 16:32:19 checkout-web.frontend: Uncaught (in promise) Error: HTTP 500 Internal Server Error at CheckoutContainer.tsx:142"
            ],
            "root_cause": "Simultaneous activation of checkout_v2 feature flag and reduction of session cache TTL from 3600s to 60s caused cart sessions to vanish midway through 3D-Secure payment handoffs.",
            "fix_steps": "Restored session_cache_ttl_sec to 3600, disabled checkout_v2 feature flag, executed automated refund reconciliation script.",
            "runbook": "RB-FE-01: Feature Flag Rollback & Stale State Eviction"
        }
    elif pattern_id == "P6":
        return {
            "severity": "SEV-2",
            "title": "notification-service Egress Timeout & Queue Overflow on Blocked SMTP Port",
            "detected_at": detection_time,
            "resolved_at": resolved_time,
            "mttr_minutes": mttr_minutes,
            "impact": "Payment confirmation receipts, 2FA OTP codes, and fraud alerts delayed by up to 90 minutes.",
            "metrics": {
                "http_5xx_rate": "8.9%",
                "p99_latency_ms": 3100,
                "error_budget_burn": "15%",
                "affected_rps": 120
            },
            "error_logs": [
                "ERROR 2026-06-26 18:05:40 notification-service.mailer: OSError: [Errno 110] Connection timed out while connecting to email-smtp.us-east-1.amazonaws.com:587",
                "WARN  2026-06-26 18:06:12 notification-service.queue: Redis queue 'email_notifications' exceeded 25,000 pending items",
                "ERROR 2026-06-26 18:07:01 notification-service.worker: MaxRetryError: SQS message failed 5 times, sending to dead_letter_queue"
            ],
            "root_cause": "Terraform security group update tightened default egress to port 443 only, inadvertently dropping outbound TCP traffic on port 587 needed by notification-service.",
            "fix_steps": "Added explicit egress rule in terraform security_groups.tf allowing outbound TCP port 587 to AWS SES CIDR ranges; ran terraform apply and flushed delayed queue.",
            "runbook": "RB-INFRA-07: VPC Security Group & Egress Connectivity Troubleshooting"
        }
    return None


def generate_history():
    """Generates 90 days of deterministic deploys, CI failures, incidents, and decoys."""
    deploys = []
    ground_truth = []
    deploy_counter = 100

    # Build planted pattern timeline map: day_offset -> pattern_id
    pattern_schedule = {}
    for pid, pdata in PLANTED_PATTERNS.items():
        for d in pdata["occurrences"]:
            pattern_schedule[d] = pid

    # Planted decoy timeline map: day_offset -> decoy_type
    decoy_schedule = {
        5: "payments_tuesday_config",      # payments-api config on Tuesday (healthy)
        12: "friday_other_service",        # Friday deploy to checkout-web (healthy)
        19: "ledger_migration_backfilled",  # ledger migration with backfill (healthy)
        26: "dep_bump_notification",       # dependency bump on notification-service (healthy)
        33: "friday_auth_code",            # Friday code change to auth-service (healthy)
        40: "flag_without_cache_ttl",      # feature flag toggle without cache TTL change (healthy)
        47: "payments_wednesday_config",   # payments-api config on Wednesday (healthy)
        54: "terraform_iam_update",        # terraform IAM change without security groups (healthy)
        61: "friday_reporting_service",    # Friday deploy to reporting-service (healthy)
        68: "ledger_migration_backfilled_2",# second backfilled migration (healthy)
        74: "friday_search_indexer",       # Friday deploy to search-indexer (healthy)
        82: "dep_bump_risk_engine",        # dependency bump on risk-engine (healthy)
    }

    current_time = START_DATE
    total_days = 90

    for day in range(1, total_days + 1):
        day_date = START_DATE + timedelta(days=day - 1)
        weekday = day_date.strftime("%A")

        # 1-3 deploys per day
        deploys_today = random.randint(1, 3)

        # Check if today has a planted pattern
        today_pattern = pattern_schedule.get(day)
        today_decoy = decoy_schedule.get(day)

        for deploy_idx in range(deploys_today):
            deploy_counter += 1
            deploy_id = f"dep-{deploy_counter}"
            author = random.choice(ENGINEERS)

            # Determine timing
            is_pattern_deploy = (today_pattern is not None and deploy_idx == 0)
            is_decoy_deploy = (not is_pattern_deploy and today_decoy is not None and deploy_idx == 0)

            if is_pattern_deploy:
                pid = today_pattern
                if pid == "P1":
                    # Friday evening deploy
                    service = "payments-api"
                    change_type = "config"
                    hour = random.randint(17, 19)
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
                    # CI failure pattern
                    service = random.choice(["payments-api", "ledger-service", "auth-service"])
                    change_type = "dependency-bump"
                    hour = random.randint(9, 14)
                    minute = random.randint(0, 59)
                elif pid == "P6":
                    service = "infra-terraform"
                    change_type = "infra"
                    hour = random.randint(14, 18)
                    minute = random.randint(0, 59)

                title, diff, files = make_pr_info(service, change_type, pattern_id=pid)
            elif is_decoy_deploy:
                pid = None
                dtype = today_decoy
                if dtype.startswith("payments_"):
                    service = "payments-api"
                    change_type = "config"
                    hour = random.randint(10, 12)
                elif dtype == "friday_other_service":
                    service = "checkout-web"
                    change_type = "code"
                    hour = random.randint(17, 18)
                elif dtype.startswith("ledger_migration_backfilled"):
                    service = "ledger-service"
                    change_type = "migration"
                    hour = random.randint(11, 14)
                elif dtype.startswith("dep_bump_"):
                    service = "notification-service" if "notification" in dtype else "risk-engine"
                    change_type = "dependency-bump"
                    hour = random.randint(13, 16)
                elif dtype == "flag_without_cache_ttl":
                    service = "checkout-web"
                    change_type = "feature-flag"
                    hour = random.randint(14, 16)
                elif dtype == "terraform_iam_update":
                    service = "infra-terraform"
                    change_type = "infra"
                    hour = random.randint(10, 15)
                else:
                    service = random.choice(SERVICES)
                    change_type = "code"
                    hour = random.randint(10, 16)

                minute = random.randint(0, 59)
                title, diff, files = make_pr_info(service, change_type, is_decoy=True)
            else:
                pid = None
                service = random.choice(SERVICES)
                change_type = random.choice(CHANGE_TYPES)
                # Normal working hours
                hour = random.randint(9, 17)
                minute = random.randint(0, 59)
                title, diff, files = make_pr_info(service, change_type)

            timestamp = day_date.replace(hour=hour, minute=minute, second=0)

            # Build deploy record
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
            incident_data = None
            if is_pattern_deploy:
                if pid == "P5":
                    # CI build failure
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
                    incident_data = make_incident_postmortem({"timestamp": timestamp, "deploy_id": deploy_id}, pid)
                    deploy_record["ci_status"] = "passed"
                    deploy_record["outcome"] = "incident"
                    deploy_record["incident"] = incident_data
            else:
                # Normal deploys: occasionally add a random non-pattern transient CI flake (~16% chance), but keep decoys strictly healthy
                is_random_ci_flake = (not is_decoy_deploy and random.random() < 0.16)
                if is_random_ci_flake:
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

            # Ground truth record (never visible to agent or stored in memory)
            gt_record = {
                "deploy_id": deploy_id,
                "timestamp": timestamp.isoformat(),
                "service": service,
                "change_type": change_type,
                "outcome": outcome_type,
                "is_pattern": is_pattern_deploy,
                "pattern_id": pid if is_pattern_deploy else None,
                "pattern_name": PLANTED_PATTERNS[pid]["name"] if is_pattern_deploy else None,
                "is_decoy": is_decoy_deploy,
                "decoy_type": today_decoy if is_decoy_deploy else None,
                "caused_incident": (outcome_type == "incident"),
                "caused_build_failure": (outcome_type == "build_failure"),
                "explanation": (
                    f"Planted {pid}: {PLANTED_PATTERNS[pid]['description']}" if is_pattern_deploy
                    else f"Decoy {today_decoy}: safe execution despite matching surface features" if is_decoy_deploy
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

    # Summary statistics
    incidents = [d for d in deploys if d.get("outcome") == "incident"]
    failures = [d for d in deploys if d.get("outcome") == "build_failure"]
    healthy = [d for d in deploys if d.get("outcome") == "healthy"]

    print(f"Total Deploys: {len(deploys)}")
    print(f"Healthy: {len(healthy)}")
    print(f"CI Build Failures: {len(failures)}")
    print(f"Incidents: {len(incidents)}")


if __name__ == "__main__":
    main()
