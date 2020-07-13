# 2.0.2

* Fixed django warnings

# 2.0.2

* setup.py now properly uses requirements files

# 2.0.1

* Declare support for Python 3.5 and Django 2.2

# 2.0

* Added LibraryLocatorV2 and LibraryUsageLocatorV2
* Added LearningContextKey, UsageKeyV2, and BundleDefinitionLocator
* Added the .is_course helper method

# 1.0.1

* Included test code in the PyPI package so its mixins can be imported into
  other code

# 1.0.0

* Remove to_deprecated_string and from_deprecated_string API methods
* Support OpaqueKeyField lookups by string
* Support more recent versions of the hypothesis Python module
* Support Python 3.6 instead of 3.5

# 0.4.4

* Remove pytest-django as a dependency of the optional Django support; it's
  only needed for testing, not normal usage

# 0.4.3

* Remove the accidentally included "settings" package from the distribution

# 0.4.2

* Added OpaqueKeyField and its subclasses, extracted from edx-platform
* Added the "django" installation option to indicate the optional dependency
  on the Django package

# 0.4.1

* Stop an assortment of deprecation warnings by replacing internal usage of
  deprecated properties.
* Trailing '/' characters are no longer valid in serialized usage keys.

# 0.4

* Enforce the property that serialized keys are equal if and only if the parsed
  keys are equal. In particular:
    * OpaqueKey parsing is now case-sensitive
    * Newlines aren't allowed at the end of any keys
    * AssetLocators are correctly terminated by their final non-matching character
      For example, '/c4x/-/-/-/-@0/c4x' no longer parses to the same key as
      '/c4x/-/-/-/-@0'
    * Stricter requirements for '/' characters in AssetLocators and deprecated
      BlockUsageLocators. For instance, 'i4x:/...' and 'c4x/...' are no longer
      valid.
    * Removed the '/i4x/...' form of deprecated usage keys.
    * Fixed improper parsing where misspellings like '0i4x://...' were accepted.
    * Added a new version of XBlock Aside keys that encodes all occurances of ':' and '$',
      and changed the old version to raise an error when a key would have an
      ambiguous encoding.

  Newly invalid keys can be found in the tracking logs by using the following
  regular expressions (in unicode-aware mode):

    grep -E '/c4x/[^/"]+/[^/"]+/[^/"]+/[^@"]+(@[^/"]+)?/' tracking.log  # unterminated AssetLocators
    grep --ignore-case "version@" tracking.log | grep -v "version"  # Mixed case 'version'
    grep --ignore-case "branch@" tracking.log | grep -v "branch"  # Mixed case 'branch'
    grep --ignore-case "[ic]4x:;_;_" tracking.log | grep -v "[ic]4x:;_;_"  # Mixed case 'i4x' and 'c4x'
    grep --ignore-case "[ic]4x:%2F%2F" tracking.log | grep -v "[ic]4x:%2F%2F"  # Mixed case 'i4x' and 'c4x'
    grep --ignore-case "[ic]4x://" tracking.log | grep -v "[ic]4x://"  # Mixed case 'i4x' and 'c4x'
    grep --ignore-case "(;_)?[ic]4x(;_)" tracking.log | grep -v "(;_)?[ic]4x(;_)"  # Mixed case 'i4x' and 'c4x'
    grep --ignore-case "(%2F)?[ic]4x(%2F)" tracking.log | grep -v "(%2F)?[ic]4x(%2F)"  # Mixed case 'i4x' and 'c4x'
    grep --ignore-case "/?[ic]4x/" tracking.log | grep -v "/?[ic]4x/"  # Mixed case 'i4x' and 'c4x'
    grep -E '"event_type": "[^"]*(%0A|%0D|\\n|\\r)' tracking.log  # Encoded newlines
    grep -P 'i4x:;_(?!;_)|(?<!;_)c4x' tracking.log  # Missing encoded '/' characters
    grep -P 'i4x:%2F(?!%2F)|(?<!%2F)c4x' tracking.log  # Missing encoded '/' characters
    grep -P 'i4x:/[^/]|(?<!/)c4x' tracking.log  # Missing '/' characters
    grep '(;_)?i4x;_' tracking.log  # Invalid form of i4x://
    grep ';_?i4x;_' tracking.log  # Invalid form of i4x://
    grep '%2F?i4x%2F' tracking.log  # Invalid form of i4x://
    grep '/?i4x/' tracking.log  # Invalid form of i4x://
    grep -P '\wi4x:;_' tracking.log  #  i4x:// misspellings
    grep -P '\wi4x:%2F' tracking.log  #  i4x:// misspellings
    grep -P '\wi4x:/' tracking.log  #  i4x:// misspellings


# 0.3.4

* Update the regular expression for a course key and locators which use course
  keys so that a string with a trailing newline will no longer be accepted as a
  valid key.

# 0.3.3

* Revert of caching optmizations introduced in 0.3.2, due to a bug that can
  occur where course keys can be parsed with trailing newlines, and those parsed
  values can be serialized into the database.

# 0.3.2

* Simple optimizations to reduce the number of OpaqueKey objects
  created, and to speed up hashing and equality checks.

-----

-No changelog was maintained before 0.3.2.
