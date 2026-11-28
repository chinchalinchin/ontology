##### Bug B069: Silent Conjunct Dropping on ISL Compilation Failure

**STATUS**: OPEN
**SEVERITY**: MEDIUM

**Description**

In `src/app/services/translators/compiler.py` (`CompilerTranslator.compile`) and `src/app/services/translators/lamb.py` (`LambdaTranslator.compile`), syntax errors in an individual condition string are caught and logged, but compilation continues and appends the remaining conditions into the resulting `Transition`. This silently weakens a conjunction (`A and INVALID` compiles into `A`), causing transitions to fire under unintended states.

**Steps to Replicate**

1. Introduce a syntax error into one condition of a multi-condition rule in `src/data/config/intentions/main.yaml`.
2. Bootstrap the application and evaluate the transition when the remaining conditions hold.
3. Observe the transition firing despite the malformed condition.

**Proposed Remediation**

Fail fast during bootstrap by raising a configuration compilation error when any ISL condition fails to parse/compile in either `CompilerTranslator` or `LambdaTranslator`.
