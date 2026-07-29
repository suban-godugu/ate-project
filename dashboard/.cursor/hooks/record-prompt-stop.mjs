#!/usr/bin/env node
import {
  clearSessionState,
  findProjectRoot,
  loadSessionState,
  updatePromptArtifacts,
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

  const state = loadSessionState();
  if (!state?.stepId) {
    process.stdout.write("{}");
    process.exit(0);
  }

  const projectRoot = state.projectRoot ?? findProjectRoot(input);
  const files = Array.isArray(state.files) ? state.files.sort() : [];

  if (files.length > 0) {
    updatePromptArtifacts(projectRoot, state.stepId, files);
  }

  clearSessionState();
  process.stdout.write("{}");
  process.exit(0);
}

main().catch((error) => {
  console.error("[record-prompt-stop]", error.message);
  process.stdout.write("{}");
  process.exit(0);
});
