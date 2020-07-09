import pytest
from behavior_machine import logging
import sys


def test_logger_print(capsys):
    # add the local sys.stdout because that's the one capture by capsys
    logging.add_fs('capsys', sys.stdout)
    logging.print("hello world")
    assert capsys.readouterr().out == 'hello world\n'
    logging.remove_fs('capsys')
    logging.print("hello world again")
    assert capsys.readouterr().out == ''


def test_remove_none_exist_fs():
    with pytest.raises(KeyError):
        logging.remove_fs('capsys')


def test_parse_debug_info():

    from behavior_machine.library import SequentialState, IdleState, WaitState
    from behavior_machine.core import Machine

    s1 = IdleState('s1')
    exe = Machine('exe', s1)
    info = exe.get_debug_info()
    parse_str = logging.parse_debug_info(info)
    assert parse_str[0] == 'exe(Machine) -- UNKNOWN'
    assert parse_str[1] == '  -> s1(IdleState) -- UNKNOWN'
