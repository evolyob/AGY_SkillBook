<!-- Template C: Native Mermaid Visual Archetypes -->

#### 1. Dual-Track Chart: Volume vs. Target (`xychart-beta`)
<div class="chart-card">

```mermaid
%%{init: {'theme': 'neutral'}}%%
xychart-beta
    title "Quarterly Throughput vs. Performance Target"
    x-axis ["Q1", "Q2", "Q3", "Q4"]
    y-axis "Processed Units" 0 --> 500
    bar [120, 210, 350, 480]
    line [100, 190, 320, 460]
```

</div>

#### 2. Architecture Topology & Flow (`flowchart TD`)
<div class="chart-card">

```mermaid
flowchart TD
    ext["Untrusted Ingress / Clients"] --> gateway["Edge Gateway / Load Balancer"]
    gateway <==> tier1["Service Cluster 01"]
    gateway <==> tier2["Service Cluster 02"]
    tier1 --> core["Core Processing Worker"]
    tier2 ==> core
    admin(((Management Console))) -.-> |mTLS / Bastion| core
    core ==> storage[("Persistent Database / Storage")]
```

</div>

#### 3. Phased Roadmap & Dependency Schedule (`gantt`)
<div class="chart-card">

```mermaid
gantt
    title "Project Execution & Phased Delivery"
    dateFormat YYYY-MM-DD
    section Discovery & Scoping
      Baseline Audit :a1, 2026-01-01, 30d
      Risk Assessment :after a1, 14d
    section Implementation & Rollout
      Infrastructure Migration :2026-02-15, 25d
      Final Acceptance :15d
```

</div>

#### 4. Milestone Timeline (`timeline`)
<div class="chart-card">

```mermaid
timeline
    title "Annual Strategic Milestone Roadmap"
    Q1 : Baseline Scoping : Initial Assessment
    Q2 : Architecture PoC : Stress & Penetration Test
    Q3 : Multi-Factor Rollout : Compliance Verification
    Q4 : Disaster Recovery Drill : Annual Retrospective
```

</div>

#### 5. Specification & Requirement Traceability (`requirementDiagram`)
<div class="chart-card">

```mermaid
requirementDiagram
    requirement req_p0 {
      id: REQ-001-CORE
      text: Critical access must enforce dual-factor auth and automated audit logging
      risk: High
      verifymethod: Test
    }
    element auth_gateway {
      type: Component
    }
    auth_gateway - satisfies -> req_p0
```

</div>
