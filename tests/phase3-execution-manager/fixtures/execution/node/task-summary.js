const assert = require("node:assert/strict");

function summarizeTasks(records) {
  if (records.length === 0) {
    throw new Error("at least one task is required");
  }

  let completed = 0;
  for (const record of records) {
    if (!record.taskId || !record.title || !["completed", "pending"].includes(record.status)) {
      throw new Error("invalid task record");
    }
    if (record.status === "completed") {
      completed += 1;
    }
  }

  const pending = records.length - completed;
  return {
    completed,
    pending,
    percentage: (completed / records.length) * 100,
  };
}

function main() {
  const records = [
    { taskId: "T-201", title: "Plan sandbox", status: "completed" },
    { taskId: "T-202", title: "Run tests", status: "completed" },
    { taskId: "T-203", title: "Write report", status: "pending" },
  ];

  console.log("ARES NODE EXAMPLE START");
  const summary = summarizeTasks(records);
  let invalidDataHandled = false;
  try {
    summarizeTasks([{ taskId: "T-204", title: "Invalid" }]);
  } catch {
    invalidDataHandled = true;
  }

  assert.deepEqual(summary, { completed: 2, pending: 1, percentage: 66.66666666666666 });
  console.log(`Completed tasks: ${summary.completed}`);
  console.log(`Pending tasks: ${summary.pending}`);
  console.log(`Completion: ${summary.percentage.toFixed(2)}%`);
  console.log(`Invalid record handled: ${invalidDataHandled ? "True" : "False"}`);
  console.log("ARES NODE EXAMPLE COMPLETE");
}

main();
