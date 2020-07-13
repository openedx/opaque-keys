#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package metadata for edx-opaque-keys.
"""
from io import open

from setuptools import setup, find_packages

def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.

    Returns:
        list: Requirements file relative path strings
    """
    requirements = set()
    for path in requirements_paths:
        with open(path) as reqs:
            requirements.update(
                line.split('#')[0].strip() for line in reqs
                if is_requirement(line.strip())
            )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.

    Returns:
        bool: True if the line is not blank, a comment, a URL, or an included file
    """
    return line and not line.startswith(('-r', '#', '-e', 'git+', '-c'))

setup(
    name='edx-opaque-keys',
    version='2.1.1',
    author='edX',
    url='https://github.com/edx/opaque-keys',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8",
    ],
    # We are including the tests because other libraries do use mixins from them.
    packages=find_packages(),
    license='AGPL-3.0',
    install_requires=load_requirements('requirements/base.in'),
    extras_require={
        'django': load_requirements('requirements/django.in')
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
