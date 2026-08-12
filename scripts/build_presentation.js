// build_presentation.js
// Generates the monthly nonprofit impact presentation from cleaned Salesforce data.
// Usage: node build_presentation.js
//
// Data below is currently hardcoded from the sample cleaned CSVs for the demo.
// To reuse each month: update the STATS object at the top from your fresh
// cleaned_clients.csv / cleaned_donors.csv (or wire this script to read the
// CSVs directly with a small csv-parse step) and re-run.

const pptxgen = require("pptxgenjs");

// ---- MONTHLY DATA (update this block each month) --------------------------
const STATS = {
  monthLabel: "February 2026",
  activeClients: 14,
  totalClients: 16,
  totalRaised: 45245,
  numDonors: 16,
  testRecordsRemoved: 4,
  duplicatesRemoved: 4,
  programs: [
    { name: "Job Training", count: 5 },
    { name: "Housing Assistance", count: 4 },
    { name: "Food Security", count: 4 },
    { name: "Youth Mentorship", count: 3 },
  ],
  campaigns: [
    { name: "Corporate Match", amount: 22500 },
    { name: "Major Gifts", amount: 16800 },
    { name: "Winter Appeal", amount: 4550 },
    { name: "General Fund", amount: 1395 },
  ],
  topDonors: [
    { name: "TheFord Family Trust", amount: 15000 },
    { name: "Community Bank Foundation", amount: 10000 },
    { name: "Riverside Auto Group", amount: 7500 },
  ],
  deadlines: [
    { item: "Winter Appeal final report due to board", date: "Mar 5" },
    { item: "Q1 grant renewal submission (Community Bank Fdn)", date: "Mar 12" },
    { item: "Spring campaign kickoff", date: "Mar 20" },
  ],
};

// ---- PALETTE ---------------------------------------------------------------
const TEAL_DARK = "1B4B43";
const TEAL = "2E7D6B";
const GOLD = "D4A24C";
const CREAM_TEXT = "FFFFFF";
const INK = "1F2A24";
const SLATE = "5B6B64";
const CARD_BG = "F4F7F5";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
const FONT = "Arial";

// ---------------------------------------------------------------------------
// Slide 1: Title
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: TEAL_DARK };
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 13.33, h: 7.5, fill: { color: TEAL_DARK },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 10.2, y: -2.2, w: 6, h: 6, fill: { color: TEAL, transparency: 55 },
    line: { type: "none" },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: -2.5, y: 4.8, w: 5, h: 5, fill: { color: GOLD, transparency: 75 },
    line: { type: "none" },
  });
  s.addText("MONTHLY IMPACT REPORT", {
    x: 0.7, y: 2.5, w: 10, h: 0.5, fontFace: FONT, fontSize: 14,
    color: GOLD, bold: true, charSpacing: 3,
  });
  s.addText(STATS.monthLabel, {
    x: 0.7, y: 3.0, w: 10, h: 1.2, fontFace: FONT, fontSize: 44,
    color: CREAM_TEXT, bold: true,
  });
  s.addText("Clients served, dollars raised, and what's ahead this quarter", {
    x: 0.7, y: 4.15, w: 8.5, h: 0.6, fontFace: FONT, fontSize: 16,
    color: "CFE3DC",
  });
  s.addText("Prepared from a cleaned, de-duplicated Salesforce export", {
    x: 0.7, y: 6.9, w: 8, h: 0.4, fontFace: FONT, fontSize: 10,
    color: "8FB3A8", italic: true,
  });
}

// ---------------------------------------------------------------------------
// Slide 2: KPI overview
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("This Month at a Glance", {
    x: 0.6, y: 0.45, w: 10, h: 0.7, fontFace: FONT, fontSize: 30, bold: true, color: INK,
  });

  const kpis = [
    { label: "Active Clients", value: STATS.activeClients.toString() },
    { label: "Total Clients Served", value: STATS.totalClients.toString() },
    { label: "Total Raised", value: `$${STATS.totalRaised.toLocaleString()}` },
    { label: "Donors This Period", value: STATS.numDonors.toString() },
  ];
  const cardW = 2.85, gap = 0.3, startX = 0.6, y = 1.6, h = 2.0;
  kpis.forEach((k, i) => {
    const x = startX + i * (cardW + gap);
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: cardW, h, rectRadius: 0.12,
      fill: { color: CARD_BG }, line: { type: "none" },
      shadow: { type: "outer", color: "1B4B43", opacity: 0.12, blur: 8, offset: 3, angle: 90 },
    });
    s.addText(k.value, {
      x, y: y + 0.35, w: cardW, h: 0.9, align: "center", fontFace: FONT,
      fontSize: 32, bold: true, color: TEAL_DARK,
    });
    s.addText(k.label, {
      x, y: y + 1.25, w: cardW, h: 0.5, align: "center", fontFace: FONT,
      fontSize: 13, color: SLATE,
    });
  });

  s.addText("Data quality this cycle", {
    x: 0.6, y: 4.1, w: 6, h: 0.5, fontFace: FONT, fontSize: 16, bold: true, color: INK,
  });
  s.addText(
    [
      { text: `${STATS.testRecordsRemoved} test/demo records removed`, options: { bullet: true, breakLine: true, color: SLATE, fontSize: 14 } },
      { text: `${STATS.duplicatesRemoved} duplicate records removed`, options: { bullet: true, color: SLATE, fontSize: 14 } },
    ],
    { x: 0.7, y: 4.65, w: 6, h: 1, fontFace: FONT }
  );
  s.addText(
    "Every number on the following slides reflects the cleaned, verified dataset only.",
    { x: 0.6, y: 6.6, w: 11.5, h: 0.5, fontFace: FONT, fontSize: 11, italic: true, color: SLATE }
  );
}

