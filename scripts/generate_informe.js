#!/usr/bin/env node
"use strict";

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, HeadingLevel,
  PageOrientation
} = require("docx");
const fs = require("fs");
const path = require("path");

// ─── Constants ────────────────────────────────────────────────────────────────
const PAGE_W   = 11906;  // A4 width  DXA
const PAGE_H   = 16838;  // A4 height DXA
const MARGIN   = 1417;   // 2.5 cm in DXA
const CONTENT_W = PAGE_W - 2 * MARGIN; // 9072 DXA

const FONT = "Times New Roman";

const CELL_BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const CELL_BORDERS = {
  top: CELL_BORDER, bottom: CELL_BORDER,
  left: CELL_BORDER, right: CELL_BORDER
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Parse **bold** fragments inside a string and return an array of TextRun */
function parseInlineBold(text, opts = {}) {
  const runs = [];
  const re = /\*\*(.*?)\*\*/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      runs.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...opts }));
    }
    runs.push(new TextRun({ text: m[1], font: FONT, bold: true, ...opts }));
    last = re.lastIndex;
  }
  if (last < text.length) {
    runs.push(new TextRun({ text: text.slice(last), font: FONT, ...opts }));
  }
  return runs.length ? runs : [new TextRun({ text, font: FONT, ...opts })];
}

