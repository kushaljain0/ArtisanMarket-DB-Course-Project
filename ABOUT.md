## Design Decisions & Architecture

### 1. Polyglot Persistence Strategy

**Why Multiple Databases?**
"Instead of using a single database for everything, I chose a polyglot persistence approach where each database technology is selected based on its strengths:"

- **PostgreSQL**: Primary transactional database for core business entities (users, products, orders)
  - ACID compliance for critical operations
  - Foreign key constraints for data integrity
  - pgvector extension for semantic search capabilities

- **MongoDB**: Document store for flexible, schema-variable content
  - Product reviews with nested comments
  - Variable product specifications by category
  - Rich seller profiles with portfolio items

- **Redis**: High-performance caching and session management
  - Shopping cart sessions with TTL
  - Search result caching
  - Rate limiting and hot products lists

- **Neo4j**: Graph database for relationship-based data
  - Purchase history and user behavior patterns
  - Product recommendations and "frequently bought together"
  - Complex relationship queries

### 2. Data Modeling Decisions

**PostgreSQL Schema Design:**
```sql
-- Core entities with proper relationships
users (id, name, email, join_date)
sellers (id, name, rating, user_id)
categories (id, name, description)
products (id, name, description, price, category_id, seller_id, stock)
orders (id, user_id, total_amount, status, order_date)
order_items (order_id, product_id, quantity, unit_price, total_price)
product_embeddings (product_id, description_embedding)
```

**MongoDB Document Structure:**
```javascript
// Flexible schema for reviews
{
  product_id: "P001",
  user_id: "U001", 
  rating: 5,
  title: "Amazing quality!",
  content: "Detailed review...",
  images: ["url1", "url2"],
  comments: [
    { user_id: "U002", content: "I agree!", created_at: ISODate() }
  ]
}
```

**Neo4j Graph Model:**
```
(User)-[:PURCHASED {quantity, date}]->(Product)
(Product)-[:BELONGS_TO]->(Category)
(User)-[:VIEWED {timestamp}]->(Product)
(Product)-[:SIMILAR_TO {score}]->(Product)
```

### 3. Technology Stack & Development Practices

**Modern Python Development:**
- **uv** for dependency management (faster than pip)
- **Rich** for beautiful CLI output
- **Pydantic** for data validation
- **Structlog** for structured logging
- **Tenacity** for retry logic and resilience

**Code Organization:**
```
src/
├── db/           # Database connection modules
├── loaders/      # Data loading scripts  
├── services/     # Business logic services
└── utils/        # Helper utilities
```

## Features Walkthrough (8 minutes)

### 1. Data Loading & Setup

**Show the CLI interface:**
```bash
# Start databases
docker-compose up -d

# Load all data
uv run python -m src.cli load all
```

**Explain the loading process:**
- CSV files parsed and loaded into appropriate databases
- Proper indexes created for performance
- Data integrity maintained across systems
- Error handling and logging throughout

### 2. Search Functionality

**Demonstrate three types of search:**

**Full-text Search:**
```bash
uv run python -m src.cli search text "wooden bowl"
```
- Uses PostgreSQL's ILIKE for pattern matching
- Searches across name, description, and tags
- Results cached in Redis for performance

**Semantic Search:**
```bash
uv run python -m src.cli search semantic "eco-friendly kitchenware"
```
- Uses sentence-transformers (all-MiniLM-L6-v2)
- 384-dimensional vector embeddings stored in pgvector
- Finds conceptually similar products, not just keyword matches

**Combined Search:**
```bash
uv run python -m src.cli search combined "handmade jewelry"
```
- Merges results from both search types
- Intelligent scoring and ranking
- Best of both worlds approach

### 3. Shopping Cart Management

**Redis-based cart with TTL:**
```bash
# Add items to cart
uv run python -m src.cli cart add U001 P001 --quantity 2
uv run python -m src.cli cart add U001 P003 --quantity 1

# View cart
uv run python -m src.cli cart show-cart U001
```

**Key Features:**
- Hash-based storage in Redis with 24-hour TTL
- Stock verification before adding items
- Automatic cart expiration
- Integration with PostgreSQL for product details

### 4. Recommendation System

**Graph-based recommendations using Neo4j:**

**Personalized Recommendations:**
```bash
uv run python -m src.cli recommend user U001 --limit 5
```
- Analyzes purchase patterns
- "Users who bought this also bought" algorithm
- Collaborative filtering approach

**Similar Products:**
```bash
uv run python -m src.cli recommend similar P001 --limit 5
```
- Uses semantic similarity from vector embeddings
- Content-based filtering

**Frequently Bought Together:**
```bash
uv run python -m src.cli recommend frequently-bought-together P001 --limit 5
```
- Graph traversal to find co-purchase patterns
- Market basket analysis

### 5. Order Management

**Complete order lifecycle:**
```bash
# View order history
uv run python -m src.cli orders history U001

# Create order from cart
uv run python -m src.cli cart convert-to-order U001

# View order details
uv run python -m src.cli orders show 1
```

**Features:**
- Transactional order creation in PostgreSQL
- Stock management and updates
- Purchase history added to Neo4j for recommendations
- Order status tracking