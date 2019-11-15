from setuptools import setup, find_packages

setup(
    name='edx-opaque-keys',
    version='2.0.1',
    author='edX',
    url='https://github.com/edx/opaque-keys',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    # We are including the tests because other libraries do use mixins from them.
    packages=find_packages(),
    license='AGPL-3.0',
    install_requires=[
        'six>=1.10.0,<2.0.0',
        'stevedore>=0.14.1,<2.0.0',
        'pymongo>=2.7.2,<4.0.0'
    ],
    extras_require={
        'django': ['Django>=1.11,<2.0;python_version<"3"', 'Django>=1.11;python_version>"3"']
    },
    entry_points={
        'opaque_keys.testing': [
            'base10 = opaque_keys.tests.test_opaque_keys:Base10Key',
            'hex = opaque_keys.tests.test_opaque_keys:HexKey',
            'dict = opaque_keys.tests.test_opaque_keys:DictKey',
        ],
        'context_key': [
            'course-v1 = opaque_keys.edx.locator:CourseLocator',
            'library-v1 = opaque_keys.edx.locator:LibraryLocator',
            'lib = opaque_keys.edx.locator:LibraryLocatorV2',
            # don't use slashes in any new code
            'slashes = opaque_keys.edx.locator:CourseLocator',
        ],
        'usage_key': [
            'block-v1 = opaque_keys.edx.locator:BlockUsageLocator',
            'lib-block-v1 = opaque_keys.edx.locator:LibraryUsageLocator',
            'lb = opaque_keys.edx.locator:LibraryUsageLocatorV2',
            'location = opaque_keys.edx.locations:DeprecatedLocation',
            'aside-usage-v1 = opaque_keys.edx.asides:AsideUsageKeyV1',
            'aside-usage-v2 = opaque_keys.edx.asides:AsideUsageKeyV2',
        ],
        'asset_key': [
            'asset-v1 = opaque_keys.edx.locator:AssetLocator',
        ],
        'definition_key': [
            'def-v1 = opaque_keys.edx.locator:DefinitionLocator',
            'aside-def-v1 = opaque_keys.edx.asides:AsideDefinitionKeyV1',
            'aside-def-v2 = opaque_keys.edx.asides:AsideDefinitionKeyV2',
            'bundle-olx = opaque_keys.edx.locator:BundleDefinitionLocator',
        ],
        'block_type': [
            'block-type-v1 = opaque_keys.edx.block_types:BlockTypeKeyV1',
        ]
    }
)
