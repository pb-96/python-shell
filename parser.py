from typing import Generator, Iterator

valid_commands = {"echo", "exit", "type", "pwd"}


def tokenize(line: str) -> Generator:
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
                if to_yield and to_yield not in valid_commands:
                    yield to_yield
                    yield " "
                token = []
            case "\\":
                token.append(next(chs))
            case ch:
                token.append(ch)
    yield "".join(token)


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


def parse_command(input_line: str):
    return list(tokenize(input_line))
