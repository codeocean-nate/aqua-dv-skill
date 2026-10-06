#!/usr/bin/env python3
"""Validate an Aqua SKILL.md against the platform's hard rules, and optionally
against what a *reference skill* for a specific capsule must contain.

Hard rules (as enforced by the platform; see docs/aqua-skill-format.md):
  name required, slug [A-Za-z0-9-], <= 64 chars; description required, <= 1,024;
  body <= 20,000; frontmatter valid YAML; tags/authors under `metadata:`;
  authors are objects with `name`.

Usage:
  validate_skill.py SKILL.md                      # hard rules only
  validate_skill.py SKILL.md --expect exp.json    # + reference checks
  add --json for machine-readable output. Exit 1 if any hard rule or expectation fails.

exp.json example (every key is optional):
  {"capsule": {"id": "<capsule-uuid>", "slug": "1234567"},
   "data_assets": [{"id": "<data-asset-uuid>", "mount": "my-dataset"}],
   "params": {"--gene": "TP53", "--no-batch": null},
   "forbidden": ["--impute-method"],
   "domain": "https://codeocean.example.com"}

  capsule      the skill must contain the capsule ID and a full https URL to its slug
  data_assets  each ID must appear (with a full URL) and each mount must be mentioned
  params       each flag must be documented; a non-null default must appear on the same line
  forbidden    stale strings that must not be presented as valid (a line that calls them
               out as stale, renamed or README-only is fine)
  domain       warn if the capsule URL doesn't use this deployment's domain
"""
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: python3 -m pip install pyyaml")

NAME_RE = re.compile(r"[A-Za-z0-9-]+")
LIMITS = {"name": 64, "description": 1024, "body": 20000}
BODY_TARGET = 8000
MAX_CODE_LINES = 15


def split_frontmatter(text):
    if not text.startswith("---"):
        return None, text
    m = re.match(r"^---[ \t]*\r?\n(?:(.*?)\r?\n)?---[ \t]*(?:\r?\n|$)(.*)$", text, re.S)
    if not m:
        return None, text
    return m.group(1) or "", m.group(2)


def check(text, expect=None):
    errors, warnings, info = [], [], {"body_chars": len(text)}
    if text.startswith("\ufeff"):
        errors.append("file starts with a UTF-8 byte-order mark (BOM); save it without one")
        return errors, warnings, info
    fm_text, body = split_frontmatter(text)
    info["body_chars"] = len(body)
    if fm_text is None:
        errors.append("no YAML frontmatter delimited by --- lines at the top of the file")
        return errors, warnings, info
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        errors.append(f"frontmatter is not valid YAML: {e}")
        return errors, warnings, info
    if fm is None:
        fm = {}
    if not isinstance(fm, dict):
        errors.append("frontmatter must be a YAML mapping")
        return errors, warnings, info

    name, desc = fm.get("name"), fm.get("description")
    if name is None or name == "":
        errors.append("missing `name`")
    elif not isinstance(name, str):
        errors.append(f"`name` must be a string (YAML parsed {name!r} as {type(name).__name__}; quote it)")
    elif not NAME_RE.fullmatch(name):
        errors.append(f"`name` must be letters, digits and hyphens only: {name!r}")
    elif len(name) > LIMITS["name"]:
        errors.append(f"`name` is {len(name)} chars (max {LIMITS['name']})")
    if not desc:
        errors.append("missing `description`")
    elif not isinstance(desc, str):
        errors.append("`description` must be a string")
    else:
        info["description_chars"] = len(desc)
        if len(desc) > LIMITS["description"]:
            errors.append(f"`description` is {len(desc)} chars (max {LIMITS['description']})")
        if not desc.lstrip().lower().startswith("use when"):
            warnings.append("description should start with 'Use when …' (it is the activation trigger)")
    if len(body) > LIMITS["body"]:
        errors.append(f"body is {len(body)} chars (max {LIMITS['body']})")
    elif len(body) > BODY_TARGET:
        warnings.append(f"body is {len(body)} chars (target < {BODY_TARGET})")

    extra = sorted(set(fm) - {"name", "description", "metadata"})
    if extra:
        warnings.append(f"top-level keys ignored by the platform (move under metadata): {extra}")
    meta = fm.get("metadata") or {}
    if not isinstance(meta, dict):
        errors.append("`metadata` must be a mapping")
        meta = {}
    authors = meta.get("authors")
    if authors is None or authors == []:
        warnings.append("no metadata.authors (release is blocked without authors)")
    elif not isinstance(authors, list) or not all(isinstance(a, dict) and a.get("name") for a in authors):
        errors.append("metadata.authors must be a list of objects with `name` (bare strings break parsing)")
    tags = meta.get("tags")
    if tags is not None and not isinstance(tags, list):
        warnings.append("metadata.tags should be a list")
    info["tags"] = tags or []

    # Long inline code blocks (fenced blocks inside the body); markdown fences are templates
    fence = r"^([ \t]*)(`{3,}|~{3,})([^\n]*)\n(.*?)^\1\2[`~]*[ \t]*$"
    for i, block in enumerate(re.findall(fence, body, re.S | re.M)):
        n = block[3].count("\n")
        if n > MAX_CODE_LINES and block[2].strip().lower() not in ("markdown", "md"):
            warnings.append(f"code block #{i + 1} is {n} lines (inline code bloats skills; link to the file)")

    if expect:
        errors += check_expectations(text, body, fm, expect, warnings)
    return errors, warnings, info


