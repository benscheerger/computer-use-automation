# smartBank

## LLM banking UI discovery and deterministic replay

Some business applications lack direct integration APIs, so automated tasks must be performed through their UIs. This repository demonstrates how an LLM can interact with an existing UI and how those interactions can be saved and reused for similar requests without additional model calls.

The LLM receives a natural language goal, observes the application, chooses actions, and discovers how to complete the task. A successfully verified run produces a typed, versioned capability with parameterized inputs. Future runs replay that capability without model calls, checking progress and independently verifying the result.

In this example, both discovery and replay operate a local banking demo with synthetic records to retrieve a member’s available savings balance and currency. A local operator console provides one interface for starting discovery and replay, selecting datasets, viewing results, and inspecting run evidence. When replay encounters a persistent service notice that automatic recovery cannot resolve, automation pauses so a human can take control of the same browser session. The operator can repair the page and request Resume, which validates the current state before automation continues. Manual actions and control transfers are recorded in the run evidence.

## Features and scope

- **Goal-driven discovery:** Accepts a natural language goal and member ID. The model observes the UI and selects validated actions within a fixed step limit.
- **Reusable capabilities:** Saves verified workflows as versioned JSON artifacts with typed inputs, parameterized targets, and checkpoints.
- **Deterministic replay:** Executes saved capabilities with new inputs without model calls and independently verifies the displayed result.
- **Explicit outcomes:** Distinguishes successful results, expected business outcomes such as missing members, and execution failures.
- **Recovery and human takeover:** Attempts bounded recovery for a known service notice. A persistent notice can trigger human takeover of the same browser session, with validation before automation resumes.
- **Operator console:** Provides discovery and replay controls, dataset selection, results, run history, and takeover controls.
- **Safety and evidence:** Enforces configurable action and network request restrictions. Saves structured run events and sanitized failure snapshots.

The implemented task is retrieving a member’s available savings balance and currency from a local banking demo containing synthetic records. Alternate datasets demonstrate capability reuse across different records within the same UI. Desktop automation, real banking integrations, and arbitrary browser tasks are outside the implemented scope.

## Requirements and installation

### Requirements

- Python 3.11.
- A graphical desktop session for the visible Chromium browser.
- An OpenAI API key for live discovery.

Replay of an existing capability and the default test suite do not require an API key or make model calls.

### Installation

Clone the repository and run these commands from its root directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

The environment activation command above is for macOS and Linux. Run subsequent project commands from the repository root with the virtual environment active.

### API configuration

Discovery loads the API key from a file outside the repository:

```text
~/.config/computer-use-automation/.env
```

Create the directory and edit the file:

```bash
mkdir -p ~/.config/computer-use-automation
nano ~/.config/computer-use-automation/.env
```

Add your API key:

```dotenv
OPENAI_API_KEY=your_api_key_here
```

Keeping credentials outside the repository reduces accidental inclusion in source control.

The discovery model is configured by `MODEL` in `automation/planner.py`. The initial tested model is `gpt-6-luna`. Live discovery makes model API requests; deterministic replay does not.

## Usage and end-to-end demonstration

Run commands from the repository root with the virtual environment active. The job functions start and stop the local demo server automatically, so port `8000` must be available.

### Launch the operator console

```bash
python -m scripts.run_console
```

The console opens in your browser and prints its local URL in the terminal. It supports one active run at a time.

### Discover a capability

1. Select **Discovery**.
2. Choose the `members` dataset.
3. Enter member ID `DEMO-101`.
4. Enter the goal:

   > Find this member's available savings balance and report its currency.

5. Start the run.

A visible Chromium browser opens, and the model interacts with the demo application. After independent verification succeeds, the console displays the model summary, verified outputs, run ID, and saved capability ID.

The capability is saved under:

```text
evidence/capabilities/get_savings_balance_<run-id>.json
```

