# Information Asset Valuation & Risk Rating Guide (Advisory Reference)

> [!NOTE]
> This guide is an advisory reference for human asset owners. The `asset-risk` automated engine does NOT calculate or hardcode these values.

## 1. Asset Valuation Criteria (5 / 3 / 1 Scale)

### Hardware Assets
- **Availability (A)**:
  - **5**: Tolerable outage $\le$ 4 hours.
  - **3**: Tolerable outage 4 hours to 1 business day.
  - **1**: Tolerable outage $>$ 1 business day.

### Software Assets
- **Confidentiality (C)**:
  - **5**: Proprietary IP / trade secrets critical to business continuity.
  - **3**: Company-owned, restricted from third-party use without consent.
  - **1**: Publicly available tools, freeware, open source.
- **Integrity (I)**:
  - **5**: Flaw causes operational shutdown or legal violation.
  - **3**: Flaw causes manual fallback, reporting delays, or inconvenience.
  - **1**: Flaw does not affect operations.
- **Availability (A)**:
  - Same as hardware (5: $\le$4h, 3: 4h~1d, 1: $>$1d).

### Data & Document Assets
- **Confidentiality (C)**:
  - **5 (Confidential)**: Requires explicit owner consent to access.
  - **3 (Internal)**: Restricted to NDA-bound personnel.
  - **1 (Public)**: Non-confidential public information.
- **Integrity (I)**:
  - **5**: Compromises customer balances, privacy, or financial reports.
  - **3**: Affects managerial decisions or execution precision.
  - **1**: No operational impact.
- **Availability (A)**:
  - **5**: Timely absence directly halts operations or violates regulations.
  - **3**: Timely absence causes operational inconvenience.
  - **1**: No time sensitivity.

### Personnel Assets
- **Confidentiality (C)**:
  - **5**: Access to all data tiers including Confidential.
  - **3**: Access to Internal and Public data.
  - **1**: Access to Public data only.
- **Availability (A)**:
  - **5**: Shortest tolerable replacement lead time (single point of failure).
  - **3**: Moderate tolerable replacement lead time.
  - **1**: High redundancy, longest tolerable replacement lead time.

## 2. Risk Calculation Model
Risk score $R$ is calculated natively by Excel:
$$R = \text{Asset Value } (V) \times \text{Threat Likelihood } (T) \times \text{Vulnerability Severity } (V_u)$$
Where $V = \max(C, I, A)$ and $V, T, V_u \in \{1, 3, 5\}$.

### Discrete States & Risk Tiers (1 to 125)
- **High Risk ($R \ge 45$)**: 45, 75, 125 $\implies$ Risk treatment plan required.
- **Medium Risk ($15 \le R \le 44$)**: 15, 25, 27 $\implies$ Monitor and evaluate controls.
- **Low Risk ($R \le 14$)**: 1, 3, 5, 9 $\implies$ Accept risk.
