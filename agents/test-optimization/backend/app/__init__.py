"""
ATE Test Optimization Recommendation Agent — Backend

Clean Architecture / SOLID layout:

  app/
    api/            FastAPI routers (async)
    core/           config, logging, DI
    domain/         entities & Pydantic schemas
    infrastructure/ LLM, repositories, persistence
    prompts/        system & user prompts
    services/       application services
  tests/
"""

__version__ = "3.0.0"
