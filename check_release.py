"""从公开交付文件创建独立临时副本与新venv；不会复制真实个人状态。"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="test*.py")
    args = parser.parse_args()
    names = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
    ).decode().split("\0")
    names = [name for name in dict.fromkeys(names) if name]
    for name in names:
        if name.startswith(("data/private/", "docs/private/")) or name == "docs/learning-plan.md":
            raise RuntimeError("私人文件出现在交付清单：" + name)
    with tempfile.TemporaryDirectory(prefix="studydocs-release-") as folder:
        project = Path(folder) / "project"
        project.mkdir()
        for name in names:
            source = ROOT / name
            if source.is_file() and not source.is_symlink():
                target = project / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        environment = Path(folder) / "environment"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"],
                       cwd=project, check=True)
        subprocess.run([str(python), "-m", "unittest", "discover", "-s", "tests",
                        "-p", args.pattern, "-v"], cwd=project, check=True)
        smoke = subprocess.run(
            [str(python), "cli.py"], input="/熟悉库\n/退出\n",
            cwd=project, text=True, capture_output=True, check=True,
        )
        if "熟悉库为空" not in smoke.stdout:
            raise RuntimeError("新副本的空库启动未符合预期")
        print("PASS：公开文件副本、新venv、依赖安装、指定检查与CLI空库启动。")
        print("这是助手执行的环境复现，不是用户独立复现能力证明；未验证真实模型。")


if __name__ == "__main__":
    main()
