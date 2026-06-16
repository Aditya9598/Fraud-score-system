import { spawn } from "node:child_process";
import { test } from "node:test";
import assert from "node:assert/strict";
import { runScorer } from "../worker.js";

test("runScorer uses stdin pipe not shell", async () => {
  const mockBin = process.execPath;
  const mockScript = `
    const chunks = [];
    process.stdin.on('data', c => chunks.push(c));
    process.stdin.on('end', () => {
      const input = JSON.parse(Buffer.concat(chunks).toString());
      console.log(JSON.stringify({
        contract_version: '1.0',
        transaction_id: input.transaction_id,
        risk_score: 10,
        risk_level: 'low',
        reasons: []
      }));
    });
  `;

  const score = await runScorer(
    {
      contract_version: "1.0",
      transaction_id: "tx-mock",
      user_id: 1,
      amount: 100,
      type: "credit",
      merchant: "test",
    },
    mockBin,
    ["-e", mockScript]
  );

  assert.equal(score.transaction_id, "tx-mock");
  assert.equal(score.risk_score, 10);
});

test("runScorer rejects invalid contract from real scorer when built", async (t) => {
  const scorerPath = new URL("../../scorer/target/debug/scorer", import.meta.url).pathname;
  t.skip(!process.env.RUN_SCORER_INTEGRATION, "set RUN_SCORER_INTEGRATION=1 to run");
  await assert.rejects(() =>
    runScorer({
      contract_version: "2.0",
      transaction_id: "tx-bad",
      user_id: 1,
      amount: 100,
      type: "credit",
      merchant: "test",
    }, scorerPath)
  );
});
