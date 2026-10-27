import random
import unittest

import scripts.generate_benchmark_v1 as base
from scripts.generate_benchmark_v1 import make_case
from scripts.generate_benchmark_v1_3 import redesign_case
from scripts.generate_benchmark_v1_4 import EXTRA_TOPICS, SEEN_STYLES, UNSEEN_STYLES, rewrite_prose


class V14ProseTests(unittest.TestCase):
    def setUp(self):
        self.topics = base.TOPICS
        base.TOPICS = self.topics + EXTRA_TOPICS

    def tearDown(self):
        base.TOPICS = self.topics

    def build(self, condition, held_out=False, world=40):
        visible, hidden = make_case(random.Random(3), world, condition, "supported", "test")
        redesign_case(visible, hidden, random.Random(4), world)
        style = rewrite_prose(visible, hidden, random.Random(5), world, held_out)
        return visible, hidden, style

    def test_style_banks_are_disjoint(self):
        self.assertFalse(set(SEEN_STYLES) & set(UNSEEN_STYLES))

    def test_heldout_uses_only_unseen_styles(self):
        for condition in ("single_origin", "shared_dataset", "ambiguous_provenance"):
            _, _, style = self.build(condition, held_out=True)
            self.assertIn(style, UNSEEN_STYLES)

    def test_derivatives_keep_visible_upstream_url(self):
        visible, hidden, _ = self.build("attributed_paraphrase")
        docs = {d["doc_id"]: d for d in visible["documents"]}
        for edge in hidden["gold_lineage_edges"]:
            self.assertIn(docs[edge["source_id"]]["url"], docs[edge["derivative_id"]]["text"])

    def test_shared_dataset_names_are_visible(self):
        visible, hidden, _ = self.build("shared_dataset")
        ids = hidden["gold_claim"]["relevant_doc_ids"]
        docs = {d["doc_id"]: d for d in visible["documents"]}
        self.assertIn("DS-040-A", docs[ids[0]]["text"])
        self.assertIn("DS-040-A", docs[ids[1]]["text"])

    def test_no_hidden_labels_in_public_text(self):
        visible, _, _ = self.build("single_origin")
        for doc in visible["documents"]:
            self.assertNotIn("single_origin", doc["text"])


if __name__ == "__main__":
    unittest.main()
