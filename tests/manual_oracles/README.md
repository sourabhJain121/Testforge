# TestForge Manual Oracles & Provenance Separation Policy

## Purpose & Scope
This directory (`tests/manual_oracles/`) houses unit test oracles authored by human engineers during Phase 2 investigative analysis.

Under the **Provenance Rule** of TestForge:
1. **Pipeline-Only Results**: Any result, mutation score, or coverage metric reported as an achievement of TestForge must be generated autonomously end-to-end by the pipeline (`IntelligentASTSynthesizer`, `TestForgeOrchestrator`, reflection repair loops) starting strictly from the target source code and minimal starter tests.
2. **Manual Oracles (`tests/manual_oracles/`)**: Hand-written oracles must NEVER be mixed into autonomous benchmark tables or claimed as autonomous agent achievements. They are retained strictly as:
   - Gold-standard reference specifications to study how humans write tests vs how agents write tests.
   - Analysis tools for investigating equivalent vs killable mutants.
   - Dual-reporting: When reporting benchmark numbers, both figures must be reported distinctly:
     - **Pipeline-Only**: What the autonomous system achieved without human assistance.
     - **Pipeline + Manual Oracles**: What the combined system + gold-standard reference achieves.

## Files
- `test_manual_discount.py`: Human-written precision tests killing `MUT_MATH_FUNC_018` (round to 1 decimal place).
- `test_manual_order_fsm.py`: Human-written FSM lifecycle transition and audit trail tests killing 60 state-machine mutants.
