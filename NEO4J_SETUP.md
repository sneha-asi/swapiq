# Running SwapIQ on Neo4j

SwapIQ has a real Neo4j runtime backend. When it is selected, safety filtering,
swap weights, graph visualization, recall propagation and graph metrics query
Neo4j. NetworkX remains an explicit zero-infrastructure fallback.

You need a running Neo4j 5.x instance (5.26 LTS is what the app was tested
with). Either option below works.

## Step 1: Start Neo4j

**Option A: Docker**

```bash
docker run --name swapiq-neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/<choose-a-password> neo4j:5.26
```

**Option B: Neo4j Desktop**

Install [Neo4j Desktop](https://neo4j.com/download/), create a local database
on version 5.x, set a password and start it.

When the database is up:
- Browser UI: http://localhost:7474  (login `neo4j` / the password you chose)
- Bolt endpoint: `bolt://localhost:7687`

## Step 2: Set the connection variables

The loader and the API read these environment variables (bash shown; in
PowerShell use `$env:NAME = "value"`):

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="<your-password>"
export NEO4J_DATABASE="neo4j"
```

## Step 3: Load the SwapIQ catalog

From the repository root, in the same shell:

```bash
pip install -r requirements.txt
python neo4j_loader.py --demo
```

Expected output:

```
Loaded: 508 products, 624 total nodes, 14010 relationships

Safe substitutes for a nut-allergic vegan shopper (almond milk out of stock):
  SAFE  ... Oat Milk ...
  SAFE  ... Soy Milk ...
What the graph blocks (nut-containing plant milks it will never offer):
  BLOCK ... Cashew Milk ...
  BLOCK ... Almond Milk ...
```

## Step 4: Run the API on Neo4j

In the same shell:

```bash
export SWAPIQ_GRAPH_BACKEND="neo4j"
uvicorn api.index:app --reload --port 8000
```

Verify the runtime rather than relying on configuration alone:

```bash
curl http://localhost:8000/api/health
```

The response must contain `"backend": "neo4j"`, `"persistent": true` and
`"connected": true`. Required Neo4j mode fails startup if the database is
unavailable or empty; it never silently drops to NetworkX.

## Step 5: See it in the Neo4j Browser

Open http://localhost:7474 and run the safety traversal in Cypher. This is the
exact logic from `graph_core.py`, now in the database:

```cypher
// Safe plant-milk swaps for a nut-allergic vegan when almond milk is out
MATCH (oos:Product {id: 'P001'})-[:IN_CATEGORY]->(cat)
MATCH (cand:Product)-[:IN_CATEGORY]->(cat)
WHERE cand.id <> oos.id
  AND (cand)-[:HAS_TAG]->(:DietTag {name: 'vegan'})
  AND NOT EXISTS {
        MATCH (cand)-[:CONTAINS]->(:Ingredient)-[:IS_A]->(a:Allergen)
        WHERE a.name IN ['tree_nuts', 'peanuts']
  }
RETURN cand.name, cand.price ORDER BY cand.price;
```

```cypher
// Visualise almond milk, its ingredients, and the allergen it carries
MATCH path = (p:Product {id:'P001'})-[:CONTAINS]->(:Ingredient)-[:IS_A]->(:Allergen)
RETURN path;
```

## Backend selection

- `SWAPIQ_GRAPH_BACKEND=neo4j`: require Neo4j and fail fast if unavailable.
- `SWAPIQ_GRAPH_BACKEND=auto`: use Neo4j when `NEO4J_URI` is configured; otherwise use NetworkX.
- `SWAPIQ_GRAPH_BACKEND=networkx`: force the offline fallback.
- `NEO4J_AUTO_SYNC=true`: idempotently upsert the deterministic demo graph at API startup. Prefer running `neo4j_loader.py` separately for hosted deployments.

For Neo4j Aura, replace the URI, username and password with the Aura credentials
and configure the same variables in the hosting provider. Do not commit database
credentials to Git.
