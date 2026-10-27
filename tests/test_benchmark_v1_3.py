import unittest

from scripts.generate_benchmark_v1 import make_case
from scripts.generate_benchmark_v1_3 import redesign_case
import random


class V13DesignTests(unittest.TestCase):
    def test_verbatim_reuse_has_an_observable_upstream_link(self):
        visible, hidden = make_case(random.Random(7), 1, "verbatim_derivative", "supported", "train")
        redesign_case(visible, hidden, random.Random(8), 1)
        docs = {doc["doc_id"]: doc for doc in visible["documents"]}
        for edge in hidden["gold_lineage_edges"]:
            self.assertIn(docs[edge["source_id"]]["url"], docs[edge["derivative_id"]]["outbound_links"])

    def test_unattributed_reports_require_abstention(self):
        visible, hidden = make_case(random.Random(7), 1, "unattributed_multihop", "supported", "train")
        redesign_case(visible, hidden, random.Random(8), 1)
        self.assertEqual(hidden["gold_root_count"], 0)
        self.assertFalse(hidden["gold_families"])
        self.assertFalse(hidden["gold_lineage_edges"])
        self.assertTrue(all(item["action"] == "abstain" for item in hidden["gold_relationships"]))


if __name__ == "__main__":
    unittest.main()
