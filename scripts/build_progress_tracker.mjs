import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const catalogPath = path.join(root, "tmp", "cat_pyq", "classified_catalog.json");
const outputDir = path.join(root, "outputs", "cat_2026_pyq_system");
const previewDir = path.join(root, "tmp", "cat_pyq", "workbook_previews");
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const catalog = JSON.parse(await fs.readFile(catalogPath, "utf8"));
const totalRows = catalog.length;
const trackerLastRow = totalRows + 1;

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
const tracker = workbook.worksheets.add("Question Tracker");
const topicPlan = workbook.worksheets.add("Topic Plan");
const weekly = workbook.worksheets.add("Weekly Log");
const guide = workbook.worksheets.add("How to Use");
const lists = workbook.worksheets.add("Lists");

const COLORS = {
  navy: "#14213D",
  blue: "#2563EB",
  teal: "#0F766E",
  green: "#16A34A",
  amber: "#F59E0B",
  red: "#DC2626",
  paleBlue: "#EFF6FF",
  paleGreen: "#F0FDF4",
  paleAmber: "#FFFBEB",
  paleRed: "#FEF2F2",
  light: "#F8FAFC",
  mid: "#CBD5E1",
  dark: "#334155",
  white: "#FFFFFF",
};

function styleTitle(sheet, range, title) {
  sheet.getRange(range).merge();
  const cell = sheet.getRange(range.split(":")[0]);
  cell.values = [[title]];
  sheet.getRange(range).format = {
    fill: COLORS.navy,
    font: { bold: true, color: COLORS.white, size: 18 },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  sheet.getRange(range).format.rowHeight = 34;
}

function styleHeader(range) {
  range.format = {
    fill: COLORS.navy,
    font: { bold: true, color: COLORS.white },
    verticalAlignment: "center",
    horizontalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: COLORS.navy },
  };
  range.format.rowHeight = 30;
}

