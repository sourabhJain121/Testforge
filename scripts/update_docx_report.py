import zipfile
import re
import os
import xml.etree.ElementTree as ET
from PIL import Image

TARGET_DOCX = "docs/TestForge_Final_Project_Report_Formatted.docx"
DELIVERABLE_DOCX = "docs/DELIVERABLES/TestForge_Final_Project_Report_Formatted.docx"
SCREENSHOT_DIR = "/tmp/docx_screenshots"
OUTPUT_DOCX = "/tmp/TestForge_Final_Project_Report_Formatted.docx"

# 24 Peer-Reviewed References
REFERENCES = [
    "1. R. A. DeMillo, R. J. Lipton, and F. G. Sayward, 'Hints on test data selection: Help for the practicing programmer,' Computer, vol. 11, no. 4, pp. 34–41, Apr. 1978.",
    "2. R. G. Hamlet, 'Testing programs with the aid of a compiler,' IEEE Transactions on Software Engineering, vol. SE-3, no. 4, pp. 279–290, Jul. 1977.",
    "3. Y. Jia and M. Harman, 'An analysis and survey of the development of mutation testing,' IEEE Transactions on Software Engineering, vol. 37, no. 5, pp. 649–678, Sep.–Oct. 2011.",
    "4. R. Just, D. Jalali, L. Inozemtseva, M. D. Ernst, R. Holmes, and G. Fraser, 'Are mutants a valid substitute for real faults in software testing?' in Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering (FSE), Hong Kong, China, 2014, pp. 654–665.",
    "5. A. J. Offutt, 'Investigations of the software testing coupling effect,' ACM Transactions on Software Engineering and Methodology (TOSEM), vol. 1, no. 1, pp. 5–20, Jan. 1992.",
    "6. M. Papadakis, M. Kintis, J. Zhang, Y. Jia, Y. Le Traon, and M. Harman, 'Mutation testing advances: An analysis and survey,' in Advances in Computers, vol. 112, A. Memon, Ed. Amsterdam, Netherlands: Elsevier, 2019, pp. 275–378.",
    "7. H. G. Rice, 'Classes of recursively enumerable sets and their decision problems,' Transactions of the American Mathematical Society, vol. 74, no. 2, pp. 358–366, Mar. 1953.",
    "8. T. A. Budd and D. Angluin, 'Two notions of correctness and their relation to testing,' Acta Informatica, vol. 18, no. 1, pp. 31–45, Nov. 1982.",
    "9. B. J. Grün, D. Schuler, and V. Zeller, 'The impact of equivalent mutants,' in Proceedings of the 2nd International Conference on Software Testing, Verification and Validation Workshops (ICSTW), Denver, CO, USA, 2009, pp. 192–199.",
    "10. M. Papadakis, Y. Jia, M. Harman, and Y. Le Traon, 'Trivial compiler equivalence: A large scale empirical study of a simple, fast and effective equivalent mutant detection technique,' in Proceedings of the 37th International Conference on Software Engineering (ICSE), Florence, Italy, 2015, pp. 936–946.",
    "11. M. J. Harrold, R. Gupta, and M. L. Soffa, 'A methodology for controlling the size of a test suite,' ACM Transactions on Software Engineering and Methodology (TOSEM), vol. 2, no. 3, pp. 270–285, Jul. 1993.",
    "12. S. Yoo and M. Harman, 'Regression testing minimization, selection and prioritization: A survey,' Software Testing, Verification and Reliability (STVR), vol. 22, no. 2, pp. 67–120, Mar. 2012.",
    "13. G. Fraser and A. Arcuri, 'EvoSuite: Automatic test suite generation for object-oriented software,' in Proceedings of the 19th ACM SIGSOFT Symposium on the Foundations of Software Engineering (FSE), Szeged, Hungary, 2011, pp. 416–419.",
    "14. C. Pacheco, S. K. Lahiri, M. D. Ernst, and T. Ball, 'Feedback-directed random test generation,' in Proceedings of the 29th International Conference on Software Engineering (ICSE), Minneapolis, MN, USA, 2007, pp. 75–84.",
    "15. S. Lukasczyk and G. Fraser, 'Pynguin: Automated unit test generation for Python,' in Proceedings of the 44th International Conference on Software Engineering: Companion Proceedings (ICSE-Companion), Pittsburgh, PA, USA, 2022, pp. 168–172.",
    "16. N. Alshahwan and M. Harman, 'Automated mobile app testing at scale: What have we learned from Sapienz at Facebook?' in Proceedings of the 40th International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP), Gothenburg, Sweden, 2018, pp. 2–3.",
    "17. A. Derezińska and K. Hałas, 'Experimental evaluation of mutation testing approaches to Python programs,' in Proceedings of the 7th International Conference on Software Testing, Verification and Validation Workshops (ICSTW), Cleveland, OH, USA, 2014, pp. 156–164.",
    "18. N. Tillmann and J. de Halleux, 'Pex—White box test generation for .NET,' in Tests and Proofs (TAP), ser. Lecture Notes in Computer Science, B. Beckert and R. Hähnle, Eds., vol. 4966. Berlin, Heidelberg: Springer, 2008, pp. 134–153.",
    "19. M. Schäfer, S. Nadi, A. Eghbali, and F. Tip, 'An empirical evaluation of using large language models for automated unit test generation,' IEEE Transactions on Software Engineering, vol. 50, no. 1, pp. 85–105, Jan. 2024.",
    "20. C. Lemieux, J. P. Inala, S. K. Lahiri, and S. Sen, 'CodaMosa: Escaping coverage plateaus in test generation with pre-trained large language models,' in Proceedings of the 45th International Conference on Software Engineering (ICSE), Melbourne, Australia, 2023, pp. 919–931.",
    "21. N. Alshahwan, R. Gao, M. Harman, et al., 'Automated unit test improvement using large language models at Meta,' in Proceedings of the 32nd ACM SIGSOFT International Symposium on Foundations of Software Engineering (FSE), Porto de Galinhas, Brazil, 2024, pp. 145–156.",
    "22. A. M. Dakhel, M. Amin, and H. Hemmati, 'Effective test generation using pre-trained large language models and mutation testing,' Information and Software Technology, vol. 171, p. 107468, Jul. 2024.",
    "23. N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao, 'Reflexion: Language agents with verbal reinforcement learning,' in Advances in Neural Information Processing Systems (NeurIPS), vol. 36, New Orleans, LA, USA, 2023, pp. 8634–8652.",
    "24. Q. Wu, G. Bansal, J. Zhang, Y. Wu, B. Li, E. Zhu, L. Jiang, X. Zhang, S. Zhang, J. Liu, A. H. Awadallah, R. W. White, D. Burger, and C. Wang, 'AutoGen: Enabling next-gen LLM applications via multi-agent conversation,' in Proceedings of the 1st Conference on Language Modeling (COLM), 2024; also arXiv:2308.08155, 2023."
]

