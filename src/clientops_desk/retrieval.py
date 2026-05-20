from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from clientops_desk.config import settings
from clientops_desk.schemas import ClientRequest


def _case_document(case: dict[str, Any]) -> str:
    parts = [
        case.get('title', ''),
        case.get('category', ''),
        case.get('symptoms', ''),
        case.get('previous_resolution', ''),
        ' '.join(case.get('keywords', [])),
    ]
    return ' '.join(parts)

@lru_cache(maxsize=1)
def _index() -> tuple[list[dict[str, Any]], TfidfVectorizer, Any]:
    cases: list[dict[str, Any]] = []
    with Path(settings.knowledge_path).open('r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform([_case_document(case) for case in cases])
    return cases, vectorizer, matrix


def search_similar_cases(issue: ClientRequest, top_k: int = 3) -> list[dict[str, Any]]:
    cases, vectorizer, matrix = _index()
    query = ' '.join([issue.subject, issue.message, ' '.join(str(v) for v in issue.metadata.values())])
    scores = cosine_similarity(vectorizer.transform([query]), matrix).flatten()
    ranked_indices = scores.argsort()[::-1][:top_k]
    results: list[dict[str, Any]] = []
    for idx in ranked_indices:
        case = cases[int(idx)]
        score = float(scores[int(idx)])
        results.append({
            'case_id': case['case_id'],
            'title': case['title'],
            'category': case['category'],
            'score': round(score, 4),
            'previous_resolution': case['previous_resolution'],
            'why_relevant': case['why_relevant'],
        })
    return results
