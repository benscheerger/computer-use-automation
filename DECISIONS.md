# Decision Log

## D001 — Use a local demo application
Status: Planned

Decision:
Build a small banking demo containing only synthetic records. Demo app loads data from a json file, so data can be edited or changed without editing the app code.

Reason:
Control the UI and data, reproduce failures, and demonstrate
human takeover without relying on an external website.

Alternative considered:
Use an existing public demo site.

Tradeoff:
Adds some implementation work and provides less evidence of
generalization to unfamiliar applications.

Validation:
Demonstrate multiple member inputs, missing records, and injected
runtime failures.

**D002 — Use Python**  
Status: Adopted  
Python is my strongest language, allowing me to focus more on the system’s design and behavior than implementation details. It also supports the model API and browser automation tools needed for this project.

**D003 — Use Flask for the demo application**  
Status: Planned  
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