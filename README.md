# aqua-dv-skill

An Aqua skill, **deployment-verification**, that makes Code Ocean's AI assistant the
**administrator** of the official Deployment Verification checklist. That's the test an admin runs
after installing or upgrading a deployment. It covers Reproducible Runs on CPU and GPU, cloud
workstations, Git, data assets, pipelines, sharing, releases and Aqua itself.

With the skill enabled, Aqua does the following:
- creates the test capsules from three public fixture repositories;
- runs every step it has a tool for, and checks each pass rule against real evidence (log lines,
  result files, IDs);
- keeps a checklist report in a `DV-<date>-report` capsule;
- stops for approval before GPU runs and releases;
- tells the operator exactly what to click for the few steps it can't do itself. Those are Start with
  Sample Files, Git Sync, pipeline settings, sharing, and the Aqua questions, which need a fresh chat.

| File | What it is |
|---|---|
| [`SKILL.md`](SKILL.md) | the skill (copy only this file into the Code Ocean skill) |
| [`RUNBOOK.md`](RUNBOOK.md) | step-by-step guide for the operator: prerequisites, install, prompts, operator steps, results, CLI use |
| [`tools/validate_skill.py`](tools/validate_skill.py) | checks a `SKILL.md` against Aqua's skill rules (`python3 tools/validate_skill.py SKILL.md`) |

Fixture repositories:
- [aqua-dv-cpu-capsule](https://github.com/codeocean-nate/aqua-dv-cpu-capsule)
- [aqua-dv-gpu-capsule](https://github.com/codeocean-nate/aqua-dv-gpu-capsule)
- [aqua-dv-git-sync-template](https://github.com/codeocean-nate/aqua-dv-git-sync-template)

**Start here:** [RUNBOOK.md](RUNBOOK.md).