# Section 3.1 Synthesis Content
SEC_31_HEADING = "3.1 Survey of Foundational & State-of-the-Art Literature"

SEC_31_P1 = (
    "Mutation testing was originally formulated by DeMillo, Lipton, and Sayward [1] and Hamlet [2] as a rigorous fault-based "
    "technique grounded in two central hypotheses: the Competent Programmer Hypothesis and the Coupling Effect. As synthesized in "
    "comprehensive surveys by Jia and Harman [3] and Papadakis et al. [6], mutation testing systematically measures the fault-detection "
    "capability of a test suite by injecting small, syntactically valid faults into the program's abstract syntax tree (AST). Empirical "
    "validation by Just et al. [4] across real-world software defects confirmed that mutant kill rates correlate significantly more "
    "strongly with actual fault detection than traditional code coverage metrics. Offutt [5] formally investigated the mutation coupling "
    "effect, demonstrating empirically that test suites capable of killing simple, first-order synthetic mutants are also overwhelmingly "
    "effective at detecting complex multi-fault interactions. In TestForge, these foundational principles guide our AST mutation engine, "
    "establishing the mutation score as our primary objective function."
)

SEC_31_P2 = (
    "A notorious theoretical and practical impediment in mutation analysis is the Equivalent Mutant Problem (EMP). As established "
    "by Rice's theorem [7], determining whether a syntactically altered program is functionally equivalent to the original is "
    "undecidable in the general case. Budd and Angluin [8] formalized these correctness boundaries in relation to program testing, while "
    "Grün, Schuler, and Zeller [9] empirically demonstrated that equivalent mutants artificially depress mutation scores and waste "
    "human and computational effort. To mitigate EMP, Papadakis et al. [10] developed Trivial Compiler Equivalence (TCE), demonstrating "
    "that compiler-level AST optimizations can rapidly detect a substantial fraction of equivalent mutants. Furthermore, iterative test "
    "synthesis risks runaway test suite bloat. Harrold, Gupta, and Soffa [11] introduced foundational heuristics for test suite size control, "
    "while Yoo and Harman [12] surveyed regression suite minimization, selection, and prioritization algorithms. TestForge addresses "
    "these dual challenges through an AST-level semantic equivalence classifier and a submodular greedy set-cover minimizer that "
    "compresses suite size while preserving 100% of the achieved kill score."
)

