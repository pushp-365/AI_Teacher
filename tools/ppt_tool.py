"""Generate editable PowerPoint files from Groq-authored python-pptx code."""

import ast
import re
import subprocess
import sys
from pathlib import Path

# Support both `python main.py` and direct execution via `python tools/ppt_tool.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import client, MODEL_PPT


PPT_CODE_PROMPT = """
You are a senior instructional designer and an expert python-pptx developer.
Create a polished, editable 16:9 PowerPoint lesson for the curriculum below.

Curriculum:
Topic: {topic}
Audience: {audience}
Duration: {duration}
Learning goals: {goals}

Write Python code only, with no Markdown fence and no explanation. The code must:
1. Import only from `pptx`, `pptx.util`, `pptx.enum.text`, `pptx.enum.shapes`,
   `pptx.enum.dml`, and `pptx.dml.color`.
2. Define exactly one public function: `create_presentation(output_path)`.
3. Create an editable .pptx with exactly 6 slides, including a minimal title slide,
   learning objectives, concept explanation, a worked example, a process or comparison,
   recap, and a short knowledge-check slide.
4. Keep the entire response under 850 output tokens. Use one compact rendering loop and a
   slide-data list instead of repeated layout code. Do not define helper functions.
5. Use python-pptx native text and shapes. Do not use
   images, external files, network calls, file reads, subprocesses, eval, exec, or imports
   other than the permitted modules.
6. Use a consistent modern academic design: dark navy, teal, and warm accent colors;
   generous whitespace; aligned elements; readable fonts. Use at least 42pt for the cover
   title, 30pt for slide titles, and 18pt for body copy.
7. Keep each slide focused. Use concise, accurate teaching language, no invented facts,
   no citations, no filler, and no text overflow. Make the deck useful to a teacher in a
   real classroom.
8. Save the deck to `output_path` and return a list of dictionaries in this form:
   `[{{"title": "...", "bullets": ["...", "..."]}}]`.

Do not use `open`, `os`, `pathlib`, `requests`, `subprocess`, `shutil`, `sys`, `eval`,
`exec`, `__import__`, or any dunder attribute. Do not create files other than output_path.
"""

ALLOWED_IMPORTS = {
    "pptx", "pptx.util", "pptx.enum.text", "pptx.enum.shapes", "pptx.enum.dml", "pptx.dml.color",
}
BLOCKED_NAMES = {
    "open", "eval", "exec", "compile", "globals", "locals", "vars", "getattr", "setattr", "delattr", "__import__",
}


def _extract_code(text: str) -> str:
    """Accept an occasional Markdown fenced response without trusting prose."""
    match = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else text).strip()


def _validate_pptx_code(code: str) -> None:
    """Reject model output outside the deliberately small presentation-code contract."""
    tree = ast.parse(code)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    public_functions = [node for node in functions if not node.name.startswith("_")]
    if len(public_functions) != 1 or public_functions[0].name != "create_presentation":
        raise ValueError("The generated code must expose only create_presentation(output_path).")

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module not in ALLOWED_IMPORTS:
            raise ValueError(f"Disallowed import: {node.module}")
        if isinstance(node, ast.Import) and any(alias.name not in ALLOWED_IMPORTS for alias in node.names):
            raise ValueError("Only python-pptx imports are allowed.")
        if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.Lambda, ast.With, ast.Try, ast.Raise, ast.Global, ast.Nonlocal)):
            raise ValueError("The generated code contains a disallowed Python construct.")
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            raise ValueError(f"Disallowed name: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("Dunder attributes are not allowed.")


def _run_pptx_code(code: str, output_path: str) -> list:
    """Execute checked python-pptx code with a minimal import surface."""
    _validate_pptx_code(code)
    allowed_builtins = {
        "range": range, "len": len, "enumerate": enumerate, "str": str,
        "int": int, "float": float, "list": list, "dict": dict, "zip": zip,
        "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
    }
    real_import = __import__

    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name not in ALLOWED_IMPORTS:
            raise ImportError(f"Import blocked: {name}")
        return real_import(name, globals, locals, fromlist, level)

    allowed_builtins["__import__"] = safe_import
    namespace = {"__builtins__": allowed_builtins, "__name__": "generated_presentation"}
    exec(compile(code, "<groq_pptx_code>", "exec"), namespace, namespace)
    result = namespace["create_presentation"](output_path)
    if not Path(output_path).is_file() or Path(output_path).stat().st_size == 0:
        raise RuntimeError("The generated code did not create a PPTX file.")
    return result if isinstance(result, list) else []


def _convert_to_legacy_ppt(pptx_path: str) -> str | None:
    """Use installed PowerPoint to create the requested PowerPoint 97-2003 file."""
    ppt_path = str(Path(pptx_path).with_suffix(".ppt"))
    source = pptx_path.replace("'", "''")
    target = ppt_path.replace("'", "''")
    command = (
        "$ErrorActionPreference = 'Stop'; "
        "$powerpoint = New-Object -ComObject PowerPoint.Application; "
        "$powerpoint.Visible = -1; "
        f"$presentation = $powerpoint.Presentations.Open('{source}', $false, $false, $false); "
        f"$presentation.SaveAs('{target}', 1); "
        "$presentation.Close(); $powerpoint.Quit()"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=True, capture_output=True, text=True, timeout=90,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        details = getattr(error, "stderr", "") or str(error)
        print(f"[!] Could not convert the PPTX to legacy .ppt: {details}")
        return None
    return ppt_path if Path(ppt_path).is_file() else None


def generate_ppt(topic_data: dict, output_filepath: str = "Lecture_Package.pptx") -> list:
    """Ask Groq for restricted python-pptx code, create a PPTX, then create a .ppt copy."""
    output_path = str(Path(output_filepath).resolve())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    prompt = PPT_CODE_PROMPT.format(
        topic=topic_data.get("topic", "Untitled lesson"),
        audience=topic_data.get("audience_level", "general learners"),
        duration=topic_data.get("duration", "a standard class period"),
        goals=", ".join(topic_data.get("key_goals", [])),
    )
    code = ""

    try:
        response = client.chat.completions.create(
            model=MODEL_PPT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=1000,
        )
        code = _extract_code(response.choices[0].message.content)
        slides_data = _run_pptx_code(code, output_path)
    except Exception as error:
        # Generated code can occasionally contain a small syntax or layout mistake.
        # Give the model one bounded repair pass instead of silently producing no deck.
        try:
            repair_prompt = (
                f"{prompt}\n\nThe following draft failed validation or execution:\n"
                f"```python\n{code}\n```\n\n"
                f"Error: {error}\n\nReturn a complete corrected replacement. Follow every constraint above."
            )
            response = client.chat.completions.create(
                model=MODEL_PPT,
                messages=[{"role": "user", "content": repair_prompt}],
                temperature=0.1,
                max_tokens=1000,
            )
            repaired_code = _extract_code(response.choices[0].message.content)
            slides_data = _run_pptx_code(repaired_code, output_path)
        except Exception as repair_error:
            print(f"[!] PPT generation failed after one repair attempt: {repair_error}")
            return []

    print(f"[+] Editable presentation saved: {output_path}")
    legacy_path = _convert_to_legacy_ppt(output_path)
    if legacy_path:
        print(f"[+] Legacy PowerPoint copy saved: {legacy_path}")
    return slides_data
