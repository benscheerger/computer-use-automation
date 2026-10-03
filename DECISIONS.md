# Decision Log

**D001 — Use a local demo application**  
Status: Adopted  
A small banking demo with synthetic records provides control over data, failure scenarios, and human-takeover testing. Records are loaded from JSON so they can change independently of application code. Compared with a public demo site, this adds implementation work and provides less evidence of generalization to unfamiliar applications.

**D002 — Use Python**  
Status: Adopted  
Python is my strongest language, allowing me to focus more on the system’s design and behavior than implementation details. It also supports the model API and browser automation tools needed for this project.

**D003 — Use Flask for the demo application**  
Status: Complete  
Flask provides a simple way to serve HTML pages and handle member searches using Python. It keeps the demo small while allowing controlled errors and session-expiry scenarios.

**D004 — Use the standard model API**  
Status: Adopted  
API-key authentication requires less setup than integrating ChatGPT sign-in. The tradeoff is separate usage charges, which I will monitor during development.

**D005 — Start with GPT-6 Luna**  
Status: Provisional; basic connection verified  
I selected GPT-6 Luna for its low token cost. Its ability to choose reliable UI actions still needs testing; I will reconsider the model if it struggles with the workflow.

**D006 — Store credentials outside the repository**  
Status: Adopted  
The API key is stored in a configuration file outside the repository and loaded at runtime. This reduces accidental inclusion in source control. 

**D007 — Separate application code, tests, and utility scripts**  
Status: Adopted  
Reusable automation logic lives in `automation/`, automated checks in `tests/`, and manual utilities in `scripts/`. The demo application remains in `demo_app/`. This keeps responsibilities clear and lets tests and utilities use the same implementation without duplicating logic.

**D008 — Use Playwright for browser interaction**  
Status: Adopted  
Playwright provides browser control, page observations, and checks for expected UI states. It supports both LLM-directed discovery and replay without model calls, while allowing a visible session for human takeover. Browser-specific logic will remain separate from workflow logic; legacy pages may require additional targeting strategies, and desktop support would require another adapter.

**D009 — Use Pydantic to validate action requests**  
Status: Adopted  
Pydantic defines structured action models and validates required fields, types, and allowed values before execution. Strict validation rejects unexpected fields and prevents silent type conversion. These models also support JSON serialization and schema generation. Valid structure does not establish that an action is safe or correct; policy checks and outcome verification remain separate.

**D010 — Share one action executor between discovery and replay**  
Status: Executor implemented; integration pending  
Validated actions are translated into Playwright operations through a shared executor. Discovery and replay will use the same execution logic to keep targeting and policy enforcement consistent. Completion verification remains separate from browser actions.

**D011 — Enforce an explicit allowlist before actions**  
Status: Adopted  
The executor checks permitted origins, paths, form fields, and buttons before acting. Link destinations are checked before clicking. This limits the current workflow to approved demo interactions; the policy will need configuration support as additional applications are introduced.

**D012 — Enforce policy on browser requests**  
Status: Implemented; validation in progress  
A browser-context request guard checks destinations and permits only GET requests for the current read-only demo. HTTP redirects and service workers are blocked to simplify enforcement. Policy violations retain a reason without recording full request contents. Disallowed-path blocking is verified; method and redirect blocking still require separate checks.

## D013 — Separate planning from execution

**Decision:** The LLM proposes one action from the current page observation. A separate executor checks policy and performs the action.

**Reason:** Keeps browser control predictable and lets discovery and deterministic replay share the same executor.

**Tradeoff:** Adds coordination between components; the planner alone cannot confirm execution or success.

## D014 — Require structured model responses

**Decision:** Request model output matching the existing Pydantic `NextAction` schema. Stop if the response is incomplete or has no parsed action.

**Reason:** Gives the executor a typed action instead of requiring it to interpret free-form text.

**Tradeoff:** Valid structure does not guarantee a correct or permitted action; policy checks and outcome verification remain necessary.

## D015 — Bound discovery runs

**Decision:** Discovery observes the page, proposes one action, and executes it, with a configurable step limit. Policy violations and execution errors stop the run.

**Reason:** Limits model usage and prevents endless action loops.

**Tradeoff:** Recoverable failures currently stop the run until explicit recovery handling is added.

## D016 — Verify completion directly from the UI

**Decision:** Treat the model’s finish action as a request for verification. Check the requested member and account, then extract a typed balance result directly from the page.

**Reason:** Success should depend on observable page evidence, independently of the model’s summary.

**Tradeoff:** Verification initially depends on the demo’s page structure and must be adapted for other applications.

**Validation:** Discovery reached DEMO-101’s savings account. Independent verification checked the account URL, heading, and displayed member ID, then extracted a balance of 1250.00 USD into a typed result.

## D017 — Store capabilities as versioned, parameterized JSON

**Decision:** Represent reusable capabilities with typed actions, explicit input references, path checkpoints, and named input/output contracts. Record link destinations so replay does not depend on member-specific display names.

**Reason:** Enables deterministic replay with different member IDs and keeps the reusable workflow separate from discovery logs.

**Tradeoff:** The initial schema supports the demo’s savings-balance workflow and URL structure; broader workflows will require extensions.

## D018 — Replay without model calls

**Decision:** Replay loads a validated capability, substitutes typed inputs, and executes its recorded steps through the shared executor and policy checks.

**Reason:** Makes execution repeatable and avoids additional model costs or decisions during replay.

**Tradeoff:** Replay cannot adapt to unexpected UI changes; failures currently stop the run.

**Validation:** A capability discovered with DEMO-101 successfully replayed for DEMO-202 without model calls.

## D019 — Check intermediate and final replay outcomes

**Decision:** Check the expected URL path after every replay action, then independently verify the requested account and extract its balance from the UI.

**Reason:** Detects navigation mismatches and prevents completed actions alone from being treated as task success.

**Tradeoff:** Path checkpoints provide limited evidence of page contents; final verification supplies stronger checks.

**Validation:** All four checkpoints passed for DEMO-202, and final verification returned 3875.50 USD.

## D020 — Save structured evidence for each run

**Decision:** Write typed JSONL events with run IDs, timestamps, step numbers, action types, and outcomes. Exclude input values, balances, page contents, and raw exception messages.

**Reason:** Makes execution reviewable while limiting sensitive information in saved logs.

**Tradeoff:** Basic events provide limited failure detail; richer sanitized diagnostics will be added separately.

## D021 — Distinguish business outcomes from automation failures

**Decision:** Detect an explicit member-not-found state, verify it corresponds to the requested search, and return a typed business outcome instead of continuing to a missing link.

**Reason:** Section 3.3 requires expected business outcomes to be reported separately from recoverable conditions and hard failures.

**Tradeoff:** The initial detector uses a marker in the local demo. Other applications require their own outcome detection strategy.