SEC_31_P3 = (
    "Automated test generation has evolved significantly across search-based and symbolic execution paradigms. Fraser and Arcuri [13] "
    "developed EvoSuite, employing genetic algorithms to optimize whole test suites targeting both branch coverage and weak mutation "
    "goals. Pacheco et al. [14] introduced feedback-directed random test generation in Randoop, pruning illegal object constructor sequences "
    "via execution observations. In the Python ecosystem, Lukasczyk and Fraser [15] created Pynguin, extending search-based generation to "
    "dynamic languages, while Derezińska and Hałas [17] investigated mutation operator effectiveness specific to Python syntax. Alshahwan "
    "and Harman [16] deployed Sapienz at Meta, demonstrating multi-objective search-based testing at industrial scale, and Tillmann and "
    "de Halleux [18] advanced dynamic symbolic execution for automated white-box test generation in Pex. While effective for branch "
    "exploration, these systems struggle with stateful data structures requiring coordinated multi-step method invocations, a limitation "
    "TestForge surmounts via stateful call-graph planning."
)

SEC_31_P4 = (
    "Recent advances leverage large language models (LLMs) for automated unit test generation. Schäfer et al. [19] empirically evaluated "
    "LLMs in TestPilot, showing high syntactic fluency but identifying frequent assertion omissions. Lemieux et al. [20] proposed CodaMosa, "
    "combining search-based testing with LLM prompt infilling to escape coverage plateaus. At Meta, Alshahwan et al. [21] deployed TestGen-LLM, "
    "verifying generated test assertions against production regressions to filter out hallucinations. Dakhel, Amin, and Hemmati [22] "
    "introduced MuTAP, demonstrating that mutation testing provides an ideal execution-grounded objective function for filtering LLM-generated "
    "tests. To orchestrate complex reasoning, Shinn et al. [23] established Reflexion, demonstrating that language agents improve "
    "decision-making via verbal reinforcement learning over environment feedback. Concurrently, Wu et al. [24] introduced AutoGen, "
    "demonstrating that conversational multi-agent systems outperform monolithic LLMs on complex software engineering tasks. TestForge "
    "unites these frontiers into an 8-agent blackboard architecture with Google ADK and CrewAI, achieving closed-loop adversarial test "
    "hardening with verified Pass@1 integrity."
)

def build_p_xml(text, is_heading=False, is_ref=False):
    text_escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if is_heading:
        return (
            f'<w:p><w:pPr><w:pStyle w:val="Heading2"/><w:spacing w:before="200" w:after="76"/><w:ind w:left="-5"/></w:pPr>'
            f'<w:r><w:t>{text_escaped}</w:t></w:r></w:p>'
        )
    elif is_ref:
        return (
            f'<w:p><w:pPr><w:ind w:left="355" w:right="0" w:hanging="355"/><w:jc w:val="both"/></w:pPr>'
            f'<w:r><w:t>{text_escaped}</w:t></w:r></w:p>'
        )
    else:
        return (
            f'<w:p><w:pPr><w:spacing w:after="169"/><w:ind w:left="-5" w:right="0"/><w:jc w:val="both"/></w:pPr>'
            f'<w:r><w:t>{text_escaped}</w:t></w:r></w:p>'
        )

