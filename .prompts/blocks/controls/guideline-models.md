**Guideline: Models**

Let the Models do their job. All data must pass through strict Pydantic TydeAdaptor validation before it is loaded into the Engine. Do not worry about excessively checking the existence of attributes on objects to prevent RuntimeErrors. The Models are there for a reason. You may assume the attributes on typed variables exist unconditionally.