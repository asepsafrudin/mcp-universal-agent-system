#!/usr/bin/env python3
"""
Production Extraction Script

Real website extraction dengan auto-save ke Knowledge Base.
Usage: python3 run_production_extraction.py --source hukumonline --save
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Root repo MCP (parent dari scripts/)
MCP_ROOT = Path(__file__).resolve().parent.parent
AGENTIC_AI_PATH = MCP_ROOT / "mcp-unified" / "integrations" / "agentic_ai"

# Output JSON ekstraksi (bukan cwd) — selaras dengan cleanup root & storage operasional
DEFAULT_EXTRACTION_OUTPUT_DIR = MCP_ROOT / "storage" / "reports" / "extractions"

# Ensure agentic_ai is in path so we can import 'extractors'
if str(AGENTIC_AI_PATH) not in sys.path:
    sys.path.insert(0, str(AGENTIC_AI_PATH))
if str(MCP_ROOT / "mcp-unified") not in sys.path:
    sys.path.insert(0, str(MCP_ROOT / "mcp-unified"))

try:
    from extractors import HukumonlineExtractor, JDIHExtractor
except ImportError:
    # Fallback jika masih gagal
    sys.path.insert(0, str(AGENTIC_AI_PATH))
    from extractors import HukumonlineExtractor, JDIHExtractor

from knowledge_bridge_integration import ExtractorKnowledgeBridge
from extractor_registry import get_registry


# Configuration
SOURCES = {
    "hukumonline": {
        "url": "https://www.hukumonline.com/berita",
        "extractor": HukumonlineExtractor,
        "name": "hukumonline"
    },
    "jdih": {
        "url": "https://jdihn.go.id",
        "extractor": JDIHExtractor,
        "name": "jdih"
    }
}


def _infer_source_from_filename(path: Path) -> Optional[str]:
    """Infer source key dari nama file extraction_*.json bila JSON tanpa field source."""
    stem = path.stem.lower()
    if "jdih" in stem:
        return "jdih"
    if "hukumonline" in stem:
        return "hukumonline"
    return None


async def _ingest_one_json_file(path: Path, namespace: str) -> Optional[Dict[str, Any]]:
    """Muat satu file JSON ekstraksi dan simpan ke Knowledge Base."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results")
    if not isinstance(results, list):
        print(f"❌ {path}: key 'results' harus berupa list")
        return None

    source = data.get("source") or _infer_source_from_filename(path)
    if not source:
        print(f"❌ {path}: tentukan 'source' di JSON atau gunakan nama file berisi jdih/hukumonline")
        return None

    base_url = data.get("url") or ""
    print(f"\n📥 Ingest: {path.name} → source={source}, items={len(results)}, namespace={namespace}")

    kb = ExtractorKnowledgeBridge()
    summary = await kb.save_extraction_results(
        results=results,
        source=source,
        url=base_url,
        namespace=namespace,
    )

    print(f"   ✅ Saved: {summary['saved']}  ⏭️ Skipped: {summary['skipped']}  ❌ Errors: {summary['errors']}")
    return summary


async def ingest_extraction_paths(paths: List[Path], namespace: str) -> None:
    """File atau direktori (semua *.json) ke Knowledge Base."""
    grand = {"saved": 0, "skipped": 0, "errors": 0, "total": 0, "files": 0}

    for raw in paths:
        p = raw.resolve()
        if not p.exists():
            print(f"❌ Tidak ditemukan: {p}")
            continue

        if p.is_dir():
            files = sorted(p.glob("*.json"))
            if not files:
                print(f"❌ Tidak ada *.json di {p}")
                continue
            for f in files:
                r = await _ingest_one_json_file(f, namespace)
                if r:
                    grand["saved"] += r["saved"]
                    grand["skipped"] += r["skipped"]
                    grand["errors"] += r["errors"]
                    grand["total"] += r.get("total", 0)
                    grand["files"] += 1
        else:
            r = await _ingest_one_json_file(p, namespace)
            if r:
                grand["saved"] += r["saved"]
                grand["skipped"] += r["skipped"]
                grand["errors"] += r["errors"]
                grand["total"] += r.get("total", 0)
                grand["files"] += 1

    print("\n" + "=" * 70)
    print("📊 RINGKASAN INGEST JSON")
    print("=" * 70)
    print(f"   File diproses: {grand['files']}")
    print(f"   ✅ Saved: {grand['saved']}  ⏭️ Skipped: {grand['skipped']}  ❌ Errors: {grand['errors']}")
    print("=" * 70)


