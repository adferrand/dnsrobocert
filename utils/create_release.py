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
        raise RuntimeError("Error, git workspace is not clean: \n{0}".format(git_clean))

    current_version = subprocess.check_output(
        "uvx --from=toml-cli toml get --toml-path=pyproject.toml project.version",
        shell=True,
        universal_newlines=True,
    )

    print("Current version is: {0}".format(current_version))
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

        today = datetime.datetime.today()
        changelog = changelog.replace(
            "## master - CURRENT\n",
            """\
## master - CURRENT

## {0} - {1}
""".format(
                new_version, today.strftime("%d/%m/%Y")
            ),
        )

        with open("CHANGELOG.md", "w") as f:
            f.write(changelog)

        subprocess.check_call(
            "uvx --from=toml-cli toml set --toml-path=pyproject.toml project.version {0}".format(
                new_version
            ),
            shell=True,
        )
        subprocess.check_call("uv run isort src test utils", shell=True)
        subprocess.check_call("uv run black src test utils", shell=True)

        subprocess.check_call(
            'git commit -a -m "Version {0}"'.format(new_version), shell=True
        )
        subprocess.check_call("git tag v{0}".format(new_version), shell=True)
        subprocess.check_call("git push --tags", shell=True)
        subprocess.check_call("git push", shell=True)

    except subprocess.CalledProcessError as e:
        print("Error detected, cleaning state.")
        subprocess.call("git tag -d v{0}".format(new_version), shell=True)
        subprocess.check_call("git reset --hard", shell=True)
        raise e


if __name__ == "__main__":
    main()
