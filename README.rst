Part of `edX code`_.

.. _`edX code`: http://code.edx.org/

edx-opaque-keys  |build-status| |coverage-status|
=================================================

Opaque-keys provides the ability to create and introspect course and xblock identities through a
clear and consistent API. See the code's docstrings for more information.

See the `edx-platform wiki documentation`_ for more detail.

CCX keys
--------

This package also provides ``ccx_keys``, the Opaque Key implementations specific to Custom Courses
for edX (CCX). ``ccx_keys`` used to be distributed separately as ``edx-ccx-keys``. Its import paths
(``ccx_keys.key`` and ``ccx_keys.locator``) and its ``ccx-v1`` and ``ccx-block-v1`` key namespaces
are unchanged.

If you depend on ``edx-ccx-keys``, remove it from your requirements and depend on
``edx-opaque-keys>=5`` instead. ``edx-ccx-keys>=3`` is an empty package that depends on
``edx-opaque-keys``, so leaving it in your requirements is harmless.

Both ``edx-ccx-keys<3`` and ``edx-opaque-keys>=5`` install the ``ccx_keys`` module. Uninstalling or
upgrading ``edx-ccx-keys<3`` in an existing environment therefore deletes the copy of ``ccx_keys``
that ``edx-opaque-keys`` provides. If you see ``ModuleNotFoundError: No module named 'ccx_keys'``
after upgrading, rebuild the environment or run::

    pip install --force-reinstall --no-deps edx-opaque-keys

.. |build-status| image:: https://github.com/openedx/opaque-keys/workflows/Python%20CI/badge.svg?branch=master
   :target: https://github.com/openedx/opaque-keys/actions?query=workflow%3A%22Python+CI%22
.. |coverage-status| image:: https://codecov.io/github/openedx/opaque-keys/coverage.svg?branch=master
   :target: https://codecov.io/github/openedx/opaque-keys?branch=master
.. _`edx-platform wiki documentation`: https://github.com/openedx/edx-platform/wiki/Opaque-Keys-(Locators)
