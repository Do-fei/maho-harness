# Electron guidance

- Validate main, preload, renderer, and IPC boundaries independently when affected.
- Build/typecheck success does not prove application or packaged launch.
- Treat context isolation, exposed APIs, signing, and update paths as security/release boundaries.
- GUI and packaging probes require explicit task authority and applicable platform tooling.
