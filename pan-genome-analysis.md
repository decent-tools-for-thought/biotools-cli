# Pan-Genome Analysis Tools

Sources:
- bio.tools registry (queried via local `biotools` CLI for pangenome, pan-genome, metabolic modeling, and known-tool lookups)
- Tool READMEs and documentation where needed

Note: some full-text searches to `bio.tools` API returned server-side HTTP 500 errors; relevant tools were mainly recovered via targeted by-name lookups.


## 1. Core Pan-Genome Construction Tools

### Roary

- Description: High-speed standalone pan-genome pipeline, focused on prokaryotes.
  - Input: annotated assemblies in GFF3 format (commonly Prokka output).
  - Output: pan-genome summary, gene presence/absence matrix.
  - Status: classic, widely used.
  - Language: Perl.
  - Registry: https://bio.tools/roary
  - Code: https://sanger-pathogens.github.io/Roary/

### Panaroo

- Description: “Producing Polished Prokaryotic Pangenomes”; modern pangenome pipeline.
  - Improvement over older tools in quality/handling of assembly/annotation issues.
  - Status: strong modern default.
  - Language: Python.
  - Registry: https://bio.tools/panaroo
  - Code: https://github.com/gtonkinhill/panaroo

### PPanGGOLiN

- Description: Software suite to create and manipulate prokaryotic pangenomes using a statistical partitioning approach.
  - Nodes = gene families; edges = genetic contiguity.
  - Partitions gene families into persistent, shell, and cloud.
  - Scales to tens of thousands of genomes; designed for low-quality data (MAGs, SAGs).
  - Native graph model central to its design.
  - Outputs:
    - Partitioned pan-genome graph (PPG)
    - HDF5 pangenome file (`pangenome.h5`)
  - Registry: https://bio.tools/PPanGGOLiN
  - Code: https://github.com/labgem/PPanGGOLiN
  - Docs: https://ppanggolin.readthedocs.io

### PIRATE

- Description: Pangenomics toolbox for clustering diverged orthologues in bacteria.
  - Good for when orthologue divergence makes simple thresholds unreliable.
  - Language: Perl.
  - Registry: https://bio.tools/PIRATE
  - Code: https://github.com/SionBayliss/PIRATE

### Panakeia

- Description: Graph-based prokaryotic pangenome analysis.
  - Builds a complete pangenome graph; detects insertions, deletions, rearrangements, and variants.
  - Often paired with Pantagruel for evolutionary history.
  - Language: Python.
  - Registry: https://bio.tools/panakeia
  - Code: https://github.com/BioSina/Panakeia

### PATO

- Description: R package for pangenome analysis (intra- or inter-species).
  - Includes core/accessory/whole-genome analyses, population structure, HGT dynamics.
  - Registry: https://bio.tools/pato
  - Code: https://github.com/irycisBioinfo/PATO

### Pagoo

- Description: R package for evolutionary pangenome analysis.
  - Object-oriented framework; designed for post-processing, subsetting, visualization, and statistical analysis.
  - Good for organizing pangenome data within R before further export or graph integration.
  - Registry: https://bio.tools/pagoo
  - Code: https://github.com/iferres/pagoo

### PanACEA

- Description: Exploration and visualization of bacterial pan-chromosomes.
  - Focus: interactive pan-chromosome visualization of core and variable regions.
  - Registry: https://bio.tools/panacea
  - Code: https://github.com/JCVenterInstitute/PanACEA


## 2. Downstream Analysis, Visualization, and Association

### Scoary

- Description: Pan-genome-wide association studies (pan-GWAS).
  - Input: gene presence/absence from pangenome tools (e.g., Roary) + traits.
  - Output: pan-genome associations per trait.
  - Registry: https://bio.tools/scoary
  - Code: https://github.com/AdmiralenOla/Scoary


## 3. Pan-Genome and Metabolic Modeling / Integrated Platforms

### MicroScope_platform

- Description: Integrated genomic, pangenomic, and metabolic comparative analysis.
  - Includes metabolic pathway prediction, metabolic network modelling, annotation, and pangenomic graph-based comparative tools.
  - Registry: https://bio.tools/microscope_platform
  - Web: https://www.genoscope.cns.fr/agc/microscope

