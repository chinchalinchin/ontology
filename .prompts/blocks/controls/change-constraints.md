**Change Constraints**

Changes that violate these constraints will be rejected.

- The only literal strings in the application codebase should be localized in `app.config.enums`. 
    - **NOTE**: This restriction does not apply to unit tests or logging.
- Code should never alter Asset Properties. Asset Properties are static and never change.
- Code that alters a Sprite's Intention belongs in TransitionMechanics. 
- Code that alters a Sprite's Goal belongs in CognitionMechanics. 
- Code that alters Resource Stages belongs in SeasonMechanics.

