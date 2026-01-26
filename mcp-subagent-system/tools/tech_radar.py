import requests
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any

class TechRadarTool:
    """Tool profesional untuk riset teknologi dan tools terbaru"""

    def __init__(self):
        self.hn_api_url = "https://hn.algolia.com/api/v1/search"
        self.github_search_url = "https://api.github.com/search/repositories"

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Mencari referensi dari berbagai sumber dan memberikan skor profesional"""
        
        # Refine query: Indo to English common tech terms
        refined_query = query.lower()
        replacements = {
            "terbaru": "latest",
            "kerangka kerja": "framework",
            "pencarian": "search",
            "kecerdasan buatan": "ai",
            "agen": "agent"
        }
        for k, v in replacements.items():
            refined_query = refined_query.replace(k, v)
        
        # Jalankan pencarian paralel
        hn_results, github_results = await asyncio.gather(
            self._search_hacker_news(refined_query, limit),
            self._search_github(refined_query, limit)
        )
        
        all_results = hn_results + github_results
        
        # Sort berdasarkan tech_score descending
        sorted_results = sorted(all_results, key=lambda x: x.get("tech_score", 0), reverse=True)
        
        return sorted_results[:limit]

    async def _search_hacker_news(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Mencari diskusi tech di Hacker News"""
        try:
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": limit
            }
            response = await asyncio.to_thread(requests.get, self.hn_api_url, params=params, timeout=10)
            if response.status_code != 200:
                return []
            
            hits = response.json().get("hits", [])
            results = []
            for hit in hits:
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)
                
                # Scoring HN: Points + (Comments * 0.5)
                tech_score = points + (comments * 0.5)
                
                results.append({
                    "source": "Hacker News",
                    "title": hit.get("title"),
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "tech_score": round(tech_score, 2),
                    "readiness": "Stable/Community Validated" if points > 100 else "Experimental",
                    "description": f"HN discussion with {points} points and {comments} comments."
                })
            return results
        except Exception as e:
            print(f"Error HN Search: {e}")
            return []

    async def _search_github(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Mencari repository tech di GitHub"""
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            params = {
                "q": f"{query} stars:>10",
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            response = await asyncio.to_thread(requests.get, self.github_search_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            items = response.json().get("items", [])
            results = []
            for item in items:
                stars = item.get("stargazers_count", 0)
                forks = item.get("forks_count", 0)
                
                # Scoring GitHub: (Stars * 0.1) + (Forks * 0.2)
                tech_score = (stars * 0.1) + (forks * 0.2)
                
                results.append({
                    "source": "GitHub",
                    "title": item.get("full_name"),
                    "url": item.get("html_url"),
                    "tech_score": round(tech_score, 2),
                    "readiness": "Stable/Mainstream" if stars > 1000 else "Growing",
                    "description": item.get("description") or "No description provided."
                })
            return results
        except Exception as e:
            print(f"Error GitHub Search: {e}")
            return []

if __name__ == "__main__":
    # Test sederhana
    async def test():
        radar = TechRadarTool()
        results = await radar.search("agentic ai framework")
        print(json.dumps(results, indent=2))
    
    asyncio.run(test())
