import React from "react";

/** Accept only absolute HTTP(S) destinations without embedded credentials. */
export function isSafeHttpUrl(value) {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.trim() !== value ||
    /[\u0000-\u0020\u007f]/.test(value) ||
    !/^https?:\/\//i.test(value)
  ) {
    return false;
  }

  try {
    const parsed = new URL(value);
    return (
      (parsed.protocol === "http:" || parsed.protocol === "https:") &&
      Boolean(parsed.hostname) &&
      !parsed.username &&
      !parsed.password
    );
  } catch {
    return false;
  }
}

/** Render a safe external reference as a link, otherwise retain plain text. */
export function ReferenceLink({ href, children, className = "" }) {
  const content = children ?? href ?? "Not available";
  if (!isSafeHttpUrl(href)) {
    return React.createElement(React.Fragment, null, content);
  }

  return React.createElement(
    "a",
    {
      href,
      target: "_blank",
      rel: "noopener noreferrer",
      className: `break-all text-blue-300 underline decoration-blue-400/70 underline-offset-2 hover:text-blue-200 hover:decoration-blue-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-300 ${className}`.trim(),
    },
    content,
  );
}
