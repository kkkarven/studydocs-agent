## Summary

- Add JSONL run records and Markdown export for the latest successful answer.
- Keep bounded tool calls, retries, sessions and local review behavior.
- Add offline tests, a six-case development evaluation, a retrieval baseline and fresh-venv checks.
- Add configuration, installation, CI, license and release documentation.
- Replace source-free final explanations with a fixed notice and update the saved conversation.

## Validation

Offline tests, isolated review checks and fresh-venv checks have been run locally; see docs/release-checklist.md.
The real-model before/after results have been reviewed in docs/evaluation-review.md.

## Known limitations

This is an experimental learning prototype. Real-model answer reliability has NOT passed acceptance.
The C example has a confirmed incompatible-pointer assignment, several queries hit the round limit,
and the version question is not answered. Offline passing tests do not establish semantic correctness.
The manual-keyword retrieval baseline is not an equivalent generative system or an independent test set.

## Privacy and authorship

Private states, logs, exports and raw evaluations remain ignored.
The learner implemented the application changes with explained references; scaffolding,
test fixtures, evaluation tools and delivery documents include assistant contributions.
D8 commit 346610d is included; check PR #8 current state before final merge; the latest status query timed out.
