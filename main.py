import sys
from typing import List, Generator, Any, Union, Tuple, Callable, Sequence
from pathlib import Path
import os
import subprocess

valid_commands = ["echo", "exit", "type", "pwd"]


def is_valid_command(command: str) -> bool:
    return command in valid_commands


def parse_input(command: str) -> Tuple[str, str]:
    head, *tail = command.split()
    return head, tail


def get_first_in_list(args: Sequence[str]) -> Union[str, None]:
    return next(iter(args), None)


def scan_dirs(
    paths: List[Path],
    target_file: str,
    predicate: Union[Callable[[Path], bool], None] = None,
) -> Union[Path, None]:
    target_file = target_file.strip()
    if predicate is None:
        predicate: Callable[[Path], bool] = (
            lambda f: f.exists() and f.name == target_file
        )

    found_exe = (f for path in paths for f in path.iterdir() if predicate(f) )
    return get_first_in_list(found_exe)

def mk_path_on_init(raw_path_str: str) -> Generator[Path, Any, None]:
    paths = raw_path_str.split(":")
    for _path in paths:
        as_path = Path(_path)
        if not as_path.exists():
            as_path.mkdir(exist_ok=True)
        yield as_path


def execute_and_find(command: str, paths: List[Path]) -> None:
    my_exe, name = parse_input(command)
    name = get_first_in_list(name)
    to_call: Path = scan_dirs(paths, my_exe)
    if to_call is None:
        return

    result = subprocess.run([to_call, name], capture_output=True, text=True).stdout
    sys.stdout.write(f"{result}")


def get_type(command: str, paths: List[Path]):
    _, _type = parse_input(command)
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
    _, command = parse_input(command)
    as_str = " ".join(command)
    sys.stdout.write(f"{as_str}\n")


def main():
    # Uncomment this block to pass the first stage
    if len(sys.argv) > 1:
        # for local testing
        _, PATH, *_ = sys.argv
        _, *path = PATH.split("=")
        PATH = path[1:]
    else:
        PATH = os.environ.get("PATH")

    paths = list(mk_path_on_init(PATH))

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        # Wait for user input
        command: str = input()
        if command.startswith("my_exe"):
            execute_and_find(command, paths)
        elif command.startswith("type"):
            get_type(command, paths)
        elif command.startswith("exit"):
            break
        elif command.startswith("echo"):
            echo(command)
        elif command.startswith("pwd"):
            sys.stdout.write(f"{str(Path.cwd())}\n")
        elif command.startswith("cd"):
            move_dir(command)
        else:
            sys.stdout.write(f"{command}: command not found\n")


if __name__ == "__main__":
    main()
