#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import {
  appendPromptRecord,
  deriveTitle,
  findProjectRoot,
  getNextStepId,
  todayIsoDate,
} from "./.cursor/hooks/prompt-recorder.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const prompt = process.argv.slice(2).join(" ").trim();

if (!prompt) {
  console.error("Usage: npm run record-prompt -- \"Your prompt text here\"");
  process.exit(1);
}

const projectRoot = findProjectRoot({});
const stepId = getNextStepId(projectRoot);
const date = todayIsoDate();
const title = deriveTitle(prompt);

appendPromptRecord(projectRoot, { stepId, date, title, prompt });
console.log(`Recorded ${stepId}: ${title}`);
