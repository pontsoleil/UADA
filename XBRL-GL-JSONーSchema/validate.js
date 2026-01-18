const fs = require("fs").promises;
const path = require("path");
const Ajv2020 = require("ajv/dist/2020");
const addFormats = require("ajv-formats");

async function loadSchema(uri) {
  const base = path.resolve(__dirname, "schemas");

  // Draft 2020-12 メインスキーマ
  if (uri === "http://json-schema.org/draft/2020-12/schema") {
    const fullPath = path.join(base, "draft2020-12.json");
    const schema = JSON.parse(await fs.readFile(fullPath, "utf8"));
    delete schema["$id"];
    return schema;
  }

  // 各 vocabulary メタスキーマ
  const vocabularies = [
    "core",
    "applicator",
    "unevaluated",
    "validation",
    "meta-data",
    "format-annotation",
    "content"
  ];

  for (const name of vocabularies) {
    if (uri === `http://json-schema.org/draft/2020-12/meta/${name}`) {
      const fullPath = path.join(base, "meta", `${name}.json`);
      const schema = JSON.parse(await fs.readFile(fullPath, "utf8"));
      delete schema["$id"];
      return schema;
    }
  }

  // その他カスタムスキーマ
  if (uri.includes("UNECE-BasicComponents.json")) {
    const fullPath = path.join(
      __dirname,
      "../uncefact/spec-JSONschema/JSONschema2020-12/library/BuyShipPay/D23B/UNECE-BasicComponents.json"
    );
    return JSON.parse(await fs.readFile(fullPath, "utf8"));
  }

  if (uri.includes("codelists/")) {
    const fileName = path.basename(uri);
    const fullPath = path.join(
      __dirname,
      "../uncefact/spec-JSONschema/JSONschema2020-12/library/BuyShipPay/D23B/codelists",
      fileName
    );
    return JSON.parse(await fs.readFile(fullPath, "utf8"));
  }

  throw new Error(`Unknown schema URI: ${uri}`);
}

const ajv = new Ajv2020({
  loadSchema,
  strict: false
});
addFormats(ajv);

(async () => {
  try {
    const schemaPath = path.join(__dirname, "schemas/xbrl-gl-cor-schema.json");
    const instancePath = path.join(__dirname, "samples/xbrl-gl-instance.json");

    const schema = JSON.parse(await fs.readFile(schemaPath, "utf8"));
    const data = JSON.parse(await fs.readFile(instancePath, "utf8"));

    const validate = await ajv.compileAsync(schema);
    const valid = validate(data);

    if (valid) {
      console.log("✅ Validation successful: data is valid against the schema.");
    } else {
      console.error("❌ Validation errors:");
      console.error(validate.errors);
    }
  } catch (err) {
    console.error("💥 Runtime error:", err);
  }
})();