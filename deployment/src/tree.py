import os
import subprocess
from collections import Counter
from glob import glob
from pprint import pprint
from typing import Dict, List, Optional, Union

from marshmallow.exceptions import ValidationError
from rich import print as richprint
from src.exceptions import NoRootFileError, NoTreeError
from src.schemas_file import (
    FileBaseSchema,
    FileCourseBaseSchema,
    QuizCodeSchema,
    QuizSchema,
)
from src.utils import open_yaml


class ErrorManager:
    def __init__(self) -> None:
        self.errors = []

    def add_error(
        self, title: str, message: Union[str, List, Dict], level: str = "FATAL"
    ) -> None:
        """Adds error to the list error.

        In order to display the list of all errors, you should call this method.
        Works with `_report` method to display the errors list to the stdout.

        :param title: the title of the error
        :type title: str
        :param message: the message of the error
        :type message: str
        :param level: you can give a level to the error, defaults to "FATAL"
        :type level: str, optional
        """
        self.errors.append({"title": title, "message": message, "level": level})

    def get_errors(self) -> List[Dict[str, str]]:
        """Returns the list of errors."""
        return self.errors

    def has_errors(self) -> bool:
        """Returns True if it has error, False otherwise."""
        if self.errors:
            return True
        return False

    def report(self) -> None:
        """Prints the list of errors and returns True if there is at least one error."""
        if self.has_errors():
            for error in self.errors:
                message = error["message"]
                richprint(
                    f"[b red]{error['level']:5}[/b red] → {error['title']:15}: ", end=""
                )
                if type(message) == dict:
                    pprint(message)
                else:
                    print(message)
        else:
            richprint("🎉 [green][b]CHECK:[/b] Tree build successfully![/green]")


class NodePath(dict):
    def __init__(self) -> None:
        pass


class NodeTrack(dict):
    def __init__(self) -> None:
        pass


class NodeCourse(dict):
    def __init__(self) -> None:
        pass


