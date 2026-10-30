import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { isSafeHttpUrl, ReferenceLink } from "../components/ReferenceLink.mjs";

const passportSource = await readFile(
  new URL("../components/EvidencePassport.js", import.meta.url),
  "utf8",
);

test("valid HTTP(S) reference renders the exact destination as a blue external link", () => {
  const destination = "https://www.ebi.ac.uk/chembl/explore/compound/CHEMBL553?ref=passport";
  const html = renderToStaticMarkup(
    React.createElement(ReferenceLink, { href: destination }, "ChEMBL compound CHEMBL553"),
  );

  assert.equal(isSafeHttpUrl(destination), true);
  assert.match(html, /<a\b/);
  assert.match(html, /href="https:\/\/www\.ebi\.ac\.uk\/chembl\/explore\/compound\/CHEMBL553\?ref=passport"/);
  assert.match(html, /target="_blank"/);
  assert.match(html, /rel="noopener noreferrer"/);
  assert.match(html, /text-blue-300/);
  assert.match(html, /underline/);
  assert.match(html, /hover:text-blue-200/);
  assert.match(html, /ChEMBL compound CHEMBL553/);
});

test("unsafe, relative, malformed, and missing references remain plain text", () => {
  for (const href of [
    "javascript:alert(1)",
    "data:text/html,hello",
    "ftp://example.org/file",
    "/relative/path",
    "https://",
    " https://example.org",
    "https://user:password@example.org/",
    null,
    undefined,
  ]) {
    assert.equal(isSafeHttpUrl(href), false, String(href));
    const html = renderToStaticMarkup(
      React.createElement(ReferenceLink, { href }, "Reference title"),
    );
    assert.doesNotMatch(html, /<a\b/);
    assert.match(html, /Reference title/);
  }
});

test("Evidence Passport applies the safe link to its dynamic source URL rows", () => {
  assert.match(passportSource, /isSafeHttpUrl\(status\)/);
  assert.match(passportSource, /<ReferenceLink href=\{status\}/);
  assert.match(passportSource, /provenance\.scaffold_provenance\?\.sources \|\| \[\]/);
  assert.match(passportSource, /label="Reference source" value=\{source\.name\} status=\{source\.url\}/);
});