def main():
    with zipfile.ZipFile(TARGET_DOCX, 'r') as zin:
        file_map = {item.filename: zin.read(item.filename) for item in zin.infolist()}

    doc_xml = file_map['word/document.xml'].decode('utf-8')

    # 1. Expand Section 3
    target_heading = "Explicit Research Gaps Identified in Literature"
    pos_gaps = doc_xml.find(target_heading, 69585) # after TOC
    if pos_gaps == -1:
        raise RuntimeError("Could not locate 'Explicit Research Gaps Identified in Literature' in body")
    
    p_start_gaps = doc_xml.rfind('<w:p ', 0, pos_gaps)

    # Prepare Section 3.1 XML
    sec31_xml = (
        build_p_xml(SEC_31_HEADING, is_heading=True)
        + build_p_xml(SEC_31_P1)
        + build_p_xml(SEC_31_P2)
        + build_p_xml(SEC_31_P3)
        + build_p_xml(SEC_31_P4)
    )

    # Insert Section 3.1 right before the gaps heading, and update gaps heading to 3.2
    doc_xml = (
        doc_xml[:p_start_gaps]
        + sec31_xml
        + doc_xml[p_start_gaps:pos_gaps]
        + "3.2 Explicit Research Gaps Identified in Literature"
        + doc_xml[pos_gaps + len(target_heading):]
    )
    print("Section 3.1 successfully inserted and Section 3.2 heading updated.")

    # 2. Update References
    pos_ref_heading = doc_xml.find('>References<', 400000)
    if pos_ref_heading == -1:
        raise RuntimeError("Could not locate References heading in body")
    
    pos_ref_p_end = doc_xml.find('</w:p>', pos_ref_heading) + 6
    
    pos_app = doc_xml.find('>Appendix<', pos_ref_p_end)
    if pos_app == -1:
        pos_app = doc_xml.find('>Appendix', pos_ref_p_end)
    pos_app_p_start = doc_xml.rfind('<w:p ', 0, pos_app)

    new_refs_xml = "".join(build_p_xml(ref, is_ref=True) for ref in REFERENCES)

    doc_xml = doc_xml[:pos_ref_p_end] + new_refs_xml + doc_xml[pos_app_p_start:]
    print("References successfully replaced with 24 peer-reviewed citations.")

    # 3. Update Image Extents for image6.png through image15.png (rId12 to rId21)
    for i in range(6, 16):
        rId = f"rId{i+6}"
        img_file = f"/tmp/docx_screenshots/image{i}.png"
        if not os.path.exists(img_file):
            raise FileNotFoundError(f"Missing screenshot: {img_file}")
        
        img = Image.open(img_file)
        cx = 5943600
        cy = int(cx * img.size[1] / img.size[0])

        pos_blip = doc_xml.find(f'r:embed="{rId}"')
        if pos_blip != -1:
            p_draw_start = doc_xml.rfind('<w:drawing>', 0, pos_blip)
            p_draw_end = doc_xml.find('</w:drawing>', pos_blip) + 12
            draw_xml = doc_xml[p_draw_start:p_draw_end]
            draw_xml = re.sub(r'<wp:extent\s+cx="\d+"\s+cy="\d+"', f'<wp:extent cx="{cx}" cy="{cy}"', draw_xml)
            draw_xml = re.sub(r'<a:ext\s+cx="\d+"\s+cy="\d+"', f'<a:ext cx="{cx}" cy="{cy}"', draw_xml)
            doc_xml = doc_xml[:p_draw_start] + draw_xml + doc_xml[p_draw_end:]
            print(f"Updated drawing extents for image{i}.png ({rId}): cx={cx}, cy={cy} (native: {img.size})")
        else:
            print(f"Warning: rId {rId} not found in doc_xml")

    # Validate XML parsing
    ET.fromstring(doc_xml)
    print("XML well-formedness validation passed for word/document.xml.")

    file_map['word/document.xml'] = doc_xml.encode('utf-8')

    # 4. Replace media files
    for i in range(6, 16):
        media_name = f"word/media/image{i}.png"
        img_src = f"/tmp/docx_screenshots/image{i}.png"
        with open(img_src, 'rb') as f:
            file_map[media_name] = f.read()
        print(f"Replaced {media_name} ({len(file_map[media_name])} bytes)")

    # 5. Ensure word/settings.xml has <w:updateFields w:val="true"/>
    if 'word/settings.xml' in file_map:
        settings_xml = file_map['word/settings.xml'].decode('utf-8')
        if '<w:updateFields' not in settings_xml:
            settings_xml = settings_xml.replace('</w:settings>', '<w:updateFields w:val="true"/></w:settings>')
            file_map['word/settings.xml'] = settings_xml.encode('utf-8')
            print("Enabled <w:updateFields w:val='true'/> in word/settings.xml")

    # 6. Write cleanly to output
    with zipfile.ZipFile(OUTPUT_DOCX, 'w', zipfile.ZIP_DEFLATED) as zout:
        for fname, data in file_map.items():
            zout.writestr(fname, data)

    print(f"\nSuccessfully created {OUTPUT_DOCX} ({os.path.getsize(OUTPUT_DOCX)} bytes)")

if __name__ == "__main__":
    main()
