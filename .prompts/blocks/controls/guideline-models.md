**Guideline: Models**

The models are there for a reason. All data must pass through strict Pydantic TydeAdaptor validation before it is loaded into the Engine. Code should **not** excessively check the existence of attributes on classes to prevent RuntimeErrors. It can be assumed the attributes on typed variables exist unconditionally.

