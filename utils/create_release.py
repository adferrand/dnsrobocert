#!/usr/bin/env python3
import datetime
import subprocess

from packaging import version


def main():
    git_clean = subprocess.check_output(
        "git status --porcelain",
        shell=True,
        universal_newlines=True,
    ).strip()
    if git_clean:
        raise RuntimeError(f"Error, git workspace is not clean: \n{git_clean}")

    current_version = subprocess.check_output(
        "uvx --from=toml-cli toml get --toml-path=pyproject.toml project.version",
        shell=True,
        universal_newlines=True,
    )

    print(f"Current version is: {current_version}")
    print("Please insert new version:")
    new_version = str(input())

    try:
        parsed_new_version = version.parse(new_version)
    except version.InvalidVersion:
        raise RuntimeError(f"Error, invalid version provided: {new_version}")

    if parsed_new_version <= version.parse(current_version):
        raise RuntimeError(
            f"Error new version is below current version: {new_version} < {current_version}"
        )

    try:
        with open("CHANGELOG.md") as f:
            changelog = f.read()

        today = datetime.datetime.now(datetime.UTC)
        changelog = changelog.replace(
            "## master - CURRENT\n",

            """\
## master - CURRENT

## {} - {}
""".format(new_version, today.strftime("%d/%m/%Y")),
        )

        with open("CHANGELOG.md", "w") as f:
            f.write(changelog)

        subprocess.check_call(
            f"uvx --from=toml-cli toml set --toml-path=pyproject.toml project.version {new_version}",
            shell=True,
        )
        subprocess.check_call("uv run isort src test utils", shell=True)
        subprocess.check_call("uv run black src test utils", shell=True)

        subprocess.check_call(
            f'git commit -a -m "Version {new_version}"', shell=True
        )
        subprocess.check_call(f"git tag v{new_version}", shell=True)
        subprocess.check_call("git push --tags", shell=True)
        subprocess.check_call("git push", shell=True)

    except subprocess.CalledProcessError:
        print("Error detected, cleaning state.")
        subprocess.call(f"git tag -d v{new_version}", shell=True)
        subprocess.check_call("git reset --hard", shell=True)
        raise


if __name__ == "__main__":
    main()
