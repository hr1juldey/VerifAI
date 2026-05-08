## ADDED Requirements

### Requirement: Send constrained explanation request to Ollama

Given a composite image (catalog + annotated return) and a product description, construct a constrained prompt and send to Gemma 4 via the Ollama HTTP API.

#### Scenario: Successful explanation generation
- **WHEN** a REJECT decision has been made and a composite image is available
- **THEN** a POST request is sent to Ollama at localhost:11434 with the composite image and a prompt that instructs: "Describe ONLY what you see in the red-highlighted regions. Be specific. If nothing appears wrong, say so."

#### Scenario: Ollama unavailable
- **WHEN** the Ollama HTTP call fails or times out (5-second limit)
- **THEN** the explanation field is set to "Explanation unavailable (Ollama timeout)" and the response still includes the spatial diff image

### Requirement: Construct anchored prompt

The prompt must include three grounding elements: the original product description, instruction to focus on red regions only, and instruction to be specific.

#### Scenario: Prompt construction
- **WHEN** an explanation request is prepared
- **THEN** the prompt contains: (1) "Left: original catalog product. Right: returned item.", (2) "Red regions: where verification detected differences.", (3) "Describe ONLY what you see in the red regions. Be specific."

### Requirement: Return structured explanation

The Gemma 4 output must be returned as a plain string, trimmed of any markdown formatting or preamble.

#### Scenario: Clean explanation output
- **WHEN** Gemma 4 returns a response
- **THEN** it is stripped of leading/trailing whitespace, markdown code blocks, and any "Here is..." preamble, returning only the factual description
