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