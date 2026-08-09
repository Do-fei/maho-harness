# Node.js and TypeScript guidance

- Derive the package manager from the committed lockfile.
- Accept only scripts actually declared in `package.json`.
- Treat build/typecheck/test as different evidence; one does not imply the others.
- Do not install or update dependencies during discovery.
