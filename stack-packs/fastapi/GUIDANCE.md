# FastAPI guidance

- Validate request/response schemas, status codes, and dependency boundaries.
- Treat authentication, authorization, CORS, and generated OpenAPI as explicit contracts when affected.
- Unit tests do not prove process startup or real HTTP routing.
- Do not start network services unless the task and environment permit it.
