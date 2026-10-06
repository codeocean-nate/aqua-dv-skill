---
name: deployment-verification
description: >-
  Use when an administrator asks you to run, continue or report on the Code Ocean
  Deployment Verification checklist on this deployment: the post-install or post-upgrade
  test of Reproducible Runs on CPU and GPU, cloud workstations, Git, data assets, pipelines,
  sharing, releases and Aqua. You act as the test administrator. You create the test capsules
  from the public aqua-dv fixture repositories, run each step, check its pass rule, record the
  evidence in a checklist report, and give the operator exact instructions for the few steps
  that need a person. Not for: debugging one user's capsule, general product questions,
  performance or load testing, or testing a deployment other than the one you are on.
metadata:
  tags: [deployment-verification, administration, testing, upgrade]
  authors:
    - name: Nate Bourgeois
      affiliation: Code Ocean
---

# Deployment verification, administered by Aqua

You run the official Deployment Verification checklist (docs.codeocean.com > Admin Guide >
Deployment Guide > Deployment Verification) on this deployment. Do every step you have a tool for.
For the rest, give the operator numbered instructions, then wait for their reply.

## Rules

1. **Names.** Name everything you create `DV-<date>-<part>`, with today's UTC date as YYYYMMDD
   (for example `DV-20261006-cpu`). Work only on objects with that prefix, or objects the operator
   names. If one already exists with that name, reuse it.
2. **Never delete or archive anything.** Never change admin settings, credentials, or other users'
   capsules and pipelines.
3. **No secrets in output.** Never run `env`, `printenv`, `set` or `export -p`, and never print tokens,
   keys or credentials. Commands may print only `CO_CAPSULE_ID`, `CO_COMPUTATION_ID`, `CO_CPUS` and
   `CO_MEMORY`. If a log you read contains a credential, don't repeat it.
4. **Gates.** Stop before each step marked GATE. One gate can cover several steps, as noted at the gate. Write one plain-text line:
   `GATE <id>: <what you will do and what it costs>. Reply "GO <id>" or "SKIP <id>".`
   Then end your turn. A step is approved only by `GO <id>` for that id, or by
   `pre-approved: <ids>` in the operator's messages. Never use an interactive form, widget or
   multiple-choice question. Ask in plain text, so the test also works from the Aqua CLI.
5. **Operator steps.** For a step marked OPERATOR, give numbered click-by-click instructions,
   then end your turn and wait for the operator to reply `DONE <id>` (with any details you
   asked for). Afterwards, verify what you can yourself.
6. **Pass only on evidence.** A step is PASS only when its pass rule is met and you have recorded
   the evidence: run number and computation ID, the named log lines, and result file contents.
   "Completed" alone is not enough. Otherwise mark it FAIL with the exact error, BLOCKED with what
   is missing, or SKIPPED (the operator chose to). Then carry on with the steps that don't depend
   on it.
7. **Keep going.** Work through the sections in order and don't stop between steps unless a gate,
   an operator step or a failure needs a decision. After each section, update the report and
   reply with a short status.
8. Prefer the smallest machines and on-demand (not spot). Commit any uncommitted changes before a
   run.

## Inputs

Read these from the operator's messages. If one is missing, use the default and say so; don't ask
for it.

| Input | Meaning | Default |
|---|---|---|
| `fixtures` | base URL of the fixture repos (a mirror, if github.com is blocked) | `https://github.com/codeocean-nate` |
| `gpu` | run the GPU steps | gate RR-2 |
| `git_repo` | HTTPS URL of a repo the tester can push to, made from `<fixtures>/aqua-dv-git-sync-template` | §3 BLOCKED until given |
| `s3_external` | S3 location for the external data asset, `s3://bucket/path` | `s3://codeocean-public-data/genomes/saccharomyces_genome` (public, about 12 MB) |
| `s3_private` | the S3 location is a private bucket | `no` |
| `pipeline` | ID or URL of an existing pipeline to run | §5 BLOCKED until given |
| `second_user` | person who will edit during the sharing test | §6 BLOCKED until given |
| `release` | run the release steps | gate REL-1 |

## Report

At the start, create a capsule `DV-<date>-report` that needs no environment. Write `dv-report.md`
in it: a header with the deployment URL, your username, the date and the operator, then one line
per checklist item (ids below), in the form `- [ ] RR-1.2 Reproducible Run on Flex: PENDING`.
When an item finishes, change it to `- [x] … : PASS: <evidence>`, or to `- [ ] … : FAIL|BLOCKED|SKIPPED: <reason>`.
Commit the report after every section. If you can't create the report capsule, keep the report
in your replies instead.

## Steps

### 0 Preflight
- P-1: record the deployment URL and your username. OPERATOR: record the Code Ocean version, from the admin or the release notes, since you have no tool for it.
- P-2: find and record exact names for:
  - the newest Python CPU starter environment and a PyTorch CUDA GPU starter environment;
  - the smallest Flex CPU tier and the smallest dedicated CPU machine;
  - a Flex GPU tier and the smallest dedicated GPU machine.
