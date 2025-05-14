from jupyter_notebook_parser import JupyterNotebookParser
import argparse
import subprocess
import uuid


def output_code_bloc(outputs):
    output = ""
    output += "    ```\n    "
    output += "    ".join(outputs)
    output += "\n    ```\n"
    return output


def convert_notebook_to_md(notebook_path):
    parsed = JupyterNotebookParser(notebook_path)
    final_output = ""
    for cell in parsed.get_all_cells():
        final_output += "\n"
        if cell["cell_type"] == "markdown":
            # Replace <img ...> by <img ... />
            for i, line in enumerate(cell["source"]):
                cell["source"][i] = line.rstrip(" ")
                cell["source"][i] = line.replace("<!--.*-->\n", "")
                # if "<img" in line and "/>" not in line:
                #     cell["source"][i] = line.replace(">", " />")
            final_output += "".join(cell["source"])
            final_output += "\n"
        elif cell["cell_type"] == "code":
            final_output += "```python\n"
            final_output += "".join(cell["source"])
            final_output += "\n```\n"
            if len(cell["outputs"]) > 0:
                for output in cell["outputs"]:
                    final_output += "\n"
                    if output["output_type"] == "stream":
                        final_output += output_code_bloc(output["text"])
                    elif output["output_type"] == "execute_result":
                        if "text/plain" in output["data"]:
                            final_output += output_code_bloc(
                                output["data"]["text/plain"]
                            )
                        elif "text/html" in output["data"]:
                            final_output += "".join(output["data"]["text/html"])
                    elif output["output_type"] == "display_data":
                        if "image/png" in output["data"]:
                            final_output += f'<img src="data:image/png;base64, {output["data"]["image/png"]}" alt="output cell {uuid.uuid4().hex[:6]}" />\n'
                        elif "text/plain" in output["data"]:
                            final_output += output_code_bloc(
                                output["data"]["text/plain"]
                            )
                        elif "text/html" in output["data"]:
                            # final_output += "".join(output["data"]["text/html"])
                            pass
                    elif output["output_type"] == "error":
                        final_output += output_code_bloc(output["traceback"])
    return final_output


def lint_markdown(markdown_file_output):
    # Use Prettier to lint the markdown output
    subprocess.run(
        [
            "prettier",
            "--parser",
            "mdx",
            "--print-width",
            "9000",
            # avoid formatting code blocs inside markdown text (https://prettier.io/docs/en/options.html#embedded-language-formatting)
            "--embedded-language-formatting",
            "off",
            "--write",
            markdown_file_output,
        ],
    )
    # output = subprocess.getoutput(
    #     f"prettier --parser mdx {markdown_file_output}",
    # )
    # print(output)
    # input()


def save_to_file(output, output_path):
    with open(output_path, "w") as f:
        f.write(output)


def export_notebook_to_mdx(notebook_path, output_path):
    markdown_output = convert_notebook_to_md(notebook_path)
    if markdown_output is None:
        print("Error: no markdown output")
    else:
        save_to_file(markdown_output, output_path)
        lint_markdown(output_path)


if __name__ == "__main__":
    # Check if prettier with mdx parser is installed
    try:
        subprocess.run(["prettier", "--parser", "mdx"], stdout=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: prettier not found")
        exit(1)
    argparse = argparse.ArgumentParser()
    argparse.add_argument(
        "notebook_path",
        type=str,
        help="Path to the notebook",
        # required=True,
    )
    argparse.add_argument("--output", type=str, help="Output file")
    args = argparse.parse_args()
    markdown_output = convert_notebook_to_md(args.notebook_path)
    if markdown_output is None:
        print("Error: no markdown output")
        exit(1)
    # If argument --output is specified, write the output to the file
    if args.output:
        save_to_file(markdown_output, args.output)
    else:
        print(markdown_output)
