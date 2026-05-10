# VerifAI Demo Video — Complete Script & Production Plan

## Video Metadata
- **Duration**: ~3:00 (target: 2:45–3:15)
- **Voice**: AI-generated English narration (text_to_speech, Edge/OpenAI)
- **Resolution**: 1920×1080 (1080p)
- **Frame rate**: 30fps
- **Format**: MP4 (H.264 + AAC)
- **Audience**: Fellowship evaluators (primary), D2C/3PL operators (secondary)

---

## Storytelling Framework: Modified H.O.O.K.

### H — Hero (0:00–0:30)
Introduce Riju — who he is, what drives him. Not the product yet. The person.
The viewer needs to care about the person before caring about the problem.

### O — Obstacle (0:30–1:20)
The problem. Return fraud. The ₹1000+ Crore bleeding. Why existing solutions fail.
This isn't abstract — this is warehouse floors, 3PL hubs, D2C founders losing sleep.

### O — Outcome (1:20–1:55)
The vision. What if verification took 1.8 seconds instead of 45 minutes?
What if a ₹30K GPU could do what ₹30L cloud infrastructure couldn't?
Show the future state before showing the tech — let the viewer want it.

### K — Key Insight (1:55–2:50)
The demo. The "aha moment." I-JEPA isn't a classifier. It doesn't learn labels.
It learns what "same product" means — from 10 images, in a warehouse with
terrible lighting, weird angles, and partial views. Then show it happening live.

### Close (2:50–3:00)
The ask. Early access. Let's talk.

---

## SHOT-BY-SHOT SCRIPT

### SEGMENT 1: HERO — "Who is Riju?" (0:00–0:30)

**[SCREEN: Black. 1 second. Then text fades in.]**

> NARRATION (V.O.):
> 
> "Indian e-commerce loses over a thousand crore rupees a year to return fraud. 
> Nobody's really building for it."

**[SCREEN: Landing page loads. Hero animation starts playing. We see the verification card cycling through images — a saree slides in, a scan line sweeps across, a SUSPECT badge pops.]**

> NARRATION (V.O.):
> 
> "My name is Hrijul. I used to run product at Lilypad — an EV logistics company. 
> Now I build AI tools. The kind that work on cheap hardware, in messy real places."

**[SCREEN: Camera holds on the hero animation. Let the viewer watch one full cycle — catalog, return, scanning, heatmap bloom, verdict.]**

> NARRATION (V.O.):
> 
> "That thing on screen? It's running right now. 
> Live. Two seconds per check."

---

### SEGMENT 2: OBSTACLE — "The ₹1000 Crore Problem" (0:30–1:20)

**[SCREEN: Smooth scroll down to the pain section. The ₹1,000+ Crore headline comes into view.]**

> NARRATION (V.O.):
> 
> "So here's what's happening. E-commerce in India is growing like crazy. 
> The returns are growing faster."

**[SCREEN: Hold on the three stat cards as they appear: 71%, ₹500-1000, 40%+]**

> NARRATION (V.O.):
> 
> "Seven out of ten returns are product mismatches. Wrong item. Used instead of new. 
> Sometimes they ship back a completely different product. 
> A saree goes out, a bedsheet comes back. That kind of thing."

**[SCREEN: Camera slowly pans across the three cards.]**

> NARRATION (V.O.):
> 
> "Each return costs five hundred to a thousand rupees to process. 
> Fashion and electronics see forty percent return rates. 
> I talked to a D2C brand that burns twelve to eighteen percent of their revenue 
> just on reverse logistics."

**[SCREEN: Hold on the full pain section. Let the weight of the numbers sink in.]**

> NARRATION (V.O.):
> 
> "Right now the options are: pay someone to record packing videos for every order. 
> Or have humans visually inspect returns — which works until the warehouse 
> lights change, or someone's tired, or the product is wrapped in plastic. 
> Or use traditional computer vision, which means labeling thousands of images 
> per product, and retraining every time a new SKU drops."

---

