# Runbook: Deployment Verification with Aqua as the administrator

This runbook is for the person who runs the test, called the **operator**. The **deployment-verification**
skill (`SKILL.md`) makes Aqua the administrator:
- Aqua creates the test capsules from public fixture repositories, runs every step it can, checks
  each pass rule, records the evidence and keeps a checklist report.
- You approve the costly or irreversible steps and do the few clicks Aqua has no tool for.

The checklist is the official one: docs.codeocean.com > Admin Guide > Deployment Guide >
Deployment Verification (8 sections, 28 items).

## 1. Before you start

| Need | Why | Who arranges it |
|---|---|---|
| A tester account that can create capsules, run Flex, dedicated and GPU machines, create data assets, run pipelines and release capsules | Aqua acts as this user | admin |
| **Admin Panel > Aqua > Enable Skills** turned on | the skill must be in Aqua's catalog | admin |
| The deployment can reach `github.com` | Aqua copies the fixtures and the skill from GitHub. If it can't, mirror the four repositories internally and pass `fixtures: <mirror base URL>` | admin / network |
| A **second user** | §6 Sharing needs someone else to edit the capsule | operator |
| A Git repository the tester can push to, made from [aqua-dv-git-sync-template](https://github.com/codeocean-nate/aqua-dv-git-sync-template) (**Use this template**; private is fine) | §3 Git commit and Git Sync | operator |
| A GitHub credential in the tester's **Account > Credentials** that can read and write that repository | Clone from Git and Git Sync use it | tester |
| An existing pipeline the tester may run | §5 Pipelines | operator |
| An AWS IAM role, selectable in Pipeline Settings, that can read the external S3 data | §5.2 external data in a pipeline | admin |
| An S3 location for the external data asset. The default is the public sample `s3://codeocean-public-data/genomes/saccharomyces_genome`; use your own private bucket to test private access | §4.2 | operator |

**Cost:**
- Every CPU run takes seconds and costs less than a cent on Flex.
- The dedicated CPU machine and the cloud workstations cost a few cents.
- The two GPU runs cost cents to tens of cents, depending on the GPU type.
- Aqua asks before each GPU step and before releasing.

## 2. The four repositories

| Repository | Used for |
|---|---|
| [aqua-dv-skill](https://github.com/codeocean-nate/aqua-dv-skill) | this runbook and `SKILL.md` |
| [aqua-dv-cpu-capsule](https://github.com/codeocean-nate/aqua-dv-cpu-capsule) | CPU runs, data asset reads, cloud workstations, the pipeline step, releases |
| [aqua-dv-gpu-capsule](https://github.com/codeocean-nate/aqua-dv-gpu-capsule) | GPU runs on Flex and dedicated machines |
| [aqua-dv-git-sync-template](https://github.com/codeocean-nate/aqua-dv-git-sync-template) | template for your writable Git repository |

The fixtures print nothing secret and need no network. The CPU check reads every byte of every file
under `/data` and prints its SHA-256, so data access is proven, not just listed.

## 3. Install the skill (once per deployment)

Paste this into a **new** Aqua chat:

```text
Create a new skill by copying the contents of this Git repository: https://github.com/codeocean-nate/aqua-dv-skill

Create an independent skill that is not linked to the Git repository. Copy only the root SKILL.md into the new skill, exactly as it is, and leave out the repository's other files. It's a single skill named deployment-verification; don't rewrite any of it.
- If a skill named deployment-verification is already in your catalog for me, tell me and stop instead of creating a second one.
- If you can't create skills here, stop without creating anything and tell me an admin needs to turn on Admin Panel > Aqua > Enable Skills.
- If you can't read the repository, stop and show me the exact error. Don't write the skill yourself.
When it's done, re-read the new skill's SKILL.md and check it against the SKILL.md rules. Don't ask me any questions. Reply with the skill's name and its full https URL.
```

Check that the skill shows as **enabled** on the Skills page. A skill you create is enabled for you;
a skill someone shares with you stays disabled until you enable it.

## 4. Start the test

In a **new** chat (keep using this chat for the whole test), paste the following, after filling in
the values:

```text
Run the Code Ocean deployment verification test on this deployment, using the deployment-verification skill. Follow its rules exactly.
Inputs:
- gpu: yes
- git_repo: https://github.com/<your-org>/<repo-made-from-the-template>
- s3_external: s3://codeocean-public-data/genomes/saccharomyces_genome
- s3_private: no
- pipeline: <pipeline ID or URL>
- second_user: <their username>
- release: yes
- pre-approved: none
Start with section 0 and keep going until you reach a gate, an operator step or the end. Ask in plain text only.
```

Aqua works through the sections in this order: 0 Preflight, 1 Reproducible Runs, 4 Data assets,
2 Cloud workstations, 3 Git, 5 Pipelines, 6 Sharing, 7 Releases, 8 Aqua, then Wrap-up. Section 4 comes
before 2 because the workstation test needs the result data asset.

## 5. Answer gates and do the operator steps

- **Gate:** Aqua writes `GATE <id>: …` and stops. Reply `GO <id>` or `SKIP <id>`. You can approve
  several up front, for example `pre-approved: RR-2, REL-1`.
- **Operator step:** Aqua gives numbered instructions and stops. Do them, then reply
  `DONE <id>`, adding anything it asked for, such as a commit SHA.

| Id | You do | Then Aqua |
|---|---|---|
| P-1 | Tell Aqua the Code Ocean version (from the release notes or your admin) | records it |
| RR-1.1, RR-2.1 | In the empty capsule Aqua made, click **Start with Sample Files** | lists the files and runs it |
| GIT-2 | Open `DV-<date>-git`, click **Sync with GitHub**, then copy the commit SHA from GitHub | records the SHA |
| PL-0 | In Pipeline Settings: cache off ("Run without cache"); only internal data attached | runs PL-1 |
| PL-2 | Attach the external data asset `DV-<date>-s3-linked` to the pipeline and pick the IAM role | runs PL-2 |
| SH-1 | Share `DV-<date>-cpu` with the second user as **Editor** (Share Assets off) | waits |
| SH-1.1 | The second user clicks **Start editing**, appends a line to `code/DV-sharing-check.md`, saves, and leaves the tab open | waits |
| SH-1.2 | You click **Start editing** (taking control), append a line, commit, and click **Finish editing** | checks that both lines are in the file |
| AQ-1..3 | Ask the three Aqua questions, each in its **own new chat** | gives you the pass rules |

## 6. Who does each checklist item

| § | Item | Aqua | Operator |
|---|---|---|---|
| 1 | RR-1 CPU capsule from a starter; RR-1.2 Flex run; RR-1.3 dedicated run | ✓ | |
| 1 | RR-1.1 / RR-2.1 Start with Sample Files | creates the capsule, then verifies | one click |
| 1 | RR-2 GPU capsule; RR-2.2 GPU Flex; RR-2.3 GPU dedicated | ✓ (gated) | approve |
| 2 | CW-1 to CW-1.6: launch, /scratch, internal data asset, result asset, hold, resume, shut down | ✓ | |
| 3 | GIT-1 commit | ✓ | |
| 3 | GIT-2 Git Sync | | one click + SHA |
| 4 | DA-1 internal result data asset; DA-2 external data asset (with a full read check) | ✓ | |
| 5 | PL-1 / PL-2 run the pipeline | ✓ | pipeline settings |
| 6 | SH-1 / SH-1.1 / SH-1.2 sharing | creates and verifies the file | share; two people edit |
| 7 | REL-1 release, then a new version | ✓ (gated) | approve |
| 8 | AQ-1 to AQ-3 | | asks in fresh chats |

## 7. Results

Aqua keeps the checklist in `dv-report.md`, inside the capsule `DV-<date>-report`, and commits it after
every section. Every PASS names its evidence:
- run numbers and computation IDs;
- the log lines it checked (`DV-BANNER`, `DV-CHECK OK`, `DV-GPU-CHECK OK`, `DV-DATA … unreadable=0`);
- data asset IDs and provenance.

At the end it replies with the full checklist and every object it created.

**Check Aqua's work.** Open two or three of the runs it cites and confirm the log lines are there.
Aqua is the administrator, not the auditor.

## 8. Using the Aqua CLI instead of the web chat

The Aqua CLI sends one prompt and prints Aqua's final reply. It's handy for a scripted, logged run.
1. Get it from `https://get.codeocean.com/aqua-cli/`.
2. Set `CODEOCEAN_DOMAIN` and `CODEOCEAN_TOKEN`, an API key from Account > Access Tokens.
3. Keep one session for the whole test:

```bash
SESSION=$(aqua -json "$(cat kickoff.txt)" | tee 01.json | jq -r .session_id)
jq -r .reply 01.json
aqua -session "$SESSION" "GO RR-2" | tee 02.txt
aqua -session "$SESSION" "DONE GIT-2 commit 1a2b3c4" | tee 03.txt
```

- If Aqua shows an interactive form, the CLI exits with an error. Reply in the same session with
  `Ask in plain text, not a form` and the CLI will work again.
- The CLI acts with your API key's permissions.
- Don't paste keys into prompts. Run `aqua -h` only in a shell where `CODEOCEAN_TOKEN` isn't set,
  because help output shows default values.
- Ask the three §8 questions with **separate** `aqua` calls, without `-session`, so each gets a
  fresh chat.

## 9. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Clone from Git says "Cannot connect to repo" | The GitHub credential in Account > Credentials is missing, expired or has no access to the repository. A capsule already linked to GitHub says "credentials are no longer valid". |
| A run or push is blocked by uncommitted changes | Ask Aqua to commit. Capsules Aqua creates start with uncommitted environment changes. |
| Aqua can't edit or commit | A cloud workstation is holding the capsule. Ask Aqua to shut it down first. |
| A pipeline won't start: "Cannot Access External Data Assets" | External data in a pipeline needs a non-default IAM role, chosen in Pipeline Settings. |
| The GPU step fails with `DV-GPU-CHECK FAIL reason=…` | The reason says what's missing: no GPU visible, no CUDA, or no PyTorch. It is a real failure. |
| The skill is never used | It's disabled for you, or it's invalid: check the Skills page. Mention "deployment-verification skill" in the prompt. |

## 10. Cleanup (optional)

Aqua never deletes or archives anything. Afterwards you can archive:
- the `DV-<date>-*` capsules;
- the data assets `DV-<date>-cpu-result`, `DV-<date>-cw-result` and `DV-<date>-s3-linked`;
- the Git test repository.

Only an admin can delete a release.
