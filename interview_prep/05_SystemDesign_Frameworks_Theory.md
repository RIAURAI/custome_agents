# 🏗️ System Design & Python Frameworks - Theory Guide (10 Years Experience)

---

## 📌 Table of Contents
1. [Python Frameworks (Django, Flask, FastAPI)](#1-python-frameworks)
2. [Databases & ORMs](#2-databases--orms)
3. [System Design Fundamentals](#3-system-design-fundamentals)
4. [API Design](#4-api-design)
5. [Caching, Queues & Messaging](#5-caching-queues--messaging)
6. [DevOps & Cloud Basics](#6-devops--cloud-basics)
7. [Python Libraries for Data Science](#7-python-libraries-for-data-science)
8. [Interview Questions & Answers](#8-interview-questions--answers)

---

## 1. Python Frameworks

### 1.1 Django vs Flask vs FastAPI

| Feature | Django | Flask | FastAPI |
|---------|--------|-------|---------|
| Type | Full-stack (batteries included) | Micro framework | Modern async API framework |
| ORM | Built-in (Django ORM) | No (use SQLAlchemy) | No (use SQLAlchemy) |
| Admin Panel | Built-in | No | No |
| Authentication | Built-in | Extensions | Manual / third-party |
| Async Support | Django 4.1+ (partial) | No (not natively) | Full async (built on Starlette) |
| Speed | Medium | Medium | Very Fast (async, Pydantic) |
| Learning Curve | High | Low | Medium |
| Best For | Large web apps, CMS, e-commerce | Small apps, microservices | APIs, ML model serving |
| Used By | Instagram, Pinterest, Mozilla | Netflix, LinkedIn, Reddit | Microsoft, Uber, Netflix |

### 1.2 Django Architecture

**MVT Pattern (Model-View-Template):**
- **Model:** Database structure define (ORM)
- **View:** Business logic + request handling (similar to Controller)
- **Template:** HTML rendering

**Request Flow:**
```
User Request → URL Router → View → (Model/DB) → Template → Response
```

**Key Components:**
- **settings.py:** Configuration (DB, apps, middleware, etc.)
- **urls.py:** URL routing
- **models.py:** Database models (ORM)
- **views.py:** Request handling logic
- **serializers.py:** Data serialization (DRF)
- **admin.py:** Auto admin interface
- **middleware:** Request/Response processing pipeline

**Django REST Framework (DRF):**
- Django ke liye REST API building toolkit
- Serializers: Model ↔ JSON conversion
- ViewSets: CRUD operations automatically
- Authentication: Token, JWT, Session, OAuth
- Permissions: IsAuthenticated, IsAdminUser, custom
- Pagination, Filtering, Throttling built-in

### 1.3 Flask Architecture

- Minimalist — sirf core features (routing, request handling)
- Extensions se features add karo: Flask-SQLAlchemy, Flask-Login, Flask-RESTful
- Blueprints: App ko modules mein organize karo
- Jinja2 templating engine
- WSGI based

### 1.4 FastAPI Architecture

- Built on Starlette (async) + Pydantic (validation)
- Automatic API documentation (Swagger/OpenAPI)
- Type hints se automatic validation
- Dependency Injection system
- WebSocket support
- Background tasks
- ASGI based (async)

**FastAPI vs Flask for ML Model Serving:**
- FastAPI: Async support → multiple requests simultaneously handle
- Automatic input validation (Pydantic)
- Auto-generated docs → easy testing
- 2-3x faster than Flask for I/O-bound tasks
- Better for production ML APIs

### 1.5 WSGI vs ASGI
- **WSGI (Web Server Gateway Interface):** Synchronous — ek request at a time process. Django (old), Flask.
- **ASGI (Asynchronous Server Gateway Interface):** Async — multiple requests concurrently. FastAPI, Django 4+.
- ASGI better for: WebSockets, long-polling, real-time apps, high-concurrency APIs

---

## 2. Databases & ORMs

### 2.1 SQL vs NoSQL

| Feature | SQL (Relational) | NoSQL |
|---------|------------------|-------|
| Structure | Fixed schema, tables, rows | Flexible schema (document, key-value, graph, column) |
| Scaling | Vertical (scale up) | Horizontal (scale out) |
| ACID | Full support | Eventual consistency (BASE) |
| Joins | Supported | Limited/none |
| Best For | Complex queries, transactions | Large scale, flexible data, high throughput |
| Examples | PostgreSQL, MySQL, SQLite | MongoDB, Redis, Cassandra, DynamoDB |

### 2.2 ACID Properties
- **Atomicity:** Transaction pura complete ho ya bilkul nahi (all or nothing)
- **Consistency:** Transaction ke baad data valid state mein rahe
- **Isolation:** Concurrent transactions ek dusre ko affect na karein
- **Durability:** Committed data permanently save rahe (even after crash)

### 2.3 CAP Theorem
- **Consistency:** Sabhi nodes pe same data ek time pe
- **Availability:** Har request ka response milta hai
- **Partition Tolerance:** Network partition hone pe bhi system kaam kare

**Rule:** Distributed system mein teeno ek saath nahi mil sakte — pick 2:
- **CP:** MongoDB, Redis — consistent but may be unavailable during partition
- **AP:** Cassandra, DynamoDB — available but eventually consistent
- **CA:** Traditional RDBMS (single node) — no partition tolerance

### 2.4 Database Indexing
- Index = data structure jo lookups fast kare (B-Tree, Hash, etc.)
- Without index: Full table scan (O(n))
- With index: O(log n) typically
- **Tradeoff:** Faster reads, slower writes (index bhi update karna padta hai), extra storage
- **Composite Index:** Multiple columns pe index
- **Covering Index:** Query ke sab columns index mein — table access nahi chahiye
- **Over-indexing:** Too many indexes → slow writes, wasted space

### 2.5 Database Normalization
- **1NF:** No repeating groups, atomic values
- **2NF:** 1NF + no partial dependencies (non-key columns fully depend on primary key)
- **3NF:** 2NF + no transitive dependencies
- **Denormalization:** Performance ke liye intentionally redundancy add karna (read-heavy systems mein)

### 2.6 ORM (Object-Relational Mapping)
- Database tables ko Python objects ke through access karo
- SQL likhne ki zaroorat kam
- **Django ORM:** Powerful, built-in, migration system
- **SQLAlchemy:** Most popular Python ORM, flexible, Flask/FastAPI ke saath
- **N+1 Problem:** Related objects ke liye extra queries — select_related/prefetch_related se solve

---

## 3. System Design Fundamentals

### 3.1 Scalability

**Vertical Scaling (Scale Up):**
- Bigger/powerful machine (more RAM, CPU, SSD)
- Simple but limited by hardware
- Single point of failure

**Horizontal Scaling (Scale Out):**
- Multiple machines add karo
- Load balancer distribute kare
- Complex but unlimited scalability
- Need: Stateless servers, distributed data

### 3.2 Load Balancing

**Algorithms:**
- **Round Robin:** Sequentially distribute
- **Weighted Round Robin:** High-capacity servers ko zyada requests
- **Least Connections:** Sabse kam busy server ko bhejo
- **IP Hash:** Same user same server pe
- **Random:** Randomly distribute

**Types:**
- **L4 (Transport):** TCP/UDP level pe route (faster)
- **L7 (Application):** HTTP level pe route (smarter, can inspect content)

**Tools:** Nginx, HAProxy, AWS ALB/ELB, Cloudflare

### 3.3 Caching Strategies

**Where to Cache:**
- **Client-side:** Browser cache, CDN
- **Application-level:** In-memory (Redis, Memcached)
- **Database-level:** Query cache
- **CDN:** Static assets globally distributed

**Caching Patterns:**
- **Cache-Aside (Lazy Loading):** App checks cache → miss → read DB → write cache. Most common.
- **Write-Through:** Write DB + cache simultaneously. Consistent but slow writes.
- **Write-Behind:** Write cache first, async write to DB. Fast writes, risk of data loss.
- **Read-Through:** Cache reads from DB on miss. Cache manages DB access.

**Cache Eviction Policies:**
- **LRU (Least Recently Used):** Sabse purana used item remove — most popular
- **LFU (Least Frequently Used):** Sabse kam used item remove
- **TTL (Time-To-Live):** Time expire hone pe remove
- **FIFO:** First in, first out

**Cache Invalidation — "The hardest problem in CS":**
- TTL-based: Auto expire
- Event-based: Data change pe cache clear
- Version-based: Data version track karke invalidate

### 3.4 Microservices vs Monolith

| Monolith | Microservices |
|----------|---------------|
| Single codebase, single deploy | Multiple small services, independent deploy |
| Simple to develop initially | Complex infrastructure |
| One technology stack | Polyglot (different languages/DBs per service) |
| Scale entire app | Scale individual services |
| One failure = all down | Isolated failures |
| Tight coupling | Loose coupling |

**When Microservices:**
- Large team, multiple feature teams
- Independent scaling needed
- Different technology requirements
- Frequent deployments

**When Monolith:**
- Small team, startup
- Simple application
- Quick iteration needed

### 3.5 Message Queues

**Why?** Asynchronous communication, decoupling, load leveling

**Patterns:**
- **Point-to-Point:** One producer → Queue → One consumer
- **Pub/Sub:** Publisher → Topic → Multiple subscribers

**Tools:**
| Tool | Best For |
|------|----------|
| **RabbitMQ** | Complex routing, traditional queuing |
| **Apache Kafka** | High throughput, event streaming, log aggregation |
| **Redis Pub/Sub** | Simple, fast pub/sub |
| **AWS SQS** | Managed queue service |
| **Celery** | Python task queue (with RabbitMQ/Redis backend) |

### 3.6 Rate Limiting

**Why?** Abuse prevent karo, server protect karo, fair usage

**Algorithms:**
- **Token Bucket:** Tokens refill at fixed rate, each request costs a token
- **Leaky Bucket:** Requests queue mein, process at fixed rate
- **Fixed Window:** Time window mein fixed number of requests
- **Sliding Window:** More accurate than fixed window

### 3.7 Consistent Hashing
- Distributed systems mein data distribute karna
- Server add/remove pe minimum data movement
- Virtual nodes: Load balance better kare
- Used in: CDNs, distributed caches, databases

---

## 4. API Design

### 4.1 REST API Design Principles

**RESTful Best Practices:**
- Nouns as resources: `/users`, `/orders` (not `/getUsers`)
- HTTP methods: GET (read), POST (create), PUT (update full), PATCH (update partial), DELETE
- Status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 500 (Server Error)
- Pagination: `/users?page=1&limit=20`
- Filtering: `/products?category=electronics&price_min=100`
- Versioning: `/api/v1/users`
- HATEOAS: Response mein related resource links

### 4.2 REST vs GraphQL vs gRPC

| Feature | REST | GraphQL | gRPC |
|---------|------|---------|------|
| Protocol | HTTP | HTTP | HTTP/2 (Protocol Buffers) |
| Data Format | JSON | JSON | Binary (Protobuf) |
| Overfetching | Yes | No (client specifies) | No |
| Real-time | Polling/WebSockets | Subscriptions | Streaming |
| Best For | Web APIs, CRUD | Complex queries, mobile apps | Microservices communication |
| Learning Curve | Low | Medium | High |

### 4.3 Authentication & Authorization

| Method | Use Case |
|--------|----------|
| **API Key** | Simple API access (public APIs) |
| **JWT (JSON Web Token)** | Stateless auth, mobile/SPA apps |
| **OAuth 2.0** | Third-party auth (Google login, GitHub login) |
| **Session-based** | Traditional web apps (server-side sessions) |

**JWT Structure:**
- Header: Algorithm + token type
- Payload: Claims (user_id, role, expiry)
- Signature: Verify token integrity
- Stateless: Server ko session store nahi karna padta
- Tradeoff: Token revoke karna mushkil (until expiry)

**OAuth 2.0 Flows:**
- **Authorization Code:** Web apps (most secure)
- **PKCE:** Mobile/SPA apps
- **Client Credentials:** Machine-to-machine
- **Implicit:** Deprecated (was for SPAs)

### 4.4 API Security
- HTTPS always (TLS encryption)
- Rate limiting
- Input validation
- CORS configuration
- API keys rotation
- Authentication + Authorization
- Request size limits
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)

---

## 5. Caching, Queues & Messaging

### 5.1 Redis
- In-memory data store
- Data structures: String, List, Set, Sorted Set, Hash, Stream
- Use cases: Caching, session store, rate limiting, leaderboards, pub/sub
- Persistence: RDB snapshots + AOF (Append-Only File)
- Cluster mode: Horizontal scaling
- Single-threaded (but very fast due to in-memory + I/O multiplexing)

### 5.2 Celery (Python Task Queue)
- Asynchronous task execution
- Backend: RabbitMQ ya Redis
- Use cases: Email sending, ML model training, report generation, periodic tasks
- Features: Retry, rate limiting, task routing, periodic tasks (celery beat)

---

## 6. DevOps & Cloud Basics

### 6.1 Docker
- Application ko container mein package karo (code + dependencies + runtime)
- "Works on my machine" problem solve
- Lightweight (vs Virtual Machines — no full OS)
- **Dockerfile:** Image build instructions
- **Image:** Read-only template
- **Container:** Running instance of image
- **Docker Compose:** Multi-container apps define + run

### 6.2 Kubernetes (K8s)
- Container orchestration platform
- **Pod:** Smallest deployable unit (1+ containers)
- **Service:** Pods ko discover + load balance kare
- **Deployment:** Desired state manage kare (replicas, updates)
- **Ingress:** External access manage kare
- Auto-scaling, self-healing, rolling updates

### 6.3 CI/CD
- **Continuous Integration:** Code merge → automated build + test
- **Continuous Delivery:** Auto deploy to staging
- **Continuous Deployment:** Auto deploy to production
- Tools: GitHub Actions, Jenkins, GitLab CI, CircleCI

### 6.4 Cloud Services Overview

| Service Type | AWS | Azure | GCP |
|-------------|-----|-------|-----|
| Compute | EC2, Lambda | VMs, Functions | Compute Engine, Cloud Functions |
| Storage | S3 | Blob Storage | Cloud Storage |
| Database | RDS, DynamoDB | SQL DB, CosmosDB | Cloud SQL, Bigtable |
| ML | SageMaker | Azure ML | Vertex AI |
| Container | ECS, EKS | AKS | GKE |

### 6.5 Git Best Practices
- **Branching:** main, develop, feature/*, hotfix/*
- **Commit messages:** Descriptive, conventional format
- **Branch Strategy:** Git Flow, GitHub Flow, Trunk-based
- **Code Review:** PRs with reviewers
- **Rebase vs Merge:** Rebase for clean history, Merge for feature branches

---

## 7. Python Libraries for Data Science

### 7.1 Library Overview

| Library | Purpose |
|---------|---------|
| **NumPy** | Numerical computing, arrays, linear algebra |
| **Pandas** | Data manipulation, DataFrames |
| **Matplotlib** | Basic plotting/visualization |
| **Seaborn** | Statistical visualization (built on matplotlib) |
| **Scikit-learn** | Classical ML algorithms |
| **TensorFlow** | Deep Learning framework (Google) |
| **PyTorch** | Deep Learning framework (Meta) — research favorite |
| **Keras** | High-level DL API (now part of TF) |
| **XGBoost** | Gradient boosting |
| **LightGBM** | Fast gradient boosting |
| **NLTK** | NLP toolkit (educational) |
| **SpaCy** | Industrial NLP |
| **Hugging Face** | Pre-trained models, Transformers |
| **LangChain** | LLM application framework |
| **OpenCV** | Computer vision |
| **Streamlit** | ML app deployment (dashboards) |
| **MLflow** | ML experiment tracking + model registry |
| **Airflow** | Workflow orchestration |

### 7.2 NumPy Key Concepts
- ndarray: N-dimensional array (fast, vectorized)
- Broadcasting: Different shapes ke arrays pe operations
- Vectorization: Loop avoid karo, NumPy operations use karo (100x faster)
- Linear algebra: dot product, matrix multiplication, eigenvalues

### 7.3 Pandas Key Concepts
- DataFrame: 2D labeled data (like Excel/SQL table)
- Series: 1D labeled data
- GroupBy: Split-Apply-Combine pattern
- Merge/Join: SQL-like joins
- Pivot Tables: Data summarization
- Method Chaining: Readable transformations
- Vectorized operations: Apply avoid karo jab vectorized possible ho

### 7.4 TensorFlow vs PyTorch

| Feature | TensorFlow | PyTorch |
|---------|-----------|---------|
| Mode | Static + Dynamic (Eager) | Dynamic (Eager by default) |
| Debugging | Harder (static graph) | Easy (Python-native) |
| Production | TF Serving, TFLite | TorchServe, ONNX |
| Research | Less popular now | Most popular |
| Learning Curve | Higher | Lower |
| Mobile | TFLite | PyTorch Mobile |
| Community | Industry focus | Research focus |

---

## 8. Interview Questions & Answers

### Q1: Monolith to Microservices kaise migrate karoge?
**Answer:**
- Ek saath mat karo — **Strangler Fig Pattern** use karo
- Pehle bounded contexts identify karo (DDD - Domain Driven Design)
- Sabse independent, high-change module pehle extract karo
- API Gateway lagao as single entry point
- Database bhi gradually split karo (hardest part)
- Event-driven communication implement karo (Kafka/RabbitMQ)
- Monitoring aur observability lagao (logging, tracing, metrics)
- Feature flags se gradually traffic shift karo

### Q2: ML model ko production mein serve karne ka architecture design karein.
**Answer:**
- **API Layer:** FastAPI/Flask — REST endpoint
- **Model Loading:** Model ko memory mein load karo (startup pe)
- **Input Validation:** Pydantic se request validate
- **Preprocessing:** Same pipeline jo training mein use hua
- **Prediction:** Model.predict()
- **Caching:** Repeated inputs ke liye Redis cache
- **Async:** Long predictions ke liye background tasks / queue (Celery)
- **Monitoring:** Predictions log karo, latency track karo, data drift detect karo
- **Scaling:** Docker + Kubernetes — `HPA` se auto-scale
- **A/B Testing:** Traffic split two model versions mein
- **Model Registry:** MLflow se model versions manage karo

### Q3: Database sharding kya hai aur kab use karein?
**Answer:**
- Data ko multiple databases mein horizontally split karna
- **Horizontal Sharding:** Rows split (e.g., user_id 1-1M → Shard 1, 1M-2M → Shard 2)
- **Shard Key:** Kaunsa column se shard karna hai (carefully choose — uneven distribution avoid karo)
- **When to shard:** Single DB ki capacity exceed ho jaye, read/write latency bahut high
- **Challenges:** Cross-shard queries mushkil, resharding painful, operational complexity
- **Alternatives pehle try karo:** Read replicas, caching, indexing optimization, vertical scaling

### Q4: Design a URL Shortener (like bit.ly)
**Answer:**
- **API:** POST /shorten {long_url} → {short_url}, GET /{short_code} → redirect
- **Encoding:** Long URL → unique short code (Base62 encoding of auto-increment ID)
- **Database:** Key-value store (short_code → long_url). Redis for hot lookups + PostgreSQL for persistence
- **Scaling:** Cache popular URLs in Redis, CDN for static redirects
- **Analytics:** Click count, location, device track karo
- **Collision handling:** Check if code exists, regenerate if needed
- **Expiry:** TTL set for temporary URLs

### Q5: Redis vs Memcached kab kya use karein?
**Answer:**
- **Redis:** Rich data structures (strings, lists, sets, sorted sets, hashes), persistence, pub/sub, Lua scripting, cluster mode. Use when you need more than simple caching.
- **Memcached:** Simple key-value, multi-threaded, slightly faster for simple cache. Use for pure caching.
- **Redis choose karo:** Leaderboards, rate limiting, session store, pub/sub, complex data
- **Memcached choose karo:** Simple object caching, multi-threaded advantage chahiye

### Q6: How would you design a real-time notification system?
**Answer:**
- **Components:** API server, Notification service, WebSocket server, Message queue, Database
- **Flow:** Event trigger → Message queue (Kafka) → Notification service → WebSocket push to user
- **WebSocket:** Persistent connection for real-time delivery
- **Fallback:** User offline toh store + push notification later
- **Priority:** Critical notifications pehle
- **Batch:** Non-urgent notifications batch mein bhejo
- **User preferences:** Notification settings respect karo

### Q7: Django mein N+1 query problem kya hai aur kaise solve karein?
**Answer:**
- **Problem:** Related objects access karne pe har ek ke liye separate query fired hoti hai. 1 query for main objects + N queries for related = N+1
- **Example:** 100 posts ke authors fetch karna = 1 query (posts) + 100 queries (each author)
- **Solution:**
  - `select_related()`: Foreign key/OneToOne — SQL JOIN (single query)
  - `prefetch_related()`: ManyToMany/Reverse FK — 2 queries (batch fetch)
- **Detection:** Django Debug Toolbar, django-silk

### Q8: JWT vs Session-based authentication ka tradeoff?
**Answer:**
- **JWT:** Stateless, server pe session store nahi, scalable, microservices ke liye best. Problem: Token revoke mushkil (blacklist chahiye), token size bada.
- **Session:** Server pe session store, easy revocation, smaller cookie. Problem: Server memory, horizontal scaling mein session sharing chahiye (Redis).
- **JWT for:** APIs, mobile apps, microservices, SPAs
- **Session for:** Traditional web apps, simple setup

### Q9: Explain CAP theorem with real examples.
**Answer:**
- **CA (Consistency + Availability):** Single-node RDBMS (PostgreSQL). No partition tolerance — single server fails toh down.
- **CP (Consistency + Partition tolerance):** MongoDB, Redis Cluster. During partition, some nodes unavailable but data consistent.
- **AP (Availability + Partition tolerance):** Cassandra, DynamoDB. Always available but data eventually consistent.
- **In practice:** Network partitions WILL happen, so choose between CP and AP.
- Mostly systems tune between consistency levels (strong vs eventual).

### Q10: Python application ka performance kaise optimize karoge?
**Answer:**
- **Profile first:** cProfile, line_profiler, py-spy — bottleneck find karo
- **Database:** N+1 fix karo, proper indexes, query optimization, connection pooling
- **Caching:** Redis for frequent queries, application-level caching
- **Async:** I/O-bound tasks ke liye asyncio/FastAPI
- **Concurrency:** ThreadPoolExecutor (I/O), ProcessPoolExecutor (CPU)
- **Code:** List comprehensions, generators, built-in functions prefer karo
- **Serialization:** orjson for fast JSON, avoid pickle for inter-service
- **Connection Pooling:** DB aur HTTP connections reuse karo
- **CDN:** Static assets serve efficiently

### Q11: Docker vs Virtual Machine ka difference?
**Answer:**
- **VM:** Full OS simulate, heavier (GB), slow startup, strong isolation (hypervisor)
- **Docker:** OS kernel share, lighter (MB), fast startup (seconds), process-level isolation
- **VM use:** Different OS chahiye, strong security isolation, legacy apps
- **Docker use:** Microservices, CI/CD, consistent environments, fast deployment
- **Together:** Docker inside VM for cloud deployments

### Q12: Design an ML Pipeline for a recommendation system.
**Answer:**
- **Data Collection:** User behavior (clicks, purchases, ratings), item features
- **Feature Engineering:** User embeddings, item embeddings, interaction features, temporal features
- **Model Options:** Collaborative filtering (user-user, item-item), Content-based, Hybrid, Deep (Neural Collaborative Filtering)
- **Training:** Offline batch training, periodic retraining
- **Serving:** Real-time: Pre-computed recommendations cached in Redis. Near-real-time: Feature store + online model
- **Evaluation:** Offline (NDCG, MAP, Hit Rate), Online (A/B test — CTR, conversion, engagement)
- **Cold Start:** New user → popular items / content-based. New item → explore/exploit.
- **Monitoring:** Diversity, coverage, feedback loops (popularity bias)

---

## Quick Revision Table

| Concept | Key Point |
|---------|-----------|
| Django | Full-stack, batteries included, ORM + Admin |
| FastAPI | Async, Pydantic validation, auto docs — best for APIs |
| REST | Resources + HTTP methods + status codes |
| GraphQL | Client specifies data needs — no overfetching |
| JWT | Stateless token auth — payload + signature |
| ACID | Atomicity, Consistency, Isolation, Durability |
| CAP | Pick 2: Consistency, Availability, Partition tolerance |
| Caching | Redis/Memcached — read performance boost |
| Microservices | Independent services, loose coupling |
| Docker | Container = app + dependencies packaged |
| K8s | Container orchestration — auto-scale, self-heal |
| Load Balancer | Distribute traffic across servers |
| Sharding | Horizontal data split across databases |
| CI/CD | Automated build → test → deploy |

---

*10+ Years Experience Level - System Design & Python Frameworks Theory*