- P-3: create the report capsule.

### 1 Reproducible Runs
- **RR-1:** create `DV-<date>-cpu` by copying (not linking) `<fixtures>/aqua-dv-cpu-capsule`.
  - Set its environment to the Python CPU starter, then commit.
  - Pass: `code/run` and `code/dv_check.py` are present, the environment is the starter, and nothing is uncommitted.
- **RR-1.1 (OPERATOR, sample files):** create an empty capsule `DV-<date>-sample` with the Python CPU starter.
  - The operator opens it and clicks **Start with Sample Files**.
  - After `DONE RR-1.1`, list its files and run it once on Flex.
  - Pass: the sample files are there and the run completes.
- **RR-1.2:** set `DV-<date>-cpu` to the smallest Flex CPU tier and start a Reproducible Run. Wait for it to finish.
  - Pass: the log has `DV-BANNER capsule=<this capsule's id>` and `DV-CHECK OK`, and `result.txt` starts with `DV-CHECK OK`.
  - Record the run number, computation ID and duration.
- **RR-1.3:** set the smallest dedicated CPU machine and run again.
  - Pass: the same as RR-1.2, and the banner's `cpus` matches the machine.
  - Then set the capsule back to Flex and commit.
- **RR-2 (GATE; covers RR-2 to RR-2.3):** create `DV-<date>-gpu` by copying `<fixtures>/aqua-dv-gpu-capsule`.
  - Set the PyTorch GPU starter, then commit.
- **RR-2.1 (OPERATOR, optional):** sample files, as in RR-1.1 but with the GPU starter, in `DV-<date>-gpu-sample`.
- **RR-2.2:** run on a Flex GPU tier.
  - Pass: exit 0, a `DV-GPU <name>` line, and `DV-GPU-CHECK OK`.
  - Record the GPU name, the driver, and the torch and CUDA versions.
- **RR-2.3:** run on the smallest dedicated GPU machine. Pass: the same as RR-2.2.

### 4 Data assets (before section 2, which needs DA-1)
- **DA-1:** create an internal result data asset `DV-<date>-cpu-result` from RR-1.2's computation, with the tag `deployment-verification`.
  - Pass: it contains `result.txt`, and its provenance names RR-1.2's computation.
- **DA-2:** create an external data asset `DV-<date>-s3-linked` from `s3_external`, kept on external storage (linked, not copied).
  - Pass: it is indexed with at least one file.
- **DA-2c:** attach DA-2 to `DV-<date>-cpu`, commit, and run.
  - Pass: the log has `DV-FILE` lines under DA-2's mount and `DV-DATA … unreadable=0`. That means every byte was read.
  - Then detach DA-2 and commit.
  - If `s3_private` is `yes` and the read fails, record FAIL with the error. The deployment's access to that bucket isn't working.

### 2 Cloud workstations (on DV-<date>-cpu)
- **CW-0:** attach DA-1 to `DV-<date>-cpu` and commit before starting. That avoids an uncommitted-change block later.
- **CW-1:** start a Terminal workstation, or the first IDE available, and run `echo DV-BANNER capsule=$CO_CAPSULE_ID computation=$CO_COMPUTATION_ID`.
  - Pass: it shows this capsule's ID. Record the computation ID.
- **CW-1.1:** pick a random 8-character token T, then run:
  `echo "dv-scratch T" > /scratch/DV-scratch.txt; echo "dv-hold T" > /root/DV-hold-marker.txt; ls -la /scratch; df -h /root`
  - Pass: both files are written. Record the size reported by `df`.
- **CW-1.2:** run `ls -la /data/<DA-1 mount>; cat /data/<DA-1 mount>/result.txt`.
  - Pass: DA-1's files are listed and `result.txt` starts with `DV-CHECK OK`.
- **CW-1.3:** run `echo "dv cw-result T" > /results/DV-cw-result.txt`, then create a result data asset `DV-<date>-cw-result` from the workstation's computation.
  - Pass: it contains `DV-cw-result.txt`, and its provenance is the workstation's computation.
- **CW-1.4:** hold the workstation. Pass: its status shows it on hold.
- **CW-1.5:** resume it, then run `cat /root/DV-hold-marker.txt /scratch/DV-scratch.txt; df -h /root`.
  - Pass: the marker reads `dv-hold T`, the scratch file is still there, and the disk size is unchanged.
- **CW-1.6:** shut it down. Then start a new workstation and run `cat /scratch/DV-scratch.txt; cat /root/DV-hold-marker.txt || echo marker-gone`, then shut that one down too.
  - Pass: the scratch file was kept, `marker-gone` was printed, and no workstation is left running.

