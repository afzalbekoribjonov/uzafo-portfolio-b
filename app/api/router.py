from fastapi import APIRouter

from app.api.routes import auth, discussions, media, posts, profile, projects, resume, site, sync, users

api_router = APIRouter()
api_router.include_router(auth.router, tags=['auth'])
api_router.include_router(site.router, tags=['site'])
api_router.include_router(profile.router, tags=['profile'])
api_router.include_router(resume.router, tags=['resume'])
api_router.include_router(projects.router, tags=['projects'])
api_router.include_router(posts.router, tags=['posts'])
api_router.include_router(discussions.router, tags=['discussions'])
api_router.include_router(media.router, tags=['media'])
api_router.include_router(users.router, tags=['users'])

api_router.include_router(sync.router, tags=['sync'])
