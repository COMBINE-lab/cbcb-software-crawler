from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .crawler import crawl
from .render import render_bundle, render_table_fragment

app = FastAPI(title="CBCB Software Crawler")

package_dir = Path(__file__).parent
app.mount("/assets", StaticFiles(directory=package_dir / "assets"), name="assets")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _page()


@app.post("/crawl", response_class=HTMLResponse)
def run_crawl(
    repos: str = Form(...),
    active_years: int = Form(2),
    out: str = Form("dist"),
) -> str:
    try:
        entries, report = crawl(repos, active_years=active_years)
        output = render_bundle(entries, report, out)
        preview = render_table_fragment(entries, report)
        message = f"Generated {report.valid_count} valid entries in {Path(output).resolve()}"
        links = (
            f'<p class="admin-links"><a href="/generated/index.html?out={out}">Open static catalog</a> '
            f'<a href="/generated/report.html?out={out}">Open report</a></p>'
        )
        return _page(message=message, preview=preview, links=links)
    except Exception as exc:
        return _page(error=f"{exc.__class__.__name__}: {exc}")


@app.get("/generated/{file_path:path}")
def generated_file(file_path: str, out: str = "dist") -> FileResponse:
    root = Path(out).resolve()
    target = (root / file_path).resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=400, detail="requested file is outside the output directory")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="generated file not found")
    return FileResponse(target)


def _page(message: str = "", error: str = "", preview: str = "", links: str = "") -> str:
    status = ""
    if message:
        status = f'<div class="notice">{message}</div>{links}'
    if error:
        status = f'<div class="error">{error}</div>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CBCB Software Crawler</title>
  <link rel="stylesheet" href="/assets/catalog.css">
</head>
<body>
  <header class="site-header">
    <div class="site-brand">University of Maryland</div>
    <div class="site-header__bar"><div class="site-header__logo-text">Center for Bioinformatics and Computational Biology</div></div>
  </header>
  <main class="catalog-shell admin-shell">
    <section class="catalog-hero">
      <p class="eyebrow">Local Admin Tool</p>
      <h1>CBCB Software Crawler</h1>
      <p>Generate a searchable catalog from a central repository list.</p>
    </section>
    <form method="post" action="/crawl" class="admin-form">
      <label>repos.yml paths or URLs
        <textarea name="repos" placeholder="examples/repos.yml&#10;https://raw.githubusercontent.com/..." required></textarea>
      </label>
      <label>Active years
        <input name="active_years" type="number" min="0" value="2">
      </label>
      <label>Output directory
        <input name="out" value="dist">
      </label>
      <button type="submit">Run Crawl</button>
    </form>
    {status}
    {preview}
  </main>
</body>
</html>"""
