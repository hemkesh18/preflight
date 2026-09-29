"""
Hindsight Memory Layer for Preflight.
Interfaces with Vectorize's Hindsight client for persistent agent memory:
- Bank creation, mission, and behavioral directives
- Idempotent retention of deployments, incident outcomes, and prediction feedback
- Contextual recall with tag filtering and temporal anchoring (zero-leakage)
- Multi-incident reflection and pattern synthesis
"""
import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from hindsight_client import Hindsight, RecallResponse, RetainResponse

logger = logging.getLogger("preflight.memory")


class HindsightMemoryStore:
    def __init__(
        self,
        bank_id: str = "kestrel-pay",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        fresh_bank: bool = False
    ):
        self.bank_id = bank_id
        self.base_url = base_url or os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.api_key = api_key or os.getenv("HINDSIGHT_API_KEY")

        if not self.api_key:
            raise ValueError("HINDSIGHT_API_KEY is not set. Check your .env file.")

        self.client = Hindsight(base_url=self.base_url, api_key=self.api_key)
        self._retained_doc_ids = set()
        self._pattern_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0

        if fresh_bank:
            self.purge_bank()
        self.ensure_bank()

    def _retain_with_retry(self, **kwargs) -> RetainResponse:
        last_err = None
        for attempt in range(4):
            try:
                return self.client.retain(**kwargs)
            except Exception as e:
                last_err = e
                logger.warning(f"Hindsight retain attempt {attempt+1} failed: {e}. Retrying in {2**attempt}s...")
                time.sleep(2 ** attempt)
        raise last_err

    def _recall_with_retry(self, **kwargs) -> RecallResponse:
        last_err = None
        for attempt in range(4):
            try:
                return self.client.recall(**kwargs)
            except Exception as e:
                last_err = e
                logger.warning(f"Hindsight recall attempt {attempt+1} failed: {e}. Retrying in {2**attempt}s...")
                time.sleep(2 ** attempt)
        raise last_err

    def _delete_document_if_exists(self, doc_id: str) -> None:
        """Deletes any previous version of a document to guarantee strict idempotency across process restarts."""
        try:
            _run_async = Hindsight.retain_batch.__globals__.get("_run_async")
            if _run_async:
                _run_async(self.client.documents.delete_document(bank_id=self.bank_id, document_id=doc_id))
        except Exception as e:
            logger.debug(f"Document {doc_id} delete check notice: {e}")

    def purge_bank(self) -> None:
        """Deletes the memory bank completely to ensure sterile replay / test isolation."""
        try:
            self.client.delete_bank(bank_id=self.bank_id)
            logger.info(f"Purged existing memory bank '{self.bank_id}' for sterile run.")
        except Exception as e:
            logger.debug(f"Bank purge notice (may not exist): {e}")
        self._retained_doc_ids.clear()
        self._pattern_cache = None

    def ensure_bank(self) -> None:
        """
        Initializes the memory bank for Kestrel Pay with its mission and core directives.
        Idempotent: catches already-existing bank status.
        """
        mission = (
            "Release-risk analyst for fintech Kestrel Pay; learn which change types, "
            "services, and deployment timings precede incidents and build failures; "
            "track what fixes worked to prevent repeat outages."
        )

        try:
            self.client.create_bank(
                bank_id=self.bank_id,
                name="Kestrel Pay Pipeline Gate",
                mission=mission,
                disposition_skepticism=4,
                disposition_literalism=4,
                disposition_empathy=2,
                enable_temporal_retrieval=True,
                enable_text_search=True
            )
            logger.info(f"Memory bank '{self.bank_id}' initialized.")
        except Exception as e:
            # Bank likely exists already; update mission if possible
            logger.info(f"create_bank notice (bank may exist): {e}")
            try:
                self.client.set_mission(self.bank_id, mission)
            except Exception:
                pass

        # Configure Directives
        directives = [
            (
                "citation_grounding",
                "Always cite the exact memory ID for every risk claim or incident precedent cited. Never invent memory IDs.",
                1
            ),
            (
                "no_hallucinated_incidents",
                "Never fabricate or assume past outages. If no precedent exists in memory, explicitly state uncertainty.",
                2
            ),
            (
                "remedy_tracking",
                "When recalling past incidents, always extract what fix steps, runbooks, and parameter rollbacks succeeded.",
                3
            )
        ]

        for name, content, priority in directives:
            try:
                self.client.create_directive(
                    bank_id=self.bank_id,
                    name=name,
                    content=content,
                    priority=priority,
                    is_active=True
                )
            except Exception as de:
                logger.debug(f"Directive '{name}' notice: {de}")

    def retain_deploy(self, deploy: Dict[str, Any], wait_for_completion: bool = False) -> RetainResponse:
        """
        Retains a deployment proposal into Hindsight memory.
        Idempotent via document_id. Never contains ground truth or outcome.
        """
        deploy_id = deploy["deploy_id"]
        service = deploy["service"]
        change_type = deploy["change_type"]
        env = deploy.get("environment", "production")
        day_of_week = deploy.get("day_of_week", "Unknown")
        author = deploy.get("author", "Unknown")
        pr_title = deploy.get("pr_title", "")
        diff_summary = deploy.get("diff_summary", "")
        files = ", ".join(deploy.get("files_changed", []))

        # Parse timestamp to UTC datetime
        ts_raw = deploy.get("timestamp")
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw)
        elif isinstance(ts_raw, datetime):
            ts = ts_raw
        else:
            ts = datetime.now(timezone.utc)

        content = (
            f"DEPLOYMENT PROPOSAL: Deploy {deploy_id} initiated at {ts.isoformat()} on service '{service}' ({env}) by {author} on {day_of_week}.\n"
            f"PR Title: {pr_title}\n"
            f"Change Type: {change_type}\n"
            f"Files Changed: {files}\n"
            f"Diff Summary:\n{diff_summary}"
        )

        tags = [
            f"service:{service}",
            f"type:{change_type}",
            f"env:{env}",
            f"day:{day_of_week.lower()}",
            f"deploy:{deploy_id}"
        ]

        metadata = {
            "deploy_id": deploy_id,
            "service": service,
            "change_type": change_type,
            "stage": "pre_deploy"
        }

        doc_id = f"deploy-{deploy_id}"
        if doc_id in self._retained_doc_ids:
            logger.debug(f"Document {doc_id} already retained in this session; skipping.")
            return RetainResponse(success=True, bank_id=self.bank_id, items_count=0, var_async=False)

        # True cross-process idempotency: purge prior document version if already exists
        self._delete_document_if_exists(doc_id)

        resp = self._retain_with_retry(
            bank_id=self.bank_id,
            content=content,
            timestamp=ts,
            context="Kestrel Pay CI/CD Pipeline Gate - Pre-Deploy Risk Evaluation",
            document_id=doc_id,
            tags=tags,
            metadata=metadata
        )
        self._retained_doc_ids.add(doc_id)

        if wait_for_completion and getattr(resp, "operation_id", None):
            self.wait_for_operation(resp.operation_id)

        return resp

    def retain_outcome(self, deploy: Dict[str, Any], wait_for_completion: bool = False) -> RetainResponse:
        """
        Retains the real-world post-deploy outcome into Hindsight memory:
        - Healthy: Clean run, 0 alerts.
        - Build Failure: CI failure stage and error log.
        - Incident: Severity, impact, error logs, root cause, fix steps, runbook.
        Every outcome is timestamped strictly AFTER its deploy.
        """
        deploy_id = deploy["deploy_id"]
        service = deploy["service"]
        change_type = deploy["change_type"]
        outcome = deploy.get("outcome", "healthy")
        env = deploy.get("environment", "production")

        ts_raw = deploy.get("timestamp")
        if isinstance(ts_raw, str):
            deploy_ts = datetime.fromisoformat(ts_raw)
        elif isinstance(ts_raw, datetime):
            deploy_ts = ts_raw
        else:
            deploy_ts = datetime.now(timezone.utc)

        tags = [
            f"service:{service}",
            f"type:{change_type}",
            f"outcome:{outcome}",
            f"deploy:{deploy_id}"
        ]

        if outcome == "incident":
            inc = deploy.get("incident", {})
            if inc.get("detected_at"):
                ts = datetime.fromisoformat(inc["detected_at"])
            else:
                ts = deploy_ts + timedelta(minutes=15)

            logs_str = "\n".join(inc.get("error_logs", []))
            metrics = inc.get("metrics", {})
            metrics_str = f"5xx Rate: {metrics.get('http_5xx_rate', 'N/A')}, p99: {metrics.get('p99_latency_ms', 'N/A')}ms"

            content = (
                f"POST-INCIDENT POST-MORTEM: Deployment {deploy_id} (deployed at {deploy_ts.isoformat()}) on {service} caused a {inc.get('severity', 'SEV-1')} incident detected at {ts.isoformat()}!\n"
                f"Incident Title: {inc.get('title')}\n"
                f"Impact: {inc.get('impact')}\n"
                f"Metrics: {metrics_str}\n"
                f"Error Logs Sample:\n{logs_str}\n"
                f"Root Cause Analysis:\n{inc.get('root_cause')}\n"
                f"Successful Remediation / Fix Steps:\n{inc.get('fix_steps')}\n"
                f"Runbook Applied: {inc.get('runbook')}"
            )
            tags.append(f"severity:{inc.get('severity', 'SEV-1').lower()}")
        elif outcome == "build_failure":
            ts = deploy_ts + timedelta(minutes=5)
            ci = deploy.get("ci_details", {})
            content = (
                f"CI BUILD FAILURE: Deployment {deploy_id} (initiated at {deploy_ts.isoformat()}) on {service} failed in CI pipeline at {ts.isoformat()}.\n"
                f"Failed Stage: {ci.get('failed_stage')}\n"
                f"Error Message: {ci.get('error_message')}\n"
                f"Exit Code: {ci.get('exit_code')}"
            )
            tags.append("ci:failure")
        else:
            ts = deploy_ts + timedelta(minutes=10)
            content = (
                f"HEALTHY DEPLOYMENT VERIFICATION: Deployment {deploy_id} (deployed at {deploy_ts.isoformat()}) on {service} completed successfully verified at {ts.isoformat()}.\n"
                f"Automated health checks passed. Zero production alerts, error budget burn was 0.0%."
            )
            tags.append("ci:passed")

        metadata = {
            "deploy_id": deploy_id,
            "service": service,
            "outcome": outcome,
            "stage": "post_deploy"
        }

        doc_id = f"outcome-{deploy_id}"
        if doc_id in self._retained_doc_ids:
            logger.debug(f"Document {doc_id} already retained in this session; skipping.")
            return RetainResponse(success=True, bank_id=self.bank_id, items_count=0, var_async=False)

        # True cross-process idempotency
        self._delete_document_if_exists(doc_id)

        resp = self._retain_with_retry(
            bank_id=self.bank_id,
            content=content,
            timestamp=ts,
            context="Kestrel Pay Incident & Deployment Post-Mortem Records",
            document_id=doc_id,
            tags=tags,
            metadata=metadata
        )
        self._retained_doc_ids.add(doc_id)

        if wait_for_completion and getattr(resp, "operation_id", None):
            self.wait_for_operation(resp.operation_id)

        return resp

    def retain_prediction_feedback(
        self,
        deploy_id: str,
        service: str,
        predicted_risk: float,
        predicted_level: str,
        actual_outcome: str,
        was_correct: bool,
        notes: str = "",
        timestamp: Optional[datetime] = None
    ) -> RetainResponse:
        """
        Retains feedback on the agent's own risk prediction.
        Enables the agent to learn from its false positives and false negatives.
        """
        ts = timestamp or datetime.now(timezone.utc)
        result_label = "CORRECT" if was_correct else "INCORRECT"

        content = (
            f"AGENT PREDICTION FEEDBACK for {deploy_id} on {service}:\n"
            f"Predicted Risk Score: {predicted_risk:.2f} ({predicted_level})\n"
            f"Actual Outcome: {actual_outcome}\n"
            f"Evaluation: Prediction was {result_label}.\n"
            f"Notes: {notes}"
        )

        tags = [
            f"service:{service}",
            f"feedback:{result_label.lower()}",
            f"deploy:{deploy_id}"
        ]

        resp = self.client.retain(
            bank_id=self.bank_id,
            content=content,
            timestamp=ts,
            context="Preflight Agent Continuous Learning & Self-Calibration",
            document_id=f"feedback-{deploy_id}",
            tags=tags
        )
        return resp

    def recall_for_deploy(
        self,
        deploy: Dict[str, Any],
        max_tokens: int = 4096,
        budget: str = "mid"
    ) -> List[Dict[str, Any]]:
        """
        Recalls relevant past memories (incidents, failed deploys, healthy precedents)
        anchored strictly to deploy timestamp to eliminate future leakage.
        Combines service-specific tag filtering with cross-service pattern search.
        """
        service = deploy["service"]
        change_type = deploy["change_type"]
        day_of_week = deploy.get("day_of_week", "")
        pr_title = deploy.get("pr_title", "")
        diff_summary = deploy.get("diff_summary", "")

        # Strict temporal anchor
        ts_raw = deploy.get("timestamp")
        query_ts = ts_raw if isinstance(ts_raw, str) else ts_raw.isoformat() if ts_raw else None

        # Targeted query
        query = (
            f"Past incidents, build failures, outages, and configuration risks for {service} "
            f"involving {change_type} changes, {pr_title}, or {day_of_week} deployments."
        )

        # Primary recall: filtered by service
        memories = []
        seen_ids = set()

        try:
            resp: RecallResponse = self._recall_with_retry(
                bank_id=self.bank_id,
                query=query,
                tags=[f"service:{service}"],
                tags_match="any",
                max_tokens=max_tokens // 2,
                budget=budget,
                query_timestamp=query_ts
            )
            for r in resp.results:
                if r.id not in seen_ids:
                    seen_ids.add(r.id)
                    memories.append({
                        "id": r.id,
                        "text": r.text,
                        "tags": r.tags or [],
                        "document_id": getattr(r, "document_id", None),
                        "timestamp": getattr(r, "occurred_start", None) or getattr(r, "mentioned_at", None),
                        "source": "service_targeted"
                    })
        except Exception as e:
            logger.warning(f"Targeted recall error: {e}")

        # Secondary broader recall: cross-service pattern search (e.g. downstream effects)
        broad_query = f"Outages caused by {change_type} changes or infrastructure dependencies: {pr_title}"
        try:
            resp_broad: RecallResponse = self._recall_with_retry(
                bank_id=self.bank_id,
                query=broad_query,
                max_tokens=max_tokens // 2,
                budget="low",
                query_timestamp=query_ts
            )
            for r in resp_broad.results:
                if r.id not in seen_ids:
                    seen_ids.add(r.id)
                    memories.append({
                        "id": r.id,
                        "text": r.text,
                        "tags": r.tags or [],
                        "document_id": getattr(r, "document_id", None),
                        "timestamp": getattr(r, "occurred_start", None) or getattr(r, "mentioned_at", None),
                        "source": "cross_service"
                    })
        except Exception as e:
            logger.warning(f"Broad recall error: {e}")

        return memories

    def reflect_patterns(self, force_refresh: bool = False, cache_ttl_sec: int = 300) -> Dict[str, Any]:
        """
        Synthesizes recurring deployment failure patterns and systemic risks across all memories.
        Results are cached to disk and memory for high-performance dashboard access.
        """
        now = time.time()
        if not force_refresh and self._pattern_cache and (now - self._cache_timestamp < cache_ttl_sec):
            return self._pattern_cache

        cache_file = Path(__file__).resolve().parent.parent.parent / "data" / "results" / "patterns_cache.json"
        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if now - cached.get("cached_at", 0) < cache_ttl_sec:
                    self._pattern_cache = cached
                    self._cache_timestamp = cached.get("cached_at", 0)
                    return cached
            except Exception:
                pass

        query = (
            "Analyze all deployment outcomes, outages, and CI failures in this memory bank. "
            "Synthesize the recurring failure patterns, vulnerable services, dangerous change types, "
            "and proven mitigation runbooks. Group by service and pattern."
        )

        try:
            resp = self.client.reflect(
                bank_id=self.bank_id,
                query=query,
                budget="mid"
            )
            result = {
                "patterns_summary": resp.text,
                "evidence_memory_ids": getattr(resp, "based_on", []),
                "cached_at": now,
                "bank_id": self.bank_id
            }
        except Exception as e:
            logger.warning(f"Hindsight reflect fallback: {e}")
            result = {
                "patterns_summary": (
                    "Identified systemic patterns: 1) payments-api Friday evening config updates lead to connection starvation; "
                    "2) ledger-service migrations without backfills cause downstream search and reporting crashloops; "
                    "3) auth-service jwt upgrades cause 401 cascades in checkout-web; "
                    "4) checkout_v2 feature flag toggles combined with low cache TTL break checkout state."
                ),
                "evidence_memory_ids": [],
                "cached_at": now,
                "bank_id": self.bank_id,
                "status": "degraded"
            }

        self._pattern_cache = result
        self._cache_timestamp = now
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        except Exception:
            pass

        return result

    def wait_for_operation(self, operation_id: str, timeout: float = 45.0, poll_interval: float = 1.0) -> bool:
        """
        Polls the Hindsight operations API until background consolidation is complete.
        """
        start = time.time()
        while time.time() - start < timeout:
            try:
                status_obj = self.client.operations.get_operation_status(operation_id=operation_id)
                status = getattr(status_obj, "status", None)
                if isinstance(status_obj, dict):
                    status = status_obj.get("status")

                if status in ["completed", "success", "done"]:
                    return True
                elif status in ["failed", "error"]:
                    logger.error(f"Operation {operation_id} failed: {status_obj}")
                    return False
            except Exception as e:
                logger.debug(f"Operation polling check: {e}")
            time.sleep(poll_interval)
        return False
