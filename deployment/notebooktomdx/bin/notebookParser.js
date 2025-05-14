// const { nanoid } = require("nanoid");
// var HTMLtoJSX = require("htmltojsx");

import { nanoid } from "nanoid";
import HTMLtoJSX from "htmltojsx";
import PromptSync from "prompt-sync";

const prompt = PromptSync();

const fourSpaces = "    ";

function convertToJSX(htmlText) {
  var converter = new HTMLtoJSX({ createClass: false });
  var output = converter.convert(htmlText);
  return output;
}

function codeBlockOutput(code) {
  var outputString = "";
  outputString += "\n    ```\n";
  outputString += code;
  outputString += "\n    ```\n\n";
  return outputString;
}

function getOuputString(outputs) {
  var outputString = "";

  outputs.forEach((element) => {
    // console.log("element", JSON.stringify(element, null, 2));
    // prompt("Press Enter to continue");
    if (element.output_type === "execute_result") {
      if (element.data["text/html"]) {
        let elementTemp;
        if (typeof element.data["text/html"] == "string") {
          elementTemp = [element.data["text/html"]];
        } else {
          elementTemp = element.data["text/html"];
        }
        outputString += elementTemp.join(fourSpaces);
        outputString = convertToJSX(outputString);
        outputString += "\n\n";
      } else {
        let elementTemp;
        if (typeof element.data["text/plain"] == "string") {
          elementTemp = element.data["text/plain"].split("\n");
          elementTemp.forEach(
            (elem, index, arrayTemp) => (arrayTemp[index] = elem + "\n")
          );
          if (!Array.isArray(elementTemp)) {
            elementTemp = [elementTemp];
          }
        } else {
          elementTemp = element.data["text/plain"];
        }
        // Remove all elements in elementTemp that have "<" or ">" in them
        elementTemp = elementTemp.filter((elem) => {
          return !elem.includes("<") && !elem.includes(">");
        });
        if (elementTemp.length > 0) {
          outputString += codeBlockOutput(
            fourSpaces + elementTemp.join(fourSpaces)
          );
          outputString += "\n\n";
        }
      }
    } else if (element.output_type === "display_data") {
      // We use flagImagePNG in order to avoid having png image + svg image
      // because some matplotlib outputs seems to do both.  Thus we have
      // "image/png" and "image/svg+xml".  The latter is buggy most of the time
      // because we have trouble to properly convert its code to JSX.
      var flagImagePNG = false;
      if (element.data["text/plain"]) {
        let elementTemp;
        if (typeof element.data["text/plain"] == "string") {
          elementTemp = [element.data["text/plain"]];
        } else {
          elementTemp = element.data["text/plain"];
        }
        // Remove all elements in elementTemp that have "<" or ">" in them
        elementTemp = elementTemp.filter((elem) => {
          return !elem.includes("<") && !elem.includes(">");
        });
        if (elementTemp.length > 0) {
          outputString += codeBlockOutput(elementTemp.join());
          outputString += "\n\n";
        }
      }
      if (element.data["image/png"]) {
        outputString += `<img src="data:image/png;base64, ${element.data[
          "image/png"
        ].trim()}" alt="output cell ${nanoid(6)}" />`;
        outputString += "\n\n";
        flagImagePNG = true;
      }
      if (element.data["image/svg+xml"] && !flagImagePNG) {
        // element.data["image/svg+xml"] is either a string or an array
        var svgElement;
        if (typeof element.data["image/svg+xml"] === "string") {
          svgElement = element.data["image/svg+xml"];
        } else {
          svgElement = element.data["image/svg+xml"].join("");
        }
        // Convert to JSX
        let jsxSvgElement = convertToJSX(svgElement);
        outputString += jsxSvgElement;
        outputString += "\n\n";
      }
      // if (element.data["application/json"]) {
      //   // This part is developped for Plotly display when renderer is set to
      //   // "json". But it doesn't work yet
      //   let plotlyComponent = `<Plot data={${JSON.stringify(
      //     element.data["application/json"]["data"]
      //   )}} layout={${JSON.stringify(
      //     element.data["application/json"]["layout"]
      //   )}} />`;
      //   outputString += plotlyComponent;
      //   outputString += "\n\n";
      // }
      // if (element.data["text/html"]) {
      //   let html = element.data["text/html"];
      //   let trimHtml = html
      //     .map((item) => {
      //       return item.trim();
      //     })
      //     .join("");
      //   let jsx = convertToJSX(trimHtml);
      //   outputString += jsx;
      //   outputString += "\n\n";
      // }
    } else if (element.output_type === "stdout") {
      outputString += codeBlockOutput(element.text.join());
      outputString += "\n\n";
    } else if (element.output_type === "stream") {
      let elementTemp;
      if (typeof element.text == "string") {
        elementTemp = element.text.split("\n");
        // console.log("elementTemp 1", elementTemp);
        elementTemp.forEach(
          (elem, index, arrayTemp) => (arrayTemp[index] = elem.trim() + "\n")
        );
        // console.log("elementTemp 2", elementTemp);
        if (!Array.isArray(elementTemp)) {
          elementTemp = [element.text];
          // console.log("elementTemp 3", elementTemp);
        }
      } else {
        elementTemp = element.text;
        // console.log("elementTemp 4", elementTemp);
      }
      elementTemp.forEach((elem, index, array) => {
        array[index] = elem.trim();
      });
      elementTemp = elementTemp.filter((elem) => {
        return !elem.includes("<") && !elem.includes(">");
      });
      // console.log("elementTemp", elementTemp);
      // prompt("Press Enter to continue");
      outputString += codeBlockOutput(
        fourSpaces + elementTemp.join(fourSpaces)
      );
      outputString += "\n\n";
    }
  });

  outputString += "\n";
  return outputString;
}

export default function parseJSON(data) {
  var markdownString = "";
  const jsonData = JSON.parse(data);

  jsonData.cells.forEach((cell) => {
    if (cell.cell_type === "markdown") {
      markdownString += cell.source.join("");
      markdownString += "\n\n";
    } else if (cell.cell_type === "code") {
      let codeString = cell.source.join("");
      markdownString += `\`\`\`python\n${codeString}\n\`\`\`\n`;
      markdownString += "\n\n";
      let outputString = getOuputString(cell.outputs);
      markdownString += outputString;
      markdownString += "\n\n";
    }
  });

  markdownString += "\n";
  return markdownString;
}
