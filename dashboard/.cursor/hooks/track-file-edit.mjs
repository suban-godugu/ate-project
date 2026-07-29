#!/usr/bin/env node
import {
  findProjectRoot,
  trackEditedFile,
} from "./prompt-recorder.mjs";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function main() {
  const raw = await readStdin();
  let input = {};

  try {
    input = raw ? JSON.parse(raw) : {};
  } catch {
    input = {};
  }

  const filePath = input.file_path ?? input.filePath;
  if (filePath) {
    const projectRoot = findProjectRoot(input);
    trackEditedFile(projectRoot, filePath);
  }

  process.exit(0);
}

main().catch((error) => {
  console.error("[track-file-edit]", error.message);
  process.exit(0);
});
