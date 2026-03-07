import { useState } from 'react';
import PropTypes from 'prop-types';
import { BookOpen, ChevronDown, ChevronUp, ExternalLink, FileText } from 'lucide-react';

export default function Citations({ sources }) {
    const [open, setOpen] = useState(false);

    if (!sources || sources.length === 0) return null;

    return (
        <div className="mt-4">
            <button 
                className="citations-toggle group"
                onClick={() => setOpen(o => !o)}
                aria-expanded={open}
                aria-label={`${open ? 'Hide' : 'Show'} ${sources.length} source${sources.length > 1 ? 's' : ''}`}
            >
                <BookOpen size={14} className="text-primary-500 dark:text-primary-400" />
                <span className="font-medium">{sources.length} Source{sources.length > 1 ? 's' : ''}</span>
                {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {open && (
                <div className="mt-3 space-y-2 animate-slide-in">
                    {sources.map((src, i) => (
                        <div 
                            key={src.id ?? i} 
                            className="
                                group/card relative p-3 rounded-lg 
                                bg-gray-50 dark:bg-gray-800/50 
                                border border-gray-200 dark:border-gray-700
                                hover:border-primary-300 dark:hover:border-primary-600
                                hover:shadow-md
                                transition-all duration-200
                            "
                        >
                            <div className="flex gap-3">
                                {/* Citation Number Badge */}
                                <div className="
                                    flex-shrink-0 w-6 h-6 rounded-full 
                                    bg-primary-500 dark:bg-primary-600 
                                    text-white text-xs font-semibold
                                    flex items-center justify-center
                                ">
                                    {i + 1}
                                </div>

                                {/* Citation Content */}
                                <div className="flex-1 min-w-0">
                                    {/* Source Title/Link */}
                                    <div className="flex items-start gap-2 mb-1">
                                        {src.url ? (
                                            <a
                                                href={src.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="
                                                    flex items-center gap-1.5 text-sm font-medium
                                                    text-primary-600 dark:text-primary-400
                                                    hover:text-primary-700 dark:hover:text-primary-300
                                                    hover:underline transition-colors
                                                "
                                            >
                                                <span className="truncate">{src.title || src.source}</span>
                                                <ExternalLink size={12} className="flex-shrink-0" />
                                            </a>
                                        ) : (
                                            <div className="flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-300">
                                                <FileText size={14} className="flex-shrink-0 text-gray-400" />
                                                <span className="truncate">{src.source}</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Excerpt */}
                                    {src.excerpt && (
                                        <p className="
                                            text-xs text-gray-600 dark:text-gray-400 
                                            leading-relaxed line-clamp-3
                                            italic border-l-2 border-gray-300 dark:border-gray-600
                                            pl-2 mt-2
                                        ">
                                            "{src.excerpt}"
                                        </p>
                                    )}

                                    {/* Metadata (if available) */}
                                    {(src.score || src.chunk_index !== undefined) && (
                                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-500">
                                            {src.score && (
                                                <span>Relevance: {Math.round(src.score * 100)}%</span>
                                            )}
                                            {src.chunk_index !== undefined && (
                                                <span>Chunk: {src.chunk_index}</span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

Citations.propTypes = {
    sources: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        title: PropTypes.string,
        source: PropTypes.string,
        url: PropTypes.string,
        excerpt: PropTypes.string,
        score: PropTypes.number,
        chunk_index: PropTypes.number,
    })),
};
