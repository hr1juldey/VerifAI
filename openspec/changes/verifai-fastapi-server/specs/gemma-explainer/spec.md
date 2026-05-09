## ADDED Requirements

### Requirement: DSPy explainer with Ollama backend

Use DSPy framework with Ollama as the LM backend for Gemma 4 multimodal inference. Configure via `dspy.LM("ollama_chat/gemma4:e4b", api_base="http://localhost:11434", api_key="")` using the local `gemma4:e4b` model (9.6 GB).

#### Scenario: Successful explanation generation
- **WHEN** a REJECT decision has been made and composite images are available
- **THEN** the DSPy explainer module is invoked with `dspy.Image` inputs for catalog and annotated return, returning a structured explanation string

#### Scenario: Ollama unavailable
- **WHEN** the Ollama call fails after retries (DSPy `num_retries=3` with exponential backoff)
- **THEN** the explanation field is set to "Explanation unavailable (Ollama timeout)" and the response still includes the spatial diff image

### Requirement: DSPy Signature for explanation

Define a `dspy.Signature` that declares image inputs and text output for type-safe multimodal inference.

#### Scenario: Signature definition
- **WHEN** the explainer is initialized
- **THEN** a signature is defined with:
  - `catalog_image: dspy.Image = dspy.InputField(desc="Original catalog product")`
  - `return_image: dspy.Image = dspy.InputField(desc="Returned item with red overlay on flagged regions")`
  - `product_description: str = dspy.InputField(desc="Product name and details for context")`
  - `explanation: str = dspy.OutputField(desc="Factual description of red-highlighted regions only. No preamble. 1-3 sentences.")`

### Requirement: Explainer module initialization

Initialize `dspy.Predict` with the explanation signature at server startup.

#### Scenario: Module creation
- **WHEN** the FastAPI lifespan starts
- **THEN** `dspy.LM` is configured with `ollama_chat/gemma4` and the explainer module is instantiated as `dspy.Predict(ExplainRejectionSignature)`

### Requirement: Clean explanation output

The DSPy output field must be stripped of any markdown formatting or preamble.

#### Scenario: Clean explanation output
- **WHEN** Gemma 4 returns a response via DSPy
- **THEN** the `explanation` field is stripped of leading/trailing whitespace, markdown code blocks, and any "Here is..." preamble, returning only the factual description
