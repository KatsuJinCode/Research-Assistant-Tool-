# Leiden Algorithm Quick Reference

## One-Liner Install

```bash
pip install python-igraph leidenalg
```

---

## Basic Usage (Copy-Paste Ready)

### Minimal Example

```python
import igraph as ig
import leidenalg as la

# Create or load graph
G = ig.Graph.Famous('Zachary')

# Detect communities (one line!)
partition = la.find_partition(G, la.CPMVertexPartition, resolution_parameter=0.1)

# Results
print(f"Communities: {len(partition)}")
print(f"Modularity: {partition.modularity():.3f}")
print(f"Membership: {partition.membership}")
```

---

## Quality Function Cheat Sheet

| Use Case | Quality Function | Code |
|----------|------------------|------|
| **Default choice** | CPM | `la.CPMVertexPartition` |
| **Negative weights** | CPM (only one that supports) | `la.CPMVertexPartition` |
| **Simple/classic** | Modularity | `la.ModularityVertexPartition` |
| **Alternative** | RBConfiguration | `la.RBConfigurationVertexPartition` |

---

## Resolution Parameter Guide

```python
# RULE OF THUMB: Start with network density

density = 2 * G.ecount() / (G.vcount() * (G.vcount() - 1))
resolution = density  # Starting point

# Then scan nearby values:
resolutions = [density/10, density/2, density, density*2, density*10]
```

### Resolution Effects

```
γ = 0.01  →  Few, large communities (coarse)
γ = 0.1   →  Moderate communities
γ = 1.0   →  Many, small communities (fine)
```

---

## Common Patterns

### Pattern 1: Weighted Graph

```python
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    weights='weight',  # Use 'weight' edge attribute
    resolution_parameter=0.1
)
```

### Pattern 2: Scan Resolutions

```python
for gamma in [0.01, 0.05, 0.1, 0.5, 1.0]:
    partition = la.find_partition(G, la.CPMVertexPartition,
                                  resolution_parameter=gamma)
    print(f"γ={gamma}: {len(partition)} communities")
```

### Pattern 3: More Iterations (Better Quality)

```python
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    resolution_parameter=0.1,
    n_iterations=10  # Default is 2
)
```

### Pattern 4: NetworkX to igraph

```python
import networkx as nx
import igraph as ig

# NetworkX graph
G_nx = nx.karate_club_graph()

# Convert to igraph
edges = list(G_nx.edges())
G_ig = ig.Graph(edges=edges)

# Now use Leiden
partition = la.find_partition(G_ig, la.CPMVertexPartition,
                              resolution_parameter=0.1)

# Convert back to NetworkX
for node, community in zip(G_nx.nodes(), partition.membership):
    G_nx.nodes[node]['community'] = community
```

---

## Evaluation Metrics

```python
# Internal metrics (no ground truth needed)
modularity = partition.modularity()
quality = partition.quality()

# External metrics (with ground truth)
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score

nmi = normalized_mutual_info_score(ground_truth, partition.membership)
ari = adjusted_rand_score(ground_truth, partition.membership)
```

### Quality Thresholds

```
Modularity (Q):
  Q > 0.3   = Strong community structure
  Q = 0.2-0.3 = Moderate
  Q < 0.2   = Weak

NMI:
  1.0 = Perfect agreement
  > 0.8 = Very good
  > 0.5 = Moderate
  < 0.5 = Poor
```

---

## Preprocessing Checklist

```python
# 1. Remove self-loops
G.simplify(loops=True)

# 2. Combine multiple edges
G.simplify(multiple=True, combine_edges='sum')

# 3. Check connectivity
components = G.components()
if len(components) > 1:
    G = components.giant()  # Use largest component

# 4. Normalize weights (if needed)
import numpy as np
weights = np.array(G.es['weight'])
normalized = (weights - weights.min()) / (weights.max() - weights.min())
G.es['weight'] = normalized.tolist()
```

---

## Troubleshooting

### Problem: Too many communities (all singletons)

**Solution**: Lower resolution parameter

```python
resolution_parameter=0.01  # Instead of 0.5
```

### Problem: One giant community

**Solution**: Raise resolution parameter

```python
resolution_parameter=0.5  # Instead of 0.01
```

### Problem: Negative weights error

**Solution**: Use CPM (only quality function that supports negative weights)

```python
partition = la.find_partition(G, la.CPMVertexPartition, ...)
# NOT Modularity or RBConfiguration
```

### Problem: Results vary across runs

**Solution**:
1. Use more iterations
2. Set random seed for reproducibility

```python
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    resolution_parameter=0.1,
    n_iterations=10,  # More iterations
    seed=42  # Reproducibility
)
```

### Problem: Disconnected communities

**Solution**: Verify after detection

