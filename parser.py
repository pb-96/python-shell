from typing import Generator, Iterator

valid_commands = {"echo", "exit", "type", "pwd"}


def tokenize(line: str, return_space: bool = True) -> Generator:
    chs = iter(line)
    token = []
    for ch in chs:
        match ch:
            case "'":
                token.append(_parse_quote("'", False, chs))
            case '"':
                token.append(_parse_quote('"', True, chs))
            case " ":
                to_yield = "".join(token)
                if not to_yield:
                    continue
                if to_yield not in valid_commands and return_space:
                    yield to_yield
                    yield " "
                elif not return_space:
                    yield to_yield
                token = []
            case "\\":
                token.append(next(chs))
            case ch:
                token.append(ch)

    token = "".join(token)
    if token:
        yield token


def _parse_quote(until: str, allow_escapes: bool, chs: Iterator) -> str:
    token = []
    for ch in chs:
        if ch == until:
            return "".join(token)
        if allow_escapes and ch == "\\":
            nch = next(chs)
            if nch not in ["\\", "$", '"']:
                token.append(ch)
            ch = nch
        token.append(ch)
    return "".join(token)


def parse_command(input_line: str, return_spaces: bool = True):
    return list(tokenize(input_line, return_spaces))
