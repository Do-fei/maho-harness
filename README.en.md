<p align="center">
  <img src="https://raw.githubusercontent.com/Do-fei/maho-harness/main/assets/brand/maho-readme-banner.png" alt="MAHO — Model-Agnostic Harness for Outcomes. Proof before done." width="100%">
</p>

<p align="center">
  <strong>Evidence-first engineering governance for coding agents.</strong><br>
  Give coding agents a project they can understand—and results you can trust.<br>
  One engineering loop for Codex, Cursor, Claude Code, Kimi Code, OpenCode, Kilo Code, and Factory/Droid.
</p>

<p align="center">
  <a href="README.zh-CN.md">简体中文</a> · <a href="README.md">Bilingual overview</a>
</p>

> **Release** — `0.1.0-beta.1` is MAHO's first public Beta. Its source tag is signed and its [GitHub Release](https://github.com/Do-fei/maho-harness/releases/tag/v0.1.0-beta.1) wheel is checksummed. PyPI is not published yet.

## Fast code is not the same as finished software

Coding agents are good at producing changes. The hard part begins around the change:

- Which repository instructions should the agent obey?
- Which files must it leave alone?
- Which test, typecheck, build, or runtime probe actually proves the task?
- What happens when the check times out or the environment cannot run it?
- Can a second agent understand what happened without rereading a long chat?
- Should the agent that wrote the code be allowed to declare its own work complete?

Most agent tools leave those questions to the prompt. Every session reconstructs the process from scratch, and “done” often means only that the agent stopped working.

**MAHO turns that loose conversation into an engineering loop.** It puts the project's rules, accepted checks, client Skills, safety boundaries, and completion evidence in the repository, where people and different coding agents can share them.

It does not replace your coding agent. It gives that agent a better project to work in.

## What changes when MAHO is present

| Before | With MAHO |
|---|---|
| Each agent guesses how the project works. | Every supported client reads the same Project Constitution and engineering Skills. |
| A setup script may merge or replace existing guidance. | Initialization starts with a dry-run and creates only missing paths. |
| The agent picks whichever test looks convenient. | MAHO proposes checks from repository facts; a maintainer decides which checks count. |
| A green command is treated as proof of the whole task. | Required checks, protected paths, timeouts, and evidence states define what the result actually proves. |
| Failed attempts disappear behind the final success. | `FAIL` and `INCONCLUSIVE` remain part of the record. |
| The implementer writes code and grades itself. | A fresh agent or human can accept the exact candidate independently. |

## The engineering loop

### 1. Inspect before editing

`maho discover` reads bounded repository signals: existing instructions, manifests, stack markers, test configuration, and known validation commands. It proposes what might matter; it does not silently turn a guess into policy.

`maho readiness` then shows what is missing before reliable agent work can begin—for example, an incomplete Constitution or checks that have not been approved.

### 2. Make the project contract explicit

MAHO creates two complementary files:

- `.harness/PROJECT_CONSTITUTION.md` explains the project's objective, constraints, authority, protected areas, and definition of success in language people and agents can read.
- `.harness/project.json` stores accepted checks, proposed checks, protected and generated paths, runtime probes, and selected Stack Packs in a machine-readable form.

Generated values are a starting point, not a substitute for review. A maintainer decides which proposed checks become accepted checks.

### 3. Give every client the same playbook

MAHO keeps one canonical set of engineering Skills and maps it into each client's discovery path. Codex and Cursor may load Skills differently from Claude Code or Factory/Droid, but the underlying rules do not fork into seven unrelated copies.

The included Skills cover:

- discovering the harness and reading the Constitution;
- defining an acceptance contract before implementation;
- recording architecture decisions;
- collecting completion evidence without overstating it;
- handing a candidate to an independent reviewer; and
- writing a retrospective that preserves failed attempts.

### 4. Protect the repository while adopting it

`maho init` is read-only unless `--apply` is present. The preview names every path it would create or preserve. Apply mode creates missing files only; an existing file or Skill directory is never merged or overwritten.

During validation, MAHO runs accepted commands as direct argument arrays rather than shell strings, enforces time limits, and takes bounded snapshots of protected paths. If a safety or resource boundary prevents a trustworthy result, the run fails closed instead of quietly weakening the check.

### 5. Replace “trust me” with a receipt

`maho validate` records check state, exit status, timing, output byte counts, and protected-path hashes within explicit resource bounds. It uses three result states:

