**Change Constraints**

Changes that violate these constraints will be rejected.

- Code should never alter Asset Properties. Asset Properties are static and never change.
- The only code that should alter a Sprite's Intention is TransitionMechanics. 
- The only code that should alter a Sprite's Goal is CognitionMechanics. 
- The only literal strings in the application codebase should be localized in `app.config.enums`. 
    - **NOTE**: This restriction does not apply to unit tests or logging.

