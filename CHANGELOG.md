# CHANGELOG

<!-- version list -->

## v1.6.2 (2025-11-17)

### Bug Fixes

- Address PR #34 code review feedback
  ([`3ac25b5`](https://github.com/jrepp/docuchango/commit/3ac25b5edd76424f12f2629d27a9231f75df69da))


## v1.6.1 (2025-11-17)

### Bug Fixes

- Address CI lint failures
  ([`7fb89fb`](https://github.com/jrepp/docuchango/commit/7fb89fb4f42aeefaf323857205d86e7cc9960445))

- Address PR review feedback
  ([`755da5c`](https://github.com/jrepp/docuchango/commit/755da5cf9aeaad5113ed0b42c84bffd90cd18d43))

- Improve error messages for unclosed code fences (issue #31)
  ([`2ca205d`](https://github.com/jrepp/docuchango/commit/2ca205d93bd7b64a1ba09a8daa7d6c2af9fc9026))

### Code Style

- Apply ruff formatting
  ([`d6dc507`](https://github.com/jrepp/docuchango/commit/d6dc507903e39ddf129cc42d367eeed9ed4f3f7f))


## v1.6.0 (2025-11-16)

### Features

- Comprehensively enhance all document templates
  ([`dd7a71d`](https://github.com/jrepp/docuchango/commit/dd7a71d9bed5a98281e9cb71a9fc9e274897ccef))


## v1.5.0 (2025-11-16)

### Bug Fixes

- Address PR #33 code review comments
  ([`fe87734`](https://github.com/jrepp/docuchango/commit/fe8773490aff526b2d329e081e944229af66b829))

- Python 3.9/3.10 compatibility for ISO 8601 timestamps
  ([`9f2da99`](https://github.com/jrepp/docuchango/commit/9f2da990aff0e1511fded31f5d1dda4ff53544b8))

- Relax mypy type checking for CLI and test files
  ([`a5b3f78`](https://github.com/jrepp/docuchango/commit/a5b3f782de5eec697fbdcdd026eb5e7c8baf0475))

- Remove unused type: ignore comments from validator
  ([`0bbcbc8`](https://github.com/jrepp/docuchango/commit/0bbcbc8957ff4ed805ee0a2afbf072459a091b02))

- Resolve all xfail tests and enhance documentation
  ([`d940745`](https://github.com/jrepp/docuchango/commit/d940745748629a6b848f64c7686a7c2c8b05bd09))

- Resolve CI lint and test failures
  ([`f89cdb1`](https://github.com/jrepp/docuchango/commit/f89cdb138ec48dce9ff7d5bb9ac98efb6e4aef8c))

- Restore necessary type: ignore for error iteration
  ([`ccdc25d`](https://github.com/jrepp/docuchango/commit/ccdc25da20f50f6b7bdd159404182899881eb82c))

### Code Style

- Apply ruff formatting to fix CI lint failures
  ([`aff09a0`](https://github.com/jrepp/docuchango/commit/aff09a0667d32bfccca17e698bb5aa5f5cb1458d))

### Features

- Add 'fix list' command to show all available fixes
  ([`e78e9e9`](https://github.com/jrepp/docuchango/commit/e78e9e92e5228e8f8a844ccced22fdb6de1ce5f3))

- Add auto-fix for frontmatter issues (status, dates, missing fields)
  ([`18f2185`](https://github.com/jrepp/docuchango/commit/18f21859a08dbf9496da1ee10ed8b04cdd1df44b))

- Add high-probability frontmatter auto-fixes (tags, whitespace, required fields)
  ([`4cb7078`](https://github.com/jrepp/docuchango/commit/4cb7078e37454ba3e966333a787b0540ab7306ea))

- Add timestamp updates and bulk frontmatter operations
  ([`326eef1`](https://github.com/jrepp/docuchango/commit/326eef1c9dd6dcdc64537cb8f40f95b9aa83d70a))

- Enhance ADR template with comprehensive structure and guidance
  ([`34a8160`](https://github.com/jrepp/docuchango/commit/34a8160ef288207ac92fe47ba2a825960b1bf8c3))

### Refactoring

- Standardize on frontmatter-only properties in templates
  ([`4e2c614`](https://github.com/jrepp/docuchango/commit/4e2c614813f1fedccfa2c50647f53fa0bb0e356b))

### Testing

- Add comprehensive edge case tests for all fixes (122 tests)
  ([`9b08f6a`](https://github.com/jrepp/docuchango/commit/9b08f6a490421baae369f8d6db05e654e1082c9e))


## v1.4.0 (2025-11-16)

### Bug Fixes

- Address PR feedback and resolve CI failures
  ([`b4f2661`](https://github.com/jrepp/docuchango/commit/b4f2661eca1c7e2275dee22c389eabd98711081a))

- Remove type annotation to avoid circular import
  ([`44aafca`](https://github.com/jrepp/docuchango/commit/44aafca6fb907a9f0b1aa769ddba4c6e916809e1))

- Resolve mypy errors in test_validator_skips_without_textstat
  ([`4996469`](https://github.com/jrepp/docuchango/commit/499646980b68b8deb6c3b608ea1c936d4aad02a2))

- Resolve ruff lint errors in test files
  ([`d545274`](https://github.com/jrepp/docuchango/commit/d545274ed497da625d898ad800376e82cf1b4e32))

### Code Style

- Apply ruff formatting
  ([`b421195`](https://github.com/jrepp/docuchango/commit/b421195ce424f37dccfcd828b98b8e3f876fe339))

- Apply ruff formatting to test files
  ([`27d7e9a`](https://github.com/jrepp/docuchango/commit/27d7e9a7a1e8aa5f4fa3b8569976fed3787efda3))

### Documentation

- Add comprehensive readability feature documentation
  ([`b9956ba`](https://github.com/jrepp/docuchango/commit/b9956ba8e5225f70a7d32e184c9d2ba5fd537e7b))

### Features

- Add document readability scoring using textstat library
  ([`7b6d0cc`](https://github.com/jrepp/docuchango/commit/7b6d0ccb156b0df7b5ea8cd31155a221aea6c0f8))

- Add readability threshold configuration and validation tests
  ([`a58054d`](https://github.com/jrepp/docuchango/commit/a58054dde9e0324b2fe810415eb1f6f28a91bcea))

### Refactoring

- Address Copilot PR review feedback
  ([`cea9010`](https://github.com/jrepp/docuchango/commit/cea90100009f21e0a6c1568ed9a160fdcedf368a))

### Testing

- Add comprehensive readability feature tests
  ([`2110e73`](https://github.com/jrepp/docuchango/commit/2110e730a7a04a17c972cdeac937430119d18ab1))


## v1.3.6 (2025-11-06)

### Bug Fixes

- Resolve mypy unreachable code error in conftest.py
  ([`6bb57a9`](https://github.com/jrepp/docuchango/commit/6bb57a9dfb64997b19ae1bf26b11939fcda92101))

### Code Style

- Apply ruff formatting to test files
  ([`1629069`](https://github.com/jrepp/docuchango/commit/1629069ddd48f4c968d8b04a36f757d5847e5749))

### Refactoring

- Address code review feedback
  ([`fb131ea`](https://github.com/jrepp/docuchango/commit/fb131ea5fa65456dcdf06b058698176ce7c8b60f))

### Testing

- Improve test coverage from 49.53% to 60.78% (+116 tests)
  ([`a768fc1`](https://github.com/jrepp/docuchango/commit/a768fc187c87d34179ef4546f4f6fcfd70d3ca69))


## v1.3.5 (2025-11-06)

### Bug Fixes

- Resolve critical bugs with 100% failure rates
  ([`e0269a2`](https://github.com/jrepp/docuchango/commit/e0269a205ff2dd7d3336c080b798702eda124356))

- Resolve lint errors
  ([`fd88b99`](https://github.com/jrepp/docuchango/commit/fd88b992e4a16d6274e30dc324baf39aaa047a20))

### Refactoring

- Move yaml import to top of file
  ([`8821b39`](https://github.com/jrepp/docuchango/commit/8821b392558fa6f884ee735278cf4363c0809bf5))


## v1.3.4 (2025-11-06)

### Bug Fixes

- Resolve encoding, regex, and string replacement bugs
  ([`c0898a0`](https://github.com/jrepp/docuchango/commit/c0898a032a0ffba85bfaff5f72b216ec9d6357be))

- Resolve lint errors in tests
  ([`fd5e9ab`](https://github.com/jrepp/docuchango/commit/fd5e9abe8235b717f486d88f92a812f35cc3f2e9))

### Documentation

- Add comprehensive issues glossary to README
  ([`6763911`](https://github.com/jrepp/docuchango/commit/6763911e598922e0cfe4f61d32a240f8cc0b686f))

- Address code review feedback on glossary
  ([`083b873`](https://github.com/jrepp/docuchango/commit/083b8738521fce5bc6ba12ce7ff949cf7b5c36e2))

- Consolidate commands into Usage Examples section
  ([`f188bd0`](https://github.com/jrepp/docuchango/commit/f188bd0e7dd468a0c6c4e196e7e0d7eeb8480944))

- Improve Quick Start ordering and command descriptions
  ([`0718e28`](https://github.com/jrepp/docuchango/commit/0718e284aff95f4f1a13dd0eeb3ee5074faa5c56))

- Rename section to Document Schema (frontmatter)
  ([`05dfe3b`](https://github.com/jrepp/docuchango/commit/05dfe3bc7e5a850fb97ea9b06203e15c83e22d64))

- Update README with pip installation, PyPI badge, and detailed frontmatter schema
  ([`a4ab206`](https://github.com/jrepp/docuchango/commit/a4ab206c9d7e03e0f0ee2ee5f4bbe8db23d39f4c))

### Refactoring

- Address code review feedback
  ([`db93581`](https://github.com/jrepp/docuchango/commit/db935810b5b894d52d8bdcfa6bda0033dbc83f97))

### Testing

- Add comprehensive tests for bug fixes
  ([`1f70c21`](https://github.com/jrepp/docuchango/commit/1f70c21a7f46acdd0e297a0546591cc84eb583cf))


## v1.3.3 (2025-11-04)

### Bug Fixes

- Integrate --fix flag into validate command for automatic issue resolution
  ([`6dd68a4`](https://github.com/jrepp/docuchango/commit/6dd68a40a0e510d74fcb3fe82b61b6b4834e4a0b))

- Resolve lint issues
  ([`2ea8acf`](https://github.com/jrepp/docuchango/commit/2ea8acfd99c681f924e59027d4969cb6d90fbd0e))

### Code Style

- Apply ruff formatting to test_validate_fix_integration.py
  ([`b40204d`](https://github.com/jrepp/docuchango/commit/b40204d086142d08eafbdcad2e1a3bd932d6cf34))

### Refactoring

- Address code review feedback
  ([`aa1b88f`](https://github.com/jrepp/docuchango/commit/aa1b88f56d03eee44c4873ed1c5ea91c6dbf4061))


## v1.3.2 (2025-11-03)

### Bug Fixes

- Improve code quality and fix several issues
  ([`0f5da60`](https://github.com/jrepp/docuchango/commit/0f5da6043b7c169c32c083155aaa2ede65f3ff74))

### Refactoring

- Optimize dependencies and separate concerns properly
  ([`a3c667d`](https://github.com/jrepp/docuchango/commit/a3c667d160a8a79b0d20c0220c784ba3ca3d1515))

- Remove unused testing utilities and their dependencies
  ([`669c8bf`](https://github.com/jrepp/docuchango/commit/669c8bfdaa55ea0b0b0f948d55572fb814b52bb0))


## v1.3.1 (2025-10-30)

### Bug Fixes

- Auto-populate version from package metadata
  ([`322cd8b`](https://github.com/jrepp/docuchango/commit/322cd8be0b080084087a064c6cdd40167d42be86))


## v1.3.0 (2025-10-29)

### Bug Fixes

- Add type annotations to fix mypy errors
  ([`09ae633`](https://github.com/jrepp/docuchango/commit/09ae633e4007eff7210df22fa806cef9b1cf1fcd))

### Code Style

- Fix ruff formatting issues
  ([`40be174`](https://github.com/jrepp/docuchango/commit/40be174f57715072ce5fdc7b972777c7fed308b2))

- Fix ruff lint errors
  ([`41c2676`](https://github.com/jrepp/docuchango/commit/41c26765c90bc1b5f24b1b0dbdeb6576aaff26de))

### Features

- Add init command to scaffold docs-cms structure
  ([`37d7ba1`](https://github.com/jrepp/docuchango/commit/37d7ba1d75bdff6fc953cbafdfe40bebb9237ddc))

### Testing

- Add comprehensive test suite for init command
  ([`995f25c`](https://github.com/jrepp/docuchango/commit/995f25cbbe066964404324b46da1497c137d8e83))


## v1.2.0 (2025-10-29)

### Bug Fixes

- Address Copilot PR review feedback
  ([`6903dd0`](https://github.com/jrepp/docuchango/commit/6903dd00be26da232e238dfeb628663c1741a227))

### Features

- Add PRD document type and configurable folder scanning
  ([`d7e5b5e`](https://github.com/jrepp/docuchango/commit/d7e5b5e430401d6b2da87e628e93d5ab58efdb99))

### Testing

- Add comprehensive tests for DocsProjectConfig and PRD schemas
  ([`e56aec0`](https://github.com/jrepp/docuchango/commit/e56aec0a0ae5a71bf528a0087b668e019ec5bf71))


## v1.1.0 (2025-10-29)

### Features

- Add automatic PyPI publishing to release workflow
  ([`a16dcd9`](https://github.com/jrepp/docuchango/commit/a16dcd9ea8751621e534d2e3b48c78d915a3a8e2))


## v1.0.3 (2025-10-29)

### Bug Fixes

- Address code review feedback for safer changelog handling
  ([`539bb87`](https://github.com/jrepp/docuchango/commit/539bb873331769eb9c0f1a29495cc6c16fbaca39))

- Correct GitHub release creation in semantic-release workflow
  ([`2794d1e`](https://github.com/jrepp/docuchango/commit/2794d1ecd6c8528379a8dd2c0b9be57d2e4c31f8))


## v1.0.2 (2025-10-29)

### Bug Fixes

- Correct semantic-release build command for uv environment
  ([`552155a`](https://github.com/jrepp/docuchango/commit/552155a710367b8390f6d310a2a9ff17624be9c9))


## v1.0.1 (2025-10-29)

### Bug Fixes

- Correct GitHub release creation command in workflow
  ([`cc2e08c`](https://github.com/jrepp/docuchango/commit/cc2e08c216cccdc45c92d81dbb279b22a816002d))


## v1.0.0 (2025-10-29)

### Bug Fixes

- Address code review feedback
  ([`5eacc89`](https://github.com/jrepp/docuchango/commit/5eacc894ad9e46f6dd7894f14db3d1d161f03aec))

- Correct semantic-release command in workflow
  ([`c719290`](https://github.com/jrepp/docuchango/commit/c719290dd6b3f8fc18f26d7fb1d1ffdfb183de01))

- Use uv build command for semantic-release
  ([`75f9fd0`](https://github.com/jrepp/docuchango/commit/75f9fd0462322a5ecf71f5d294ae55620924dc3a))

### Documentation

- Add semantic release guidelines to agent instructions
  ([`021853b`](https://github.com/jrepp/docuchango/commit/021853b4265c0c2d65ee70a8d8b5bb4b97025ca8))

### Features

- Add python-semantic-release for automated versioning
  ([`3f7b2c3`](https://github.com/jrepp/docuchango/commit/3f7b2c3fd6f44e668b56ec8abd72194aad1ac82e))


## v0.1.2 (2025-10-27)


## v0.1.1 (2025-10-27)


## v0.1.0 (2025-10-27)

- Initial Release
