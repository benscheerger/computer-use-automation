# Assignment checklist

## 3.1 Goal-driven agent loop
- [] Accept a natural-language goal and target application.
- [X] Use a real LLM to observe the UI, choose actions, and execute them.
- [X] Verify goal completion.
- [X] Stop on step limits, timeouts, or a dead end.

## 3.2 Structured capability artifact
- [ ] Record the successful run as a typed, versioned artifact.
- [ ] Include ordered actions and reusable target identifiers.
- [ ] Define typed input parameters.
- [ ] Define typed outputs and extraction instructions.
- [ ] Include checkpoints or success conditions.
- [ ] Keep the artifact separate from the raw model transcript.

## 3.3 Deterministic replay
- [ ] Replay a saved artifact with supplied input parameters.
- [ ] Make no LLM calls for replay decisions.
- [ ] Use stable targeting and verify success.
- [ ] Extract and return the declared outputs.
- [ ] Distinguish business outcomes, recoverable conditions, and hard failures.
- [ ] Return structured results with useful failure details.

## 3.4 Safety and policy
- [ ] Enforce configurable allowed destinations and action types.
- [ ] Handle risky or irreversible actions conservatively.
- [ ] Keep secrets and raw sensitive data out of artifacts and logs.

## 3.5 Evidence and observability
- [ ] Produce structured execution logs.
- [ ] Capture sanitized screenshots, snapshots, or traces on failure.

## 3.6 Human escalation and handoff
- [ ] Detect blocked states and request human intervention.
- [ ] Provide the operator with context and the reason for stopping.
- [ ] Pause automation and transfer control of the same live session.
- [ ] Record what the human does.
- [ ] Support handing control back and safely resuming.

## 3.7 Design for heterogeneity and scale
- [ ] Explain how the design extends to legacy web and desktop surfaces.
- [ ] Explain capability reuse and overrides across tenants.
- [ ] Explain how tenant or application-version differences are detected.

## Submission
- [ ] Public GitHub repository containing the source.
- [ ] README.md with setup and exact discovery/replay commands.
- [ ] REPORT.md of approximately 1–3 pages using the seven required headings.
- [ ] evidence/ containing an example artifact and real discovery/replay logs.
- [ ] Document deliberate cuts and remaining limitations.
- [ ] Email the repository URL on its own line from the application email address.