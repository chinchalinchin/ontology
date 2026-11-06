#### Refactor: Phase 04.06 - Menu Consolidation

**Overview** 

Review, refactor and consolidate Menus and Widgets.

**Notes**

* Menus are in need of enumeration and formal induction into the application semantics. There are lots of literal strings scattered across the modules and services.
* Extensive use of duck-typing in app.game.menus.modules.layout. Inconsistent use of enums. Lots of math calculations that look prime for Cythonization.
* Need to separate the menu models from the menu logic. (Done.)
    * Renamed EventContext to EventData to prevent ambiguity with MenuContexts.
* The concept of Inventory needs further elaboration.
* All of the duck-typing suggests there are core ambiguities in the model and application flow. The application is defensive because it needs to be, in order to work. 