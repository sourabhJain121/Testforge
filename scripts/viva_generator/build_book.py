"""
build_book.py - Master Assembly Script for TestForge Viva Answer Book.
Generates: docs/VIVA_PREPARATION/TestForge_Complete_Viva_Preparation_and_All_Questions_Answered.docx
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("scripts/viva_generator"))

import time
import docx
from docx.shared import Inches, Pt, RGBColor

# Import local viva generator modules
from scripts.viva_generator.styles import (
    setup_document_styles,
    add_cover_page,
    add_h1,
    add_h2,
    add_h3,
    add_p,
    add_bullet,
    add_callout,
    add_code_block,
    add_table
)
from scripts.viva_generator import content_chapters as cc
from scripts.viva_generator.content_questions_1_to_5 import add_questions_part_1_to_5
from scripts.viva_generator.content_questions_6_to_10 import add_questions_part_6_to_10
from scripts.viva_generator.content_additional_and_defense import (
    add_additional_defense_questions,
    add_chapters_26_to_31
)


def build_complete_viva_book():
    print("=" * 80)
    print("TESTFORGE COMPLETE VIVA PREPARATION BOOK GENERATOR")
    print("=" * 80)
    start_time = time.time()

    # 1. Initialize Document
    print("[1/6] Initializing Document & Applying Academic Styles...")
    doc = docx.Document()
    setup_document_styles(doc)

    # 2. Cover Page
    print("[2/6] Generating Chapter 1: Cover Page & Metadata...")
    add_cover_page(
        doc=doc,
        title="TestForge: Complete Viva Voce Defense & Comprehensive Examination Answer Book",
        subtitle="Autonomous Multi-Agent Unit Test Hardening via Mutation-Verified Reflection Loops — Exhaustive Source-Code Audit, Complete Viva Question Bank (All 114 Questions Answered), High-Probability Defense Questions, and Academic Verification Evidence",
        metadata_rows=[
            ("Project Name", "TestForge (Autonomous Multi-Agent Unit Test Hardening Engine)"),
            ("Academic Degree", "Master of Science / Bachelor of Engineering in Computer Science"),
            ("Department / Faculty", "Department of Computer Science & Software Engineering"),
            ("Institution", "Academic Project Evaluation Board"),
            ("Candidate / Author", "Sourabh (TestForge Lead Architect & Engineer)"),
            ("Defense Date", "November 2026"),
            ("Evaluation Status", "All 10 Academic Evaluation Criteria Complete & Verified"),
            ("Verified Test Suite", "598 Passed, 0 Failed, 0 Skipped (100% Pass Rate)"),
            ("Primary Benchmarks", "discount.py (89.47% raw / 94.44% adj) | uploaded_logistics_engine.py (68.22% raw / 75.21% adj)"),
            ("Security Defense Rate", "100% Mitigation (120/120 deterministic security trials passed)"),
            ("Document Deliverable", "Phase 15 Master Single-Document Deliverable (All Questions Answered)")
        ]
    )

    # 3. Chapters 2 through 23
    print("[3/6] Generating Foundational Technical Chapters (Chapters 2 to 23)...")
    cc.add_table_of_contents(doc)
    cc.add_chapter_project_overview(doc)
    cc.add_chapter_problem_statement(doc)
    cc.add_chapter_technology_stack(doc)
    cc.add_chapter_complete_architecture(doc)
    cc.add_chapter_blackboard(doc)
    cc.add_chapter_mcp(doc)
    cc.add_chapter_ast_and_generation(doc)
    cc.add_chapter_mutation_testing(doc)
    cc.add_chapter_reflection_loop(doc)
    cc.add_chapter_benchmarking_and_results(doc)

    # 4. Mandatory Viva Question Bank (Q1 to Q114)
    print("[4/6] Generating Complete Answers to Viva Question Bank (Questions 1 to 114)...")
    add_h1(doc, "Section II: Complete Viva Voce Question Bank (All 114 Questions Answered)")
    add_p(
        doc,
        "This section provides exhaustive, fully verified answers to every question in the 114-question academic viva question bank across 10 core categories. Every single question adheres strictly to the mandatory 7-field structure: Short Viva Answer, Detailed Explanation, How TestForge Implements It, Concrete Example, Why This Design Was Chosen, Possible Examiner Follow-up, and Evidence / Verification Status."
    )
    add_questions_part_1_to_5(doc)
    add_questions_part_6_to_10(doc)

    # 5. Additional Defense Questions (Q115 to Q135)
    print("[5/6] Generating Additional High-Probability Defense Questions (Questions 115 to 135)...")
    add_additional_defense_questions(doc)

    # 6. Chapters 26 to 31
    print("[6/6] Generating Practical Code Walkthrough, Defense Strategy, and Reference Appendices (Chapters 26 to 31)...")
    add_chapters_26_to_31(doc)

    # Ensure output directory exists
    output_dir = "docs/VIVA_PREPARATION"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "TestForge_Complete_Viva_Preparation_and_All_Questions_Answered.docx")

    print(f"Saving publication-quality DOCX to {output_path}...")
    doc.save(output_path)
    elapsed = time.time() - start_time

    # Verification and Quality Audit
    file_size_bytes = os.path.getsize(output_path)
    file_size_kb = file_size_bytes / 1024.0

    print("=" * 80)
    print("VIVA BOOK GENERATION COMPLETE!")
    print(f"File Path: {output_path}")
    print(f"File Size: {file_size_kb:.2f} KB ({file_size_bytes:,} bytes)")
    print(f"Elapsed Time: {elapsed:.2f} seconds")
    print(f"Total Paragraphs: {len(doc.paragraphs)}")
    print(f"Total Tables: {len(doc.tables)}")
    print("=" * 80)

    # Audit question counts
    q_count = 0
    for t in doc.tables:
        if len(t.rows) >= 1:
            first_cell_text = t.rows[0].cells[0].text
            if "Question " in first_cell_text and "Short viva answer" in first_cell_text:
                q_count += 1
    print(f"Verified Questions in Document Tables: {q_count} (Expected: 135 total = 114 original + 21 additional)")
    print("=" * 80)


if __name__ == "__main__":
    build_complete_viva_book()
