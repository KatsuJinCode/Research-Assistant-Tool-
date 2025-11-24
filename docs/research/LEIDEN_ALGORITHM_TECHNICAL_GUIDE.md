# Leiden Algorithm: Complete Technical Guide

## Table of Contents
1. [Overview](#overview)
2. [Mathematical Foundation](#mathematical-foundation)
3. [How Leiden Improves Upon Louvain](#how-leiden-improves-upon-louvain)
4. [Quality Functions](#quality-functions)
5. [Parameter Tuning](#parameter-tuning)
6. [Implementation Guide](#implementation-guide)
7. [When to Use Leiden vs Other Algorithms](#when-to-use-leiden-vs-other-algorithms)
8. [Performance Characteristics](#performance-characteristics)
9. [Best Practices for Graph Preparation](#best-practices-for-graph-preparation)
10. [Quality Metrics and Evaluation](#quality-metrics-and-evaluation)
11. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
12. [Complete Code Examples](#complete-code-examples)

---

## Overview

The **Leiden algorithm** is a community detection algorithm that guarantees well-connected communities and overcomes critical defects in the widely-used Louvain algorithm.

### Original Paper
- **Title**: "From Louvain to Leiden: guaranteeing well-connected communities"
- **Authors**: Vincent A. Traag, Ludo Waltman, and Nees Jan van Eck
- **Published**: Scientific Reports, Nature (March 26, 2019)
- **DOI**: 10.1038/s41598-019-41695-z
- **ArXiv**: 1810.08473

### Key Contributions
1. Identifies and solves the disconnected communities problem in Louvain
2. Guarantees that all communities are connected
3. Runs faster than Louvain while finding better quality partitions
4. Provides theoretical guarantees about community structure
5. Converges to partitions where all communities are uniformly γ-dense

---

## Mathematical Foundation

### Three-Phase Algorithm

The Leiden algorithm consists of three phases per iteration:

#### Phase 1: Local Moving of Nodes
Nodes are moved to communities that maximize the quality function. Similar to Louvain, but uses a fast local move approach.

#### Phase 2: Refinement (Key Innovation)
**This is the critical difference from Louvain.** The refinement phase:
- Visits all nodes in random order
- Considers moving nodes to new communities
- Guarantees all communities remain well-connected
- Prevents formation of disconnected or poorly connected communities

#### Phase 3: Aggregation
- Creates a new aggregate network where each community becomes a single node
- Edge weights represent connections between communities
- Algorithm continues on the aggregate network

### Quality Function

The general quality function optimized by Leiden is:

```
H = Σ[e_c - γ * n_c * (n_c - 1)/2]
```

Where:
- `e_c` = number of edges within community c
- `n_c` = number of nodes in community c
- `γ` = resolution parameter

### Theoretical Guarantees

After each iteration, Leiden guarantees:

1. **γ-separated communities**: Communities are separated by the resolution parameter
2. **γ-connected communities**: All communities are well-connected
3. **Subpartition γ-density**: After stable iteration, all communities are subpartition γ-dense

#### Subpartition γ-density Definition
A community is **subpartition γ-dense** if it can be partitioned into two parts such that:
1. The two parts are well connected to each other
2. Neither part can be separated from its community
3. Each part is also subpartition γ-dense itself (recursive property)

---

## How Leiden Improves Upon Louvain

### Critical Defects in Louvain Algorithm

The Louvain algorithm has a **major defect**: it may yield arbitrarily badly connected communities.

#### Empirical Evidence
- Up to **25% of communities** can be badly connected
- Up to **16% of communities** can be completely disconnected
- Problem worsens with iterative application
- Especially problematic in large, complex empirical networks

### Leiden's Solutions

| Aspect | Louvain | Leiden |
|--------|---------|--------|
| **Connectivity** | Can produce disconnected communities | Guarantees connected communities |
| **Partition Quality** | Converges quickly, then stagnates | Keeps improving in each iteration |
| **Speed** | Fast | Faster (2-20x in first iteration) |
| **Theoretical Guarantees** | None | Multiple guarantees about structure |
| **Convergence** | Stops prematurely | Converges to uniformly γ-dense partition |
| **Complex Networks** | Quality degrades | Better performance on empirical networks |

### Performance Comparison

```
Runtime Complexity:
- Louvain: Can become quadratic O(n²) on challenging graphs
- Leiden: Remains near-linear O(L|E|) where L = iterations

Speed on Large Networks:
- Leiden is 2-20x faster than Louvain in first iteration
- Speed difference increases with network size
- Leiden spends time: 46% local-moving, 19% refinement, 20% aggregation
```

---

## Quality Functions

The `leidenalg` library implements multiple quality functions. Each has specific use cases and mathematical properties.

### 1. ModularityVertexPartition

**Classic Newman-Girvan Modularity**

```python
import leidenalg as la
partition = la.find_partition(G, la.ModularityVertexPartition)
```

**Formula**:
```
Q = (1/2m) * Σ[A_ij - (k_i * k_j)/(2m)] * δ(c_i, c_j)
```

Where:
- `m` = total number of edges
- `A_ij` = adjacency matrix
- `k_i, k_j` = degrees of nodes i and j
- `δ(c_i, c_j)` = 1 if nodes in same community, 0 otherwise

**Properties**:
- Optimal for positive-weighted networks
- Normalizes by 2m (directed graphs: by m)
- Subject to resolution limit
- No tunable resolution parameter

**Use When**:
- You want standard modularity
- Working with positive edge weights only
- Don't need fine-grained resolution control

---

### 2. RBConfigurationVertexPartition

**Reichardt-Bornholdt Model with Configuration Null Model**

```python
partition = la.find_partition(
    G,
    la.RBConfigurationVertexPartition,
    resolution_parameter=1.0
)
```

**Formula**:
```
H = Σ[A_ij - γ * (k_i * k_j)/(2m)] * δ(c_i, c_j)
```

**Properties**:
- Linear resolution parameter γ
- Well-defined only for **positive edge weights**
- Addresses resolution limit via γ parameter
- Most commonly used in practice

**Resolution Parameter Effects**:
- γ > 1: Favors more, smaller communities
- γ = 1: Equivalent to standard modularity
- γ < 1: Favors fewer, larger communities

**Use When**:
- Need resolution control
- All edge weights are positive
- Want modularity-like behavior with tuning

---

### 3. CPMVertexPartition (Constant Potts Model)

**Resolution-Limit-Free Approach**

```python
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    resolution_parameter=0.05
)
```

**Formula**:
```
H = Σ[A_ij - γ] * δ(c_i, c_j)
```

**Properties**:
- Supports **both positive and negative** edge weights
- Resolution-limit-free
- γ acts as density threshold
- Communities have density ≥ γ
- Inter-community density ≤ γ

**Resolution Parameter Interpretation**:
- γ = desired community density
- At optimal partition: internal density ≥ γ, external density ≤ γ
- More intuitive than RB model

**Relationship to Modularity**:
```python
# Modularity is essentially CPM with:
# - node_size = degree
# - resolution_parameter = 1/(2m)
```

**Use When**:
- Have negative edge weights
- Want intuitive density-based communities
- Need to avoid resolution limit
- Want communities of specific density

---

### 4. RBERVertexPartition

**Reichardt-Bornholdt with Erdős-Rényi Null Model**

```python
partition = la.find_partition(
    G,
    la.RBERVertexPartition,
    resolution_parameter=1.0,
    node_sizes=custom_sizes  # Optional
)
```

**Properties**:
- Uses Erdős-Rényi random graph as null model
- Supports custom node sizes
- Linear resolution parameter

**Use When**:
- Want ER null model instead of configuration model
- Need to specify custom node importance (sizes)

---

### 5. SignificanceVertexPartition

**Based on Kullback-Leibler Divergence**

```python
partition = la.find_partition(G, la.SignificanceVertexPartition)
```

**Properties**:
- Uses KL-divergence as quality measure
- **Unweighted graphs only**
- Expects ~0.5n ln(n) in random graphs
- No resolution parameter

**Use When**:
- Have unweighted graphs
- Want statistical significance-based detection
- Don't need resolution tuning

---

### 6. SurpriseVertexPartition

**Asymptotic Surprise Using Binary KL-Divergence**

```python
partition = la.find_partition(G, la.SurpriseVertexPartition)
```

**Properties**:
- Measures deviation from random expectation
- **Positive weights only**
- No resolution parameter
- Alternative to modularity without resolution limit

**Use When**:
- Want surprise-based quality
- Working with positive weights
- Seeking alternative to modularity

---

### Quality Function Comparison Table

| Quality Function | Resolution Param | Negative Weights | Weighted | Resolution Limit | Null Model |
|-----------------|------------------|------------------|----------|------------------|------------|
| Modularity | No | No | Yes | Yes | Configuration |
| RBConfiguration | Yes (linear) | No | Yes | Addressable | Configuration |
| CPM | Yes (density) | **Yes** | Yes | **No** | Constant |
| RBER | Yes (linear) | No | Yes | Addressable | Erdős-Rényi |
| Significance | No | No | **No** | No | KL-divergence |
| Surprise | No | No | Yes | **No** | Binary KL |

---

## Parameter Tuning

### Resolution Parameter (γ)

The resolution parameter is the most critical parameter for Leiden algorithm.

#### What Resolution Controls

```
Higher γ → More communities (smaller, denser)
Lower γ → Fewer communities (larger, sparser)
```

#### Resolution Parameter by Quality Function

**CPM (Constant Potts Model)**:
```python
# γ = desired density threshold
# Communities will have internal density ≥ γ
# Inter-community density will be ≤ γ

# Example: Find communities with density ≥ 0.3
partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.3)
```

**Interpretation**:
- γ = 0.05: Very loose communities (5% internal density)
- γ = 0.5: Moderate communities (50% internal density)
- γ = 0.9: Very dense communities (90% internal density)

**RBConfiguration**:
```python
# γ scales the null model
# γ = 1.0: Standard modularity
# γ > 1.0: Find smaller communities
# γ < 1.0: Find larger communities

partition = la.find_partition(G, la.RBConfigurationVertexPartition,
                              resolution_parameter=1.5)
```

#### How to Choose Resolution Parameter

There is **no a-priori way** to choose the optimal γ. Use these strategies:

##### Strategy 1: Resolution Profile Scanning

```python
from leidenalg import Optimiser

optimiser = Optimiser()

# Scan range of resolutions
resolution_range = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]

results = []
for gamma in resolution_range:
    partition = la.find_partition(G, la.CPMVertexPartition,
                                  resolution_parameter=gamma)
    results.append({
        'gamma': gamma,
        'num_communities': len(partition),
        'quality': partition.quality(),
        'modularity': partition.modularity()
    })

# Plot results to find stable "plateaus"
import matplotlib.pyplot as plt
gammas = [r['gamma'] for r in results]
num_comms = [r['num_communities'] for r in results]
plt.plot(gammas, num_comms)
plt.xscale('log')
plt.xlabel('Resolution parameter (γ)')
plt.ylabel('Number of communities')
plt.show()
```

##### Strategy 2: Stability Analysis

Look for "plateaus" where partition remains stable across γ range:

```python
def stability_analysis(G, resolution_range):
    """Find stable resolution ranges."""
    partitions = []
    for gamma in resolution_range:
        p = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=gamma)
        partitions.append(p)

    # Compare consecutive partitions
    stabilities = []
    for i in range(len(partitions)-1):
        # Use Normalized Mutual Information
        from sklearn.metrics import normalized_mutual_info_score as nmi
        similarity = nmi(partitions[i].membership,
                        partitions[i+1].membership)
        stabilities.append(similarity)

    # High stability = good resolution choice
    return stabilities
```

##### Strategy 3: Domain Knowledge

Use known properties of your network:

```python
# For social networks: typical community size 10-100 nodes
# Calculate expected density and use as starting point

avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
network_density = 2 * G.number_of_edges() / (G.number_of_nodes() * (G.number_of_nodes() - 1))

# Start with network density as γ
gamma_start = network_density
```

##### Strategy 4: Multi-Scale Analysis

```python
# Detect communities at multiple resolutions
resolutions = [0.01, 0.1, 0.5, 1.0, 2.0]
hierarchical_communities = {}

for gamma in resolutions:
    partition = la.find_partition(G, la.CPMVertexPartition,
                                  resolution_parameter=gamma)
    hierarchical_communities[gamma] = partition
    print(f"γ={gamma}: {len(partition)} communities")
```

#### Guidelines for Different Network Types

```python
# Social Networks: γ = 0.05 - 0.2
# Good starting point for typical social structure

# Biological Networks: γ = 0.1 - 0.5
# Biological modules tend to be dense

# Citation Networks: γ = 0.01 - 0.1
# Research communities are loosely connected

# Infrastructure Networks: γ = 0.3 - 0.8
# Physical constraints create dense communities
```

---

### Number of Iterations (n_iterations)

```python
partition = la.find_partition(G, la.CPMVertexPartition,
                              n_iterations=2,  # Default
                              resolution_parameter=0.1)
```

**Effects**:
- `n_iterations=1`: Fast, may not converge
- `n_iterations=2`: Default, good balance
- `n_iterations=-1`: Run until convergence (can be slow)
- `n_iterations=10`: Very thorough, diminishing returns

**Recommendation**: Start with default (2), increase if quality improvements are needed.

---

### Maximum Community Size (max_comm_size)

```python
partition = la.find_partition(G, la.CPMVertexPartition,
                              max_comm_size=100,  # Limit community size
                              resolution_parameter=0.1)
```

**Use Cases**:
- Prevent extremely large communities
- Ensure interpretable community sizes
- `max_comm_size=0`: No limit (default)

---

### Node Sizes (Custom Weighting)

```python
# Weight communities by custom node importance
node_sizes = {node: custom_importance(node) for node in G.nodes()}

partition = la.find_partition(G, la.CPMVertexPartition,
                              node_sizes=node_sizes,
                              resolution_parameter=0.1)
```

**Use Cases**:
- Scientific papers: weight by citation count
- Social networks: weight by influence
- Biological networks: weight by expression level

---

### Edge Weights

```python
# For weighted graphs, pass weights parameter
edge_weights = [G[u][v]['weight'] for u, v in G.edges()]

partition = la.find_partition(G, la.CPMVertexPartition,
                              weights=edge_weights,
                              resolution_parameter=0.1)
```

**Handling Different Weight Ranges**:

```python
# Normalize weights to [0, 1] range
import numpy as np

weights = np.array([G[u][v]['weight'] for u, v in G.edges()])
normalized_weights = (weights - weights.min()) / (weights.max() - weights.min())

# Or use log transform for skewed distributions
log_weights = np.log1p(weights)  # log(1 + x) to handle zeros
```

---

## Implementation Guide

### Installation

```bash
# Install python-igraph and leidenalg
pip install igraph leidenalg

# Or with conda
conda install -c conda-forge igraph leidenalg
```

**Version Requirements**:
- Python >= 3.9
- igraph >= 0.10
- leidenalg >= 0.10

---

### Basic Usage Patterns

#### Pattern 1: Simple Community Detection

```python
import igraph as ig
import leidenalg as la

# Create or load graph
G = ig.Graph.Famous('Zachary')

# Detect communities using modularity
partition = la.find_partition(G, la.ModularityVertexPartition)

# Access results
print(f"Found {len(partition)} communities")
print(f"Modularity: {partition.quality():.3f}")
print(f"Membership: {partition.membership}")

# Visualize
ig.plot(partition, "communities.png", bbox=(800, 800))
```

#### Pattern 2: CPM with Resolution Tuning

```python
import igraph as ig
import leidenalg as la

G = ig.Graph.Read_GML('network.gml')

# Try different resolutions
for gamma in [0.01, 0.05, 0.1, 0.5, 1.0]:
    partition = la.find_partition(
        G,
        la.CPMVertexPartition,
        resolution_parameter=gamma,
        n_iterations=5  # Thorough optimization
    )

    print(f"γ={gamma:4.2f}: {len(partition):3d} communities, "
          f"Q={partition.quality():6.2f}")
```

#### Pattern 3: Weighted Graph

```python
import igraph as ig
import leidenalg as la

# Create weighted graph
G = ig.Graph()
G.add_vertices(10)
G.add_edges([(0,1), (1,2), (2,3)])
G.es['weight'] = [1.0, 0.5, 0.8]

# Detect communities with weights
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    weights='weight',  # Use 'weight' attribute
    resolution_parameter=0.1
)

# Or pass weights directly
weights = G.es['weight']
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    weights=weights,
    resolution_parameter=0.1
)
```

#### Pattern 4: Directed Graphs

```python
import igraph as ig
import leidenalg as la

# Leiden works with directed graphs
G = ig.Graph.Erdos_Renyi(n=100, p=0.05, directed=True)

partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    resolution_parameter=0.1
)

# Modularity calculation respects directionality
print(f"Directed modularity: {partition.modularity()}")
```

#### Pattern 5: Initial Membership

```python
import igraph as ig
import leidenalg as la

G = ig.Graph.Famous('Zachary')

# Start from known partition (e.g., from another algorithm)
initial_membership = G.community_fastgreedy().as_clustering().membership

# Refine with Leiden
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    initial_membership=initial_membership,
    resolution_parameter=0.1
)

print("Refined community structure")
```

---

### Advanced Usage

#### Using Optimiser Class

```python
import leidenalg as la

# Create optimiser with custom settings
optimiser = la.Optimiser()

# Control refinement phase
optimiser.refine_partition = True  # Enable refinement (default)

# Control community consideration
optimiser.consider_comms = la.Optimiser.ALL_NEIGH_COMMS  # Default
# Options:
# - ALL_COMMS: Consider all communities (slow)
# - ALL_NEIGH_COMMS: Consider neighbor communities (default)
# - RAND_COMM: Random community
# - RAND_NEIGH_COMM: Random neighbor community

# Optimize partition
partition = la.CPMVertexPartition(G, resolution_parameter=0.1)
diff = optimiser.optimise_partition(partition, n_iterations=10)

print(f"Quality improvement: {diff}")
```

#### Multiplex Networks

```python
import igraph as ig
import leidenalg as la

# Create multiplex network (multiple layers)
G_social = ig.Graph.Erdos_Renyi(n=100, p=0.05)
G_work = ig.Graph.Erdos_Renyi(n=100, p=0.03)
G_family = ig.Graph.Erdos_Renyi(n=100, p=0.02)

layers = [G_social, G_work, G_family]
layer_weights = [1.0, 0.5, 0.5]  # Weight importance of each layer

# Find partition across all layers
partitions, improvement = la.find_partition_multiplex(
    layers,
    la.CPMVertexPartition,
    layer_weights=layer_weights,
    resolution_parameter=0.1,
    n_iterations=5
)

print(f"Quality improvement: {improvement}")
for i, partition in enumerate(partitions):
    print(f"Layer {i}: {len(partition)} communities")
```

#### Temporal Networks

```python
import igraph as ig
import leidenalg as la

# Time slices of evolving network
time_slices = []
for t in range(10):
    G_t = ig.Graph.Erdos_Renyi(n=100, p=0.05)
    G_t.vs['time'] = t
    time_slices.append(G_t)

# Find communities across time with temporal coupling
partitions, improvement = la.find_partition_temporal(
    time_slices,
    la.CPMVertexPartition,
    interslice_weight=0.1,  # Weight for temporal connections
    slice_attr='time',
    resolution_parameter=0.1,
    n_iterations=5
)

print(f"Found communities across {len(partitions)} time slices")
```

#### Bipartite Networks

```python
import igraph as ig
import leidenalg as la

# Create bipartite graph (e.g., users and items)
G = ig.Graph.Bipartite([0,0,0,1,1,1,1], [(0,3), (0,4), (1,4), (1,5), (2,5), (2,6)])

# Detect communities in bipartite structure
partition = la.CPMVertexPartition.Bipartite(
    G,
    resolution_parameter_01=0.5,  # Between-type edges
    resolution_parameter_0=0.0,   # Within type-0
    resolution_parameter_1=0.0,   # Within type-1
    types='type'  # Attribute indicating type
)

optimiser = la.Optimiser()
optimiser.optimise_partition(partition)

print(f"Bipartite communities: {len(partition)}")
```

---

### Converting from NetworkX

```python
import networkx as nx
import igraph as ig
import leidenalg as la

# Create NetworkX graph
G_nx = nx.karate_club_graph()

# Convert to igraph
# Method 1: Via edge list
edge_list = list(G_nx.edges())
G_ig = ig.Graph(edge_list)

# Method 2: Via adjacency matrix
adj_matrix = nx.to_scipy_sparse_array(G_nx)
G_ig = ig.Graph.Adjacency(adj_matrix.tolist())

# Method 3: Preserve attributes
G_ig = ig.Graph(directed=G_nx.is_directed())
G_ig.add_vertices(list(G_nx.nodes()))
G_ig.add_edges(list(G_nx.edges()))

# Copy node attributes
for node in G_nx.nodes():
    for attr, value in G_nx.nodes[node].items():
        G_ig.vs[node][attr] = value

# Copy edge attributes
for i, (u, v) in enumerate(G_nx.edges()):
    for attr, value in G_nx.edges[u, v].items():
        G_ig.es[i][attr] = value

# Now use Leiden
partition = la.find_partition(G_ig, la.CPMVertexPartition,
                              resolution_parameter=0.1)

# Convert membership back to NetworkX
for node, community in zip(G_nx.nodes(), partition.membership):
    G_nx.nodes[node]['community'] = community
```

---

### Saving and Loading Results

```python
import igraph as ig
import leidenalg as la
import pickle

# Detect communities
G = ig.Graph.Famous('Zachary')
partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

# Save partition membership
membership = partition.membership

# Method 1: Add to graph and save
G.vs['community'] = membership
G.write_graphml('network_with_communities.graphml')

# Method 2: Save as JSON
import json
community_dict = {i: comm for i, comm in enumerate(membership)}
with open('communities.json', 'w') as f:
    json.dump(community_dict, f)

# Method 3: Pickle the partition object
with open('partition.pkl', 'wb') as f:
    pickle.dump(partition, f)

# Load partition
with open('partition.pkl', 'rb') as f:
    loaded_partition = pickle.load(f)
```

---

## When to Use Leiden vs Other Algorithms

### Algorithm Decision Matrix

```
Choose LEIDEN when:
✓ Need guaranteed well-connected communities
✓ Quality is more important than speed
✓ Working with large complex networks
✓ Iterative refinement is required
✓ Need reproducible, theoretically-grounded results

Choose LOUVAIN when:
✗ Speed is absolutely critical (but Leiden is often faster anyway)
✗ Disconnected communities are acceptable (rare use case)
✗ Legacy system compatibility required

Choose INFOMAP when:
✓ Network represents information or movement flow
✓ Want to understand random walk patterns
✓ Need stable, consistent results
✓ Have directed networks representing flows

Choose LABEL PROPAGATION when:
✓ Extremely large networks (millions of nodes)
✓ Speed is paramount
✓ Result variability is acceptable
✓ Can run multiple times for consensus

Choose SPECTRAL CLUSTERING when:
✓ Small to medium networks
✓ Want mathematically clean solution
✓ Have computational resources for eigendecomposition

Choose EDGE BETWEENNESS when:
✓ Small networks (<1000 nodes)
✓ Want hierarchical dendrogram
✓ Can afford O(m²n) complexity
```

### Detailed Comparisons

#### Leiden vs Louvain

```
WINNER: Leiden in almost all cases

Louvain advantages:
- Slightly more widely available in older software
- Marginally faster in very specific cases

Leiden advantages:
- Guarantees connected communities
- Better partition quality
- Usually faster (2-20x)
- Theoretical guarantees
- Continues improving in iterations

Recommendation: Use Leiden. It's the superior algorithm.
```

#### Leiden vs Infomap

```
COMPLEMENTARY: Use both for different purposes

Infomap advantages:
- Better for flow-based networks
- More stable results
- Natural for directed graphs

Leiden advantages:
- More flexible quality functions
- Resolution parameter control
- Faster on large networks
- Better for structural communities

Recommendation:
- Flow networks (web, transport): Infomap
- Structural communities (social, biological): Leiden
- Compare both and choose based on results
```

#### Leiden vs Label Propagation

```
TRADE-OFF: Quality vs extreme scale

Label Propagation advantages:
- Fastest algorithm
- Scales to millions of nodes
- Simple implementation

Leiden advantages:
- Much better quality
- Reproducible results
- Theoretical guarantees
- Controllable resolution

Recommendation:
- Network < 10M edges: Leiden
- Network > 10M edges: Try Leiden first, fall back to LP if needed
- Can use LP for initialization, then refine with Leiden
```

---

### Algorithm Selection Flowchart

```
Start
  |
  ├─ Graph size?
  │   ├─ < 10K nodes → Leiden or Infomap
  │   ├─ 10K-1M nodes → Leiden (primary choice)
  │   └─ > 1M nodes → Leiden first, Label Propagation if too slow
  |
  ├─ Graph type?
  │   ├─ Directed flow network → Infomap or Leiden
  │   ├─ Weighted network → Leiden (especially if negative weights)
  │   ├─ Bipartite → Leiden (built-in support)
  │   └─ Temporal/Multiplex → Leiden (built-in support)
  |
  ├─ Quality requirements?
  │   ├─ Need guarantees → Leiden
  │   ├─ Speed critical → Label Propagation or Leiden
  │   └─ Hierarchical structure → Leiden at multiple resolutions
  |
  └─ Resolution needs?
      ├─ Need fine control → Leiden (CPM or RB)
      ├─ Single scale → Leiden (Modularity)
      └─ Multi-scale → Leiden (scan resolutions)
```

---

## Performance Characteristics

### Time Complexity

```
Leiden: O(L|E|)
- L = number of iterations
- |E| = number of edges
- Near-linear scaling with network size
```

**Empirical Performance**:
```python
# Approximate runtimes (rough guidelines)
# Modern laptop (Intel i7)

Graph Size      | Time (Leiden)  | Time (Louvain)
----------------|----------------|----------------
1K nodes        | < 0.1s        | < 0.1s
10K nodes       | 0.5-1s        | 0.5-2s
100K nodes      | 5-10s         | 10-50s
1M nodes        | 50-100s       | 100-500s
10M edges       | 100-200s      | 300-1000s
```

### Space Complexity

```
Space: O(|V| + |E|)
- |V| = number of vertices
- |E| = number of edges
- Linear space requirement
```

### Runtime Distribution

For typical graphs, Leiden spends:
- **46%** in local-moving phase
- **19%** in refinement phase
- **20%** in aggregation phase
- **15%** in other operations

**First iteration dominates**: 63% of total runtime in first pass

### Scalability

```python
# Parallel implementation (GVE-Leiden)
# Can achieve 3.8B edges/sec on 2x Intel Xeon Gold 6226R (32 cores)

# Standard implementation scales well to:
# - 10M nodes
# - 100M edges
# - Using < 10GB RAM
```

### Convergence Behavior

```python
# Monitor convergence
import leidenalg as la

partition = la.CPMVertexPartition(G, resolution_parameter=0.1)
optimiser = la.Optimiser()

improvements = []
for iteration in range(10):
    improvement = optimiser.optimise_partition(partition, n_iterations=1)
    improvements.append(improvement)
    print(f"Iteration {iteration}: improvement = {improvement:.6f}")

    if improvement < 1e-6:
        print("Converged!")
        break

# Plot convergence
import matplotlib.pyplot as plt
plt.plot(improvements)
plt.xlabel('Iteration')
plt.ylabel('Quality improvement')
plt.yscale('log')
plt.show()
```

**Typical Convergence**:
- Iteration 1: Large improvement (70-90% of total)
- Iteration 2: Moderate improvement (5-20%)
- Iteration 3+: Diminishing returns (< 5%)
- Usually converges in 3-5 iterations

---

## Best Practices for Graph Preparation

### 1. Handle Self-Loops

```python
import igraph as ig

# Remove self-loops (usually recommended)
G = ig.Graph.Erdos_Renyi(n=100, p=0.05)
G.simplify(multiple=False, loops=True)

# Or keep self-loops if they're meaningful
# (e.g., self-citations in citation network)
```

**Recommendation**: Remove self-loops unless they have specific meaning.

---

### 2. Handle Multiple Edges

```python
import igraph as ig

# Combine multiple edges by summing weights
G.simplify(multiple=True, loops=True, combine_edges='sum')

# Or use max weight
G.simplify(combine_edges='max')

# Or use mean weight
G.simplify(combine_edges='mean')
```

---

### 3. Normalize Edge Weights

```python
import numpy as np

# Get all edge weights
weights = np.array(G.es['weight'])

# Method 1: Min-max normalization to [0, 1]
normalized = (weights - weights.min()) / (weights.max() - weights.min())

# Method 2: Z-score normalization
normalized = (weights - weights.mean()) / weights.std()

# Method 3: Log transform for skewed distributions
normalized = np.log1p(weights)  # log(1 + x)

# Method 4: Percentile-based (robust to outliers)
from scipy import stats
normalized = stats.rankdata(weights) / len(weights)

# Apply normalized weights
G.es['weight'] = normalized.tolist()
```

**When to Normalize**:
- Weights span multiple orders of magnitude
- Comparing different edge types
- Combining multiple graphs

---

### 4. Handle Disconnected Components

```python
import igraph as ig

# Find connected components
components = G.components()

print(f"Number of components: {len(components)}")
print(f"Largest component size: {max(components.sizes())}")

# Option 1: Work with largest component only
giant_component = components.giant()

# Option 2: Process each component separately
for component in components:
    subgraph = component.subgraph()
    partition = la.find_partition(subgraph, la.CPMVertexPartition,
                                  resolution_parameter=0.1)
    print(f"Component with {subgraph.vcount()} nodes: "
          f"{len(partition)} communities")

# Option 3: Add artificial connections (use with caution)
# Not generally recommended
```

**Recommendation**: Process largest component or handle components separately.

---

### 5. Remove Low-Degree Nodes (Optional)

```python
# Remove isolated nodes or very low-degree nodes
min_degree = 2
to_delete = [v.index for v in G.vs if v.degree() < min_degree]
G.delete_vertices(to_delete)

print(f"Removed {len(to_delete)} low-degree nodes")
```

**When to Remove**:
- Many isolated or near-isolated nodes
- Focus on core network structure
- Reduce noise in community detection

**When NOT to Remove**:
- All nodes are important
- Studying network periphery
- Small networks

---

### 6. Weight Filtering

```python
# Remove weak edges
threshold = 0.1
strong_edges = [e.index for e in G.es if e['weight'] > threshold]
G_filtered = G.subgraph_edges(strong_edges, delete_vertices=False)

# Or remove edges in bottom percentile
import numpy as np
weights = np.array(G.es['weight'])
threshold = np.percentile(weights, 10)  # Bottom 10%
strong_edges = [e.index for e in G.es if e['weight'] > threshold]
G_filtered = G.subgraph_edges(strong_edges, delete_vertices=False)
```

**Use Case**: Focus on strong relationships, reduce noise.

---

### 7. Graph Laplacian Normalization

```python
import numpy as np
from scipy.sparse import csr_matrix

# Get adjacency matrix
A = np.array(G.get_adjacency(attribute='weight').data)

# Compute degree matrix
D = np.diag(A.sum(axis=1))

# Symmetric normalized Laplacian: L = I - D^(-1/2) A D^(-1/2)
D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(D)))
L_sym = np.eye(len(A)) - D_inv_sqrt @ A @ D_inv_sqrt

# Random walk normalized Laplacian: L = I - D^(-1) A
D_inv = np.linalg.inv(D)
L_rw = np.eye(len(A)) - D_inv @ A

# Use for spectral initialization or feature extraction
```

**Use Case**: Preprocessing for spectral methods or feature engineering.

---

### 8. Dealing with Negative Weights

```python
# Only CPM supports negative weights
partition = la.find_partition(
    G,
    la.CPMVertexPartition,  # Use CPM!
    weights='weight',
    resolution_parameter=0.1
)

# For other methods, need to handle negatives:

# Option 1: Shift to positive range
import numpy as np
weights = np.array(G.es['weight'])
shifted = weights - weights.min() + 0.01  # Ensure > 0
G.es['weight'] = shifted.tolist()

# Option 2: Split into positive and negative graphs
pos_edges = [(u, v, w) for u, v, w in G.es.attributes() if w['weight'] > 0]
neg_edges = [(u, v, abs(w)) for u, v, w in G.es.attributes() if w['weight'] < 0]

G_pos = ig.Graph(edges=[(e[0], e[1]) for e in pos_edges])
G_pos.es['weight'] = [e[2] for e in pos_edges]

# Detect communities on positive graph
partition_pos = la.find_partition(G_pos, la.CPMVertexPartition,
                                  resolution_parameter=0.1)
```

---

### Complete Preprocessing Pipeline

```python
import igraph as ig
import leidenalg as la
import numpy as np

def preprocess_graph_for_leiden(G,
                                remove_self_loops=True,
                                remove_multi_edges=True,
                                normalize_weights=True,
                                min_degree=1,
                                weight_threshold=None):
    """
    Complete preprocessing pipeline for Leiden algorithm.

    Args:
        G: igraph.Graph
        remove_self_loops: Remove self-loops
        remove_multi_edges: Combine multiple edges
        normalize_weights: Normalize edge weights to [0,1]
        min_degree: Remove nodes with degree < min_degree
        weight_threshold: Remove edges with weight < threshold

    Returns:
        Preprocessed graph
    """
    G = G.copy()  # Don't modify original

    # 1. Simplify graph
    if remove_self_loops or remove_multi_edges:
        G.simplify(multiple=remove_multi_edges,
                   loops=remove_self_loops,
                   combine_edges='sum' if 'weight' in G.es.attributes() else None)

    # 2. Normalize weights
    if normalize_weights and 'weight' in G.es.attributes():
        weights = np.array(G.es['weight'])
        if weights.std() > 0:  # Avoid division by zero
            normalized = (weights - weights.min()) / (weights.max() - weights.min())
            G.es['weight'] = normalized.tolist()

    # 3. Filter weak edges
    if weight_threshold is not None and 'weight' in G.es.attributes():
        strong_edges = [e.index for e in G.es if e['weight'] >= weight_threshold]
        G = G.subgraph_edges(strong_edges, delete_vertices=False)

    # 4. Remove low-degree nodes
    if min_degree > 0:
        while True:
            to_delete = [v.index for v in G.vs if v.degree() < min_degree]
            if not to_delete:
                break
            G.delete_vertices(to_delete)

    # 5. Work with largest component
    components = G.components()
    if len(components) > 1:
        print(f"Warning: Graph has {len(components)} components. "
              f"Using largest ({max(components.sizes())} nodes).")
        G = components.giant()

    print(f"Preprocessed graph: {G.vcount()} nodes, {G.ecount()} edges")
    return G

# Usage
G = ig.Graph.Read_GML('network.gml')
G_clean = preprocess_graph_for_leiden(
    G,
    normalize_weights=True,
    min_degree=2,
    weight_threshold=0.1
)

partition = la.find_partition(G_clean, la.CPMVertexPartition,
                              resolution_parameter=0.1)
```

---

## Quality Metrics and Evaluation

### Internal Metrics (No Ground Truth Required)

#### 1. Modularity

```python
import leidenalg as la

partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

# Calculate modularity
Q = partition.modularity()
print(f"Modularity: {Q:.4f}")

# Interpretation:
# Q > 0.3: Strong community structure
# Q = 0.2-0.3: Moderate community structure
# Q < 0.2: Weak community structure
# Q ≈ 0: No better than random
```

#### 2. Quality Function Value

```python
# Quality depends on partition type
partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

quality = partition.quality()
print(f"CPM Quality: {quality:.4f}")

# Higher is better, but absolute value depends on:
# - Graph size
# - Resolution parameter
# - Quality function used
```

#### 3. Conductance (Cut Ratio)

```python
import numpy as np

def community_conductance(G, membership, community_id):
    """
    Calculate conductance for a single community.
    Lower is better (fewer edges leaving community).
    """
    community_nodes = [i for i, c in enumerate(membership) if c == community_id]

    # Internal edges
    internal = 0
    external = 0

    for node in community_nodes:
        for neighbor in G.neighbors(node):
            if neighbor in community_nodes:
                internal += 1
            else:
                external += 1

    internal //= 2  # Each edge counted twice

    if external == 0:
        return 0.0  # Perfect community

    conductance = external / (2 * internal + external)
    return conductance

# Calculate for all communities
partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

conductances = []
for comm_id in range(len(partition)):
    cond = community_conductance(G, partition.membership, comm_id)
    conductances.append(cond)
    print(f"Community {comm_id}: conductance = {cond:.4f}")

print(f"Mean conductance: {np.mean(conductances):.4f}")

# Interpretation:
# Conductance = 0: No edges leave community (perfect)
# Conductance < 0.1: Very good separation
# Conductance < 0.3: Reasonable separation
# Conductance > 0.5: Poor separation
```

#### 4. Coverage and Performance

```python
def coverage_and_performance(G, membership):
    """
    Coverage: Fraction of edges within communities
    Performance: Edges correctly classified (internal + external)
    """
    total_edges = G.ecount()
    internal_edges = 0

    for edge in G.es:
        source, target = edge.tuple
        if membership[source] == membership[target]:
            internal_edges += 1

    coverage = internal_edges / total_edges

    # Performance (edges correctly classified)
    possible_edges = G.vcount() * (G.vcount() - 1) / 2
    internal_non_edges = 0

    # Count non-edges within communities
    from collections import defaultdict
    comms = defaultdict(list)
    for i, c in enumerate(membership):
        comms[c].append(i)

    for nodes in comms.values():
        n = len(nodes)
        internal_non_edges += n * (n - 1) / 2 - sum(
            1 for i in nodes for j in nodes
            if i < j and G.are_connected(i, j)
        )

    performance = (internal_edges + internal_non_edges) / possible_edges

    return coverage, performance

partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

coverage, performance = coverage_and_performance(G, partition.membership)
print(f"Coverage: {coverage:.4f}")
print(f"Performance: {performance:.4f}")

# Interpretation:
# Coverage: Higher is better (more edges within communities)
# Performance: Higher is better (better edge classification)
```

---

### External Metrics (With Ground Truth)

#### 1. Normalized Mutual Information (NMI)

```python
from sklearn.metrics import normalized_mutual_info_score

# Compare detected communities with ground truth
ground_truth = [0, 0, 0, 1, 1, 1, 2, 2, 2, 2]
detected = partition.membership

nmi = normalized_mutual_info_score(ground_truth, detected)
print(f"NMI: {nmi:.4f}")

# Interpretation:
# NMI = 1.0: Perfect agreement
# NMI = 0.8-1.0: Very good
# NMI = 0.5-0.8: Moderate agreement
# NMI < 0.5: Poor agreement
# NMI = 0.0: No agreement

# Note: NMI has bias issues with many communities
```

#### 2. Adjusted Rand Index (ARI)

```python
from sklearn.metrics import adjusted_rand_score

ari = adjusted_rand_score(ground_truth, detected)
print(f"ARI: {ari:.4f}")

# Interpretation:
# ARI = 1.0: Perfect agreement
# ARI = 0.0: Random agreement (adjusted for chance)
# ARI < 0.0: Worse than random
```

#### 3. Variation of Information (VI)

```python
from sklearn.metrics.cluster import contingency_matrix
import numpy as np

def variation_of_information(labels_true, labels_pred):
    """
    Calculate Variation of Information.
    Lower is better (0 = perfect agreement).
    """
    n = len(labels_true)
    contingency = contingency_matrix(labels_true, labels_pred)

    # Joint probabilities
    p_ij = contingency / n

    # Marginal probabilities
    p_i = p_ij.sum(axis=1)
    p_j = p_ij.sum(axis=0)

    # Entropy calculations
    H_UV = -np.sum(p_ij[p_ij > 0] * np.log(p_ij[p_ij > 0]))
    H_U = -np.sum(p_i[p_i > 0] * np.log(p_i[p_i > 0]))
    H_V = -np.sum(p_j[p_j > 0] * np.log(p_j[p_j > 0]))

    # Mutual information
    MI = H_U + H_V - H_UV

    # Variation of information
    VI = H_UV - MI

    return VI

vi = variation_of_information(ground_truth, detected)
print(f"VI: {vi:.4f}")

# Lower is better (0 = perfect)
```

---

### Stability Analysis

```python
import numpy as np
from sklearn.metrics import normalized_mutual_info_score

def stability_analysis(G, partition_type, resolution, n_runs=10):
    """
    Test stability across multiple runs with different random seeds.
    """
    partitions = []

    for seed in range(n_runs):
        partition = la.find_partition(
            G,
            partition_type,
            resolution_parameter=resolution,
            seed=seed
        )
        partitions.append(partition.membership)

    # Compare all pairs
    nmis = []
    for i in range(n_runs):
        for j in range(i+1, n_runs):
            nmi = normalized_mutual_info_score(partitions[i], partitions[j])
            nmis.append(nmi)

    stability = np.mean(nmis)
    return stability, partitions

# Test stability
stability, partitions = stability_analysis(
    G,
    la.CPMVertexPartition,
    resolution=0.1,
    n_runs=10
)

print(f"Stability (mean NMI): {stability:.4f}")

# Interpretation:
# Stability > 0.95: Very stable results
# Stability > 0.8: Reasonably stable
# Stability < 0.8: Results vary significantly
```

---

### Complete Evaluation Suite

```python
def evaluate_partition(G, partition, ground_truth=None):
    """
    Comprehensive evaluation of community detection results.
    """
    results = {}

    # Basic statistics
    results['num_communities'] = len(partition)
    results['community_sizes'] = np.bincount(partition.membership)
    results['mean_community_size'] = np.mean(results['community_sizes'])
    results['std_community_size'] = np.std(results['community_sizes'])

    # Internal metrics
    results['modularity'] = partition.modularity()
    results['quality'] = partition.quality()

    coverage, performance = coverage_and_performance(G, partition.membership)
    results['coverage'] = coverage
    results['performance'] = performance

    # Conductances
    conductances = [
        community_conductance(G, partition.membership, i)
        for i in range(len(partition))
    ]
    results['mean_conductance'] = np.mean(conductances)
    results['min_conductance'] = np.min(conductances)
    results['max_conductance'] = np.max(conductances)

    # External metrics (if ground truth available)
    if ground_truth is not None:
        from sklearn.metrics import (normalized_mutual_info_score,
                                     adjusted_rand_score)
        results['nmi'] = normalized_mutual_info_score(
            ground_truth, partition.membership
        )
        results['ari'] = adjusted_rand_score(
            ground_truth, partition.membership
        )
        results['vi'] = variation_of_information(
            ground_truth, partition.membership
        )

    return results

# Usage
partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

evaluation = evaluate_partition(G, partition, ground_truth=None)

print("\nPartition Evaluation:")
print("=" * 50)
for metric, value in evaluation.items():
    if isinstance(value, float):
        print(f"{metric:20s}: {value:6.4f}")
    else:
        print(f"{metric:20s}: {value}")
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Not Checking for Disconnected Communities

**Problem**: Even Leiden can produce disconnected communities if not used properly.

**Solution**:
```python
def verify_connected_communities(G, membership):
    """Verify all communities are connected."""
    from collections import defaultdict
    import igraph as ig

    # Group nodes by community
    communities = defaultdict(list)
    for node, comm in enumerate(membership):
        communities[comm].append(node)

    disconnected = []
    for comm_id, nodes in communities.items():
        subgraph = G.subgraph(nodes)
        components = subgraph.components()

        if len(components) > 1:
            disconnected.append({
                'community': comm_id,
                'num_components': len(components),
                'sizes': components.sizes()
            })

    if disconnected:
        print("WARNING: Found disconnected communities!")
        for d in disconnected:
            print(f"  Community {d['community']}: "
                  f"{d['num_components']} components, sizes {d['sizes']}")
        return False
    else:
        print("All communities are connected ✓")
        return True

partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

verify_connected_communities(G, partition.membership)
```

---

### Pitfall 2: Wrong Quality Function for Negative Weights

**Problem**: Using Modularity or RB with negative weights causes errors or incorrect results.

**Solution**:
```python
# Check for negative weights
if 'weight' in G.es.attributes():
    weights = G.es['weight']
    has_negative = any(w < 0 for w in weights)

    if has_negative:
        print("Negative weights detected. Using CPM.")
        partition = la.find_partition(
            G,
            la.CPMVertexPartition,  # Only CPM supports negative weights
            weights='weight',
            resolution_parameter=0.1
        )
    else:
        print("All weights positive. Using RBConfiguration.")
        partition = la.find_partition(
            G,
            la.RBConfigurationVertexPartition,
            weights='weight',
            resolution_parameter=1.0
        )
else:
    # Unweighted graph
    partition = la.find_partition(G, la.ModularityVertexPartition)
```

---

### Pitfall 3: Resolution Parameter Too High or Too Low

**Problem**: Extreme resolution values produce trivial results (all singletons or one giant community).

**Solution**:
```python
def find_reasonable_resolution_range(G):
    """Find reasonable resolution parameter range."""
    import numpy as np

    # Calculate network density
    n = G.vcount()
    m = G.ecount()
    density = 2 * m / (n * (n - 1))

    # Reasonable range: [density/10, density*10]
    min_res = density / 10
    max_res = density * 10

    print(f"Network density: {density:.4f}")
    print(f"Suggested resolution range: [{min_res:.4f}, {max_res:.4f}]")

    # Test extreme values
    resolutions = [min_res, density, max_res]

    for gamma in resolutions:
        partition = la.find_partition(G, la.CPMVertexPartition,
                                      resolution_parameter=gamma)
        print(f"γ={gamma:.4f}: {len(partition)} communities")

    return min_res, max_res

min_res, max_res = find_reasonable_resolution_range(G)
```

---

### Pitfall 4: Not Normalizing Heterogeneous Weights

**Problem**: Edge weights from different sources have different scales.

**Solution**:
```python
import numpy as np

def normalize_by_type(G, weight_attr='weight', type_attr='edge_type'):
    """
    Normalize weights within each edge type separately.
    """
    if type_attr not in G.es.attributes():
        print("No edge types found. Using global normalization.")
        weights = np.array(G.es[weight_attr])
        G.es[weight_attr] = ((weights - weights.min()) /
                             (weights.max() - weights.min())).tolist()
        return

    # Normalize by type
    edge_types = set(G.es[type_attr])

    for edge_type in edge_types:
        type_edges = [e.index for e in G.es if e[type_attr] == edge_type]
        weights = np.array([G.es[i][weight_attr] for i in type_edges])

        if weights.std() > 0:  # Avoid division by zero
            normalized = (weights - weights.min()) / (weights.max() - weights.min())

            for i, norm_weight in zip(type_edges, normalized):
                G.es[i][weight_attr] = norm_weight

    print(f"Normalized {len(edge_types)} edge types")

# Usage
normalize_by_type(G, weight_attr='weight', type_attr='type')
```

---

### Pitfall 5: Ignoring Graph Preprocessing

**Problem**: Running Leiden on raw, messy graphs produces poor results.

**Solution**: Always preprocess (see [Best Practices](#best-practices-for-graph-preparation))

```python
# Checklist before running Leiden:
# ✓ Remove or handle self-loops
# ✓ Combine multiple edges
# ✓ Check for disconnected components
# ✓ Normalize weights if heterogeneous
# ✓ Consider removing very low-degree nodes
# ✓ Verify no extreme outliers in weights
```

---

### Pitfall 6: Comparing Results Across Different Resolutions

**Problem**: Directly comparing community counts or quality values at different resolutions.

**Solution**:
```python
# Don't compare quality values directly
# DO compare structural properties

def compare_resolutions(G, resolutions):
    """
    Compare community detection results across resolutions.
    Use structural metrics, not quality values.
    """
    results = []

    for gamma in resolutions:
        partition = la.find_partition(G, la.CPMVertexPartition,
                                      resolution_parameter=gamma)

        coverage, performance = coverage_and_performance(G, partition.membership)

        results.append({
            'resolution': gamma,
            'num_communities': len(partition),
            'modularity': partition.modularity(),  # Comparable
            'coverage': coverage,  # Comparable
            'performance': performance,  # Comparable
            # Don't compare partition.quality() across resolutions!
        })

    return results

resolutions = [0.01, 0.05, 0.1, 0.5, 1.0]
comparison = compare_resolutions(G, resolutions)

for r in comparison:
    print(f"γ={r['resolution']:5.2f}: "
          f"{r['num_communities']:3d} comms, "
          f"Q={r['modularity']:.3f}, "
          f"cov={r['coverage']:.3f}")
```

---

### Pitfall 7: Not Using Enough Iterations

**Problem**: Stopping optimization too early, missing quality improvements.

**Solution**:
```python
# Monitor improvements
partition = la.CPMVertexPartition(G, resolution_parameter=0.1)
optimiser = la.Optimiser()

improvements = []
for i in range(10):
    improvement = optimiser.optimise_partition(partition, n_iterations=1)
    improvements.append(improvement)

    print(f"Iteration {i+1}: improvement = {improvement:.6f}")

    # Stop if converged
    if improvement < 1e-6:
        print(f"Converged after {i+1} iterations")
        break

    # Warn if still improving significantly
    if i == 9 and improvement > 1e-3:
        print("WARNING: Still improving after 10 iterations. "
              "Consider using more iterations.")
```

---

### Pitfall 8: Misinterpreting Modularity Values

**Problem**: Thinking Q > 0.3 is always "good" without context.

**Solution**:
```python
# Compare against null model
import numpy as np

def modularity_significance(G, partition, n_random=100):
    """
    Compare modularity against random partitions.
    """
    observed_Q = partition.modularity()

    # Generate random partitions with same number of communities
    n_comms = len(partition)
    random_Qs = []

    for _ in range(n_random):
        random_membership = np.random.randint(0, n_comms, G.vcount())
        random_partition = la.CPMVertexPartition(G,
                                                  initial_membership=random_membership,
                                                  resolution_parameter=0.1)
        random_Qs.append(random_partition.modularity())

    mean_random_Q = np.mean(random_Qs)
    std_random_Q = np.std(random_Qs)

    z_score = (observed_Q - mean_random_Q) / std_random_Q

    print(f"Observed Q: {observed_Q:.4f}")
    print(f"Random Q: {mean_random_Q:.4f} ± {std_random_Q:.4f}")
    print(f"Z-score: {z_score:.2f}")

    if z_score > 2:
        print("Community structure is SIGNIFICANT")
    else:
        print("Community structure may not be significant")

    return z_score

partition = la.find_partition(G, la.CPMVertexPartition,
                              resolution_parameter=0.1)

modularity_significance(G, partition)
```

---

## Complete Code Examples

### Example 1: Basic Community Detection Pipeline

```python
import igraph as ig
import leidenalg as la
import matplotlib.pyplot as plt
import numpy as np

# Load graph
G = ig.Graph.Famous('Zachary')

# Add some synthetic weights
np.random.seed(42)
G.es['weight'] = np.random.uniform(0.1, 1.0, G.ecount())

# Preprocess
G.simplify(loops=True, multiple=True, combine_edges='sum')

# Detect communities
partition = la.find_partition(
    G,
    la.CPMVertexPartition,
    weights='weight',
    resolution_parameter=0.1,
    n_iterations=5
)

# Print results
print(f"Found {len(partition)} communities")
print(f"Modularity: {partition.modularity():.4f}")
print(f"Quality: {partition.quality():.4f}")

# Community sizes
sizes = np.bincount(partition.membership)
print(f"Community sizes: {sizes}")

# Visualize
G.vs['community'] = partition.membership
ig.plot(partition,
        bbox=(800, 800),
        vertex_label=range(G.vcount()),
        edge_width=[w*2 for w in G.es['weight']])
plt.savefig('communities.png', dpi=150, bbox_inches='tight')
```

---

### Example 2: Resolution Parameter Scan

```python
import igraph as ig
import leidenalg as la
import matplotlib.pyplot as plt
import numpy as np

# Load network
G = ig.Graph.Erdos_Renyi(n=500, p=0.01)

# Scan resolutions
resolutions = np.logspace(-2, 1, 20)  # 0.01 to 10

results = []
for gamma in resolutions:
    partition = la.find_partition(
        G,
        la.CPMVertexPartition,
        resolution_parameter=gamma,
        n_iterations=3
    )

    results.append({
        'gamma': gamma,
        'num_communities': len(partition),
        'modularity': partition.modularity(),
        'quality': partition.quality()
    })

# Plot results
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

# Number of communities vs resolution
gammas = [r['gamma'] for r in results]
num_comms = [r['num_communities'] for r in results]
ax1.plot(gammas, num_comms, 'o-')
ax1.set_xscale('log')
ax1.set_xlabel('Resolution parameter (γ)')
ax1.set_ylabel('Number of communities')
ax1.set_title('Community Count vs Resolution')
ax1.grid(True, alpha=0.3)

# Modularity vs resolution
modularities = [r['modularity'] for r in results]
ax2.plot(gammas, modularities, 's-', color='green')
ax2.set_xscale('log')
ax2.set_xlabel('Resolution parameter (γ)')
ax2.set_ylabel('Modularity')
ax2.set_title('Modularity vs Resolution')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('resolution_scan.png', dpi=150)
plt.show()

# Find stable plateaus
from sklearn.metrics import normalized_mutual_info_score

partitions = []
for gamma in resolutions:
    p = la.find_partition(G, la.CPMVertexPartition,
                         resolution_parameter=gamma)
    partitions.append(p.membership)

stabilities = []
for i in range(len(partitions)-1):
    nmi = normalized_mutual_info_score(partitions[i], partitions[i+1])
    stabilities.append(nmi)

# Plot stability
plt.figure(figsize=(10, 4))
plt.plot(resolutions[1:], stabilities, 'o-')
plt.axhline(y=0.9, color='r', linestyle='--', label='High stability threshold')
plt.xscale('log')
plt.xlabel('Resolution parameter (γ)')
plt.ylabel('Stability (NMI with next resolution)')
plt.title('Community Detection Stability')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('stability_analysis.png', dpi=150)
plt.show()

# Recommend stable resolutions
stable_indices = [i for i, s in enumerate(stabilities) if s > 0.9]
stable_gammas = [resolutions[i+1] for i in stable_indices]
print(f"\nStable resolution parameters: {stable_gammas}")
```

---

### Example 3: Comparing Multiple Algorithms

```python
import igraph as ig
import leidenalg as la
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import normalized_mutual_info_score

# Create test network with known structure
G = ig.Graph.Erdos_Renyi(n=300, p=0.01)

# Ground truth (if available)
# ground_truth = [...]

# Compare algorithms
algorithms = {
    'Leiden (CPM)': lambda g: la.find_partition(g, la.CPMVertexPartition,
                                                resolution_parameter=0.1),
    'Leiden (Modularity)': lambda g: la.find_partition(g, la.ModularityVertexPartition),
    'Leiden (RB)': lambda g: la.find_partition(g, la.RBConfigurationVertexPartition,
                                               resolution_parameter=1.0),
    'Fast Greedy': lambda g: g.community_fastgreedy().as_clustering(),
    'Infomap': lambda g: g.community_infomap(),
    'Label Propagation': lambda g: g.community_label_propagation(),
}

results = {}
for name, algorithm in algorithms.items():
    import time

    start = time.time()
    partition = algorithm(G)
    runtime = time.time() - start

    # Get membership
    if hasattr(partition, 'membership'):
        membership = partition.membership
        modularity = partition.modularity()
    else:
        membership = partition.membership
        modularity = G.modularity(membership)

    results[name] = {
        'num_communities': len(set(membership)),
        'modularity': modularity,
        'runtime': runtime,
        'membership': membership
    }

# Print comparison
print("\nAlgorithm Comparison")
print("=" * 70)
print(f"{'Algorithm':<25} {'#Comms':>8} {'Modularity':>12} {'Time (s)':>10}")
print("-" * 70)

for name, res in results.items():
    print(f"{name:<25} {res['num_communities']:>8} "
          f"{res['modularity']:>12.4f} {res['runtime']:>10.4f}")

# Compare agreement between algorithms
print("\n\nPairwise NMI (Agreement Between Algorithms)")
print("=" * 70)

names = list(results.keys())
nmi_matrix = np.zeros((len(names), len(names)))

for i, name1 in enumerate(names):
    for j, name2 in enumerate(names):
        if i <= j:
            nmi = normalized_mutual_info_score(
                results[name1]['membership'],
                results[name2]['membership']
            )
            nmi_matrix[i, j] = nmi
            nmi_matrix[j, i] = nmi

# Plot heatmap
plt.figure(figsize=(10, 8))
plt.imshow(nmi_matrix, cmap='viridis', vmin=0, vmax=1)
plt.colorbar(label='NMI')
plt.xticks(range(len(names)), names, rotation=45, ha='right')
plt.yticks(range(len(names)), names)
plt.title('Algorithm Agreement (NMI)')

for i in range(len(names)):
    for j in range(len(names)):
        text = plt.text(j, i, f'{nmi_matrix[i, j]:.2f}',
                       ha='center', va='center', color='white')

plt.tight_layout()
plt.savefig('algorithm_comparison.png', dpi=150)
plt.show()
```

---

### Example 4: Weighted Citation Network

```python
import igraph as ig
import leidenalg as la
import numpy as np
from collections import Counter

# Simulate citation network
np.random.seed(42)
n_papers = 1000

# Create scale-free network (realistic for citations)
G = ig.Graph.Barabasi(n_papers, m=3, directed=True)

# Add paper metadata
G.vs['year'] = np.random.randint(2010, 2024, n_papers)
G.vs['citations'] = [v.indegree() for v in G.vs]

# Weight edges by citation importance
# More recent citations get higher weight
for edge in G.es:
    source_year = G.vs[edge.source]['year']
    target_year = G.vs[edge.target]['year']

    # Citation must go forward in time
    if source_year > target_year:
        age = source_year - target_year
        edge['weight'] = 1.0 / (1.0 + 0.1 * age)  # Decay with age
    else:
        edge['weight'] = 0.1  # Small weight for temporal anomalies

# Make undirected for community detection
G_undirected = G.as_undirected(mode='collapse', combine_edges='sum')

# Detect research communities
partition = la.find_partition(
    G_undirected,
    la.CPMVertexPartition,
    weights='weight',
    resolution_parameter=0.05,  # Larger communities for research areas
    n_iterations=5
)

print(f"\nCitation Network Analysis")
print("=" * 70)
print(f"Papers: {n_papers}")
print(f"Citations: {G.ecount()}")
print(f"Research communities: {len(partition)}")
print(f"Modularity: {partition.modularity():.4f}")

# Analyze communities
G_undirected.vs['community'] = partition.membership

community_stats = []
for comm_id in range(len(partition)):
    comm_nodes = [i for i, c in enumerate(partition.membership) if c == comm_id]

    # Stats for this community
    years = [G_undirected.vs[i]['year'] for i in comm_nodes]
    citations = [G_undirected.vs[i]['citations'] for i in comm_nodes]

    community_stats.append({
        'community': comm_id,
        'size': len(comm_nodes),
        'avg_year': np.mean(years),
        'total_citations': sum(citations),
        'avg_citations': np.mean(citations)
    })

# Sort by size
community_stats.sort(key=lambda x: x['size'], reverse=True)

print(f"\nTop Research Communities:")
print("-" * 70)
print(f"{'Comm':>5} {'Size':>6} {'Avg Year':>10} {'Total Cites':>12} {'Avg Cites':>10}")
print("-" * 70)

for stat in community_stats[:10]:
    print(f"{stat['community']:>5} {stat['size']:>6} "
          f"{stat['avg_year']:>10.1f} {stat['total_citations']:>12} "
          f"{stat['avg_citations']:>10.1f}")

# Save network with communities
G_undirected.write_graphml('citation_network_communities.graphml')
print(f"\nSaved: citation_network_communities.graphml")
```

---

### Example 5: Temporal Evolution of Communities

```python
import igraph as ig
import leidenalg as la
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import normalized_mutual_info_score

# Simulate evolving network
np.random.seed(42)
n_nodes = 200
n_timesteps = 10

# Generate time slices
networks = []
for t in range(n_timesteps):
    # Network evolves over time
    # Start with strong community structure, gradually mix
    p_within = 0.15 - 0.01 * t  # Decreasing internal density
    p_between = 0.01 + 0.005 * t  # Increasing external density

    # Create 4 initial communities
    sizes = [50, 50, 50, 50]
    prefs = np.full((4, 4), p_between)
    np.fill_diagonal(prefs, p_within)

    G_t = ig.Graph.SBM(n_nodes, prefs, sizes)
    G_t.vs['time'] = t
    networks.append(G_t)

# Detect communities at each time step
partitions = []
qualities = []

for t, G in enumerate(networks):
    partition = la.find_partition(
        G,
        la.CPMVertexPartition,
        resolution_parameter=0.1,
        n_iterations=3
    )
    partitions.append(partition)
    qualities.append(partition.quality())

    print(f"Time {t}: {len(partition)} communities, Q={partition.modularity():.3f}")

# Analyze temporal stability
stabilities = []
for t in range(len(partitions) - 1):
    nmi = normalized_mutual_info_score(
        partitions[t].membership,
        partitions[t+1].membership
    )
    stabilities.append(nmi)

# Visualize evolution
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Number of communities over time
num_comms = [len(p) for p in partitions]
ax1.plot(range(n_timesteps), num_comms, 'o-', linewidth=2, markersize=8)
ax1.set_xlabel('Time')
ax1.set_ylabel('Number of Communities')
ax1.set_title('Community Count Over Time')
ax1.grid(True, alpha=0.3)

# Stability over time
ax2.plot(range(1, n_timesteps), stabilities, 's-', linewidth=2,
         markersize=8, color='orange')
ax2.axhline(y=0.8, color='r', linestyle='--', label='Stability threshold')
ax2.set_xlabel('Time')
ax2.set_ylabel('Stability (NMI with previous time)')
ax2.set_title('Community Stability Over Time')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('temporal_evolution.png', dpi=150)
plt.show()

# Track individual communities
# Build community correspondence across time
print("\n\nCommunity Tracking:")
print("=" * 70)

# Use maximum overlap to track communities
for t in range(len(partitions) - 1):
    curr_partition = partitions[t].membership
    next_partition = partitions[t+1].membership

    # Build contingency table
    from sklearn.metrics.cluster import contingency_matrix
    contingency = contingency_matrix(curr_partition, next_partition)

    # Find best matches
    print(f"\nTime {t} → {t+1}:")
    for comm_t in range(contingency.shape[0]):
        if contingency[comm_t].sum() == 0:
            continue
        best_match = contingency[comm_t].argmax()
        overlap = contingency[comm_t, best_match]
        size_t = contingency[comm_t].sum()

        print(f"  Community {comm_t} (size {size_t}) → "
              f"Community {best_match} ({overlap}/{size_t} nodes retained)")
```

---

### Example 6: Integration with NetworkX (Current Codebase)

```python
import networkx as nx
import igraph as ig
import leidenalg as la
import numpy as np

# Load from existing NetworkX graph (from your codebase)
# Assume you have GraphDatabase instance

from research_agent.graph_database import GraphDatabase

# Create sample data
db = GraphDatabase()

# Add some papers and claims
paper1 = db.create_node('Document', {'title': 'Paper 1', 'text': 'Content 1'})
paper2 = db.create_node('Document', {'title': 'Paper 2', 'text': 'Content 2'})
paper3 = db.create_node('Document', {'title': 'Paper 3', 'text': 'Content 3'})

claim1 = db.create_node('Claim', {'text': 'Claim A', 'confidence': 0.9})
claim2 = db.create_node('Claim', {'text': 'Claim B', 'confidence': 0.8})
claim3 = db.create_node('Claim', {'text': 'Claim C', 'confidence': 0.85})
claim4 = db.create_node('Claim', {'text': 'Claim D', 'confidence': 0.75})

# Add relationships
db.create_relationship(paper1, claim1, 'CONTAINS')
db.create_relationship(paper1, claim2, 'CONTAINS')
db.create_relationship(paper2, claim2, 'CONTAINS')
db.create_relationship(paper2, claim3, 'CONTAINS')
db.create_relationship(paper3, claim4, 'CONTAINS')

# Add similarity relationships
db.create_relationship(claim1, claim2, 'SIMILAR_TO', {'score': 0.85})
db.create_relationship(claim2, claim3, 'SIMILAR_TO', {'score': 0.78})
db.create_relationship(claim1, claim3, 'SIMILAR_TO', {'score': 0.65})

# Convert NetworkX to igraph
def networkx_to_igraph(nx_graph, weight_attr='score'):
    """
    Convert NetworkX graph to igraph for Leiden algorithm.
    """
    # Create mapping from node IDs to indices
    nodes = list(nx_graph.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(nodes)}

    # Create igraph
    G_ig = ig.Graph(directed=nx_graph.is_directed())
    G_ig.add_vertices(len(nodes))

    # Add node attributes
    for idx, node in enumerate(nodes):
        for attr, value in nx_graph.nodes[node].items():
            # Skip non-serializable attributes
            if isinstance(value, (str, int, float, bool)):
                G_ig.vs[idx][attr] = value

    # Add edges
    edges = []
    weights = []

    for u, v, data in nx_graph.edges(data=True):
        edges.append((node_to_idx[u], node_to_idx[v]))

        # Get weight from specified attribute
        if weight_attr in data:
            weights.append(float(data[weight_attr]))
        else:
            weights.append(1.0)

    G_ig.add_edges(edges)
    if weights:
        G_ig.es['weight'] = weights

    # Store original node IDs for reverse mapping
    G_ig.vs['original_id'] = nodes

    return G_ig, node_to_idx

# Convert claim similarity network
similarity_graph = nx.Graph()
for u, v, data in db.graph.edges(data=True):
    if data.get('type') == 'SIMILAR_TO':
        similarity_graph.add_edge(u, v, score=data.get('score', 0.0))

print(f"Claim similarity network: {similarity_graph.number_of_nodes()} nodes, "
      f"{similarity_graph.number_of_edges()} edges")

# Convert to igraph
G_ig, node_mapping = networkx_to_igraph(similarity_graph, weight_attr='score')

# Detect communities
partition = la.find_partition(
    G_ig,
    la.CPMVertexPartition,
    weights='weight',
    resolution_parameter=0.3,
    n_iterations=5
)

print(f"\nFound {len(partition)} claim clusters")
print(f"Modularity: {partition.modularity():.4f}")

# Map back to original node IDs
original_ids = G_ig.vs['original_id']
community_mapping = {
    original_ids[i]: community
    for i, community in enumerate(partition.membership)
}

# Create super-claims for each community
for comm_id in range(len(partition)):
    # Get claims in this community
    claim_ids = [node_id for node_id, comm in community_mapping.items()
                 if comm == comm_id]

    if len(claim_ids) > 1:
        # Get claim texts
        claim_texts = [db.get_node(cid)['text'] for cid in claim_ids]

        # Simple normalization (in practice, use better method)
        normalized_text = f"Merged claim from {len(claim_ids)} sources"

        # Create super-claim
        super_claim_id = db.create_super_claim(
            claim_ids,
            normalized_text,
            confidence=0.9
        )

        print(f"\nCommunity {comm_id}:")
        print(f"  Claims: {claim_texts}")
        print(f"  Super-claim: {normalized_text}")

# Add community labels to original graph
nx.set_node_attributes(
    db.graph,
    {k: v for k, v in community_mapping.items() if k in db.graph},
    'community'
)

print(f"\nDatabase stats: {db.stats()}")
```

---

## Summary and Recommendations

### Quick Start Checklist

1. **Install libraries**:
   ```bash
   pip install igraph leidenalg
   ```

2. **Basic usage**:
   ```python
   import igraph as ig
   import leidenalg as la

   partition = la.find_partition(G, la.CPMVertexPartition,
                                 resolution_parameter=0.1)
   ```

3. **Choose quality function**:
   - **CPM**: Best default choice (supports negative weights, intuitive resolution)
   - **RBConfiguration**: Alternative with linear resolution
   - **Modularity**: Simple, no parameters, but has resolution limit

4. **Tune resolution parameter**:
   - Start with network density as initial guess
   - Scan multiple values: [0.01, 0.05, 0.1, 0.5, 1.0]
   - Look for stable plateaus
   - Choose based on domain knowledge and quality metrics

5. **Evaluate results**:
   - Check modularity (Q > 0.3 is good guideline)
   - Verify communities are connected
   - Test stability across multiple runs
   - Compare with other algorithms

### Best Practices Summary

1. Always preprocess graphs (remove self-loops, normalize weights)
2. Use CPM for most applications (best flexibility)
3. Scan multiple resolutions, don't rely on single value
4. Verify community connectivity
5. Use n_iterations ≥ 2 (default is good)
6. Compare with baseline algorithms
7. Evaluate with multiple metrics
8. Test stability with different random seeds

### When to Use Leiden

✓ **Always** as first choice over Louvain
✓ Need guaranteed well-connected communities
✓ Working with weighted or directed graphs
✓ Need control over community size via resolution
✓ Have negative edge weights (use CPM)
✓ Want theoretically-grounded results
✓ Networks up to millions of edges

### Performance Expectations

- **Small** (<1K nodes): Near instant
- **Medium** (1K-100K nodes): Seconds to minutes
- **Large** (100K-1M nodes): Minutes
- **Very large** (>1M nodes): Tens of minutes, consider parallel implementation

---

## References

### Key Papers

1. **Traag, V. A., Waltman, L., & van Eck, N. J. (2019)**. "From Louvain to Leiden: guaranteeing well-connected communities." *Scientific Reports*, 9(1), 5233.
   - Original Leiden paper
   - DOI: 10.1038/s41598-019-41695-z

2. **Newman, M. E., & Girvan, M. (2004)**. "Finding and evaluating community structure in networks." *Physical Review E*, 69(2), 026113.
   - Modularity definition

3. **Reichardt, J., & Bornholdt, S. (2006)**. "Statistical mechanics of community detection." *Physical Review E*, 74(1), 016110.
   - Potts model for community detection

4. **Fortunato, S., & Barthélemy, M. (2007)**. "Resolution limit in community detection." *PNAS*, 104(1), 36-41.
   - Resolution limit problem

### Software Documentation

- **leidenalg**: https://leidenalg.readthedocs.io/
- **python-igraph**: https://igraph.org/python/
- **GitHub repository**: https://github.com/vtraag/leidenalg

### Further Reading

- Community detection survey: Fortunato, S. (2010). "Community detection in graphs." *Physics Reports*, 486(3-5), 75-174.
- Network science textbook: Barabási, A. L. (2016). *Network Science*. Cambridge University Press.

---

**Document prepared for Research Assistant Tool project**
**Date**: 2025-11-20
**Based on comprehensive literature review and official documentation**
