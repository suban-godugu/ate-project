#!/usr/bin/env node
import {
  appendPromptRecord,
  clearSessionState,
  deriveTitle,
  findProjectRoot,
  isDuplicatePrompt,
  loadSessionState,
  getNextStepId,
  saveSessionState,
  shouldSkipPrompt,
  todayIsoDate,
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

  const prompt = input.prompt ?? input.text ?? "";
  const projectRoot = findProjectRoot(input);

  if (shouldSkipPrompt(prompt) || isDuplicatePrompt(projectRoot, prompt)) {
    process.stdout.write(JSON.stringify({ continue: true }));
    process.exit(0);
  }

  const stepId = getNextStepId(projectRoot);
  const date = todayIsoDate();
  const title = deriveTitle(prompt);

  appendPromptRecord(projectRoot, { stepId, date, title, prompt });

  saveSessionState({
    stepId,
    date,
    title,
    prompt: prompt.trim(),
    projectRoot,
    files: [],
    startedAt: new Date().toISOString(),
    generationId: input.generation_id ?? null,
  });

  process.stdout.write(JSON.stringify({ continue: true }));
  process.exit(0);
}

main().catch((error) => {
  console.error("[record-prompt-start]", error.message);
  process.stdout.write(JSON.stringify({ continue: true }));
  process.exit(0);
});
