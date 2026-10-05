# ADR-001 — SysML v2 model parsing in CI (Spike 1)

- **Status:** proposed — local and CI evidence recorded; awaiting pb's acceptance
- **Date:** 2026-10-05
- **Decided by:** pb (pending)
- **Relates to:** brief §12 M0 (Spike 1), §3 (MBSE), [ADR-000](ADR-000-project-setup.md) D-02, D-20

## Context

M3 needs CI to confirm that the SysML v2 textual model parses and that its names resolve,
and M3's `tools/sysml_check.py` needs the parse result. The brief names the SysML v2 Pilot
Implementation, which ships as a Jupyter kernel. Whether it runs headless in CI was
unknown. If it does not, ADR-000 D-02 trims to a text-level ID check.

## Options

1. **Pilot kernel driven directly through `jupyter_client`.** Start the kernel, send each
   `.sysml` file as one cell, treat `stderr` output or an error reply as a failure. No
   notebook files, no notebook server.
2. **Pilot kernel through `jupyter nbconvert --execute`.** Same kernel, but the model has to
   be wrapped in a generated notebook, and error detection depends on how nbconvert
   reports kernel `stderr`.
3. **Eclipse-based Pilot installation in batch mode.** Heavier (Eclipse + Xtext), no
   documented headless CLI.
4. **Fallback: no parser in CI.** Parse locally only; CI checks requirement IDs at text
   level.

## Decision

Option 1. The kernel `jupyter-sysml-kernel=0.62.0` (conda-forge,
matching the 2026-08 Pilot release) is installed in the toolchain image under
`/opt/sysml` with micromamba. `tools/sysml_parse.py` drives it.

The option 4 fallback is not needed. If a later kernel or runner change breaks parsing in
a way that cannot be fixed in the image, switch to option 4 and amend this ADR.

## Evidence

Local run inside the toolchain image (`safecruise-dev:local`, built from this commit's
`Dockerfile`), 2026-10-05:

```text
$ python tools/sysml_parse.py model/sysml/spike/Toy.sysml
[OK  ] model/sysml/spike/Toy.sysml
       Package SpikeToy (38aae1b1-66cb-49aa-8231-23a2641c10a6)
exit=0 (11 s)

$ python tools/sysml_parse.py tests/tools/fixtures/broken_syntax.sysml
[FAIL] tests/tools/fixtures/broken_syntax.sysml
       ERROR:mismatched input '<EOF>' expecting '}' (1.sysml line : 4 column : 25)
exit=1 (10 s)

$ python tools/sysml_parse.py tests/tools/fixtures/broken_reference.sysml
[FAIL] tests/tools/fixtures/broken_reference.sysml
       ERROR:Couldn't resolve reference to Type 'NoSuchType'. (1.sysml line : 4 column : 27)
       ERROR:An attribute must be typed by attribute definitions. (1.sysml line : 4 column : 9)
exit=1 (10 s)
```

The toy model covers the constructs M3 needs: package with import, port def with a
directed attribute, conjugated port, part defs and usages, `connect`, a `state def` with
transitions, `exhibit state`, a requirement def with a short ID (`<'SYS_TOY_001'>`) and
`satisfy`. Both kinds of error (syntax, unresolved reference) are reported.
`tests/tools/test_sysml_parse.py` repeats these three checks under pytest.

**CI evidence:** [run #1](https://github.com/Prennoy99/safecruise/actions/runs/37376630395), commit `743bb87`, job
[`docs-trace-gate`](https://github.com/Prennoy99/safecruise/actions/runs/37376630395/job/111988530345), image `ghcr.io/prennoy99/safecruise-ci@sha256:61e674ec3e5fab215301376f115884d140eac50f6dfe9315f0da4d5ae7716f4f`:

| Step | Result |
|---|---|
| Spike 1 (ADR-001): SysML v2 toy model parses | success |
| Spike 1 (ADR-001): broken models fail (both fixtures rejected) | success |

Neither step uses `continue-on-error`, so a success is a real pass. The same run's
`build-unit` job also passed `tests/tools/test_sysml_parse.py`. Job runtime 1 min 2 s,
including the docs builds.

## Consequences

- One kernel start costs about 10 s (JVM start plus standard library load). M3 should parse
  all model files in one kernel session rather than one process per file.
- Files sent to one kernel session share a namespace. `sysml_check.py` in M3 must either
  load the model files in dependency order in one session or isolate them deliberately.
- The kernel runs `java` from `PATH`, i.e. the image's OpenJDK 21. The conda prefix brings
  its own runtime too, which makes `/opt/sysml` about 926 MB. Slimming the image (copying
  only the kernel jars) is possible later and does not change this decision.
- The kernel spec sets `ISYSML_API_BASE_PATH` to a remote model repository used only by
  the kernel's publish command. Parsing does not contact it; CI must never use publish.
- Error detection relies on the kernel writing `ERROR:` lines to `stderr`. A kernel
  upgrade is a change to this ADR and must re-run the two broken fixtures.
