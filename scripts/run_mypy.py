import subprocess
import sys


def main() -> int:
    """Run mypy for the whole project."""
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["uv", "run", "mypy", "."], capture_output=True, text=True
    )

    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
