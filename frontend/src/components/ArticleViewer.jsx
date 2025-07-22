import React, { useState } from 'react';
import { BookOpen, Calendar, Users, FileText, Calculator, Zap } from 'lucide-react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

const ArticleViewer = ({ articles, principles, mathModels }) => {
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [showMath, setShowMath] = useState(true);
  const [mathType, setMathType] = useState('static'); // 'static' or 'recursive'

  const handleArticleClick = (article) => {
    setSelectedArticle(article);
  };

  const closeArticle = () => {
    setSelectedArticle(null);
  };

  const renderMathContent = (mathModel) => {
    if (!mathModel || !showMath) return null;

    return (
      <div className="terminal-window p-4 mt-4">
        <div className="flex items-center gap-2 mb-3">
          <Calculator className="w-5 h-5 text-terminal-amber" />
          <h3 className="text-lg font-bold text-terminal-amber">Mathematical Model</h3>
        </div>
        
        <div className="mb-4">
          <div className="flex gap-2 mb-2">
            <button
              onClick={() => setMathType('static')}
              className={`px-3 py-1 text-sm border ${
                mathType === 'static' 
                  ? 'bg-terminal-green text-terminal-black' 
                  : 'border-terminal-green text-terminal-green'
              }`}
            >
              Static
            </button>
            <button
              onClick={() => setMathType('recursive')}
              className={`px-3 py-1 text-sm border ${
                mathType === 'recursive' 
                  ? 'bg-terminal-green text-terminal-black' 
                  : 'border-terminal-green text-terminal-green'
              }`}
            >
              Recursive
            </button>
          </div>
        </div>

        {mathModel.latex_equation && (
          <div className="mb-4">
            <div className="text-sm text-terminal-light-green mb-2">Equation:</div>
            <div className="bg-terminal-dark p-3 border border-terminal-green">
              <BlockMath math={mathModel.latex_equation} />
            </div>
          </div>
        )}

        {mathModel.description && (
          <div className="mb-4">
            <div className="text-sm text-terminal-light-green mb-2">Description:</div>
            <div className="text-sm">{mathModel.description}</div>
          </div>
        )}

        {mathModel.parameters && (
          <div>
            <div className="text-sm text-terminal-light-green mb-2">Parameters:</div>
            <div className="text-sm font-mono bg-terminal-dark p-2 border border-terminal-green">
              {mathModel.parameters}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderArticleList = () => (
    <div className="grid gap-4">
      {articles.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-xl text-terminal-amber mb-2">NO ARTICLES FOUND</div>
          <div className="text-sm">Try adjusting your filters or search terms</div>
        </div>
      ) : (
        articles.map((article) => (
          <div
            key={article.id}
            onClick={() => handleArticleClick(article)}
            className="terminal-window p-4 cursor-pointer hover:border-terminal-light-green transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-bold text-terminal-amber mb-2">
                  {article.title}
                </h3>
                <div className="flex items-center gap-4 text-sm mb-2">
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>{article.authors}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span>{article.year}</span>
                  </div>
                  {article.volume && (
                    <div className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      <span>Vol. {article.volume}</span>
                    </div>
                  )}
                </div>
                
                {article.principle && (
                  <div className="flex items-center gap-1 text-sm text-terminal-light-green mb-2">
                    <Zap className="w-4 h-4" />
                    <span>{article.principle.name}</span>
                  </div>
                )}
                
                {article.abstract && (
                  <div className="text-sm text-gray-300 line-clamp-3">
                    {article.abstract}
                  </div>
                )}
              </div>
              
              {article.math_model && (
                <div className="text-terminal-amber text-xs">
                  <Calculator className="w-4 h-4" />
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );

  const renderArticleDetail = () => (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-terminal-black border-2 border-terminal-green max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-2xl font-bold text-terminal-amber">
              {selectedArticle.title}
            </h2>
            <button
              onClick={closeArticle}
              className="text-terminal-green hover:text-terminal-light-green text-2xl"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Article Details */}
            <div>
              <div className="terminal-window p-4 mb-4">
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen className="w-5 h-5 text-terminal-amber" />
                  <h3 className="text-lg font-bold text-terminal-amber">Article Details</h3>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-terminal-light-green">Authors:</span> {selectedArticle.authors}
                  </div>
                  <div>
                    <span className="text-terminal-light-green">Year:</span> {selectedArticle.year}
                  </div>
                  {selectedArticle.volume && (
                    <div>
                      <span className="text-terminal-light-green">Volume:</span> {selectedArticle.volume}
                    </div>
                  )}
                  {selectedArticle.issue && (
                    <div>
                      <span className="text-terminal-light-green">Issue:</span> {selectedArticle.issue}
                    </div>
                  )}
                  {selectedArticle.pages && (
                    <div>
                      <span className="text-terminal-light-green">Pages:</span> {selectedArticle.pages}
                    </div>
                  )}
                  {selectedArticle.doi && (
                    <div>
                      <span className="text-terminal-light-green">DOI:</span> {selectedArticle.doi}
                    </div>
                  )}
                </div>
              </div>

              {selectedArticle.abstract && (
                <div className="terminal-window p-4 mb-4">
                  <h3 className="text-lg font-bold text-terminal-amber mb-3">Abstract</h3>
                  <div className="text-sm leading-relaxed">{selectedArticle.abstract}</div>
                </div>
              )}

              {selectedArticle.principle && (
                <div className="terminal-window p-4 mb-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Zap className="w-5 h-5 text-terminal-amber" />
                    <h3 className="text-lg font-bold text-terminal-amber">Behavioral Principle</h3>
                  </div>
                  
                  <div className="mb-2">
                    <div className="text-lg font-bold text-terminal-light-green">
                      {selectedArticle.principle.name}
                    </div>
                  </div>
                  
                  {selectedArticle.principle.description && (
                    <div className="text-sm">{selectedArticle.principle.description}</div>
                  )}
                  
                  {selectedArticle.principle.category && (
                    <div className="text-sm text-terminal-light-green mt-2">
                      Category: {selectedArticle.principle.category}
                    </div>
                  )}
                </div>
              )}

              {selectedArticle.procedure && (
                <div className="terminal-window p-4">
                  <h3 className="text-lg font-bold text-terminal-amber mb-3">Experimental Procedure</h3>
                  
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-terminal-light-green">Name:</span> {selectedArticle.procedure.name}
                    </div>
                    {selectedArticle.procedure.organism && (
                      <div>
                        <span className="text-terminal-light-green">Organism:</span> {selectedArticle.procedure.organism}
                      </div>
                    )}
                    {selectedArticle.procedure.apparatus && (
                      <div>
                        <span className="text-terminal-light-green">Apparatus:</span> {selectedArticle.procedure.apparatus}
                      </div>
                    )}
                    {selectedArticle.procedure.description && (
                      <div className="mt-3">
                        <div className="text-terminal-light-green mb-1">Description:</div>
                        <div>{selectedArticle.procedure.description}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Math Model */}
            <div>
              {selectedArticle.math_model ? (
                renderMathContent(selectedArticle.math_model)
              ) : (
                <div className="terminal-window p-4 mt-4">
                  <div className="text-center text-terminal-light-green">
                    <Calculator className="w-8 h-8 mx-auto mb-2" />
                    <div>No mathematical model available</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      {selectedArticle ? renderArticleDetail() : renderArticleList()}
    </div>
  );
};

export default ArticleViewer; 