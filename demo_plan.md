# Demo plan

## Goal
Given a member ID, find the member, open their savings account, and return the
available balance and currency.

Example:
"Find member DEMO and retrieve their savings balance."

## Screens
1. Member search: an input field and Search button.
2. Search results: matching member and a link to their details.
3. Member details: a list of accounts.
4. Account details: account type, available balance, and currency.

## Synthetic records
| Member ID | Name | Savings balance | Currency |
|---|---|---|---|
| DEMO-101 | Alex Example | 1250.00 | USD |
| DEMO-202 | Jordan Sample | 3875.50 | USD |
| DEMO-303 | Casey Test | 642.25 | USD |

## Discovery demonstration
The LLM navigates the UI for DEMO-101.
The system records the successful actions as a reusable capability.

## Replay demonstration
The saved capability runs for DEMO-202 without calling the LLM.
It extracts 3875.50 USD from the current UI.

## Conditions to demonstrate
- Unknown member: return a member_not_found business outcome.
- Slow loading: wait within a bounded timeout.
- Permission denied: stop with a clear failure.
- Mock session expiry: pause for human intervention, then resume.
- Disallowed action: block before execution.

## Boundaries
- All records are fictional.
- The agent interacts only through the browser UI.
- The agent cannot read the application's source or data files.
- The initial capability is read-only.
- A minimal local UI is sufficient; visual polish is secondary.


