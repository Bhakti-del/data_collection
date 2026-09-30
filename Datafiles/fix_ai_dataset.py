"""
fix_ai_dataset.py
-----------------
Corrects mistagged topic_tags and wrong bloom_levels in
Artificial_Intelligence_Dataset.csv based on manual review.

Issues fixed:
  1. INTRODUCTION_AND_AI_OVERVIEW — questions that belong to other topics
  2. PROPOSITIONAL_LOGIC — misplaced questions from other units
  3. STATE_SPACE_SEARCH — misplaced questions (learning by advice, graph plan)
  4. SEMANTIC_WEB — "knowledge vs learning" and "knowledge representation" misplaced
  5. CONSTRAINT_SATISFACTION — resolution for propositional logic misplaced
  6. KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS — frames confusion
  7. bloom_level fixes — "give an overview", "explain" wrongly tagged as Remember
"""

import csv
from pathlib import Path

INPUT  = Path("Data/Artificial_Intelligence_Dataset.csv")
OUTPUT = Path("Data/Artificial_Intelligence_Dataset.csv")

FIELDNAMES = [
    "subject_name", "raw_question_text", "topic_tag", "bloom_level",
    "original_marks", "part_a_years", "part_b_years",
]

# ── EXACT TEXT → (correct_topic_tag, correct_bloom_level) ────────────────────
# Use None to keep existing value unchanged.

