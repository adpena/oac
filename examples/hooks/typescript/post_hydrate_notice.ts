/**
 * Small example hook used by starter adapter profiles.
 *
 * This script intentionally does something boring: it writes a JSON note that a hydrate step
 * completed. Real users can replace it with notifications, index refreshes, or environment-
 * specific automation once they opt in via a copied adapter profile.
 */

const payload = {
  event: "post-hydrate",
  tool: "oac",
  status: "ok",
  note: "typescript starter hook placeholder",
};

process.stdout.write(`${JSON.stringify(payload)}
`);
