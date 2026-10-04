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
