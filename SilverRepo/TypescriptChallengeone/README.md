Repository https://github.com/gvergnaud/ts-pattern Commit: 0e15315eafbbb813a91bad34496418846981c1b1
Title Array quantifier and length chainables
P.array() chainables must support some(pattern), none(pattern), and every(pattern): some fails on empty arrays, none/every match empty arrays.
Selections from quantifiers must stay list-shaped: some/every collect values from matching elements, while none returns empty lists for declared selections.
For named selections under quantifiers, selection element types must remain the array input element union type, not narrowed to the quantifier subpattern type.
When quantifiers are chained after P.array(elementPattern), both the base element constraint and quantifier constraint must hold in the same branch.
Quantifier and length chainables must narrow the input type to the array branch.
P.array() must support minLength(n), maxLength(n), length(n), empty(), and nonEmpty().
Invalid bounds for minLength/maxLength/length must throw with the exact message format ``\`P.array().<method>\` expected a non-negative integer, received <value>`` - where the method name is wrapped in backticks and <value> is the raw value passed.
The full feature set must compose with optional() and variadic tuple usage.
