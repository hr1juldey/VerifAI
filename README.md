# Verifai

> JEPA-powered visual verification platform for Indian D2C return fraud elimination

---

## The Problem: ₹1000+ Crore Return Fraud Crisis

### Critical Pain Points
- **71% of returns** are due to product mismatches (wrong items, used instead of new, etc.)
- **Claim windows**: 24-72 hours on marketplaces (Amazon/Flipkart) - miss it, you lose
- **Cost**: ₹500-1000 per return in reverse logistics + quality checks
- **Warehouse scale**: Manual verification = 1 QA person per 4 pickers; one 3PL spends ₹45,000/day just on picking accuracy
- **Fraud patterns**: "Wardrobing", swap fraud, damage claims
- **D2C bleeding**: Reverse logistics costs 12-18% of net revenue; fashion/electronics have 40%+ return rates

### Current Solutions Failing
- **Manual packing videos**: TrackVid charges ₹X per order, labor-intensive, not scalable
- **Visual inspection**: Brittle to lighting/angle changes, can't handle product variations
- **Traditional CV**: Requires 1000s of labeled images per product, expensive to retrain

---

## The Solution: Verifai

### What It Does
Full-stack visual verification platform across the warehouse lifecycle using **JEPA (Joint-Embedding Predictive Architecture)**:

**1. Inbound Verification** (Receiving)
- Camera at receiving dock
- JEPA identifies products in real-time
- Flags: wrong items, damaged goods, quantity mismatches
- Auto-generates discrepancy reports

**2. Packing Verification** (Outbound)
- Camera at packing stations
- Records JEPA-verified packing proof linked to Order ID
- Auto-uploads to cloud for claim evidence
- Replaces manual packing video services

**3. Return Verification** (Reverse Logistics)
- Camera at return processing
- JEPA compares returned item vs. what was sent
- Detects: wrong items, damage, missing components
- Auto-generates claim evidence for marketplaces

**4. Quality Control**
- Continuous visual inspection
- Damage detection, packaging integrity
- Pattern recognition for recurring issues
- Feeds back into product/supplier decisions

### Why JEPA Wins
- **Few-shot learning**: 10-20 images per product → production ready (vs 1000s for traditional CV)
- **Semantic understanding**: Learns "what makes a phone a phone" not just pixels
- **Robust representations**: Handles Indian warehouse chaos (lighting, angles, partial views)
- **Fast adaptation**: New product? Show 5 examples, done
- **Edge-first**: Runs on ₹30K GPUs, not ₹30L cloud bills

---

## Architecture

### Data Pipeline
```
EDGE LAYER (Warehouse)
├── RTX 3060/4060 per camera cluster
├── JEPA inference: 30 FPS
├── Local storage: 7 days rolling
└── Auto-upload: Flagged events only

SYNC LAYER
├── Order ID linking
├── Compression + encryption
└── Bandwidth-aware upload

CLOUD LAYER
├── JEPA model updates (federated)
├── Cross-client fraud patterns
├── Claim evidence API
└── Analytics dashboard
```

### Key Innovation: Federated Learning
- Each warehouse trains local JEPA on their products
- Anonymized fraud patterns shared across network
- Better fraud detection as network grows
- Privacy-preserving (no raw product images leave warehouse)

---

## Commercial Model (B2B SaaS)

### Pricing Tiers
| Tier | Cameras | Verifications/Month | Price | Target |
|-------|-----------|---------------------|---------|---------|
| Starter | 1-2 | 1,000 | ₹15,000/month | Instagram/Facebook D2C brands |
| Growth | 5-10 | 10,000 | ₹75,000/month | Shopify stores, small 3PLs |
| Enterprise | Unlimited | Unlimited | ₹2.5L-10L/month | Meesho sellers, WareIQ, Shiprocket |

### Revenue Streams
- SaaS subscription (predictable recurring)
- Per-claim-won bonus (performance-based)
- Fraud pattern insights (data monetization)

---

## Tech Stack

### Backend
- Python 3.12+
- FastAPI (API layer)
- JEPA (PyTorch implementation)
- OpenCV / PyAV (video processing)
- SQLite/PostgreSQL (order linking + evidence storage)

### Frontend
- Next.js 14+ (dashboard)
- Tailwind CSS
- shadcn/ui
- React Query (data fetching)

### AI/ML
- PyTorch 2.x
- JEPA implementation (pytorch-jepa or custom)
- On-device inference (edge GPUs)

### Infrastructure
- Docker Compose (development)
- RTX 3060/4060 (edge deployment)
- Bandwidth-optimized sync
- Encryption at rest and in transit

---

## 5-Day Build Plan

### Day 1: Core JEPA + Data Infra
- Set up I-JEPA with video input pipeline
- Build Order ID linking system
- Create mock warehouse data (50 products)
- Set up local edge inference

### Day 2: Verification Workflows
- Inbound: Product identification + anomaly detection
- Packing: Order-linked video generation
- Return: Comparison logic (sent vs. returned)

### Day 3: Data Pipeline + Storage
- Event-based upload (only upload anomalies/flagged)
- Order ID → Video evidence mapping
- Local 7-day rolling storage
- Compression + encryption

### Day 4: Dashboard + Claim Integration
- Real-time verification dashboard
- Claim evidence export (Flipkart/Amazon format)
- Fraud pattern analytics
- ROI calculator

### Day 5: Demo + Scale Simulation
- Multi-camera setup simulation
- Stress test: 1000 orders/hour
- Demo with real products
- Professional video + docs

---

## Target Market

- **Meesho sellers** (primary target - bleeding on return fraud)
- **3PLs** (WareIQ, Shiprocket - want verification at scale)
- **Shopify stores** (mid-market D2C brands)
- **Amazon/Flipkart sellers** (need marketplace-specific claim evidence)

---

## Development Status

### Current State
- Project scaffolded with `uv` + Python 3.12
- Basic `main.py` entry point
- Git repository initialized
- Virtual environment created

### Next Steps
- [ ] Design JEPA architecture for few-shot product learning
- [ ] Build camera integration layer (RTSP/WebRTC)
- [ ] Implement video processing pipeline
- [ ] Design Order ID linking system
- [ ] Create mock warehouse product database
- [ ] Build verification workflow orchestration
- [ ] Design dashboard UI wireframes
- [ ] Set up edge inference infrastructure
- [ ] Implement federated learning framework
- [ ] Prepare fellowship application materials

---

## Fellowship Alignment

### Why This Wins
1. **Depth (Technical)**: Novel JEPA application in logistics; solves few-shot learning at scale
2. **Velocity (Can Ship Fast)**: 5 days to working demo; edge-first architecture
3. **Taste (Problem Selection)**: ₹1000+ crore problem; targets Meesho ecosystem directly
4. **Activation Alignment**: Meesho sellers bleeding + Emergent's edge-first philosophy

### Demo Strategy (3-minute video)
1. **Problem** (30s): Real return fraud case + ₹ loss
2. **Solution** (90s): Live demo of all 4 workflows
3. **Scale** (45s): Multi-camera setup + data pipeline
4. **Impact** (15s): ROI calculation for D2C brand

---

## Contributing

Coming soon. This is early development - check back for contribution guidelines.

## License

TBD (will decide before fellowship submission)

---

## Contact

- **Developer**: Riju (hr1juldey)
- **Project**: Verifai
- **Status**: Early development - planning phase
