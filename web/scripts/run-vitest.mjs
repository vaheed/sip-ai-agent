#!/usr/bin/env node
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const argv = process.argv.slice(2);
const filteredArgs = [];
for (let index = 0; index < argv.length; index += 1) {
  const arg = argv[index];
  if (arg === "--ci" || arg.startsWith("--ci=")) {
    continue;
  }
  if (arg === "--reporters") {
    const value = argv[index + 1];
    if (value && !value.startsWith("-")) {
      filteredArgs.push("--reporter", value);
      index += 1;
      continue;
    }
    continue;
  }
  if (arg.startsWith("--reporters=")) {
    const value = arg.slice("--reporters=".length);
    if (value.length > 0) {
      filteredArgs.push(`--reporter=${value}`);
    }
    continue;
  }
  filteredArgs.push(arg);
}

const __dirname = dirname(fileURLToPath(import.meta.url));
const vitestBin = resolve(__dirname, "../node_modules/.bin/vitest");

const child = spawn(vitestBin, ["--run", ...filteredArgs], {
  stdio: "inherit",
  shell: process.platform === "win32",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});

child.on("error", (error) => {
  console.error("Failed to start Vitest:", error);
  process.exit(1);
});
