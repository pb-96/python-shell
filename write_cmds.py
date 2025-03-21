from pathlib import Path
from typing import List, cast, Tuple
import sys
from .parser import parse_command
from re import Match, search


def cmd_index_range(command: str):
    find = {">", "<"}
    for char in find:
        idx = command.find(char)
        if idx >= 0:
            return idx - 1, idx + 1
    return (-1, -1)


def ls(dest: Path, rem: List[str], write_type: str):
    if not dest.exists():
        dest.touch(exist_ok=True)

    src = rem[-1]
    src = Path(src)

    if src.exists():
        content = "\n".join(sorted(p.stem for p in src.iterdir()))
        dest.write_text(content)
    elif write_type in {"2>", "2<"}:
        content = f"ls: {src.stem or src}: No such file or directory"
        dest.write_text(content)


def echo_write(dest: Path, rem: List[str], write_type: str):
    if dest.exists():
        content = "".join(rem)
        dest.write_text(content)
    elif write_type in {"2>", "2<", "<"}:
        dest.touch(exist_ok=True)
        sys.stderr.write("".join(rem) + "\n")
    elif write_type in {"1>", "1<", ">"}:
        if not dest.exists():
            dest.touch(exist_ok=True)
        with dest.open("a") as f:
            f.write("".join(rem) + "\n")


def cat_file(rem: List[str], dest: Path, write_type: str) -> None:
    to_parse = rem[0]
    p = Path(to_parse)
    t = p.read_text()
    if not dest.exists():
        if "1" in write_type and t:
            dest.touch(exist_ok=True)
            dest.write_text(t)
            t = "cat: nonexistent: No such file or directory\n"
        elif "2" in write_type:
            dest.touch(exist_ok=True)
            dest.write_text("cat: nonexistent: No such file or directory\n")
    if t:
        sys.stdout.write(t)
        sys.stdout.flush()


def process_write_cmd(command: str):
    before, after = cmd_index_range(command)
    to_parse, dest, write_type = (
        command[:before],
        command[after:],
        command[before:after],
    )
    write_type = write_type.strip()
    dest: Path = cast(Path, Path(dest.strip()))
    cmd, *rem = tuple(parse_command(to_parse, False))
    match cmd:
        case "ls":
            ls(dest, rem, write_type)
        case "echo":
            echo_write(dest, rem, write_type)
        case "cat":
            cat_file(rem, dest, write_type)


def append_ls(rem: List[str], write_type: str, dest: Path):
    from_path = Path(rem[-1])
    contents = None
    valid_write_type = write_type in {">>", "1>>", "2>>"}
    if valid_write_type and from_path.exists():
        contents = "".join(sorted(map(lambda p: p.stem + "\n", from_path.iterdir())))
    elif valid_write_type and not from_path.exists():
        dest.touch(exist_ok=True)
        if write_type == "2>>":
            contents = f"ls: {from_path.stem}: No such file or directory\n"
        else:
            sys.stdout.write(f"ls: {from_path.stem}: No such file or directory\n")
            sys.stdout.flush()
    else:
        contents = f"ls: {from_path.stem}: No such file or directory\n"
    if contents is not None:
        with dest.open("a") as f:
            f.write(contents)


def append_to_file(command: str) -> None:
    found: Match = search(r"\d*>>", command)
    span: Tuple[int, int] = found.span()
    left, right = command[: span[0]], command[span[1] + 1 :]
    write_type = command[span[0] : span[1]]

    dest = Path(right)
    if not dest.exists():
        dest.touch(exist_ok=True)

    cmd, *rem = tuple(parse_command(left, False))

    match cmd:
        case "ls":
            append_ls(rem, write_type, dest)
        case "cat":
            from_file = Path(rem[-1])
            if not from_file.exists():
                with dest.open("a") as f:
                    f.write(f"cat: {from_file.stem}: No such file or directory\n")
        case "echo":
            if write_type in {">>", "1>>"}:
                with dest.open("a") as f:
                    f.write("".join(rem) + "\n")
            elif write_type in {"2>>"}:
                sys.stdout.write(f"{''.join(rem)}\n")
                sys.stdout.flush()
