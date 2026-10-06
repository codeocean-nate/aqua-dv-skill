# Runbook: the Aqua smoke test (Deployment Verification run by Aqua)

**Goal:** an admin types **`run the smoke test`** into Aqua, walks away, and comes back to a dated report.

The **deployment-verification** skill (`SKILL.md`) makes Aqua run the automated part of the
official Deployment Verification checklist end to end, without stopping to ask:
- CPU and GPU runs on Flex and dedicated machines;
- the cloud workstation lifecycle;
- a Git commit;
- internal and external data assets;
- a pipeline;
- a new release version.

The checklist is the official one: docs.codeocean.com > Admin Guide > Deployment Guide >
Deployment Verification. The few checks that need a person are listed as **manual checks** in
every report.

## 1. What a run does

1. Aqua reads the smoke-test config and makes sure the fixed `DV-smoke-*` objects exist, creating
   any that are missing.
2. It runs the checks:
   - CPU on Flex and dedicated;
   - GPU on Flex and dedicated (if enabled);
   - data assets, including a read of every byte of the external S3 data;
   - workstation launch, /scratch, data asset, result asset, hold, resume and shutdown;
   - Git commit;
   - the pipeline;
   - a new release version (if enabled).
3. It writes `reports/DV-smoke-<YYYYMMDD-HHMM>.md` and `reports/latest.md` in the capsule
   `DV-smoke-report`, and replies with a summary line:
   `SMOKE TEST COMPLETE: 18 PASS, 0 FAIL, 0 BLOCKED, 0 SKIPPED; 9 manual checks open.`

If Aqua can't finish in one turn, its reply ends with `SMOKE TEST INCOMPLETE … Say "continue the
smoke test" to resume.` The CLI driver in §5 does that for you.

**What each run creates:**
- three small data assets (a result asset, a linked S3 asset and a workstation result), tagged `dv-smoke`;
- runs and commits in the fixed capsules;
- one new version of the release target (if releases are enabled).

Aqua never deletes or archives anything.

**Cost per run:**
- CPU runs: less than a cent each.
- Dedicated CPU machine and workstations: a few cents.
- GPU runs (if enabled): cents to tens of cents, depending on the GPU type.

## 2. One-time setup per deployment