### SEGMENT 3: OUTCOME — "What If Verification Was Instant?" (1:20–1:55)

**[SCREEN: Smooth scroll to the Technology section. I-JEPA · ViT-H/14 · 632M parameters fades in.]**

> NARRATION (V.O.):
> 
> "So what would it actually take to walk into any warehouse — bad lighting, 
> weird angles, half the product covered — and verify what's in front of you 
> in under two seconds?"

**[SCREEN: Hold on the tech tags: I-JEPA Encoder, Spatial Diff Analysis, Gemma 4 VLM, Edge-First Architecture, Federated Learning.]**

> NARRATION (V.O.):
> 
> "A classifier won't cut it. You can train a model to recognize 'saree' vs 'not saree,' 
> but there are ten thousand kinds of sarees and a new one launches every day. 
> You'd be retraining constantly."
> 
> "What you need is something that can look at two photos and tell you: 
> is this the same thing? Not by matching pixels. By understanding what it's looking at."

---

### SEGMENT 4: KEY INSIGHT — "Why I-JEPA?" (1:55–2:25)

**[SCREEN: Stay on the tech section. Camera is still.]**

> NARRATION (V.O.):
> 
> "I-JEPA. Image-based Joint-Embedding Predictive Architecture. 
> Came out of Yann LeCun's group at Meta, 2023."

**[SCREEN: Subtle zoom into the tech tags area.]**

> NARRATION (V.O.):
> 
> "The short version: instead of learning labels like 'saree' or 'kurta,' 
> it learns representations. It predicts parts of an image from other parts, 
> which means it ends up understanding object structure — shape, texture, context — 
> without anyone telling it what to look for."
> 
> "In practice, that means you show it ten photos of a product. Ten. 
> And it can verify returns. It doesn't care if the photo was taken 
> under fluorescent warehouse lights at a weird angle. 
> It still works."
> 
> "Also: the whole thing runs on a thirty thousand rupee GPU. 
> You don't need cloud infrastructure for this."

---

### SEGMENT 5: THE DEMO — "Watch It Work" (2:25–2:50)

**[SCREEN: Navigate to /demo page. The page loads clean — two upload zones side by side.]**

> NARRATION (V.O.):
> 
> "Let me just show you."

**[ACTION: Click the catalog upload zone. Select a saree image. It appears in the preview.]**

> NARRATION (V.O.):
> 
> "Catalog image. This is what was supposed to go to the customer."

**[ACTION: Click the return upload zone. Select a DIFFERENT saree image. It appears in the preview.]**

> NARRATION (V.O.):
> 
> "And this is what came back. Different saree. Swap fraud."

**[ACTION: Click "Verify". The processing state fires — scan lines, ANALYZING text. Then the heatmap blooms — red/orange overlay on the difference regions. The verdict pops: SUSPECT or FRAUD with confidence score.]**

> NARRATION (V.O.):
> 
> "One point eight seconds. Heatmap shows where they differ. 
> Confidence score. Flagged."

**[ACTION: Quick reset. Upload same image for both catalog and return. Verify. MATCH badge pops green.]**

> NARRATION (V.O.):
> 
> "Same product? Match."

**[ACTION: One more — catalog is a sherwani, return is a saree. FRAUD. Red heatmap blooms dramatically.]**

> NARRATION (V.O.):
> 
> "Completely wrong product? Caught."

---

### SEGMENT 6: CLOSE — "The Ask" (2:50–3:00)

**[SCREEN: Navigate back to landing page. Scroll to early access form.]**

> NARRATION (V.O.):
> 
> "We're looking for early partners. D2C brands, 3PLs, marketplace sellers. 
> If returns are eating your margins, reach out."

**[SCREEN: Hold on the form for 3 seconds. Fade to black.]**

> NARRATION (V.O.):
> 
> "VerifAI."

**[SCREEN: Black. VerifAI logo. Fade out.]**

---

## NARRATION WORD COUNT & TIMING

