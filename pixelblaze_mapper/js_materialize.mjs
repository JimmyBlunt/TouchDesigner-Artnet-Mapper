import vm from "node:vm";

let input = "";
for await (const chunk of process.stdin) input += chunk;

try {
  const request = JSON.parse(input);
  if (typeof request.source !== "string") throw new Error("source must be text");
  if (!Number.isSafeInteger(request.pixelCount) || request.pixelCount < 0) {
    throw new Error("pixelCount must be a non-negative integer");
  }
  const sandbox = Object.create(null);
  sandbox.pixelCount = request.pixelCount;
  sandbox.Math = Math;
  const context = vm.createContext(sandbox, {
    name: "pixelblaze-mapper",
    codeGeneration: { strings: false, wasm: false },
  });
  const script = new vm.Script(`(${request.source})(pixelCount)`, {
    filename: "pixelblaze-map.js",
  });
  const result = script.runInContext(context, { timeout: 500 });
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  process.stderr.write(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
