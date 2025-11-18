"""
View Claim Hierarchy - Simple Visualization Tool

Run this script to see your claim hierarchy in different formats.
"""

import sys
from pathlib import Path
from research_agent.neo4j_database import Neo4jDatabase


def print_hierarchy_tree():
    """Print the claim hierarchy as an ASCII tree."""
    db = Neo4jDatabase()

    print("\n" + "=" * 80)
    print("CLAIM HIERARCHY TREE".center(80))
    print("=" * 80 + "\n")

    # Find root claims (no parents)
    query = """
    MATCH (c:Claim)
    WHERE NOT ()-[:PARENT_OF]->(c)
    RETURN c.id as id, c.text as text, c.specificity_score as specificity
    ORDER BY c.specificity_score ASC
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        roots = list(result)

    print(f"Found {len(roots)} root claims (most general):\n")

    # Print each root and its children
    for i, root in enumerate(roots, 1):
        print(f"{i}. ROOT: {root['text'][:100]}...")
        print(f"   Specificity: {root['specificity']:.3f}\n")

        # Get children
        print_children(db, root['id'], indent=1)
        print()

    db.close()


def print_children(db, parent_id, indent=0, max_depth=3):
    """Recursively print children of a claim."""
    if indent >= max_depth:
        return

    query = """
    MATCH (parent:Claim {id: $parent_id})-[r:PARENT_OF]->(child:Claim)
    RETURN child.id as id,
           child.text as text,
           child.specificity_score as specificity,
           r.specificity_delta as delta
    ORDER BY r.specificity_delta DESC
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query, parent_id=parent_id)
        children = list(result)

    for child in children:
        prefix = "   " * indent + "  -> "
        print(f"{prefix}CHILD: {child['text'][:80]}...")
        print(f"{'   ' * indent}     Specificity: {child['specificity']:.3f} (+{child['delta']:.3f})")

        # Recursively print grandchildren
        print_children(db, child['id'], indent + 1, max_depth)


def print_support_relationships():
    """Print claims that support each other."""
    db = Neo4jDatabase()

    print("\n" + "=" * 80)
    print("SUPPORT RELATIONSHIPS (Claims Supporting Other Claims)".center(80))
    print("=" * 80 + "\n")

    query = """
    MATCH (c1:Claim)-[r:SUPPORTS]->(c2:Claim)
    RETURN c1.text as supporter,
           c2.text as supported,
           r.confidence as confidence
    ORDER BY r.confidence DESC
    LIMIT 10
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        supports = list(result)

    if not supports:
        print("No support relationships found.")
        db.close()
        return

    print(f"Top {len(supports)} support relationships:\n")

    for i, rel in enumerate(supports, 1):
        print(f"{i}.")
        print(f"   SUPPORTS: {rel['supporter'][:100]}...")
        print(f"   SUPPORTED: {rel['supported'][:100]}...")
        print(f"   Confidence: {rel.get('confidence', 'N/A')}\n")

    db.close()


def print_statistics():
    """Print overall statistics."""
    db = Neo4jDatabase()

    print("\n" + "=" * 80)
    print("HIERARCHY STATISTICS".center(80))
    print("=" * 80 + "\n")

    stats = db.stats()

    print("Database Overview:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total relationships: {stats['total_relationships']}\n")

    print("Node Types:")
    for label, count in stats['node_labels'].items():
        print(f"  {label}: {count}")

    print("\nRelationship Types:")
    for rel_type, count in stats['relationship_types'].items():
        print(f"  {rel_type}: {count}")

    # Calculate hierarchy depth
    query = """
    MATCH path = (:Claim)-[:PARENT_OF*]->(:Claim)
    RETURN length(path) as depth
    ORDER BY depth DESC
    LIMIT 1
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        record = result.single()
        max_depth = record['depth'] if record else 0

    print(f"\nHierarchy Metrics:")
    print(f"  Maximum depth: {max_depth} levels")

    # Count root and leaf claims
    query_roots = """
    MATCH (c:Claim)
    WHERE NOT ()-[:PARENT_OF]->(c)
    RETURN count(c) as count
    """

    query_leaves = """
    MATCH (c:Claim)
    WHERE NOT (c)-[:PARENT_OF]->()
    RETURN count(c) as count
    """

    with db.driver.session(database=db.database) as session:
        roots = session.run(query_roots).single()['count']
        leaves = session.run(query_leaves).single()['count']

    print(f"  Root claims (most general): {roots}")
    print(f"  Leaf claims (most specific): {leaves}")

    db.close()


