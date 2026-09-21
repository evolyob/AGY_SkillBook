# Phase 3 Protocol: Evidence-Based Fact-Checking

## Objective
Evaluate data accuracy, audit claim provenance, and assign reliability levels to prevent unverified assumptions or hallucinations from entering final deliverables.

## 3-Tier Evidence Hierarchy (Business & Technical)
- **Level 1 (Verified / High Reliability)**: Direct database entries, official API specs, signed contracts, or system logs.
- **Level 2 (Internal / Moderate Reliability)**: Internal draft documents, PRD specifications, or team discussion notes.
- **Level 3 (Unverified / Advisory Risk)**: Verbal statements, informal memos, unbacked assumptions, or AI-generated hypotheses.

## Audit Rules
1. Every critical claim or metric in the report must carry an assigned Evidence Level (L1, L2, L3).
2. Flag any Level 3 claim that is used to support a high-impact design or business decision as **[HIGH RISK: UNVERIFIED]**.
