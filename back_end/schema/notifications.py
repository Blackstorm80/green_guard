from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    # Les noms d'API restent en anglais (contrat front) ; les colonnes sont en français
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    message: str
    type: str
    is_read: bool = Field(validation_alias="est_lue")
    created_at: datetime = Field(validation_alias="cree_le")