- `PASS` — the accepted evidence supports the claim;
- `FAIL` — the check or protected state disproves it; and
- `INCONCLUSIVE` — the required proof could not be obtained.

This distinction matters. A broken environment is not a passing test, but it is not always proof that the code is broken either. MAHO keeps that uncertainty visible.

### 6. Separate implementation from acceptance

For consequential work, the final reviewer should be fresh: another agent or a person who receives the exact candidate, the acceptance contract, and the evidence. The implementer can fix a failure, but it does not get to rename the earlier failure or silently lower the bar.

That is the heart of **Proof before done**.

## A concrete example

Suppose you ask a coding agent to change authentication in an existing Node.js application.

Without a harness, the agent might find one package file, edit the login flow, run a nearby unit test, and say the task is complete. It may never notice the repository's `AGENTS.md`, the required typecheck, an integration test in another package, or a protected lockfile.

With MAHO:

1. discovery finds the existing guidance and relevant stack signals;
2. the Constitution states the task, constraints, protected paths, and required outcome;
3. the maintainer approves the checks that count—perhaps unit tests, typecheck, and a bounded runtime probe;
4. the coding agent follows the same acceptance-contract and completion-evidence Skills regardless of client;
5. validation runs the accepted checks and verifies protected paths; and
6. a fresh reviewer judges the exact candidate from the contract and evidence.

MAHO did not write the authentication feature. It made the path from request to accepted change visible and repeatable.

## Why use MAHO

### Change agents without rebuilding your process

The project contract lives in the repository, not in a vendor account or one chat history. A team can move between supported clients while keeping the same definition of success.

### Add governance without surrendering the repository

MAHO is local and dependency-free at runtime. It does not require a hosted MAHO service, a service account, or a model API key. Its generated contract, Skills, and evidence are ordinary files that you can inspect, version, and remove.

### Adopt it safely in real projects

Preview is the default. Existing paths are preserved. Installation reports exactly what it would create, what it kept, and that it overwrote zero files.

### Keep evidence after the chat ends

The next person or agent does not need to trust a summary of the conversation. It can inspect the same project contract, candidate, and receipts—and disagree when the evidence does not support the claim.

### Make honest failure useful

MAHO does not optimize for a wall of green badges. It preserves `FAIL`, distinguishes missing proof as `INCONCLUSIVE`, and records the scope of a `PASS`. That makes failures actionable instead of embarrassing artifacts to hide.

## Similar projects—and where MAHO fits

MAHO is not the first project to bring structure to AI-assisted development. The most relevant alternatives solve neighboring parts of the problem. The comparison below is based on their official documentation as checked on 2026-08-14.

