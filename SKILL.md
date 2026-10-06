---
name: deployment-verification
description: >-
  Use when an administrator says "run the smoke test", "run the deployment verification",
  "continue the smoke test" or "smoke test report" on this Code Ocean deployment. You run
  the automated part of the official Deployment Verification checklist end to end, unattended:
  Reproducible Runs on CPU and GPU (Flex and dedicated), cloud workstations, a Git commit, data
  assets, a pipeline and a new release version. You use a fixed set of DV-smoke objects that
  you create once and reuse, record evidence for every check, write a dated report, and list
  the checks that need a person. Not for: debugging one user's capsule, general product
  questions, load testing, or any other deployment.
metadata:
  tags: [deployment-verification, smoke-test, administration, testing, upgrade]
  authors:
    - name: Nate Bourgeois
      affiliation: Code Ocean
---

# Deployment verification smoke test, run by Aqua

The admin says **"run the smoke test"** and walks away. You run every automated check below,
without stopping to ask, and leave a dated report.
- **"continue the smoke test"** resumes the latest unfinished run.
- **"smoke test report"** returns the latest report.

The checks come from the official checklist: docs.codeocean.com > Admin Guide > Deployment Guide >
Deployment Verification.

## Rules

1. **Unattended.**
   - Never ask questions, never wait for a person, and never use a form.
   - The only approvals are `gpu` and `release` in the config: the admin's config is their approval.
   - A check that needs a person goes under Manual checks in the report.
   - If a step fails, record FAIL with the exact error and continue with the steps that don't
     depend on it.
2. **Don't stop early.**
   - Keep working until every automated item has a status. Don't pause at section boundaries to
     report.
   - For long operations (runs, workstation hold, resume and shutdown, data asset indexing), check
     the status every 30 seconds for up to 20 minutes each.
   - Commit the report after each section.
   - If you really can't go on in this turn, end with exactly
     `SMOKE TEST INCOMPLETE: next <id>. Say "continue the smoke test" to resume.`
   - When everything has a status, end with exactly
     `SMOKE TEST COMPLETE: <n> PASS, <n> FAIL, <n> BLOCKED, <n> SKIPPED; <n> manual checks open.`
3. **Names.**
   - Fixed objects are `DV-smoke-<part>`.
   - Per-run objects are `DV-smoke-<run>-<part>`, where `<run>` is the UTC start time `YYYYMMDD-HHMM`.
   - Touch only these objects and the ones named in the config.
4. **Never delete or archive anything.** Never change admin settings, credentials or other users'
   objects. Change the config's `gpu`, `release`, `git_repo`, `pipeline` or capsule values only
   when the admin explicitly tells you to.
5. **No secrets in output.** Never run `env`, `printenv`, `set` or `export -p`, and never print
   tokens, keys or credentials. Commands may print only `CO_CAPSULE_ID`, `CO_COMPUTATION_ID`,
   `CO_CPUS` and `CO_MEMORY`.
6. **Pass only on evidence.**
   - PASS means the pass rule is met and you've recorded the run number, the computation ID, the
     named log lines and the result file contents. "Completed" alone is not enough.
   - Otherwise record FAIL (with the error), BLOCKED (with what's missing) or SKIPPED (the config
     turned it off).
7. **Housekeeping.**
   - Use the configured machines, on-demand only.
   - Commit any pending change before a run, and before starting a workstation.
   - If data assets need custom metadata, use the config's `data_asset_metadata`, or `n/a`.

## Config: `config.md` in DV-smoke-report

```text
fixtures: https://github.com/codeocean-nate
gpu: no            # yes = run the GPU checks in every smoke test (the admin's approval)
release: no        # yes = release a NEW VERSION of release_target in every smoke test (irreversible)
git_repo: none     # a repo the tester can push to, made from <fixtures>/aqua-dv-git-sync-template
s3_external: s3://codeocean-public-data/genomes/saccharomyces_genome
pipeline: none     # ID or URL of the smoke-test pipeline; an admin builds it once in the UI
release_target: none   # an existing capsule; if none, you create DV-smoke-release
cpu_capsule: none  # optional existing capsule to use instead of DV-smoke-cpu
gpu_capsule: none  # optional existing GPU capsule to use instead of DV-smoke-gpu
git_capsule: none  # optional existing capsule already linked to git_repo
cpu_flex: auto
cpu_dedicated: auto
gpu_flex: auto
gpu_dedicated: auto
data_asset_metadata: none
ids: {}            # you fill this in: the ID of every fixed object
```

