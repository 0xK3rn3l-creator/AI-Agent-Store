from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import auth, store
from api.seed import seed_admin_user
from api.graphql_schema import schema
from strawberry.fastapi import GraphQLRouter

# Lifespan замінює застарілий @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаємо сідер при старті
    seed_admin_user()
    yield

app = FastAPI(title="AI-Native CRM API", lifespan=lifespan)

# REST ендпоінти
app.include_router(auth.router)
app.include_router(store.router)

# GraphQL ендпоінт
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
