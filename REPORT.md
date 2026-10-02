# Design Report

## Architecture
Planned: Python automation system with a local Flask demo application.
Discovery uses an LLM; replay executes a saved capability without model calls.

## Artifact schema
To decide: how to represent actions, targets, input parameters,
output extraction, checkpoints, and schema versions.

## Determinism & error handling
To decide: targeting strategy, waiting, recovery, and the distinction
between business outcomes and failures.

## Heterogeneity & multi-tenant
To decide: how browser-specific code is separated from workflow logic,
and how capabilities could be reused across application variants.

## Escalation & handoff
To decide: how automation pauses, a human takes over the same session,
manual actions are recorded, and execution resumes.

## Safety
Planned: synthetic demo data, destination/action allowlists,
conservative handling of risky actions, and sanitized evidence.
API keys are stored outside the repository.

## Cuts
Planned: one local browser application.
Desktop support and multi-tenant infrastructure will be discussed
but not implemented.