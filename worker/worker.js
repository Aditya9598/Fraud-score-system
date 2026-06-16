import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadEnv() {
  try {
    const envPath = resolve(__dirname, "../.env");
    const content = readFileSync(envPath, "utf8");
    for (const line of content.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const [key, ...rest] = trimmed.split("=");
      if (key && rest.length) process.env[key] = rest.join("=");
    }
  } catch {
    // use defaults
  }
}

loadEnv();

const API_BASE_URL = process.env.API_BASE_URL || "http://127.0.0.1:8002";
const SCORER_BIN =
  process.env.SCORER_BIN ||
  resolve(__dirname, "../scorer/target/debug/scorer");
const POLL_INTERVAL_MS = Number(process.env.WORKER_POLL_INTERVAL_MS || 2000);
const SCORER_TIMEOUT_MS = Number(process.env.WORKER_SCORER_TIMEOUT_MS || 5000);
const CONTRACT_VERSION = "1.0";

export function runScorer(transaction, scorerBin = SCORER_BIN, scorerArgs = ["score"]) {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(scorerBin, scorerArgs, {
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error("scorer timeout"));
    }, SCORER_TIMEOUT_MS);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        reject(new Error(stderr || `scorer exited ${code}`));
        return;
      }
      try {
        resolvePromise(JSON.parse(stdout.trim()));
      } catch (e) {
        reject(new Error(`invalid scorer output: ${e.message}`));
      }
    });

    child.stdin.write(JSON.stringify(transaction));
    child.stdin.end();
  });
}

export async function fetchPending() {
  const res = await fetch(`${API_BASE_URL}/transactions/pending`);
  if (!res.ok) throw new Error(`pending fetch failed: ${res.status}`);
  return res.json();
}

export async function claimTransaction(id) {
  const res = await fetch(`${API_BASE_URL}/transactions/${id}/claim`, {
    method: "PATCH",
  });
  if (!res.ok) throw new Error(`claim failed: ${res.status}`);
  return res.json();
}

export async function submitScore(id, score) {
  const res = await fetch(`${API_BASE_URL}/transactions/${id}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(score),
  });
  if (!res.ok) throw new Error(`score submit failed: ${res.status}`);
  return res.json();
}

export async function markFailed(id) {
  const res = await fetch(`${API_BASE_URL}/transactions/${id}/fail`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`fail mark failed: ${res.status}`);
  return res.json();
}

export async function processOnce(scorerBin = SCORER_BIN) {
  const pending = await fetchPending();
  if (!pending.length) return 0;

  let processed = 0;
  for (const txn of pending) {
    if (txn.contract_version !== CONTRACT_VERSION) {
      await markFailed(txn.transaction_id);
      continue;
    }

    await claimTransaction(txn.transaction_id);
    try {
      const score = await runScorer(txn, scorerBin);
      await submitScore(txn.transaction_id, score);
      processed += 1;
    } catch {
      await markFailed(txn.transaction_id);
    }
  }
  return processed;
}

async function main() {
  const once = process.argv.includes("--once");
  console.log(`Worker polling ${API_BASE_URL}`);

  if (once) {
    const n = await processOnce();
    console.log(`Processed ${n} transaction(s)`);
    return;
  }

  for (;;) {
    try {
      const n = await processOnce();
      if (n > 0) console.log(`Processed ${n} transaction(s)`);
    } catch (err) {
      console.error("Worker error:", err.message);
    }
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
