from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

# AcceleratorOptions moved to its own module in newer Docling releases;
# fall back to the legacy location for older versions.
try:
    from docling.datamodel.accelerator_options import (
        AcceleratorDevice,
        AcceleratorOptions,
    )
except ImportError:  # pragma: no cover - depends on docling version
    from docling.datamodel.pipeline_options import (
        AcceleratorDevice,
        AcceleratorOptions,
    )

__all__ = ["ParsedElement", "parse_pdf"]

logger = logging.getLogger(__name__)

# Building a DocumentConverter loads the layout + table-structure models,
# which is slow. Cache converters by their pipeline options so repeated
# calls (e.g. re-running a notebook cell) reuse the already-loaded models.
_CONVERTER_CACHE: dict[tuple, DocumentConverter] = {}


def _get_converter(
    do_ocr: bool,
    do_table_structure: bool,
    table_mode: TableFormerMode,
    num_threads: int,
) -> DocumentConverter:
    key = (do_ocr, do_table_structure, table_mode, num_threads)
    converter = _CONVERTER_CACHE.get(key)
    if converter is not None:
        return converter

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = do_ocr
    pipeline_options.do_table_structure = do_table_structure
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=num_threads,
        device=AcceleratorDevice.CPU,
    )
    if do_table_structure:
        pipeline_options.table_structure_options.mode = table_mode

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )
    _CONVERTER_CACHE[key] = converter
    return converter


@dataclass
class ParsedElement:
    content: str
    type: str  # "text", "table", "heading"
    page: int
    section_title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def parse_pdf(
    path: str | Path,
    *,
    do_ocr: bool = False,
    do_table_structure: bool = True,
    fast_tables: bool = True,
    num_threads: int | None = None,
    status_callback: Callable[[str], None] | None = None,
) -> list[ParsedElement]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    def _emit(msg: str) -> None:
        logger.info(msg)
        if status_callback is not None:
            status_callback(msg)

    table_mode = (
        TableFormerMode.FAST if fast_tables else TableFormerMode.ACCURATE
    )
    if num_threads is None:
        num_threads = os.cpu_count() or 4

    _emit(
        f"Configuring Docling pipeline "
        f"(OCR={'on' if do_ocr else 'off'}, "
        f"table_structure={'on' if do_table_structure else 'off'}, "
        f"table_mode={table_mode.value if do_table_structure else 'n/a'}, "
        f"threads={num_threads})"
    )

    converter = _get_converter(
        do_ocr=do_ocr,
        do_table_structure=do_table_structure,
        table_mode=table_mode,
        num_threads=num_threads,
    )

    _emit(
        "Running Docling conversion (layout + table-structure "
        "inference on CPU, ~1-5 min for a 50-page PDF)..."
    )
    t0 = time.time()
    result = converter.convert(str(path))
    doc = result.document
    _emit(f"Docling conversion finished in {time.time() - t0:.1f}s")

    _emit("Extracting structured elements...")
    elements: list[ParsedElement] = []
    current_section = ""

    for item in doc.iterate_items():
        element, _level, *_ = item
        page_num = _get_page_number(element, doc)

        if hasattr(element, "label"):
            label = element.label.value if hasattr(
                element.label, "value"
            ) else str(element.label)
        else:
            label = "text"

        # Skip picture/image elements
        if label in ("picture", "figure"):
            continue

        if label in ("section_header", "title"):
            current_section = _get_text(element, doc)
            elements.append(ParsedElement(
                content=current_section,
                type="heading",
                page=page_num,
                section_title=current_section,
            ))
        elif label == "table":
            table_text = _export_table(element, doc)
            elements.append(ParsedElement(
                content=table_text,
                type="table",
                page=page_num,
                section_title=current_section,
            ))
        else:
            text = _get_text(element, doc)
            if text.strip():
                elements.append(ParsedElement(
                    content=text,
                    type="text",
                    page=page_num,
                    section_title=current_section,
                ))

    return elements


def _get_text(element, doc=None) -> str:
    if hasattr(element, "text"):
        return element.text
    if hasattr(element, "export_to_markdown"):
        # Newer Docling expects the doc argument; older versions don't
        # accept it. Prefer passing doc to avoid the deprecation warning.
        if doc is not None:
            try:
                return element.export_to_markdown(doc)
            except TypeError:
                return element.export_to_markdown()
        return element.export_to_markdown()
    return str(element)


def _export_table(element, doc=None) -> str:
    if hasattr(element, "export_to_markdown"):
        # Newer Docling expects the doc argument; older versions don't
        # accept it. Prefer passing doc to avoid the deprecation warning.
        if doc is not None:
            try:
                return element.export_to_markdown(doc)
            except TypeError:
                return element.export_to_markdown()
        return element.export_to_markdown()
    if hasattr(element, "text"):
        return element.text
    return str(element)


def _get_page_number(element, doc) -> int:
    if hasattr(element, "prov") and element.prov:
        for prov in element.prov:
            if hasattr(prov, "page_no"):
                return prov.page_no
    return 0
