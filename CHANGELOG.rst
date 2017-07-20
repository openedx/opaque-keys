# 0.4.1

* Re-introduce the caching optimizations of 0.3.2, but this time don't blindly
  assign the argument to OpaqueKey.from_string() to be the key's serialized
  representation. The OpaqueKey always serializes itself out to whatever its
  canonical form is. This should be redundant given the other precautions added
  since 0.3.2, but it's an extra layer of security.

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