- If `config.md` is missing, create it with these defaults and replace each `auto` with the
  smallest option on this deployment.
- Record `ids` as you create objects. Use an ID from `ids` (or from the config) even if the
  object's name differs.

## Fixed objects (create when missing; reuse every run)

| Object | Create it by | Used for |
|---|---|---|
| DV-smoke-report | a new capsule with no environment | `config.md` and `reports/` |
| DV-smoke-cpu | copying `<fixtures>/aqua-dv-cpu-capsule`, then setting the newest Python CPU starter | CPU runs, data checks, workstations, the pipeline step |
| DV-smoke-gpu (if `gpu: yes`) | copying `<fixtures>/aqua-dv-gpu-capsule`, then setting a PyTorch CUDA starter | GPU runs |
| DV-smoke-git (if `git_repo` is set) | cloning `git_repo` (linked), then setting a CPU starter | Git commit |
| DV-smoke-release (if `release: yes` and there's no `release_target`) | copying `<fixtures>/aqua-dv-cpu-capsule`, then setting the Python starter, a description and an author | releases |
| DV-smoke-data-internal | a result data asset from DV-smoke-cpu's first Flex run | the pipeline's internal input |
| DV-smoke-data-s3 | an external data asset linked to `s3_external`, kept on external storage | the pipeline's external input |

If the config names an existing capsule that wasn't made from a fixture, judge it by its own
signals. A CPU capsule passes if it completes with exit 0 and its banner names it. A GPU capsule
passes if it completes with exit 0 and its log shows an nvidia-smi GPU line and CUDA available
(torch `True`).

When you create a fixed object, record it in the report as SETUP and say that it also proves
"new capsule from a starter" (RR-1, RR-2) or "create a data asset" (DA-1, DA-2). You can't create
pipelines. If `pipeline` is `none`, §5 is BLOCKED. Add a manual check telling the admin to build
the pipeline once:
- Pipeline Builder: one step `DV-smoke-cpu` with the argument `--require-data 1`, and data
  `DV-smoke-data-internal` and `DV-smoke-data-s3`.
- Settings: cache off, and an IAM role that can read `s3_external`.
- Then put its ID in the config.

## Each run, in this order

**0. Preflight**
- Read the config and make sure the fixed objects exist.
- Create `reports/DV-smoke-<run>.md` with every item PENDING.
- Record the deployment URL, your username and the start time.

**1. CPU** (DV-smoke-cpu)
- **RR-1.2:** set `cpu_flex`, then run.
  - Pass: the log has `DV-BANNER capsule=<this capsule's ID>` and `DV-CHECK OK`, and `result.txt` starts with `DV-CHECK OK`.
- **RR-1.3:** set `cpu_dedicated`, then run.
  - Pass: as RR-1.2, and the banner's `cpus` matches the machine.
  - Set `cpu_flex` back and commit.

**2. GPU** (if `gpu: yes`, on DV-smoke-gpu)
- **RR-2.2:** set `gpu_flex`, then run.
  - Pass: exit 0, a `DV-GPU <name>` line, and `DV-GPU-CHECK OK`.
  - Record the GPU name, the driver, and the torch and CUDA versions.
- **RR-2.3:** set `gpu_dedicated`, then run. Pass: as RR-2.2. Set `gpu_flex` back and commit.

**3. Data assets**
- **DA-1:** create `DV-smoke-<run>-cpu-result` from RR-1.2's computation, with the tag `dv-smoke`.
  - Pass: it has `result.txt`, and its provenance is RR-1.2's computation.
- **DA-2:** create `DV-smoke-<run>-s3`, linked to `s3_external` and kept on external storage, with the tag `dv-smoke`.
  - Pass: it is indexed with at least one file.
- **DA-2c:** attach DA-2 to DV-smoke-cpu, commit, run, detach, and commit again.
  - Pass: the log has `DV-FILE` lines under DA-2's mount and `DV-DATA … unreadable=0`.

**4. Workstation** (DV-smoke-cpu; attach DA-1 and commit first; T is a random 8-character token)
- **CW-1:** start a Terminal workstation, or the first IDE available, and run `echo DV-BANNER capsule=$CO_CAPSULE_ID`.
  - Pass: it shows this capsule's ID.
- **CW-1.1:** run `echo "dv-scratch T" > /scratch/DV-scratch.txt; echo "dv-hold T" > /root/DV-hold-marker.txt; df -h /root`.
  - Pass: both files are written. Record the size reported by `df`.
- **CW-1.2:** run `ls -la /data/<DA-1 mount>; cat /data/<DA-1 mount>/result.txt`.
  - Pass: `DV-CHECK OK`.
- **CW-1.3:** run `echo "dv cw-result T" > /results/DV-cw-result.txt`, then create `DV-smoke-<run>-cw-result` from the workstation's computation.
  - Pass: it has that file, and its provenance is the workstation.
- **CW-1.4:** hold the workstation. Pass: its status is on hold.
- **CW-1.5:** resume it, then run `cat /root/DV-hold-marker.txt /scratch/DV-scratch.txt; df -h /root`.
  - Pass: both files read back T, and the size is unchanged.
- **CW-1.6:** shut it down. Start a new workstation and run `cat /scratch/DV-scratch.txt; cat /root/DV-hold-marker.txt || echo marker-gone`, then shut that one down.
  - Pass: the scratch file is kept, `marker-gone` is printed, and no workstation is left.
- Then detach DA-1 and commit.

**5. Git** (if DV-smoke-git exists)
- **GIT-1:** append `DV smoke <run> commit check` to `code/dv-git-check.md`, then commit with the message `DV-smoke-<run>: git check`.
  - Pass: the commit is in the history.
- **GIT-2** (Git Sync) is a manual check.

**6. Pipeline** (if `pipeline` is set)
- **PL-1 / PL-2:** run it and wait.
  - Pass: it completes, every task is Completed with 0 failed and 0 cached, and the results list both the internal asset's files and the S3 files with `unreadable=0`.
  - If a run is refused for missing credentials, record BLOCKED with the exact error. An admin must fix the pipeline's credential settings.

**7. Release** (if `release: yes`)
- **REL-1:** on the release target, append `smoke <run>` to `README.md`, commit, run (pass rule as RR-1.2), then release a **new version**. Never create a second release capsule.
  - Pass: the version list grew by one. Record the new version number and URL.

**8. Wrap-up**
- **W-1:** check that no DV-smoke workstation is running or on hold. Shut down any that are.
- **W-2:** finish the report, copy it to `reports/latest.md`, and commit.
- Reply with:
  - the summary line from rule 2;
  - the checklist with each status and its evidence;
  - the open manual checks;
  - any objects you created.

## Report format

Put a header first:
- the deployment URL, your username, the run ID, the start and end times;
- the `gpu` and `release` settings;
- the summary line.

Then one line per official item:

`- [x] RR-1.2 Reproducible Run on Flex: PASS: run 123, computation <id>, DV-CHECK OK`

The official items, by section:
- **§1 Reproducible Runs:** RR-1 CPU capsule from a starter (SETUP); RR-1.1 sample files (manual); RR-1.2 Flex; RR-1.3 dedicated; RR-2 GPU capsule (SETUP); RR-2.1 sample files (manual); RR-2.2 GPU Flex; RR-2.3 GPU dedicated.
- **§2 Cloud workstations:** CW-1 launch; CW-1.1 /scratch; CW-1.2 internal data asset; CW-1.3 result asset; CW-1.4 hold; CW-1.5 resume; CW-1.6 shut down.
- **§3 Git:** GIT-1 commit; GIT-2 Git Sync (manual).
- **§4 Data assets:** DA-1 internal from a result; DA-2 external.
- **§5 Pipelines:** PL-1 internal data; PL-2 external data.
- **§6 Sharing:** SH-1 share; SH-1.1 the other user edits; SH-1.2 regain control (all manual).
- **§7 Releases:** REL-1 new version.
- **§8 Aqua:** AQ-1, AQ-2, AQ-3 (manual: someone asks these in fresh chats).

**Manual checks**, listed in every report, each with one line of instructions:
- RR-1.1 / RR-2.1: in a new empty capsule with a starter, click Start with Sample Files.
- GIT-2: open DV-smoke-git, click Sync with GitHub, and check the commit on GitHub.
- SH-1 to SH-1.2: share DV-smoke-cpu as Editor; the other user edits and saves; the owner takes control, edits and commits.
- AQ-1 to AQ-3: in fresh chats, ask "What Capsule am I currently looking at?" with DV-smoke-cpu open, "List my 3 most recently accessed Capsules" and "What is a Data Asset?".
- The Code Ocean version: from the admin.
