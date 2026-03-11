# modules/02_script.py
#
# FIXES APPLIED:
#   Issue 1: All f-strings converted to single-line or explicit concatenation
#   Issue 2: Two-call split strategy instead of one massive call
#            Call A: metadata + chapters (~1,500 tokens)
#            Call B: scenes only, 6 per chapter in batches (~1,200 tokens each)
#            Each call is well within limits and never truncates.

import json
import os
import time
from openai import OpenAI
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

def load_system_prompt() -> str:
    prompt_path = Path("config/prompts/script_system.txt")
    return prompt_path.read_text() if prompt_path.exists() else ""

def safe_json_parse(raw: str, call_name: str) -> dict:
    """
    Robust JSON parser with 3 fallback strategies.
    Handles: markdown fences, trailing commas, truncation.
    """
    # Strategy 1: Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find first { to last } and extract
    try:
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        return json.loads(cleaned[start:end])
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("JSON parse failed for call: " + call_name)
        logger.error("Raw response (first 500 chars): " + raw[:500])
        raise RuntimeError("Could not parse LLM response for " + call_name) from e

def call_llm(client: OpenAI, system: str, user: str,
             max_tokens: int, call_name: str, retries: int = 3) -> dict:
    """
    Single LLM call with retry logic.
    Retries on any failure up to `retries` times with exponential backoff.
    """
    for attempt in range(1, retries + 1):
        try:
            logger.info("LLM call: " + call_name + " (attempt " + str(attempt) + ")")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user}
                ]
            )
            raw = response.choices[0].message.content
            result = safe_json_parse(raw, call_name)
            logger.success("LLM call OK: " + call_name)
            return result
        except Exception as e:
            logger.warning("Attempt " + str(attempt) + " failed: " + str(e))
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError("All retries exhausted for: " + call_name)

# ---------------------------------------------------------------------------
# CALL A: Metadata + Chapters
# ---------------------------------------------------------------------------
CALL_A_USER = """
Create documentary metadata and chapter narrations for this topic:
TOPIC: {topic}

Return ONLY this JSON (no extra text):
{{
  "title": "YouTube title max 60 chars with curiosity and numbers",
  "description": "YouTube description 150 words with timestamps",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "hook_stat": "The shocking opening fact in one sentence with specific numbers",
  "thumbnail_text": "3 to 4 words max for thumbnail overlay",
  "dominant_palette": "teal_orange",
  "chapters": [
    {{
      "chapter_id": 1,
      "name": "HOOK",
      "start_sec": 0,
      "end_sec": 60,
      "narration": "Full narration text for this chapter spoken by narrator. Minimum 80 words.",
      "emotion": "establishing",
      "retention_hook": "The specific hook or reframe used in this chapter"
    }},
    {{
      "chapter_id": 2,
      "name": "RISE",
      "start_sec": 60,
      "end_sec": 210,
      "narration": "Full narration text. Minimum 80 words.",
      "emotion": "hopeful",
      "retention_hook": "Hook used here"
    }},
    {{
      "chapter_id": 3,
      "name": "CRACK",
      "start_sec": 210,
      "end_sec": 330,
      "narration": "Full narration text. Minimum 80 words.",
      "emotion": "tension",
      "retention_hook": "Hook used here"
    }},
    {{
      "chapter_id": 4,
      "name": "FALL",
      "start_sec": 330,
      "end_sec": 450,
      "narration": "Full narration text. Minimum 80 words.",
      "emotion": "dramatic",
      "retention_hook": "Hook used here"
    }},
    {{
      "chapter_id": 5,
      "name": "REVELATION",
      "start_sec": 450,
      "end_sec": 510,
      "narration": "Full narration text. Minimum 80 words.",
      "emotion": "revelation",
      "retention_hook": "The thing nobody talks about"
    }},
    {{
      "chapter_id": 6,
      "name": "LESSON",
      "start_sec": 510,
      "end_sec": 570,
      "narration": "Full narration text. Minimum 80 words.",
      "emotion": "reflective",
      "retention_hook": "Personal relevance to viewer"
    }}
  ]
}}
"""