| Segment | Words | Est. Duration |
|---------|-------|---------------|
| 1. Hero | ~85 | 0:30 |
| 2. Obstacle | ~145 | 0:50 |
| 3. Outcome | ~100 | 0:35 |
| 4. Key Insight | ~130 | 0:30 |
| 5. Demo | ~110 | 0:25 |
| 6. Close | ~40 | 0:10 |
| **Total** | **~610** | **~3:00** |

At average narration pace (~200 words/min), 610 words ≈ 3:03.

---

## PRODUCTION PIPELINE

### Phase 1: Record Browser Footage
- **Tool**: Playwright/Puppeteer or manual OBS screen recording
- **Approach**: Automated Playwright script that navigates, scrolls, clicks, uploads
- **Resolution**: 1920×1080 viewport
- **Output**: Raw `.webm` segments per segment

### Phase 2: Generate Narration Audio
- **Tool**: `text_to_speech` (Edge TTS or OpenAI TTS)
- **Voice**: Professional male English voice
- **Output**: `.mp3` segments per segment

### Phase 3: Assemble in FFmpeg
- Merge video segments with audio segments
- Add fade transitions between segments
- Add text overlays for stat cards
- Output: `verifai-demo-final.mp4`

### Phase 4: QA
- Watch full video end-to-end
- Check audio sync, pacing, visual quality
- Verify all interactions are visible and clear

---

## RIJU'S PROFILE — Key Facts for Narration Accuracy

| Detail | Source |
|--------|--------|
| Full name | Hrijul Dey |
| Identity | Indie hacker, AI researcher |
| Past role | Product Manager, Lilypad (EV brand — connected fleet/logistics products) |
| Education | B.Tech Biotechnology, VIT Vellore (2018-2022) |
| Research fellow | Ashva Wearable Technologies (2020-present) |
| Tech stack | Python, DSPy, Ollama, FastAPI, PyTorch, ColBERTv2 |
| Philosophy | Local-first AI, privacy-preserving, edge-first |
| GitHub | hr1juldey — 1,925 contributions/year, 45 repos |
| Notable projects | AgentX (JARVIS-style AI), FairDOC (healthcare triage), IndiByte (nutrition), Demosaur (MCP code intern) |
| Location | Kolkata, India |
| Blog | artificialintelligenceupdate.com |

### Why Lilypad matters for this story:
Lilypad is an EV brand that connects Addtrack, Lilyput, Rider_del, fleet-mgmt, and breath_rush.
Riju was PM there — he understands logistics, fleet operations, and the chaos of physical-world operations.
This isn't an AI researcher who stumbled into e-commerce. This is someone who lived the logistics problem
and then brought AI research to solve it.

---

## DEMO INTERACTION SCRIPT (for Playwright)

```
1. Navigate to http://localhost:3000/
2. Wait 4s (let hero animation play one full cycle)
3. Scroll to pain section (smooth, 1.5s)
4. Wait 3s (let stats sink in)
5. Scroll to tech section (smooth, 1.5s)
6. Wait 2s
7. Navigate to http://localhost:3000/demo
8. Wait 2s (page load)
9. Click catalog upload → select saree_000.jpeg
10. Wait 1.5s (preview renders)
11. Click return upload → select saree_005.jpeg
12. Wait 1.5s
13. Click "Verify" button
14. Wait 3s (processing + heatmap + verdict)
15. Reset
16. Upload same image for both (saree_002.jpeg)
17. Click "Verify"
18. Wait 3s (MATCH result)
19. Reset
20. Upload sherwani_000.jpeg (catalog) + saree_003.jpeg (return)
21. Click "Verify"
22. Wait 3s (FRAUD result)
23. Navigate back to /
24. Scroll to early access form
25. Wait 3s
26. Fade to black
```

---

## FILES TO PRODUCE

1. `scripts/video/record-footage.py` — Playwright recording script
2. `scripts/video/generate-narration.sh` — TTS generation script
3. `scripts/video/assemble.sh` — FFmpeg assembly script
4. `scripts/video/verifai-demo-final.mp4` — Final output
5. `scripts/video/segments/` — Raw video + audio segments
