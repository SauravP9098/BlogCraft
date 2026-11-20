from __future__ import annotations

import logging
from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import IMAGE_MD_PREFIX, IMAGES_DIR, S3_BUCKET_NAME
from backend.llm import llm
from backend.prompts.images import DECIDE_IMAGES_SYSTEM
from backend.schemas import GlobalImagePlan, State
from backend.tools.bedrock_image import _bedrock_generate_image_bytes
from backend.tools.s3_storage import upload_bytes_to_s3, upload_file_to_s3
from backend.utils.files import _safe_slug, ensure_output_dirs, save_markdown

logger = logging.getLogger(__name__)


def merge_content(state: State) -> dict:
    plan = state["plan"]
    if plan is None:
        raise ValueError("merge_content called without plan.")

    ordered_sections = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered_sections).strip()
    merged_md = f"# {plan.blog_title}\n\n{body}\n"
    return {"merged_md": merged_md}


def decide_images(state: State) -> dict:
    planner = llm.with_structured_output(GlobalImagePlan)
    merged_md = state["merged_md"]
    plan = state["plan"]
    assert plan is not None

    # Extract section titles for prompt efficiency
    section_titles = [f"## {task.title}" for task in plan.tasks]

    try:
        image_plan = planner.invoke(
            [
                SystemMessage(content=DECIDE_IMAGES_SYSTEM),
                HumanMessage(
                    content=(
                        f"Blog Title: {plan.blog_title}\n"
                        f"Topic: {state['topic']}\n"
                        f"Kind: {plan.blog_kind}\n\n"
                        f"Available Sections:\n"
                        + "\n".join(f"- {t}" for t in section_titles)
                        + "\n\nPropose up to 3 technical diagrams or illustrations."
                    )
                ),
            ]
        )
        images = image_plan.images or []
    except Exception as e:
        logger.warning(f"[Reducer] decide_images prompt failed ({e}). Proceeding without images.")
        images = []

    # Insert placeholders programmatically into merged_md
    md_with_placeholders = merged_md
    for i, spec in enumerate(images):
        placeholder = f"[[IMAGE_{i + 1}]]"
        spec.placeholder = placeholder

        # If after_section was specified, insert after that heading
        placed = False
        if spec.after_section:
            for title in section_titles:
                if spec.after_section.lower() in title.lower() and title in md_with_placeholders:
                    md_with_placeholders = md_with_placeholders.replace(
                        title, f"{title}\n\n{placeholder}"
                    )
                    placed = True
                    break

        if not placed and len(section_titles) > (i + 1):
            # Fallback to inserting after section (i+1)
            target_title = section_titles[i + 1]
            if target_title in md_with_placeholders:
                md_with_placeholders = md_with_placeholders.replace(
                    target_title, f"{target_title}\n\n{placeholder}"
                )

    return {
        "md_with_placeholders": md_with_placeholders,
        "image_specs": [img.model_dump() for img in images],
    }


def generate_and_place_images(state: State) -> dict:
    plan = state["plan"]
    assert plan is not None

    md = state.get("md_with_placeholders") or state["merged_md"]
    image_specs = state.get("image_specs", []) or []

    # If no images requested, just write merged markdown
    if not image_specs:
        local_path = save_markdown(plan.blog_title, md)
        if S3_BUCKET_NAME:
            upload_file_to_s3(local_path, f"blogs/{_safe_slug(plan.blog_title)}.md")
        return {"final": md}

    ensure_output_dirs()

    for spec in image_specs:
        placeholder = spec["placeholder"]
        filename = spec["filename"]
        out_path = IMAGES_DIR / filename

        img_url = f"{IMAGE_MD_PREFIX}/{filename}"

        # Generate image only if not already cached
        if not out_path.exists():
            try:
                img_bytes = _bedrock_generate_image_bytes(spec["prompt"])
                out_path.write_bytes(img_bytes)

                # Upload to S3 if configured
                if S3_BUCKET_NAME:
                    uploaded_s3_url = upload_bytes_to_s3(
                        img_bytes, f"images/{filename}", "image/png"
                    )
                    if uploaded_s3_url:
                        img_url = uploaded_s3_url

            except Exception as e:
                # Graceful fallback: maintain readable markdown
                prompt_block = (
                    f"> **[TECHNICAL DIAGRAM]** {spec.get('caption','')}\n>\n"
                    f"> *Alt:* {spec.get('alt','')}\n>\n"
                    f"> *Prompt:* {spec.get('prompt','')}\n"
                )
                md = md.replace(placeholder, prompt_block)
                continue
        else:
            if S3_BUCKET_NAME:
                uploaded_s3_url = upload_bytes_to_s3(
                    out_path.read_bytes(), f"images/{filename}", "image/png"
                )
                if uploaded_s3_url:
                    img_url = uploaded_s3_url

        img_md = f"![{spec['alt']}]({img_url})\n*{spec['caption']}*"
        md = md.replace(placeholder, img_md)

    local_path = save_markdown(plan.blog_title, md)
    if S3_BUCKET_NAME:
        upload_file_to_s3(local_path, f"blogs/{_safe_slug(plan.blog_title)}.md")

    return {"final": md}