/** Strip inline code backticks (treat as normal text) */
function stripCode(text) {
  return text.replace(/`([^`]+)`/g, "$1");
}

/** Normal body paragraph (justified, 12pt, 1.5 line spacing) */
function bodyPara(text, opts = {}) {
  const cleaned = stripCode(text);
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 120, line: 360, lineRule: "auto" },
    children: parseInlineBold(cleaned, { size: 24 }),
    ...opts,
  });
}

/** Heading 1 — 14pt bold centered */
function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    spacing: { before: 300, after: 180 },
    children: [new TextRun({ text: stripCode(text), font: FONT, size: 28, bold: true })],
  });
}

/** Heading 2 — 12pt bold left */
function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    alignment: AlignmentType.LEFT,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text: stripCode(text), font: FONT, size: 24, bold: true })],
  });
}

/** Heading 3 — 12pt bold italic left */
function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    alignment: AlignmentType.LEFT,
    spacing: { before: 160, after: 80 },
    children: [new TextRun({ text: stripCode(text), font: FONT, size: 24, bold: true, italics: true })],
  });
}

/** Bullet paragraph */
function bulletPara(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 0, after: 80, line: 360, lineRule: "auto" },
    children: parseInlineBold(stripCode(text), { size: 24 }),
  });
}

/** Reference paragraph — hanging indent */
function refPara(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 120, line: 360, lineRule: "auto" },
    indent: { left: 720, hanging: 360 },
    children: parseInlineBold(stripCode(text), { size: 24 }),
  });
}

/** Caption / italic note paragraph */
function notePara(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 0, after: 120, line: 360, lineRule: "auto" },
    children: [new TextRun({ text: stripCode(text), font: FONT, size: 20, italics: true })],
  });
}

// ─── Table builder ────────────────────────────────────────────────────────────

function buildTable(headerCells, dataRows) {
  const colCount = headerCells.length;
  const colWidth = Math.floor(CONTENT_W / colCount);
  const colWidths = Array(colCount).fill(colWidth);
  // adjust last column for rounding
  colWidths[colCount - 1] = CONTENT_W - colWidth * (colCount - 1);

  function makeCell(text, isHeader, colIdx) {
    const parsed = parseInlineBold(stripCode(text), {
      size: isHeader ? 20 : 20,
      bold: isHeader,
      color: isHeader ? "FFFFFF" : "000000",
    });
    return new TableCell({
      borders: CELL_BORDERS,
      width: { size: colWidths[colIdx], type: WidthType.DXA },
      shading: isHeader
        ? { fill: "2E4057", type: ShadingType.CLEAR }
        : undefined,
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      children: [
        new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 0, after: 0 },
          children: parsed,
        }),
      ],
    });
  }

  const headerRow = new TableRow({
    tableHeader: true,
    children: headerCells.map((h, i) => makeCell(h, true, i)),
  });

  const bodyRows = dataRows.map((row, rowIdx) =>
    new TableRow({
      children: row.map((cell, colIdx) => {
        const isShaded = rowIdx % 2 === 1;
        const tc = makeCell(cell, false, colIdx);
        if (isShaded) {
          // apply alternating shade via a fresh cell — override shading
          return new TableCell({
            borders: CELL_BORDERS,
            width: { size: colWidths[colIdx], type: WidthType.DXA },
            shading: { fill: "F5F5F5", type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            verticalAlign: VerticalAlign.CENTER,
            children: tc.options.children,
          });
        }
        return tc;
      }),
    })
  );

  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...bodyRows],
  });
}

// ─── Markdown parser ──────────────────────────────────────────────────────────

/**
 * Parse markdown lines into docx elements.
 * Handles: # ## ### #### headings, tables, bullet lists, blockquotes, blank lines, normal paragraphs.
 * isRefSection: if true, body paragraphs use refPara styling.
 */
function parseMarkdown(lines, isRefSection = false) {
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Skip document title (# Title at top)
    if (/^# /.test(line)) {
      i++;
      continue;
    }

    // Skip horizontal rules
    if (/^---+$/.test(line.trim())) {
      i++;
      continue;
    }

    // Skip "Parte N:" subtitle paragraphs like "## Parte 1: ..."
    if (/^## Parte \d+:/.test(line)) {
      i++;
      continue;
    }

    // Skip trailing note "*La Parte 3 del informe..."
    if (/^\*La Parte/.test(line)) {
      i++;
      continue;
    }

    // Heading 1 — ## (section level)
    if (/^## /.test(line)) {
      const text = line.replace(/^## /, "");
      elements.push(heading1(text));
      i++;
      continue;
    }

    // Heading 2 — ###
    if (/^### /.test(line)) {
      const text = line.replace(/^### /, "");
      elements.push(heading2(text));
      i++;
      continue;
    }

    // Heading 3 — ####
    if (/^#### /.test(line)) {
      const text = line.replace(/^#### /, "");
      elements.push(heading3(text));
      i++;
      continue;
    }

    // Heading 4 — ##### (treat as heading3)
    if (/^##### /.test(line)) {
      const text = line.replace(/^##### /, "");
      elements.push(heading3(text));
      i++;
      continue;
    }

    // Table — detect by leading pipe
    if (/^\|/.test(line)) {
      const tableLines = [];
      while (i < lines.length && /^\|/.test(lines[i])) {
        tableLines.push(lines[i]);
        i++;
      }
      // parse table
      const rows = tableLines
        .filter(l => !/^\|[-:| ]+\|$/.test(l.trim()))  // skip separator row
        .map(l =>
          l.replace(/^\|/, "").replace(/\|$/, "")
            .split("|")
            .map(c => c.trim())
        );
      if (rows.length > 0) {
        const header = rows[0];
        const data = rows.slice(1);
        elements.push(buildTable(header, data));
        // small spacing after table
        elements.push(new Paragraph({ spacing: { before: 0, after: 120 }, children: [] }));
      }
      continue;
    }

    // Bullet list — "- " or "* "
    if (/^[-*] /.test(line)) {
      const text = line.replace(/^[-*] /, "");
      elements.push(bulletPara(text));
      i++;
      continue;
    }

    // Blockquote ">"
    if (/^> /.test(line)) {
      const text = line.replace(/^> /, "");
      elements.push(new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { before: 80, after: 80, line: 360, lineRule: "auto" },
        indent: { left: 720, right: 720 },
        children: parseInlineBold(stripCode(text), { size: 24, italics: true }),
      }));
      i++;
      continue;
    }

    // Note line (starts with *)
    if (/^\*[^*]/.test(line) && !isRefSection) {
      elements.push(notePara(line.replace(/^\*/, "").replace(/\*$/, "")));
      i++;
      continue;
    }

    // Bold standalone line "**Text**" — treat as bold body para
    if (/^\*\*[^*]/.test(line)) {
      elements.push(bodyPara(line));
      i++;
      continue;
    }

    // Empty line — skip
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Normal paragraph
    if (isRefSection) {
      elements.push(refPara(line));
    } else {
      elements.push(bodyPara(line));
    }
    i++;
  }

  return elements;
}

// ─── Cover page ───────────────────────────────────────────────────────────────

function makeCoverPage() {
  const centered = (text, size, bold = false, spacing = {}) =>
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 120, ...spacing },
      children: [new TextRun({ text, font: FONT, size, bold })],
    });

  return [
    // big vertical space at top
    new Paragraph({ spacing: { before: 0, after: 2880 }, children: [] }),

    centered("INSTITUTO TECNOLÓGICO DE BUENOS AIRES", 28, true, { after: 80 }),
    centered("Analítica en Venta Minorista", 24, false, { after: 2880 }),

    centered(
      "Distribución Espacial de Indicadores de Vulnerabilidad Habitacional",
      32, true, { after: 60 }
    ),
    centered(
      "en los Radios Censales de la Ciudad Autónoma de Buenos Aires",
      32, true, { after: 60 }
    ),
    centered(
      "Censo Nacional 2022 — INDEC",
      24, false, { after: 2880 }
    ),

    centered("Autores:", 24, true, { after: 60 }),
    centered("Agustín Chaud", 24, false, { after: 60 }),
    centered("Gerónimo Fasce", 24, false, { after: 360 }),

    centered("Profesor:", 24, true, { after: 60 }),
    centered("Sebastián Perera", 24, false, { after: 360 }),

    centered("Abril 2026", 24, false, { after: 0 }),

    // page break after cover
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ─── Main ─────────────────────────────────────────────────────────────────────

const BASE = "C:/Users/Dell/Agus/2026/Plan de expansion";

const part1 = fs.readFileSync(path.join(BASE, "05_informe/parte_1_intro_metodologia.md"), "utf8");
const part2 = fs.readFileSync(path.join(BASE, "05_informe/parte_2_resultados.md"), "utf8");
const part3 = fs.readFileSync(path.join(BASE, "05_informe/parte_3_discusion_conclusiones.md"), "utf8");

// Split references section from part3
const refMarker = "## Referencias bibliográficas";
const refIdx3 = part3.indexOf(refMarker);
const part3Body = part3.slice(0, refIdx3 >= 0 ? refIdx3 : part3.length);
const refsText = refIdx3 >= 0 ? part3.slice(refIdx3) : "";

// Also split part1 references (## Referencias at end)
const refMarker1 = "\n## Referencias\n";
const refIdx1 = part1.indexOf(refMarker1);
const part1Body = refIdx1 >= 0 ? part1.slice(0, refIdx1) : part1;
// part1 references will be merged at end — skip them since part3 has full list

function splitLines(text) {
  return text.split(/\r?\n/);
}

const body1 = parseMarkdown(splitLines(part1Body));
const body2 = parseMarkdown(splitLines(part2));
const body3 = parseMarkdown(splitLines(part3Body));

// References
let refsElements = [];
if (refsText) {
  const refLines = splitLines(refsText);
  // First line is the heading
  const [headingLine, ...rest] = refLines;
  refsElements.push(heading1(headingLine.replace(/^## /, "")));
  // Each non-empty line is a reference
  for (const l of rest) {
    if (l.trim() === "" || /^---/.test(l.trim())) continue;
    refsElements.push(refPara(l));
  }
}

// ─── Document ─────────────────────────────────────────────────────────────────

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT, size: 24 },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: FONT, color: "000000" },
        paragraph: {
          spacing: { before: 300, after: 180 },
          alignment: AlignmentType.CENTER,
          outlineLevel: 0,
        },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 24, bold: true, font: FONT, color: "000000" },
        paragraph: {
          spacing: { before: 200, after: 120 },
          alignment: AlignmentType.LEFT,
          outlineLevel: 1,
        },
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 24, bold: true, italics: true, font: FONT, color: "000000" },
        paragraph: {
          spacing: { before: 160, after: 80 },
          alignment: AlignmentType.LEFT,
          outlineLevel: 2,
        },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "\u2022",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 },
                spacing: { line: 360, lineRule: "auto" },
              },
              run: { font: FONT },
            },
          },
        ],
      },
    ],
  },
  sections: [
    // ── Section 1: Cover (no header/footer, titlePage) ───────────────────────
    {
      properties: {
        titlePage: true,
        page: {
          size: { width: PAGE_W, height: PAGE_H, orientation: PageOrientation.PORTRAIT },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      footers: {
        // default footer (body pages) — page number
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { before: 0, after: 0 },
              children: [
                new TextRun({ text: "— ", font: FONT, size: 20 }),
                new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 }),
                new TextRun({ text: " —", font: FONT, size: 20 }),
              ],
            }),
          ],
        }),
        // first page footer — empty
        first: new Footer({ children: [] }),
      },
      children: [
        ...makeCoverPage(),
        ...body1,
        ...body2,
        ...body3,
        ...refsElements,
      ],
    },
  ],
});

const outPath = path.join(BASE, "05_informe/informe_final_CABA_IVH.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  const kb = Math.round(buf.length / 1024);
  console.log(`OK: ${outPath}`);
  console.log(`Size: ${kb} KB`);
}).catch(err => {
  console.error("ERROR:", err.message);
  process.exit(1);
});
