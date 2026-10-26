# Condition predicates are single-token equality

A v2 transition predicate uses only the form `<condition-variable> == <literal>`. The variable is nonempty lowercase snake case. The literal is either bare `true` or `false` for a boolean condition, or a nonempty single token containing ASCII letters, digits, dots, underscores, hyphens, or slashes for an exact string condition.

The predicate deliberately does not support quoted strings, spaces, empty values, multiline values, regular expressions, `in`, `!=`, logical operators, or nested expressions. Text-sensitive judgment belongs in a `workflow_script` producer that reduces the answer to a scalar condition such as `needs_human_review == true`. This keeps the route grammar inspectable and the parser small while avoiding the accidental evolution of a general expression language.

Whitespace is permitted only around the single equality operator, not inside the variable or literal. A predicate that violates the token rule is statically invalid under `wf validate`.
