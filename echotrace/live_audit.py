from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RELATIONSHIPS = {
    "root",
    "exact_copy",
    "paraphrase",
    "attributed_derivative",
    "unattributed_derivative",
    "independent",
    "unknown",
}
CLUSTER_TYPES = {"determinate", "ambiguous"}
OBSERVABILITY = {"explicit", "inferable", "indeterminate"}


def validate_live_audit(path: str | Path, require_complete: bool = False) -> dict[str, object]:
    errors: list[str] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    seen_urls: set[str] = set()
    clusters: dict[str, list[dict[str, str]]] = {}
    for line, row in enumerate(rows, start=2):
        for field in (
            "cluster_id",
            "cluster_type",
            "claim",
            "source_url",
            "accessed_at",
            "content_sha256",
            "relationship",
            "observability",
            "author_id",
            "author_verified",
        ):
            if not row.get(field, "").strip():
                errors.append(f"line {line}: missing {field}")
        if row.get("cluster_type") not in CLUSTER_TYPES:
            errors.append(f"line {line}: invalid cluster_type {row.get('cluster_type')!r}")
        if row.get("relationship") not in RELATIONSHIPS:
            errors.append(f"line {line}: invalid relationship {row.get('relationship')!r}")
        if row.get("observability") not in OBSERVABILITY:
            errors.append(f"line {line}: invalid observability {row.get('observability')!r}")
        if row.get("author_verified", "").lower() not in {"yes", "no"}:
            errors.append(f"line {line}: author_verified must be yes or no")
        url = row.get("source_url", "")
        if urlparse(url).scheme not in {"http", "https"}:
            errors.append(f"line {line}: source_url must be HTTP(S)")
        upstream = row.get("upstream_url", "").strip()
        if upstream and urlparse(upstream).scheme not in {"http", "https"}:
            errors.append(f"line {line}: upstream_url must be empty or HTTP(S)")
        if row.get("relationship") == "attributed_derivative" and not upstream:
            errors.append(f"line {line}: attributed_derivative requires upstream_url")
        if url in seen_urls:
            errors.append(f"line {line}: duplicate source_url")
        seen_urls.add(url)
        if not SHA256_RE.fullmatch(row.get("content_sha256", "")):
            errors.append(f"line {line}: content_sha256 must be 64 lowercase hex characters")
        for field in ("accessed_at", "published_at"):
            if row.get(field):
                try:
                    datetime.fromisoformat(row[field].replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"line {line}: invalid {field}")
        clusters.setdefault(row.get("cluster_id", ""), []).append(row)
    cluster_types = Counter(items[0]["cluster_type"] for items in clusters.values() if items)
    if require_complete:
        if len(clusters) != 30:
            errors.append(f"expected 30 clusters, got {len(clusters)}")
        if cluster_types["determinate"] != 20 or cluster_types["ambiguous"] != 10:
            errors.append(
                f"expected 20 determinate and 10 ambiguous clusters, got {dict(cluster_types)}"
            )
        for cluster_id, items in clusters.items():
            cluster_type = items[0]["cluster_type"]
            if len(items) < 3:
                errors.append(f"cluster {cluster_id}: requires at least three inspected sources")
            if len({item["cluster_type"] for item in items}) != 1:
                errors.append(f"cluster {cluster_id}: cluster_type must be consistent")
            if len({item["claim"].strip() for item in items}) != 1:
                errors.append(f"cluster {cluster_id}: focal claim must be identical across rows")
            if cluster_type == "determinate" and not any(
                item["relationship"] == "root" for item in items
            ):
                errors.append(f"cluster {cluster_id}: missing root")
            if cluster_type == "ambiguous" and not any(
                item["relationship"] == "unknown" for item in items
            ):
                errors.append(
                    f"cluster {cluster_id}: ambiguous cluster must contain an unknown relationship"
                )
            if not all(item.get("author_verified", "").lower() == "yes" for item in items):
                errors.append(f"cluster {cluster_id}: contains sources not verified by the author")
            if not all(item.get("evidence_span", "").strip() for item in items):
                errors.append(f"cluster {cluster_id}: evidence_span is required")
    return {
        "valid": not errors,
        "rows": len(rows),
        "clusters": len(clusters),
        "cluster_types": dict(cluster_types),
        "errors": errors,
    }