| Step | Who | What |
|---|---|---|
| 1 | admin | Turn on **Admin Panel > Aqua > Enable Skills**. Give the tester account rights to create capsules, run Flex, dedicated and GPU machines, create data assets, run pipelines and release capsules. |
| 2 | tester | Install the skill: paste the prompt in §3 into a new Aqua chat. |
| 3 | tester | Run `run the smoke test` once. Aqua creates `DV-smoke-report` with a `config.md` (GPU and releases **off**, Git and pipeline not set), creates the fixed capsules, and runs the CPU, data asset and workstation checks. |
| 4 | tester | Edit `config.md` in `DV-smoke-report`, or tell Aqua, for example "in the smoke test config set gpu: yes and release: yes". See §4. |
| 5 | tester | For Git: make a private repo from [aqua-dv-git-sync-template](https://github.com/codeocean-nate/aqua-dv-git-sync-template) (**Use this template**). Make sure the tester's **Account > Credentials** GitHub token can read and write it. Put its URL in `git_repo`. |
| 6 | admin or tester | Build the smoke-test pipeline once, as below, and put its ID in `pipeline`. |

**Building the pipeline once.** Aqua can't create pipelines or change their credentials.
1. In the Pipeline builder, add one capsule step: `DV-smoke-cpu`, with the argument `--require-data 1`.
2. Add the data assets `DV-smoke-data-internal` and `DV-smoke-data-s3`, which Aqua made at setup, and connect both to the step.
3. In Pipeline Settings:
   - set cache to **off** ("Run without cache");
   - pick an **AWS IAM role** that can read `s3_external`. External data in a pipeline needs a non-default role.
4. Don't use a step capsule that needs a secret. A missing secret makes Aqua's run fail with "missing required credentials".

If github.com is blocked from the deployment, mirror the four repos to an internal Git server and set
`fixtures: <mirror base URL>`. Install the skill from the mirror, or paste `SKILL.md` into a new
skill by hand.

## 3. Install the skill

Paste into a **new** Aqua chat:

```text
Create a new skill by copying the contents of this Git repository: https://github.com/codeocean-nate/aqua-dv-skill

Create an independent skill that is not linked to the Git repository. Copy only the root SKILL.md into the new skill, exactly as it is, and leave out the repository's other files. It's a single skill named deployment-verification; don't rewrite any of it.
- If a skill named deployment-verification is already in your catalog for me, tell me and stop instead of creating a second one.
- If you can't create skills here, stop without creating anything and tell me an admin needs to turn on Admin Panel > Aqua > Enable Skills.
- If you can't read the repository, stop and show me the exact error. Don't write the skill yourself.
When it's done, re-read the new skill's SKILL.md and check it against the SKILL.md rules. Don't ask me any questions. Reply with the skill's name and its full https URL.
```

A skill you create is enabled for you. Others must enable it on their Skills page.

**To update** to a newer version, ask Aqua to replace the skill's `SKILL.md` with the one from this
repository. Give it the skill's UUID: Aqua can't find a skill by its name or by its `/capsule/` URL.

## 4. The config (`config.md` in `DV-smoke-report`)

| Key | Meaning | Default |
|---|---|---|
| `gpu` | `yes` = run the GPU checks every time. Setting it is the admin's approval. | `no` |
| `release` | `yes` = release a **new version** of `release_target` every time. Irreversible; only an admin can delete releases. | `no` |
| `git_repo` | a repo the tester can push to, made from the template | `none` |
| `pipeline` | ID of the smoke-test pipeline | `none` |
| `release_target` | an existing capsule to release new versions of; if `none`, Aqua creates `DV-smoke-release` | `none` |
| `cpu_capsule`, `gpu_capsule`, `git_capsule` | optional existing capsules to use instead of the `DV-smoke-*` ones | `none` |
| `s3_external` | S3 location for the external data checks; use your own private bucket to test private access | public sample genome |
| `cpu_flex`, `cpu_dedicated`, `gpu_flex`, `gpu_dedicated` | machines to run on | the smallest found at setup |
| `data_asset_metadata` | values for any custom metadata fields your data assets require | `none` |

## 5. Run it

**In the web chat.** Type `run the smoke test` and leave. Read the reply, or
`DV-smoke-report > reports/latest.md`, later. If the reply ends with `SMOKE TEST INCOMPLETE`, type
`continue the smoke test`.

**Unattended from the Aqua CLI,** for example nightly or after an upgrade. Use
[`tools/run-smoke-test.sh`](tools/run-smoke-test.sh). It sends `run the smoke test`, repeats
`continue the smoke test` in the same session until Aqua reports `SMOKE TEST COMPLETE` (up to
`MAX_TURNS`), and saves every reply.

```bash
# the Aqua CLI: https://get.codeocean.com/aqua-cli/
export CODEOCEAN_DOMAIN=https://<your-deployment>
export CODEOCEAN_TOKEN=<API key from Account > Access Tokens>
AQ_CHECKS=1 ./tools/run-smoke-test.sh      # exit 0 = complete; replies in ./smoke-<time>/
```

- `AQ_CHECKS=1` also asks two of the three §8 Aqua questions in fresh sessions and saves the
  answers for a person to grade.
- The CLI acts with that API key's permissions.
- Run `aqua -h` only in a shell where `CODEOCEAN_TOKEN` isn't set, because help output shows default
  values.

## 6. Manual checks (not automated; every report lists them)

| Id | What a person does |
|---|---|
| RR-1.1, RR-2.1 | In a new empty capsule with a starter environment, click **Start with Sample Files**, and run it once. |
| GIT-2 | Open `DV-smoke-git`, click **Sync with GitHub**, and check the latest `DV-smoke-…: git check` commit on GitHub. |
| SH-1 to SH-1.2 | Share `DV-smoke-cpu` with a second user as Editor. They click Start editing, append a line and save. The owner clicks Start editing (taking control), appends a line, commits and clicks Finish editing. |
| AQ-1 to AQ-3 | In fresh chats, ask "What Capsule am I currently looking at?" with `DV-smoke-cpu` open, "List my 3 most recently accessed Capsules" and "What is a Data Asset?". |
| version | Note the Code Ocean version from your admin or the release notes. |

## 7. Reading the report

- Each item is PASS, FAIL, BLOCKED or SKIPPED, with its evidence: run numbers, computation IDs, the
  log lines checked (`DV-BANNER`, `DV-CHECK OK`, `DV-GPU-CHECK OK`, `DV-DATA … unreadable=0`), and
  data asset IDs.
- **SETUP** marks fixed objects created during that run. Creating them is also what proves "new
  capsule from a starter environment".
- **Spot-check Aqua's work.** Open two or three of the runs it cites and confirm the log lines are
  there. Aqua is the administrator, not the auditor.

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| Pipeline: "missing required credentials" | A step capsule needs a secret that isn't set. Use a step without secrets (`DV-smoke-cpu`) or set the secret in the pipeline's settings. |
| Pipeline: "Cannot Access External Data Assets" | Select a non-default AWS IAM role in Pipeline Settings. |
| Clone from Git: "Cannot connect to repo" | The GitHub token in Account > Credentials is missing, expired or has no access to the repo. |
| A run or push is blocked by uncommitted changes | Ask Aqua to commit. Capsules it creates start with uncommitted environment changes. |
| Aqua can't edit a capsule | A workstation or another editor holds it. Shut the workstation down, or ask the editor to click Finish editing. |
| `DV-GPU-CHECK FAIL reason=…` | A real failure: no GPU visible, no CUDA, or no PyTorch. Check the GPU starter and machine type. |
| The CLI exits with an error mid-run | Aqua showed an interactive form. Reply in the same session with `Ask in plain text, not a form`, then `continue the smoke test`. |
| The skill is never used | It's disabled for you, or invalid. Check the Skills page, and say "smoke test" in the prompt. |

## 9. Cleanup (optional)

Archive old `DV-smoke-<run>-*` data assets (tag `dv-smoke`) when you like. Keep the fixed
`DV-smoke-*` objects for the next run. Only an admin can delete a release.
