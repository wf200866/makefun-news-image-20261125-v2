// make.fun entrypoint: publish the bundled front page to the output folder.
// Node 22+, standard library only, no network. The picture is drawn ahead of
// time by draw.py; grading runs offline, so this program only validates and
// copies the PNG that ships beside it.
import { chmodSync, copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(ROOT, "entry.png");
const LIMIT = 1024 * 1024;
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function stop(reason) {
  console.error(`entry: ${reason}`);
  process.exit(1);
}

if (!existsSync(SOURCE)) {
  stop("entry.png is missing next to main.ts");
}

const magic = readFileSync(SOURCE).subarray(0, PNG_MAGIC.length);
if (!magic.equals(PNG_MAGIC)) {
  stop("entry.png does not start with the PNG signature");
}

const outDir = resolve(process.env.MAKEFUN_OUTPUT_DIR || "/output");
const target = join(outDir, "entry.png");
mkdirSync(outDir, { recursive: true });
copyFileSync(SOURCE, target);
chmodSync(target, 0o644);

const written = statSync(target).size;
if (written === 0 || written > LIMIT) {
  stop(`output is ${written} bytes; the gate allows 1..${LIMIT}`);
}

console.log(`published ${target} (${written} bytes, mode 0644)`);
