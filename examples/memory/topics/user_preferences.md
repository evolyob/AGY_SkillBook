# User Preferences & Storage Directives

## 1. File Storage & Export Rules

### 1.1 Default Deliverable Path
- **Mandate**: Always export official deliverables (.pptx, .docx, .pdf, spreadsheets) and generated design assets directly to `~/Downloads` (or configured deliverable directory).

### 1.2 Text Encoding Compatibility
- **Mandate**: Markdown and text exports MUST use `utf-8-sig` (UTF-8 with BOM) for seamless Windows/macOS/cross-platform compatibility.

### 1.3 Memory Mutation Trigger
- **Mandate**: Write to `~/.gemini/memory/` ONLY upon explicit user instruction ("remember this", "save to memory", or `/learn`).
- **Prohibit**: Automatically persisting general conversation output to memory without explicit user approval.

---

## 2. Resource & Safety Budgets

### 2.1 Download Safety Limit
- **Mandate**: Halt and request explicit confirmation if a single download package exceeds configured threshold (e.g. **480 MB**).

### 2.2 Conversation Retention Budget
- **Mandate**: Respect local conversation log limits configured in `config.json` (e.g. **39 MB** cap).