FIXES = {

    # ── INTRODUCTION_AND_AI_OVERVIEW misplacements ────────────────────────────

    # Baye's rule belongs to UNCERTAINTY_AND_BAYESIAN_NETWORKS
    "Give Baye's rule and its uses.":
        ("UNCERTAINTY_AND_BAYESIAN_NETWORKS", "Remember"),

    "State Baye's rule. [3] (50 Marks)":
        ("UNCERTAINTY_AND_BAYESIAN_NETWORKS", "Remember"),

    # Perceptron belongs to ARTIFICIAL_NEURAL_NETWORKS
    "Give the schematics of a single layer perceptron.":
        ("ARTIFICIAL_NEURAL_NETWORKS", "Remember"),

    # Syntax tree belongs to NATURAL_LANGUAGE_PROCESSING
    "What is a syntax tree?":
        ("NATURAL_LANGUAGE_PROCESSING", "Remember"),

    # Predicate sentences belong to PREDICATE_LOGIC
    "Paris and Marseilles are both in France. ii) There is a country that borders both Iraq and Pakistan. iii) All countries that border Ecuador are in South America.":
        ("PREDICATE_LOGIC", "Apply"),

    # Certainty factors → CERTAINTY_AND_DEMPSTER_SHAFER
    "What are the uses of certainity factors?":
        ("CERTAINTY_AND_DEMPSTER_SHAFER", "Remember"),

    # Agent elements → INTRODUCTION (correct, fix bloom)
    "Name the elements of an agent.":
        ("INTRODUCTION_AND_AI_OVERVIEW", "Remember"),

    # "Give an overview" bloom should be Understand not Remember
    "Give an overview of different kinds of agent programs. Explain A* algorithm. What are the conditions for optimality?":
        ("INTRODUCTION_AND_AI_OVERVIEW", "Understand"),

    # Model based agents → INTRODUCTION, bloom Understand
    "Write a short note on model based reflex agents and utility based agents. Give an overview of genetic algorithms. Give the advantages of it.":
        ("INTRODUCTION_AND_AI_OVERVIEW", "Understand"),

    # "Explain the challenges" → Understand
    "Explain the challenges and applications of artificial intelligence.":
        ("INTRODUCTION_AND_AI_OVERVIEW", "Understand"),

    # Control strategy belongs to STATE_SPACE_SEARCH
    "What do you mean by a contr ol strategy? Give an overview of various control strategies for search. Explain bounded-look ahead searching with an example.":
        ("STATE_SPACE_SEARCH", "Understand"),

    # Prolog program → PREDICATE_LOGIC (logic programming)
    "Create a simple Prolog program to solve the classic \"parent\" relationship problem. Define the relationships and provide sample queries and their expected outcomes.":
        ("PREDICATE_LOGIC", "Apply"),

    # "Consider axioms" → PREDICATE_LOGIC (first-order logic)
    "Consider the following set of axioms Everyone who loves someone who loves them back is happy Mary loves everyone There is someone who loves Mary From the above statements conclude that: Mary is happy.":
        ("PREDICATE_LOGIC", "Apply"),

    # "Define over fitting" → MACHINE_LEARNING_PARADIGMS
    "Define over fitting.":
        ("MACHINE_LEARNING_PARADIGMS", "Remember"),

    # "Define training and testing data" → MACHINE_LEARNING_PARADIGMS
    "Define training and testing data.":
        ("MACHINE_LEARNING_PARADIGMS", "Remember"),

    # "Explain how the natural language is processed" → NLP
    "Explain how the natural language is processed, with a relevant example.":
        ("NATURAL_LANGUAGE_PROCESSING", "Understand"),

    # ── PROPOSITIONAL_LOGIC misplacements ─────────────────────────────────────

    # Job-shop scheduling → PLANNING (R18 Unit IV)
    "Explain the job-shop scheduling problem with various constraints. Describe the semantics of propositional logic with the truth table.":
        ("PLANNING", "Understand"),

    # Knowledge acquisition → EXPERT_SYSTEMS
    "Explain the process of knowledge acquisition and validation for expert systems.":
        ("EXPERT_SYSTEMS", "Understand"),

    # Frame-based inference → KNOWLEDGE_REPRESENTATION_FRAMES
    "Discuss how inference through inheritance can be achieved in a frame based knowledge representation. Give the rules of inference in propositional logic and explain natural deduction using an example.":
        ("KNOWLEDGE_REPRESENTATION_FRAMES", "Understand"),

    # Semantic net + propositional logic → KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS
    "Explain semantic network using an example. How do you make inferences using refutation in propositional logic? Explain with an example.":
        ("KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS", "Understand"),

    # Frame advantages → KNOWLEDGE_REPRESENTATION_FRAMES
    "What are the advantages and problems of a frame based knowledge representation? Give examples of knowledge hard to represent in a frame. Give a simple resolution algorithm for propositional logic.":
        ("KNOWLEDGE_REPRESENTATION_FRAMES", "Understand"),

    # Basic inference in semantic nets → KR_SEMANTIC_NETS
    "Explain the basic inference mechanism in semantic nets and frames. Prove the inconsistency of bbafeba ~)&(~&)(&)(  using semantic tableaux method.":
        ("KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS", "Understand"),

    # Forward chaining / default → PROPOSITIONAL_LOGIC (keep, fix bloom)
    "Explain reasoning with default information. Write simple forward chaining algorithm.":
        ("PROPOSITIONAL_LOGIC", "Understand"),

    # Procedural vs Declarative → KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS
    "Differentiate between Procedural and Declarative Knowledge. Describe about Forward Chaining System.":
        ("KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS", "Analyze"),

    # ── STATE_SPACE_SEARCH misplacements ──────────────────────────────────────

    # "Learning by taking advice" → MACHINE_LEARNING_PARADIGMS
    "Write short note on the following: Learning by taking advice Learning in problem solving – learning by parameter adjustment, learning by chunking.":
        ("MACHINE_LEARNING_PARADIGMS", "Understand"),

    # Graph Plan → PLANNING (R18 Unit IV)
    "Discuss regressive relevant state space search. What is Graph Plan? Explain in detail.":
        ("PLANNING", "Understand"),

    # "How can computer acquire knowledge" → EXPERT_SYSTEMS
    "How can computer acquire knowledge? What is its role in problem solving?":
        ("EXPERT_SYSTEMS", "Understand"),

    # ── SEMANTIC_WEB misplacements ────────────────────────────────────────────

    # "Distinguish between knowledge and learning" → MACHINE_LEARNING_PARADIGMS
    "Distinguish between knowledge and learning.":
        ("MACHINE_LEARNING_PARADIGMS", "Analyze"),

    # "What is Knowledge Representation?" → KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS
    "What is Knowledge Representation?":
        ("KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS", "Remember"),

    # ── CONSTRAINT_SATISFACTION misplacements ─────────────────────────────────

    # Resolution for propositional logic → PROPOSITIONAL_LOGIC
    "What is Resolution? Explain Resolution algorithm for Proposition logic. Explain backtracking searching technique.":
        ("PROPOSITIONAL_LOGIC", "Understand"),

    # ── KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS fixes ──────────────────────────

    # Frames is the primary topic → KNOWLEDGE_REPRESENTATION_FRAMES
    "Write a short note on: Semantic nets Frames Scripts Conceptual Dependency":
        ("KNOWLEDGE_REPRESENTATION_FRAMES", "Understand"),

    # "What is frames?" with expert systems → keep FRAMES tag
    "What is frames? [3] Write about Expert systems.":
        ("KNOWLEDGE_REPRESENTATION_FRAMES", "Remember"),

    # ── EXPERT_SYSTEMS fixes ──────────────────────────────────────────────────

    # Knowledge engineering → EXPERT_SYSTEMS (keep), fix bloom
    "Describe the steps involved in the knowledge engineering process with example.":
        ("EXPERT_SYSTEMS", "Understand"),

    # TMS in expert systems → TRUTH_MAINTENANCE_SYSTEMS
    "Write a short note on: Justification – Based Truth Maintenance Systems Logic – Based Truth Maintenance.":
        ("TRUTH_MAINTENANCE_SYSTEMS", "Understand"),

    # Knowledge acquisition → EXPERT_SYSTEMS
    "What is Knowledge Acquisition?":
        ("EXPERT_SYSTEMS", "Remember"),

    # ── BLOOM LEVEL FIXES (Give an overview = Understand, not Remember) ────────

    "Give an overview of multi-layer perceptron algorithm in detail.":
        ("ARTIFICIAL_NEURAL_NETWORKS", "Understand"),

    "Give an overview of various knowledge representation approaches. Represent the following knowledge using a semantic network: Tom is a cat Tom caught a bird Tom is owned by John Tom is ginger in colour Cats like cream Cat is on the mat A cat is a mammal A bird is an animal All mammals are animals Mammals have fur":
        ("KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS", "Understand"),

    "Give an overview of support vector machines. What is a recurrent network? Explain.":
        ("SUPPORT_VECTOR_MACHINES", "Understand"),

    "Give an overview of knowledge base and inference engine in expert systems. Distinguish among the following Truth Maintenance Systems: JTMS, ATMS and LTMS.":
        ("EXPERT_SYSTEMS", "Understand"),

    "Give an overview of various types of expert system tools and criteria for selecting the right kind of tool. Give an overview of reasoning with uncertainty using Dempster-Shafer theory.":
        ("EXPERT_SYSTEMS", "Understand"),

    "Give an overview of syntax representation and parsing methods in natural language processing. What is a semantic web? What are the challenges automated reasoning systems will have to deal with respect to semantic web?":
        ("NATURAL_LANGUAGE_PROCESSING", "Understand"),

    "Give an overview of rule-based system using certainty factor.":
        ("CERTAINTY_AND_DEMPSTER_SHAFER", "Understand"),

    # "Explain A* algorithm" should be Understand not Remember
    "Explain A* algorithm with a suitable example. State the limitations in the algorithm.":
        ("HEURISTIC_SEARCH", "Understand"),

    "What is A* search? Explain various stages of A* search with an example.":
        ("HEURISTIC_SEARCH", "Understand"),

    # Explain how to define → Understand not Remember
    "Explain how to define a problem as a state space search, with a suitable example.":
        ("STATE_SPACE_SEARCH", "Understand"),

    "How to define a problem as state space search? Discuss it with the help of an example.":
        ("STATE_SPACE_SEARCH", "Understand"),

    # Explain propositional logic → Understand
    "What is propositional logic? Explain its syntax and logical connectivities with examples.":
        ("PROPOSITIONAL_LOGIC", "Understand"),

    # Explain ML → Understand
    "What is machine learning? How the data is classified using decision trees?":
        ("MACHINE_LEARNING_PARADIGMS", "Understand"),

    "What is machine learning? What are the phases in it? How data is analyzed and classified through Support vector machine?":
        ("MACHINE_LEARNING_PARADIGMS", "Understand"),

    "What is goal of Inductive learning? Explain. Mention design issues of recurrent networks.":
        ("MACHINE_LEARNING_PARADIGMS", "Understand"),

    # Expert systems explain → Understand
    "What is an expert system? Briefly describe five major components of an expert system. Using a suitable query, explain the working of an inference engine in a rule-based expert system.":
        ("EXPERT_SYSTEMS", "Understand"),

    "Describe in detail various phases in building Expert systems. List and explain various capabilities of the Expert System.":
        ("EXPERT_SYSTEMS", "Understand"),

    "Explain the general approach for developing an expert system. Give an overview of rule-based system using certainty factor.":
        ("EXPERT_SYSTEMS", "Understand"),

    "Explain the use of expert system shells. What are the different ways (support for explanation) to make the expert system effective?":
        ("EXPERT_SYSTEMS", "Understand"),

    "What are the basic components of an expert system? Explain. What is the purpose of a Truth Maintenance System in expert systems?":
        ("EXPERT_SYSTEMS", "Understand"),

    # NLP explain → Understand
    "List and explain the applications of Natural Language Processing.":
        ("NATURAL_LANGUAGE_PROCESSING", "Understand"),

    "What are the tasks involved in natural language processing? Explain. What is the purpose of a case grammar? Give an overview of case grammars with examples.":
        ("NATURAL_LANGUAGE_PROCESSING", "Understand"),

    "What is a grammar? Give an overview of various methods for specifying grammar in natural language processing.":
        ("NATURAL_LANGUAGE_PROCESSING", "Understand"),

    "List and explain the various approaches of knowledge representation.":
        ("KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS", "Understand"),

    # State space → Understand
    "What is state space tree? Explain with an example.":
        ("STATE_SPACE_SEARCH", "Understand"),

    "What are the characteristics of a problem? Explain about iterative deepening A* algorithm.":
        ("STATE_SPACE_SEARCH", "Understand"),

    "What are the various components of AI program? Explain. What are various problem characteristics? Explain.":
        ("INTRODUCTION_AND_AI_OVERVIEW", "Understand"),

    "What is artificial intelligence technique? Explain why problem formulation must follow goal formulation.":
        ("INTRODUCTION_AND_AI_OVERVIEW", "Understand"),

    # Bayesian → Understand
    "What is meant by universal and existential quantification? Give examples for each. Explain the resolution algorithm used for reasoning under first order logic with an example.":
        ("PREDICATE_LOGIC", "Understand"),

    "What are various problem characteristics? Explain.":
        ("STATE_SPACE_SEARCH", "Understand"),

    # Planning → Understand
    "Comment on the complexity of classical planning. Explain job-shop scheduling problem with and without resource constraints.":
        ("PLANNING", "Understand"),
}


