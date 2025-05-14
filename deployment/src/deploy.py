import os
import subprocess
import sys
from datetime import datetime
from glob import glob
from typing import Dict, List, Optional, Tuple, Union
import requests

import boto3
import psycopg2
from psycopg2.extras import Json
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from rich import print as richprint
from src.schemas_database import BaseSchema, ContentSchema, CourseSchema, ResourceSchema
from src.utils import open_yaml
from src.notebook_parser import export_notebook_to_mdx


class Deployment:
    mongo_tables = {
        "path": "paths",
        "track": "tracks",
        "course": "courses",
        "quiz": "quiz",
        "code-local": "quizCode",
    }

    def __init__(
        self,
        tree: Dict,
        mongodb_uri: str,
        aws_access_id: str,
        aws_secret_access_key: str,
        region_name: str,
        s3_bucket_content: str,
        s3_bucket_resources: str,
        github_workspace: str,
        github_repository_name: str,
        postgres_database: str,
        postgres_user: str,
        postgres_password: str,
        postgres_host: str,
        vimeo_token: str,
        verbose: bool = True,
    ) -> None:
        self.tree = tree
        self.verbose = verbose
        self._links = self.__get_links([], self.tree, self.tree["kind"])
        self._links.insert(0, f"/{self.tree['kind']}/{self.tree['slug']}")
        self._links.insert(
            len(self._links), f"/{self.tree['kind']}/{self.tree['slug']}"
        )
        self._root_slug = tree["slug"]
        self.mongo_client = MongoClient(mongodb_uri)
        self.region_name = region_name
        self.session = boto3.Session(
            aws_access_key_id=aws_access_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        self.s3client = self.session.client("s3")
        self.s3_bucket_content = s3_bucket_content
        self.s3_bucket_resources = s3_bucket_resources
        self.github_workspace = github_workspace
        self.github_repository_name = github_repository_name
        self.tmp_folder = "/tmp/julie"
        if not os.path.exists(self.tmp_folder):
            os.makedirs(self.tmp_folder)
        self.postgres_database = postgres_database
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.postgres_host = postgres_host
        self.vimeo_token = vimeo_token
        # Get "category" (meaning it is either a degree or an online course) based on
        # the Github repository name
        self.category = (
            "online" if "ONLINE_COURSES" in self.github_workspace else "degree"
        )

    def __push_to_earnings_list_postgres(self, item: Dict, kind: str):
        default_earnings = {
            "path-online": {"points": 10, "multiplier": None},
            "path-degree": {"points": 11, "multiplier": None},
            "track-online": {"points": 12, "multiplier": None},
            "track-degree": {"points": 13, "multiplier": None},
            "course-online": {"points": 14, "multiplier": None},
            "course-degree": {"points": 15, "multiplier": None},
            "video": {"points": 16, "multiplier": None},
            "lecture": {"points": 17, "multiplier": None},
            "exercice": {"points": 18, "multiplier": None},
            "project": {"points": 19, "multiplier": None},
            "quiz": {"points": 20, "multiplier": None},
            "code-local": {"points": 21, "multiplier": None},
        }
        with psycopg2.connect(
            f"dbname={self.postgres_database} user={self.postgres_user} password={self.postgres_password} host={self.postgres_host} port=5432"
        ) as conn:
            type = None

            if kind == "path" or kind == "track" or kind == "course":
                type = kind + "-" + item["category"]
            else:
                type = kind

            points = (
                item.get("points")
                if item.get("points")
                else default_earnings[type]["points"]
            )
            multiplier = (
                item.get("multiplier")
                if item.get("multiplier")
                else default_earnings[type]["multiplier"]
            )
            skills = item.get("skills") if item.get("skills") else None

            if skills:
                sumRatio = 0.0
                isRatioPresent = False
                isRationAbsent = False
                for skill in skills:
                    sumRatio += skill.get("ratio", 0.0)
                    if skill.get("ratio"):
                        isRatioPresent = True
                    else:
                        isRationAbsent = True
                if not (sumRatio == 0.0 or sumRatio == 1.0):
                    richprint(
                        f"[b red]ERROR: {item['slug']} has a ratio not equal to 1.[/b red]"
                    )
                    sys.exit()
                if not (isRatioPresent is not isRationAbsent):
                    richprint(
                        f"[b red]ERROR: {item['slug']} has skill with ratio key and other without.[/b red]"
                    )
                    sys.exit()

            curr = conn.cursor()
            curr.execute(
                """
                INSERT INTO earnings_list (id, type, points, multiplier, skills, created_at, updated_at)
                VALUES (%(slug)s, %(type)s, %(points)s, %(multiplier)s, %(skills)s, %(created_at)s, %(updated_at)s)
                ON CONFLICT (id)
                DO UPDATE SET points = %(points)s, multiplier = %(multiplier)s, skills = %(skills)s, updated_at = %(updated_at)s
                """,
                {
                    "slug": item["slug"],
                    "type": type,
                    "points": points,
                    "multiplier": multiplier,
                    "skills": Json(skills),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            )

            conn.commit()

    def __get_links(self, links: List, tree: Dict, kind: str) -> List[str]:
        for content in tree["children"]:
            if kind == "course":
                links.append(self.__compose_link(kind, tree["slug"], content["slug"]))
            else:
                self.__get_links(links, content, content["kind"])
        return links

    def __push_to_mongodb(self, document: Dict, kind: str):
        try:
            result = self.mongo_client.JULIE[self.mongo_tables[kind]].update_one(
                {"slug": document["slug"]}, {"$set": document}, upsert=True
            )
            if kind in {"quiz", "code-local"} and not result.matched_count:
                self.mongo_client.JULIE[self.mongo_tables[kind]].update_one(
                    {"slug": document["slug"]}, {"$set": {"created_at": datetime.now()}}
                )
            if kind in {"quiz", "code-local"} and result.modified_count:
                self.mongo_client.JULIE[self.mongo_tables[kind]].update_one(
                    {"slug": document["slug"]}, {"$set": {"updated_at": datetime.now()}}
                )
            if result.modified_count:
                richprint(
                    f"👍 {document['slug']} has been updated in {self.mongo_tables[kind]}"
                )
        except DuplicateKeyError as e:
            richprint(
                f"[b red]ERROR: {document['slug']} already exists in {self.mongo_tables[kind]}.[/b red]"
            )
            richprint(e)
        except Exception as e:
            richprint("[b red]ERROR:[/b red]")
            richprint(e)

    def __get_illustration(self, kind: str, slug: str) -> str:
        # sourcery skip: merge-comparisons, merge-duplicate-blocks, remove-redundant-if, remove-unnecessary-else, swap-if-else-branches
        if kind == "path":
            if slug in {"full-stack-full-time", "full-stack-part-time"}:
                return "fullstack"
            elif slug == "essentials":
                return "essentials"
            elif slug == "lead":
                return "lead"
            else:
                return "fullstack"
        else:
            return "workingMaleAndFemale"

    def __get_gradient(self, kind: str) -> str:
        return "sunset" if kind in {"course", "track"} else "twilight"

    def __get_children_slug_list(self, children_list: List[Dict]) -> List[str]:
        return [child["slug"] for child in children_list]

    def __get_modules(self, children_list: List) -> int:
        return len(children_list)

    def __upload_to_s3(
        self, filepath: str, bucket_name: str, outputpath: str
    ) -> Union[str, None]:
        richprint(f"🚀 Uploading {filepath} to S3 {bucket_name}")
        try:
            self.s3client.upload_file(filepath, bucket_name, outputpath)
            return f"https://{bucket_name}.s3.{self.region_name}.amazonaws.com/{outputpath}"
        except Exception as e:
            richprint(
                f"😓 An error occurred while pushing {filepath} to S3 {bucket_name}:"
            )
            richprint(e)

    def __convert_notebook_to_markdown(self, input_file: str, output_file: str) -> None:
        richprint(f"♻️ Converting {input_file} into mardkown")
        export_notebook_to_mdx(input_file, output_file)

    def __process_resources(self, resources: List[Dict]) -> Union[List[Dict], None]:
        if not resources:
            return None
        resources_final = []
        for resource in resources:
            # We assume that the resources are of "type" "file" by default. If
            # "type" key does not exist, create it and set it to "file"
            if "type" not in resource.keys():
                resource["type"] = "file"
            resource_link = resource["target"]
            if resource["type"] in ["file", "solution"]:
                # Upload resource file to S3
                resource_link = self.__upload_to_s3(
                    resource["path"],
                    self.s3_bucket_resources,
                    os.path.join(
                        self._root_slug,
                        resource["course_slug"],
                        resource["content_slug"],
                        resource["title"],
                    ),
                )
            # Put it in JSON load
            resource_ready = ResourceSchema().load(
                {
                    "name": resource["title"],
                    "link": resource_link,
                    "type": resource["type"],
                }
            )
            resources_final.append(resource_ready)
        return resources_final

    def __process_content(
        self, content: Union[Dict, str], type: str, slug: str
    ) -> Union[Dict, str]:
        if type == "quiz":
            content_yaml = glob(
                os.path.join(self.github_workspace, "**", content),
                recursive=True,
            )
            opened_yaml = open_yaml(content_yaml[0])
            opened_yaml["slug"] = slug
            self.__push_to_mongodb(opened_yaml, type)
        elif type == "code-local":
            content_yaml = glob(
                os.path.join(self.github_workspace, "**", content),
                recursive=True,
            )
            opened_yaml = open_yaml(content_yaml[0])
            opened_yaml["slug"] = slug
            self.__push_to_mongodb(opened_yaml, type)
        if type in {"video", "quiz", "code-local"}:
            return content
        basename = (
            os.path.join(
                "course", content["course_slug"], content["content_slug"]
            ).replace("/", "-")
            + ".mdx"
        )
        # Case for markdown ("normal" case)
        output_file = content["path"]
        # Case for notebooks
        if content["name"].endswith(".ipynb"):
            output_file = os.path.join(self.tmp_folder, basename)
            self.__convert_notebook_to_markdown(content["path"], output_file)
        self.__upload_to_s3(output_file, self.s3_bucket_content, basename)
        return basename

    def __compose_link(self, kind: str, course_slug: str, content_slug: str) -> str:
        # sourcery skip: use-fstring-for-concatenation
        return "/" + os.path.join(kind, course_slug, content_slug)

    def __get_prev_and_next_links(self, current_link: str) -> Tuple[str, str]:
        index = self._links.index(current_link)
        return self._links[index - 1], self._links[index + 1]

    def __get_source_github_url(self, filepath: Union[str, Dict]) -> str:
        if type(filepath) == str:
            filepath_name = filepath
        else:
            filepath_name = filepath["path"]
        path = filepath_name.split(self.github_repository_name)[-1]
        return f"https://github.com/JedhaBootcamp/{self.github_repository_name}/blob/main{path}"

    def __process_solution(
        self, content: str, content_slug: str, course_slug: str
    ) -> Union[str, None]:
        """Process the exercices solution files, send them to MongoDB `contents`
        collection.

        The slug is like `course-course-slug-content-slug-solution`.

        :param content: file path to the solution (either a markdown or notebook
            file).
        :param content_slug: the content slug of the exercise.
        :param course_slug: the course slug.
        :return: the S3 path.
        """
        source_file = glob(
            os.path.join(self.github_workspace, "**", content),
            recursive=True,
        )[0]
        solution_slug = "-".join(["course", course_slug, content_slug, "solution"])
        solution_basename = solution_slug + ".md"
        if content.endswith(".ipynb"):
            output_tmp_file = os.path.join(self.tmp_folder, solution_basename)
            self.__convert_notebook_to_markdown(source_file, output_tmp_file)
            source_file = output_tmp_file
        with open(source_file, "r") as f:
            markdown_content = f.read()
        self.mongo_client.JULIE["contents"].update_one(
            {"slug": solution_slug},
            {
                "$set": {
                    "slug": solution_slug,
                    "content": markdown_content,
                    "resources": [],
                }
            },
            upsert=True,
        )
        return solution_slug

    def __get_vimeo_video_duration(self, video_id: str) -> int:
        """Fecth the Vimeo API to get the video stats and retrieve the duration.

        Returns the rounded duration in minutes.

        :param video_id: the video ID, usually looks like `651193403`.
        """
        duration = 90
        try:
            response = requests.get(
                f"https://api.vimeo.com/users/97521436/videos/{video_id}",
                headers={"Authorization": f"bearer {self.vimeo_token}"},
            )
            response_json = response.json()
            duration = int(round(int(response_json["duration"]) / 60))
            return duration
        except:
            print(f"ERROR: Couldn't get duration for video ID {video_id}")
            return duration

    def __process_contents(
        self,
        contents: List[Dict],
        course_slug: str,
        replay: Dict[str, Optional[str]],
    ) -> List[Dict]:
        contents_final = []
        link = None
        prev = None
        next = None
        for content in contents:
            link = self.__compose_link("course", course_slug, content["slug"])
            prev, next = self.__get_prev_and_next_links(link)
            duration = content["duration"]
            if content["type"] == "video":
                duration = self.__get_vimeo_video_duration(content["content"])
            content_dict = {
                "slug": content["slug"],
                "title": content["title"],
                "type": content["type"],
                "duration": duration,
                "content": self.__process_content(
                    content["content"], content["type"], content["slug"]
                ),
                "link": link,
                "prevLink": prev,
                "nextLink": next,
                "points": content.get("points"),
                "skills": content.get("skills"),
                "multiplier": content.get("multiplier"),
                "source": self.__get_source_github_url(content["content"]),
            }
            if "solution" in content.keys():
                # We rely on the fact that the tree have already done the check
                # on the type so we are sure it is an exercice
                content_dict["solution"] = self.__process_solution(
                    content["solution"], content["slug"], course_slug
                )
            content_dict["resources"] = self.__process_resources(content["resources"])

            content_ready = ContentSchema().load(content_dict)
            contents_final.append(content_ready)
            self.__push_to_earnings_list_postgres(content_ready, content["type"])
        prev = link
        next = next
        if replay["replay"] or replay["replay_fr"] or replay["replay_en"]:
            for replay_key in replay.keys():
                if not replay[replay_key]:
                    continue
                if replay_key == "replay_en":
                    replay_slug = f"{course_slug}-replay-en"
                    replay_title = "Replay 🇬🇧"
                    replay_content = replay["replay_en"]
                    replay_duration = self.__get_vimeo_video_duration(
                        replay["replay_en"].split("/")[-1]
                    )
                    replay_prev = (
                        self.__compose_link(
                            "course", course_slug, f"{course_slug}-replay-fr"
                        )
                        if replay["replay_fr"]
                        else prev
                    )
                    replay_next = next
                else:
                    replay_slug = f"{course_slug}-replay-fr"
                    replay_title = "Replay 🇫🇷"
                    replay_content = (
                        replay["replay_fr"] if replay["replay_fr"] else replay["replay"]
                    )
                    replay_duration = 90
                    replay_prev = prev
                    replay_next = (
                        self.__compose_link(
                            "course", course_slug, f"{course_slug}-replay-en"
                        )
                        if replay["replay_en"]
                        else next
                    )
                    if replay_key == "replay_fr":
                        replay_duration = self.__get_vimeo_video_duration(
                            replay["replay_fr"].split("/")[-1]
                        )
                    if replay_key == "replay":
                        replay_duration = self.__get_vimeo_video_duration(
                            replay["replay"].split("/")[-1]
                        )
                content_replay = ContentSchema().load(
                    {
                        "slug": replay_slug,
                        "title": replay_title,
                        "type": "replay",
                        "duration": replay_duration,
                        "content": replay_content,
                        "link": self.__compose_link("course", course_slug, replay_slug),
                        "prevLink": replay_prev,
                        "nextLink": replay_next,
                        "resources": None,
                    }
                )
                contents_final.append(content_replay)
        return contents_final

    def __sum_minutes(self, contents: List[Dict]) -> int:
        sum_minutes = 0
        for content in contents:
            sum_minutes += content["duration"]
        return sum_minutes

    def __process_teacher_notes(self, notes: Dict, course_slug: str) -> str:
        """Process the teacher notes and attached resources, send them to
        MongoDB in `contents` collection.

        The teacher note should be an unique markdown file.

        The slug for a notes form is `notes-course-slug-suffix`.

        :param notes: a dictionary from the YAML file.
        :param course_slug: the course slug in which the note belongs to.
        :return: the slug
        """
        notes_slug = "-".join(["notes", course_slug])
        notes_filepath = glob(
            os.path.join(self.github_workspace, "**", notes["content"]),
            recursive=True,
        )[0]
        resources = []
        if notes["resources"]:
            for resource in notes["resources"]:
                resource_filepath = glob(
                    os.path.join(self.github_workspace, "**", resource["target"]),
                    recursive=True,
                )
                notes_s3_resources_output_path = os.path.join(
                    self._root_slug,
                    course_slug,
                    "notes",
                    resource["title"],
                )
                resource_link = self.__upload_to_s3(
                    resource_filepath[0],
                    self.s3_bucket_resources,
                    notes_s3_resources_output_path,
                )
                resources.append({"link": resource_link, "name": resource["title"]})
        with open(notes_filepath, "r") as f:
            markdown_content = f.read()
        self.mongo_client.JULIE["contents"].update_one(
            {"slug": notes_slug},
            {
                "$set": {
                    "slug": notes_slug,
                    "content": markdown_content,
                    "resources": resources,
                }
            },
            upsert=True,
        )
        return notes_slug

    def __internal_deploy(
        self, tree: Dict, kind: str, parents: List[Dict[str, str]], minutes: int
    ) -> int:
        children: List[Dict] = tree["children"]
        illustration: str = self.__get_illustration(kind, tree["slug"])
        gradient: str = self.__get_gradient(kind)
        parents_copy: List[Dict[str, str]] = parents.copy()
        link: str = "/" + os.path.join(tree["kind"], tree["slug"])
        if kind == "course":
            contents_processed = self.__process_contents(
                children,
                tree["slug"],
                {
                    "replay": tree.get("replay"),
                    "replay_fr": tree.get("replay_fr"),
                    "replay_en": tree.get("replay_en"),
                },
            )
            minutes = self.__sum_minutes(contents_processed)
            course = {
                "slug": tree["slug"],
                "title": tree["title"],
                "level": tree["level"],
                "link": link,
                "duration": tree["duration"],
                "minutes": minutes,
                "modules": self.__get_modules(children),
                "illustration": illustration,
                "gradient": gradient,
                "type": tree["kind"].capitalize(),
                "introductionVideoId": tree.get("introductionVideoId"),
                "description": tree.get("description"),
                "goals": tree.get("goals"),
                "prerequisites": tree.get("prerequisites"),
                "tags": tree.get("tags"),
                "access": tree["access"],
                "parents": parents_copy,
                "children": contents_processed,
                "category": self.category,
                "points": tree.get("points"),
                "skills": tree.get("skills"),
                "isWorkingDay": tree.get("isWorkingDay", True),
            }
            if "notes" in tree.keys():
                self.__process_teacher_notes(tree["notes"], tree["slug"])
                course["notes"] = True
            item = CourseSchema().load(course)
        else:
            if "ONLINE_COURSES" in self.github_workspace:
                # Update online collection
                online_doc = {
                    "href": f"/{tree['kind']}/{tree['slug']}",
                    "duration": tree["duration"],
                    "gradients": "sunset",
                    "illus": "workingMaleAndFemale",
                    "level": tree["level"],
                    "modules": len(tree["children"]),
                    "title": tree["title"],
                    "access": tree["access"],
                }
                self.mongo_client.JULIE["online"].update_one(
                    {"slug": tree["slug"]}, {"$set": online_doc}, upsert=True
                )
            parents_copy.append({"slug": tree["slug"], "kind": tree["kind"]})
            minutes = 0
            for child in children:
                minutes += self.__internal_deploy(
                    child, child["kind"], parents_copy, minutes
                )
            item = BaseSchema().load(
                {
                    "slug": tree["slug"],
                    "title": tree["title"],
                    "level": tree["level"],
                    "link": link,
                    "duration": tree["duration"],
                    "minutes": minutes,
                    "modules": self.__get_modules(children),
                    "illustration": illustration,
                    "gradient": gradient,
                    "type": tree["kind"].capitalize(),
                    "introductionVideoId": tree.get("introductionVideoId"),
                    "description": tree.get("description"),
                    "goals": tree.get("goals"),
                    "prerequisites": tree.get("prerequisites"),
                    "tags": tree.get("tags"),
                    "access": tree["access"],
                    "parents": parents_copy,
                    "children": self.__get_children_slug_list(children),
                    "category": self.category,
                    "points": tree.get("points"),
                    "skills": tree.get("skills"),
                    "topic": tree.get("topic"),
                    "pathLevel": tree.get("pathLevel"),
                    "schedule": tree.get("schedule"),
                    "halfDays": tree.get("halfDays"),
                }
            )
        self.__push_to_mongodb(item, kind)
        self.__push_to_earnings_list_postgres(item, kind)
        return minutes

    def deploy(self) -> None:
        tree = self.tree
        self.__internal_deploy(tree, tree["kind"], [], 0)
