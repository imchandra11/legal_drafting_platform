from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from .base_provider import StorageProvider
import io

class GoogleDriveProvider(StorageProvider):
    def __init__(self, credentials: dict):
        self.creds = Credentials.from_service_account_info(credentials)
        self.service = build("drive", "v3", credentials=self.creds)
    
    async def save_file(self, name: str, content: str) -> str:
        file_metadata = {"name": name}
        media = io.BytesIO(content.encode())
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        return file.get("id")
    
    async def get_file(self, file_id: str) -> str:
        request = self.service.files().get_media(fileId=file_id)
        return request.execute().decode()