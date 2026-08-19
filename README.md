# Payna | Multi-State License Compliance Graph & Renewal Engine

An advanced, end-to-end AI-agents capstone. You model the messy real world of U.S. money-transmitter and lender licensing — states, license types, requirements, renewal cadences, and the entities that operate across state lines — as a knowledge graph living in plain Postgres (adjacency lists, no Neo4j required). You build an LLM structured-extraction pass that pulls filing requirements and deadlines out of scanned regulator PDFs into typed records, load them as graph nodes and edges, then implement graph traversal that, given an entity and the states it operates in, computes exactly which requirements it owes and when they lapse. On top of that graph you wire an AI compliance agent that drafts a filing checklist and flags upcoming renewals — grounded strictly in the graph so it can never hallucinate a rule that isn't there. You finish with a FastAPI surface and an append-only audit trail so every answer is traceable back to the regulator document it came from.

Built step-by-step with [KhwajaLabs Build](https://khwajalabs.com).

## Stack
- Python
- LLM extraction
- graph model
- PostgreSQL
- FastAPI