// ---------------------------------------------------------------------------
// Slide 3: Clients by program (chart)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("Clients Served by Program", {
    x: 0.6, y: 0.45, w: 10, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: INK,
  });

  const chartData = [
    {
      name: "Clients",
      labels: STATS.programs.map((p) => p.name),
      values: STATS.programs.map((p) => p.count),
    },
  ];
  s.addChart(pres.ChartType.bar, chartData, {
    x: 0.6, y: 1.4, w: 7.6, h: 5.4,
    barDir: "col",
    chartColors: [TEAL],
    showTitle: false,
    showLegend: false,
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: INK,
    dataLabelFontSize: 12,
    catAxisLabelColor: SLATE,
    catAxisLabelFontSize: 11,
    valAxisLabelColor: SLATE,
    valAxisHidden: false,
    valGridLine: { color: "E5E9E7", size: 0.75 },
    catGridLine: { style: "none" },
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: 8.55, y: 1.4, w: 4.15, h: 5.4, rectRadius: 0.12,
    fill: { color: CARD_BG }, line: { type: "none" },
  });
  s.addText("What this means", {
    x: 8.85, y: 1.7, w: 3.6, h: 0.5, fontFace: FONT, fontSize: 15, bold: true, color: TEAL_DARK,
  });
  s.addText(
    "Job Training remains our largest program this month, with Housing " +
      "Assistance and Food Security close behind. Youth Mentorship is the " +
      "smallest but growing steadily as referral partnerships expand.",
    { x: 8.85, y: 2.3, w: 3.6, h: 4.2, fontFace: FONT, fontSize: 13, color: SLATE, lineSpacingMultiple: 1.3 }
  );
}

// ---------------------------------------------------------------------------
// Slide 4: Donations by campaign (chart) + top donors
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("Fundraising by Campaign", {
    x: 0.6, y: 0.45, w: 10, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: INK,
  });

  const chartData = [
    {
      name: "Raised",
      labels: STATS.campaigns.map((c) => c.name),
      values: STATS.campaigns.map((c) => c.amount),
    },
  ];
  s.addChart(pres.ChartType.pie, chartData, {
    x: 0.6, y: 1.4, w: 6.6, h: 5.4,
    chartColors: [TEAL_DARK, TEAL, GOLD, "9BC6BA"],
    showTitle: false,
    showLegend: true,
    legendPos: "b",
    legendColor: SLATE,
    legendFontSize: 11,
    showValue: true,
    dataLabelColor: "FFFFFF",
    dataLabelFontSize: 12,
    dataLabelFormatCode: "$#,##0",
  });

  s.addText("Top Donors This Period", {
    x: 7.6, y: 1.4, w: 5.1, h: 0.5, fontFace: FONT, fontSize: 16, bold: true, color: INK,
  });
  STATS.topDonors.forEach((d, i) => {
    const y = 2.05 + i * 0.85;
    s.addShape(pres.ShapeType.roundRect, {
      x: 7.6, y, w: 5.1, h: 0.7, rectRadius: 0.1,
      fill: { color: CARD_BG }, line: { type: "none" },
    });
    s.addText(d.name, {
      x: 7.85, y: y + 0.07, w: 3.4, h: 0.55, fontFace: FONT, fontSize: 13, bold: true, color: INK, valign: "middle",
    });
    s.addText(`$${d.amount.toLocaleString()}`, {
      x: 11.0, y: y + 0.07, w: 1.5, h: 0.55, align: "right", fontFace: FONT,
      fontSize: 13, bold: true, color: TEAL_DARK, valign: "middle",
    });
  });
  s.addText(
    `Total raised this period: $${STATS.totalRaised.toLocaleString()} across ${STATS.numDonors} donors`,
    { x: 7.6, y: 5.4, w: 5.1, h: 0.6, fontFace: FONT, fontSize: 12, italic: true, color: SLATE }
  );
}

// ---------------------------------------------------------------------------
// Slide 5: Deadlines & next steps
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: TEAL_DARK };
  s.addText("Upcoming Deadlines & Next Steps", {
    x: 0.6, y: 0.5, w: 11, h: 0.8, fontFace: FONT, fontSize: 28, bold: true, color: "FFFFFF",
  });

  STATS.deadlines.forEach((d, i) => {
    const y = 1.8 + i * 1.3;
    s.addShape(pres.ShapeType.roundRect, {
      x: 0.6, y, w: 12.1, h: 1.05, rectRadius: 0.1,
      fill: { color: "23574D" }, line: { type: "none" },
    });
    s.addShape(pres.ShapeType.roundRect, {
      x: 0.85, y: y + 0.22, w: 1.5, h: 0.6, rectRadius: 0.08,
      fill: { color: GOLD }, line: { type: "none" },
    });
    s.addText(d.date, {
      x: 0.85, y: y + 0.22, w: 1.5, h: 0.6, align: "center", valign: "middle",
      fontFace: FONT, fontSize: 15, bold: true, color: TEAL_DARK,
    });
    s.addText(d.item, {
      x: 2.6, y, w: 9.8, h: 1.05, valign: "middle", fontFace: FONT, fontSize: 16, color: "FFFFFF",
    });
  });

  s.addText("Questions before next month's meeting? Reach out any time.", {
    x: 0.6, y: 6.7, w: 11, h: 0.5, fontFace: FONT, fontSize: 12, italic: true, color: "9BC6BA",
  });
}

pres.writeFile({ fileName: "outputs/Monthly_Impact_Presentation.pptx" }).then(() => {
  console.log("✔ Presentation written to outputs/Monthly_Impact_Presentation.pptx");
});
