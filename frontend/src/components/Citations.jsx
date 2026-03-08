import PropTypes from 'prop-types';
import { BookOpen, ExternalLink, FileText, Globe2, Quote } from 'lucide-react';

function formatHostname(url) {
    try {
        return new URL(url).hostname.replace(/^www\./, '');
    } catch {
        return '';
    }
}

function prettifyLabel(source) {
    const raw = (source.title || source.source || '').trim();
    if (!raw) return '';

    if (/^https?:\/\//i.test(raw)) {
        const hostname = formatHostname(raw);
        return hostname || raw;
    }

    return raw
        .replace(/^EPID[_-]?Reports?[_-]?/i, 'EPID Report ')
        .replace(/^MOH[_-]?Main[_-]?/i, 'MOH ')
        .replace(/[_-]+/g, ' ')
        .replace(/\.pdf$/i, '')
        .replace(/\s+/g, ' ')
        .trim();
}

function normalizeSources(sources) {
    const unique = [];
    const seen = new Set();

    for (const src of sources) {
        const label = prettifyLabel(src);
        if (!label || label.toLowerCase().startsWith('unknown')) continue;

        const key = `${label}::${src.url || ''}`;
        if (seen.has(key)) continue;
        seen.add(key);

        unique.push({
            ...src,
            label,
            hostname: src.url ? formatHostname(src.url) : '',
            excerpt: (src.excerpt || '').trim(),
        });
    }

    return unique;
}

export default function Citations({ sources }) {
    if (!sources || sources.length === 0) return null;

    const unique = normalizeSources(sources);

    if (unique.length === 0) return null;

    return (
        <section className="citations-wrapper" aria-label="Sources">
            <div className="citations-header">
                <div className="citations-title">
                    <BookOpen size={14} />
                    <span>Sources</span>
                </div>
                <div className="citations-count">{unique.length}</div>
            </div>

            <div className="citations-panel">
                {unique.map((src, index) => {
                    const content = (
                        <>
                            <div className="citation-topline">
                                <div className="citation-badge">{index + 1}</div>
                                <div className="citation-main">
                                    <div className="citation-name-row">
                                        {src.url ? <Globe2 size={14} /> : <FileText size={14} />}
                                        <span className="citation-name">{src.label}</span>
                                        {src.url && <ExternalLink size={13} className="citation-link-icon" />}
                                    </div>
                                    <div className="citation-meta-row">
                                        {src.hostname && <span className="citation-meta-pill">{src.hostname}</span>}
                                        {src.chunk_index !== undefined && src.chunk_index !== null && (
                                            <span className="citation-meta-pill">Chunk {src.chunk_index}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            {src.excerpt && (
                                <p className="citation-excerpt">
                                    <Quote size={12} className="citation-excerpt-icon" />
                                    <span>{src.excerpt}</span>
                                </p>
                            )}
                        </>
                    );

                    return src.url ? (
                        <a
                            key={`${src.label}-${index}`}
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="citation-card citation-card-link"
                        >
                            {content}
                        </a>
                    ) : (
                        <div key={`${src.label}-${index}`} className="citation-card" title={src.label}>
                            {content}
                        </div>
                    );
                })}
            </div>
        </section>
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
