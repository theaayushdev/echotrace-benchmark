# Manuscript

`main.tex` uses the official ACL style (`acl.sty`, `acl_natbib.bst`; source commit in
`ACL_STYLE_VERSION.txt`) in preprint mode. All result values are LaTeX macros in `generated/`,
written by `scripts/export_llm_study_results.py` and `scripts/export_v1_paper_results.py`. Do not
edit them by hand.

Build from this directory:

```bash
latexmk -pdf main.tex
```

For anonymous peer review, change `\usepackage[preprint]{acl}` to `\usepackage[review]{acl}`.
