#!/usr/bin/env python3
"""Universal Office & PPTX Document Validator (Rigorous 4-Gate Quality Verification)"""

import os
import sys
import argparse
from pptx import Presentation
from pptx.enum.text import PP_ALIGN


def _check_zorder_occlusion(shape, shape_box: tuple, text_boxes: list, s_num: int, shape_idx: int) -> None:
    """Anti-Occlusion Shield: Check if solid filled shape obscures earlier text frames."""
    fill_type = getattr(getattr(shape, "fill", None), "type", None)
    if fill_type is None or int(fill_type) not in (1, 3, 4):  # Solid / Pattern / Texture fill
        return

    sx1, sy1, sx2, sy2 = shape_box
    for prev_idx, (tx1, ty1, tx2, ty2), txt in text_boxes:
        ix1, iy1 = max(sx1, tx1), max(sy1, ty1)
        ix2, iy2 = min(sx2, tx2), min(sy2, ty2)
        if ix2 <= ix1 or iy2 <= iy1:
            continue
        inter_area = (ix2 - ix1) * (iy2 - iy1)
        text_area = max(0.001, (tx2 - tx1) * (ty2 - ty1))
        if (inter_area / text_area) >= 0.75:
            raise ValueError(
                f"[Gate 2: Geometry Failed] Layering Occlusion on slide {s_num}: Solid shape (Index {shape_idx + 1}) "
                f"renders over earlier text frame (Index {prev_idx + 1}: '{txt}'), obscuring content!"
            )


def _validate_shape_geometry(shape, shape_idx: int, s_num: int, slide_w_in: float, slide_h_in: float, text_boxes: list) -> None:
    """Gate 2: Validate spatial bounds and Z-Order occlusion."""
    if not (hasattr(shape, "left") and hasattr(shape, "width") and shape.left is not None and shape.width is not None):
        return

    x_in, y_in = shape.left / 914400.0, shape.top / 914400.0
    w_in, h_in = shape.width / 914400.0, shape.height / 914400.0

    if w_in <= 0 or h_in <= 0:
        raise ValueError(f"[Gate 2: Geometry Failed] Shape {shape_idx + 1} on slide {s_num} has non-positive dimensions: w={w_in:.2f}\", h={h_in:.2f}\"")
    if (x_in + w_in) > (slide_w_in + 1.0) or (y_in + h_in) > (slide_h_in + 1.0):
        raise ValueError(f"[Gate 2: Geometry Failed] Shape {shape_idx + 1} on slide {s_num} overflows canvas bounds (Canvas: {slide_w_in:.2f}\"x{slide_h_in:.2f}\")")

    shape_box = (x_in, y_in, x_in + w_in, y_in + h_in)
    has_text = False
    if shape.has_text_frame and shape.text_frame.text and shape.text_frame.text.strip():
        has_text = True
        text_boxes.append((shape_idx, shape_box, shape.text_frame.text.strip()[:20]))

    shape_type = getattr(shape, "shape_type", None)
    if not has_text and shape_type is not None and int(shape_type) == 1:
        try:
            _check_zorder_occlusion(shape, shape_box, text_boxes, s_num, shape_idx)
        except (AttributeError, TypeError, ValueError) as ex:
            if "[Gate 2: Geometry Failed]" in str(ex):
                raise


def _validate_paragraph(p, p_idx: int, para_count: int, *, check_align: bool, min_font_pt: float, s_num: int) -> None:
    """Gate 3: Validate paragraph and run typography bounds."""
    p_text = p.text.strip()
    if not p_text:
        return

    p_pt = p.font.size.pt if (p.font and p.font.size) else None
    if p_pt is not None and p_pt < (min_font_pt - 0.05):
        raise ValueError(f"[Gate 3: Typography Failed] Font size {p_pt}pt on slide {s_num} below minimum {min_font_pt}pt rule: '{p_text[:30]}'")

    for r in p.runs:
        r_text = r.text.strip()
        r_pt = r.font.size.pt if (r.font and r.font.size) else None
        if r_text and r_pt is not None and r_pt < (min_font_pt - 0.05):
            raise ValueError(f"[Gate 3: Typography Failed] Run font size {r_pt}pt on slide {s_num} below minimum {min_font_pt}pt rule: '{r_text[:30]}'")

    if check_align and para_count > 2 and p_idx > 0 and getattr(p, "alignment", None) == PP_ALIGN.CENTER and len(p_text) > 15:
        raise ValueError(f"[Gate 3: Typography Failed] Body paragraph on slide {s_num} is centered! Must be explicitly left-aligned: '{p_text[:25]}'")


