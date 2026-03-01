Release history and notes
=========================

`Sequence based identifiers
<http://en.wikipedia.org/wiki/Software_versioning#Sequence-based_identifiers>`_
are used for versioning (schema follows below):

.. code-block:: text

    major.minor[.revision]

- It's always safe to upgrade within the same minor version (for example, from
  0.3 to 0.3.4).
- Minor version changes might be backwards incompatible. Read the
  release notes carefully before upgrading (for example, when upgrading from
  0.3.4 to 0.4).
- All backwards incompatible changes are mentioned in this document.

0.2.2
-----
2026-03-01

- Added named profiles (``[tool.sphinx-source-tree.file-options-profiles]``)
  allowing different inclusion rules per output file. Each
  ``[[tool.sphinx-source-tree.files]]`` entry can select a profile via
  ``file-options-profile``; unrecognised profile names fall back to the
  top-level ``file-options`` table with a stderr warning.

0.2.1
-----
2026-02-28

- Added per-file inclusion options: You can now limit which parts of a file
  are shown in the documentation using ``lines``, ``start-after``,
  ``start-at``, ``end-before``, and ``end-at``.
  These can be configured in your pyproject.toml or via the Python API.
- Test against Python 3.15.

0.2
---
2026-02-17

- Support multiple configurations.

0.1
---
2026-02-12

- Initial beta release.
