"""
Show Graph - Auto-Open Visualization

Generates HTML visualizations and automatically opens them in your browser.
NO copying code required!
"""

import webbrowser
from pathlib import Path
from research_agent.neo4j_database import Neo4jDatabase


def generate_full_graph_html():
    """Generate interactive HTML showing the full research graph."""

    db = Neo4jDatabase()

    # Get all optimal claims with their connections
    query = """
    MATCH (c:Claim)
    WHERE c.is_optimal = true
    OPTIONAL MATCH (c)-[:EXTRACTED_FROM]->(s:Sentence)
    OPTIONAL MATCH (c)-[r_ev:SUPPORTS|CONTRADICTS]-(e:Evidence)
    OPTIONAL MATCH (c)<-[:INVESTIGATES]-(res:ResearchResult)
    OPTIONAL MATCH (c)-[r:CITES|PARENT_OF]-(other:Claim)
    RETURN c.id as claim_id,
           c.text as claim_text,
           c.specificity_score as specificity,
           collect(DISTINCT {page: s.page, line: s.start_line, sentence: s.text}) as sources,
           collect(DISTINCT {title: e.title, rel_type: type(r_ev)}) as evidence,
           collect(DISTINCT {agent: res.agent_name, findings: res.findings}) as research,
           collect(DISTINCT {related: other.text, rel_type: type(r)}) as citations
    LIMIT 50
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        claims = [dict(record) for record in result]

    db.close()

    # Generate HTML
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Research Graph Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #2196F3;
            text-align: center;
        }
        .claim-card {
            background: white;
            border-left: 4px solid #2196F3;
            margin: 20px 0;
            padding: 20px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .claim-text {
            font-size: 16px;
            margin-bottom: 15px;
            color: #333;
        }
        .metadata {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }
        .section {
            background: #f9f9f9;
            padding: 10px;
            border-radius: 4px;
        }
        .section-title {
            font-weight: bold;
            color: #666;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .item {
            margin: 5px 0;
            padding: 5px;
            background: white;
            border-radius: 3px;
            font-size: 13px;
        }
        .source {
            border-left: 3px solid #4CAF50;
        }
        .evidence {
            border-left: 3px solid #FF9800;
        }
        .research {
            border-left: 3px solid #9C27B0;
        }
        .citation {
            border-left: 3px solid #00BCD4;
        }
        .stats {
            background: #2196F3;
            color: white;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>🔍 Research Graph Visualization</h1>
    <div class="stats">
        <h3>Graph Statistics</h3>
        <p>Showing """ + str(len(claims)) + """ claims with all their connections</p>
    </div>
"""

    for i, claim in enumerate(claims, 1):
        # Clean up sources
        sources = [s for s in claim['sources'] if s.get('page')]
        evidence = [e for e in claim['evidence'] if e.get('title')]
        research = [r for r in claim['research'] if r.get('agent')]
        citations = [c for c in claim['citations'] if c.get('related')]

        html += f"""
    <div class="claim-card">
        <div class="claim-text">
            <strong>Claim {i}:</strong> {claim['claim_text'][:300]}{'...' if len(claim['claim_text']) > 300 else ''}
        </div>
        <div class="metadata">
"""

        # Sources section
        if sources:
            html += """
            <div class="section">
                <div class="section-title">📄 Source Locations</div>
"""
            for source in sources[:5]:
                html += f"""
                <div class="item source">
                    Page {source['page']}, Line {source['line']}<br>
                    <small>{source['sentence'][:100]}...</small>
                </div>
"""
            html += """
            </div>
"""

        # Evidence section
        if evidence:
            html += """
            <div class="section">
                <div class="section-title">📚 Evidence</div>
"""
            for ev in evidence:
                html += f"""
                <div class="item evidence">
                    {ev['title']}
                </div>
"""
            html += """
            </div>
"""

        # Research section
        if research:
            html += """
            <div class="section">
                <div class="section-title">🤖 Agent Research</div>
"""
            for res in research:
                html += f"""
                <div class="item research">
                    <strong>{res['agent']}:</strong><br>
                    {res['findings'][:150]}...
                </div>
"""
            html += """
            </div>
"""

        # Citations section
        if citations:
            html += """
            <div class="section">
                <div class="section-title">🔗 Citations</div>
"""
            for cit in citations[:3]:
                html += f"""
                <div class="item citation">
                    {cit['rel_type']}: {cit['related'][:100]}...
                </div>
"""
            html += """
            </div>
"""

        html += """
        </div>
    </div>
"""

    html += """
</body>
</html>
"""

    # Write file
    output_file = Path("research_graph_view.html")
    output_file.write_text(html, encoding='utf-8')

    return output_file


def main():
    print("=" * 80)
    print("GENERATING GRAPH VISUALIZATION".center(80))
    print("=" * 80)

    print("\nGenerating HTML visualization...")
    output_file = generate_full_graph_html()

    print(f"\n[SUCCESS] Created: {output_file}")
    print("\nOpening in your browser...")

    # Auto-open in browser
    webbrowser.open(str(output_file.absolute()))

    print("\n[DONE] Visualization opened in your default browser!")
    print("=" * 80)


if __name__ == "__main__":
    main()
