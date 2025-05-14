import os
import glob
import yaml
import argparse

from pprint import pprint

import boto3

repository = os.getenv("GITHUB_WORKSPACE", ".")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
region_name = os.getenv("REGION_NAME", "")
s3_bucket_content = os.getenv("S3_BUCKET_NAME", "")
s3_bucket_resources = os.getenv("S3_BUCKET_NAME_RESOURCES", "")

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name,
)
s3_client = session.client("s3")


def upload_file_to_s3(file_path, s3_key):
    s3_client.upload_file(file_path, s3_bucket_content, s3_key)


def get_course_yaml_files(github_repository_name):
    contents = {}
    for root, dirs, files in os.walk(github_repository_name):
        if "old" in root:
            continue
        for file_name in files:
            if file_name.endswith(".yaml"):
                file_path = os.path.join(root, file_name)
                with open(file_path, "r") as file:
                    yaml_data = yaml.safe_load(file)
                    if yaml_data.get("kind") == "course":
                        contents_file_name = []
                        for child in yaml_data["children"]:
                            contents_file_name.append(
                                {"slug": child["slug"], "content": child["content"]}
                            )

                        contents[yaml_data["slug"]] = contents_file_name
    return contents


def upload_course_files_to_s3(course_files, version):
    for course, files in course_files.items():
        print(f"⏳ \033[1mUploading files from course '{course}'\033[0m")
        for file in files:
            file_path = None
            for path in glob.glob(
                os.path.join(repository, "**", file["content"]), recursive=True
            ):
                if os.path.isfile(path):
                    file_path = path
                    break
            if file_path is not None:
                file_name = f"course-{course}-{file['slug']}"
                s3_file_key = f"{version}/{file_name}"
                print(f"\t🚀 Uploading {file_path} to {s3_file_key}")
                upload_file_to_s3(file_path, s3_file_key)


def main(args):
    github_workspace = os.getenv("GITHUB_WORKSPACE", ".")
    course_yaml_files = get_course_yaml_files(github_workspace)
    upload_course_files_to_s3(
        course_yaml_files,
        args.version[5:],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check and deploy a cursus to JULIE.")
    parser.add_argument(
        "--version",
        default=None,
        help="Content version to deploy",
    )
    args = parser.parse_args()
    main(args)
