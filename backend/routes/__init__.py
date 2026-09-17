"""Route modules for Extension IA API.
Extracted routes: folders, projects, workflows, oauth, profile
Remaining in server.py: auth, chat, admin, payments (to be extracted next)
"""
from .folders import folders_router
from .projects import projects_router
from .workflows import workflows_router
from .oauth import oauth_router
from .profile import profile_router

__all__ = [
    "folders_router", "projects_router", "workflows_router",
    "oauth_router", "profile_router",
]
