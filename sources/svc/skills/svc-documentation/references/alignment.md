# Alignment of Objects and Operations

Alignment is optional coordination vocabulary for repeated costly disagreement about what a request refers to or what an operation means.
It becomes useful when normal knowledge owners, stable code identifiers, and clearer requests are already insufficient.
It does not add another source of product rules, technical invariants, runtime topology, evidence, permissions, or acceptance.
Those remain with their existing owners.

## Recognize the Need

Look for a recurring concrete pattern: names or screenshots fail to identify an object, boundaries are interpreted differently, an operation hides different effects, or a state change makes an old address invalid.
First try the cheaper repair: a semantic identifier, typed handle, route name, code symbol, existing schema or owner document, or a clearer request.
Do not create an Alignment document for a single ambiguous message or to avoid deciding who owns a rule.

When the pattern persists, define stable object and address conventions that consumers can use.
Derive a map from current anchors when possible rather than maintaining a second static copy.
Give an operation name durable meaning only when its observable effect and relevant boundaries can be understood and checked.
State how the address or operation depends on version, view, current state, or context.

## Connect a Request to Its Effect

Identify the object, its address, intended operation, boundary and invariants, applicable state, evidence, and any coordination checkpoint the work actually needs.
Express a change as the relevant current-to-desired state difference rather than positional prose alone.
Reference the normal owner for product or technical meaning and the real evidence for present state.
The project's existing authorization governs the action; making a request precise does not grant permission or require a new approval ritual.

For example, contributors repeatedly interpret “move this field up” as either changing display order or changing the underlying schema.
Refer to the field by its schema key, identify the view, and define “reorder display” as changing view order while preserving storage keys and data.
State the current and desired order and observe the resulting view and preserved data where relevant.
This vocabulary removes the repeated referential mismatch; it does not decide which order serves the product or who may publish the change.

## Maintain Only Useful Vocabulary

Update affected consumers when an address convention or operation meaning changes, including the state in which the old form stops applying.
Keep derived anchors connected to their source and retire stale maps or terms rather than leaving both in the current path.
Use actual recurring misunderstanding and corrected operations as feedback on whether the convention helps.
If ordinary identifiers and owner documentation now suffice, remove the extra coordination layer.
The [alignment request template](../assets/templates/alignment-request.template.md) is an optional prompt for this admitted need, not a required request schema.
