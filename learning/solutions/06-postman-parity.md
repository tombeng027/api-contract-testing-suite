# Lab 6 reference explanation

Read after attempting [Lab 6](../labs/06-postman-parity.md).

1. A price of 2500 is a valid nonnegative integer. Status, media type and structural checks pass. Independent expectation 2501 differs, so `known-values` fails.
2. A documented 404 with `PRODUCT_NOT_FOUND` / `Product not found` is the expected successful outcome of a negative API test.
3. A refused connection supplies no product/error contract to evaluate. CLI exit 1 alone cannot distinguish that failure from an assertion, syntax error or another failed run. Inspect request and assertion evidence.
4. `category` is additive and allowed by the selected v1 response consumer. Known fields must still satisfy their constraints and independently expected values.

Reference source is [the shared assertion script](../../postman/checks.js). The [exported collection](../../postman/catalog.postman_collection.json) embeds it so it can be imported without local script dependencies. [Export source](../../postman/export.cjs) generates the collection from the script and independent request expectations; tests detect a stale export.

Selected regression evidence separates a schema-valid wrong price from the intended known-value assertion failure. It also demonstrates integral numeric acceptance and additive tolerance, plus missing-field/type/bound/status/media defects. These probes are not exhaustive proof of compatibility.

The Python wrapper retains the exact collection snapshot, stdout and stderr in a unique ignored evidence directory. It preserves exit codes rather than treating a nonzero code as a learner-grade result. It deliberately does not create practice-runner answers, scores or completion records.
