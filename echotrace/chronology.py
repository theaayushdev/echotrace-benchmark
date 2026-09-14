"""Publication chronology checks and deterministic repair of synthetic timestamps."""
from copy import deepcopy
from datetime import datetime, timedelta


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def reversed_edges(public, gold):
    dates = {d["doc_id"]: timestamp(d["published_at"]) for d in public["documents"]}
    return [e for e in gold["gold_lineage_edges"]
            if dates[e["source_id"]] > dates[e["derivative_id"]]]


def repair_dates(public, gold):
    """Move derivatives forward as needed without changing texts or provenance.

    This is appropriate while constructing a new benchmark release.  It must not
    be used to alter an already-frozen evaluation release.
    """
    result = deepcopy(public)
    documents = {d["doc_id"]: d for d in result["documents"]}
    parents = {doc: set() for doc in documents}
    for edge in gold["gold_lineage_edges"]:
        source, derivative = edge["source_id"], edge["derivative_id"]
        if source not in documents or derivative not in documents:
            raise ValueError("Lineage references an unknown document")
        parents[derivative].add(source)
    done = set()
    while len(done) < len(documents):
        ready = sorted(doc for doc in documents if doc not in done and parents[doc] <= done)
        if not ready:
            raise ValueError("Cyclic lineage cannot be assigned causal publication dates")
        for doc in ready:
            original = timestamp(documents[doc]["published_at"])
            date = max([original] + [timestamp(documents[p]["published_at"]) + timedelta(days=1)
                                    for p in parents[doc]])
            if date != original:
                documents[doc]["published_at"] = date.isoformat()
            done.add(doc)
    return result


# Retained for the already-published development-sample script.
repair_development_dates = repair_dates