**[GitHub Spec Kit](https://github.github.com/spec-kit/)** goes deeper on specification-driven feature planning. Its default path moves from a Constitution through specification, planning, tasks, and implementation, with broad coding-agent integration. MAHO concentrates more on what happens around the implementation: safe repository adoption, executable accepted checks, protected-path verification, evidence states, and independent completion acceptance.

**[OpenSpec](https://github.com/Fission-AI/OpenSpec)** is an iterative, artifact-guided specification and change system designed for both new and existing projects. It is stronger as a change-spec lifecycle. MAHO focuses on the engineering contract around the work: what may change, which commands count, what the evidence proves, and who may accept it.

**[BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD)** provides a much larger Agile lifecycle with specialist agent roles and structured workflows across analysis, planning, architecture, and implementation. MAHO is deliberately smaller. It governs work performed by the coding agent you already use rather than supplying a virtual organization.

**Client-native rules, instructions, and hooks** provide deep control inside a particular product. They are useful, but usually vendor-specific. MAHO keeps a canonical contract and Skill catalog in the repository, then maps them into supported client paths.

MAHO can be used with these tools rather than instead of them. For example, Spec Kit or OpenSpec can help a team decide **what to build**; MAHO can define **what counts as done, which checks prove it, and how a fresh reviewer accepts the result**.

### Where MAHO is weaker

- **It is early.** `0.1.0-beta.1` has a small community and fewer integrations than established specification frameworks.
- **Coverage is bounded.** Seven clients are verified for recorded versions and scenarios, not every coding agent, operating system, client release, or model route. Third-party discovery behavior may change.
- **Governance adds work.** Someone must review the Constitution and approve the checks. That is useful for consequential changes and unnecessary overhead for some throwaway tasks.
- **Receipts are not full logs.** MAHO stores bounded status metadata and hashes, not complete terminal output. Deep debugging may still require CI logs or the client's native transcript.
- **It is not an orchestrator.** MAHO does not generate a product strategy, manage a team of agent personas, choose a model, run remote workers, or host a dashboard.
- **It is not a sandbox.** Direct-command validation and protected-path snapshots reduce ambiguity; they do not make untrusted code safe to execute.

If your main problem is “help me discover and design the product,” a planning framework may be the better starting point. If the problem is “several agents touch this repository and I need a trustworthy definition of done,” MAHO is designed for that job.

## Quick start

MAHO requires Python 3.10 or later and has no runtime Python dependencies.

### 1. Download, verify, and install

Download the wheel and `SHA256SUMS` from the [GitHub Release](https://github.com/Do-fei/maho-harness/releases/tag/v0.1.0-beta.1), then run:

```bash
shasum -a 256 -c SHA256SUMS
pipx install ./maho_harness-0.1.0b1-py3-none-any.whl
maho --version
```

`uv tool install` can be used instead of `pipx install`. When the [PyPI project page](https://pypi.org/project/maho-harness/) lists this version, installing by package name will also be supported. Until then, the GitHub Release is canonical.

### 2. Preview—MAHO writes nothing

```bash
maho --locale en init /path/to/project --agent codex
```

Review the project path, selected client, proposed files, preserved paths, and the explicit zero-overwrite result.

### 3. Apply the reviewed plan

```bash
maho --locale en init /path/to/project --agent codex --apply --yes
```

### 4. Inspect the project and approve its checks

```bash
maho discover /path/to/project
maho readiness /path/to/project
```

Open `.harness/PROJECT_CONSTITUTION.md` and `.harness/project.json`. Complete the project-specific decisions and move only the checks you accept from `proposed_checks` into `checks`.

### 5. Validate

```bash
maho validate /path/to/project
maho context-audit /path/to/project
```

### 6. Add another agent

```bash
maho --locale en init . --agent cursor --apply --yes
maho --locale en init . --agent all --apply --yes
```

`--agent all` installs adapters for all seven verified clients only. Experimental adapters must be selected by name and display an explicit warning.

For automation, add `--json` to receive deterministic machine-readable output.

## What ships in this Beta

| State | Scope |
|---|---|
| **Core complete** | Zero-overwrite initialization; discovery; readiness; validation; context audit; English and Simplified Chinese surfaces; allowlisted public export; wheel, sdist, and pipx installation checks. |
| **Verified clients** | Codex, Cursor, Factory/Droid, Claude Code, Kilo Code, Kimi Code, and OpenCode have a filesystem adapter, bounded real-client evidence, and separate acceptance for this Beta. |
| **Experimental adapters** | Gemini CLI, Roo Code, and GitHub Copilot have tested adapter behavior, but no real-client support claim or independent acceptance in `0.1.0-beta.1`. |
| **Known limitation** | Wheel and sdist are installable but not proven byte-for-byte reproducible across different build environments. |
| **Not claimed** | A coding-agent runtime, model routing, model-quality improvement, a security sandbox, or identical semantics in every third-party client. |

The [compatibility matrix](docs/en/COMPATIBILITY.md) records the client versions, discovery paths, evidence boundaries, and acceptance phases behind these labels.

## Commands at a glance

| Command | What it answers |
|---|---|
| `maho init` | What would MAHO add, and can it do so without touching existing paths? |
| `maho discover` | What kind of project is this, and which checks might matter? |
| `maho readiness` | What is still missing before reliable agent work? |
| `maho validate` | Did the accepted checks pass, and did protected paths stay intact? |
| `maho context-audit` | Is always-on agent guidance within the project's context budget? |
| `maho bootstrap` | Backward-compatible machine-oriented initialization. |

## Documentation

- [Quick start](docs/en/QUICKSTART.md)
- [Architecture](docs/en/ARCHITECTURE.md)
- [CLI behavior](docs/en/CLI.md)
- [Compatibility matrix](docs/en/COMPATIBILITY.md)
- [Project contract schema](schemas/project.schema.json)
- [Public release process](docs/en/RELEASING.md)
- [Uninstall](docs/en/UNINSTALL.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License and project marks

Code and documentation are licensed under the [Apache License 2.0](LICENSE). The MAHO name and sailboat project mark are governed separately by [TRADEMARKS.md](TRADEMARKS.md).

Copyright is attributed to MAHO contributors. **Future Apparatus Laboratory** stewards the project identity and marks. The public source is [`Do-fei/maho-harness`](https://github.com/Do-fei/maho-harness).
