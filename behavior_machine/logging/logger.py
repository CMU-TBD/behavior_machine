import sys
import typing

output_fs = {
    'stdout': sys.stdout
}


def print(text: str, flush: bool = True) -> None:
    text += '\n'
    for fs in output_fs.values():
        fs.write(text)
        if flush:
            fs.flush()


def add_fs(name: str, fs) -> bool:
    global output_fs
    if name in output_fs:
        return False
    else:
        output_fs[name] = fs


def remove_fs(name: str) -> None:
    """ Remove the file stream from the publishing list according to the name.
    KeyErrorException is raised if the name doesn't exist.

    Parameters
    ----------
    name : str
        Name of the file stream

    Raises
    ------
    KeyError
        If the name of the file stream wasn't added previously
    """
    global output_fs
    output_fs.pop(name)


def parse_debug_info(info: typing.Dict[str, typing.Any], spacing: int = 0, margin: int = 2, prefix: str = ""):

    ori_str = f'{prefix}{info["name"]}({info["type"]}) -- {info["status"].name}'
    str_list = [ori_str.rjust(len(ori_str) + spacing)]
    if 'children' in info:
        for child in info['children']:
            str_list += parse_debug_info(child,
                                         spacing + margin, margin, "-> ")
    return str_list