### 3 Git (needs git_repo)
- **GIT-1:** create `DV-<date>-git` by cloning (linked) `git_repo`, set a CPU starter environment, and commit.
  - Append the line `DV <UTC time> commit check` to `code/dv-git-check.md`, then commit with the message `DV-<date>: git check`.
  - Pass: the commit appears in the capsule's history.
  - If the clone fails, record FAIL with the exact error. A likely cause is the GitHub credential in Account > Credentials.
- **GIT-2 (OPERATOR):** the operator opens `DV-<date>-git`, presses **Sync with GitHub**, and replies `DONE GIT-2` with the commit SHA as shown on GitHub.
  - Pass: GitHub has the commit `DV-<date>: git check`.

### 5 Pipelines (needs pipeline)
- **PL-0 (OPERATOR):** the operator sets these in the pipeline's settings, since you can't change them:
  - cache off ("Run without cache");
  - for PL-2, an AWS IAM role that can read `s3_external`;
  - with only internal data attached, for example DA-1.
  - Optional: if the operator wants a fresh pipeline, they build a one-step pipeline in the UI with `DV-<date>-cpu` as the step and pass `--require-data 1`.
- **PL-1:** run the pipeline and wait for it.
  - Pass: it completes, every task is Completed with 0 failed and 0 cached, and the step's results show the data files were read: `data_manifest.tsv` from this fixture, or the step's own output.
  - Record the run number and the task IDs.
- **PL-2 (OPERATOR, then you):** the operator attaches DA-2 and selects the IAM role. You run the pipeline.
  - Pass: as in PL-1, and the results show DA-2's files.

### 6 Sharing (needs second_user)
- **SH-0:** create `code/DV-sharing-check.md` in `DV-<date>-cpu` with the line `DV sharing check <UTC>`, then commit.
- **SH-1 (OPERATOR):** share `DV-<date>-cpu` with `second_user` as Editor, with Share Assets off. You can't share.
- **SH-1.1 (OPERATOR + second user):** the second user clicks Start editing, appends `edited by <their name> <UTC>` to the file, saves, and leaves the tab open.
- **SH-1.2 (OPERATOR):** the owner clicks Start editing (which takes control), appends `edited by owner <UTC>`, commits, and clicks Finish editing.
  - After `DONE SH-1.2`, read the file at the latest commit.
  - Pass: both edits are present.

### 7 Releases (GATE REL-1; covers REL-1 and REL-1b)
- **REL-0:** make sure `DV-<date>-cpu` is ready to release:
  - it has a description and an author (set them and commit if not);
  - nothing is uncommitted;
  - its latest run succeeded after the last change.
- **REL-1 (GATE, irreversible):** release `DV-<date>-cpu`. Pass: a release capsule exists at version 1. Record its URL.
- **REL-1b:** append a line to `README.md` and commit, run (pass rule as in RR-1.2), then release again.
  - Pass: the release lists versions 1 and 2.

### 8 Aqua (OPERATOR, fresh chats; don't grade yourself)
The operator asks each question in a new chat, without mentioning this skill:
1. With `DV-<date>-cpu` open: "What Capsule am I currently looking at?"
2. "List my 3 most recently accessed Capsules"
3. "What is a Data Asset?"

Give the operator these pass rules:
1. The answer names `DV-<date>-cpu`.
2. It matches My Capsules sorted by Last Accessed.
3. It covers internal vs external, attaching to capsules and pipelines, the read-only mount under `/data`, and results becoming data assets, and says nothing false.

### Wrap-up
- **W-1:** check that no `DV-` workstation is running or on hold. Shut down any that are.
- **W-2:** final report. Commit `dv-report.md` and reply with:
  - the full checklist with each status and its evidence;
  - every object you created, with its URL;
  - the operator steps still open.

  Don't delete anything; the operator archives later.

## Checklist ids (the 28 official items)
- **§1 Reproducible Runs:** RR-1 CPU capsule; RR-1.1 sample files; RR-1.2 Flex run; RR-1.3 dedicated run; RR-2 GPU capsule; RR-2.1 sample files; RR-2.2 GPU Flex run; RR-2.3 GPU dedicated run.
- **§2 Cloud workstations:** CW-1 launch; CW-1.1 /scratch; CW-1.2 attach and browse an internal data asset; CW-1.3 result data asset; CW-1.4 hold; CW-1.5 resume; CW-1.6 shut down.
- **§3 Git:** GIT-1 commit; GIT-2 Git Sync.
- **§4 Data assets:** DA-1 internal from a result; DA-2 external.
- **§5 Pipelines:** PL-1 internal data; PL-2 external data.
- **§6 Sharing:** SH-1 share; SH-1.1 the other user edits; SH-1.2 regain control.
- **§7 Releases:** REL-1 release a new version (with REL-1b).
- **§8 Aqua:** AQ-1, AQ-2, AQ-3.
