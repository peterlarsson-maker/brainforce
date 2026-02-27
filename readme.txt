# BrainForce Core

BrainForce Core is a local, session-aware AI engine built for stability and control.

This repository contains the clean backend core only.
Experimental distributed/network layers have been archived.

---

## 🎯 Purpose

BrainForce Core provides a controlled AI execution layer that:

- Exposes an OpenAI-compatible API
- Maintains session-based conversational memory
- Uses turn-aware token trimming
- Enforces configurable token budgets
- Supports mock mode for safe testing
- Is fully test-covered

It is designed to be stable, minimal, and production-ready as a foundation.

---

## 🧠 Core Features

### 1. Session-Aware Memory
- Every request requires `X-Session-Id`
- User and assistant messages are automatically persisted
- Session isolation enforced

### 2. Turn-Aware Token Trimming
- Token budget controlled via environment variable: