""" Locator module. """
import re

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import (
    AssetLocator,
    BlockUsageLocator,
    CourseLocator,
)

from ccx_keys.key import CCXKey


class CCXLocator(CourseLocator, CCXKey):
    """Concrete implementation of an Opaque Key for CCX courses"""

    CANONICAL_NAMESPACE = 'ccx-v1'
    KEY_FIELDS = CourseLocator.KEY_FIELDS + ('ccx',)
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False
    CCX_PREFIX = 'ccx'
    deprecated = False

    # pep8 and pylint don't agree on the indentation in this block; let's make
    # pep8 happy and ignore pylint as that's easier to do.
    URL_RE_SOURCE = r"""
        ((?P<org>{ALLOWED_ID_CHARS}+)\+(?P<course>{ALLOWED_ID_CHARS}+)(\+(?P<run>{ALLOWED_ID_CHARS}+))?{SEP})??
        ({BRANCH_PREFIX}@(?P<branch>{ALLOWED_ID_CHARS}+){SEP})?
        ({VERSION_PREFIX}@(?P<version_guid>[A-F0-9]+){SEP})?
        ({CCX_PREFIX}@(?P<ccx>\d+){SEP})
        ({BLOCK_TYPE_PREFIX}@(?P<block_type>{ALLOWED_ID_CHARS}+){SEP})?
        ({BLOCK_PREFIX}@(?P<block_id>{ALLOWED_ID_CHARS}+))?
        """.format(
        ALLOWED_ID_CHARS=CourseLocator.ALLOWED_ID_CHARS,
        BRANCH_PREFIX=CourseLocator.BRANCH_PREFIX,
        VERSION_PREFIX=CourseLocator.VERSION_PREFIX,
        BLOCK_TYPE_PREFIX=CourseLocator.BLOCK_TYPE_PREFIX,
        BLOCK_PREFIX=CourseLocator.BLOCK_PREFIX,
        CCX_PREFIX=CCX_PREFIX,
        SEP=r'(\+(?=.)|\Z)',  # Separator: requires a non-trailing '+' or end of string
    )

    URL_RE = re.compile(
        '^' + URL_RE_SOURCE + r'\Z', re.IGNORECASE | re.VERBOSE | re.UNICODE
    )

    def __init__(self, **kwargs):
        """constructor for a ccx locator"""
        # for a ccx locator we require a ccx id to be passed.
        if 'ccx' not in kwargs:
            raise InvalidKeyError(self.__class__, "ccx must be set")

        if kwargs.get('deprecated', False):
            raise InvalidKeyError(self.__class__, "cannot be deprecated")

        super().__init__(**kwargs)

    @classmethod
    def from_course_locator(cls, course_locator, ccx):
        """Construct a CCXLocator given a CourseLocator and a ccx id"""
        new_obj = cls(
            org=course_locator.org,
            course=course_locator.course,
            run=course_locator.run,
            branch=course_locator.branch,
            version_guid=course_locator.version_guid,
            deprecated=course_locator.deprecated,
            ccx=ccx,
        )
        return new_obj

    def to_course_locator(self):
        """
        Returns a CourseLocator representing this location.
        """
        return CourseLocator(
            org=self.org,
            course=self.course,
            run=self.run,
            branch=self.branch,
            version_guid=self.version_guid
        )

    def _to_string(self):
        """
        Return a string representing this location.
        """
        string = super()._to_string()
        # append the identifier for the ccx to the existing course string
        string += f"+{self.CCX_PREFIX}@{self.ccx}"
        return string

    def _to_deprecated_string(self):
        """ CCXLocators are never deprecated. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """ CCXLocators are never deprecated. """
        raise NotImplementedError

    def make_usage_key(self, block_type, block_id):
        return CCXBlockUsageLocator(
            course_key=self,
            block_type=block_type,
            block_id=block_id,
            deprecated=False
        )

    def make_asset_key(self, asset_type, path):
        return AssetLocator(
            self.to_course_locator(),
            asset_type,
            path,
            deprecated=False
        )


class CCXBlockUsageLocator(BlockUsageLocator, UsageKey):
    """Concrete implementation of a usage key for blocks in CCXs"""

    CANONICAL_NAMESPACE = 'ccx-block-v1'

    URL_RE = re.compile(
        '^' + CCXLocator.URL_RE_SOURCE + r'\Z', re.IGNORECASE | re.VERBOSE | re.UNICODE
    )

    def replace(self, **kwargs):
        # BlockUsageLocator allows for the replacement of 'KEY_FIELDS' in 'self.course_key'.
        # This includes the deprecated 'KEY_FIELDS' of CourseLocator `'revision'` and `'version'`.
        course_key_kwargs = {}
        for key in CCXLocator.KEY_FIELDS:
            if key in kwargs:
                course_key_kwargs[key] = kwargs.pop(key)
        if course_key_kwargs:
            kwargs['course_key'] = self.course_key.replace(**course_key_kwargs)

        return super().replace(**kwargs)

    @classmethod
    def _from_string(cls, serialized):
        """
        Requests CCXLocator to deserialize its part and then adds the local
        deserialization of block
        """
        # Allow access to _from_string protected method
        course_key = CCXLocator._from_string(serialized)
        parsed_parts = cls.parse_url(serialized)
        block_id = parsed_parts.get('block_id', None)
        if block_id is None:
            raise InvalidKeyError(cls, serialized)
        return cls(course_key, parsed_parts.get('block_type'), block_id)

    @property
    def ccx(self):
        """Returns the ccx for this object's course_key."""
        return self.course_key.ccx

    def to_block_locator(self):
        """
        Returns a BlockUsageLocator for this location.
        """
        return BlockUsageLocator(
            course_key=self.course_key.to_course_locator(),
            block_type=self.block_type,
            block_id=self.block_id
        )

    def _to_deprecated_string(self):
        """ CCXBlockUsageLocators are never deprecated. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """ CCXBlockUsageLocators are never deprecated."""
        raise NotImplementedError
