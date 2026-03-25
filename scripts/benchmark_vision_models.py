#!/usr/bin/env python3
"""
Benchmark Script untuk Vision Models di Ollama
Mengukur performa OCR dan image analysis
"""

import asyncio
import time
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import subprocess

@dataclass
class BenchmarkResult:
    model: str
    image_path: str
    prompt: str
    success: bool
    processing_time: float
    content: str
    content_length: int
    error: str = None

async def run_ollama_vision(image_path: str, prompt: str, model: str = "llava") -> Dict[str, Any]:
    """Run vision model via Ollama CLI"""
    import base64
    
    # Convert image to base64
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Prepare payload
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    # Write payload to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        payload_file = f.name
    
    try:
        # Call Ollama API
        start_time = time.time()
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:11434/api/generate', 
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(payload)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        processing_time = time.time() - start_time
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return {
                "success": True,
                "content": response.get("response", ""),
                "processing_time": processing_time
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "processing_time": processing_time
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processing_time": time.time() - start_time
        }
    finally:
        Path(payload_file).unlink(missing_ok=True)

async def benchmark_model(
    model: str,
    test_images: List[str],
    prompts: List[str]
) -> List[BenchmarkResult]:
    """Benchmark satu model dengan multiple images dan prompts"""
    results = []
    
    print(f"\n{'='*60}")
    print(f"Benchmarking Model: {model}")
    print(f"{'='*60}")
    
    for image_path in test_images:
        if not Path(image_path).exists():
            print(f"⚠️  Image not found: {image_path}")
            continue
            
        for prompt in prompts:
            print(f"\n🖼️  Image: {Path(image_path).name}")
            print(f"💬 Prompt: {prompt[:60]}...")
            print(f"⏳ Processing...", end=" ", flush=True)
            
            result = await run_ollama_vision(image_path, prompt, model)
            
            benchmark = BenchmarkResult(
                model=model,
                image_path=image_path,
                prompt=prompt,
                success=result["success"],
                processing_time=result["processing_time"],
                content=result.get("content", ""),
                content_length=len(result.get("content", "")),
                error=result.get("error")
            )
            results.append(benchmark)
            
            if benchmark.success:
                print(f"✅ {benchmark.processing_time:.2f}s")
                print(f"📄 Output: {benchmark.content[:100]}...")
            else:
                print(f"❌ Error: {benchmark.error}")
    
    return results

def create_test_image() -> str:
    """Create a simple test image with text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image with text
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use default font, fallback to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        text = """INVOICE #001
Date: 2024-01-15
Vendor: PT Example Indonesia
Total: Rp 1.500.000
Tax: Rp 150.000"""
        
        draw.text((50, 50), text, fill='black', font=font)
        
        # Save
        temp_path = "/tmp/benchmark_test_image.jpg"
        img.save(temp_path)
        return temp_path
        
    except ImportError:
        print("⚠️  PIL not installed, cannot create test image")
        return None
    except Exception as e:
        print(f"⚠️  Failed to create test image: {e}")
        return None

def print_summary(results: List[BenchmarkResult]):
    """Print benchmark summary"""
    print(f"\n\n{'='*60}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*60}\n")
    
    # Group by model
    models = {}
    for r in results:
        if r.model not in models:
            models[r.model] = []
        models[r.model].append(r)
    
    for model, model_results in models.items():
        print(f"\n📊 Model: {model}")
        print(f"{'-'*60}")
        
        successful = [r for r in model_results if r.success]
        failed = [r for r in model_results if not r.success]
        
        print(f"  Total Tests: {len(model_results)}")
        print(f"  Successful: {len(successful)} ✅")
        print(f"  Failed: {len(failed)} ❌")
        
        if successful:
            times = [r.processing_time for r in successful]
            print(f"\n  Processing Time:")
            print(f"    Min: {min(times):.2f}s")
            print(f"    Max: {max(times):.2f}s")
            print(f"    Avg: {sum(times)/len(times):.2f}s")
            
            contents = [r.content_length for r in successful]
            print(f"\n  Output Length:")
            print(f"    Min: {min(contents)} chars")
            print(f"    Max: {max(contents)} chars")
            print(f"    Avg: {sum(contents)//len(contents)} chars")

def save_results(results: List[BenchmarkResult], output_path: str = None):
    """Save benchmark results to JSON"""
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/vision_benchmark_{timestamp}.json"
    
    data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system_info": {
            "cpu": "Intel Core i7-13620H",
            "ram_gb": 10,
            "gpu": "None (CPU-only)"
        },
        "results": [asdict(r) for r in results]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")

async def main():
    print("="*60)
    print("VISION MODEL BENCHMARK")
    print("="*60)
    print(f"System: Intel i7-13620H, 10GB RAM, CPU-only")
    print(f"Ollama Version: ", end="")
    
    # Check Ollama version
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        print(result.stdout.strip() if result.returncode == 0 else "Unknown")
    except:
        print("Unknown")
    
    # Check available models
    print(f"\nChecking available models...")
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Create test image
    test_image = create_test_image()
    if not test_image:
        print("❌ Cannot create test image, exiting")
        return
    
    print(f"\n🖼️  Test image created: {test_image}")
    
    # Define test prompts
    prompts = [
        "Extract all text from this image",
        "Describe the content of this document",
        "What type of document is this? Extract key information."
    ]
    
    # Models to benchmark
    models = ["llava"]  # Will add more if available
    
    # Check if moondream2 is available
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if 'moondream' in result.stdout.lower():
            models.append('moondream2')
            print("✅ Found: moondream2")
    except:
        pass
    
    all_results = []
    
    for model in models:
        results = await benchmark_model(model, [test_image], prompts)
        all_results.extend(results)
    
    # Print summary
    print_summary(all_results)
    
    # Save results
    save_results(all_results)
    
    # Cleanup
    Path(test_image).unlink(missing_ok=True)

if __name__ == "__main__":
    asyncio.run(main())
