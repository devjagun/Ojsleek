Repository https://github.com/gvergnaud/ts-pattern Commit: 0e15315eafbbb813a91bad34496418846981c1b1
Title Set and Map quantifier and size chainables

P.set() must support quantifier chainables some(pattern), every(pattern), and none(pattern): some fails on empty sets, every and none match empty sets. P.set() must also support minSize(n), maxSize(n), size(n), empty(), and nonEmpty() size constraints.
P.map() must support key quantifiers someKey(pattern), everyKey(pattern), noneKey(pattern) and value quantifiers someValue(pattern), everyValue(pattern) with the same empty-input semantics. P.map() must also support minSize(n), maxSize(n), size(n), empty(), and nonEmpty() size constraints.
Invalid bounds for minSize/maxSize/size on either P.set() or P.map() throw with format `\`P.set().<method>\`` or `\`P.map().<method>\`` followed by `` expected a non-negative integer, received <value>``.
Named selections under P.set() quantifiers collect matching elements as arrays. Named selections under P.map() key quantifiers collect matching keys; under value quantifiers, matching values. The inferred TypeScript type of a named selection is an array of the container's element, key, or value type respectively — not narrowed to the subpattern's type.
All P.set() and P.map() size and quantifier patterns fail on non-Set and non-Map inputs respectively.
Quantifier and size chainables may be composed freely, and each chained call intersects with the previous pattern.
