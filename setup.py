#!/usr/bin/env python
"""
Package metadata for edx-opaque-keys.
"""
import os
import re

from setuptools import find_packages, setup


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.

    Requirements will include any constraints from files specified
    with -c in the requirements files.
    Returns a list of requirement strings.
    """
    # UPDATED VIA SEMGREP - if you need to remove/modify this method remove this line and add a comment specifying why.

    # e.g. {"django": "Django", "confluent-kafka": "confluent_kafka[avro]"}
    by_canonical_name = {}

    def check_name_consistent(package):
        """
        Raise exception if package is named different ways.

        This ensures that packages are named consistently so we can match
        constraints to packages. It also ensures that if we require a package
        with extras we don't constrain it without mentioning the extras (since
        that too would interfere with matching constraints.)
        """
        canonical = package.lower().replace('_', '-').split('[')[0]
        seen_spelling = by_canonical_name.get(canonical)
        if seen_spelling is None:
            by_canonical_name[canonical] = package
        elif seen_spelling != package:
            raise Exception(
                f'Encountered both "{seen_spelling}" and "{package}" in requirements '
                'and constraints files; please use just one or the other.'
            )

    requirements = {}
    constraint_files = set()

    # groups "pkg<=x.y.z,..." into ("pkg", "<=x.y.z,...")
    re_package_name_base_chars = r"a-zA-Z0-9\-_."  # chars allowed in base package name
    # Two groups: name[maybe,extras], and optionally a constraint
    requirement_line_regex = re.compile(
        r"([%s]+(?:\[[%s,\s]+\])?)([<>=][^#\s]+)?"
        % (re_package_name_base_chars, re_package_name_base_chars)
    )

    def add_version_constraint_or_raise(current_line, current_requirements, add_if_not_present):
        regex_match = requirement_line_regex.match(current_line)
        if regex_match:
            package = regex_match.group(1)
            version_constraints = regex_match.group(2)
            check_name_consistent(package)
            existing_version_constraints = current_requirements.get(package, None)
            # It's fine to add constraints to an unconstrained package,
            # but raise an error if there are already constraints in place.
            if existing_version_constraints and existing_version_constraints != version_constraints:
                raise BaseException(f'Multiple constraint definitions found for {package}:'
                                    f' "{existing_version_constraints}" and "{version_constraints}".'
                                    f'Combine constraints into one location with {package}'
                                    f'{existing_version_constraints},{version_constraints}.')
            if add_if_not_present or package in current_requirements:
                current_requirements[package] = version_constraints

    # Read requirements from .in files and store the path to any
    # constraint files that are pulled in.
    for path in requirements_paths:
        with open(path) as reqs:
            for line in reqs:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, True)
                if line and line.startswith('-c') and not line.startswith('-c http'):
                    constraint_files.add(os.path.dirname(path) + '/' + line.split('#')[0].replace('-c', '').strip())

    # process constraint files: add constraints to existing requirements
    for constraint_file in constraint_files:
        with open(constraint_file) as reader:
            for line in reader:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, False)

    # process back into list of pkg><=constraints strings
    constrained_requirements = [f'{pkg}{version or ""}' for (pkg, version) in sorted(requirements.items())]
    return constrained_requirements


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.

    Returns:
        bool: True if the line is not blank, a comment,
        a URL, or an included file
    """
    # UPDATED VIA SEMGREP - if you need to remove/modify this method remove this line and add a comment specifying why

    return line and line.strip() and not line.startswith(('-r', '#', '-e', 'git+', '-c'))


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    with open(filename, encoding='utf-8') as opened_file:
        version_file = opened_file.read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


VERSION = get_version("opaque_keys", "__init__.py")


setup(
    name='edx-opaque-keys',
    version=VERSION,
    author='edX',
    url='https://github.com/openedx/opaque-keys',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
    ],
    # We are including the tests because other libraries do use mixins from them.
    packages=find_packages(),
    include_package_data=True,
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
