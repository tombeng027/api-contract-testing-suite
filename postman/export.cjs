const fs = require("node:fs");
const path = require("node:path");
const cases = JSON.parse(fs.readFileSync(path.join(__dirname, "requests.json"), "utf8"));
const checks = fs.readFileSync(path.join(__dirname, "checks.js"), "utf8").replace(/\r\n/g, "\n");
const collection = {
    info: {
        name: "Synthetic Catalog Critical Contracts",
        schema: "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    variable: [{key: "base_url", value: "http://127.0.0.1:8001"}],
    event: [{listen: "test", script: {type: "text/javascript", exec: checks.split("\n")}}],
    item: cases.map(entry => ({
        name: entry.name,
        request: {method: "GET", url: "{{base_url}}" + entry.path},
        event: [{
            listen: "prerequest",
            script: {type: "text/javascript", exec: [
                "pm.variables.set('expected', " + JSON.stringify(JSON.stringify(entry.expected)) + ");"
            ]}
        }]
    }))
};
fs.writeFileSync(
    path.join(__dirname, "catalog.postman_collection.json"),
    JSON.stringify(collection, null, 2) + "\n"
);