Successful discovery also updates `get_savings_balance.json`, a convenience alias for the latest capability.

### Replay with another member

1. Select **Replay**.
2. Choose the capability created by the discovery run.
3. Choose the `members` dataset.
4. Enter member ID `DEMO-202`.
5. Set the notice mode to **Off** and disable human takeover.
6. Start replay.

Replay executes the recorded workflow with the new member ID, checks its checkpoints, and independently verifies the final balance and currency. It does not make model calls.

To demonstrate reuse across different records, select `members_alternate` and replay the same capability. The verified output should reflect the selected dataset.

### Command-line discovery and replay

The following example calls the same job functions used by the console. It discovers a workflow for `DEMO-101`, then replays the exact capability produced by that run for `DEMO-202`.

Stop the console and any separately running demo server before running this example. Discovery requires the configured API key and makes model API requests.

```bash
python -m scripts.demo
```

Both runs save evidence under `evidence/runs/`. The replay log references the original discovery run through `source_run_id`.

### Replay without live model services

An existing saved capability can be replayed through the console without an API key. Start the console, select **Replay**, and choose an artifact from the capability catalog.

This path runs entirely against the local demo application. A saved capability must already be present in `evidence/capabilities/`.

## Recovery and human takeover

Replay supports three simulated service-notice modes, selected through the operator console:

| Notice mode | Human takeover | Expected behavior |
| --- | --- | --- |
| Off | Disabled | Replay completes normally and verifies the result. |
| Dismissible | Disabled | Automatic recovery dismisses the notice and replay continues. |
| Persistent | Disabled | Automatic recovery is exhausted and replay returns a structured failure. |
| Persistent | Enabled | Automation pauses and requests human intervention. |

Automatic recovery is limited to one dismissal attempt per run. It handles the known service notice rather than attempting arbitrary repairs.

### Demonstrate human takeover

1. Select **Replay**, choose a saved capability, and enter `DEMO-202`.
2. Select the `members` dataset, set the notice mode to **Persistent**, and enable human takeover.
3. Start replay and wait for automation to pause.
4. Press **Resume** before repairing the page. The request should be rejected, and automation should remain paused.
5. In the existing Chromium session, click **Resolve notice manually**.
6. Press **Resume** again.

Before continuing, the system checks the original session, member identity, expected page, absence of the blocking notice, and readiness of the pending target. Successful validation returns control to automation, which continues replay and independently verifies the result.

During takeover, the demo replaces the automatic dismissal control with the manual resolution control.

### Cancellation, expiry, and evidence

Only one takeover is permitted per run, with a default timeout of 180 seconds. Cancelling takeover or allowing it to expire ends the run with a structured failure.

Run evidence records takeover initiation, rejected Resume attempts, categorized manual actions, successful resumption, cancellation, and expiry. Manual-action records omit entered values.

The implemented takeover path handles exhausted service-notice recovery during replay. It does not provide general human recovery for every discovery or replay failure.

## Results and evidence

Replay returns a structured result:

| Status | Meaning |
| --- | --- |
| `success` | Independent UI verification passed. Outputs include the member ID, account type, available balance, and currency. |
| `business_outcome` | An expected business result was detected, such as `member_not_found`. |
| `failure` | Execution stopped with a failure code, step, expected condition, observed condition, and error type. |

The verified outputs are extracted from the displayed UI rather than taken from the model’s summary.

### Saved evidence

| Location | Contents |
| --- | --- |
| `evidence/capabilities/*.json` | Versioned, parameterized capability artifacts. |
| `evidence/runs/*.jsonl` | Structured discovery and replay events, including verification, recovery, and human handoff. |
| `evidence/runs/*.failure.json` | Sanitized structural snapshots captured on failure. |

Run-specific capabilities preserve the artifact associated with each discovery run. `get_savings_balance.json` is an alias for the latest successful recording.

Failure snapshots contain bounded DOM structure and control counts, excluding raw page text, field values, and attributes. Manual actions are recorded by category without entered values.

