"""Generate professional, high-resolution graphics for CodeMind AI.

Creates:
  1. assets/hero.png & assets/hero.svg
  2. assets/architecture.png & assets/architecture.svg
  3. assets/workflow.png & assets/workflow.svg
"""

import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"

def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REGULAR)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ============================================================================
# 1. HERO GRAPHIC (1200 x 500)
# ============================================================================
def create_hero():
    width, height = 1200, 500
    img = Image.new("RGBA", (width, height), (11, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # Subtle gradient / glow effect in center-top
    for r in range(350, 0, -10):
        alpha = int(25 * (1 - r / 350))
        draw.ellipse(
            [600 - r, 180 - r * 0.6, 600 + r, 180 + r * 0.6],
            fill=(56, 189, 248, alpha)
        )
    for r in range(250, 0, -10):
        alpha = int(35 * (1 - r / 250))
        draw.ellipse(
            [600 - r, 200 - r * 0.5, 600 + r, 200 + r * 0.5],
            fill=(129, 140, 248, alpha)
        )

    # Tech Category Pill
    pill_text = "HACKWITHHYDERABAD 3.0  •  AI AGENTS THAT LEARN"
    font_pill = get_font(13, bold=True)
    pill_bbox = draw.textbbox((0, 0), pill_text, font=font_pill)
    pw = pill_bbox[2] - pill_bbox[0] + 32
    ph = 30
    px = (width - pw) // 2
    py = 55
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=15, fill=(30, 41, 59, 220), outline=(56, 189, 248, 180), width=1)
    draw.text((px + 16, py + 7), pill_text, font=font_pill, fill=(56, 189, 248, 255))

    # Main Title
    title = "CodeMind AI"
    font_title = get_font(56, bold=True)
    t_bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = t_bbox[2] - t_bbox[0]
    draw.text(((width - tw) // 2, 110), title, font=font_title, fill=(255, 255, 255, 255))

    # Subtitle
    sub = "Adaptive AI Code Review Agent with Persistent Memory"
    font_sub = get_font(24, bold=True)
    s_bbox = draw.textbbox((0, 0), sub, font=font_sub)
    sw = s_bbox[2] - s_bbox[0]
    draw.text(((width - sw) // 2, 185), sub, font=font_sub, fill=(148, 163, 184, 255))

    # Tagline
    tagline = "Learns your team's coding conventions, common pitfalls, and architectural standards using Hindsight."
    font_tag = get_font(16)
    tg_bbox = draw.textbbox((0, 0), tagline, font=font_tag)
    tgw = tg_bbox[2] - tg_bbox[0]
    draw.text(((width - tgw) // 2, 230), tagline, font=font_tag, fill=(203, 213, 225, 255))

    # Badges row
    badges = [
        ("Vectorize Hindsight Memory", (56, 189, 248)),
        ("Groq Ultra-Fast Inference", (249, 115, 22)),
        ("Python AST Static Analysis", (52, 211, 153)),
        ("Adaptive Feedback Loop", (168, 85, 247)),
    ]
    total_w = sum(draw.textbbox((0, 0), b[0], font=get_font(13, bold=True))[2] - draw.textbbox((0, 0), b[0], font=get_font(13, bold=True))[0] + 32 for b in badges) + (len(badges) - 1) * 16
    start_x = (width - total_w) // 2
    cur_x = start_x
    for text, color in badges:
        f = get_font(13, bold=True)
        tb = draw.textbbox((0, 0), text, font=f)
        bw = tb[2] - tb[0] + 28
        bh = 34
        draw.rounded_rectangle([cur_x, 290, cur_x + bw, 290 + bh], radius=8, fill=(15, 23, 42, 240), outline=color, width=1)
        draw.text((cur_x + 14, 290 + 8), text, font=f, fill=color)
        cur_x += bw + 16

    # Bottom Terminal Preview Banner
    term_x, term_y = 180, 360
    term_w, term_h = 840, 95
    draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h], radius=10, fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=1)
    # Window buttons
    draw.ellipse([term_x + 16, term_y + 14, term_x + 26, term_y + 24], fill=(239, 68, 68))
    draw.ellipse([term_x + 32, term_y + 14, term_x + 42, term_y + 24], fill=(245, 158, 11))
    draw.ellipse([term_x + 48, term_y + 14, term_x + 58, term_y + 24], fill=(16, 185, 129))
    
    font_code = get_font(14, mono=True)
    draw.text((term_x + 75, term_y + 11), "codemind-agent --review auth_module.py", font=font_code, fill=(148, 163, 184))
    draw.text((term_x + 20, term_y + 44), "[Recall] Retained memory #4 applied: 'Team strictly rejects bare except clauses.'", font=font_code, fill=(56, 189, 248))
    draw.text((term_x + 20, term_y + 68), "[Review] Suppressed 2 generic suggestions based on active developer guardrails.", font=font_code, fill=(52, 211, 153))

    png_path = os.path.join(ASSETS_DIR, "hero.png")
    img.save(png_path, "PNG")
    print(f"Saved: {png_path}")


# ============================================================================
# 2. ARCHITECTURE DIAGRAM (1200 x 720)
# ============================================================================
def create_architecture():
    width, height = 1200, 720
    img = Image.new("RGBA", (width, height), (11, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # Header
    font_head = get_font(28, bold=True)
    draw.text((60, 40), "CodeMind AI — System Architecture Specification", font=font_head, fill=(255, 255, 255))
    font_sub = get_font(15)
    draw.text((60, 78), "Multi-tiered architecture combining deterministic AST analysis, persistent Hindsight memory, and high-speed LLM inference.", font=font_sub, fill=(148, 163, 184))

    # Helper for stylized cards
    def draw_card(x, y, w, h, title, subtitle, items, border_color, fill_color=(15, 23, 42)):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=fill_color, outline=border_color, width=2)
        # Title bar
        draw.text((x + 18, y + 16), title, font=get_font(17, bold=True), fill=border_color)
        draw.text((x + 18, y + 38), subtitle, font=get_font(12), fill=(148, 163, 184))
        # Divider
        draw.line([x + 18, y + 58, x + w - 18, y + 58], fill=(51, 65, 85), width=1)
        # Items
        cur_y = y + 70
        for item in items:
            draw.text((x + 22, cur_y), f"• {item}", font=get_font(13), fill=(226, 232, 240))
            cur_y += 24

    # 1. Client Layer
    draw_card(
        60, 130, 240, 240,
        "1. Client Layer", "Developer Entrypoints",
        [
            "Web Workspace (SPA)",
            "HTML5 / Tailwind UI",
            "File Upload (.py)",
            "Live Code Editor",
            "Accept / Reject Buttons",
            "Memory Inspector Panel",
        ],
        (56, 189, 248)
    )

    # 2. REST API & Orchestration Layer
    draw_card(
        340, 130, 260, 240,
        "2. API Gateway", "FastAPI Asynchronous Server",
        [
            "/api/review (JSON)",
            "/api/review/upload",
            "/api/feedback (Loop)",
            "/api/conventions",
            "/api/memories (Reflect)",
            "Async Lifespan Engine",
        ],
        (129, 140, 248)
    )

    # 3. Static Code Analyzer
    draw_card(
        640, 130, 240, 240,
        "3. AST Analyzer", "Deterministic Pre-Scan",
        [
            "Python ast.NodeVisitor",
            "Cyclomatic Complexity",
            "Hardcoded Secrets Scan",
            "eval() / exec() Checks",
            "Mutable Default Traps",
            "Bare except: Detection",
        ],
        (52, 211, 153)
    )

    # 4. LLM Review Engine
    draw_card(
        920, 130, 220, 240,
        "4. Review Engine", "Groq Cloud Inference",
        [
            "qwen/qwen3.8-27b",
            "Native JSON Object Mode",
            "Context Prompt Builder",
            "json-repair Resilient Parser",
            "Prioritized Issue Sort",
            "Memory Attribution Tags",
        ],
        (249, 115, 22)
    )

    # Lower Layer: Persistent Memory Layer (Full Width)
    draw_card(
        60, 420, 1080, 240,
        "5. Persistent Memory Layer — Vectorize Hindsight", "Adaptive Experience Retention & Semantic Retrieval Substrate",
        [
            "Bank Isolation: Dedicated Memory Bank ('codemind-main-bank') for project-level conventions and security boundaries.",
            "Pre-Review Recall: Query Hindsight prior to LLM execution to extract team preferences, accepted rules, and active guardrails.",
            "Negative Constraints (Guardrails): Stored when developers reject suggestions; explicitly injected to suppress repeat mistakes.",
            "Positive Reinforcement: Accepted review suggestions are retained as formal coding standards applied to future PRs.",
            "Higher-Order Reflection: client.areflect() synthesizes long-term team mental models into a unified living style profile.",
            "Audit & Review History: Every review session summary is retained with timestamps, issue counts, and file-level metrics.",
        ],
        (168, 85, 247)
    )

    # Connecting Flow Arrows
    font_arrow = get_font(11, bold=True)
    draw.text((305, 230), "HTTP", font=font_arrow, fill=(56, 189, 248))
    draw.text((605, 230), "AST", font=font_arrow, fill=(52, 211, 153))
    draw.text((885, 230), "PROMPT", font=font_arrow, fill=(249, 115, 22))

    draw.text((430, 385), "RECALL CONVENTIONS & GUARDRAILS", font=font_arrow, fill=(168, 85, 247))
    draw.text((850, 385), "RETAIN FEEDBACK & SESSION AUDIT", font=font_arrow, fill=(168, 85, 247))

    png_path = os.path.join(ASSETS_DIR, "architecture.png")
    img.save(png_path, "PNG")
    print(f"Saved: {png_path}")


# ============================================================================
# 3. WORKFLOW INFOGRAPHIC (1200 x 780)
# ============================================================================
def create_workflow():
    width, height = 1200, 780
    img = Image.new("RGBA", (width, height), (11, 15, 25, 255))
    draw = ImageDraw.Draw(img)

    # Header
    font_head = get_font(28, bold=True)
    draw.text((60, 40), "CodeMind AI — End-to-End Operational Workflow", font=font_head, fill=(255, 255, 255))
    font_sub = get_font(15)
    draw.text((60, 78), "The 8-step continuous learning cycle connecting source code submission to persistent memory adaptation.", font=font_sub, fill=(148, 163, 184))

    steps = [
        (1, "Code Ingestion", "Developer submits Python source via web editor or .py file upload.", (56, 189, 248)),
        (2, "AST Analysis", "Deterministic AST traversal extracts functions, classes, complexity & smells.", (52, 211, 153)),
        (3, "Memory Recall", "Semantic query to Hindsight retrieves past accepted standards & active guardrails.", (168, 85, 247)),
        (4, "Prompt Synthesis", "Combines raw code, AST metrics, retrieved memories & guardrail constraints.", (249, 115, 22)),
        (5, "Groq AI Inference", "qwen/qwen3.8-27b analyzes code with native JSON mode for speed & accuracy.", (236, 72, 153)),
        (6, "Resilient Output", "Validates output schema with json-repair recovery; logs session in Hindsight.", (14, 165, 233)),
        (7, "Review Display", "Presents prioritized findings (Critical → Low) with applied memory citations.", (234, 179, 8)),
        (8, "Feedback Loop", "Accept/Reject clicks retain positive conventions or negative guardrails.", (16, 185, 129)),
    ]

    card_w, card_h = 245, 240
    xs = [60, 335, 610, 885]
    
    # Row 1 (Steps 1 to 4)
    for i in range(4):
        num, title, desc, color = steps[i]
        x = xs[i]
        y = 130
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=10, fill=(15, 23, 42), outline=color, width=2)
        # Step Number Badge
        draw.ellipse([x + 18, y + 16, x + 48, y + 46], fill=color)
        draw.text((x + 27, y + 21), str(num), font=get_font(16, bold=True), fill=(11, 15, 25))
        # Title
        draw.text((x + 60, y + 22), title, font=get_font(16, bold=True), fill=(255, 255, 255))
        # Divider
        draw.line([x + 18, y + 56, x + card_w - 18, y + 56], fill=(51, 65, 85), width=1)
        # Description
        words = desc.split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 26:
                lines.append(" ".join(cur))
                cur = []
        if cur:
            lines.append(" ".join(cur))
        
        cur_y = y + 72
        for line in lines:
            draw.text((x + 18, cur_y), line, font=get_font(13), fill=(203, 213, 225))
            cur_y += 22

    # Row 2 (Steps 5 to 8, reversed flow)
    for i in range(4):
        num, title, desc, color = steps[4 + i]
        x = xs[3 - i]  # Reverse direction
        y = 430
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=10, fill=(15, 23, 42), outline=color, width=2)
        # Step Number Badge
        draw.ellipse([x + 18, y + 16, x + 48, y + 46], fill=color)
        draw.text((x + 27, y + 21), str(num), font=get_font(16, bold=True), fill=(11, 15, 25))
        # Title
        draw.text((x + 60, y + 22), title, font=get_font(16, bold=True), fill=(255, 255, 255))
        # Divider
        draw.line([x + 18, y + 56, x + card_w - 18, y + 56], fill=(51, 65, 85), width=1)
        # Description
        words = desc.split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 26:
                lines.append(" ".join(cur))
                cur = []
        if cur:
            lines.append(" ".join(cur))
        
        cur_y = y + 72
        for line in lines:
            draw.text((x + 18, cur_y), line, font=get_font(13), fill=(203, 213, 225))
            cur_y += 22

    # Connecting Arrows
    font_arrow = get_font(18, bold=True)
    draw.text((310, 240), "→", font=font_arrow, fill=(56, 189, 248))
    draw.text((585, 240), "→", font=font_arrow, fill=(52, 211, 153))
    draw.text((860, 240), "→", font=font_arrow, fill=(168, 85, 247))

    # Down arrow at right
    draw.text((1000, 385), "↓", font=font_arrow, fill=(236, 72, 153))

    # Bottom row left arrows
    draw.text((860, 540), "←", font=font_arrow, fill=(14, 165, 233))
    draw.text((585, 540), "←", font=font_arrow, fill=(234, 179, 8))
    draw.text((310, 540), "←", font=font_arrow, fill=(16, 185, 129))

    # Up feedback arrow back to memory
    draw.text((170, 385), "⟳ Adaptive Memory Update", font=get_font(12, bold=True), fill=(16, 185, 129))

    png_path = os.path.join(ASSETS_DIR, "workflow.png")
    img.save(png_path, "PNG")
    print(f"Saved: {png_path}")


if __name__ == "__main__":
    create_hero()
    create_architecture()
    create_workflow()
    print("All professional assets generated successfully!")