```python
def verify_connected(G, membership):
    from collections import defaultdict
    communities = defaultdict(list)
    for node, comm in enumerate(membership):
        communities[comm].append(node)

    for comm_id, nodes in communities.items():
        subgraph = G.subgraph(nodes)
        if len(subgraph.components()) > 1:
            print(f"WARNING: Community {comm_id} is disconnected!")
            return False
    return True

verify_connected(G, partition.membership)
```

---

## Complete Working Example

```python
import igraph as ig
import leidenalg as la
import numpy as np

# 1. Create or load graph
G = ig.Graph.Erdos_Renyi(n=100, p=0.05)

# 2. Add random weights
np.random.seed(42)
G.es['weight'] = np.random.uniform(0.1, 1.0, G.ecount())

# 3. Preprocess
G.simplify(loops=True, multiple=True, combine_edges='sum')

# 4. Detect communities
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    weights='weight',
    resolution_parameter=0.1,
    n_iterations=5
)

# 5. Evaluate
print(f"Found {len(partition)} communities")
print(f"Modularity: {partition.modularity():.3f}")
print(f"Quality: {partition.quality():.2f}")

# 6. Analyze community sizes
sizes = np.bincount(partition.membership)
print(f"Community sizes: {sizes}")
print(f"Mean size: {np.mean(sizes):.1f}")
print(f"Largest: {np.max(sizes)}")

# 7. Add to graph and save
G.vs['community'] = partition.membership
G.write_graphml('network_with_communities.graphml')

print("\nDone!")
```

---

## Performance Expectations

| Graph Size | Expected Time | Memory |
|------------|---------------|--------|
| < 1K nodes | < 1 second | < 100 MB |
| 1K-10K nodes | 1-10 seconds | 100 MB - 1 GB |
| 10K-100K nodes | 10-60 seconds | 1-5 GB |
| 100K-1M nodes | 1-10 minutes | 5-20 GB |

---

## When to Use Leiden

✅ **Use Leiden when:**
- Need well-connected communities
- Want control over community size (resolution parameter)
- Have weighted or directed graphs
- Need better quality than Louvain
- Working with moderate to large networks

❌ **Consider alternatives when:**
- Extremely large networks (>10M edges) → Try Leiden first, use Label Propagation if too slow
- Real-time requirements (<100ms) → Pre-compute communities
- Network represents flows → Consider Infomap

---

## Key Differences from Louvain

| Aspect | Louvain | Leiden |
|--------|---------|--------|
| **Connectivity** | May produce disconnected communities | Guarantees connected |
| **Quality** | Good | Better |
| **Speed** | Fast | Faster (2-20x) |
| **Guarantees** | None | Multiple theoretical guarantees |
| **Recommendation** | ❌ Deprecated | ✅ Use this |

---

## Formula Reference

### Modularity

```
Q = (1/2m) Σ [A_ij - (k_i * k_j)/(2m)] δ(c_i, c_j)
```

### CPM (Constant Potts Model)

```
H = Σ [A_ij - γ] δ(c_i, c_j)
```

Where:
- `A_ij` = adjacency matrix (or weight)
- `k_i` = degree of node i
- `m` = total edges
- `γ` = resolution parameter
- `δ(c_i, c_j)` = 1 if nodes in same community, 0 otherwise

---

## API Quick Reference

```python
# Main function
partition = la.find_partition(
    graph,                        # igraph.Graph
    partition_type,               # la.CPMVertexPartition, etc.
    initial_membership=None,      # Optional starting partition
    weights=None,                 # None, 'weight', or list
    n_iterations=2,               # Number of iterations
    max_comm_size=0,              # Max community size (0=no limit)
    seed=None,                    # Random seed
    resolution_parameter=1.0      # For CPM, RBConfiguration
)

# Partition object attributes
partition.membership              # List of community assignments
partition.modularity()           # Calculate modularity
partition.quality()              # Quality function value
len(partition)                   # Number of communities

# Quality function classes
la.ModularityVertexPartition     # Standard modularity
la.CPMVertexPartition           # Constant Potts Model (best default)
la.RBConfigurationVertexPartition # Reichardt-Bornholdt
la.SignificanceVertexPartition   # Significance
la.SurpriseVertexPartition       # Surprise
```

---

## Common Imports

```python
# Always needed
import igraph as ig
import leidenalg as la

# Often useful
import numpy as np
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

# For NetworkX conversion
import networkx as nx
```

---

## Resources

- **Official docs**: https://leidenalg.readthedocs.io/
- **Original paper**: Traag et al. (2019), Scientific Reports
- **GitHub**: https://github.com/vtraag/leidenalg
- **python-igraph**: https://igraph.org/python/

---

## Getting Help

```python
# View documentation
help(la.find_partition)
help(la.CPMVertexPartition)

# Check installed versions
import igraph, leidenalg
print(f"igraph: {igraph.__version__}")
print(f"leidenalg: {leidenalg.__version__}")
```

---

**For comprehensive technical details**: See `LEIDEN_ALGORITHM_TECHNICAL_GUIDE.md`

**For integration with your codebase**: See `LEIDEN_INTEGRATION_GUIDE.md`