def validate_pptx(filepath: str, min_size: int = 1024, min_font_pt: float = 13.5, verbose: bool = True) -> bool:
    """Rigorous 4-Gate consolidated quality verification for PPTX presentations."""
    # Gate 1: Package Integrity & Non-Empty Structure
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"[Gate 1: Structure Failed] Target file does not exist: {filepath}")
    size = os.path.getsize(filepath)
    if size < min_size:
        raise ValueError(f"[Gate 1: Structure Failed] File size {size} bytes below threshold ({min_size} bytes): {filepath}")
    try:
        prs = Presentation(filepath)
    except Exception as e:
        raise RuntimeError(f"[Gate 1: Structure Failed] PPTX binary stream / XML package corrupt: {e}")
    slides_count = len(prs.slides)
    if slides_count <= 0:
        raise ValueError(f"[Gate 1: Structure Failed] PPTX contains 0 slides: {filepath}")

    slide_w_in = prs.slide_width.inches if hasattr(prs.slide_width, "inches") else (prs.slide_width / 914400.0)
    slide_h_in = prs.slide_height.inches if hasattr(prs.slide_height, "inches") else (prs.slide_height / 914400.0)

    for s_idx, slide in enumerate(prs.slides):
        s_num = s_idx + 1
        text_chunks = []
        text_boxes = []  # Track for Gate 2 Z-Order occlusion: (shape_idx, bbox, snippet)
        pic_count = 0
        shapes_count = len(slide.shapes)

        # Gate 4: Non-empty slide check
        if shapes_count == 0:
            raise ValueError(f"[Gate 4: Asset Density Failed] Slide {s_num} is completely empty without shapes!")

        # Single-pass inspection across all shapes on this slide
        for shape_idx, shape in enumerate(slide.shapes):
            shape_type = getattr(shape, "shape_type", None)
            if shape_type is not None and int(shape_type) in (13, 6):  # 13 = Picture, 6 = Group/SVG
                pic_count += 1

            # Gate 2: Spatial Geometry & Layering Bounds
            _validate_shape_geometry(shape, shape_idx, s_num, slide_w_in, slide_h_in, text_boxes)

            # Gate 3: Executive Typography & Encoding Standards (Flatten text frames)
            tfs = []
            if shape.has_text_frame:
                tfs.append((shape.text_frame, True))
            elif shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        if cell.text_frame:
                            tfs.append((cell.text_frame, False))

            for tf, check_align in tfs:
                if tf.text:
                    text_chunks.append(tf.text)
                para_count = len(tf.paragraphs)
                for p_idx, p in enumerate(tf.paragraphs):
                    _validate_paragraph(p, p_idx, para_count, check_align=check_align, min_font_pt=min_font_pt, s_num=s_num)

        # Zero-Tofu Unicode Shield
        if "\ufffd" in " ".join(text_chunks):
            raise ValueError(f"[Gate 3: Typography Failed] Font glyph tofu / Unicode replacement character detected on slide {s_num}!")

        # Gate 4: Visual Asset Density Check (Multi-card SVG Icon Requirement)
        if shapes_count >= 6 and pic_count == 0:
            raise ValueError(f"[Gate 4: Asset Density Failed] Slide {s_num} contains multi-card layout ({shapes_count} shapes) but 0 vector SVG icons rendered!")

    if verbose:
        size_kb = round(size / 1024, 2)
        print(f"[Verification PASSED] 4/4 Gates OK | {slides_count} Slide(s) | {size_kb} KB | {filepath}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Validate Office PPTX presentation files (4-Gate Quality Gate)")
    parser.add_argument("path", help="Path to PPTX file to validate")
    parser.add_argument("--min-size", type=int, default=1024, help="Minimum file size in bytes")
    parser.add_argument("--min-font", type=float, default=13.5, help="Minimum allowed font size in pt (default 13.5pt)")
    parser.add_argument("-v", "--verbose", action="store_true", default=True, help="Enable verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output on success")

    args = parser.parse_args()
    try:
        validate_pptx(args.path, min_size=args.min_size, min_font_pt=args.min_font, verbose=not args.quiet)
        return 0
    except Exception as e:
        print(f"[Verification FAILED] {args.path} -> {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
