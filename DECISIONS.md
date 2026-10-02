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