### Example evidence

- [Saved capability](evidence/capabilities/get_savings_balance_1be7478a-45c1-4af6-856b-0b34d255f193.json)
- [Original discovery run](evidence/runs/1be7478a-45c1-4af6-856b-0b34d255f193.jsonl)
- [Successful replay with another member](evidence/runs/80fc5cee-1a33-4843-902c-50d440796efb.jsonl)
- [Missing-member business outcome](evidence/runs/811880ba-2afa-465b-8f87-c2a25da02b76.jsonl)
- [Human repair followed by successful Resume](evidence/runs/3d63c619-4390-488b-be80-cc7aac567d8e.jsonl)

Replay logs reference the originating discovery run through `source_run_id`.

## Project structure

### Automation

| File | Purpose |
| --- | --- |
| `automation/jobs.py` | Shared discovery and replay entry points, task models, capability loading, and catalog access. Manages the demo server, browser, and run lifecycle. |
| `automation/discovery.py` | Runs the bounded observe–decide–act loop and collects steps for a reusable capability. |
| `automation/planner.py` | Sends the goal and current observation to the model and obtains a typed next action. |
| `automation/observation.py` | Collects the page URL, title, and accessibility snapshot used by the model. |
| `automation/actions.py` | Defines validated action models and shared strict validation settings. |
| `automation/executor.py` | Locates permitted controls and executes browser actions. |
| `automation/recording.py` | Converts discovered actions into recorded steps with parameterized values, targets, and checkpoints. |
| `automation/capability.py` | Defines the versioned capability schema, typed inputs, text templates, recorded actions, and checkpoints. |
| `automation/replay.py` | Executes saved workflows without model calls, checks progress, handles known conditions, and returns structured results. |
| `automation/results.py` | Defines replay success, business-outcome, and failure contracts. |
| `automation/verification.py` | Independently validates the final account page and extracts the displayed balance and currency. |
| `automation/business_outcomes.py` | Detects expected application outcomes, such as a missing member. |
| `automation/recovery.py` | Performs bounded automatic recovery for the known service notice. |
| `automation/policy.py` | Loads policy configuration and checks permitted URLs, request methods, and actions. |
| `automation/network.py` | Enforces browser request restrictions and records blocked requests. |
| `automation/handoff.py` | Coordinates human takeover of the live session, records manual actions, and validates readiness before Resume. |
| `automation/takeover_controls.py` | Provides queued Resume and Cancel controls for the persistent console and temporary CLI operator panel. |
| `automation/evidence.py` | Writes structured run logs and captures sanitized structural evidence on failure. |
| `automation/console.py` | Implements console endpoints, job queuing, run state, results, and evidence access. |
| `automation/__init__.py` | Marks the automation directory as a Python package. |

### Interfaces, demo application, and configuration

| File or directory | Purpose |
| --- | --- |
| `automation/templates/console.html` | Main interface for discovery, replay, dataset selection, results, run history, and takeover controls. |
| `automation/templates/operator_panel.html` | Temporary operator interface used during CLI takeover. |
| `demo_app/app.py` | Loads the selected dataset and serves member search, member details, and account details. |
| `demo_app/server.py` | Starts and stops the local demo server for managed jobs. |
| `demo_app/data/*.json` | Synthetic datasets that can be changed independently of application code. |
| `demo_app/templates/search.html` | Member search form and search results. |
| `demo_app/templates/member.html` | Member details, account links, and simulated service notices. |
| `demo_app/templates/account.html` | Account details, including the available balance and currency. |
| `config/policy.json` | Default action and request allowlists, including explicit risky-action restrictions. |

### Entry points and supporting files

