# Architecture

Chinese: [`../zh-CN/ARCHITECTURE.md`](../zh-CN/ARCHITECTURE.md)

MAHO keeps portable engineering policy separate from client-specific discovery paths.

```text
User request
    |
Acceptance Contract
    |
Universal Core ---- Stack Packs
    |                    |
Project Constitution ---+
    |
Agent Skills adapter
    |
Direct validation + protected-path snapshot
    |
Completion evidence
    |
Fresh independent acceptance when required
```

## Universal Core

The core defines evidence states, authority boundaries, no-overwrite bootstrap, command validation, and completion semantics. It does not contain framework-specific identifiers.

## Stack Packs

Stack Packs are declarative metadata and guidance. They detect bounded repository signals and propose checks and runtime probes. Detection is not runtime proof.

## Project Constitution

The Constitution records project-specific commands, protected and generated paths, authority, selected Stack Packs, and required evidence. Generated content remains incomplete until a maintainer reviews it.

## Agent adapters

Adapters map one canonical Skill catalog to client discovery roots. Several clients read `.agents/skills`; MAHO deduplicates shared destinations. Client-specific roots are thin copies, not divergent implementations.

## Evidence boundary

Validation stores exit codes, timestamps, byte counts, and hashes. Raw output and raw argument vectors are not persisted. Protected-path snapshots are bounded by file size, total bytes, entry count, depth, and elapsed time; exceeding a bound fails closed.

## Non-goals

MAHO does not replace a client sandbox, run remote agents, select models, manage credentials, deploy software, or prove cost/performance improvement merely because an adapter exists.
