#!/usr/bin/env python
import os
import subprocess
import sys


class SDKProject:
    CORE = "core-sdk"
    LANGCHAIN = "dist-langchain"
    MCP = "dist-mcp"


class SDKPackage:
    CORE = "alation-ai-agent-sdk"
    LANGCHAIN = "alation-ai-agent-langchain"
    MCP = "alation-ai-agent-mcp"


sdk_project_dirs = [SDKProject.CORE, SDKProject.LANGCHAIN, SDKProject.MCP]
sdk_package_names = [SDKPackage.CORE, SDKPackage.LANGCHAIN, SDKPackage.MCP]


def verify_changes():
    ruff_check_all_projects()
    ruff_format_all_projects()

    projects_to_version_bump = projects_needing_version_bump()
    if len(projects_to_version_bump) != 0:
        print(
            "Please bump the version within pyproject.toml for the following projects:"
        )
        for project in projects_to_version_bump:
            print(f" - {project}/pyproject.toml")
        sys.exit(1)
    else:
        print("pyproject.toml files reflect changes")
    projects_needing_requirements_update()
    sys.exit(0)


def ruff_check_all_projects():
    for project in sdk_project_dirs:
        result = subprocess.run(
            ["ruff", "check", "--fix", project],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"ruff check failed - {project}:")
            print(result.stdout)
            print(result.stderr)
        else:
            print(f"ruff check passed - {project}.")


def ruff_format_all_projects():
    for project in sdk_project_dirs:
        result = subprocess.run(
            ["ruff", "format", project],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"ruff format failed - {project}:")
            print(result.stdout)
            print(result.stderr)
        else:
            print(f"ruff format passed - {project}.")


def get_current_working_dir():
    return os.getcwd()


def get_local_branch_name():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: Failed to get current git branch name.")
        print(result.stderr)
        exit(1)
    return result.stdout.strip()


def get_files_changed_from_base(
    is_relative: bool = False, grep_filter: str | None = None
):
    local_branch_name = get_local_branch_name()
    # NOTE: These paths are relative to the repo root and not the current working directory
    relative_option = "--relative" if is_relative else ""
    # Get the merge base
    merge_base_result = subprocess.run(
        ["git", "merge-base", "main", local_branch_name],
        capture_output=True,
        text=True,
        check=True,
    )
    merge_base = merge_base_result.stdout.strip()
    diff_args = ["git", "diff", "--no-color", "--name-only"]
    if relative_option:
        diff_args.append(relative_option)
    diff_args.extend([merge_base, "."])
    diff_result = subprocess.run(
        diff_args,
        capture_output=True,
        text=True,
        check=True,
    )
    files = diff_result.stdout.strip().split("\n")
    if grep_filter:
        files = [f for f in files if grep_filter in f]
    return files


def group_changes_by_project(is_relative: bool = False, grep_filter: str | None = None):
    files_changed = get_files_changed_from_base(
        is_relative=is_relative, grep_filter=grep_filter
    )
    changed_projects = {}
    for file_path in files_changed:
        for sdk_project_name in sdk_project_dirs:
            if sdk_project_name in file_path:
                changed_projects[sdk_project_name] = changed_projects.get(
                    sdk_project_name, []
                ) + [file_path]
                break
    return changed_projects


def split_semantic_version(semantic_version_str: str) -> list[int]:
    return list(map(int, semantic_version_str.split(".")))


def is_pyproject_version_already_bumped(pyproject_file_path: str):
    local_branch_name = get_local_branch_name()
    # Get the merge base between main and the local branch
    merge_base_result = subprocess.run(
        ["git", "merge-base", "main", local_branch_name],
        capture_output=True,
        text=True,
        check=True,
    )
    merge_base = merge_base_result.stdout.strip()
    # Get the diff for the pyproject_file_path
    diff_result = subprocess.run(
        ["git", "diff", "--no-color", merge_base, "--", pyproject_file_path],
        capture_output=True,
        text=True,
        check=True,
    )
    new_version = None
    old_version = None
    for line in diff_result.stdout.splitlines():
        if line.startswith("+version"):
            new_version = line.split("=")[-1].strip().replace('"', '')
        if line.startswith("-version"):
            old_version = line.split("=")[-1].strip().replace('"', '')
    # Check if any line in the diff adds a version line

    if not new_version or not old_version:
        return False
    old_version_parts = split_semantic_version(old_version)
    new_version_parts = split_semantic_version(new_version)
    return new_version_parts > old_version_parts


monitored_file_suffixes = set([".py", "Dockerfile", "LICENSE", ".toml"])


