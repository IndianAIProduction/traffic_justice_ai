from fastapi import APIRouter

from app.api.v1 import auth, legal, challan, evidence, complaints, cases, analytics

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(legal.router, prefix="/legal", tags=["Legal Intelligence"])
api_router.include_router(challan.router, prefix="/challan", tags=["Challan Validation"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
api_router.include_router(cases.router, prefix="/cases", tags=["Cases"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
