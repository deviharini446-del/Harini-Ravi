from pathlib import Path
import traceback

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.ai.gemini_flash import generate_outline
from app.ai.gemini_pro import generate_story
from app.ai.image_generator import generate_image

from app.utils.layout_builder import build_comic_layout
from app.utils.exporters import save_pdf


# =========================================================
# ROUTER
# =========================================================

router = APIRouter()


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"

PANELS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# TEMPLATES
# =========================================================

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


# =========================================================
# REQUEST MODEL
# =========================================================

class PromptRequest(BaseModel):
    story_prompt: str
    character_name: str
    setting: str
    tone: str
    art_style: str


# =========================================================
# HOME PAGE
# =========================================================

@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    try:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={}
        )

    except Exception:
        error = traceback.format_exc()

        return HTMLResponse(
            content=f"<pre>{error}</pre>",
            status_code=500
        )


# =========================================================
# GET /generate
# =========================================================

@router.get("/generate")
async def generate_get():

    return RedirectResponse(
        url="/",
        status_code=303
    )


# =========================================================
# FULL COMIC GENERATION PIPELINE
# =========================================================

def generate_complete_comic(
    data: PromptRequest
):

    # STEP 1: Gemini Flash

    outline = generate_outline(

        story_prompt=data.story_prompt,
        character_name=data.character_name,
        setting=data.setting,
        tone=data.tone,
        art_style=data.art_style,

    )

    # STEP 2: Gemini Pro

    story = generate_story(

        outline=outline,
        story_prompt=data.story_prompt,
        character_name=data.character_name,
        setting=data.setting,
        tone=data.tone,
        art_style=data.art_style,

    )

    # STEP 3: Generate images

    image_paths = []

    for index, panel in enumerate(outline):

        image_prompt = panel.get(
            "image_prompt",
            panel.get(
                "scene_description",
                ""
            )
        )

        image_path = generate_image(

            prompt=image_prompt,

            panel_number=panel.get(
                "panel_number",
                index + 1
            ),

        )

        image_paths.append(image_path)

    # STEP 4: Build layout

    layout = build_comic_layout(

        outline=outline,
        story=story,
        image_paths=image_paths,

    )

    # STEP 5: Export PDF

    pdf_path = save_pdf(layout)

    return {

        "outline": outline,
        "story": story,
        "layout": layout,
        "pdf_path": pdf_path,

    }


# =========================================================
# GENERATE - FULL COMIC
# =========================================================

@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate(

    request: Request,

    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),

):

    try:

        data = PromptRequest(

            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,

        )

        result = generate_complete_comic(data)

        return HTMLResponse(

            content=f"""
            <!DOCTYPE html>

            <html>

            <head>

                <title>ComicCraft AI - Comic Generated</title>

                <style>

                    body {{
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        background: #f5f5f5;
                    }}

                    .container {{
                        max-width: 1000px;
                        margin: auto;
                        background: white;
                        padding: 30px;
                        border-radius: 15px;
                    }}

                    h1 {{
                        color: green;
                    }}

                    h2 {{
                        margin-top: 30px;
                    }}

                    pre {{
                        white-space: pre-wrap;
                        background: #f4f4f4;
                        padding: 20px;
                        border-radius: 10px;
                    }}

                    .success {{
                        padding: 15px;
                        background: #e8f5e9;
                        border-radius: 10px;
                    }}

                    a {{
                        display: inline-block;
                        margin-top: 20px;
                        margin-right: 15px;
                        padding: 10px 15px;
                        background: #222;
                        color: white;
                        text-decoration: none;
                        border-radius: 8px;
                    }}

                </style>

            </head>

            <body>

                <div class="container">

                    <h1>Comic Generated Successfully!</h1>

                    <div class="success">
                        Flash → Pro → Images → Layout → PDF completed.
                    </div>

                    <h2>5-Panel Outline</h2>

                    <pre>{result["outline"]}</pre>

                    <h2>Comic Story</h2>

                    <pre>{result["story"]}</pre>

                    <h2>PDF</h2>

                    <pre>{result["pdf_path"]}</pre>

                    <a href="/">
                        Back to ComicCraft
                    </a>

                </div>

            </body>

            </html>
            """,

            status_code=200

        )

    except Exception:

        error = traceback.format_exc()

        return HTMLResponse(

            content=f"<pre>{error}</pre>",
            status_code=500

        )


# =========================================================
# JSON COMIC GENERATION
# =========================================================

@router.post(
    "/generate-comic/json"
)
async def generate_comic_json(
    payload: PromptRequest
):

    try:

        result = generate_complete_comic(payload)

        return {

            "success": True,
            "layout": result["layout"],
            "pdf_path": result["pdf_path"],

        }

    except Exception as error:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# TEST IMAGE
# =========================================================

@router.get(
    "/test-image",
    response_class=HTMLResponse
)
async def test_image(

    request: Request,

    prompt: str = (
        "A brave fox exploring an "
        "enchanted forest, comic book "
        "illustration"
    )

):

    try:

        image_path = generate_image(
            prompt=prompt,
            panel_number=0
        )

        return templates.TemplateResponse(

            request=request,

            name="export_success.html",

            context={

                "message":
                    "Test image generated successfully.",

                "pdf_path": None,

                "image_path": image_path,

            }

        )

    except Exception:

        error = traceback.format_exc()

        return HTMLResponse(
            content=f"<pre>{error}</pre>",
            status_code=500
        )


# =========================================================
# EXPORT SUCCESS
# =========================================================

@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(

    request: Request,

    pdf_path: str = ""

):

    return templates.TemplateResponse(

        request=request,

        name="export_success.html",

        context={

            "message":
                "Your comic has been exported successfully.",

            "pdf_path": pdf_path,

            "image_path": None,

        }

    )