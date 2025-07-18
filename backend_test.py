#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Manga Reader Application
Tests all core endpoints including MangaDex integration, library management, 
progress tracking, and bookmarks functionality.
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

# Configuration
BASE_URL = "https://882ecef0-f450-49fa-985b-402fd88bacd0.preview.emergentagent.com/api"
TEST_USER_ID = "user123"
TIMEOUT = 30

class MangaReaderTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.manga_id = None
        self.chapter_id = None
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("API Root", True, "API root endpoint accessible")
                    return True
                else:
                    self.log_test("API Root", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("API Root", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_manga_search(self):
        """Test manga search functionality"""
        try:
            # Test with "one piece"
            response = self.session.get(f"{BASE_URL}/manga/search", params={"query": "one piece", "limit": 5})
            
            if response.status_code == 200:
                data = response.json()
                if "manga" in data and isinstance(data["manga"], list):
                    manga_list = data["manga"]
                    if len(manga_list) > 0:
                        # Store first manga for further testing
                        self.manga_id = manga_list[0]["id"]
                        self.log_test("Manga Search", True, f"Found {len(manga_list)} manga results for 'one piece'")
                        
                        # Validate manga structure
                        first_manga = manga_list[0]
                        required_fields = ["id", "title", "description", "author", "status", "cover_art", "tags"]
                        missing_fields = [field for field in required_fields if field not in first_manga]
                        
                        if missing_fields:
                            self.log_test("Manga Search Structure", False, f"Missing fields: {missing_fields}", first_manga)
                        else:
                            self.log_test("Manga Search Structure", True, "All required fields present in manga data")
                        
                        return True
                    else:
                        self.log_test("Manga Search", False, "No manga results returned", data)
                        return False
                else:
                    self.log_test("Manga Search", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test("Manga Search", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Manga Search", False, f"Request error: {str(e)}")
            return False
    
    def test_manga_details(self):
        """Test manga details endpoint"""
        if not self.manga_id:
            self.log_test("Manga Details", False, "No manga ID available from search test")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/manga/{self.manga_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "description", "author", "status", "cover_art", "tags"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Manga Details", False, f"Missing fields: {missing_fields}", data)
                    return False
                else:
                    self.log_test("Manga Details", True, f"Retrieved details for manga: {data.get('title', 'Unknown')}")
                    return True
            else:
                self.log_test("Manga Details", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Manga Details", False, f"Request error: {str(e)}")
            return False
    
    def test_manga_chapters(self):
        """Test manga chapters endpoint"""
        if not self.manga_id:
            self.log_test("Manga Chapters", False, "No manga ID available from search test")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/manga/{self.manga_id}/chapters", params={"limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                if "chapters" in data and isinstance(data["chapters"], list):
                    chapters = data["chapters"]
                    if len(chapters) > 0:
                        # Store first chapter for further testing
                        self.chapter_id = chapters[0]["id"]
                        self.log_test("Manga Chapters", True, f"Retrieved {len(chapters)} chapters")
                        
                        # Validate chapter structure
                        first_chapter = chapters[0]
                        required_fields = ["id", "title", "chapter_number", "pages", "manga_id"]
                        missing_fields = [field for field in required_fields if field not in first_chapter]
                        
                        if missing_fields:
                            self.log_test("Chapter Structure", False, f"Missing fields: {missing_fields}", first_chapter)
                        else:
                            self.log_test("Chapter Structure", True, "All required fields present in chapter data")
                        
                        return True
                    else:
                        self.log_test("Manga Chapters", False, "No chapters returned", data)
                        return False
                else:
                    self.log_test("Manga Chapters", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test("Manga Chapters", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Manga Chapters", False, f"Request error: {str(e)}")
            return False
    
    def test_chapter_pages(self):
        """Test chapter pages endpoint"""
        if not self.chapter_id:
            self.log_test("Chapter Pages", False, "No chapter ID available from chapters test")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/chapter/{self.chapter_id}/pages")
            
            if response.status_code == 200:
                data = response.json()
                if "pages" in data and isinstance(data["pages"], list):
                    pages = data["pages"]
                    if len(pages) > 0:
                        self.log_test("Chapter Pages", True, f"Retrieved {len(pages)} pages")
                        
                        # Validate page structure
                        first_page = pages[0]
                        required_fields = ["page_number", "image_url", "width", "height"]
                        missing_fields = [field for field in required_fields if field not in first_page]
                        
                        if missing_fields:
                            self.log_test("Page Structure", False, f"Missing fields: {missing_fields}", first_page)
                        else:
                            self.log_test("Page Structure", True, "All required fields present in page data")
                        
                        return True
                    else:
                        self.log_test("Chapter Pages", False, "No pages returned", data)
                        return False
                else:
                    self.log_test("Chapter Pages", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test("Chapter Pages", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Chapter Pages", False, f"Request error: {str(e)}")
            return False
    
    def test_library_add(self):
        """Test adding manga to library"""
        if not self.manga_id:
            self.log_test("Library Add", False, "No manga ID available for library test")
            return False
        
        try:
            payload = {
                "user_id": TEST_USER_ID,
                "manga_id": self.manga_id,
                "title": "One Piece",
                "cover_art": "https://example.com/cover.jpg"
            }
            
            response = self.session.post(f"{BASE_URL}/library/add", params=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Library Add", True, f"Added manga to library: {data['message']}")
                    return True
                else:
                    self.log_test("Library Add", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Library Add", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Library Add", False, f"Request error: {str(e)}")
            return False
    
    def test_library_get(self):
        """Test getting user library"""
        try:
            response = self.session.get(f"{BASE_URL}/library/{TEST_USER_ID}")
            
            if response.status_code == 200:
                data = response.json()
                if "library" in data and isinstance(data["library"], list):
                    library = data["library"]
                    self.log_test("Library Get", True, f"Retrieved library with {len(library)} items")
                    
                    if len(library) > 0:
                        # Validate library item structure
                        first_item = library[0]
                        required_fields = ["id", "user_id", "manga_id", "title", "cover_art"]
                        missing_fields = [field for field in required_fields if field not in first_item]
                        
                        if missing_fields:
                            self.log_test("Library Item Structure", False, f"Missing fields: {missing_fields}", first_item)
                        else:
                            self.log_test("Library Item Structure", True, "All required fields present in library item")
                    
                    return True
                else:
                    self.log_test("Library Get", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test("Library Get", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Library Get", False, f"Request error: {str(e)}")
            return False
    
    def test_progress_update(self):
        """Test updating reading progress"""
        if not self.manga_id or not self.chapter_id:
            self.log_test("Progress Update", False, "No manga/chapter ID available for progress test")
            return False
        
        try:
            payload = {
                "user_id": TEST_USER_ID,
                "manga_id": self.manga_id,
                "chapter_id": self.chapter_id,
                "page_number": 5
            }
            
            response = self.session.post(f"{BASE_URL}/progress/update", params=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Progress Update", True, f"Updated progress: {data['message']}")
                    return True
                else:
                    self.log_test("Progress Update", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Progress Update", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Progress Update", False, f"Request error: {str(e)}")
            return False
    
    def test_progress_get(self):
        """Test getting reading progress"""
        if not self.manga_id:
            self.log_test("Progress Get", False, "No manga ID available for progress test")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/progress/{TEST_USER_ID}/{self.manga_id}")
            
            if response.status_code == 200:
                data = response.json()
                # Progress might not exist or might be a "No progress found" message
                if "message" in data and "No progress found" in data["message"]:
                    self.log_test("Progress Get", True, "No progress found (expected for new user)")
                    return True
                elif "id" in data and "user_id" in data:
                    self.log_test("Progress Get", True, f"Retrieved progress for user {data.get('user_id')}")
                    return True
                else:
                    self.log_test("Progress Get", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Progress Get", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Progress Get", False, f"Request error: {str(e)}")
            return False
    
    def test_bookmarks_add(self):
        """Test adding bookmark"""
        if not self.manga_id or not self.chapter_id:
            self.log_test("Bookmarks Add", False, "No manga/chapter ID available for bookmark test")
            return False
        
        try:
            payload = {
                "user_id": TEST_USER_ID,
                "manga_id": self.manga_id,
                "chapter_id": self.chapter_id,
                "page_number": 10,
                "title": "Interesting scene"
            }
            
            response = self.session.post(f"{BASE_URL}/bookmarks/add", params=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Bookmarks Add", True, f"Added bookmark: {data['message']}")
                    return True
                else:
                    self.log_test("Bookmarks Add", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Bookmarks Add", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Bookmarks Add", False, f"Request error: {str(e)}")
            return False
    
    def test_bookmarks_get(self):
        """Test getting user bookmarks"""
        try:
            response = self.session.get(f"{BASE_URL}/bookmarks/{TEST_USER_ID}")
            
            if response.status_code == 200:
                data = response.json()
                if "bookmarks" in data and isinstance(data["bookmarks"], list):
                    bookmarks = data["bookmarks"]
                    self.log_test("Bookmarks Get", True, f"Retrieved {len(bookmarks)} bookmarks")
                    
                    if len(bookmarks) > 0:
                        # Validate bookmark structure
                        first_bookmark = bookmarks[0]
                        required_fields = ["id", "user_id", "manga_id", "chapter_id", "page_number", "title"]
                        missing_fields = [field for field in required_fields if field not in first_bookmark]
                        
                        if missing_fields:
                            self.log_test("Bookmark Structure", False, f"Missing fields: {missing_fields}", first_bookmark)
                        else:
                            self.log_test("Bookmark Structure", True, "All required fields present in bookmark data")
                    
                    return True
                else:
                    self.log_test("Bookmarks Get", False, "Invalid response structure", data)
                    return False
            else:
                self.log_test("Bookmarks Get", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Bookmarks Get", False, f"Request error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid manga ID
            response = self.session.get(f"{BASE_URL}/manga/invalid-id")
            if response.status_code in [404, 500]:
                self.log_test("Error Handling - Invalid Manga", True, f"Properly handled invalid manga ID with HTTP {response.status_code}")
            else:
                self.log_test("Error Handling - Invalid Manga", False, f"Unexpected response for invalid manga ID: HTTP {response.status_code}")
            
            # Test invalid chapter ID
            response = self.session.get(f"{BASE_URL}/chapter/invalid-id/pages")
            if response.status_code in [404, 500]:
                self.log_test("Error Handling - Invalid Chapter", True, f"Properly handled invalid chapter ID with HTTP {response.status_code}")
            else:
                self.log_test("Error Handling - Invalid Chapter", False, f"Unexpected response for invalid chapter ID: HTTP {response.status_code}")
            
            return True
        except Exception as e:
            self.log_test("Error Handling", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("=" * 60)
        print("MANGA READER BACKEND API TESTING")
        print("=" * 60)
        print(f"Base URL: {BASE_URL}")
        print(f"Test User ID: {TEST_USER_ID}")
        print(f"Timeout: {TIMEOUT}s")
        print("=" * 60)
        
        # Core API tests
        self.test_api_root()
        self.test_manga_search()
        self.test_manga_details()
        self.test_manga_chapters()
        self.test_chapter_pages()
        
        # Library management tests
        self.test_library_add()
        self.test_library_get()
        
        # Progress tracking tests
        self.test_progress_update()
        self.test_progress_get()
        
        # Bookmark tests
        self.test_bookmarks_add()
        self.test_bookmarks_get()
        
        # Error handling tests
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        return passed == total

if __name__ == "__main__":
    tester = MangaReaderTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)