| File or directory | Purpose |
| --- | --- |
| `scripts/run_console.py` | Launches the local operator console. |
| `scripts/run_discovery.py` | Command-line entry point for discovery. |
| `scripts/replay.py` | Command-line entry point for replay. |
| `scripts/demo.py` | Demonstrates discovery for one member followed by replay of the resulting capability for another member. |
| `scripts/observe_page.py` | Development helper for manually inspecting page observations. |
| `scripts/run_tests.py` | Runs the automated checks and reports their results. |
| `tests/` | Policy, privacy, browser, business-outcome, and workflow checks, plus failure fixtures. |
| `evidence/` | Saved capabilities, discovery/replay logs, and failure snapshots. |
| `requirements.txt` | Pinned direct dependencies used to install the project. |
| `REPORT.md` | Design reasoning, tradeoffs, extension plans, and deliberate scope cuts. |

## Testing

Run tests from the repository root with the virtual environment active. Stop the operator console and any separately running demo server first so port `8000` is available.

### Run the full suite

```bash
python -m scripts.run_tests
```

The runner executes each test module in a separate process, starts the demo server where needed, and reports a summary.

The default suite makes no model calls. Its workflow checks require an existing `get_savings_balance` capability in `evidence/capabilities/`.

### Include live discovery

```bash
python -m scripts.run_tests --live-discovery
```

This performs fresh discovery before replaying the newly saved capability with another member. It requires the configured API key and makes model API requests.

### Run workflow checks independently

```bash
python -m tests.test_workflows
```

To test a specific archived capability, supply its filename without the `.json` extension:

```bash
python -m tests.test_workflows --capability-id get_savings_balance_1be7478a-45c1-4af6-856b-0b34d255f193
```

### Automated coverage

| Test module | Coverage |
| --- | --- |
| `tests/test_policy.py` | Configurable permissions, blocked destinations and methods, and risky-action restrictions. |
| `tests/test_failure_evidence.py` | Structural failure capture and exclusion of sensitive sentinel values. |
| `tests/test_browser.py` | Browser interaction, independent balance verification, rejection of an incorrect member, and blocked network requests. |
| `tests/test_business_outcomes.py` | Missing-member detection and distinction from an existing member. |
| `tests/test_workflows.py` | Optional live discovery, replay with another member, capability provenance, evidence ordering, and validated takeover. |

The automated takeover test uses a scripted operator to request Resume before repair, resolve the notice through the real demo control, and request Resume again. It exercises production handoff validation and manual-action recording, but does not test the console interface itself.

### Manual verification

The operator console was also checked manually for:

- Replay against the default and alternate datasets.
- Missing-member business outcomes.
- Automatic recovery from a dismissible notice.
- Structured failure when a persistent notice blocks replay and takeover is disabled.
- Rejected Resume before repair and successful Resume after manual repair.
- Cancellation and takeover expiry.
- Console refresh during takeover, restoration of controls, and prevention of a second concurrent run.

Saved evidence was inspected alongside console results to confirm the expected run, recovery, and handoff events.

## Limitations and design documentation

- **One supported task:** Natural-language input is scoped to retrieving a member’s available savings balance and currency.
- **One implemented surface:** Automation targets a local web application with semantic controls. Desktop applications, legacy framesets, and real banking integrations are not implemented.
- **Limited generalization:** Alternate datasets demonstrate reuse across different records within the same UI, rather than compatibility across vendor products or application versions.
- **Bounded recovery:** Automatic recovery handles one known service notice. Human takeover supports the demonstrated persistent-notice condition during replay; specialized recovery for other conditions is not implemented.
- **Local operation:** The console supports one active job in a single process. It does not provide production operator authentication, remote co-browsing, or session recovery after a process restart.
- **Safety boundaries:** Action and network restrictions constrain automation but do not provide an operating-system sandbox. Synthetic page observations are sent to the model during discovery.

See [REPORT.md](REPORT.md) for the architecture, artifact schema, error-handling strategy, proposed extensions for heterogeneous surfaces and tenant reuse, human handoff model, safety limits, and deliberate scope cuts.