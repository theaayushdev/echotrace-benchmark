# EchoBench data card

EchoBench v0.1 contains 400 generated cases from 80 fictional micro-worlds. It is intended to
measure source-dependence reasoning, not factual knowledge about real people or organizations.

## Current status

The checked-in release is **generated, not human-verified**. The `review_status` field must not be
changed until two independent reviewers complete `annotations/reviews.csv` and an additional reviewer adjudicates every
disagreement. These are proposed review roles; no completed reviews or recruited reviewers are claimed. Papers and reports must describe this version accurately.

## Splits

Micro-worlds are disjoint across 240 training, 60 validation, and 100 test cases. All five matched
conditions from a micro-world remain in one split.

## Limitations

Generated prose is cleaner than the open web, English-only, and based on explicit publication
dates. The live-web audit is required before claiming external validity.

