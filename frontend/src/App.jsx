import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ArticleViewer from './components/ArticleViewer';
import axios from 'axios';

// API base URL - update this with your Railway backend URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [articles, setArticles] = useState([]);
  const [principles, setPrinciples] = useState([]);
  const [mathModels, setMathModels] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDecade, setSelectedDecade] = useState('all');
  const [selectedPrinciple, setSelectedPrinciple] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [articlesRes, principlesRes, mathRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/articles`),
        axios.get(`${API_BASE_URL}/api/principles`),
        axios.get(`${API_BASE_URL}/api/math`),
        axios.get(`${API_BASE_URL}/api/stats`)
      ]);

      setArticles(articlesRes.data);
      setPrinciples(principlesRes.data);
      setMathModels(mathRes.data);
      setStats(statsRes.data);
    } catch (err) {
      setError('Failed to load data from server');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredArticles = articles.filter(article => {
    const matchesDecade = selectedDecade === 'all' || 
      (article.year >= parseInt(selectedDecade) && article.year < parseInt(selectedDecade) + 10);
    const matchesPrinciple = selectedPrinciple === 'all' || 
      (article.principle && article.principle.name.toLowerCase().includes(selectedPrinciple.toLowerCase()));
    const matchesSearch = searchTerm === '' || 
      article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.authors.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesDecade && matchesPrinciple && matchesSearch;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-terminal-black text-terminal-green font-terminal crt relative">
        <div className="scan-line"></div>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="text-2xl mb-4 glow-text">JEAB DATABASE</div>
            <div className="text-lg">Loading<span className="loading-dots"></span></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-terminal-black text-terminal-green font-terminal crt relative">
        <div className="scan-line"></div>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="text-2xl mb-4 text-red-500">ERROR</div>
            <div className="text-lg">{error}</div>
            <button 
              onClick={fetchData}
              className="mt-4 px-4 py-2 border border-terminal-green text-terminal-green hover:bg-terminal-green hover:text-terminal-black transition-colors"
            >
              RETRY
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-terminal-black text-terminal-green font-terminal crt relative">
        <div className="scan-line"></div>
        
        {/* Header */}
        <header className="border-b border-terminal-green p-4">
          <div className="container mx-auto">
            <h1 className="text-3xl font-pixel glow-text text-center">
              JEAB CATALOG
            </h1>
            <p className="text-center text-terminal-light-green mt-2">
              Journal of the Experimental Analysis of Behavior Database
            </p>
          </div>
        </header>

        {/* Stats Bar */}
        {stats && (
          <div className="bg-terminal-dark border-b border-terminal-green p-2">
            <div className="container mx-auto flex justify-between text-sm">
              <span>Articles: {stats.total_articles}</span>
              <span>Principles: {stats.total_principles}</span>
              <span>Procedures: {stats.total_procedures}</span>
              <span>Math Models: {stats.total_math_models}</span>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-terminal-gray p-4 border-b border-terminal-green">
          <div className="container mx-auto">
            <div className="flex flex-wrap gap-4 items-center">
              <div>
                <label className="block text-sm mb-1">Decade:</label>
                <select 
                  value={selectedDecade}
                  onChange={(e) => setSelectedDecade(e.target.value)}
                  className="input-terminal px-2 py-1"
                >
                  <option value="all">All Decades</option>
                  <option value="1950">1950s</option>
                  <option value="1960">1960s</option>
                  <option value="1970">1970s</option>
                  <option value="1980">1980s</option>
                  <option value="1990">1990s</option>
                  <option value="2000">2000s</option>
                  <option value="2010">2010s</option>
                  <option value="2020">2020s</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm mb-1">Principle:</label>
                <select 
                  value={selectedPrinciple}
                  onChange={(e) => setSelectedPrinciple(e.target.value)}
                  className="input-terminal px-2 py-1"
                >
                  <option value="all">All Principles</option>
                  {principles.map(principle => (
                    <option key={principle.id} value={principle.name}>
                      {principle.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm mb-1">Search:</label>
                <input 
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search articles..."
                  className="input-terminal px-2 py-1"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <main className="container mx-auto p-4">
          <Routes>
            <Route path="/" element={
              <ArticleViewer 
                articles={filteredArticles}
                principles={principles}
                mathModels={mathModels}
              />
            } />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-terminal-green p-4 mt-8">
          <div className="container mx-auto text-center text-sm">
            <p>© 2024 JEAB Catalog - Behavioral Analysis Database</p>
            <p className="text-terminal-light-green">Built with FastAPI + React + Railway</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App; 