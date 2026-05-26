from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.session import init_db

app = FastAPI(title='Pep.AI Backend')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router, prefix='/api')


@app.on_event('startup')
def on_startup():
    init_db()

@app.get('/')
def root():
    return {'message': 'Pep.AI backend is running'}
