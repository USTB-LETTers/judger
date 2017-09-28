# -*- coding: utf-8 -*-
class CrazyBoxError(Exception):
    """
    The base class for custom exceptions raised by crazybox.
    """
    pass


class DockerError(Exception):
    """
    An error occurred with the underlying docker system.
    """
    pass


class NoAcceptError(Exception):
    """
    Base error for compile error, wrong answer
    """


class CompileError(NoAcceptError):
    """
    An error for judge process.
    """
    def __str__(self):
        return 'Compile Error'


class WrongAnswer(NoAcceptError):
    """

    """