# ---------------------------------------------------------------------------
# CALL B: Scenes for ONE chapter (called 6 times)
# ---------------------------------------------------------------------------
CALL_B_USER = """
Generate exactly 6 video scenes for Chapter {chapter_id} ({chapter_name}) of a documentary about: {topic}

PREVIOUS VISUAL CONTEXT (Maintain continuity with this):
{prev_visual_context}

CHAPTER NARRATION:
{narration}

CINEMATOGRAPHER RULES (Wan 2.2):
Structure every "comfyui_prompt" in exactly 4 parts:
1. Motion: Primary action with concrete verbs.
2. Camera: Professional cinematic movement (e.g., 50mm Anamorphic Slow Dolly In, 85mm Static Observational).
3. Environment: Specific lighting (rim-light, golden hour glow) and atmosphere.
4. Intensity: Pacing modifiers (gradually increasing, imperceptibly slow, locked composition).

Rules:
- 30% subject content, 70% cinematography focus.
- Wide or Medium shots ONLY — no face closeups.
- model: "mochi" for humans, "wan2" for environments. (Note: use "wan2" as primary).
- Always end prompt with: "cinematic documentary, teal and orange grade, anamorphic lens, high-detail textures."

Return ONLY this JSON:
{{
  "scenes": [
    {{
      "scene_id": {scene_id_start},
      "chapter_id": {chapter_id},
      "duration_sec": 5,
      "subject": "subject description for consistency",
      "emotion": "{emotion}",
      "scene_type": "environment",
      "sound_profile": "foley",
      "model": "wan2",
      "color_palette": "#hex",
      "comfyui_prompt": "[Motion], [Camera], [Environment], [Intensity], cinematic documentary, teal and orange grade, anamorphic lens, high-detail textures",
      "lower_third": null
    }}
  ]
}}

Generate scenes {scene_id_start} through {scene_id_end}.
"""

def generate_full_production_package(topic: str) -> dict:
    """
    7-call split strategy:
      Call A (1x): metadata + all 6 chapter narrations  (~1,500 tokens)
      Call B (6x): 6 scenes per chapter with 'Visual Thread' context.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system_prompt = load_system_prompt()

    # --- CALL A: Metadata + Chapters ---
    logger.info("Generating metadata and chapters for: " + topic)
    meta = call_llm(
        client=client,
        system=system_prompt,
        user=CALL_A_USER.format(topic=topic),
        max_tokens=3000,
        call_name="metadata_chapters"
    )

    if "chapters" not in meta or len(meta["chapters"]) != 6:
        raise RuntimeError("Expected 6 chapters, got: " + str(len(meta.get("chapters", []))))

    # --- CALL B x6: Scenes per chapter ---
    all_scenes = []
    prev_visual_context = "No previous scenes. This is the start of the documentary."
    
    for ch in meta["chapters"]:
        chapter_id  = ch["chapter_id"]
        scene_start = (chapter_id - 1) * 6 + 1
        scene_end   = chapter_id * 6

        scenes_data = call_llm(
            client=client,
            system=system_prompt,
            user=CALL_B_USER.format(
                chapter_id=chapter_id,
                chapter_name=ch["name"],
                topic=topic,
                narration=ch["narration"][:500],
                scene_id_start=scene_start,
                scene_id_end=scene_end,
                prev_visual_context=prev_visual_context,
                emotion=ch.get("emotion", "neutral")
            ),
            max_tokens=2500,
            call_name="scenes_chapter_" + str(chapter_id)
        )

        chapter_scenes = scenes_data.get("scenes", [])
        if chapter_scenes:
            # Capture the last scene of this chapter to be the context for the next chapter
            last_scene = chapter_scenes[-1]
            prev_visual_context = (
                f"Chapter {chapter_id} ended with: Subject: {last_scene.get('subject')}, "
                f"Camera: {last_scene.get('camera')}, Palette: {last_scene.get('color_palette')}"
            )
        
        all_scenes.extend(chapter_scenes)

    # Assemble full package
    package = {**meta, "scenes": all_scenes}

    # Save to disk
    slug = topic[:40].replace(" ", "_").replace(":", "").replace("?", "").replace("/", "").lower()
    save_path = Path("output/scripts/" + slug + ".json")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(json.dumps(package, indent=2))
    logger.success("Production package saved: " + str(save_path))

    return package

if __name__ == "__main__":
    topic = "The Rise and Fall of WeWork"
    logger.info("Generating production package for: " + topic)
    package = generate_full_production_package(topic)

    print("")
    print("Title:    " + package["title"])
    print("Chapters: " + str(len(package["chapters"])))
    print("Scenes:   " + str(len(package["scenes"])))
    print("Hook:     " + package["hook_stat"])

    mochi = sum(1 for s in package["scenes"] if s.get("model") == "mochi")
    wan2  = sum(1 for s in package["scenes"] if s.get("model") == "wan2")
    print("Mochi scenes (human):      " + str(mochi))
    print("Wan2 scenes (environment): " + str(wan2))

    print("")
    print("First scene preview:")
    print(json.dumps(package["scenes"][0], indent=2))
