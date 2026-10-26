"""Academic dashboard endpoint.

Adapter HTTP ringkasan akademik yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryRead
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryRead)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "lecturer")),
) -> DashboardSummaryRead:
    """Sajikan ringkasan akademik sesuai role pengguna.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif; superadmin melihat cakupan lintas
            dosen.

    Returns:
        Hitungan, kelompok kelas, dan rilis terbaru sesuai cakupan
        pengguna.
    """
    return await dashboard_service.get_summary(db, current_user)
