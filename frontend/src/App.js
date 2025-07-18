import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MangaReader = () => {
  const [currentView, setCurrentView] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState(''); // Add debug state
  const [selectedManga, setSelectedManga] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [currentChapter, setCurrentChapter] = useState(null);
  const [currentPages, setCurrentPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [library, setLibrary] = useState([]);
  const [bookmarks, setBookmarks] = useState([]);
  const [userId] = useState('user123'); // Mock user ID

  // Search for manga
  const searchManga = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setSearchResults([]); // Clear previous results
    try {
      console.log('Searching for:', searchQuery);
      console.log('API URL:', `${API}/manga/search`);
      
      const response = await axios.get(`${API}/manga/search`, {
        params: { query: searchQuery, limit: 20 }
      });
      
      console.log('Full response:', response);
      console.log('Response data:', response.data);
      console.log('Response status:', response.status);
      
      if (response.data && response.data.manga) {
        console.log('Manga array:', response.data.manga);
        console.log('Manga count:', response.data.manga.length);
        setSearchResults(response.data.manga);
      } else {
        console.log('No manga data in response');
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      console.error('Error response:', error.response);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Get manga chapters
  const getMangaChapters = async (mangaId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/manga/${mangaId}/chapters`);
      setChapters(response.data.chapters);
      setCurrentView('chapters');
    } catch (error) {
      console.error('Chapters error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get chapter pages
  const getChapterPages = async (chapterId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/chapter/${chapterId}/pages`);
      setCurrentPages(response.data.pages);
      setCurrentPage(0);
      setCurrentView('reader');
    } catch (error) {
      console.error('Pages error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Add to library
  const addToLibrary = async (manga) => {
    try {
      await axios.post(`${API}/library/add`, null, {
        params: {
          user_id: userId,
          manga_id: manga.id,
          title: manga.title,
          cover_art: manga.cover_art
        }
      });
      loadLibrary();
    } catch (error) {
      console.error('Add to library error:', error);
    }
  };

  // Load library
  const loadLibrary = async () => {
    try {
      const response = await axios.get(`${API}/library/${userId}`);
      setLibrary(response.data.library);
    } catch (error) {
      console.error('Library error:', error);
    }
  };

  // Update reading progress
  const updateProgress = async (mangaId, chapterId, pageNumber) => {
    try {
      await axios.post(`${API}/progress/update`, null, {
        params: {
          user_id: userId,
          manga_id: mangaId,
          chapter_id: chapterId,
          page_number: pageNumber
        }
      });
    } catch (error) {
      console.error('Progress update error:', error);
    }
  };

  // Navigate pages
  const nextPage = () => {
    if (currentPage < currentPages.length - 1) {
      const newPage = currentPage + 1;
      setCurrentPage(newPage);
      if (currentChapter && selectedManga) {
        updateProgress(selectedManga.id, currentChapter.id, newPage);
      }
    }
  };

  const prevPage = () => {
    if (currentPage > 0) {
      const newPage = currentPage - 1;
      setCurrentPage(newPage);
      if (currentChapter && selectedManga) {
        updateProgress(selectedManga.id, currentChapter.id, newPage);
      }
    }
  };

  // Load library on mount
  useEffect(() => {
    loadLibrary();
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (currentView === 'reader') {
        if (e.key === 'ArrowRight' || e.key === ' ') {
          nextPage();
        } else if (e.key === 'ArrowLeft') {
          prevPage();
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentView, currentPage, currentPages.length]);

  const renderSearch = () => (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
        🌙 Manga Reader
      </h1>
      
      <div className="max-w-2xl mx-auto mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar manga..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && searchManga()}
          />
          <button
            onClick={searchManga}
            disabled={loading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        </div>
      </div>

      {searchResults.length > 0 && (
        <div>
          <p className="text-gray-600 mb-4">Encontrados {searchResults.length} resultados:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {searchResults.map((manga) => (
              <div key={manga.id} className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
                <img
                  src={manga.cover_art}
                  alt={manga.title}
                  className="w-full h-64 object-cover"
                />
                <div className="p-4">
                  <h3 className="font-bold text-lg mb-2 line-clamp-2">{manga.title}</h3>
                  <p className="text-gray-600 text-sm mb-2">{manga.author}</p>
                  <p className="text-gray-500 text-xs mb-3 line-clamp-3">{manga.description}</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setSelectedManga(manga);
                        getMangaChapters(manga.id);
                      }}
                      className="flex-1 px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                    >
                      Ler
                    </button>
                    <button
                      onClick={() => addToLibrary(manga)}
                      className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                    >
                      + Biblioteca
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {loading && (
        <div className="text-center py-8">
          <div className="loading-spinner mb-4"></div>
          <p className="text-gray-600">Buscando manga...</p>
        </div>
      )}
      
      {!loading && searchResults.length === 0 && searchQuery.trim() && (
        <div className="text-center py-8">
          <p className="text-gray-600">Nenhum resultado encontrado para "{searchQuery}"</p>
        </div>
      )}
    </div>
  );

  const renderChapters = () => (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => setCurrentView('search')}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          ← Voltar
        </button>
        <h2 className="text-2xl font-bold">{selectedManga?.title}</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {chapters.map((chapter) => (
          <div
            key={chapter.id}
            className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => {
              setCurrentChapter(chapter);
              getChapterPages(chapter.id);
            }}
          >
            <h3 className="font-semibold">{chapter.title}</h3>
            <p className="text-gray-600 text-sm">Capítulo {chapter.chapter_number}</p>
            <p className="text-gray-500 text-xs">{chapter.pages} páginas</p>
          </div>
        ))}
      </div>
    </div>
  );

  const renderReader = () => (
    <div className="min-h-screen bg-black text-white">
      <div className="flex items-center justify-between p-4 bg-gray-900">
        <button
          onClick={() => setCurrentView('chapters')}
          className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
        >
          ← Capítulos
        </button>
        <div className="text-center">
          <h3 className="font-semibold">{selectedManga?.title}</h3>
          <p className="text-sm text-gray-300">{currentChapter?.title}</p>
        </div>
        <div className="text-sm text-gray-300">
          {currentPage + 1} / {currentPages.length}
        </div>
      </div>

      {currentPages.length > 0 && (
        <div className="flex justify-center items-center min-h-screen p-4">
          <div className="relative max-w-4xl w-full">
            <img
              src={currentPages[currentPage]?.image_url}
              alt={`Page ${currentPage + 1}`}
              className="w-full h-auto max-h-screen object-contain"
              onClick={nextPage}
            />
            
            {/* Navigation buttons */}
            <button
              onClick={prevPage}
              disabled={currentPage === 0}
              className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75 disabled:opacity-25"
            >
              ←
            </button>
            <button
              onClick={nextPage}
              disabled={currentPage === currentPages.length - 1}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75 disabled:opacity-25"
            >
              →
            </button>
          </div>
        </div>
      )}

      {/* Progress bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 p-2">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentPage + 1) / currentPages.length) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderLibrary = () => (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => setCurrentView('search')}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          ← Buscar
        </button>
        <h2 className="text-2xl font-bold">Minha Biblioteca</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {library.map((item) => (
          <div key={item.id} className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
            <img
              src={item.cover_art}
              alt={item.title}
              className="w-full h-64 object-cover"
            />
            <div className="p-4">
              <h3 className="font-bold text-lg mb-2 line-clamp-2">{item.title}</h3>
              <p className="text-gray-600 text-sm mb-2">Status: {item.status}</p>
              {item.last_read_chapter && (
                <p className="text-gray-500 text-xs mb-3">
                  Última leitura: Página {item.last_read_page}
                </p>
              )}
              <button
                onClick={() => {
                  // TODO: Find manga by ID and continue reading
                  console.log('Continue reading:', item.manga_id);
                }}
                className="w-full px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
              >
                Continuar Lendo
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <span className="text-xl font-bold text-gray-900">📚 Manga Reader</span>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentView('search')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'search' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Buscar
              </button>
              <button
                onClick={() => {
                  setCurrentView('library');
                  loadLibrary();
                }}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'library' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Biblioteca
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      {currentView === 'search' && renderSearch()}
      {currentView === 'chapters' && renderChapters()}
      {currentView === 'reader' && renderReader()}
      {currentView === 'library' && renderLibrary()}
    </div>
  );
};

export default MangaReader;