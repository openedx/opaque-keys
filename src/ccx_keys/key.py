""" Key module. """
from __future__ import annotations

from abc import abstractmethod

from opaque_keys.edx.keys import CourseKey


class CCXKey(CourseKey):
    """ Custom course key. """

    @property
    @abstractmethod
    def ccx(self) -> str:
        """The id of the ccx for this key"""
        raise NotImplementedError()
