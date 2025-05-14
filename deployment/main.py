import argparse
import json
import os
import sys
from glob import glob
import subprocess

from rich import print as richprint
from src.deploy import Deployment
from src.tree import Tree


def get_github_repository(github_workspace: str) -> str:
    """Returns repository name only.

    If it runs in local, it will look which known repository name we are running
    from. YOU NEED TO GIVE THE FOLDER THE SAME NAME AS THE REPOSITORY.

    If it runs in Github Action it will take GITHUB_WORKSPACE and split the
    value to keep the name only.
    """
    repository = os.getenv("GITHUB_WORKSPACE")
    if repository:
        repository = repository.split("/")
        return repository[-1]
    repository_name_list = [
        "ESSENTIALS_PROGRAM",
        "FULL_STACK_12_WEEK_PROGRAM",
        "FULL_STACK_24_WEEK_PROGRAM",
        "LEAD_PROGRAM",
        "cybersecurity_essentials_program",
        "CYBERSEC_FULLSTACK_12_WEEK_PROGRAM",
        "DATA_ANALYTICS_FULL_STACK_PROGRAM",
    ]
    for name in repository_name_list:
        if name in github_workspace:
            return name
    return "Not-A-Repo-Name"


def check_mdx_syntax(github_workspace):
    """Check if all mdx files are correctly formatted."""
    mdx_files = glob(os.path.join(github_workspace, "**/*.mdx"), recursive=True)
    has_errors = False
    for mdx_file in mdx_files:
        output = subprocess.run(["mdx-check", mdx_file], capture_output=True, text=True)
        if output.returncode != 0:
            richprint(f"🚨 {mdx_file} is not correctly formatted.")
            richprint(output.stderr)
            has_errors = True
    return has_errors


def main(args: argparse.Namespace) -> None:
    mongodb_uri = os.getenv("MONGODB_URI", "")

    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    region_name = os.getenv("REGION_NAME", "")
    s3_bucket_content = os.getenv("S3_BUCKET_NAME", "")
    s3_bucket_resources = os.getenv("S3_BUCKET_NAME_RESOURCES", "")

    github_workspace = os.getenv("GITHUB_WORKSPACE", ".")
    github_repository_name = get_github_repository(github_workspace)

    postgres_database = os.getenv("POSTGRES_DATABASE", "")
    postgres_user = os.getenv("POSTGRES_USER", "")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_host = os.getenv("POSTGRES_HOST", "")

    vimeo_token = os.getenv("VIMEO_TOKEN", "")

    root_files = glob(os.path.join(github_workspace, "**", "root.yaml"), recursive=True)

    has_mdx_errors = False
    if not args.deploy:
        richprint("Checking mdx syntax...")
        has_mdx_errors = check_mdx_syntax(github_workspace)
        if has_mdx_errors:
            richprint(
                "🚨 Some mdx files are not correctly formatted. Please check the above logs for more infos."
            )
        else:
            richprint("✅ All mdx files are correctly formatted.")
    has_errors = has_mdx_errors
    for root_file in root_files:
        # This allow us to proceed only one folder
        if args.only and args.only != os.path.basename(os.path.dirname(root_file)):
            continue

        richprint(f"👷‍♀️ Working on: {os.path.dirname(root_file)}")
        # Get tree and perform checks
        tree_cursus = Tree(workspace=github_workspace, root_file=root_file)
        tree = tree_cursus.build()

        if args.json:
            with open(args.json, "w") as f:
                json.dump(tree, f, indent=2)
            richprint("⬇️ JSON file written to ", args.json)

        errors = tree_cursus.errors.get_errors()

        if errors:
            has_errors = True

        if args.deploy and len(errors) == 0:
            # Deploy!
            deploy = Deployment(
                tree,
                mongodb_uri,
                aws_access_key_id,
                aws_secret_access_key,
                region_name,
                s3_bucket_content,
                s3_bucket_resources,
                github_workspace,
                github_repository_name,
                postgres_database,
                postgres_user,
                postgres_password,
                postgres_host,
                vimeo_token,
            )
            deploy.deploy()
            richprint("✅ Deployment done!")
        else:
            tree_cursus.errors.report()
    if has_errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check and deploy a cursus to JULIE.")
    parser.add_argument(
        "--deploy",
        action="store_true",
        default=False,
        help="Push the content to JULIE backend",
    )
    parser.add_argument(
        "--json",
        action="store",
        default=None,
        help="Output the tree in JSON format, precise the path and filename",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Process only the folder corresponding slug",
    )
    args = parser.parse_args()

    main(args)
