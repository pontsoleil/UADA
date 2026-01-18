const Ajv = require("ajv");
const fs = require("fs");

const ajv = new Ajv({ strict: false });

const basic = JSON.parse(fs.readFileSync("D23B/UNECE-BasicComponents.json", "utf8"));
ajv.addSchema(basic, "https://example.com/UNECE-BasicComponents.json");

const core = JSON.parse(fs.readFileSync("./xbrl-gl-core-schema.json", "utf8"));
ajv.addSchema(core, "https://xbrl.org/XBRL-GL-YYYY-MM-DD/schemas/gl-cor.json");

const instance = JSON.parse(fs.readFileSync("./xbrl-gl-instance.json", "utf8"));
const validate = ajv.getSchema("https://xbrl.org/XBRL-GL-YYYY-MM-DD/schemas/gl-cor.json");

const valid = validate(instance);
console.log(valid ? "✅ OK" : validate.errors);