def generate_html_visualization():
    """Generate an HTML file with interactive visualization."""
    db = Neo4jDatabase()

    # Get all claims and relationships
    query = """
    MATCH (c:Claim)
    OPTIONAL MATCH (c)-[r:PARENT_OF]->(child:Claim)
    RETURN c.id as id,
           c.text as text,
           c.specificity_score as specificity,
           collect({child_id: child.id, child_text: child.text}) as children
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query)
        claims = list(result)

    # Generate HTML
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Claim Hierarchy Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .stats {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .claim {
            background: white;
            margin: 15px 0;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .claim.root {
            border-left-color: #2196F3;
            font-weight: bold;
        }
        .claim.child {
            margin-left: 40px;
            border-left-color: #FF9800;
        }
        .claim.grandchild {
            margin-left: 80px;
            border-left-color: #9C27B0;
        }
        .specificity {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .text {
            color: #333;
            line-height: 1.6;
        }
        .controls {
            background: white;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background: #45a049;
        }
    </style>
    <script>
        function expandAll() {
            document.querySelectorAll('.claim').forEach(el => el.style.display = 'block');
        }
        function collapseAll() {
            document.querySelectorAll('.child, .grandchild').forEach(el => el.style.display = 'none');
        }
        function showRoots() {
            collapseAll();
            document.querySelectorAll('.root').forEach(el => el.style.display = 'block');
        }
    </script>
</head>
<body>
    <h1>[TREE] Claim Hierarchy Visualization</h1>

    <div class="stats">
        <h2>Statistics</h2>
"""

    # Add statistics
    stats = db.stats()
    html += f"""
        <p><strong>Total Claims:</strong> {stats['node_labels'].get('Claim', 0)}</p>
        <p><strong>Hierarchical Relationships:</strong> {stats['relationship_types'].get('PARENT_OF', 0)}</p>
        <p><strong>Support Relationships:</strong> {stats['relationship_types'].get('SUPPORTS', 0)}</p>
        <p><strong>Overlap Relationships:</strong> {stats['relationship_types'].get('OVERLAPS', 0)}</p>
    </div>

    <div class="controls">
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
        <button onclick="showRoots()">Show Roots Only</button>
    </div>

    <div class="hierarchy">
        <h2>Hierarchy Tree</h2>
"""

    # Find roots
    roots = [c for c in claims if not any(
        other['id'] != c['id'] and
        any(child['child_id'] == c['id'] for child in other['children'] if child['child_id'])
        for other in claims
    )]

    def add_claim_html(claim, level=0):
        class_name = ['root', 'child', 'grandchild'][min(level, 2)]
        text = claim['text'][:200] + ('...' if len(claim['text']) > 200 else '')
        spec = claim.get('specificity', 0.0)

        if spec is None:
            spec = 0.0

        html_out = f"""
        <div class="claim {class_name}">
            <div class="text">{text}</div>
            <div class="specificity">Specificity: {spec:.3f}</div>
        </div>
"""

        # Add children
        for child_info in claim['children']:
            if child_info['child_id']:
                child_claim = next((c for c in claims if c['id'] == child_info['child_id']), None)
                if child_claim:
                    html_out += add_claim_html(child_claim, level + 1)

        return html_out

    # Add all root claims
    for root in roots:
        html += add_claim_html(root, 0)

    html += """
    </div>

    <div class="stats">
        <h2>How to Use</h2>
        <ul>
            <li><strong>Expand All:</strong> Show all claims in the hierarchy</li>
            <li><strong>Collapse All:</strong> Hide child claims, show roots only</li>
            <li><strong>Show Roots Only:</strong> Display only the most general claims</li>
        </ul>
        <p><strong>Color coding:</strong></p>
        <ul>
            <li><span style="color: #2196F3;">Blue</span> = Root claims (most general)</li>
            <li><span style="color: #FF9800;">Orange</span> = Child claims</li>
            <li><span style="color: #9C27B0;">Purple</span> = Grandchild claims (most specific)</li>
        </ul>
    </div>
</body>
</html>
"""

    # Save HTML file
    output_file = Path("claim_hierarchy_visualization.html")
    output_file.write_text(html, encoding='utf-8')

    print(f"\n[SUCCESS] HTML visualization saved to: {output_file.absolute()}")
    print(f"\nOpen this file in your browser to see the interactive hierarchy!")

    db.close()


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("CLAIM HIERARCHY VIEWER".center(80))
    print("=" * 80)

    # Show menu
    print("\nWhat would you like to view?\n")
    print("1. Hierarchy Tree (ASCII)")
    print("2. Support Relationships")
    print("3. Statistics")
    print("4. Generate HTML Visualization (opens in browser)")
    print("5. Show All")
    print("0. Exit")

    choice = input("\nEnter choice (0-5): ").strip()

    if choice == '1':
        print_hierarchy_tree()
    elif choice == '2':
        print_support_relationships()
    elif choice == '3':
        print_statistics()
    elif choice == '4':
        generate_html_visualization()
    elif choice == '5':
        print_statistics()
        print_hierarchy_tree()
        print_support_relationships()
        generate_html_visualization()
    elif choice == '0':
        print("\nGoodbye!")
        return
    else:
        print("\nInvalid choice. Showing all...")
        print_statistics()
        print_hierarchy_tree()
        print_support_relationships()
        generate_html_visualization()


if __name__ == "__main__":
    main()
