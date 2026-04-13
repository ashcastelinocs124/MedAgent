# Personalized Agentic Healthcare Search: A Hybrid Retrieval System with Knowledge Graph-Augmented Reasoning for Consumer Health Queries

## Abstract

Consumer health information seeking online continues to accelerate, with recent cross-sectional studies showing that over 63% of adults actively search for health information online and that this behavior significantly increases healthcare utilization [1]. A 2025 systematic review of 2,761 publications confirms the convergence of AI, big data, and social media is fundamentally reshaping how consumers access health information [2]. Yet current search paradigms remain inadequate for medical queries: studies evaluating commercial search engine results find that only 25% of health-related pages meet high-quality standards [3], while an interview study using think-aloud protocols reveals that the convenience of AI-generated health summaries introduces new risks of bias and misinformation [4]. Health misinformation itself remains pervasive, with a recent meta-analysis reporting a 47% prevalence rate among older adults alone [5]. These challenges disproportionately affect vulnerable populations—approximately 88% of U.S. adults have less-than-proficient health literacy, costing the healthcare system an estimated $238 billion annually [6]—and a 2025 meta-analysis confirms that lower digital health literacy is significantly associated with poorer outcomes among patients with chronic diseases [7].

This paper presents an agentic healthcare search system that addresses these limitations through three integrated innovations. First, we propose a **hybrid retrieval architecture** that fuses dense semantic search using domain-specific biomedical embeddings (e.g., MedCPT [8]), sparse lexical retrieval with medical terminology expansion via UMLS and MeSH, and structured traversal over biomedical knowledge graphs such as PrimeKG [9] and SPOKE [10]. Retrieval results are combined through reciprocal rank fusion, which has demonstrated 10–60% improvement over single-system baselines in biomedical information retrieval tasks [11]. Second, we employ a **multi-agent pipeline** in which specialized LLM agents coordinate query understanding, retrieval planning, synthesis, and verification. A 2025 systematic review of AI agents in clinical medicine found that all agent-based systems outperformed baseline LLMs, with a median accuracy improvement of 53 percentage points and optimal performance observed in multi-agent configurations of up to five collaborative agents [12]. Emerging frameworks for agentic LLMs in healthcare further demonstrate that combining reasoning, planning, and tool use enables autonomous problem-solving beyond the reach of standalone models [13]. Third, we introduce a **personalization layer** that adapts retrieved information to each user's health literacy level, known conditions, and demographic context. A 2025 systematic review of 61 dynamically tailored eHealth interventions found that nearly three-quarters integrated contextual, emotional, or physiological variables for personalization [14], and a parallel review of 31 RCTs confirmed that tailoring interventions to health literacy levels improves both comprehension and health outcomes [15].

The system constructs a personal health knowledge graph from user-provided medical data and intake forms, enabling context-aware query reformulation before retrieval. A tiered source strategy prioritizes peer-reviewed literature from PubMed and vetted medical databases, with community health forums serving as supplementary evidence—mirroring best practices for consumer health question answering [16]. All synthesized responses include source citations and explicit uncertainty flagging, addressing the critical challenge of LLM hallucination in medical contexts, where adversarial hallucination rates of 50–82% have been observed across leading models [17]. We evaluate the system using established biomedical QA benchmarks including PubMedQA, MedQA, and the MIRAGE medical RAG benchmark [18], measuring retrieval quality (nDCG, MAP, Recall@k), answer factual accuracy, citation correctness, and personalization effectiveness via Flesch-Kincaid readability scores. A 2025 systematic review of 70 RAG studies in healthcare confirms that retrieval-augmented generation improves LLM accuracy from 73.4% to 80.0% with external knowledge integration [19], while a scoping review of 67 studies categorizes the landscape into text-based RAG (54%), knowledge graph-enhanced RAG (25%), and agentic RAG (9%) [20]—positioning our work at the intersection of the latter two emerging paradigms.

**Keywords:** agentic AI, hybrid search, healthcare information retrieval, knowledge graphs, personalization, health literacy, retrieval-augmented generation

---

## References

[1] Y. Li, Y. Lu, X. Wang, and Y. Zhang, "Associations among online health information seeking behavior, online health information perception, and health service utilization: Cross-sectional study," *J. Med. Internet Res.*, vol. 27, e66683, 2025. doi: 10.2196/66683

