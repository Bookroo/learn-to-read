#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const PAGE_WIDTH = 852;
const PAGE_HEIGHT = 1280;
const SPREAD_WIDTH = PAGE_WIDTH * 2;
const SPREAD_HEIGHT = PAGE_HEIGHT;
const SPREAD_RE = /^(\d+)(?:-[^.]+)?\.(jpe?g|png)$/i;
const COVER_RE = /^cover(?:-[^.]+)?\.(jpe?g|png)$/i;

function usage() {
  console.log(`Usage: node scripts/process-ebook-images.js [target ...]

Targets can be a books root, a book folder, or a spread folder.
Defaults to ./books.

The script finds numeric spread images such as 1.jpg and 1-bw.jpg,
resizes each spread to ${SPREAD_WIDTH}x${SPREAD_HEIGHT}, splits it into
left/right ${PAGE_WIDTH}x${PAGE_HEIGHT} pages, and writes sequential PNGs
to a shared ebook folder in the book folder. Black-and-white pages are
written with a -bw suffix, such as 1-bw.png. A front cover image such as
Cover.jpg or cover-bw.jpg is resized to ${PAGE_WIDTH}x${PAGE_HEIGHT} and
written as cover.png for color folders and cover-bw.png for black-and-white
folders. Back covers are ignored.`);
}

function parseArgs(argv) {
  const targets = [];

  for (const arg of argv) {
    if (arg === "-h" || arg === "--help") {
      usage();
      process.exit(0);
    }

    targets.push(arg);
  }

  return targets.length > 0 ? targets : ["books"];
}

function findMagick() {
  if (process.env.MAGICK_BINARY) {
    return process.env.MAGICK_BINARY;
  }

  const result = spawnSync("sh", ["-c", "command -v magick || command -v convert"], {
    encoding: "utf8",
  });

  const binary = result.stdout.trim().split("\n")[0];
  if (!binary) {
    throw new Error("ImageMagick is required. Install it or set MAGICK_BINARY.");
  }

  return binary;
}

function isDirectory(filePath) {
  try {
    return fs.statSync(filePath).isDirectory();
  } catch {
    return false;
  }
}

function getSpreadImages(dir) {
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => {
      const match = entry.name.match(SPREAD_RE);
      if (!match) {
        return null;
      }

      return {
        name: entry.name,
        spreadNumber: Number.parseInt(match[1], 10),
        path: path.join(dir, entry.name),
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.spreadNumber - b.spreadNumber || a.name.localeCompare(b.name));
}

function getCoverImage(dir) {
  const cover = fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && COVER_RE.test(entry.name))
    .map((entry) => path.join(dir, entry.name))
    .sort((a, b) => path.basename(a).localeCompare(path.basename(b)))[0];

  return cover || null;
}

function findSpreadFolders(target) {
  const resolvedTarget = path.resolve(target);
  const spreadFolders = new Set();

  function visit(dir) {
    if (path.basename(dir) === "ebook") {
      return;
    }

    const spreads = getSpreadImages(dir);
    if (spreads.length > 0) {
      spreadFolders.add(dir);
      return;
    }

    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (!entry.isDirectory() || entry.name.startsWith(".")) {
        continue;
      }

      visit(path.join(dir, entry.name));
    }
  }

  if (!isDirectory(resolvedTarget)) {
    throw new Error(`Target is not a directory: ${target}`);
  }

  visit(resolvedTarget);
  return [...spreadFolders].sort();
}

function runMagick(magick, args) {
  const result = spawnSync(magick, args, { encoding: "utf8" });

  if (result.status !== 0) {
    const command = [magick, ...args].join(" ");
    const detail = result.stderr.trim() || result.stdout.trim();
    throw new Error(`ImageMagick failed: ${command}\n${detail}`);
  }
}

function cleanGeneratedPages(ebookDir) {
  if (!fs.existsSync(ebookDir)) {
    fs.mkdirSync(ebookDir, { recursive: true });
    return;
  }

  removeGeneratedEbookFiles(ebookDir);
}

function removeGeneratedEbookFiles(ebookDir) {
  if (!fs.existsSync(ebookDir)) {
    return;
  }

  for (const entry of fs.readdirSync(ebookDir, { withFileTypes: true })) {
    if (entry.isFile() && /^\d+(?:-bw)?\.png$/i.test(entry.name)) {
      fs.unlinkSync(path.join(ebookDir, entry.name));
    }
  }

  const coverPath = path.join(ebookDir, "cover.png");
  if (fs.existsSync(coverPath)) {
    fs.unlinkSync(coverPath);
  }

  const bwCoverPath = path.join(ebookDir, "cover-bw.png");
  if (fs.existsSync(bwCoverPath)) {
    fs.unlinkSync(bwCoverPath);
  }
}

