"""A nonempty mapping: decimal scores upsert, null clears a draft score."""

import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import Field

ScoreValue = Annotated[Decimal, Field(ge=0, max_digits=6, decimal_places=2)]
ScorePayload = Annotated[dict[uuid.UUID, ScoreValue | None], Field(min_length=1)]
