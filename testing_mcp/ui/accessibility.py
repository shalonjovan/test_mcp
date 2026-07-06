from __future__ import annotations

import json
from typing import Any

AXE_CORE_SCRIPT = """
const axe = window.axe || undefined;
if (!axe) {
  // Inject axe-core from CDN if not present
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js';
  script.onload = () => window.__axeReady = true;
  document.head.appendChild(script);
  await new Promise(resolve => {
    const check = () => {
      if (window.__axeReady) resolve();
      else setTimeout(check, 100);
    };
    check();
  });
}
const result = await axe.run(document, {
  runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']
});
return JSON.stringify(result);
"""


async def run_accessibility_scan(
    url: str,
    timeout: int = 30000,
    standard: str = "wcag2aa",
    include_iframe: bool = True,
) -> dict[str, Any]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "Playwright not installed", "passed": False}

    rulesets = {
        "wcag2a": ["wcag2a"],
        "wcag2aa": ["wcag2a", "wcag2aa"],
        "wcag21a": ["wcag2a", "wcag21a"],
        "wcag21aa": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
        "wcag22aa": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"],
        "best-practice": ["best-practice"],
        "all": None,
    }

    run_only = rulesets.get(standard, ["wcag2aa"])

    result: dict[str, Any] = {
        "url": url,
        "standard": standard,
        "violations": [],
        "passes": [],
        "incomplete": [],
        "summary": {},
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout)
        except Exception as e:
            await browser.close()
            return {"error": f"Failed to load {url}: {e}", "passed": False}

        try:
            raw = await page.evaluate(
                """async () => {
                    const script = document.createElement('script');
                    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js';
                    document.head.appendChild(script);
                    await new Promise((resolve, reject) => {
                        script.onload = resolve;
                        script.onerror = reject;
                        setTimeout(reject, 10000);
                    });
                    const axeResult = await axe.run(document, {
                        runOnly: """ + json.dumps(run_only) + """,
                        iframes: """ + ("true" if include_iframe else "false") + """
                    });
                    return JSON.stringify(axeResult);
                }"""
            )
            data = json.loads(raw)
        except Exception as e:
            await browser.close()
            return {"error": f"Axe scan failed: {e}", "passed": False}

        await browser.close()

    for v in data.get("violations", []):
        for node in v.get("nodes", []):
            result["violations"].append({
                "id": v["id"],
                "impact": v.get("impact", "unknown"),
                "description": v.get("description", ""),
                "help": v.get("help", ""),
                "help_url": v.get("helpUrl", ""),
                "tags": v.get("tags", []),
                "target": node.get("target", []),
                "failure_summary": node.get("failureSummary", ""),
                "html": node.get("html", ""),
            })

    for v in data.get("passes", []):
        result["passes"].append({
            "id": v["id"],
            "description": v.get("description", ""),
            "impact": v.get("impact", "unknown"),
        })

    for v in data.get("incomplete", []):
        for node in v.get("nodes", []):
            result["incomplete"].append({
                "id": v["id"],
                "impact": v.get("impact", "unknown"),
                "description": v.get("description", ""),
                "target": node.get("target", []),
            })

    critical = sum(1 for v in result["violations"] if v["impact"] == "critical")
    serious = sum(1 for v in result["violations"] if v["impact"] == "serious")
    moderate = sum(1 for v in result["violations"] if v["impact"] == "moderate")
    minor = sum(1 for v in result["violations"] if v["impact"] == "minor")
    total_violations = len(result["violations"])

    result["summary"] = {
        "total_violations": total_violations,
        "critical": critical,
        "serious": serious,
        "moderate": moderate,
        "minor": minor,
        "passed_checks": len(result["passes"]),
        "incomplete": len(result["incomplete"]),
    }
    result["passed"] = total_violations == 0

    return result


def check_color_contrast(foreground: str, background: str) -> dict[str, Any]:
    import re

    def hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    def relative_luminance(r: int, g: int, b: int) -> float:
        def linearize(c: float) -> float:
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

    def parse_color(color: str) -> tuple[int, int, int]:
        if color.startswith("#"):
            return hex_to_rgb(color)
        m = re.match(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
        return (0, 0, 0)

    fg = parse_color(foreground)
    bg = parse_color(background)

    l1 = relative_luminance(*fg)
    l2 = relative_luminance(*bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)

    passes_aa_normal = ratio >= 4.5
    passes_aa_large = ratio >= 3.0
    passes_aaa_normal = ratio >= 7.0
    passes_aaa_large = ratio >= 4.5

    return {
        "foreground": foreground,
        "background": background,
        "contrast_ratio": round(ratio, 2),
        "passes_AA_normal": passes_aa_normal,
        "passes_AA_large": passes_aa_large,
        "passes_AAA_normal": passes_aaa_normal,
        "passes_AAA_large": passes_aaa_large,
    }


def check_keyboard_navigation(selectors: list[str]) -> dict[str, Any]:
    return {
        "type": "keyboard-navigation",
        "description": "Manual check required: tab through all interactive elements",
        "selectors_to_check": selectors,
        "recommendations": [
            "Ensure all interactive elements are reachable via Tab",
            "Ensure focus indicators are visible (outline, ring)",
            "Avoid tabindex > 0 (use document order)",
            "Ensure no keyboard traps (can Tab out of every element)",
            "Test with a screen reader (NVDA, VoiceOver, TalkBack)",
        ],
    }
