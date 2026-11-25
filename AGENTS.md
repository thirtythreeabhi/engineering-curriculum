# Repository Guide for Coding Agents

## Project structure

- `latex/common/` contains the shared preamble, foundations chapter, and bibliography.
- `latex/master/` assembles the five volumes into the master textbook.
- `latex/volume-1/` through `latex/volume-5/` contain the editable chapter sources and individual volume documents.
- `exercises/` contains standalone exercises and labs; `projects/` contains reference implementations.
- PDFs at the repository root and under `latex/` are generated deliverables. Their corresponding `.tex` files are the source of truth.

## Build the books

- Run builds from the repository root with `make master`, `make volume-1` through `make volume-5`, `make curriculum-map`, or `make all`.
- `make master` runs pdfLaTeX, BibTeX, and two further pdfLaTeX passes so citations, cross-references, and the table of contents are refreshed.
- Do not treat a PDF from a single pdfLaTeX pass as final. Check the command exit status and inspect the final log for LaTeX errors and unresolved references.
- `make clean` removes generated LaTeX auxiliary files. It does not remove the PDFs.

## Editing LaTeX content

- Keep shared packages, colors, and layout settings in `latex/common/preamble.tex`; keep shared bibliography entries in `latex/common/bibliography.bib`.
- Chapter `\input` paths are resolved from the directory used to run that document's build target. When adding, removing, or renaming a chapter, update the relevant volume document and `latex/master/master-textbook.tex`.
- Escape ampersands in prose as `\&`; reserve bare `&` for alignment columns in tables and similar environments. Use `\_` for underscores in ordinary text and `\texttt{...}` for code identifiers. Escape special characters inside code markup too.
- Titles written to the table of contents are moving arguments. Use robust LaTeX forms such as `\protect\&` where needed, and rebuild the master twice or with `make master` to refresh its contents and page numbers.
- Do not edit generated PDFs or auxiliary files by hand. Fix the source and rebuild the relevant deliverable.

## Exercises and projects

- Keep exercises runnable and consistent with the commands and file paths documented in `exercises/README.md` and each project's README.
- Follow the language and framework conventions already used within the affected exercise or project. Avoid changing unrelated projects when editing one implementation.

## Repository changes

- Preserve unrelated user changes in the working tree.
- Do not commit or push unless the user explicitly requests it.
- Keep credentials, tokens, and local build outputs other than the tracked PDFs out of commits.
