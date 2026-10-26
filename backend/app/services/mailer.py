"""Mock logger or SMTP delivery of plain-text Indonesian grade emails.

Transport email nilai untuk service notifications, dengan mode mock
tanpa SMTP host.

Validasi alamat tetap berlaku pada kedua mode agar status pengiriman
tidak menutupi input rusak.
"""

import logging
import smtplib
import ssl
import uuid
from dataclasses import dataclass
from decimal import Decimal
from email.message import EmailMessage
from email.utils import parseaddr

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GradeEmail:
    """Payload immutable nilai final untuk transport email."""

    grade_id: uuid.UUID
    recipient: str | None
    full_name: str
    course_name: str
    section: str
    final_score: Decimal
    rank: int | None


def validate_address(value: str | None) -> str:
    """Tolak alamat kosong, display name, newline, atau invalid.

    Validasi format ini tidak memverifikasi keberadaan mailbox.

    Args:
        value: Alamat penerima/pengirim; None, newline, dan format
            invalid ditolak.

    Returns:
        Alamat yang telah dipangkas spasi luarnya dan lolos pemeriksaan
        format dasar.

    Raises:
        ValueError: jika invalid.
    """
    if not value or "\r" in value or "\n" in value:
        raise ValueError("Alamat email belum diisi atau tidak valid")
    value = value.strip()
    address = parseaddr(value)[1]
    if address != value or "@" not in address or "." not in address.split("@")[-1]:
        raise ValueError("Alamat email tidak valid")
    return address


def send_grade_email(data: GradeEmail) -> None:
    """Kirim email melalui SMTP atau catat pengiriman mode mock.

    Jaringan SMTP/log; ValueError alamat invalid, error SMTP/koneksi
    diteruskan.

    Args:
        data: Payload email yang dibentuk dari hasil nilai final.
    """
    recipient = validate_address(data.recipient)
    settings = get_settings()
    if not settings.smtp_host:
        logger.info("Mock notifikasi rilis nilai %s untuk %s", data.grade_id, recipient)
        return
    message = EmailMessage()
    message["From"] = validate_address(settings.smtp_from or settings.smtp_user)
    message["To"] = recipient
    message["Subject"] = "Nilai " + " ".join(data.course_name.splitlines()) + " telah dirilis"
    # Batas 45 juga digunakan laporan dan analytics untuk status kelulusan.
    message.set_content(
        f"Halo {data.full_name},\n\n"
        f"Nilai mata kuliah {data.course_name}, kelas {data.section}, telah dirilis.\n"
        f"Nilai akhir: {data.final_score}\nPeringkat kelas: {data.rank if data.rank is not None else '-'}\n"
        f"Status: {'Tidak lulus' if data.final_score < 45 else 'Lulus'}\n"
    )
    secure_context = ssl.create_default_context()
    if settings.smtp_security == "ssl":
        connection = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port,
                                      timeout=settings.smtp_timeout, context=secure_context)
    else:
        connection = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout)
    with connection as smtp:
        if settings.smtp_security == "starttls":
            smtp.starttls(context=secure_context)
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
