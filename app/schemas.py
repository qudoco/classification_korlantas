from pydantic import BaseModel, Field
from typing import List, Optional


class NewsRequest(BaseModel):
    title: str = Field(
        ...,
        description="Judul berita yang akan dianalisis untuk relevansi terhadap client"
    )
    content: str = Field(
        ...,
        description="Isi lengkap artikel berita yang akan dilakukan scoring relevansi"
    )
    urlCallback: Optional[str] = Field(
        None,
        description="URL callback untuk mengirim hasil scoring setelah proses selesai"
    )
    id: int = Field(
        ...,
        description="ID unik artikel dari sistem sumber"
    )
    client: List[str] = Field(
        ...,
        description="Daftar nama client yang akan dicek relevansinya terhadap artikel"
    )
    mediaId: str = Field(
        ...,
        description="ID unik media atau sumber berita"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "DVI Polda Jabar identifikasi 80 jenazah korban longsor Cisarua",
                "content": "Tim Disaster Victim Identification (DVI) Polda Jawa Barat berhasil mengidentifikasi...",
                "urlCallback": "http://localhost:8080/api/v1/news/scoring",
                "id": 299924,
                "client": [
                    "Mediahub",
                    "Korlantas Polri",
                    "testing",
                    "Multipool"
                ],
                "mediaId": "297cda85-0379-4cee-b78e-fe416a19c8a4"
            }
        }