function formatCard(labelRange, valueRange, fill, numberFormat = "0") {
  dashboard.getRange(labelRange).merge();
  dashboard.getRange(valueRange).merge();
  dashboard.getRange(labelRange.split(":")[0]).format = {
    fill,
    font: { bold: true, color: COLORS.dark, size: 9 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  dashboard.getRange(valueRange).format = {
    fill,
    font: { bold: true, color: COLORS.navy, size: 18 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    numberFormat,
    borders: { preset: "outside", style: "thin", color: COLORS.mid },
  };
}

// Lists and validation sources.
lists.showGridLines = false;
lists.getRange("A1:E7").values = [
  ["Status", "Result", "Revision Status", "Priority", "Confidence"],
  ["Not Started", "", "Not Reviewed", "High", 1],
  ["In Progress", "Correct", "Review 1", "Medium", 2],
  ["Completed", "Incorrect", "Review 2", "Low", 3],
  ["Skipped", "Skipped", "Review 3", "", 4],
  ["", "", "Mastered", "", 5],
  ["", "", "Needs Work", "", ""],
];
styleHeader(lists.getRange("A1:E1"));
lists.getRange("A2:E7").format = { borders: { preset: "inside", style: "thin", color: COLORS.mid } };
lists.getRange("A:E").format.columnWidth = 19;
lists.freezePanes.freezeRows(1);

// Question tracker.
tracker.showGridLines = false;
styleTitle(tracker, "A1:U1", "CAT 2026 - Individual Question Tracker");
const headers = [
  "Question ID", "Section", "Subsection", "Topic", "Year", "Slot", "Question No", "Set No",
  "Archive Difficulty", "Question Cue", "Source Link", "Status", "Attempt Date", "Result",
  "Time (min)", "Confidence (1-5)", "Review Date", "Revision Status", "Notes", "Classification Review", "Due?",
];
tracker.getRange("A2:U2").values = [headers];
styleHeader(tracker.getRange("A2:U2"));

const trackerRows = catalog.map((row) => [
  row.question_id,
  row.section,
  row.subsection,
  row.topic,
  Number(row.year),
  Number(row.slot),
  Number(row.question_number),
  row.set_number === "" || row.set_number == null ? null : Number(row.set_number),
  row.archive_difficulty,
  row.question_cue,
  row.question_url || row.source_page,
  "Not Started",
  null,
  "",
  null,
  null,
  null,
  "Not Reviewed",
  "",
  row.needs_review ? "Yes" : "No",
  null,
]);
tracker.getRange(`A3:U${trackerLastRow + 1}`).values = trackerRows;
const firstDataRow = 3;
const lastDataRow = totalRows + 2;
tracker.getRange(`U${firstDataRow}`).formulas = [[`=IF(AND($L${firstDataRow}="Completed",$Q${firstDataRow}<>"",$Q${firstDataRow}<=TODAY(),$R${firstDataRow}<>"Mastered"),"Due","")`]];
tracker.getRange(`U${firstDataRow}:U${lastDataRow}`).fillDown();

tracker.getRange(`L${firstDataRow}:L${lastDataRow}`).dataValidation = {
  rule: { type: "list", formula1: "'Lists'!$A$2:$A$5" },
};
tracker.getRange(`N${firstDataRow}:N${lastDataRow}`).dataValidation = {
  rule: { type: "list", formula1: "'Lists'!$B$2:$B$5" },
};
tracker.getRange(`P${firstDataRow}:P${lastDataRow}`).dataValidation = {
  rule: { type: "whole", operator: "between", formula1: 1, formula2: 5 },
};
tracker.getRange(`R${firstDataRow}:R${lastDataRow}`).dataValidation = {
  rule: { type: "list", formula1: "'Lists'!$C$2:$C$7" },
};
tracker.getRange(`M${firstDataRow}:M${lastDataRow}`).format.numberFormat = "yyyy-mm-dd";
tracker.getRange(`Q${firstDataRow}:Q${lastDataRow}`).format.numberFormat = "yyyy-mm-dd";
tracker.getRange(`O${firstDataRow}:P${lastDataRow}`).format.numberFormat = "0.0";
tracker.getRange(`A${firstDataRow}:U${lastDataRow}`).format = {
  font: { color: COLORS.dark, size: 9 },
  verticalAlignment: "top",
  borders: { insideHorizontal: { style: "thin", color: "#E2E8F0" } },
};
tracker.getRange(`J${firstDataRow}:K${lastDataRow}`).format.wrapText = true;
tracker.getRange(`S${firstDataRow}:S${lastDataRow}`).format.wrapText = true;
tracker.getRange(`L${firstDataRow}:L${lastDataRow}`).conditionalFormats.add("containsText", {
  text: "Completed", format: { fill: COLORS.paleGreen, font: { color: COLORS.green, bold: true } },
});
tracker.getRange(`N${firstDataRow}:N${lastDataRow}`).conditionalFormats.add("containsText", {
  text: "Incorrect", format: { fill: COLORS.paleRed, font: { color: COLORS.red, bold: true } },
});
tracker.getRange(`U${firstDataRow}:U${lastDataRow}`).conditionalFormats.add("containsText", {
  text: "Due", format: { fill: COLORS.paleAmber, font: { color: "#B45309", bold: true } },
});

const trackerTable = tracker.tables.add(`A2:U${lastDataRow}`, true, "QuestionTrackerTable");
trackerTable.style = "TableStyleMedium2";
tracker.freezePanes.freezeRows(2);
tracker.freezePanes.freezeColumns(4);

const trackerWidths = {
  A: 24, B: 12, C: 22, D: 34, E: 9, F: 8, G: 11, H: 9, I: 16, J: 44, K: 48,
  L: 15, M: 13, N: 12, O: 11, P: 14, Q: 13, R: 16, S: 28, T: 18, U: 9,
};
for (const [col, width] of Object.entries(trackerWidths)) tracker.getRange(`${col}:${col}`).format.columnWidth = width;

// Topic plan.
topicPlan.showGridLines = false;
styleTitle(topicPlan, "A1:L1", "CAT 2026 - Topic Mastery Plan");
const topicHeaders = ["Section", "Subsection", "Topic", "Total", "Completed", "Correct", "Accuracy", "Time Logged", "Progress", "Priority", "Target Date", "Notes"];
topicPlan.getRange("A2:L2").values = [topicHeaders];
styleHeader(topicPlan.getRange("A2:L2"));
const topicKeys = [...new Map(catalog.map((r) => [`${r.section}|${r.subsection}|${r.topic}`, [r.section, r.subsection, r.topic]])).values()]
  .sort((a, b) => a.join("|").localeCompare(b.join("|")));
const topicStart = 3;
const topicEnd = topicStart + topicKeys.length - 1;
topicPlan.getRange(`A${topicStart}:L${topicEnd}`).values = topicKeys.map(([section, subsection, topic]) => [
  section, subsection, topic, null, null, null, null, null, null, "Medium", null, "",
]);
for (let row = topicStart; row <= topicEnd; row++) {
  topicPlan.getRange(`D${row}:I${row}`).formulas = [[
    `=COUNTIFS('Question Tracker'!$B$${firstDataRow}:$B$${lastDataRow},$A${row},'Question Tracker'!$C$${firstDataRow}:$C$${lastDataRow},$B${row},'Question Tracker'!$D$${firstDataRow}:$D$${lastDataRow},$C${row})`,
    `=COUNTIFS('Question Tracker'!$B$${firstDataRow}:$B$${lastDataRow},$A${row},'Question Tracker'!$C$${firstDataRow}:$C$${lastDataRow},$B${row},'Question Tracker'!$D$${firstDataRow}:$D$${lastDataRow},$C${row},'Question Tracker'!$L$${firstDataRow}:$L$${lastDataRow},"Completed")`,
    `=COUNTIFS('Question Tracker'!$B$${firstDataRow}:$B$${lastDataRow},$A${row},'Question Tracker'!$C$${firstDataRow}:$C$${lastDataRow},$B${row},'Question Tracker'!$D$${firstDataRow}:$D$${lastDataRow},$C${row},'Question Tracker'!$N$${firstDataRow}:$N$${lastDataRow},"Correct")`,
    `=IF($E${row}=0,"",$F${row}/$E${row})`,
    `=SUMIFS('Question Tracker'!$O$${firstDataRow}:$O$${lastDataRow},'Question Tracker'!$B$${firstDataRow}:$B$${lastDataRow},$A${row},'Question Tracker'!$C$${firstDataRow}:$C$${lastDataRow},$B${row},'Question Tracker'!$D$${firstDataRow}:$D$${lastDataRow},$C${row})`,
    `=IFERROR($E${row}/$D${row},0)`,
  ]];
}
topicPlan.getRange(`J${topicStart}:J${topicEnd}`).dataValidation = {
  rule: { type: "list", formula1: "'Lists'!$D$2:$D$4" },
};
topicPlan.getRange(`K${topicStart}:K${topicEnd}`).format.numberFormat = "yyyy-mm-dd";
topicPlan.getRange(`G${topicStart}:G${topicEnd}`).format.numberFormat = "0%";
topicPlan.getRange(`H${topicStart}:H${topicEnd}`).format.numberFormat = "0.0";
topicPlan.getRange(`I${topicStart}:I${topicEnd}`).format.numberFormat = "0%";
topicPlan.getRange(`I${topicStart}:I${topicEnd}`).conditionalFormats.add("dataBar", { color: COLORS.blue, gradient: true });
topicPlan.getRange(`G${topicStart}:G${topicEnd}`).conditionalFormats.addCustom(
  `=AND($E${topicStart}>0,$G${topicStart}<0.7)`,
  { fill: COLORS.paleRed, font: { color: COLORS.red, bold: true } },
);
topicPlan.getRange(`G${topicStart}:G${topicEnd}`).conditionalFormats.addCustom(
  `=AND($E${topicStart}>0,$G${topicStart}>=0.7)`,
  { fill: COLORS.paleGreen, font: { color: COLORS.green, bold: true } },
);
const topicTable = topicPlan.tables.add(`A2:L${topicEnd}`, true, "TopicPlanTable");
topicTable.style = "TableStyleMedium2";
topicPlan.freezePanes.freezeRows(2);
topicPlan.freezePanes.freezeColumns(3);
const topicWidths = { A: 12, B: 24, C: 38, D: 10, E: 11, F: 10, G: 11, H: 13, I: 11, J: 11, K: 13, L: 28 };
for (const [col, width] of Object.entries(topicWidths)) topicPlan.getRange(`${col}:${col}`).format.columnWidth = width;

// Dashboard.
dashboard.showGridLines = false;
styleTitle(dashboard, "A1:N1", "CAT 2026 - PYQ Progress Dashboard");
dashboard.getRange("A2:N2").merge();
dashboard.getRange("A2").values = [["Live summary from the Question Tracker. Update status, result, time, and review dates after every attempt."]];
dashboard.getRange("A2:N2").format = { fill: COLORS.paleBlue, font: { color: COLORS.dark, italic: true }, verticalAlignment: "center" };
dashboard.getRange("A2:N2").format.rowHeight = 25;

const cards = [
  ["A4:B4", "A5:B6", "Total Questions", `=COUNTA('Question Tracker'!$A$${firstDataRow}:$A$${lastDataRow})`, COLORS.paleBlue, "0"],
  ["D4:E4", "D5:E6", "Completed", `=COUNTIF('Question Tracker'!$L$${firstDataRow}:$L$${lastDataRow},"Completed")`, COLORS.paleGreen, "0"],
  ["G4:H4", "G5:H6", "Overall Progress", "=IFERROR(D5/A5,0)", "#ECFDF5", "0%"],
  ["J4:K4", "J5:K6", "Accuracy", `=IFERROR(COUNTIF('Question Tracker'!$N$${firstDataRow}:$N$${lastDataRow},"Correct")/(COUNTIF('Question Tracker'!$N$${firstDataRow}:$N$${lastDataRow},"Correct")+COUNTIF('Question Tracker'!$N$${firstDataRow}:$N$${lastDataRow},"Incorrect")),0)`, COLORS.paleAmber, "0%"],
  ["M4:N4", "M5:N6", "Time Logged (min)", `=SUM('Question Tracker'!$O$${firstDataRow}:$O$${lastDataRow})`, "#F5F3FF", "0.0"],
  ["A8:B8", "A9:B10", "Revision Due", `=COUNTIF('Question Tracker'!$U$${firstDataRow}:$U$${lastDataRow},"Due")`, COLORS.paleAmber, "0"],
  ["D8:E8", "D9:E10", "Topics Mastered", `=COUNTIF('Topic Plan'!$I$${topicStart}:$I$${topicEnd},1)`, COLORS.paleGreen, "0"],
  ["G8:H8", "G9:H10", "Classification Flags", `=COUNTIF('Question Tracker'!$T$${firstDataRow}:$T$${lastDataRow},"Yes")`, COLORS.paleRed, "0"],
  ["J8:K8", "J9:K10", "Completed (Last 7 Days)", `=COUNTIFS('Question Tracker'!$M$${firstDataRow}:$M$${lastDataRow},">="&TODAY()-6,'Question Tracker'!$L$${firstDataRow}:$L$${lastDataRow},"Completed")`, COLORS.paleBlue, "0"],
  ["M8:N8", "M9:N10", "Average Time", `=IFERROR(AVERAGEIF('Question Tracker'!$O$${firstDataRow}:$O$${lastDataRow},">0"),0)`, "#F5F3FF", "0.0"],
];
for (const [labelRange, valueRange, label, formula, fill, fmt] of cards) {
  dashboard.getRange(labelRange.split(":")[0]).values = [[label]];
  dashboard.getRange(valueRange.split(":")[0]).formulas = [[formula]];
  formatCard(labelRange, valueRange, fill, fmt);
}

dashboard.getRange("A12:F12").values = [["Section", "Total", "Completed", "Correct", "Progress", "Accuracy"]];
styleHeader(dashboard.getRange("A12:F12"));
dashboard.getRange("A13:A15").values = [["Quant"], ["DILR"], ["VARC"]];
for (let row = 13; row <= 15; row++) {
  dashboard.getRange(`B${row}:F${row}`).formulas = [[
    `=COUNTIF('Question Tracker'!$B$${firstDataRow}:$B$${lastDataRow},$A${row})`,
    `=COUNTIFS('Question Tracker'!$B$${firstDataRow}:$B$${lastDataRow},$A${row},'Question Tracker'!$L$${firstDataRow}:$L$${lastDataRow},"Completed")`,
    `=COUNTIFS('Question Tracker'!$B$${firstDataRow}:$B$${lastDataRow},$A${row},'Question Tracker'!$N$${firstDataRow}:$N$${lastDataRow},"Correct")`,
    `=IFERROR($C${row}/$B${row},0)`,
    `=IFERROR($D${row}/$C${row},0)`,
  ]];
}
dashboard.getRange("E13:F15").format.numberFormat = "0%";
dashboard.getRange("A13:F15").format = { borders: { preset: "all", style: "thin", color: COLORS.mid } };
dashboard.getRange("E13:E15").conditionalFormats.add("dataBar", { color: COLORS.blue, gradient: true });

dashboard.getRange("H12:L12").values = [["Year", "Total", "Completed", "Progress", "Accuracy"]];
styleHeader(dashboard.getRange("H12:L12"));
const years = [...new Set(catalog.map((r) => Number(r.year)))].sort((a, b) => a - b);
dashboard.getRange(`H13:H${12 + years.length}`).values = years.map((year) => [year]);
for (let i = 0; i < years.length; i++) {
  const row = 13 + i;
  dashboard.getRange(`I${row}:L${row}`).formulas = [[
    `=COUNTIF('Question Tracker'!$E$${firstDataRow}:$E$${lastDataRow},$H${row})`,
    `=COUNTIFS('Question Tracker'!$E$${firstDataRow}:$E$${lastDataRow},$H${row},'Question Tracker'!$L$${firstDataRow}:$L$${lastDataRow},"Completed")`,
    `=IFERROR($J${row}/$I${row},0)`,
    `=IFERROR(COUNTIFS('Question Tracker'!$E$${firstDataRow}:$E$${lastDataRow},$H${row},'Question Tracker'!$N$${firstDataRow}:$N$${lastDataRow},"Correct")/$J${row},0)`,
  ]];
}
dashboard.getRange(`K13:L${12 + years.length}`).format.numberFormat = "0%";
dashboard.getRange(`H13:L${12 + years.length}`).format = { borders: { preset: "all", style: "thin", color: COLORS.mid } };

dashboard.getRange("M12:N12").values = [["Section", "Progress"]];
styleHeader(dashboard.getRange("M12:N12"));
dashboard.getRange("M13:M15").formulas = [["=A13"], ["=A14"], ["=A15"]];
dashboard.getRange("N13:N15").formulas = [["=E13"], ["=E14"], ["=E15"]];
dashboard.getRange("N13:N15").format.numberFormat = "0%";

const progressChart = dashboard.charts.add("bar", dashboard.getRange("A12:C15"));
progressChart.title = "Total vs Completed by CAT Section";
progressChart.hasLegend = true;
progressChart.setPosition("A18", "G33");

dashboard.getRange("H24:N24").merge();
dashboard.getRange("H24").values = [["Decision rule"]];
dashboard.getRange("H24:N24").format = { fill: COLORS.teal, font: { bold: true, color: COLORS.white } };
dashboard.getRange("H25:N30").merge();
dashboard.getRange("H25").values = [[
  "Prioritize topics where progress is below 50% or accuracy is below 70%. After completing a topic, schedule reviews at roughly 2, 7, and 21 days. Keep mixed mocks in the plan: topicwise PYQs improve pattern recognition, but mocks train selection, stamina, and switching under time pressure."
]];
dashboard.getRange("H25:N30").format = { fill: COLORS.paleBlue, font: { color: COLORS.dark }, wrapText: true, verticalAlignment: "top" };

dashboard.getRange("A:N").format.columnWidth = 13;
for (const col of ["A", "D", "G", "J", "M"]) dashboard.getRange(`${col}:${col}`).format.columnWidth = 15;
dashboard.getRange("A12:N12").format.rowHeight = 32;
dashboard.getRange("A12:N21").format.horizontalAlignment = "center";
dashboard.freezePanes.freezeRows(2);

// Weekly log through the CAT 2026 exam week.
weekly.showGridLines = false;
styleTitle(weekly, "A1:J1", "CAT 2026 - Weekly Execution Log");
weekly.getRange("A2:J2").values = [["Week", "Start", "End", "Planned Questions", "Completed", "Correct", "Accuracy", "Minutes", "Cumulative Completed", "Cumulative Progress"]];
styleHeader(weekly.getRange("A2:J2"));
const weekStarts = [];
const start = new Date(2026, 7, 17);
for (let i = 0; i < 15; i++) weekStarts.push(new Date(start.getFullYear(), start.getMonth(), start.getDate() + i * 7));
const weeklyStart = 3;
const weeklyEnd = weeklyStart + weekStarts.length - 1;
weekly.getRange(`A${weeklyStart}:C${weeklyEnd}`).values = weekStarts.map((date, idx) => [idx + 1, date, new Date(date.getFullYear(), date.getMonth(), date.getDate() + 6)]);
for (let row = weeklyStart; row <= weeklyEnd; row++) {
  weekly.getRange(`D${row}:J${row}`).formulas = [[
    `=ROUNDUP('Dashboard'!$A$5/${weekStarts.length},0)`,
    `=COUNTIFS('Question Tracker'!$M$${firstDataRow}:$M$${lastDataRow},">="&$B${row},'Question Tracker'!$M$${firstDataRow}:$M$${lastDataRow},"<="&$C${row},'Question Tracker'!$L$${firstDataRow}:$L$${lastDataRow},"Completed")`,
    `=COUNTIFS('Question Tracker'!$M$${firstDataRow}:$M$${lastDataRow},">="&$B${row},'Question Tracker'!$M$${firstDataRow}:$M$${lastDataRow},"<="&$C${row},'Question Tracker'!$N$${firstDataRow}:$N$${lastDataRow},"Correct")`,
    `=IFERROR($F${row}/$E${row},0)`,
    `=SUMIFS('Question Tracker'!$O$${firstDataRow}:$O$${lastDataRow},'Question Tracker'!$M$${firstDataRow}:$M$${lastDataRow},">="&$B${row},'Question Tracker'!$M$${firstDataRow}:$M$${lastDataRow},"<="&$C${row})`,
    `=SUM($E$${weeklyStart}:$E${row})`,
    `=IFERROR($I${row}/'Dashboard'!$A$5,0)`,
  ]];
}
weekly.getRange(`B${weeklyStart}:C${weeklyEnd}`).format.numberFormat = "dd-mmm";
weekly.getRange(`G${weeklyStart}:G${weeklyEnd}`).format.numberFormat = "0%";
weekly.getRange(`J${weeklyStart}:J${weeklyEnd}`).format.numberFormat = "0%";
weekly.getRange(`A${weeklyStart}:J${weeklyEnd}`).format = { borders: { preset: "all", style: "thin", color: COLORS.mid } };
weekly.getRange(`J${weeklyStart}:J${weeklyEnd}`).conditionalFormats.add("dataBar", { color: COLORS.teal, gradient: true });
weekly.getRange("L2:N2").values = [["Week", "Planned", "Completed"]];
for (let row = weeklyStart; row <= weeklyEnd; row++) {
  weekly.getRange(`L${row}:N${row}`).formulas = [[`=A${row}`, `=D${row}`, `=E${row}`]];
}
const weeklyChart = weekly.charts.add("line", weekly.getRange(`L2:N${weeklyEnd}`));
weeklyChart.title = "Weekly Plan vs Completion";
weeklyChart.hasLegend = true;
weeklyChart.setPosition("A21", "J37");
for (const col of ["A", "D", "E", "F", "G", "H", "I", "J"]) weekly.getRange(`${col}:${col}`).format.columnWidth = 16;
weekly.getRange("B:C").format.columnWidth = 13;
weekly.freezePanes.freezeRows(2);

// How-to guide.
guide.showGridLines = false;
styleTitle(guide, "A1:H1", "How to Use This CAT 2026 PYQ System");
guide.getRange("A3:H3").merge();
guide.getRange("A3").values = [["A fast, disciplined workflow for limited preparation time"]];
guide.getRange("A3:H3").format = { fill: COLORS.paleBlue, font: { bold: true, color: COLORS.navy, size: 13 }, verticalAlignment: "center" };
guide.getRange("A5:B10").values = [
  ["1", "Pick one topic from Topic Plan. Start with high-frequency Arithmetic, Algebra, RC, and set-selection-heavy DILR."],
  ["2", "Open its topic PDF, solve each linked question, and avoid viewing the explanation until your attempt is complete."],
  ["3", "Log Status, Result, Time, Confidence, and Attempt Date immediately in Question Tracker."],
  ["4", "For incorrect or slow questions, set Review Date for about 2 days later; repeat at 7 and 21 days until Mastered."],
  ["5", "Use Dashboard and Topic Plan weekly. Prioritize progress below 50%, accuracy below 70%, and revision-due questions."],
  ["6", "Do not rely only on topicwise practice. Reserve regular timed sectionals and full mocks for question selection, stamina, and exam-day switching."],
];
guide.getRange("A5:A10").format = { fill: COLORS.blue, font: { bold: true, color: COLORS.white, size: 14 }, horizontalAlignment: "center", verticalAlignment: "center" };
guide.getRange("B5:H10").merge(true);
guide.getRange("B5:H10").format = { fill: COLORS.light, font: { color: COLORS.dark, size: 10 }, wrapText: true, verticalAlignment: "center", borders: { insideHorizontal: { style: "thin", color: COLORS.mid } } };
guide.getRange("A5:H10").format.rowHeight = 46;

guide.getRange("A12:H12").merge();
guide.getRange("A12").values = [["Recommended time split"]];
guide.getRange("A12:H12").format = { fill: COLORS.teal, font: { bold: true, color: COLORS.white, size: 12 } };
guide.getRange("A13:H16").values = [
  ["Phase", "Focus", "Share", "Outcome", "", "", "", ""],
  ["Build", "Topicwise PYQs + concept repair", 0.6, "Coverage and pattern recognition", "", "", "", ""],
  ["Mix", "Mixed sets + timed sectionals", 0.25, "Selection and speed", "", "", "", ""],
  ["Test", "Full mocks + analysis", 0.15, "Stamina and strategy", "", "", "", ""],
];
guide.getRange("A13:D16").format = { borders: { preset: "all", style: "thin", color: COLORS.mid }, wrapText: true };
guide.getRange("A13:D13").format = { fill: COLORS.navy, font: { bold: true, color: COLORS.white } };
guide.getRange("C14:C16").format.numberFormat = "0%";
guide.getRange("A13:D16").format.rowHeight = 30;
guide.getRange("A18:H18").merge();
guide.getRange("A18").values = [["Coverage and source note"]];
guide.getRange("A18:H18").format = { fill: COLORS.amber, font: { bold: true, color: COLORS.navy } };
guide.getRange("A19:H23").merge();
guide.getRange("A19").values = [[
  "Coverage: CAT 2017-2025, all publicly archived slots, 1,830 individual questions. Source: https://online.2iim.com/CAT-question-paper/. The PDFs are source-linked indexes, not republished paper text. Automated topic labels marked Yes in Classification Review are broad or image-dependent and can be refined as you solve."
]];
guide.getRange("A19:H23").format = { fill: COLORS.paleAmber, font: { color: COLORS.dark }, wrapText: true, verticalAlignment: "top" };
guide.getRange("A:A").format.columnWidth = 12;
guide.getRange("B:B").format.columnWidth = 34;
guide.getRange("C:C").format.columnWidth = 12;
guide.getRange("D:D").format.columnWidth = 28;
guide.getRange("E:H").format.columnWidth = 12;

// Compact verification before export.
const dashboardCheck = await workbook.inspect({ kind: "table", range: "Dashboard!A1:N30", include: "values,formulas", tableMaxRows: 30, tableMaxCols: 14 });
console.log(dashboardCheck.ndjson);
const topicCheck = await workbook.inspect({ kind: "table", range: `Topic Plan!A1:L${Math.min(topicEnd, 15)}`, include: "values,formulas", tableMaxRows: 15, tableMaxCols: 12 });
console.log(topicCheck.ndjson);
const errorCheck = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
console.log(errorCheck.ndjson);

const renderSpecs = [
  ["Dashboard", "A1:N33"],
  ["Question Tracker", "A1:U24"],
  ["Topic Plan", `A1:L${Math.min(topicEnd, 32)}`],
  ["Weekly Log", "A1:J37"],
  ["How to Use", "A1:H23"],
  ["Lists", "A1:E7"],
];
for (const [sheetName, range] of renderSpecs) {
  const image = await workbook.render({ sheetName, range, scale: 1.1, format: "png" });
  const filename = sheetName.toLowerCase().replaceAll(" ", "_") + ".png";
  await fs.writeFile(path.join(previewDir, filename), new Uint8Array(await image.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(outputDir, "CAT_2026_PYQ_Progress_Tracker.xlsx");
await output.save(outputPath);
console.log(outputPath);