async def extract_from_source(
    source_key: str,
    save_to_kb: bool = False,
    output_dir: Optional[Path] = None,
    namespace: str = "legal_regulations",
):
    """
    Extract data dari source tertentu.
    
    Args:
        source_key: Key dari SOURCES dict
        save_to_kb: Save ke knowledge base?
        output_dir: Direktori untuk file JSON hasil (default: storage/reports/extractions)
    """
    out = Path(output_dir) if output_dir is not None else DEFAULT_EXTRACTION_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    if source_key not in SOURCES:
        print(f"❌ Unknown source: {source_key}")
        print(f"Available: {', '.join(SOURCES.keys())}")
        return None
    
    config = SOURCES[source_key]
    url = config["url"]
    extractor_class = config["extractor"]
    source_name = config["name"]
    
    print("\n" + "="*70)
    print(f"🚀 PRODUCTION EXTRACTION: {source_name.upper()}")
    print("="*70)
    print(f"📡 URL: {url}")
    print(f"💾 Save to KB: {save_to_kb}")
    print("="*70)
    
    extractor = extractor_class()
    summary = {"saved": 0, "skipped": 0, "errors": 0, "total": 0}
    
    from integrations.web_scraping import GenericBrowserBridge
    
    async with GenericBrowserBridge(headless=True, stealth_mode=True) as browser:
        try:
            # Navigate
            print(f"\n⏳ Loading page with stealth bridge...")
            page = await browser.navigate(url, wait_until="domcontentloaded")
            print(f"✅ Page loaded")
            
            # Pre-process
            print(f"⏳ Pre-processing (scroll & wait)...")
            await extractor.pre_process(page)
            
            # Extract
            print(f"🔍 Extracting data...")
            results = await extractor.extract(page)
            results = await extractor.post_process(results)
            
            # Filter out "Security Verification" content if any
            results = [r for r in results if "security verification" not in r.get('title', '').lower()]
            
            print(f"✅ Extracted: {len(results)} items")
            
            # Show sample
            if results:
                print(f"\n📋 Sample Results (first 3):")
                for i, item in enumerate(results[:3], 1):
                    title = item.get('title', 'N/A')[:70]
                    url_item = item.get('url', 'N/A')[:50]
                    print(f"   {i}. {title}")
                    print(f"      → {url_item}")
                    print()
            
            # Save to knowledge base
            if save_to_kb and results:
                print(f"💾 Saving to Knowledge Base...")
                kb = ExtractorKnowledgeBridge()
                summary = await kb.save_extraction_results(
                    results=results,
                    source=source_name,
                    url=url,
                    namespace=namespace,
                )
                
                print(f"\n📊 Save Summary:")
                print(f"   ✅ Saved: {summary['saved']}")
                print(f"   ⏭️  Skipped: {summary['skipped']}")
                print(f"   ❌ Errors: {summary['errors']}")
                print(f"   📊 Total: {summary['total']}")
            
            # Save to file (path tetap, tidak bergantung pada cwd)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extraction_{source_name}_{timestamp}.json"
            out_path = out / filename

            payload = {
                "source": source_name,
                "url": url,
                "timestamp": timestamp,
                "count": len(results),
                "output_path": str(out_path),
                "results": results,
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            print(f"💾 Results saved to: {out_path}")
            
            return {
                "source": source_name,
                "count": len(results),
                "saved": summary['saved'],
                "file": str(out_path),
            }
            
        except Exception as e:
            print(f"\n❌ Error during extraction from {source_name}: {e}")
            import traceback
            # traceback.print_exc()
            return None


async def extract_all_sources(
    save_to_kb: bool = False,
    output_dir: Optional[Path] = None,
    namespace: str = "legal_regulations",
):
    """Extract dari semua sources"""
    print("\n" + "="*70)
    print("🚀 BATCH EXTRACTION: ALL SOURCES")
    print("="*70)
    
    results = []
    for source_key in SOURCES.keys():
        result = await extract_from_source(
            source_key, save_to_kb, output_dir=output_dir, namespace=namespace
        )
        if result:
            results.append(result)
        print("\n" + "-"*70)
    
    # Summary
    print("\n" + "="*70)
    print("📊 BATCH SUMMARY")
    print("="*70)
    for r in results:
        print(f"   {r['source']:15} → {r['count']:3} items (saved: {r['saved']})")
    print(f"\n   Total: {sum(r['count'] for r in results)} items")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Production Extraction Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/run_production_extraction.py --source hukumonline
  python3 scripts/run_production_extraction.py --source hukumonline --save
  python3 scripts/run_production_extraction.py --all --save --namespace legal_regulations
  python3 scripts/run_production_extraction.py --ingest-json storage/reports/extractions
  python3 scripts/run_production_extraction.py --ingest-json storage/reports/extractions/extraction_jdih_20260401_060027.json
        """
    )
    
    parser.add_argument(
        "--source",
        choices=list(SOURCES.keys()),
        help="Source to extract from"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract from all sources"
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to Knowledge Base"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_EXTRACTION_OUTPUT_DIR,
        help=(
            "Direktori untuk menyimpan file JSON ekstraksi "
            f"(default: {DEFAULT_EXTRACTION_OUTPUT_DIR})"
        ),
    )

    parser.add_argument(
        "--namespace",
        default="legal_regulations",
        help="Namespace pgvector untuk --save dan --ingest-json",
    )

    parser.add_argument(
        "--ingest-json",
        action="append",
        dest="ingest_json_paths",
        metavar="PATH",
        help=(
            "Impor file JSON hasil ekstraksi (atau direktori berisi *.json) ke Knowledge Base. "
            "Bisa dipanggil beberapa kali."
        ),
    )
    
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()

    if args.ingest_json_paths and (args.all or args.source):
        parser.error("Jangan gabungkan --ingest-json dengan --source atau --all")

    if args.ingest_json_paths:
        paths = [Path(p) for p in args.ingest_json_paths]
        asyncio.run(ingest_extraction_paths(paths, args.namespace))
    elif args.all:
        asyncio.run(extract_all_sources(args.save, output_dir=out_dir, namespace=args.namespace))
    elif args.source:
        asyncio.run(
            extract_from_source(args.source, args.save, output_dir=out_dir, namespace=args.namespace)
        )
    else:
        parser.print_help()
        print("\n❌ Gunakan --source, --all, atau --ingest-json")


if __name__ == "__main__":
    main()
