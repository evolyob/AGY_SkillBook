# Subagent Dispatch & Isolation Protocol (`subagent_dispatch.md`)

> **Core Philosophy**: Minified contract-first dispatch with strict context quotas, exclusive write paths, and 2-retry circuit breaker.

---

## 1. The 4-Step Execution Pipeline
1. **Pre-flight**: Primary agent establishes and writes shared interfaces (`typing.Protocol`) or schema files (e.g. `types.py`) before parallel dispatch.
2. **Map (Isolation)**: Dispatch workers across mutually exclusive `Allowed Write Paths` with designated read-only context.
3. **Scan (Integration)**: Main agent runs deterministic integration test or lint script across all touched files.
4. **Circuit Breaker**: Workers execute verification ONCE per dispatch; if it fails, report raw error logs immediately without recursive internal debugging or probing out-of-scope files. Main agent re-dispatches error trace (maximum **2 retries**); halt and write `FAILED_REMEDIATION_REPORT.md` (in workspace root) on 3rd failure.

---

## 2. Hard Context & Cost Quotas
- **Tool Reuse Gate**: Mandatory check against `~/.gemini/skills/SKILLS.md`. Workers MUST directly execute declared CLI tools instead of generating redundant one-off scratch scripts.
- **Read-Only Quota**: Maximum **2 reference files** per subagent (e.g. 1 type stub + 1 schema).
- **Stateless Dispatch**: Prohibit conversational history dumps. Inject only target input data and acceptance commands.
- **Model Tiering**: Default `Model: "flash"` for extraction, parsing, and batch sharding; reserve `inherit`/`pro` for complex logic.

---

## 3. High-Density Dispatch Proposal (Presented to User)
Dynamically output the execution table:

```markdown
### 🚀 Dispatch Plan

| ID | Target / Shard | Read-Only Context | Allowed Write Paths | Verification Command |
|---|---|---|---|---|
| 0 | Pre-flight Interface | - | `types.py` | Built by primary agent |
| 1 | `scripts/parser.py` | `types.py` | `scripts/parser.py`, `tests/test_parser.py` | `python3 -m unittest tests/test_parser.py` |
| 2 | `scripts/cli.py` | `types.py` | `scripts/cli.py`, `tests/test_cli.py` | `python3 -m unittest tests/test_cli.py` |

> 💡 Run parallel dispatch? (Y/n)
```
