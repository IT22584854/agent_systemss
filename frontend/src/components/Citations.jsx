import PropTypes from 'prop-types';
import { BookOpen, ExternalLink, FileText } from 'lucide-react';

export default function Citations({ sources }) {
    if (!sources || sources.length === 0) return null;

    // Deduplicate by source name, filter out Unknown/empty
    const unique = [];
    const seen = new Set();
    for (const src of sources) {
        const name = src.title || src.source || '';
        if (!name || name.toLowerCase().startsWith('unknown')) continue;
        if (!seen.has(name)) {
            seen.add(name);
            unique.push({ ...src, _name: name });
        }
    }

    if (unique.length === 0) return null;

    return (
        <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500 font-medium shrink-0">
                <BookOpen size={12} />
                Sources:
            </span>
            {unique.map((src, i) =>
                src.url ? (
                    <a
                        key={i}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="
                            inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs
                            bg-primary-50 dark:bg-primary-900/30
                            text-primary-700 dark:text-primary-300
                            border border-primary-200 dark:border-primary-700
                            hover:bg-primary-100 dark:hover:bg-primary-800/40
                            transition-colors duration-150
                        "
                    >
                        <ExternalLink size={10} className="shrink-0" />
                        <span className="max-w-[200px] truncate">{src._name}</span>
                    </a>
                ) : (
                    <span
                        key={i}
                        className="
                            inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs
                            bg-gray-100 dark:bg-gray-800
                            text-gray-600 dark:text-gray-300
                            border border-gray-200 dark:border-gray-700
                        "
                        title={src._name}
                    >
                        <FileText size={10} className="shrink-0 text-gray-400" />
                        <span className="max-w-[200px] truncate">{src._name}</span>
                    </span>
                )
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
