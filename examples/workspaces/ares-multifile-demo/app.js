const fs = require("node:fs");
const path = require("node:path");

function loadTasks() {
  const contents = fs.readFileSync(path.join(__dirname, "tasks.json"), "utf8");
  const data = JSON.parse(contents);
  if (!Array.isArray(data)) {
    throw new Error("tasks.json must contain an array");
  }
  return data;
}

function summarizeTasks(records) {
  if (records.length === 0) {
    throw new Error("tasks.json must contain at least one task");
  }
  let completed = 0;
  for (const record of records) {
    if (!record.id || !record.title || !["completed", "pending"].includes(record.status)) {
      throw new Error("each task requires id, title, and status");
    }
    if (record.status === "completed") completed += 1;
  }
  const total = records.length;
  const pending = total - completed;
  return { total, completed, pending, percentage: (completed / total) * 100 };
}

function main() {
  console.log("ARES MULTI-FILE NODE START");
  try {
    const summary = summarizeTasks(loadTasks());
    let invalidHandled = false;
    try {
      summarizeTasks([{ id: "invalid" }]);
    } catch {
      invalidHandled = true;
    }
    if (!invalidHandled) throw new Error("invalid task data was not rejected");
    console.log(`Total tasks: ${summary.total}`);
    console.log(`Completed tasks: ${summary.completed}`);
    console.log(`Pending tasks: ${summary.pending}`);
    console.log(`Completion: ${summary.percentage.toFixed(2)}%`);
    console.log(`Invalid record handled: ${invalidHandled ? "True" : "False"}`);
    console.log("ARES MULTI-FILE NODE COMPLETE");
  } catch (error) {
    console.error(`Execution error: ${error.message}`);
    process.exitCode = 1;
  }
}

main();