def apply_fixes(rows):
    fixed = 0
    for r in rows:
        q = r["raw_question_text"].strip()
        # Try exact match first
        if q in FIXES:
            new_tag, new_bloom = FIXES[q]
            changed = False
            if new_tag and r["topic_tag"] != new_tag:
                r["topic_tag"] = new_tag
                changed = True
            if new_bloom and r["bloom_level"] != new_bloom:
                r["bloom_level"] = new_bloom
                changed = True
            if changed:
                fixed += 1
        else:
            # Try substring match for truncated texts
            for key, (new_tag, new_bloom) in FIXES.items():
                if len(key) > 40 and key[:60] in q:
                    changed = False
                    if new_tag and r["topic_tag"] != new_tag:
                        r["topic_tag"] = new_tag
                        changed = True
                    if new_bloom and r["bloom_level"] != new_bloom:
                        r["bloom_level"] = new_bloom
                        changed = True
                    if changed:
                        fixed += 1
                    break
    return fixed


def main():
    with open(INPUT, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} rows")

    fixed = apply_fixes(rows)
    print(f"Fixed  {fixed} rows")

    # Sort by topic_tag
    rows.sort(key=lambda x: (x["topic_tag"], x["raw_question_text"]))

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    # Print final tag counts
    from collections import defaultdict
    counts = defaultdict(int)
    for r in rows:
        counts[r["topic_tag"]] += 1
    print(f"\nFinal topic distribution:")
    for tag, cnt in sorted(counts.items()):
        print(f"  {tag:45s}: {cnt}")

    print(f"\nOutput: {OUTPUT}")


if __name__ == "__main__":
    main()
