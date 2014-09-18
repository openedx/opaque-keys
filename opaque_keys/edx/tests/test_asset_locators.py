"""
Tests of AssetLocators
"""
import ddt

from unittest import TestCase
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import AssetKey, CourseKey

from opaque_keys.edx.locator import AssetLocator, CourseLocator


@ddt.ddt
class TestAssetLocators(TestCase):
    """
    Tests of :class:`AssetLocator`
    """
    @ddt.data(
        "/c4x/org/course/asset/path",
    )
    def test_deprecated_round_trip_asset_location(self, path):
        self.assertEquals(
            path,
            unicode(AssetKey.from_string(path)),
        )

    def test_map_into_course_asset_location(self):
        original_course = CourseKey.from_string('org/course/run')
        new_course = CourseKey.from_string('edX/toy/2012_Fall')
        loc = AssetLocator(original_course, 'asset', 'foo.bar')
        self.assertEquals(
            AssetLocator(new_course, 'asset', 'foo.bar', deprecated=True),
            loc.map_into_course(new_course)
        )

    def test_make_asset_key(self):
        course = CourseKey.from_string('org/course/run')
        self.assertEquals(
            AssetLocator(course, 'asset', 'foo.bar', deprecated=True),
            course.make_asset_key('asset', 'foo.bar')
        )

    @ddt.data(
        (AssetLocator, '_id.', 'c4x', (CourseLocator('org', 'course', 'run', 'rev', deprecated=True), 'ct', 'n')),
        (AssetLocator, '_id.', 'c4x', (CourseLocator('org', 'course', 'run', 'rev', deprecated=True), 'ct', None)),
    )
    @ddt.unpack
    def test_deprecated_son(self, key_cls, prefix, tag, source):
        source_key = key_cls(*source, deprecated=True)
        son = source_key.to_deprecated_son(prefix=prefix, tag=tag)
        self.assertEquals(son.keys(), [prefix + key for key in ('tag', 'org', 'course', 'category', 'name', 'revision')])

        self.assertEquals(son[prefix + 'tag'], tag)
        self.assertEquals(son[prefix + 'category'], source_key.block_type)
        self.assertEquals(son[prefix + 'name'], source_key.block_id)

        self.assertEquals(son[prefix + 'org'], source_key.course_key.org)
        self.assertEquals(son[prefix + 'course'], source_key.course_key.course)
        self.assertEquals(son[prefix + 'revision'], source_key.course_key.branch)

    @ddt.data(
        (AssetKey.from_string('/c4x/o/c/ct/n'), 'run'),
        (AssetKey.from_string('/c4x/o/c/ct/n@v'), 'run'),
    )
    @ddt.unpack
    def test_roundtrip_deprecated_son(self, key, run):
        self.assertEquals(
            key.replace(course_key=key.course_key.replace(run=run)),
            key.__class__._from_deprecated_son(key.to_deprecated_son(), run)  # pylint: disable=protected-access
        )

    def test_old_charset(self):
        # merely not raising InvalidKeyError suffices
        AssetLocator(CourseLocator('a', 'b', 'c'), 'asset', 'subs_%20S2x5jhbWl_o.srt.sjson')
        AssetLocator(CourseLocator('a', 'b', 'c'), 'asset', 'subs_%20S2x5jhbWl_o.srt.sjson', deprecated=True)

    def test_replace(self):
        asset_key = AssetKey.from_string('/c4x/o/c/asset/path')
        self.assertEquals(
            'foo',
            asset_key.replace(path='foo').path
        )
        self.assertEquals(
            'bar',
            asset_key.replace(asset_type='bar').asset_type
        )

    def test_empty_path(self):
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string('course-v1:org+course+run').make_asset_key('asset', '')

        self.assertEquals(
            '/c4x/org/course/asset/',
            unicode(CourseKey.from_string('org/course/run').make_asset_key('asset', ''))
        )

    def test_version_agnostic_for_branch(self):
        course = CourseLocator(org='org', course='course', run='run', branch='branch', version_agnostic=True)
        asset = course.make_asset_key('type', 'id')
        new_asset = asset.for_branch('new_branch')

        self.assertIsInstance(new_asset, AssetLocator)
        self.assertEquals('branch', asset._branch)
        self.assertEquals('new_branch', new_asset._branch)
