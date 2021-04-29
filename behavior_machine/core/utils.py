import typing


def parse_debug_info(info: typing.Dict[str, typing.Any], spacing: int = 0, margin: int = 2,
                     prefix: str = "") -> typing.List[str]:

    ori_str = f'{prefix}{info["name"]}({info["type"]}) -- {info["status"].name}'
    str_list = [ori_str.rjust(len(ori_str) + spacing)]
    if 'children' in info:
        for child in info['children']:
            str_list += parse_debug_info(child,
                                         spacing + margin, margin, "-> ")
    return str_list