[2] Y. Fu, P. Han, J. Wang, and F. Shahzad, "Digital pathways to healthcare: A systematic review for unveiling the trends and insights in online health information-seeking behavior," *Front. Public Health*, vol. 13, 1497025, 2025. doi: 10.3389/fpubh.2025.1497025

[3] N. Arif, P. Ghezzi, et al., "Using the Google search engine for health information: Is there a problem? Case study: Supplements for cancer," *PMC*, 2021. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC8059196/

[4] "Evolving health information-seeking behavior in the context of Google AI Overviews, ChatGPT, and Alexa: Interview study using the think-aloud protocol," *J. Med. Internet Res.*, vol. 27, e79961, 2025. doi: 10.2196/79961

[5] B. Hu, X. Liu, C. Lu, and X. Ju, "Prevalence and intervention strategies of health misinformation among older adults: A meta-analysis," *J. Health Psychol.*, vol. 30, no. 2, 2025. doi: 10.1177/13591053241298362

[6] Market.us, "Health literacy statistics and facts (2025)," 2025. Available: https://media.market.us/health-literacy-statistics/ [Note: 88% of U.S. adults have less-than-proficient health literacy per NAAL data; $238B annual cost estimate from recent analysis]

[7] J. Yu, L. Zhang, X. Wang, et al., "Digital health literacy in patients with common chronic diseases: Systematic review and meta-analysis," *J. Med. Internet Res.*, vol. 27, e56231, 2025. doi: 10.2196/56231

[8] Q. Jin et al., "MedCPT: Contrastive pre-trained transformers with large-scale PubMed search logs for zero-shot biomedical information retrieval," *Bioinformatics*, vol. 39, no. 11, btad651, 2023. doi: 10.1093/bioinformatics/btad651

[9] P. Chandak, K. Huang, and M. Zitnik, "Building a knowledge graph to enable precision medicine," *Scientific Data*, vol. 10, 2023. doi: 10.1038/s41597-023-01960-3

[10] J. S. Baranzini et al., "The scalable precision medicine open knowledge engine (SPOKE): A massive knowledge graph of biomedical information," *Bioinformatics*, vol. 39, no. 2, 2023. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC9940622/

[11] "Subset selection based fusion for biomedical information retrieval tasks," *BMC Bioinformatics*, 2025. doi: 10.1186/s12859-025-06313-y

[12] A. Gorenshtein, M. Omar, B. S. Glicksberg, G. N. Nadkarni, and E. Klang, "AI agents in clinical medicine: A systematic review," *medRxiv*, 2025. doi: 10.1101/2025.08.22.25334232

[13] H. Yuan, "Agentic large language models for healthcare: Current progress and future opportunities," *Med. Adv.*, 2025. doi: 10.1002/med4.70000

[14] E. A. G. Hietbrink, C. Lansink, G. D. Laverman, et al., "Systematic review of dynamically tailored eHealth interventions targeting physical activity and healthy diet in chronic disease," *npj Digit. Med.*, vol. 8, 696, 2025. doi: 10.1038/s41746-025-02054-7

[15] J. W. Hovingh, C. Elderson-van Duin, D. A. Kuipers, et al., "Tailoring for health literacy in the design and development of eHealth interventions: Systematic review," *JMIR Hum. Factors*, vol. 12, e76172, 2025. doi: 10.2196/76172

[16] A. Welivita et al., "A survey of consumer health question answering systems," *AI Magazine*, 2023. doi: 10.1002/aaai.12140

[17] "Multi-model assurance analysis showing large language models are highly vulnerable to adversarial hallucination attacks during clinical decision support," *PMC*, 2024. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC12318031/

[18] T. Xiong et al., "MIRAGE: Medical information retrieval-augmented generation evaluation," 2025. Available: https://teddy-xionggz.github.io/benchmark-medical-rag/

[19] L. M. Amugongo, P. Mascheroni, S. Brooks, S. Doering, and J. Seidel, "Retrieval augmented generation for large language models in healthcare: A systematic review," *PLOS Digit. Health*, vol. 4, no. 6, e0000877, 2025. doi: 10.1371/journal.pdig.0000877

[20] "Improving large language model applications in the medical and nursing domains with retrieval-augmented generation: Scoping review," *J. Med. Internet Res.*, vol. 27, e80557, 2025. doi: 10.2196/80557
