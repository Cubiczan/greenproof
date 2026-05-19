# Adversarial Challenge Templates — greenverify-ai

## Phase 0: Foundation Challenge
When a new decision enters CHP, the adversary MUST address:
1. Why is the proposed direction wrong? (vulnerability_strike)
2. What is the system not seeing? (invalidation_conditions)
3. What is the false consensus risk?

## Domain-Specific Challenges (Blockchain / DeFi)
1. What smart contract vulnerability vectors exist (reentrancy, flash loan, oracle manipulation)?
2. How does transaction finality risk affect the decision? What if a chain reorg occurs?
3. What governance attack vectors exist if protocol parameters change post-deployment?
4. What is the immutable transaction risk — once on-chain, this cannot be reversed?
5. How does MEV extraction risk affect the expected outcome of this decision?

## Round 3: Implementation Drift Check
1. Does the implementation match the locked spec acceptance criteria?
2. Are operational handoffs and owner capacity accounted for?
3. Is evidence quality sufficient for the decision domain?

## Council Spawn Triggers
When confidence <85% on high-stakes decisions:
- Attacker Model 1: Challenge foundational assumptions
- Attacker Model 2: Challenge operational feasibility
- Synthesizer: Resolve contradictions and produce final recommendation