def _value_re(default):
    """Match a default as a whole value: '3' must not match '30' or '3.5'."""
    d = json.dumps(default) if isinstance(default, bool) else str(default)
    return re.compile(rf"(?<![\w.]){re.escape(d)}(?!\w|\.\d)", re.I)


def check_expectations(text, body, fm, expect, warnings):
    errs = []
    domain = (expect.get("domain") or "").rstrip("/")
    cap = expect.get("capsule") or {}
    if cap.get("id") and cap["id"] not in text:
        errs.append(f"capsule ID {cap['id']} not found")
    if cap.get("slug"):
        slug = cap["slug"]
        full = re.compile(rf"https://[^\s)|>]+/capsule/{slug}\b")
        if not full.search(text):
            errs.append(f"no full https URL to capsule slug {slug}")
        bare = [m.start() for m in re.finditer(rf"(?<![\w.:/-])/capsule/{slug}\b", text)]
        if bare:
            warnings.append(f"bare /capsule/{slug} path used {len(bare)}x without a domain")
        if domain and f"{domain}/capsule/{slug}" not in text:
            warnings.append(f"capsule URL does not use the expected domain {domain}")
        tags = ((fm.get("metadata") or {}).get("tags")) or []
        if f"capsule-{slug}" not in [str(t) for t in tags]:
            warnings.append(f"metadata.tags lacks capsule-{slug}")
    for da in expect.get("data_assets", []):
        if da.get("id") and da["id"] not in text:
            errs.append(f"data asset ID {da['id']} ({da.get('mount', '?')}) not found")
        elif da.get("id") and not re.search(rf"https://[^\s)|>]+/data-assets/{da['id']}", text):
            warnings.append(f"data asset {da['id']} has no full https URL")
        if da.get("mount") and da["mount"] not in text:
            errs.append(f"mount {da['mount']} not mentioned")
    for flag, default in (expect.get("params") or {}).items():
        lines = [ln for ln in body.splitlines() if re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", ln)]
        if not lines:
            errs.append(f"parameter {flag} not documented")
        elif default is not None and not any(_value_re(default).search(ln) for ln in lines):
            errs.append(f"parameter {flag}: default {default!r} not stated next to it")
    # A forbidden (stale) string only counts when used as if valid; a line that calls it
    # out as stale/renamed/README-only is the behavior we want.
    callout = re.compile(r"\b(readme|stale|renamed|instead|outdated|wrong|not|cannot|can.t|no longer|"
                         r"deprecated|removed|doesn.t|does not|old)\b", re.I)
    lines = text.splitlines()
    for s in expect.get("forbidden", []):
        # look at the hit line and the two before it: callouts often wrap across lines
        uses = [ln for i, ln in enumerate(lines)
                if re.search(rf"(?<![\w-]){re.escape(s)}(?![\w-])", ln)
                and not callout.search(" ".join(lines[max(0, i - 2):i + 1]))]
        if uses:
            errs.append(f"stale string used as valid: {s} (e.g. {uses[0].strip()[:80]!r})")
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skill_md")
    ap.add_argument("--expect")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        text = open(a.skill_md, encoding="utf-8").read()
        expect = json.load(open(a.expect, encoding="utf-8")) if a.expect else None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        sys.exit(f"cannot read input: {e}")
    errors, warnings, info = check(text, expect)
    if a.json:
        print(json.dumps({"file": a.skill_md, "valid": not errors, "errors": errors,
                          "warnings": warnings, **info}, indent=2))
    else:
        print(f"{a.skill_md}: {'VALID' if not errors else 'INVALID'}  "
              f"(body {info.get('body_chars')} chars, description {info.get('description_chars', '-')} chars)")
        for e in errors:
            print(f"  ERROR   {e}")
        for w in warnings:
            print(f"  warning {w}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
