from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import httpx
import asyncio
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class MangaInfo(BaseModel):
    id: str
    title: str
    description: str
    author: str
    status: str
    cover_art: str
    tags: List[str]
    chapters: int
    source: str = "mangadex"

class ChapterInfo(BaseModel):
    id: str
    title: str
    chapter_number: float
    pages: int
    manga_id: str
    volume: Optional[str] = None
    published_date: Optional[datetime] = None

class MangaPage(BaseModel):
    page_number: int
    image_url: str
    width: int
    height: int

class ReadingProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    manga_id: str
    chapter_id: str
    page_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Bookmark(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    manga_id: str
    chapter_id: str
    page_number: int
    title: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserLibrary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    manga_id: str
    title: str
    cover_art: str
    last_read_chapter: Optional[str] = None
    last_read_page: int = 0
    favorite: bool = False
    status: str = "reading"  # reading, completed, on_hold, dropped
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# MangaDex API Integration
class MangaDexAPI:
    BASE_URL = "https://api.mangadex.org"
    
    @staticmethod
    async def search_manga(query: str, limit: int = 20) -> List[MangaInfo]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MangaDexAPI.BASE_URL}/manga",
                params={
                    "title": query,
                    "limit": limit,
                    "includes[]": ["cover_art", "author"]
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to search manga")
            
            data = response.json()
            manga_list = []
            
            for manga_data in data.get("data", []):
                # Get cover art
                cover_art_url = ""
                for rel in manga_data.get("relationships", []):
                    if rel["type"] == "cover_art":
                        cover_filename = rel["attributes"]["fileName"]
                        cover_art_url = f"https://uploads.mangadex.org/covers/{manga_data['id']}/{cover_filename}.256.jpg"
                        break
                
                # Get author
                author = "Unknown"
                for rel in manga_data.get("relationships", []):
                    if rel["type"] == "author":
                        author = rel["attributes"].get("name", "Unknown")
                        break
                
                manga_info = MangaInfo(
                    id=manga_data["id"],
                    title=manga_data["attributes"]["title"].get("en", list(manga_data["attributes"]["title"].values())[0]),
                    description=manga_data["attributes"]["description"].get("en", ""),
                    author=author,
                    status=manga_data["attributes"]["status"],
                    cover_art=cover_art_url,
                    tags=[tag["attributes"]["name"]["en"] for tag in manga_data["attributes"]["tags"]],
                    chapters=0,
                    source="mangadex"
                )
                manga_list.append(manga_info)
            
            return manga_list
    
    @staticmethod
    async def get_manga_chapters(manga_id: str, limit: int = 100) -> List[ChapterInfo]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MangaDexAPI.BASE_URL}/manga/{manga_id}/feed",
                params={
                    "limit": limit,
                    "order[chapter]": "asc",
                    "translatedLanguage[]": "en"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to get chapters")
            
            data = response.json()
            chapters = []
            
            for chapter_data in data.get("data", []):
                chapter_info = ChapterInfo(
                    id=chapter_data["id"],
                    title=chapter_data["attributes"]["title"] or f"Chapter {chapter_data['attributes']['chapter']}",
                    chapter_number=float(chapter_data["attributes"]["chapter"] or 0),
                    pages=int(chapter_data["attributes"]["pages"] or 0),
                    manga_id=manga_id,
                    volume=chapter_data["attributes"]["volume"],
                    published_date=datetime.fromisoformat(chapter_data["attributes"]["publishAt"].replace("Z", "+00:00")) if chapter_data["attributes"]["publishAt"] else None
                )
                chapters.append(chapter_info)
            
            return chapters
    
    @staticmethod
    async def get_chapter_pages(chapter_id: str) -> List[MangaPage]:
        async with httpx.AsyncClient() as client:
            # Get chapter info
            response = await client.get(f"{MangaDexAPI.BASE_URL}/at-home/server/{chapter_id}")
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to get chapter pages")
            
            data = response.json()
            base_url = data["baseUrl"]
            chapter_hash = data["chapter"]["hash"]
            pages_data = data["chapter"]["data"]
            
            pages = []
            for i, page_filename in enumerate(pages_data):
                page_url = f"{base_url}/data/{chapter_hash}/{page_filename}"
                pages.append(MangaPage(
                    page_number=i + 1,
                    image_url=page_url,
                    width=0,  # Will be determined by frontend
                    height=0
                ))
            
            return pages

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Manga Reader API"}

@api_router.get("/manga/search")
async def search_manga(query: str, limit: int = 20):
    try:
        manga_list = await MangaDexAPI.search_manga(query, limit)
        return {"manga": manga_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/manga/{manga_id}")
async def get_manga_details(manga_id: str):
    try:
        # Get manga info from MangaDX
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MangaDexAPI.BASE_URL}/manga/{manga_id}",
                params={"includes[]": ["cover_art", "author"]}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Manga not found")
            
            data = response.json()
            manga_data = data["data"]
            
            # Get cover art
            cover_art_url = ""
            for rel in manga_data.get("relationships", []):
                if rel["type"] == "cover_art":
                    cover_filename = rel["attributes"]["fileName"]
                    cover_art_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}.256.jpg"
                    break
            
            # Get author
            author = "Unknown"
            for rel in manga_data.get("relationships", []):
                if rel["type"] == "author":
                    author = rel["attributes"].get("name", "Unknown")
                    break
            
            manga_info = MangaInfo(
                id=manga_id,
                title=manga_data["attributes"]["title"].get("en", list(manga_data["attributes"]["title"].values())[0]),
                description=manga_data["attributes"]["description"].get("en", ""),
                author=author,
                status=manga_data["attributes"]["status"],
                cover_art=cover_art_url,
                tags=[tag["attributes"]["name"]["en"] for tag in manga_data["attributes"]["tags"]],
                chapters=0,
                source="mangadex"
            )
            
            return manga_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/manga/{manga_id}/chapters")
