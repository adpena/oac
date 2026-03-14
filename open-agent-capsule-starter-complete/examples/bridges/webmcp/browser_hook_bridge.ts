/**
 * Illustrative WebMCP bridge sketch.
 *
 * In a real browser environment this code would register or expose JavaScript-based tools that
 * let an agent inspect capsule summaries, search promoted memory, or view hook status without
 * turning the browser into canonical storage.
 */

const payload = {
  surface: "webmcp",
  mode: "read-only",
  note: "starter WebMCP bridge placeholder",
};

process.stdout.write(`${JSON.stringify(payload)}
`);
