#!/usr/bin/env node

import fs from "fs";
import { compile } from "@mdx-js/mdx";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";

const file = process.argv[2];

if (!file) {
  console.error("Please provide a filename");
  process.exit(1);
}

fs.readFile(file, "utf8", (err, content) => {
  if (err) {
    console.error(`Error reading ${file}:`, err);
    return;
  }

  compile(content, {
    remarkPlugins: [remarkMath, remarkGfm],
  })
    .then(() => {})
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
});
