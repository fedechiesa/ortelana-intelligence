# Contributing

Start with the README and architecture decision records. For a bug, open an issue with reproducible steps, expected/actual behavior and sanitized diagnostic details. Discuss substantial changes first; this portfolio favors a small, demonstrable scope.

Use Python 3.12 and Node 22, install from committed locks, and run the README's backend, frontend and Compose checks. Persistence, human authority or recovery changes should include a meaningful regression test against the dedicated PostgreSQL `_test` database. Check UI behavior in the connected application. State which service/browser checks you ran and which you did not.

Never contribute original academic datasets, teaching documents, private execution exports, credentials or personal information. Use independently authored synthetic fixtures. Keep arithmetic and policy decisions deterministic. Any proposed model integration must preserve evidence, missing-data semantics and authenticated human authority.

Pull requests should explain the concrete behavior change, its purpose and executed validation. Follow Ruff/Prettier and update operations documentation when configuration changes. Explain lockfile changes.

There is currently no project-wide open-source license. Public visibility allows portfolio review; it does not establish a blanket MIT grant. Submit only material you have the right to publish, identify its provenance, and discuss licensing with the maintainer before contributing substantial code. Dependencies retain their own licenses.
