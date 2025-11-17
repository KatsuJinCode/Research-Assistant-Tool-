from web_ui.document_processor import LiveDocumentProcessor

processor = LiveDocumentProcessor(progress_callback=None)

examples = [
    "A person's belief cannot be explained by a defect or disease of the nervous system",
    "The study suggests that some users who regularly utilize the system might experience improved performance metrics",
    "Mental illness derives its main support from syphilis of the brain in which persons manifest various peculiarities or disorders of thinking"
]

for i, claim in enumerate(examples, 1):
    print(f"Example {i}:")
    print(f"Original: {claim}")
    summary = processor._simplify_claim_with_agent(claim)
    print(f"Simplified: {summary}")
    print()
