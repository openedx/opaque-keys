from setuptools import setup

setup(
    name="opaque_keys",
    version="0.1.1",
    packages=[
        "opaque_keys",
        "opaque_keys.edx",
    ],
    install_requires=[
        "stevedore"
    ],
    entry_points={
        'opaque_keys.testing': [
            'base10 = opaque_keys.tests.test_opaque_keys:Base10Key',
            'hex = opaque_keys.tests.test_opaque_keys:HexKey',
            'dict = opaque_keys.tests.test_opaque_keys:DictKey',
        ],
        'course_key': [
            'course-locator = opaque_keys.edx.locator:CourseLocator',
        ],
        'usage_key': [
            'edx = opaque_keys.edx.locator:BlockUsageLocator',
        ],
        'asset_key': [
            'asset-location = opaque_keys.edx.locator:AssetLocator',
        ],
        'definition_key': [
            'defx = opaque_keys.edx.locator:DefinitionLocator',
        ],
    }

)
