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
