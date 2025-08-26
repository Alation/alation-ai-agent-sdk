#!/usr/bin/env python
import os
import subprocess


class SDKProject:
    CORE = "core-sdk"
    LANGCHAIN = "dist-langchain"
    MCP = "dist-mcp"


sdk_project_dirs = [SDKProject.CORE, SDKProject.LANGCHAIN, SDKProject.MCP]


def verify_changes():
    
    ruff_check_all_projects()
    ruff_format_all_projects()

    projects_to_version_bump = projects_needing_version_bump()
    if len(projects_to_version_bump) != 0:
        print(
            "Please bump the version within pyproject.toml for the following projects:"
        )
        for project in projects_to_version_bump:
            print(f" - {project}")


def ruff_check_all_projects():
    for project in sdk_project_dirs:
        result = subprocess.run(
            f"ruff check --fix {project}",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Ruff check failed for {project}:")
            print(result.stdout)
            print(result.stderr)
        else:
            print(f"Ruff check passed for {project}.")

def ruff_format_all_projects():
    for project in sdk_project_dirs:
        result = subprocess.run(
            f"ruff format {project}",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Ruff format failed for {project}:")
            print(result.stdout)
            print(result.stderr)
        else:
            print(f"Ruff format passed for {project}.")


def get_current_working_dir():
    return os.getcwd()


def get_local_branch_name():
    return os.popen("git rev-parse --abbrev-ref HEAD").read().strip()


def get_files_changed_from_base():
    local_branch_name = get_local_branch_name()
    # NOTE: These paths are relative to the repo root and not the current working directory
    return (
        os.popen(
            f"git diff --no-color --name-only $(git merge-base main {local_branch_name}) ."
        )
        .read()
        .strip()
        .split("\n")
    )


def group_changes_by_project():
    files_changed = get_files_changed_from_base()
    changed_projects = {}
    for file_path in files_changed:
        for sdk_project_name in sdk_project_dirs:
            if sdk_project_name in file_path:
                changed_projects[sdk_project_name] = changed_projects.get(
                    sdk_project_name, []
                ) + [file_path]
                break
    return changed_projects


cmd_pipe_version_line_count_to_shell_exit_code = (
    "grep \"+version\" | wc -l | awk '{exit ($1 == 0)}'"
)


def is_pyproject_version_bump_needed(pyproject_file_path: str):
    local_branch_name = get_local_branch_name()
    result = subprocess.run(
        f"git diff --no-color --name-only $(git merge-base main {local_branch_name}) {pyproject_file_path} | {cmd_pipe_version_line_count_to_shell_exit_code}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.returncode != 0


monitored_file_suffixes = set([".py", "Dockerfile", "LICENSE"])


def projects_needing_version_bump():
    changed_projects = group_changes_by_project()
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
                if is_pyproject_version_bump_needed(pyproject_file_path=file_path):
                    projects_needing_version_bump.remove(project)
                break
    return projects_needing_version_bump


if __name__ == "__main__":
    verify_changes()