class Tree:
    """Produces a dictionary tree from several YAML files.

    :param workspace: the current workspace, it should be the folder where to
        find the following root_file file
    :type workspace: str
    :param root_file: the root file defining the tree root
    :type root_file: str
    """

    def __init__(self, workspace: str = ".", root_file: str = "root.yaml") -> None:
        self.workspace = workspace
        self.root_file = root_file
        self.tree: Dict = {}
        self.errors: ErrorManager = ErrorManager()

    def __check_notebooks(self, filepath: str) -> None:
        try:
            subprocess.run(["notebooktomdx", "-v", filepath], text=False, check=True)
        except subprocess.SubprocessError as err:
            self.errors.add_error("Invalid notebook", f"{filepath} error: {err}")

    def __check_empty_file(self, filepath: str) -> None:
        if os.path.getsize(filepath) == 0:
            self.errors.add_error(
                "Empty file",
                f"The file {filepath} is empty, are you sure this is the right file?",
            )

    def __check_files(self, filename: str, filepaths: List[str], kind: str) -> bool:
        """Returns True if the file is valid, False otherwise."""
        if kind not in {"lecture", "exercice", "project", "quiz", "code-local", "yaml"}:
            return True
        valid = True
        if len(filepaths) == 0:
            self.errors.add_error("File not found", f"Could not find {filename}")
            valid = False
        if len(filepaths) > 1:
            self.errors.add_error(
                "Found more than one file",
                f"We found more than one {filename}, you cannot create duplicates",
            )
            valid = False
        if len(filepaths) == 1:
            if not os.path.exists(filepaths[0]):
                self.errors.add_error(
                    "File does not exist", f"{filepaths[0]} does not exist"
                )
                valid = False
            self.__check_empty_file(filepaths[0])
        return valid

    def __get_filepath(self, filename: str) -> List[str]:
        return glob(
            os.path.join(self.workspace, "**", filename),
            recursive=True,
        )

    def __process_files(
        self, children: List[Dict], parent: Optional[str]
    ) -> List[Dict]:
        for i, _ in enumerate(children):
            content_to_resource = None
            filepath = self.__get_filepath(children[i]["content"])
            file_is_valid = self.__check_files(
                children[i]["content"], filepath, children[i]["type"]
            )
            if children[i]["type"] == "quiz":
                if not file_is_valid:
                    continue
                content_yaml = open_yaml(filepath[0])
                try:
                    QuizSchema().load(content_yaml)
                except ValidationError as err:
                    self.errors.add_error(
                        title=f"Schema error → {filepath[0]}",
                        message=err.messages,
                    )
            elif children[i]["type"] == "code-local":
                if not file_is_valid:
                    continue
                content_yaml = open_yaml(filepath[0])
                try:
                    QuizCodeSchema().load(content_yaml)
                except ValidationError as err:
                    self.errors.add_error(
                        title=f"Schema error → {filepath[0]}",
                        message=err.messages,
                    )
            elif children[i]["type"] in {"lecture", "exercice", "project"}:
                if not file_is_valid:
                    continue
                if children[i]["type"] != "exercice":
                    if "solution" in children[i].keys():
                        self.errors.add_error(
                            title="solution key is not allowed here",
                            message="solution key should be attached to exercice content only.",
                        )
                        continue
                if "solution" in children[i].keys():
                    self.__check_files(
                        children[i]["solution"],
                        self.__get_filepath(children[i]["solution"]),
                        "exercice",
                    )
                    if (
                        not children[i]["solution"].endswith(".ipynb")
                        and not children[i]["solution"].endswith(".md")
                        and not children[i]["solution"].endswith(".mdx")
                    ):
                        self.errors.add_error(
                            title=f"solution file extension is wrong for {children[i]['solution']}",
                            message="solution should be markdown (.md), MDX (.mdx) or notebook file (.ipynb).",
                        )
                children[i]["content"] = {
                    "name": children[i]["content"],
                    "content_slug": children[i]["slug"],
                    "course_slug": parent,
                    "type": "content",
                    "path": filepath[0],
                }
                if children[i]["content"]["name"].endswith(".ipynb"):
                    # Add content as resources in order to make it downloadable
                    # only if it is a notebook
                    content_to_resource = {
                        "content_slug": children[i]["slug"],
                        "course_slug": parent,
                        "path": filepath[0],
                        "target": children[i]["content"]["name"],
                        "title": children[i]["content"]["name"],
                    }
                if (
                    children[i]["type"] == "exercice"
                    and "solution" in children[i].keys()
                    and children[i]["solution"].endswith(".ipynb")
                ):
                    # Add solution to resources automatically
                    if not children[i]["resources"]:
                        children[i]["resources"] = []
                    children[i]["resources"].append(
                        {
                            "target": children[i]["solution"],
                            "title": children[i]["solution"],
                            "type": "solution",
                        }
                    )

            if children[i]["resources"]:
                for j, _ in enumerate(children[i]["resources"]):
                    if (
                        "type" in children[i]["resources"][j].keys()
                        and children[i]["resources"][j]["type"] == "website"
                    ):
                        # Case resource is just a website
                        continue
                    resource_filepath = self.__get_filepath(
                        children[i]["resources"][j]["target"]
                    )
                    if len(resource_filepath) == 0:
                        self.errors.add_error(
                            "File not found",
                            f"Could not find {children[i]['resources'][j]['target']}",
                        )
                        continue
                    children[i]["resources"][j]["content_slug"] = children[i]["slug"]
                    children[i]["resources"][j]["course_slug"] = parent
                    children[i]["resources"][j]["path"] = resource_filepath[0]
                    self.__check_empty_file(resource_filepath[0])

            if content_to_resource:
                # Last but not least: add the content as resource to the list
                if children[i]["resources"]:
                    children[i]["resources"].append(content_to_resource)
                else:
                    children[i]["resources"] = [content_to_resource]

        return children

    def __check_yaml_schema(self, content: dict, filename: str) -> bool:
        valid = True
        try:
            if not "kind" in content.keys():
                raise ValidationError("Missing 'kind' key in YAML file")
            if content["kind"] == "course":
                FileCourseBaseSchema().load(content)
            else:
                FileBaseSchema().load(content)
        except ValidationError as err:
            self.errors.add_error(
                title=f"[b red]SCHEMA ERROR[/b red] → {filename}",
                message=err.messages,
            )
            valid = False
        finally:
            return valid

    def __get_yamlpath(self, filename: str) -> List[str]:
        """Returns list of file path found for filename.

        :param filename: the filename slug WITHOUT extension, e.g.
            `my-file-name`
        """
        filepath = os.path.join(self.workspace, "**", filename)
        yaml_extension = glob(filepath + ".yaml", recursive=True)
        yml_extension = glob(filepath + ".yml", recursive=True)
        return list(set(yaml_extension + yml_extension))

    def __get_children_file_list(
        self,
        children: List,
        kind: str,
        parent: Optional[str],
        access_from_root: Optional[str],
        level_from_root: Optional[str],
        others_from_root: Optional[Dict[str, Optional[str]]] = None,
    ) -> List:
        if kind == "course":
            return self.__process_files(children, parent)
        children_file_list = []
        for filename in children:
            # Remove extension to manage children with `.yaml` or `.yml`
            filename = os.path.splitext(filename)[0]
            glob_find = self.__get_yamlpath(filename)
            if not self.__check_files(filename, glob_find, "yaml"):
                continue
            content = open_yaml(glob_find[0])
            if not self.__check_yaml_schema(content, glob_find[0]):
                continue
            if content["slug"] != filename:
                self.errors.add_error(
                    "Slug and file mismatch",
                    f"The file {glob_find[0]} has not the same name as the slug '{content['slug']}'",
                )
                continue
            # Add topic, pathLevel and schedule from root file to track file if not specified
            # if content["kind"] == "track":
            if kind == "path":
                if others_from_root is not None:
                    content["topic"] = others_from_root["topic"]
                    content["pathLevel"] = others_from_root["pathLevel"]
                    content["schedule"] = others_from_root["schedule"]
            if content["kind"] == "course":
                if "notes" in content.keys():
                    notes_filepath = self.__get_filepath(content["notes"]["content"])
                    if len(notes_filepath) == 0:
                        self.errors.add_error(
                            "File not found",
                            f"Could not find {content['notes']['content']}",
                        )
                        continue
                    self.__check_empty_file(notes_filepath[0])
            if "level" not in content.keys():
                if level_from_root:
                    content["level"] = level_from_root
                else:
                    self.errors.add_error(
                        "Can't infer level from root file",
                        f"The file {glob_find[0]} does not precise level on its own and root.yaml file does not either. Please precise one of them",
                    )
            if "access" not in content.keys():
                if access_from_root:
                    content["access"] = access_from_root
                else:
                    self.errors.add_error(
                        "Can't infer access from root file",
                        f"The file {glob_find[0]} does not precise access on its own and root.yaml file does not either. Please precise one of them",
                    )
            content_children = content["children"]
            content["children"] = self.__get_children_file_list(
                content_children,
                content["kind"],
                content["slug"],
                access_from_root,
                level_from_root,
            )
            children_file_list.append(content)
        return children_file_list

    def __tree_traversal(
        self, children: List, kind: str, selected_key: str = "slug"
    ) -> List[str]:
        if kind == "course":
            return [content[selected_key] for content in children]
        new_list = []
        for child in children:
            new_list.append(child["slug"])
            children_list = self.__tree_traversal(
                child["children"], child["kind"], selected_key
            )
            new_list.extend(children_list)
        return new_list

    def __check_slugs(self) -> None:
        slugs_list: List[str] = [self.tree["slug"]]
        children_list = self.__tree_traversal(
            self.tree["children"], self.tree["kind"], "slug"
        )
        slugs_list.extend(children_list)
        if len(slugs_list) != len(set(slugs_list)):
            self.errors.add_error(
                "Duplicate slugs",
                f"Some slugs are not unique: {[item for item, count in Counter(slugs_list).items() if count > 1]}",
            )

    def build(self) -> Dict:
        """Returns the tree as a dictionnary containing all infos from YAML
        files.

        It iterates from root_file over all other YAML files, building a tree using
        dictionnary. It also check that the YAML files respects a schema.
        """
        richprint("👷‍♂️ [b]Building the tree from YAML files[/b]")
        root_file_path = glob(os.path.join(self.workspace, self.root_file))

        if len(root_file_path) != 1:
            raise NoRootFileError

        root_content = open_yaml(root_file_path[0])

        self.__check_yaml_schema(root_content, root_file_path[0])

        if not "access" in root_content.keys():
            self.errors.add_error(
                "No access key in root file",
                "You need to precise the access key at least in the root file. If you do not for the children it will be infered from the root file",
            )
        if not "level" in root_content.keys():
            self.errors.add_error(
                "No level key in root file",
                "You need to precise the level key at least in the root file. If you do not for the children it will be infered from the root file",
            )

        root_content_children = root_content["children"]

        other_from_root = (
            {
                "topic": root_content.get("topic"),
                "pathLevel": root_content.get("pathLevel"),
                "schedule": root_content.get("schedule"),
            }
            if root_content["kind"] == "path"
            else None
        )

        children_content = self.__get_children_file_list(
            root_content_children,
            root_content["kind"],
            None,
            root_content.get("access"),
            root_content.get("level"),
            other_from_root,
        )

        root_content["children"] = children_content

        self.tree = root_content
        self.__check_slugs()
        return self.tree

    def get_tree(self) -> Dict:
        if not self.tree:
            raise NoTreeError
        return self.tree