async def get_manga_chapters(manga_id: str, limit: int = 100):
    try:
        chapters = await MangaDexAPI.get_manga_chapters(manga_id, limit)
        return {"chapters": chapters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/chapter/{chapter_id}/pages")
async def get_chapter_pages(chapter_id: str):
    try:
        pages = await MangaDexAPI.get_chapter_pages(chapter_id)
        return {"pages": pages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Library Management
@api_router.post("/library/add")
async def add_to_library(user_id: str, manga_id: str, title: str, cover_art: str):
    try:
        # Check if already in library
        existing = await db.user_library.find_one({"user_id": user_id, "manga_id": manga_id})
        if existing:
            return {"message": "Already in library"}
        
        library_item = UserLibrary(
            user_id=user_id,
            manga_id=manga_id,
            title=title,
            cover_art=cover_art
        )
        
        await db.user_library.insert_one(library_item.dict())
        return {"message": "Added to library"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/library/{user_id}")
async def get_user_library(user_id: str):
    try:
        library_items = await db.user_library.find({"user_id": user_id}).to_list(1000)
        return {"library": [UserLibrary(**item) for item in library_items]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/progress/update")
async def update_reading_progress(user_id: str, manga_id: str, chapter_id: str, page_number: int):
    try:
        progress = ReadingProgress(
            user_id=user_id,
            manga_id=manga_id,
            chapter_id=chapter_id,
            page_number=page_number
        )
        
        # Update or insert progress
        await db.reading_progress.replace_one(
            {"user_id": user_id, "manga_id": manga_id, "chapter_id": chapter_id},
            progress.dict(),
            upsert=True
        )
        
        # Update library item
        await db.user_library.update_one(
            {"user_id": user_id, "manga_id": manga_id},
            {"$set": {"last_read_chapter": chapter_id, "last_read_page": page_number}}
        )
        
        return {"message": "Progress updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/progress/{user_id}/{manga_id}")
async def get_reading_progress(user_id: str, manga_id: str):
    try:
        progress = await db.reading_progress.find_one(
            {"user_id": user_id, "manga_id": manga_id}, 
            sort=[("timestamp", -1)]
        )
        
        if progress:
            return ReadingProgress(**progress)
        else:
            return {"message": "No progress found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bookmarks
@api_router.post("/bookmarks/add")
async def add_bookmark(user_id: str, manga_id: str, chapter_id: str, page_number: int, title: str):
    try:
        bookmark = Bookmark(
            user_id=user_id,
            manga_id=manga_id,
            chapter_id=chapter_id,
            page_number=page_number,
            title=title
        )
        
        await db.bookmarks.insert_one(bookmark.dict())
        return {"message": "Bookmark added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bookmarks/{user_id}")
async def get_user_bookmarks(user_id: str):
    try:
        bookmarks = await db.bookmarks.find({"user_id": user_id}).to_list(1000)
        return {"bookmarks": [Bookmark(**bookmark) for bookmark in bookmarks]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()