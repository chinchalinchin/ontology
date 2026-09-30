**Data Models**

Let the data model validators do their job. All data must pass through strict Pydantic TydeAdaptor validation before it is loaded into the game. Do not worry about excessively checking the existence of attributes on objects to prevent RuntimeErrors. The models are there for a reason. 

**Enums**

All enums are `class Test(str, Enum)`. Do not raise issues related to enum str comparisons. 

