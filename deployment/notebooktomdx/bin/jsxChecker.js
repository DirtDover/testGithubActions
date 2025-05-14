// var visit = require("unist-util-visit");
import { visit } from "unist-util-visit";

export default function attacher() {
  return transformer;

  function transformer(tree, file) {
    visit(tree, ["html", "code"], visitor);

    function visitor(node) {
      var value = node.value;
      if (node.type === "html") {
        if ((styleAttr = value.match(/style="(.*)"/g))) {
          // Avoid to raise warning if it is a plotly code block
          if (!value.includes("plotly")) {
            styleAttr.forEach((element) =>
              file.message(
                `Remove the style attribute in ${value}.`,
                node.position
              )
            );
          }
        }
        // if (value.match(/width="?(.*)"?/g)) {
        //   if (!value.match(/width="(.*)"/)) {
        //     file.message(
        //       `Correct the width attribute in ${value}.`,
        //       node.position
        //     );
        //   }
        // }
        // if (value.match(/height="?(.*)"?/g)) {
        //   if (!value.match(/height="(.*)"/)) {
        //     file.message(
        //       `Correct the height attribute in ${value}`,
        //       node.position
        //     );
        //   }
        // }
        if ((imgTags = value.match(/^(<img)(.*)(>)$/g))) {
          imgTags.forEach((element) => {
            if (!value.match(/(\/>)$/)) {
              file.message(
                `Correct the img tag in ${value}: close it with \`/>\`.`,
                node.position
              );
            }
          });
        }
        // if ((brTags = value.match(/<\/?br>/))) {
        //   brTags.forEach((element) =>
        //     file.message(
        //       `${element} is incorrect. Replace it with <br/>.`,
        //       node.position
        //     )
        //   );
        // }
      }
      if (node.type === "code") {
        if (node.lang === "text") {
          file.message(
            `Error in code block: text does not exist.`,
            node.position
          );
        }
      }
    }
    // if (
    //   tree.children &&
    //   tree.children[tree.children.length - 1].type === "code" &&
    //   tree.children[tree.children.length - 1].value === ""
    // ) {
    //   file.message("Trailing empty code cell at the end of the notebook.");
    // }
  }
}
