from backend.nodes import reducer as reducer_mod
from backend.schemas import Plan, Task


def _plan():
    tasks = [Task(id=1, title="A", goal="g", bullets=["a", "b", "c"], target_words=200)]
    return Plan(blog_title="My Test Blog", audience="devs", tone="clear", tasks=tasks)


def test_merge_content_orders_sections_by_task_id():
    state = {"plan": _plan(), "sections": [(2, "## Two"), (1, "## One"), (3, "## Three")]}
    out = reducer_mod.merge_content(state)
    md = out["merged_md"]
    assert md.startswith("# My Test Blog")
    assert md.index("## One") < md.index("## Two") < md.index("## Three")


def _use_tmp_dirs(monkeypatch, tmp_path):
    import backend.utils.files as files_mod

    blogs, images = tmp_path / "blogs", tmp_path / "images"
    monkeypatch.setattr(files_mod, "BLOGS_DIR", blogs)
    monkeypatch.setattr(files_mod, "IMAGES_DIR", images)
    monkeypatch.setattr(reducer_mod, "IMAGES_DIR", images)
    return blogs, images


def test_no_images_writes_markdown(monkeypatch, tmp_path):
    blogs, _ = _use_tmp_dirs(monkeypatch, tmp_path)
    state = {"plan": _plan(), "merged_md": "# T\n\nbody", "md_with_placeholders": "# T\n\nbody", "image_specs": []}
    out = reducer_mod.generate_and_place_images(state)
    assert out["final"] == "# T\n\nbody"
    assert (blogs / "my_test_blog.md").read_text(encoding="utf-8") == "# T\n\nbody"


def test_image_success_replaces_placeholder(monkeypatch, tmp_path):
    blogs, images = _use_tmp_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(reducer_mod, "_gemini_generate_image_bytes", lambda p: b"PNGDATA")
    spec = {"placeholder": "[[IMAGE_1]]", "filename": "flow.png", "alt": "alt", "caption": "cap", "prompt": "p"}
    state = {"plan": _plan(), "merged_md": "x", "md_with_placeholders": "A\n[[IMAGE_1]]\nB", "image_specs": [spec]}
    out = reducer_mod.generate_and_place_images(state)
    assert "![alt](../images/flow.png)" in out["final"]
    assert "[[IMAGE_1]]" not in out["final"]
    assert (images / "flow.png").read_bytes() == b"PNGDATA"


def test_image_failure_falls_back_to_prompt_block(monkeypatch, tmp_path):
    _use_tmp_dirs(monkeypatch, tmp_path)

    def boom(prompt):
        raise RuntimeError("quota")

    monkeypatch.setattr(reducer_mod, "_gemini_generate_image_bytes", boom)
    spec = {"placeholder": "[[IMAGE_1]]", "filename": "flow.png", "alt": "alt", "caption": "cap", "prompt": "p"}
    state = {"plan": _plan(), "merged_md": "x", "md_with_placeholders": "A\n[[IMAGE_1]]", "image_specs": [spec]}
    out = reducer_mod.generate_and_place_images(state)
    assert "IMAGE GENERATION FAILED" in out["final"]
    assert "quota" in out["final"]
