"""
Yuga Evolution Generator Service

Generates Yuga-based evolution for ideas/innovations using OpenRouter API.
Maps modern ideas to their symbolic evolution across the four Yugas:
- Satya Yuga (Golden Age)
- Treta Yuga (Silver Age)
- Dwapar Yuga (Bronze Age)
- Kali Yuga (Iron Age/Modern Era)
"""

import re
import os
import json
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional


# Wikipedia requires a descriptive User-Agent or it returns 403
WIKI_HEADERS = {
    "User-Agent": "YugaEvolutionTracker/1.0 (educational project)"
}

# Hard cap on how long image fetching is allowed to take
IMAGE_FETCH_TIMEOUT_SECS = 8


class YugaGeneratorService:
    """Service for generating Yuga-based evolution narratives."""

    def __init__(self):
        self.api_key = os.getenv(
            "OPENAI_API_KEY",
            "YOUR_OPENAI_API_KEY"
        )
        self.model = "gpt-3.5-turbo"
        # Fallback chain — tried in order if primary is rate-limited (429)
        self.fallback_models = [
            "gpt-3.5-turbo",
            "gpt-4o-mini",
        ]
        self.api_url = "https://api.openai.com/v1/chat/completions"

    # ------------------------------------------------------------------ #
    #  Wikipedia / Wikimedia helpers                                       #
    # ------------------------------------------------------------------ #

    def fetch_wikipedia_info(self, topic: str) -> Dict:
        """
        Fetch summary + thumbnail for a topic from Wikipedia REST API.
        Returns: {title, description, image_url, wiki_url}
        """
        try:
            url = (
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + topic.replace(" ", "_")
            )
            r = requests.get(url, headers=WIKI_HEADERS, timeout=4)
            if r.status_code == 200:
                data = r.json()
                return {
                    "title": data.get("title", topic),
                    "description": data.get("extract", "")[:400],
                    "image_url": (data.get("thumbnail") or {}).get("source", ""),
                    "wiki_url": (
                        data.get("content_urls", {})
                            .get("desktop", {})
                            .get("page", "")
                    ),
                }
        except Exception as e:
            print(f"Wikipedia fetch error for '{topic}': {e}")
        return {"title": topic, "description": "", "image_url": "", "wiki_url": ""}

    def _fetch_images_worker(self, idea_name: str, result_holder: list) -> None:
        """
        Worker that fetches images and stores them in result_holder[0].
        Runs inside a thread so it can be killed by a timeout.
        """
        image_urls: List[str] = []
        base = "https://en.wikipedia.org/w/api.php"
        commons_base = "https://commons.wikimedia.org/w/api.php"

        try:
            # 1. Find the top 3 matching Wikipedia pages to broaden image pool
            r = requests.get(base, headers=WIKI_HEADERS, params={
                "action": "query", "list": "search",
                "srsearch": idea_name, "srlimit": 3, "format": "json",
            }, timeout=4)
            
            page_titles = []
            if r.status_code == 200:
                results = r.json().get("query", {}).get("search", [])
                page_titles = [res["title"] for res in results]

            image_titles = []
            skip_words = [
                "flag", "icon", "logo", "symbol", "commons-logo",
                "wikidata", "edit", ".svg", "map", "electoral",
                "election", "stamp", "coat_of_arms", "seal_of",
                "portrait", "signature", "autograph", "medal",
                "ribbon", "badge", "emblem", "banner", "chart",
                "diagram", "graph", "table", "census", "vote",
                "political", "district", "blank", "stub", "button"
            ]

            # 2. Get image file names from these pages combined
            for page_title in page_titles:
                try:
                    r2 = requests.get(base, headers=WIKI_HEADERS, params={
                        "action": "query", "titles": page_title,
                        "prop": "images", "imlimit": 20, "format": "json",
                    }, timeout=4)
                    if r2.status_code == 200:
                        for page in r2.json().get("query", {}).get("pages", {}).values():
                            for img in page.get("images", []):
                                title = img.get("title", "")
                                lower = title.lower()
                                if any(s in lower for s in skip_words):
                                    continue
                                if any(lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                                    if title not in image_titles:
                                        image_titles.append(title)
                except Exception:
                    continue

            # 3. Resolve file names → direct URLs (IN PARALLEL for speed)
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def _resolve_image_url(img_title):
                """Resolve a single image title to its direct URL."""
                try:
                    r3 = requests.get(base, headers=WIKI_HEADERS, params={
                        "action": "query", "titles": img_title,
                        "prop": "imageinfo", "iiprop": "url|size", "format": "json",
                    }, timeout=4)
                    if r3.status_code == 200:
                        for p in r3.json().get("query", {}).get("pages", {}).values():
                            for info in p.get("imageinfo", []):
                                url = info.get("url", "")
                                w = info.get("width", 0)
                                h = info.get("height", 0)
                                if url and w >= 200 and h >= 150:
                                    return url
                except Exception:
                    pass
                return None
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(_resolve_image_url, t): t for t in image_titles[:8]}
                for future in as_completed(futures):
                    if len(image_urls) >= 4:
                        break
                    url = future.result()
                    if url and url not in image_urls:
                        image_urls.append(url)

            # 4. Fallback/Augmentation: Directly search Wikimedia Commons files if we need more images
            if len(image_urls) < 4:
                try:
                    cr = requests.get(commons_base, headers=WIKI_HEADERS, params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": f"filetype:bitmap {idea_name}",
                        "gsrnamespace": 6,  # File namespace
                        "gsrlimit": 10,
                        "prop": "imageinfo",
                        "iiprop": "url|size",
                        "format": "json"
                    }, timeout=4)
                    if cr.status_code == 200:
                        pages = cr.json().get("query", {}).get("pages", {}).values()
                        for p in pages:
                            if len(image_urls) >= 4:
                                break
                            title = p.get("title", "").lower()
                            if any(s in title for s in skip_words):
                                continue
                            for info in p.get("imageinfo", []):
                                url = info.get("url", "")
                                w = info.get("width", 0)
                                h = info.get("height", 0)
                                if url and w >= 200 and h >= 150 and url not in image_urls:
                                    image_urls.append(url)
                except Exception as ce:
                    print(f"Commons direct search error: {ce}")

        except Exception as e:
            print(f"Image fetch error for '{idea_name}': {e}")

        result_holder[0] = image_urls

    def fetch_images_for_idea(self, idea_name: str) -> List[str]:
        """
        Fetch up to 4 Wikimedia image URLs with a hard wall-clock timeout.
        Returns empty list if the fetch takes longer than IMAGE_FETCH_TIMEOUT_SECS.
        """
        result_holder = [None]
        t = threading.Thread(
            target=self._fetch_images_worker,
            args=(idea_name, result_holder),
            daemon=True,
        )
        t.start()
        t.join(timeout=IMAGE_FETCH_TIMEOUT_SECS)
        if result_holder[0] is None:
            print(f"Image fetch timed out for '{idea_name}' — skipping images")
            return []
        return result_holder[0]

    def fetch_images_by_yuga(self, idea_name: str) -> Dict[str, Dict]:
        """
        Fetch images organized by Yuga stages.
        Each Yuga gets images that represent that era's version of the idea.
        
        Returns:
        {
            "satya_yuga": {"url": "...", "alt": "...", "source": "..."},
            "treta_yuga": {"url": "...", "alt": "...", "source": "..."},
            "dwapar_yuga": {"url": "...", "alt": "...", "source": "..."},
            "kali_yuga": {"url": "...", "alt": "...", "source": "..."}
        }
        """
        yuga_images = {}
        
        # Map Yugas to search terms that represent that era
        yuga_search_terms = {
            "satya_yuga": f"{idea_name} ancient golden age divine",
            "treta_yuga": f"{idea_name} classical mythology spiritual",
            "dwapar_yuga": f"{idea_name} medieval traditional",
            "kali_yuga": f"{idea_name} modern contemporary technology"
        }
        
        for yuga, search_term in yuga_search_terms.items():
            try:
                # Fetch images for this specific Yuga interpretation
                images = self._fetch_images_for_yuga_stage(search_term, yuga)
                if images:
                    yuga_images[yuga] = images[0]  # Take first image
                else:
                    # Fallback to placeholder
                    yuga_images[yuga] = self._get_yuga_placeholder(idea_name, yuga)
            except Exception as e:
                print(f"Error fetching images for {yuga}: {e}")
                yuga_images[yuga] = self._get_yuga_placeholder(idea_name, yuga)
        
        return yuga_images

    def _fetch_images_for_yuga_stage(self, search_term: str, yuga: str) -> List[Dict]:
        """
        Fetch images for a specific Yuga stage with themed search.
        """
        images = []
        base = "https://en.wikipedia.org/w/api.php"
        
        try:
            # Search for pages matching the Yuga-specific term
            r = requests.get(base, headers=WIKI_HEADERS, params={
                "action": "query", "list": "search",
                "srsearch": search_term, "srlimit": 3, "format": "json",
            }, timeout=8)
            
            if r.status_code != 200:
                return images
            
            results = r.json().get("query", {}).get("search", [])
            
            for result in results[:2]:  # Try first 2 results
                page_title = result["title"]
                
                # Get images from this page
                r2 = requests.get(base, headers=WIKI_HEADERS, params={
                    "action": "query", "titles": page_title,
                    "prop": "images", "imlimit": 10, "format": "json",
                }, timeout=8)
                
                if r2.status_code != 200:
                    continue
                
                image_titles = []
                for page in r2.json().get("query", {}).get("pages", {}).values():
                    for img in page.get("images", []):
                        title = img.get("title", "")
                        lower = title.lower()
                        # Filter out non-content images
                        if any(s in lower for s in [
                            "flag", "icon", "logo", "symbol", "map",
                            "commons-logo", "wikidata", "edit", ".svg"
                        ]):
                            continue
                        if any(lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                            image_titles.append(title)
                
                # Get URLs for these images
                for img_title in image_titles[:5]:
                    if len(images) >= 1:
                        break
                    try:
                        r3 = requests.get(base, headers=WIKI_HEADERS, params={
                            "action": "query", "titles": img_title,
                            "prop": "imageinfo", "iiprop": "url|size", "format": "json",
                        }, timeout=8)
                        
                        if r3.status_code != 200:
                            continue
                        
                        for p in r3.json().get("query", {}).get("pages", {}).values():
                            for info in p.get("imageinfo", []):
                                url = info.get("url", "")
                                w = info.get("width", 0)
                                h = info.get("height", 0)
                                if url and w >= 200 and h >= 150:
                                    images.append({
                                        "url": url,
                                        "alt": f"{img_title} from {page_title}",
                                        "source": "Wikimedia Commons"
                                    })
                    except Exception:
                        continue
                
                if images:
                    break
        
        except Exception as e:
            print(f"Error in _fetch_images_for_yuga_stage: {e}")
        
        return images

    def _get_yuga_placeholder(self, idea_name: str, yuga: str) -> Dict:
        """
        Get a themed placeholder image for a Yuga stage.
        Uses placehold.co with Yuga-specific colors.
        """
        yuga_colors = {
            "satya_yuga": {"bg": "FFD700", "text": "000000", "name": "Golden Age"},
            "treta_yuga": {"bg": "C0C0C0", "text": "000000", "name": "Silver Age"},
            "dwapar_yuga": {"bg": "CD7F32", "text": "FFFFFF", "name": "Bronze Age"},
            "kali_yuga": {"bg": "2F4F4F", "text": "FFFFFF", "name": "Iron Age"}
        }
        
        style = yuga_colors.get(yuga, {"bg": "CCCCCC", "text": "666666", "name": "Unknown"})
        text = f"{idea_name}%20{style['name']}".replace(" ", "%20")
        
        return {
            "url": f"https://placehold.co/800x600/{style['bg']}/{style['text']}?text={text}",
            "alt": f"{idea_name} in {yuga.replace('_', ' ').title()}",
            "source": "Placeholder"
        }

    # ------------------------------------------------------------------ #
    #  LLM generation                                                      #
    # ------------------------------------------------------------------ #

    def _parse_llm_response(self, content: str) -> Optional[Dict]:
        """
        Robustly parse the LLM response into a 4-Yuga dict.

        Attempt 1 — direct json.loads on the {...} block
        Attempt 2 — sanitize control chars, retry
        Attempt 3 — extract each Yuga field individually via regex
        """
        content = re.sub(r"```(?:json)?", "", content).strip()
        m = re.search(r"\{.*\}", content, re.DOTALL)

        # Attempt 1: direct parse
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

        # Attempt 2: strip control chars
        if m:
            try:
                sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', m.group(0))
                return json.loads(sanitized)
            except json.JSONDecodeError:
                pass

        # Attempt 3: per-field regex extraction
        result = {}
        for yuga in ["satya_yuga", "treta_yuga", "dwapar_yuga", "kali_yuga"]:
            yuga_block = {}
            yuga_match = re.search(
                rf'"{yuga}"\s*:\s*\{{([^{{}}]*)\}}', content, re.DOTALL
            )
            if yuga_match:
                block_text = yuga_match.group(1)
                for field in ["description", "statistics", "characteristics", "impact"]:
                    fm = re.search(
                        rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"',
                        block_text, re.DOTALL
                    )
                    if fm:
                        val = fm.group(1)
                        val = val.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                        yuga_block[field] = val
                    else:
                        yuga_block[field] = ""
            if yuga_block:
                result[yuga] = yuga_block

        if len(result) == 4:
            print("LLM response recovered via per-field extraction")
            return result

        return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """
        Make a direct call to Google Gemini API using gemini-2.5-flash.
        """
        try:
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
            if not api_key:
                return None
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[WARN] Gemini Yuga generation failed: {e}")
        return None

    def _call_llm(self, prompt: str, model: str) -> Optional[str]:
        """
        Make a single LLM call. Returns the content string or None.
        Raises a ValueError with 'RATE_LIMITED' if the model returns 429.
        """
        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Yuga Evolution Tracker",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2500,
            },
            timeout=60,
        )
        if response.status_code == 429:
            raise ValueError("RATE_LIMITED")
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        print(f"LLM API error {response.status_code} ({model}): {response.text[:150]}")
        return None

    def generate_yuga_evolution(
        self, idea_name: str, description: str, rich_content: bool = True
    ) -> Dict:
        """
        Call Google Gemini API or OpenRouter LLM to generate 4-Yuga evolution for an idea.
        Tries Google Gemini first, then OpenRouter models on failure/429, then fallback template.
        """
        # Define prompt first
        prompt = f"""You are a master creative historian, visionary philosopher, and expert technologist writing a captivating, highly original evolutionary encyclopedia.

Topic: **{idea_name}**
Context: {description}
""" + """
Write a deeply engaging, custom-tailored evolution of "{idea_name}" across the four Hindu cosmic ages (Yugas).
CRITICAL REQUIREMENT: Avoid repetitive, formulaic, or identical phrasing. Ensure every sentence is uniquely customized to the specific concept, history, and physical mechanics of "{idea_name}".

Rules:
- Deep Concept Integration: Clearly explain how the core mechanics and essence of "{idea_name}" operated in each cosmic era.
- Structure: Provide exactly 4 detailed paragraphs per Yuga, separated by double newlines:
  Paragraph 1: Conceptual Manifestation — what unique form or precursor did "{idea_name}" take in this era?
  Paragraph 2: Practical Methodology — specific tools, energies, rituals, or mechanisms utilized by practitioners.
  Paragraph 3: Era Limitations — real conceptual, physical, or philosophical barriers faced.
  Paragraph 4: Cosmic & Cultural Impact — profound philosophical significance tailored specifically to "{idea_name}".
- statistics: Provide 3 distinct, varied metrics using real numeric estimates tailored to this topic.
- characteristics: Exactly 5 highly descriptive, distinct comma-separated adjectives/traits.
- impact: One striking, bespoke sentence capturing its transformative shift for civilization.

Respond ONLY with this valid JSON object (no markdown formatting, no comments, no extra text):
{
  "satya_yuga": {"description": "para1\n\npara2\n\npara3\n\npara4", "statistics": "Metric1: value, Metric2: value, Metric3: value", "characteristics": "trait1, trait2, trait3, trait4, trait5", "impact": "one sentence"},
  "treta_yuga": {"description": "para1\n\npara2\n\npara3\n\npara4", "statistics": "Metric1: value, Metric2: value, Metric3: value", "characteristics": "trait1, trait2, trait3, trait4, trait5", "impact": "one sentence"},
  "dwapar_yuga": {"description": "para1\n\npara2\n\npara3\n\npara4", "statistics": "Metric1: value, Metric2: value, Metric3: value", "characteristics": "trait1, trait2, trait3, trait4, trait5", "impact": "one sentence"},
  "kali_yuga": {"description": "para1\n\npara2\n\npara3\n\npara4", "statistics": "Metric1: value, Metric2: value, Metric3: value", "characteristics": "trait1, trait2, trait3, trait4, trait5", "impact": "one sentence"}
}"""

        # First attempt: Try Google Gemini API (premium experience!)
        try:
            print(f"[INFO] Generating Yuga evolution for '{idea_name}' using Google Gemini (gemini-2.5-flash)...")
            content = self._call_gemini(prompt.replace("{idea_name}", idea_name))
            if content:
                evolution_data = self._parse_llm_response(content)
                if evolution_data:
                    print(f"[OK] Successfully generated Yuga evolution using Google Gemini!")
                    if rich_content:
                        evolution_data = self._enhance_with_rich_content(
                            evolution_data, idea_name
                        )
                    return evolution_data
                else:
                    print("[WARN] Gemini response received but failed to parse JSON, falling back to OpenAI...")
        except Exception as e:
            print(f"[WARN] Gemini generation attempt failed: {e}. Falling back to OpenAI...")


        models_to_try = [self.model] + self.fallback_models

        for model in models_to_try:
            try:
                content = self._call_llm(prompt, model)
                if content is None:
                    continue

                evolution_data = self._parse_llm_response(content)
                if evolution_data:
                    if model != self.model:
                        print(f"Used fallback model: {model}")
                    if rich_content:
                        evolution_data = self._enhance_with_rich_content(
                            evolution_data, idea_name
                        )
                    return evolution_data

                print(f"LLM response from {model} could not be parsed, trying next")

            except ValueError as e:
                if "RATE_LIMITED" in str(e):
                    print(f"Rate limited on {model}, trying next...")
                    continue
                print(f"LLM error on {model}: {e}")
            except Exception as e:
                print(f"LLM generation error on {model}: {e}")

        print("All models exhausted, using fallback template")
        return self._generate_fallback_evolution(idea_name, description)

    # ------------------------------------------------------------------ #
    #  Rich content helpers                                                #
    # ------------------------------------------------------------------ #

    def _enhance_with_rich_content(self, evolution: Dict, idea_name: str) -> Dict:
        """
        Post-process LLM output:
        - Add time_period
        - Split description into paragraphs list
        - Extract key_insight from last paragraph
        - Build characteristics_list
        - Build statistics_detailed with metric cards
        """
        time_periods = {
            "satya_yuga":  "10,000 BCE – 5,000 BCE",
            "treta_yuga":  "5,000 BCE – 1,000 BCE",
            "dwapar_yuga": "1,000 BCE – 1500 CE",
            "kali_yuga":   "1500 CE – Present",
        }
        para_labels = [
            "Manifestation",
            "Practice & Methods",
            "Limitations",
            "Cultural Significance",
        ]

        for yuga in ["satya_yuga", "treta_yuga", "dwapar_yuga", "kali_yuga"]:
            if yuga not in evolution:
                continue

            evolution[yuga]["time_period"] = time_periods[yuga]

            # --- Description: split into labelled paragraphs ---
            desc = evolution[yuga].get("description", "").strip()
            # Pad if too short with varied dynamic text
            if len(desc) < 150:
                themes = {
                    "satya_yuga": f"In this foundational golden era, the pure blueprint of {idea_name} resonated with divine clarity.",
                    "treta_yuga": f"As ritualistic frameworks emerged, the conceptual depth of {idea_name} was preserved through sacred lineage.",
                    "dwapar_yuga": f"With the expansion of practical trades, early mechanical precursors of {idea_name} began to materialize.",
                    "kali_yuga": f"Driven by empirical inquiry and mass industry, {idea_name} achieved widespread technological optimization."
                }
                desc = (
                    desc
                    + f"\n\n{themes.get(yuga, f'The concept of {idea_name} evolved profoundly.')} "
                    f"Its manifestations reflected the specific energetic and material state of the age."
                    f"\n\nPractitioners adapted methods to overcome environmental thresholds, laying critical groundwork for future iterations."
                    f"\n\nUltimately, this era's understanding of {idea_name} established a vital conceptual pillar in human evolution."
                )
            # Split on double newlines
            raw_paras = [p.strip() for p in re.split(r'\n\n+', desc) if p.strip()]
            paragraphs = []
            for i, para in enumerate(raw_paras[:4]):
                label = para_labels[i] if i < len(para_labels) else f"Part {i+1}"
                paragraphs.append({"label": label, "text": para})
            # If fewer than 4 paragraphs, pad
            while len(paragraphs) < 4:
                i = len(paragraphs)
                label = para_labels[i] if i < len(para_labels) else f"Part {i+1}"
                paragraphs.append({"label": label, "text": ""})

            evolution[yuga]["paragraphs"] = paragraphs
            # key_insight = last non-empty paragraph text (cultural significance)
            evolution[yuga]["key_insight"] = paragraphs[-1]["text"] or paragraphs[0]["text"]

            # --- Characteristics as a list ---
            chars = evolution[yuga].get("characteristics", "")
            if chars:
                evolution[yuga]["characteristics_list"] = [
                    c.strip() for c in chars.split(",") if c.strip()
                ]

            # --- Statistics: parse "Label: value" pairs into metric cards ---
            stats = evolution[yuga].get("statistics", "")
            parsed_metrics = []
            for part in stats.split(","):
                part = part.strip()
                if ":" in part:
                    label, _, value = part.partition(":")
                    parsed_metrics.append({
                        "label": label.strip(),
                        "value": value.strip(),
                        "icon": self._icon_for_label(label.strip()),
                    })
            # Always add the 3 standard Yuga metrics
            parsed_metrics.extend(self._build_metrics(stats, yuga))
            evolution[yuga]["statistics_detailed"] = {
                "original": stats,
                "metrics": parsed_metrics,
            }

        return evolution

    def _icon_for_label(self, label: str) -> str:
        """Pick an emoji icon based on the metric label."""
        label_lower = label.lower()
        mapping = {
            "reach": "🌍", "users": "👥", "practitioners": "👥",
            "tools": "🔧", "instruments": "🎵", "duration": "⏳",
            "efficiency": "⚡", "speed": "🚀", "energy": "🔋",
            "accessibility": "🔓", "cost": "💰", "accuracy": "🎯",
            "scale": "📈", "impact": "💥", "knowledge": "📚",
        }
        for key, icon in mapping.items():
            if key in label_lower:
                return icon
        return "📊"

    def _build_metrics(self, stats_text: str, yuga: str) -> list:
        """Build metric card data for a Yuga."""
        metrics = []
        low = stats_text.lower()

        if "efficiency" in low:
            if "100%" in stats_text or "divine" in low:
                metrics.append({"label": "Efficiency", "value": "100%", "icon": "✨"})
            elif "75%" in stats_text:
                metrics.append({"label": "Efficiency", "value": "75%",  "icon": "⚡"})
            elif "50%" in stats_text:
                metrics.append({"label": "Efficiency", "value": "50%",  "icon": "⚙️"})
            else:
                metrics.append({"label": "Efficiency", "value": "Variable", "icon": "📊"})

        defaults = {
            "satya_yuga":  [
                {"label": "Speed",         "value": "Instantaneous",  "icon": "⚡"},
                {"label": "Energy",        "value": "Divine/Natural",  "icon": "🌟"},
                {"label": "Accessibility", "value": "Universal",       "icon": "🌍"},
            ],
            "treta_yuga":  [
                {"label": "Speed",         "value": "Hours",           "icon": "⏰"},
                {"label": "Energy",        "value": "Ritual/Manual",   "icon": "🔥"},
                {"label": "Accessibility", "value": "Priests/Sages",   "icon": "👥"},
            ],
            "dwapar_yuga": [
                {"label": "Speed",         "value": "Minutes–Hours",   "icon": "⏱️"},
                {"label": "Energy",        "value": "Mechanical",      "icon": "⚙️"},
                {"label": "Accessibility", "value": "Craftsmen",       "icon": "🔨"},
            ],
            "kali_yuga":   [
                {"label": "Speed",         "value": "Seconds–Minutes", "icon": "⚡"},
                {"label": "Energy",        "value": "Electrical",      "icon": "🔌"},
                {"label": "Accessibility", "value": "Mass Market",     "icon": "🏪"},
            ],
        }
        metrics.extend(defaults.get(yuga, []))
        return metrics

    def _generate_fallback_evolution(self, idea_name: str, description: str) -> Dict:
        """Template-based fallback when the LLM is unavailable."""
        suffix = (
            f"\n\nIn this era, {idea_name} carried deep symbolic significance "
            "intertwined with the spiritual and material consciousness of the age."
        )
        base = {
            "satya_yuga": {
                "description": (
                    f"In the Golden Age, {idea_name} existed in its purest divine form — "
                    "a natural manifestation of cosmic harmony requiring no physical tools. "
                    "All beings understood it intuitively, and its expression was effortless."
                    + suffix
                ),
                "statistics": "Efficiency: 100% (divine perfection), Accessibility: Universal, Energy: Pure consciousness",
                "characteristics": "Divine, effortless, instantaneous, perfect harmony with nature",
                "impact": "Complete integration with cosmic order; no separation between thought and manifestation.",
                "time_period": "10,000 BCE – 5,000 BCE",
            },
            "treta_yuga": {
                "description": (
                    f"In Treta Yuga, {idea_name} began to require physical form. "
                    "Sacred rituals and mantras were used to invoke its power, "
                    "and knowledge was held by sages and priests."
                    + suffix
                ),
                "statistics": "Efficiency: 75%, Accessibility: Limited to learned ones, Energy: Spiritual practices",
                "characteristics": "Ritualistic, requires training, partially mechanized through sacred knowledge",
                "impact": "Emergence of specialised knowledge keepers; beginning of hierarchical access.",
                "time_period": "5,000 BCE – 1,000 BCE",
            },
            "dwapar_yuga": {
                "description": (
                    f"In Dwapar Yuga, {idea_name} became mechanical and tool-based. "
                    "Physical devices were developed and knowledge spread to warriors "
                    "and merchants beyond the priestly class."
                    + suffix
                ),
                "statistics": "Efficiency: 50%, Accessibility: Moderate (skilled craftsmen), Energy: Physical labor + basic tools",
                "characteristics": "Mechanical, requires skill and tools, trade-based knowledge transfer",
                "impact": "Democratisation of knowledge; emergence of crafts, guilds, and increased complexity.",
                "time_period": "1,000 BCE – 1500 CE",
            },
            "kali_yuga": {
                "description": (
                    f"In the modern Kali Yuga, {idea_name} is fully technological. "
                    f"{description} "
                    "It relies on complex machinery, electricity, and mass production — "
                    "available to the masses but disconnected from spiritual roots."
                    + suffix
                ),
                "statistics": "Efficiency: Variable (30–90%), Accessibility: Mass market, Energy: Fossil fuels/electricity",
                "characteristics": "Technological, automated, mass-produced, requires external energy",
                "impact": "Universal access but spiritual disconnect; environmental impact and technology dependency.",
                "time_period": "1500 CE – Present",
            },
        }
        return self._enhance_with_rich_content(base, idea_name)

    # ------------------------------------------------------------------ #
    #  Public record builder                                               #
    # ------------------------------------------------------------------ #

    def create_yuga_record(
        self, idea_name: str, description: str, source: str = "Manual"
    ) -> Dict:
        """
        Build a complete Yuga evolution record.

        - Auto-fetches Wikipedia summary when description is blank
        - Fetches up to 4 Wikimedia images with a hard timeout
        - Generates 4-Yuga evolution via LLM (falls back to template)
        """
        image_urls: List[str] = []

        # Auto-research when description is missing
        if not description.strip():
            wiki = self.fetch_wikipedia_info(idea_name)
            if wiki["description"]:
                description = wiki["description"]
            if wiki["image_url"]:
                image_urls.append(wiki["image_url"])

        # Fetch additional images (non-blocking — hard timeout inside)
        for img in self.fetch_images_for_idea(idea_name):
            if img not in image_urls:
                image_urls.append(img)
            if len(image_urls) >= 4:
                break

        evolution = self.generate_yuga_evolution(idea_name, description)

        return {
            "idea": idea_name,
            "description": description,
            "source": source,
            "evolution": evolution,
            "images": image_urls,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  Bulk fetch helpers                                                  #
    # ------------------------------------------------------------------ #

    def fetch_ideas_from_wikipedia(self, limit: int = 10) -> List[Dict]:
        """Fetch summaries for a curated list of tech topics from Wikipedia."""
        tech_topics = [
            "Artificial intelligence", "Blockchain", "Quantum computing",
            "3D printing", "Virtual reality", "Internet of Things",
            "Renewable energy", "Gene editing", "Nanotechnology",
            "Autonomous vehicles", "Cloud computing", "Robotics",
            "Augmented reality", "5G technology", "Smart cities",
            "Biotechnology", "Cryptocurrency", "Machine learning",
            "Solar power", "Electric vehicles", "Drones",
        ]
        ideas = []
        for topic in tech_topics[:limit]:
            info = self.fetch_wikipedia_info(topic)
            if info["description"]:
                ideas.append({
                    "name": info["title"],
                    "description": info["description"],
                    "image_url": info["image_url"],
                    "source": "Wikipedia",
                })
        return ideas

    def fetch_ideas_from_github(self, limit: int = 10) -> List[Dict]:
        """Fetch trending GitHub repositories as idea seeds."""
        ideas = []
        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": "stars:>1000", "sort": "stars",
                    "order": "desc", "per_page": limit,
                },
                timeout=10,
            )
            if r.status_code == 200:
                for repo in r.json().get("items", [])[:limit]:
                    ideas.append({
                        "name": repo.get("name", ""),
                        "description": (repo.get("description") or "")[:200],
                        "source": "GitHub",
                    })
        except Exception as e:
            print(f"GitHub fetch error: {e}")
        return ideas
