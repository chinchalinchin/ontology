**Constraint: Changes**

Changes that violate these constraints will be rejected.

- The only literal strings in the application codebase should be localized in `app.config.enums`. 
    - **NOTE**: This restriction does not apply to unit tests or logging.
- Code should never alter Asset Properties. Asset Properties are static and never change.
- Code that alters a Sprite Intentions belongs in TransitionMechanics. 
- Code that alters a Sprite Goals belongs in CognitionMechanics. 
- Code that alters Resource Stages belongs in SeasonMechanics.
- Do not enforce backwards compatibility. Do not turn the code into spaghetti to support outdated data structures. If a change requires breaking an interface, commit to an action and stay the course. Any changes that unnecessarily bend the code to support an old version of *an application in development* will be rejected. 