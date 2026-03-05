"""
Phase 1 Dry Run
Runs: Intelligence → Script → prints full production plan
Cost: ~$0.06 total
No GPU required.
"""
import json
import sys
import os
import importlib.util

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

def import_module_by_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load modules using absolute paths to avoid digit-start issues in normal imports
intelligence = import_module_by_path("intelligence", os.path.join(project_root, "modules", "01_intelligence.py"))
script = import_module_by_path("script", os.path.join(project_root, "modules", "02_script.py"))

from loguru import logger

def run_phase1_test():
    logger.info("=" * 50)
    logger.info("PHASE 1 DRY RUN STARTING")
    logger.info("=" * 50)

    # Test 1: Intelligence (scan 1 channel only to save time)
    logger.info("TEST 1: Intelligence Module")
    # Using the first channel from the module's own list
    outliers = intelligence.find_outlier_topics([intelligence.COMPETITOR_CHANNELS[0]])  # just one channel
    logger.success(f"Found {len(outliers)} outlier videos")
    assert len(outliers) > 0, "No outliers found - check yt-dlp"

    # Test 2: LLM ranking
    logger.info("TEST 2: LLM Topic Ranking")
    ranked = intelligence.rank_topics_with_llm(outliers, count=5)
    top_topic = ranked['ranked_topics'][0]['title']
    logger.success(f"Top topic: {top_topic}")

    # Test 3: Full production package
    logger.info("TEST 3: Production Package Generation")
    package = script.generate_full_production_package(top_topic)
    assert len(package['scenes']) > 0, "No scenes generated"
    assert len(package['chapters']) == 6, "Should have 6 chapters"
    logger.success(f"Generated {len(package['scenes'])} scenes for: {package['title']}")

    # Summary
    print("\n" + "=" * 50)
    print("PHASE 1 DRY RUN COMPLETE")
    print("=" * 50)
    print(f"Topic: {package['title']}")
    print(f"Hook: {package['hook_stat']}")
    print(f"Scenes: {len(package['scenes'])}")
    print(f"Chapters: {len(package['chapters'])}")
    mochi = sum(1 for s in package['scenes'] if s.get('model') == 'mochi')
    wan2 = sum(1 for s in package['scenes'] if s.get('model') == 'wan2')
    print(f"Mochi clips: {mochi} | Wan2 clips: {wan2}")
    print("\n✅ ALL PHASE 1 TESTS PASSED")
    print("Ready for Phase 2: First GPU contact")

if __name__ == "__main__":
    run_phase1_test()
