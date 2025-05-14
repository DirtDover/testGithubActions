#!/usr/bin/env node
import parseJSON from "./notebookParser.js";
import jsxChecker from "./jsxChecker.js";
import { remark } from "remark";
import remarkMdx from "remark-mdx";
import remarkMath from "remark-math";
import { reporter } from "vfile-reporter";
import fs from "fs";
import path from "path";
import * as prettier from "prettier";

// Parse command line arguments
const args = process.argv.slice(2);
let inputFile = args[0],
  validate = false,
  output;

args.forEach((arg, index) => {
  switch (arg) {
    case "-v":
    case "--validate":
      validate = true;
      break;
    case "-o":
    case "--output":
      output = args[index + 1];
      break;
  }
});

try {
  const data = fs.readFileSync(inputFile, "utf8");
  var markdownString = parseJSON(data);
  // Use prettier to prettify the MDX string avoiding some issues
  markdownString = markdownString.replace(/<!--.*-->\n/g, "");
  markdownString = await prettier.format(markdownString, {
    parser: "mdx",
  });
  // console.log(markdownString);
} catch (err) {
  console.error("⚠️", err);
}

if (validate) {
  remark()
    .use(jsxChecker)
    .process(markdownString, (err, file) => {
      file.path = inputFile;
      console.error(reporter(err || file));
    });
}

if (output) {
  remark()
    .use(remarkMath)
    .use(remarkMdx)
    .process(markdownString, (err, file) => {
      if (err) {
        console.error("⚠️", err);
      }
      var filename = path.parse(path.basename(inputFile)).name;
      let fileCommentClean = String(file).replace(/<!--.*-->\n/g, "");
      fs.writeFile(output, fileCommentClean, (err) => {
        // If there is any error in writing to the file, return
        if (err) {
          console.error("⚠️", err);
          return;
        }
        // Log this message if the file was written to successfully
        console.log("🎉 Wrote successfully to", `${output}`);
      });
    });
}
