# Working Methods

Choose the method that addresses the current gap.
These are reasoning aids, not mandatory stages or Agent roles.

| Method | Use when | Useful result |
| --- | --- | --- |
| [Explore](explore/index.md) | A decision needs information you do not yet have | Supported finding and remaining uncertainty |
| [Design](design/index.md) | The intended behavior or solution needs a choice | Concrete proposal and its reasons |
| [Implementation](implementation/index.md) | An intended change is ready to make | Changed artifact and local feedback |

Use [Verification](../verification/index.md) to judge what the resulting evidence supports.

## When Work Stops Advancing

Repeated searches, explanations, patches, or reviews deserve reconsideration when they neither improve the artifact nor change what you know.
Ruling out an explanation or identifying a necessary external wait is useful progress; elapsed time and tool-call counts alone do not measure it.
Before repeating work, identify what has changed or what a new observation could distinguish.
A retry can be useful when conditions changed or a transient failure makes another attempt informative.

Revisit the question when the goal is unclear, the evidence path when observations are missing, the design when local repairs keep exposing the same boundary, or the assignment when the work needs different capabilities.
Use an appropriate wait or notification mechanism for an external dependency instead of repeatedly inspecting unchanged state.
Preserve the current conclusion and next useful action in the [task packet](../task-packet/index.md).
When continuation is not feasible, return the supported result and the specific unmet condition.
