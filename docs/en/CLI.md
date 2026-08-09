# CLI design and behavior

Chinese: [`../zh-CN/CLI.md`](../zh-CN/CLI.md)

The CLI uses a restrained single-column layout: one decision at a time, explicit state labels, and no dependence on color, emoji, animation, or a particular font.

The full sailboat appears only for onboarding and installation receipts. Routine commands remain compact and machine-readable.

```text
                 |
             |\  |\
             | \ | \
             |  \|  \
             |   |   \
             |___|____\
                 |
           ______|_______
       ~~~\_____________/~~~

              M A H O
 Model-Agnostic Harness for Outcomes
          Proof before done.
```

## Interaction contract

- `maho init` defaults to dry-run.
- `--apply` changes only missing paths.
- `--yes` is required for non-interactive application.
- `--json` returns deterministic machine-readable output.
- `--locale en|zh-CN` selects terminal text and installed Skill language.
- `--no-color` is accepted for scripts and terminals that prohibit ANSI output. The beta UI currently remains readable without emitting ANSI sequences.
- `--agent all` selects the seven verified clients only.
- Experimental adapters must be selected by name; the receipt labels them `Experimental` and warns that real-client acceptance is absent.

Every receipt reports verified and experimental selections, created, preserved, skipped, overwritten, verification state, and the next command. Status is always conveyed in text, never by color alone.
