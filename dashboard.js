"use strict";
const $ = (id) => document.getElementById(id);
const accents = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24"];
const fmt = (value) => String(value);
function element(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = String(text);
  return e;
}
function message(text, error = false) {
  $("message").textContent = text;
  $("message").classList.toggle("error", error);
}
async function api(path, payload) {
  const response = await fetch(path, {
    method: payload === undefined ? "GET" : "POST",
    headers: payload === undefined ? {} : {"Content-Type": "application/json"},
    body: payload === undefined ? undefined : JSON.stringify(payload)
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Request failed");
  return body;
}
function renderShard(shard) {
  const card = element("article", "shard");
  card.style.setProperty("--accent", accents[shard.id % accents.length]);
  const head = element("div", "shard-head");
  head.append(element("span", "", "SHARD " + shard.id),
              element("span", "shard-index", "#" + String(shard.id).padStart(2, "0")));
  card.append(head);
  const accounts = Object.entries(shard.accounts);
  const total = accounts.reduce((sum, [, balance]) => sum + Number(balance), 0);
  card.append(element("div", "shard-total", total.toLocaleString(undefined, {maximumFractionDigits:8}) + " DDC"));
  card.append(element("p", "muted", accounts.length + " accounts"));
  for (const [name, balance] of accounts) {
    const line = element("div", "account");
    line.append(element("span", "", name), element("span", "", fmt(balance)));
    card.append(line);
  }
  return card;
}
function render(state) {
  const ledger = state.ledger;
  const accounts = ledger.shards.flatMap(s => Object.keys(s.accounts));
  $("shard-count").textContent = ledger.shards.length;
  $("account-count").textContent = accounts.length;
  $("supply").textContent = ledger.total_supply;
  $("pending").textContent = ledger.pending_receipts.length;
  $("shards").replaceChildren(...ledger.shards.map(renderShard));

  for (const id of ["sender", "recipient"]) {
    const select = $(id);
    const previous = select.value;
    select.replaceChildren(...accounts.map(name => {
      const opt = element("option", "", name);
      opt.value = name;
      return opt;
    }));
    if (accounts.includes(previous)) select.value = previous;
    else if (id === "recipient" && accounts.length > 1) select.value = accounts[1];
  }
  const receipts = $("receipts");
  if (ledger.pending_receipts.length === 0) receipts.replaceChildren(element("p", "muted", "All cross-shard transfers settled."));
  else {
    receipts.replaceChildren(...ledger.pending_receipts.map(r => {
      const line = element("div", "receipt");
      const label = element("div", "", "#" + r.id + " · " + r.sender + " → " + r.recipient);
      label.append(element("p", "muted", r.amount + " DDC · shard " + r.source + " → " + r.destination));
      const button = element("button", "secondary", "Settle");
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          await api("/api/settle", {receipt_id:r.id});
          message("Receipt #" + r.id + " settled.");
          await refresh();
        } catch (e) {message(e.message, true); button.disabled = false;}
      });
      line.append(label, button);
      return line;
    }));
  }
  $("events").replaceChildren(...state.events.slice(0, 12).map(evt => {
    const line = element("div", "event");
    line.append(element("span", "", evt.detail), element("span", "muted", "#" + evt.id));
    return line;
  }));
}
async function refresh() {
  try { render(await api("/api/state")); }
  catch (e) {message("Could not load dashboard: " + e.message, true);}
}
$("account-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.currentTarget);
  try {
    const result = await api("/api/accounts", {name:form.get("name"),balance:form.get("balance")});
    message("Account created on shard " + result.shard);
    e.currentTarget.reset();
    await refresh();
  } catch (err) {message(err.message, true);}
});
$("transfer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.currentTarget);
  try {
    const result = await api("/api/transfers", {sender:form.get("sender"),recipient:form.get("recipient"),amount:form.get("amount")});
    message(result.receipt_id === null ? "Same-shard transfer completed." : "Cross-shard receipt #" + result.receipt_id + " queued. Click Settle to credit recipient.");
    await refresh();
  } catch (err) {message(err.message, true);}
});
$("refresh").addEventListener("click", refresh);
refresh();

function showBenchmark(result) {
  if (!result) return;
  const m = result.measured_local_execution;
  $("lab-results").hidden = false;
  $("lab-tps").textContent = m.completed_tps.toLocaleString(undefined,{maximumFractionDigits:0});
  $("lab-wall").textContent = m.wall_seconds.toFixed(3) + " s";
  $("lab-p95").textContent = m.transfer_latency_p95_ms.toFixed(3) + " ms";
  $("lab-correct").textContent = result.correctness.passed ? "PASS" : "FAIL";
  $("lab-status").textContent = "Completed on this local machine";
  $("lab-detail").textContent = "SIMULATED: " + result.simulated_workload.generated_transactions +
    " transactions (" + result.simulated_workload.cross_shard_transactions + " cross-shard). " +
    "MEASURED: settlements " + m.receipt_settlements + "; source-shard counts " +
    m.source_transactions_per_shard.join(" / ") + ".";
}
$("run-benchmark").addEventListener("click", async () => {
  const button = $("run-benchmark");
  button.disabled = true;
  $("lab-status").textContent = "Executing real local benchmark…";
  try {
    const data = await api("/api/benchmark", {
      category:"sharding",algorithm:"sha",transactions:10000,
      cross_percent:25,seed:20261101,fault:"none"
    });
    showBenchmark(data.result);
  } catch (err) {
    $("lab-status").textContent = "Benchmark failed: " + err.message;
  } finally {
    button.disabled = false;
  }
});
api("/api/benchmark").then(data => showBenchmark(data.result)).catch(() => {});
