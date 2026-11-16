""" Key module. """

from abc import abstractproperty

from opaque_keys.edx.keys import CourseKey


class CCXKey(CourseKey):
    """ Custom course key. """

    @abstractproperty  # pylint: disable=deprecated-decorator
    def ccx(self):
        """The id of the ccx for this key"""
        raise NotImplementedError()
