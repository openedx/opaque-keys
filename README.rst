Part of `edX code`_.

.. _`edX code`: http://code.edx.org/

opaque-keys  |build-status| |coverage-status|
=============================================

Opaque-keys is an API used by edx-platform to construct database keys.
"Opaque keys" are used where the application should be agnostic with
respect to key format, and uses an API to get information about the key
and to construct new keys.

See the `edx-platform wiki documentation`_ for more detail.

.. |build-status| image:: https://travis-ci.org/edx/opaque-keys.png  
   :target: https://travis-ci.org/edx/opaque-keys
.. |coverage-status| image:: https://coveralls.io/repos/edx/opaque-keys/badge.png
   :target: https://coveralls.io/r/edx/opaque-keys
.. _`edx-platform wiki documentation`: https://github.com/edx/edx-platform/wiki/Opaque-Keys
