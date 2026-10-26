**Guideline: Debugging**

* Do not burn cycles digging through stack traces or inferring the functionality of code not present in the context. If the solution to the problem cannot be derived from the present context, suggest telemetry logs to add to the application at critical junctures to log and dump necessary debugging information.
* If the code you require is not present in the context, suggest a [Filter Strategy](#view-filter) for retrieving it.

