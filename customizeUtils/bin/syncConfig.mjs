import * as fs from "node:fs";
import * as path from "node:path";
import { CoreDirPath, ProjectRoot } from "../common.js";
import { normalizePath } from "vite";

/**
 * Syncs tsconfig.json, setting the "paths" key to resolve "@/*".
 */
function main() {
  const tsconfigFile = path.resolve(ProjectRoot, "tsconfig.json");
  let tsconfig = {};
  try {
    const contents = fs.readFileSync(tsconfigFile, { encoding: "utf-8" });
    tsconfig = JSON.parse(contents || "{}");
  } catch (err) {
    throw new Error("Failed to parse tsconfig.json");
  }

  tsconfig.compilerOptions ||= {};
  tsconfig.compilerOptions.paths ||= {};

  const corePath = normalizePath(path.relative(ProjectRoot, CoreDirPath));
  tsconfig.compilerOptions.paths["@/*"] = [`./${corePath}/*`];

  try {
    const contents = fs.writeFileSync(
      tsconfigFile,
      JSON.stringify(tsconfig, null, 2)
    );
    tsconfig = JSON.parse(contents || "{}");
  } catch (err) {
    throw new Error("Failed to parse tsconfig.json");
  }
}

main();
