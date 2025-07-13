# Nether

> Nether means beneath, below, or underneath — representing both our minimalistic goals and system-level thinking.

## What is Nether?

Nether is a lightweight framework for rapid development and deployment of web services, built primarily on Python's standard library. Originally created to serve internal needs at Arjuna, it may or may not suit your use case — our goal is not to build a universal framework, but one that works best for us.

## Philosophy

- Favor the standard library – minimize external dependencies.
- Embrace asynchronous IO and efficient background task scheduling.
- Service failures shouldn't crash the app – services handle their own errors.
-Focus on observability and graceful shutdown (no orphaned threads).
- Avoid premature complexity – Clean Architecture & DDD come later.
