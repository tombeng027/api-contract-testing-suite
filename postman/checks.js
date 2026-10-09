const expected = JSON.parse(pm.variables.get("expected"));
const payload = pm.response.json();

function object(value) {
    pm.expect(value).to.be.an("object");
    pm.expect(value).not.to.equal(null);
    pm.expect(Array.isArray(value)).to.equal(false);
}

function product(value) {
    object(value);
    pm.expect(value.id).to.be.a("number");
    pm.expect(Number.isInteger(value.id)).to.equal(true);
    pm.expect(value.id).to.be.within(1, 2147483647);
    for (const key of ["sku", "name"]) {
        pm.expect(value[key]).to.be.a("string");
        pm.expect(/\S/.test(value[key])).to.equal(true);
    }
    pm.expect(value.price_cents).to.be.a("number");
    pm.expect(Number.isInteger(value.price_cents)).to.equal(true);
    pm.expect(value.price_cents).to.be.at.least(0);
    pm.expect(value.available).to.be.a("boolean");
}

pm.test("status", function () {
    pm.expect(pm.response.code).to.equal(expected.status);
});
pm.test("media-type", function () {
    const header = pm.response.headers.get("Content-Type");
    pm.expect(header).to.be.a("string");
    pm.expect(header.split(";")[0].trim().toLowerCase()).to.equal("application/json");
});
pm.test("schema", function () {
    if (expected.kind === "product") {
        product(payload);
    } else if (expected.kind === "list") {
        pm.expect(payload).to.be.an("array");
        payload.forEach(product);
    } else if (expected.kind === "error") {
        object(payload);
        object(payload.error);
        pm.expect(payload.error.code).to.be.oneOf(["PRODUCT_NOT_FOUND", "INVALID_REQUEST"]);
        pm.expect(payload.error.message).to.be.a("string");
        pm.expect(/\S/.test(payload.error.message)).to.equal(true);
    } else {
        throw new Error("Unknown expected response kind");
    }
});
pm.test("known-values", function () {
    const keys = ["id", "sku", "name", "price_cents", "available"];
    function exact(value, reference) {
        for (const key of keys) {
            pm.expect(value[key], key).to.equal(reference[key]);
        }
    }
    if (expected.kind === "product") {
        exact(payload, expected.value);
    } else if (expected.kind === "list") {
        pm.expect(payload.length).to.equal(expected.value.length);
        expected.value.forEach((value, index) => exact(payload[index], value));
    } else if (expected.kind === "error") {
        pm.expect(payload.error.code).to.equal(expected.value.error.code);
        pm.expect(payload.error.message).to.equal(expected.value.error.message);
    } else {
        throw new Error("Unknown expected response kind");
    }
});
