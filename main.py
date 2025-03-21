import sys
from typing import List, Generator, Any, Union, Tuple, Sequence, cast, Dict
from pathlib import Path
import os
import subprocess
import re
from .parser import parse_command
from .write_cmds import process_write_cmd, append_to_file
from .autocomplete import build_tree, search_tree, all_options
import readline
from functools import partial
from collections.abc import Mapping
import pathlib
from typing import Final, TextIO

SHELL_BUILTINS: Final[list[str]] = [
    "echo",
    "exit",
    "type",
    "pwd",
    "cd",
]

PATH = os.environ.get("PATH")


def parse_programs_in_path(path: str, programs: dict[str, pathlib.Path]) -> None:
    """Creates a mapping of programs in path to their paths"""
    for p, _, bins in pathlib.Path(path).walk():
        for b in bins:
            programs[b] = p / b


def generate_program_paths() -> Mapping[str, pathlib.Path]:
    programs: dict[str, pathlib.Path] = {}
    for p in (os.getenv("PATH") or "").split(":"):
        parse_programs_in_path(p, programs)
    return programs


PROGRAMS_IN_PATH: Final[Mapping[str, pathlib.Path]] = {**generate_program_paths()}
PATHS = [*PROGRAMS_IN_PATH.values()]
COMPLETIONS: Final[list[str]] = [*SHELL_BUILTINS, *PROGRAMS_IN_PATH.keys()]
TREE = build_tree(COMPLETIONS)


def display_matches(substitution, matches, longest_match_length):
    print()
    if matches:
        print("  ".join(matches))
    print("$ " + substitution, end="")


def complete(text: str, state: int) -> str | None:
    if state == 0:
        options = list(search_tree(TREE, text))
        if not options:
            return " ".join((found for found in COMPLETIONS if found.startswith(text)))
        return " ".join(options)
    return None


readline.set_completion_display_matches_hook(display_matches)
readline.parse_and_bind("tab: complete")
readline.set_completer(complete)


def is_valid_command(command: str) -> bool:
    return command in SHELL_BUILTINS


def string_literal_present(command: str) -> bool:
    return bool(re.search(r"'[^']*'|\"[^\"]*\"", command))


def cat_file(command_line: str, paths: List[Path]) -> str:
    file_contents = []
    files_by_line = parse_command(command_line, False)
    as_path = Path(get_first_in_list(paths))

    _file: str
    for _file in files_by_line:
        _file = _file.strip()
        _path: Path = cast(Path, Path(_file))
        if _file == "cat":
            continue
        elif _path.exists():
            contents = _path.read_text()
            file_contents.append(contents)
        elif (full_path := as_path / _path) and full_path.exists():
            contents = full_path.read_text()
            file_contents.append(contents)

    return "".join(file_contents)


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
    found_exe = [*filter(lambda p: default_predicate(target_file, p), paths)]
    return get_first_in_list(found_exe)


def execute_and_find(command: str, paths: List[Path]) -> Union[str, None]:
    my_exe, args = parse_input(command)
    to_call: Path = scan_dirs(paths, my_exe)
    if to_call is None:
        return None
    else:
        args = [char for char in args if char not in {" ", ""}]
        programs_args = [to_call.stem]
        programs_args.extend(args)
        result = subprocess.run(
            programs_args, capture_output=True, text=True
        ).stdout.strip()
        return result


def get_type(command: str, paths: List[Path]) -> str:
    _type = parse_input(command)
    target_type = get_first_in_list(_type)
    valid_type = is_valid_command(target_type)

    if valid_type:
        return f"{target_type} is a shell builtin\n"
    elif (path := scan_dirs(paths, target_type)) and path is not None:
        return f"{target_type} is {path}\n"
    else:
        return f"{target_type}: not found\n"


def move_dir(command: str):
    _, target = tuple(command.split())
    try:
        os.chdir(os.path.expanduser(target))
    except OSError:
        return f"cd: {target}: No such file or directory"


def echo(command: str) -> str:
    command = parse_command(command)
    command = "".join(command)
    return command + "\n"


def state_machine(command: str, paths: List[Path]) -> str:
    if command.startswith("type"):
        return get_type(command, paths)
    elif command.startswith("echo"):
        return echo(command)
    elif command.startswith("pwd"):
        return f"{str(Path.cwd())}\n"
    elif command.startswith("cd"):
        return move_dir(command)
    elif command.startswith("cat"):
        return cat_file(command_line=command, paths=paths)
    else:
        found = execute_and_find(command, paths)
        if found:
            return found
    return f"{command}: command not found\n"


def main():

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        command: str = input()
        if ">>" in command:
            append_to_file(command)
        elif ">" in command or "<" in command:
            process_write_cmd(command)
        elif command.startswith("exit"):
            break
        else:
            to_display = state_machine(command, paths=PATHS)
            if to_display is None:
                continue
            if not to_display.endswith("\n"):
                to_display += "\n"
            sys.stdout.write(to_display)
            sys.stdout.flush()


if __name__ == "__main__":
    main()