def projects_needing_version_bump():
    changed_projects = group_changes_by_project(is_relative=True)
    projects_needing_version_bump = set()
    for project, project_files in changed_projects.items():
        advance_project = False
        for file_path in project_files:
            if advance_project:
                break
            for monitored_file_suffix in monitored_file_suffixes:
                if advance_project:
                    break
                if file_path.endswith(monitored_file_suffix):
                    projects_needing_version_bump.add(project)
                    advance_project = True
                    break
    for project, project_files in changed_projects.items():
        if project not in projects_needing_version_bump:
            continue
        for file_path in project_files:
            # We want to discover pyproject.toml changes because the developer
            # may have already bumped the version. Let's take a closer look.
            if file_path.endswith("pyproject.toml"):
                if is_pyproject_version_already_bumped(pyproject_file_path=file_path):
                    projects_needing_version_bump.remove(project)
                break
    return projects_needing_version_bump


def group_requirements_files_by_project_name():
    result = subprocess.run(
        ["find", ".", "-name", "requirements.txt"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    grouped_requirements = {}
    for line in result.stdout.split("\n"):
        for project_name in sdk_project_dirs:
            if project_name in line:
                grouped_requirements[project_name] = grouped_requirements.get(
                    project_name, []
                ) + [line.strip()]
    return grouped_requirements

# TODO: some pyproject.toml list other packages as dependencies - those need to be changed as well


def get_changed_project_versions_dict(
    changed_projects_and_pyproject_files: dict[str, list[str]],
) -> dict[str, str]:
    changed_projects_and_project_versions = {}
    for project_name, project_files in changed_projects_and_pyproject_files.items():
        for pyproject_file_path in project_files:
            new_project_version = get_project_version_str(
                pyproject_file_path=pyproject_file_path
            )
            changed_projects_and_project_versions[project_name] = new_project_version
    return changed_projects_and_project_versions


def process_requirements_file_for_project(
    changed_projects_and_project_versions: dict[str, str], requirement_file: str
):
    packages_needing_update = []
    for (
        inner_project_name,
        package_version,
    ) in changed_projects_and_project_versions.items():
        package_name = get_package_name_from_project(project_name=inner_project_name)
        if is_package_required(
            package_name=package_name,
            requirements_file=requirement_file,
        ) and not is_package_version_current(
            package_name=package_name,
            package_version=package_version,
            requirements_file=requirement_file,
        ):
            packages_needing_update.append(f"{package_name}>={package_version}")
    return packages_needing_update


def process_requirements_files_for_project(
    requirements_files: list[str],
    changed_projects_and_project_versions: dict[str, str],
    is_fatal: bool = False,
):
    for requirement_file in requirements_files:
        packages_needing_update = process_requirements_file_for_project(
            changed_projects_and_project_versions=changed_projects_and_project_versions,
            requirement_file=requirement_file,
        )
        if len(packages_needing_update) != 0:
            print(
                f"\nPlease update {requirement_file}\n{'\n'.join(packages_needing_update)}"
            )
            is_fatal = True
    return is_fatal


def projects_needing_requirements_update():
    """
    We only check for requirements if we detect a pyproject.toml was changed.
    """
    changed_projects_and_pyproject_files = group_changes_by_project(
        is_relative=True, grep_filter="pyproject.toml"
    )
    changed_projects_and_project_versions = get_changed_project_versions_dict(
        changed_projects_and_pyproject_files=changed_projects_and_pyproject_files
    )
    changed_projects_and_requirements_files = group_requirements_files_by_project_name()

    is_fatal = False
    # Optimization: Figure this out ahead of time so it shows up as part of the task list
    for project_name in changed_projects_and_pyproject_files.keys():
        requirements_files = changed_projects_and_requirements_files.get(
            project_name, []
        )
        is_fatal = process_requirements_files_for_project(
            requirements_files=requirements_files,
            changed_projects_and_project_versions=changed_projects_and_project_versions,
            is_fatal=is_fatal,
        )
    if is_fatal:
        sys.exit(1)
    print("requirement.txt files reflect changes")


def is_package_required(package_name: str, requirements_file: str) -> bool:
    result = subprocess.run(
        ["grep", package_name, requirements_file],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def is_package_version_current(
    package_name: str, package_version: str, requirements_file: str
) -> bool:
    result = subprocess.run(
        ["grep", f"{package_name}>={package_version}", requirements_file],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def get_project_version_str(pyproject_file_path: str):
    result = subprocess.run(
        ["grep", "version =", pyproject_file_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Failed to get version from {pyproject_file_path}: {result.stderr}")
        sys.exit(1)
    # Parse the version from the output
    version_line = result.stdout.strip()
    if version_line:
        return version_line.split(" = ")[1].strip().strip('"')
    print(f"Failed to get version from {pyproject_file_path}: {result.stderr}")
    sys.exit(1)


def get_package_name_from_project(project_name: str):
    if project_name == SDKProject.CORE:
        return SDKPackage.CORE
    elif project_name == SDKProject.LANGCHAIN:
        return SDKPackage.LANGCHAIN
    elif project_name == SDKProject.MCP:
        return SDKPackage.MCP
    raise ValueError(f"Unknown project name: {project_name}")


if __name__ == "__main__":
    verify_changes()
