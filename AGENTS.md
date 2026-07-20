# AGENTS.md

# YT Signal Scout

## Purpose

This repository contains the implementation of **YT Signal Scout**, a production-grade SaaS platform that discovers high-potential YouTube channels using public performance signals from the official YouTube Data API.

This document is the primary operating manual for AI coding agents working on this repository.

Every implementation should prioritize:

1. Correctness
2. Maintainability
3. Reliability
4. Security
5. Simplicity

Performance optimization should only occur after measurable evidence identifies a bottleneck.

---

# Source of Truth

Every implementation must follow this hierarchy.

```
Product Behaviour
        ↓
PRD

Architecture
        ↓
TRD

Architecture Decisions
        ↓
ADR

Engineering Philosophy
        ↓
ENGINEERING_PRINCIPLES.md

Git Workflow
        ↓
GIT_CONVENTIONS.md

Implementation
        ↓
Source Code
```

Never invent product behaviour.

Never change architecture without approval.

---

# Required Reading Order

Before implementing any feature:

1. Read this file.
2. Read the relevant PRD section.
3. Read the relevant TRD section.
4. Read applicable ADRs.
5. Review existing implementation.
6. Reuse existing code whenever possible.

Only then begin implementation.

---

# Technology Stack

## Backend

- FastAPI
- SQLAlchemy
- Supabase PostgreSQL
- Pydantic

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui

## Authentication

- Google OAuth

## Rules

Do not introduce additional frameworks, ORMs, databases, or major libraries without explicit approval.

Architectural changes require an ADR.

---

# Repository Structure

```
backend/
    api/
    core/
    db/
    models/
    repositories/
    schemas/
    services/

frontend/

docs/

tools/

infrastructure/
```

Respect this structure.

Do not create new top-level folders without approval.

---

# Architecture Rules

The application follows a Modular Monolith architecture.

The dependency direction is:

```
Routes

↓

Services

↓

Repositories

↓

Database
```

Never bypass layers.

---

## API Layer

Responsible only for:

- HTTP
- Validation
- Authentication
- Authorization
- Response formatting

API routes must never contain business logic.

---

## Services

Services own business logic.

Services may call multiple repositories.

Services must remain independent from HTTP.

---

## Repositories

Repositories own persistence.

Repositories must not contain business rules.

---

## Models

Models represent persistence.

---

## Schemas

Schemas represent API contracts.

Do not expose persistence models directly through APIs.

---

# Coding Standards

Always:

- Use type hints.
- Prefer explicit code over clever code.
- Keep functions small.
- Keep classes focused.
- Follow the Single Responsibility Principle.
- Prefer composition over inheritance.
- Remove dead code.
- Avoid duplicated logic.

Never:

- Use global mutable state.
- Hardcode secrets.
- Hardcode configuration.
- Leave commented-out code.
- Introduce unnecessary abstraction.

---

# Configuration

Configuration must come from:

- Environment variables
- Configuration classes

Never hardcode:

- API keys
- URLs
- Credentials
- Tokens
- Secrets

---

# Error Handling

Errors must:

- Fail clearly.
- Provide meaningful messages.
- Be logged.
- Never silently fail.

Recover only when recovery is intentional.

---

# Logging

Use structured logging.

Never use print() for application logging.

Logging should help diagnose production issues.

Sensitive information must never be logged.

---

# Database Rules

Repositories own database interaction.

Transactions should remain explicit.

Avoid N+1 queries.

Never expose raw database objects outside the repository layer.

---

# API Design

Follow REST principles.

Use versioned routes.

Return consistent response models.

Validate all input.

Never expose internal exceptions directly.

---

# Security

Always assume user input is untrusted.

Validate everything.

Escape output where appropriate.

Never expose secrets.

Never commit credentials.

Never trust client-side validation.

---

# Dependency Policy

Before introducing a dependency ask:

1. Does Python already provide this?
2. Does the framework already solve this?
3. Can existing project code solve this?

Prefer fewer dependencies.

Every dependency increases maintenance cost.

---

# Documentation Rules

Whenever behaviour changes:

Update the PRD if required.

Whenever architecture changes:

Create or update an ADR.

Whenever engineering philosophy changes:

Update ENGINEERING_PRINCIPLES.md.

Whenever workflow changes:

Update GIT_CONVENTIONS.md.

Keep documentation synchronized with implementation.

---

# Git Workflow

Follow:

docs/engineering/GIT_CONVENTIONS.md

Do not invent new commit formats.

Keep commits focused.

Prefer small commits.

---

# Testing Expectations

Every completed feature should be:

- Buildable
- Runnable
- Testable

Business logic should be testable independently of HTTP.

---

# Refactoring

Refactor when it:

- Improves readability
- Reduces duplication
- Simplifies maintenance

Do not refactor unrelated code while implementing a feature.

---

# Performance

Never optimize prematurely.

Measure first.

Optimize second.

Document major performance changes when they affect architecture.

---

# AI Decision Checklist

Before writing code ask:

- Did I read the PRD?
- Did I read the TRD?
- Did I check existing implementation?
- Am I duplicating code?
- Can I reuse an existing service?
- Does this require an ADR?
- Does this violate Engineering Principles?
- Does documentation need updating?
- Is there a simpler design?
- Will another engineer easily understand this six months from now?

If any answer is uncertain, stop and resolve it before implementing.

---

# Definition of Done

A task is complete only when:

- The solution builds successfully.
- The application runs.
- Code follows the agreed architecture.
- Documentation is updated when required.
- No TODOs remain.
- No secrets are committed.
- The work is committed using the agreed Git conventions.

---

# Things Never To Do

Never:

- Commit secrets.
- Hardcode credentials.
- Bypass service layers.
- Duplicate business logic.
- Introduce new frameworks without approval.
- Ignore warnings.
- Change architecture silently.
- Mix business logic into API routes.
- Ignore documentation updates.
- Sacrifice maintainability for cleverness.

---

# Guiding Principle

Every change should leave the repository in a better state than it was found.

Build software that is easy to understand, easy to extend, and easy to operate.