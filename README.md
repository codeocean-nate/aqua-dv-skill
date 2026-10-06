# aqua-dv-skill

An Aqua skill, **deployment-verification**, that turns Code Ocean's AI assistant into an
unattended **smoke tester** for a deployment. An admin says **"run the smoke test"**, walks away,
and comes back to a dated report. The skill follows the official Deployment Verification
checklist, the test an admin runs after installing or upgrading a deployment.

With the skill enabled, Aqua does the following:
- keeps a fixed set of `DV-smoke-*` test objects, created once from public fixture repositories
  and reused every run;
- runs, without stopping to ask:
  - CPU and GPU Reproducible Runs on Flex and dedicated machines;
  - the cloud workstation lifecycle;
  - a Git commit;
  - internal and external data assets, with a read of every byte;
  - a pipeline;
  - a new release version;
- checks each pass rule against real evidence (log lines, result files, IDs);
- writes `reports/DV-smoke-<time>.md` and `reports/latest.md` in the `DV-smoke-report` capsule;
- lists the few checks that need a person: Start with Sample Files, Git Sync, sharing, the Aqua
  questions, and the version.

GPU checks and releases run only when the admin turns them on in the smoke-test config.

| File | What it is |
|---|---|
| [`SKILL.md`](SKILL.md) | the skill (copy only this file into the Code Ocean skill) |
| [`RUNBOOK.md`](RUNBOOK.md) | one-time setup, the config, running it (web chat or CLI), manual checks, reading the report, troubleshooting |
| [`tools/run-smoke-test.sh`](tools/run-smoke-test.sh) | unattended driver for the Aqua CLI (cron or CI): runs the smoke test to completion and saves every reply |
| [`tools/validate_skill.py`](tools/validate_skill.py) | checks a `SKILL.md` against Aqua's skill rules (`python3 tools/validate_skill.py SKILL.md`) |

Fixture repositories:
- [aqua-dv-cpu-capsule](https://github.com/codeocean-nate/aqua-dv-cpu-capsule)
- [aqua-dv-gpu-capsule](https://github.com/codeocean-nate/aqua-dv-gpu-capsule)
- [aqua-dv-git-sync-template](https://github.com/codeocean-nate/aqua-dv-git-sync-template)

**Start here:** [RUNBOOK.md](RUNBOOK.md).
