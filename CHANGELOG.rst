# Unreleased

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
    * Changed XBlock Aside encoding to escape all occurances of ':' and '$',
      and to raise an error when attempting to decode a string that hadn't been
      properly encoded (for instance, one with an odd number of '$' characters).

  Newly invalid keys can be found in the tracking logs by using the following
  regular expressions (in unicode-aware mode):

    grep -E "/c4x/[^/]+/[^/]+/[^/]+/[^@]+(@[^/]+)?/"  # AssetLocators
    grep --ignore-case "version@" | grep -v "version"  # Mixed case 'version'
    grep --ignore-case "branch@" | grep -v "branch"  # Mixed case 'branch'
    grep --ignore-case "[ic]4x" | grep -v "[ic]4x"  # Mixed case 'i4x' and 'c4x'
    grep -E "%20|\\n|\\\\n"  # Encoded newlines
    grep -P "i4x:/[^/]|(?<!/)c4x"  # Missing '/' characters
    grep "/?i4x/"  # Invalid form of i4x://
    grep -P '(?<![/\'"])i4x://'  #  i4x:// misspellings
    grep "aside-(usage|def)"  # Aside encodings changed


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
