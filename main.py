import sys
from typing import List, Generator, Any, Union, Tuple, Sequence
from pathlib import Path
import os
import subprocess
import re
from .parser import parse_command

valid_commands = ["echo", "exit", "type", "pwd"]


def is_valid_command(command: str) -> bool:
    return command in valid_commands


def string_literal_present(command: str) -> bool:
    return bool(re.search(r"'[^']*'|\"[^\"]*\"", command))


def cat_file(command_line: str, path: str) -> str:
    file_contents = []
    files_by_line = parse_command(command_line)
    as_path = Path(path)
    _file: str

    for _file in files_by_line:
        full_path = as_path / _file.strip()
        if full_path.exists():
            contents = full_path.read_text()
            file_contents.append(contents)

    joined_content = "".join(file_contents)
    sys.stdout.write(joined_content)


def parse_input(command: str) -> Tuple[str, str]:
    head, *tail = parse_command(command)
    return head, tail


def get_first_in_list(args: Sequence[str]) -> Union[str, None]:
    return next(iter(args), None)


def default_predicate(target_file: str, f: Path) -> bool:
    return f.exists() and f.name == target_file


def scan_dirs(
    paths: List[Path],
    target_file: str,
) -> Union[Path, None]:
    target_file = target_file.strip()
    found_exe = (
        f for path in paths for f in path.iterdir() if default_predicate(target_file, f)
    )
    return get_first_in_list(found_exe)


def mk_path_on_init(raw_path_str: str) -> Generator[Path, Any, None]:
    paths = raw_path_str.split(":")
    for _path in paths:
        as_path = Path(_path)
        if not as_path.exists():
            as_path.mkdir(exist_ok=True)
        yield as_path


def execute_and_find(command: str, paths: List[Path]) -> bool:
    my_exe, args = parse_input(command)
    to_call: Path = scan_dirs(paths, my_exe)
    if to_call is None:
        return False
    else:
        args = [char for char in args if char not in {" ", ""}]
        programs_args = [to_call.stem]
        programs_args.extend(args)
        result = subprocess.run(programs_args, capture_output=True, text=True).stdout
        sys.stdout.write(f"{result}")
        return True


def get_type(command: str, paths: List[Path]):
    _type = parse_input(command)
    target_type = get_first_in_list(_type)
    valid_type = is_valid_command(target_type)

    if valid_type:
        sys.stdout.write(f"{target_type} is a shell builtin\n")
    elif (path := scan_dirs(paths, target_type)) and path is not None:
        sys.stdout.write(f"{target_type} is {path}\n")
    else:
        sys.stdout.write(f"{target_type}: not found\n")


def move_dir(command: str):
    _, target = tuple(command.split())
    try:
        os.chdir(os.path.expanduser(target))
    except OSError:
        print(f"cd: {target}: No such file or directory")


def echo(command: str):
    command = parse_command(command)
    command = "".join(command)
    sys.stdout.write(command + "\n")


def main():
    # This block is for testing
    if len(sys.argv) > 1:
        # for local testing
        _, PATH, *_ = sys.argv
        _, *path = PATH.split("=")
        PATH = path[1:]
    else:
        PATH = os.environ.get("PATH")

    paths = list(mk_path_on_init(PATH))

    while True:
        command: str = input()
        if command.startswith("type"):
            get_type(command, paths)
        elif command.startswith("exit"):
            break
        elif command.startswith("echo"):
            echo(command)
        elif command.startswith("pwd"):
            sys.stdout.write(f"{str(Path.cwd())}\n")
        elif command.startswith("cd"):
            move_dir(command)
        elif command.startswith("cat"):
            cat_file(command_line=command, path=PATH)
        else:
            found = execute_and_find(command, paths)
            if not found:
                sys.stdout.write(f"{command}: command not found\n")


if __name__ == "__main__":
    main()