function removeEmptyDirectory(dir) {
  try {
    fs.rmdirSync(dir);
  } catch {
    // Leave non-empty directories alone.
  }
}

function removeStaleNestedEbookFolders(spreadFolders) {
  for (const folder of spreadFolders) {
    const nestedEbookDir = path.join(folder, "ebook");

    removeGeneratedEbookFiles(nestedEbookDir);
    removeEmptyDirectory(nestedEbookDir);
  }
}

function isBlackAndWhiteFolder(dir, spreads, cover) {
  return (
    /\bbw\b/i.test(path.basename(dir)) ||
    spreads.some((spread) => /-bw\./i.test(spread.name)) ||
    (cover ? /-bw\./i.test(path.basename(cover)) : false)
  );
}

function pageFileName(pageNumber, isBlackAndWhite) {
  return `${pageNumber}${isBlackAndWhite ? "-bw" : ""}.png`;
}

function coverFileName(isBlackAndWhite) {
  return isBlackAndWhite ? "cover-bw.png" : "cover.png";
}

function groupSpreadFoldersByBook(spreadFolders) {
  const groups = new Map();

  for (const folder of spreadFolders) {
    const bookDir = path.dirname(folder);
    const group = groups.get(bookDir) || [];
    group.push(folder);
    groups.set(bookDir, group);
  }

  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}

function processSpreadFolder(magick, dir, ebookDir) {
  const spreads = getSpreadImages(dir);
  const cover = getCoverImage(dir);
  const isBlackAndWhite = isBlackAndWhiteFolder(dir, spreads, cover);

  if (cover) {
    runMagick(magick, [
      cover,
      "-auto-orient",
      "-resize",
      `${PAGE_WIDTH}x${PAGE_HEIGHT}!`,
      path.join(ebookDir, coverFileName(isBlackAndWhite)),
    ]);
  }

  let pageNumber = 1;
  for (const spread of spreads) {
    const leftPage = path.join(ebookDir, pageFileName(pageNumber, isBlackAndWhite));
    const rightPage = path.join(ebookDir, pageFileName(pageNumber + 1, isBlackAndWhite));

    runMagick(magick, [
      spread.path,
      "-auto-orient",
      "-resize",
      `${SPREAD_WIDTH}x${SPREAD_HEIGHT}!`,
      "-crop",
      `${PAGE_WIDTH}x${PAGE_HEIGHT}+0+0`,
      "+repage",
      leftPage,
    ]);

    runMagick(magick, [
      spread.path,
      "-auto-orient",
      "-resize",
      `${SPREAD_WIDTH}x${SPREAD_HEIGHT}!`,
      "-crop",
      `${PAGE_WIDTH}x${PAGE_HEIGHT}+${PAGE_WIDTH}+0`,
      "+repage",
      rightPage,
    ]);

    pageNumber += 2;
  }

  return { dir, cover: Boolean(cover), isBlackAndWhite, spreads: spreads.length, pages: pageNumber - 1 };
}

function processBook(magick, bookDir, spreadFolders) {
  const ebookDir = path.join(bookDir, "ebook");
  const results = [];

  cleanGeneratedPages(ebookDir);

  for (const folder of spreadFolders.sort((a, b) => a.localeCompare(b))) {
    results.push(processSpreadFolder(magick, folder, ebookDir));
  }

  removeStaleNestedEbookFolders(spreadFolders);

  return { bookDir, ebookDir, results };
}

function main() {
  const targets = parseArgs(process.argv.slice(2));
  const magick = findMagick();
  const folders = [...new Set(targets.flatMap(findSpreadFolders))];

  if (folders.length === 0) {
    console.log("No spread folders found.");
    return;
  }

  for (const [bookDir, spreadFolders] of groupSpreadFoldersByBook(folders)) {
    const book = processBook(magick, bookDir, spreadFolders);
    const parts = book.results.map((result) => {
      const variant = result.isBlackAndWhite ? "bw" : "color";
      const coverStatus = result.cover ? "cover + " : "";
      return `${variant}: ${coverStatus}${result.spreads} spreads -> ${result.pages} pages`;
    });

    console.log(`${path.relative(process.cwd(), book.ebookDir)}: ${parts.join("; ")}`);
  }
}

main();