### metagem

- Description: Metagenomic workflow for pangenome analysis and genome-scale metabolic model reconstruction.
  - Focus: microbial communities, MAGs, and community-level metabolism.
  - Registry: https://bio.tools/metagem


## 4. Graph-Centric Pan-Genome Concepts

### What it means

- Pan-genome is represented as a graph rather than a single reference or a flat presence/absence matrix.
- Nodes: sequence segments, genes, or genomic blocks.
- Edges: adjacency, continuity, or alternative paths.
- Each genome corresponds to a path through the graph.

### Why it matters

- Preserves genome architecture: synteny, rearrangements, variable neighborhoods.
- Encodes structural variation and multiple alternative genomic paths across strains.

### Typical implementations

- Gene-family graphs (nodes = gene families).
- Sequence graphs (nodes = sequence blocks).
- Pan-chromosome graphs (structural focus).

### Tradeoffs

- More expressive biologically.
- Harder to build, visualize, and analyze than simple presence/absence pangenomes.


## 5. Neo4j Suitability

### Best near-direct fits

#### PPanGGOLiN

- Explicit graph model: gene-family nodes with contiguity edges.
- Built-in useful layers:
  - Partitions: persistent, shell, cloud.
  - Regions of Genome Plasticity (RGPs).
  - Insertion spots.
  - Modules.
- Native graph output; highly suitable for Neo4j.

#### Panakeia

- Graph-based pangenome with graph algorithms for insertions, deletions, rearrangements, variants.
- Good fit for structural/event-oriented graph data.

#### PanACEA

- Pan-chromosome focus with interactive visualization.
- Less general than PPanGGOLiN, but conceptually clean for graph import.

### Usable with more work

#### Panaroo

- Strong pangenome builder, but not obviously graph-native.
- Self-interpretation of outputs needed for Neo4j schema design.

#### Pagoo

- Powerful post-processing framework in R.
- Good for organizing and enriching before export; not a native graph pangenome constructor.

#### PATO, Roary, PIRATE

- Useful downstream or clustering tools.
- Can be imported into Neo4j, but schema design is user-driven.

### Example Neo4j schema sketch

Based on PPanGGOLiN structure:

- Nodes:
  - `(:Genome)`
  - `(:GeneFamily)`
  - `(:Gene)`
  - `(:Region)`
  - `(:Module)`
  - `(:Partition {name: persistent|shell|cloud})`

- Relationships:
  - `(:Genome)-[:CONTAINS]->(:Gene)`
  - `(:Gene)-[:BELONGS_TO]->(:GeneFamily)`
  - `(:GeneFamily)-[:NEIGHBOR_OF]->(:GeneFamily)`
  - `(:GeneFamily)-[:IN_PARTITION]->(:Partition)`
  - `(:Region)-[:CONTAINS_FAMILY]->(:GeneFamily)`
  - `(:Region)-[:IN_GENOME]->(:Genome)`
  - `(:Module)-[:CONTAINS_FAMILY]->(:GeneFamily)`


## 6. Practical Shortlists

### To build a pangenome

- `panaroo`
- `PPanGGOLiN`
- `PIRATE`
- `roary`

### To explore and analyze pangenome structure

- `Panakeia`
- `Pagoo`
- `PATO`
- `PanACEA`

### To associate pangenome with phenotype

- `Scoary`

### For pangenome plus metabolism

- `MicroScope_platform`
- `metagem` (metagenomics/MAGs / community metabolism)

### For direct Neo4j integration

1. `PPanGGOLiN`
2. `Panakeia`
3. `PanACEA`
4. `Panaroo` (with more interpretation)
5. `Roary` (with schema design)


## 7. Notes on Registry Coverage

- Dedicated pangenome analysis tools: well represented.
- Dedicated pan-genome metabolic modeling: sparsely represented; usually embedded in broader integrated platforms.
- Some broad pangenome queries hit `bio.tools` 500 errors; narrower targeted lookups recovered key tools.