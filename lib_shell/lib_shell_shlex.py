import re
from typing import List, Optional

import lib_parameter
import lib_platform

_re_cmd_lex_precompiled_win = re.compile(pattern=r'''"((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)''', flags=0)
_re_cmd_lex_precompiled_posix = re.compile(pattern=r'''"((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)''', flags=0)


def shlex_split_multi_platform(s_commandline: str, is_platform_windows: Optional[bool] = None) -> List[str]:
    """
    its ~10x faster than shlex, which does single-char stepping and streaming;
    and also respects pipe-related characters (unlike shlex).

    from : https://stackoverflow.com/questions/33560364/python-windows-parsing-command-lines-with-shlex

    >>> shlex_split_multi_platform('', is_platform_windows=True)     # acc = None
    []
    >>> shlex_split_multi_platform('c:/test.exe /n /r /s=test | test2.exe > test3.txt', is_platform_windows=True)
    ['c:/test.exe', '/n', '/r', '/s=test', '|', 'test2.exe', '>', 'test3.txt']
    >>> shlex_split_multi_platform('c:/test.exe /n /r /s=test | test2.exe > test3.txt', is_platform_windows=False)
    ['c:/test.exe', '/n', '/r', '/s=test', '|', 'test2.exe', '>', 'test3.txt']

    >>> shlex_split_multi_platform('c:/test.exe /n /r \\t \\e[0m /s=""test" ,', is_platform_windows=True)
    ['c:/test.exe', '/n', '/r', '\\\\e[0m', '/s=test ,']
    >>> shlex_split_multi_platform('c:/test.exe /n /r \\t \\e[0m /s=""test" ,',
    ...     is_platform_windows=False)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: invalid or incomplete shell string

    """
    is_platform_windows = lib_parameter.get_default_if_none(
        is_platform_windows, default=lib_platform.is_platform_windows)  # type: ignore

    if is_platform_windows:
        re_cmd_lex_precompiled = _re_cmd_lex_precompiled_win
    else:
        re_cmd_lex_precompiled = _re_cmd_lex_precompiled_posix

    args = []
    acc = None   # collects pieces of one arg
    for qs, qss, esc, pipe, word, white, fail in re_cmd_lex_precompiled.findall(s_commandline):
        if word:
            pass   # most frequent
        elif esc:
            word = esc[1]
        elif white or pipe:
            if acc is not None:
                args.append(acc)
            if pipe:
                args.append(pipe)
            acc = None
            continue
        elif fail:
            raise ValueError("invalid or incomplete shell string")
        elif qs:
            word = qs.replace('\\"', '"').replace('\\\\', '\\')
            if lib_platform.is_platform_windows:
                word = word.replace('""', '"')
        else:
            word = qss   # may be even empty; must be last

        acc = (acc or '') + word

    if acc is not None:
        args.append(acc)

    return args
