#!/usr/bin/env node
/**
 * CLI wrapper for the PDB parser.
 *
 * Usage:  node cli.js <path-to-pdb-file>
 *
 * Reads the PDB file, runs extractSummary (AlphaFold-compatible output),
 * and writes the result to output.json in the same directory as this script.
 */

const fs   = require('fs');
const path = require('path');
const extractSummary = require('./lib/extract-summary');

// ── Validate CLI args ─────────────────────────────────────────────────────────
const inputFile = process.argv[2];

if (!inputFile) {
  console.error('Usage: node cli.js <path-to-pdb-file>');
  process.exit(1);
}

const resolvedPath = path.resolve(inputFile);

if (!fs.existsSync(resolvedPath)) {
  console.error(`File not found: ${resolvedPath}`);
  process.exit(1);
}

// ── Parse ─────────────────────────────────────────────────────────────────────
try {
  const pdbString = fs.readFileSync(resolvedPath, 'utf-8');
  const result    = extractSummary(pdbString, { source: 'pdb_upload' });

  // Write output.json alongside this script
  const outputPath = path.join(__dirname, 'output.json');
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), 'utf-8');

  console.log(JSON.stringify({ status: 'ok', output: outputPath }));
  process.exit(0);
} catch (err) {
  console.error(`Parse error: ${err.message}`);
  process.exit(1);
}
