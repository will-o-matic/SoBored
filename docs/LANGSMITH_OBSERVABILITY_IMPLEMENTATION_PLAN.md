# LangSmith LLM Observability Implementation Plan

## Executive Summary

**Problem:** LLM calls in your event processing pipeline are invisible in LangSmith UI. The Parse URL Content tool shows execution time (2.25s) but no prompt/response details, token usage, or model parameters.

**Root Cause:** Missing LangSmith client wrappers and @traceable decorators on LLM functions.

**Impact:** No debugging capability, cost tracking, prompt engineering, or error observability for LLM operations.

## Current State Analysis

### Trace Visibility Gap
```
Smart Event Processing Pipeline (6.89s)
├── Smart Input Classification (0.00s) ✅ Visible
├── URL Event Processing (6.89s)
    ├── Fetch URL Content (0.26s) ✅ Visible  
    ├── Parse URL Content (2.25s) ⚠️ Tool visible, LLM call HIDDEN
    └── Save to Notion (4.38s) ✅ Visible
```

### Missing LLM Observability
- ❌ No prompt/response visibility
- ❌ No token usage tracking
- ❌ No cost attribution
- ❌ No model parameter logging
- ❌ No error tracing within LLM calls
- ❌ No prompt versioning/testing capability

## Implementation Plan

### Phase 1: Critical LLM Call Visibility (Priority 1)
**Timeline:** 1-2 hours  
**Impact:** HIGH - Immediate LLM observability

#### 1.1 Fix Anthropic Client Wrapping
**File:** `langgraph/agents/tools/parse_url_tool.py`

**Current Code:**
```python
client = anthropic.Anthropic(api_key=api_key)
```

**Updated Code:**
```python
from langsmith.wrappers import wrap_anthropic
from langsmith import traceable

client = wrap_anthropic(anthropic.Anthropic(api_key=api_key))
```

#### 1.2 Add @traceable Decorator
**Current:**
```python
@tool
def parse_url_content(webpage_content: str, webpage_title: str = "Untitled") -> dict:
```

**Updated:**
```python
@tool
@traceable(
    run_type="tool", 
    name="Parse URL Content",
    metadata={"model": "claude-3-haiku-20240307", "use_case": "event_extraction"}
)
def parse_url_content(webpage_content: str, webpage_title: str = "Untitled") -> dict:
```

#### 1.3 Create Dedicated LLM Function
**New Function:**
```python
@traceable(
    run_type="llm",
    name="Claude Event Extraction",
    tags=["claude", "event-parsing", "url-content"]
)
def extract_event_with_claude(prompt: str, model: str = "claude-3-haiku-20240307") -> dict:
    """Dedicated LLM function for event extraction with full observability."""
    response = client.messages.create(
        model=model,
        max_tokens=300,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )
    return response
```

#### 1.4 Expected Result
After Phase 1, LangSmith UI will show:
```
Parse URL Content (tool)
└── Claude Event Extraction (llm) ← NOW VISIBLE
    ├── Full prompt with variables
    ├── Complete Claude response  
    ├── Token usage (input: X, output: Y, total: Z)
    ├── Cost: $0.00X
    ├── Latency: 2.25s
    └── Model parameters (temperature: 0.1, max_tokens: 300)
```

### Phase 2: Prompt Engineering Infrastructure (Priority 2)
**Timeline:** 1-2 days  
**Impact:** HIGH - Enables prompt versioning & testing

**Architectural Decision:** Keep prompts in version control with optional LangSmith override for experiments.

**Rationale:** Prompts are application logic that determine data extraction accuracy and business outcomes. They must be versioned with code for deployment integrity and operational stability.

#### 2.1 Extract & Version Control Prompts
**Action Items:**
1. Extract hardcoded prompt from `parse_url_tool.py:48-86`
2. Create versioned prompt files: `prompts/event_extraction_v1.py`
3. Implement semantic versioning for prompt changes
4. Add prompt loading utilities with fallback logic

#### 2.2 Implement Hybrid Prompt System
**New Code:**
```python
from langsmith import Client
from prompts.event_extraction import get_event_extraction_prompt_v1

def load_event_extraction_prompt() -> str:
    """Load prompt with version control primary, LangSmith experiments optional."""
    # Default: version-controlled prompt (always available)
    base_prompt = get_event_extraction_prompt_v1()
    
    # Optional: LangSmith override for controlled experiments
    if feature_flag_enabled("prompt_experiments"):
        try:
            client = Client()
            experimental_prompt = client.pull_prompt("event-extraction-experiment")
            return experimental_prompt.format_prompt()
        except Exception:
            # Fallback to version-controlled prompt
            pass
    
    return base_prompt

@traceable(run_type="tool")
def parse_url_content(webpage_content: str, webpage_title: str = "Untitled") -> dict:
    # Load hybrid prompt (version control + optional experiments)
    prompt_template = load_event_extraction_prompt()
    
    # Format with variables
    formatted_prompt = prompt_template.format(
        current_date=current_date,
        current_day=current_day,
        webpage_title=webpage_title,
        webpage_content=webpage_content[:3000]
    )
    
    # Call traced LLM function
    return extract_event_with_claude(formatted_prompt)
```

#### 2.3 Enable Controlled Experimentation
**Hybrid Architecture Benefits:**
- **Production Stability:** Version controlled prompts ensure reliable deployments
- **Experimentation:** LangSmith A/B testing for prompt optimization
- **Atomic Deployments:** Code + prompts version together
- **Fail-Safe Operation:** System works without LangSmith dependency
- **Promotion Path:** Experiment → validate → commit to version control → deploy

#### 2.4 Prompt Versioning Workflow
**Implementation:**
```python
# prompts/event_extraction.py
def get_event_extraction_prompt_v1() -> str:
    """Version 1.0 - Initial event extraction prompt."""
    return """Today is {current_date} ({current_day}).
    
Parse the following webpage content for events...
[Full prompt text with semantic version]
"""

def get_event_extraction_prompt_v2() -> str:
    """Version 2.0 - Improved accuracy for recurring events."""
    return """Enhanced prompt with better event detection..."""
```

**Benefits:**
- Git history tracks all prompt changes
- Semantic versioning for prompt evolution  
- Code review process for prompt modifications
- Rollback capability with full system state
- Environment consistency guaranteed

### Phase 3: Enhanced Error Observability (Priority 3)  
**Timeline:** 2-3 days  
**Impact:** MEDIUM - Better debugging & reliability

#### 3.1 Trace Fallback Logic
**Current Issue:** Fallback to regex parsing isn't well-traced

**Enhanced Implementation:**
```python
@traceable(run_type="tool", name="Parse URL Content with Fallback")
def parse_url_content_robust(webpage_content: str, webpage_title: str) -> dict:
    try:
        # Primary: LLM-based parsing (fully traced)
        return parse_with_claude(webpage_content, webpage_title)
    except anthropic.APIError as e:
        # Traced fallback for API errors
        return fallback_parse_with_tracing(webpage_content, webpage_title, error=str(e))
    except Exception as e:
        # Traced fallback for other errors  
        return emergency_fallback_with_tracing(webpage_content, webpage_title, error=str(e))

@traceable(run_type="tool", name="Regex Fallback Parser")
def fallback_parse_with_tracing(content: str, title: str, error: str) -> dict:
    """Traced version of fallback parsing logic."""
    result = _fallback_parse_webpage(content, title)
    result["fallback_reason"] = error
    result["parsing_method"] = "regex_fallback"
    return result
```

#### 3.2 Error Classification & Alerting
**Implementation:**
- Classify errors: API timeouts, quota exceeded, parsing failures
- Set up LangSmith alerts for error rate spikes
- Track error patterns for proactive fixes

### Phase 4: Cost & Performance Monitoring (Priority 4)
**Timeline:** 3-5 days  
**Impact:** MEDIUM - Cost optimization & performance insights

#### 4.1 Token Usage Analytics
**Metrics to Track:**
- Tokens per event extraction
- Cost per user/source (telegram vs web)
- Model efficiency (Haiku vs Sonnet vs Opus)
- Prompt length optimization opportunities

#### 4.2 Performance Optimization
**Implementation:**
```python
@traceable(
    run_type="llm",
    metadata={
        "model": "claude-3-haiku-20240307",
        "use_case": "event_extraction", 
        "content_length_bucket": "0-1000|1000-3000|3000+"
    }
)
def extract_event_with_performance_tracking(prompt: str, content_length: int) -> dict:
    # Track performance by content length
    bucket = get_content_length_bucket(content_length)
    
    # LangSmith automatically tracks:
    # - Time to first token
    # - Total latency  
    # - Tokens per second
    # - Cost per call
    
    return client.messages.create(...)
```

#### 4.3 Cost Attribution Dashboard
**Setup:**
- Group costs by user_id, source, date
- Track monthly spending trends
- Set budget alerts
- Identify high-cost usage patterns

### Phase 5: Advanced Observability Features (Priority 5)
**Timeline:** 1-2 weeks  
**Impact:** MEDIUM - Advanced debugging & optimization

#### 5.1 Prompt Performance Testing
**A/B Testing Setup:**
```python
@traceable(run_type="llm", tags=["experiment:prompt-v2"])
def test_improved_prompt(content: str, title: str) -> dict:
    """Test improved prompt version against baseline."""
    prompt_v2 = client.pull_prompt("event-extraction-prompt:v2")
    return extract_event_with_claude(prompt_v2.format(...))
```

#### 5.2 Quality Metrics Tracking
**Implementation:**
- Track parsing confidence scores over time
- Monitor fallback usage rates  
- Measure accuracy against ground truth dataset
- Set up regression detection

#### 5.3 Multi-Agent Trace Correlation
**Enhanced Tracing:**
```python
@traceable(run_type="chain", name="Smart Pipeline Orchestration")
def process_with_smart_pipeline(raw_input: str, source: str, user_id: str, dry_run: bool) -> dict:
    # This creates the top-level trace that groups all sub-operations
    classification = classify_input(raw_input)  # Traced
    processing = process_by_type(classification)  # Traced (includes LLM calls)
    saving = save_to_notion(processing, dry_run)  # Traced
    
    return {
        "classification": classification,
        "processing": processing, 
        "saving": saving
    }
```

## Implementation Checklist

### Phase 1: Immediate (1-2 hours)
- [ ] Install langsmith client wrappers: `pip install langsmith`
- [ ] Update `parse_url_tool.py` with `wrap_anthropic()` 
- [ ] Add `@traceable` decorators to LLM functions
- [ ] Test trace visibility in LangSmith UI
- [ ] Verify prompt/response capture

### Phase 2: Short-term (1-2 days)  
- [ ] Extract hardcoded prompt to version-controlled files
- [ ] Implement hybrid prompt loading system (git + LangSmith experiments)
- [ ] Create prompt versioning utilities with semantic versions
- [ ] Set up feature flag for experimental prompt override
- [ ] Test version control → experiment → promotion workflow

### Phase 3: Medium-term (2-3 days)
- [ ] Implement traced fallback logic
- [ ] Add error classification
- [ ] Set up error rate alerts
- [ ] Test error trace hierarchy

### Phase 4: Extended (3-5 days)
- [ ] Implement cost tracking by user/source
- [ ] Set up performance monitoring dashboard
- [ ] Create budget alerts
- [ ] Optimize token usage

### Phase 5: Advanced (1-2 weeks)
- [ ] Set up A/B testing infrastructure
- [ ] Implement quality metrics tracking
- [ ] Create multi-agent trace correlation
- [ ] Build custom monitoring dashboards

## Files to Modify

### High Priority
1. **`langgraph/agents/tools/parse_url_tool.py`** - Core LLM call wrapping
2. **`langgraph/observability/langsmith_config.py`** - Enhanced configuration
3. **`requirements.txt`** - Add langsmith dependencies

### Medium Priority  
4. **`langgraph/pipeline/processors/url_processor.py`** - Pipeline-level tracing
5. **`langgraph/pipeline/smart_pipeline.py`** - Orchestration tracing
6. **`langgraph/main_agent.py`** - Session-level correlation

### Low Priority
7. **`langgraph/agents/tools/classify_tool.py`** - Classification tracing
8. **`langgraph/agents/tools/fetch_url_tool.py`** - URL fetch tracing
9. **`langgraph/agents/tools/save_notion_tool.py`** - Notion save tracing

## Success Metrics

### Immediate (Post Phase 1)
- ✅ LLM calls visible in LangSmith UI with full prompt/response
- ✅ Token usage and cost tracking per call
- ✅ Model parameters logged (temperature, max_tokens)

### Short-term (Post Phase 2)  
- ✅ Prompt versioning in git with semantic versions
- ✅ Hybrid system: version control primary + LangSmith experiments
- ✅ A/B testing capability without production risk
- ✅ Atomic deployment integrity maintained
- ✅ Fail-safe operation without external dependencies

### Medium-term (Post Phase 3-4)
- ✅ Complete error trace hierarchy
- ✅ Cost attribution by user/source
- ✅ Performance regression detection
- ✅ Budget alerts and cost optimization

### Long-term (Post Phase 5)
- ✅ Quality metrics trending
- ✅ Multi-agent workflow observability  
- ✅ Automated performance optimization
- ✅ Production monitoring dashboards

## Risk Mitigation

### Performance Impact
- **Risk:** LangSmith adds latency
- **Reality:** Async trace submission - zero application latency
- **Mitigation:** Monitor performance metrics pre/post implementation

### Cost Increase
- **Risk:** Additional API calls to LangSmith  
- **Mitigation:** LangSmith API calls are minimal vs LLM costs (1:1000 ratio)

### Implementation Complexity
- **Risk:** Breaking existing functionality
- **Mitigation:** Phased rollout with fallback support

### Team Adoption  
- **Risk:** Team doesn't use new observability features
- **Mitigation:** Training sessions + clear documentation + visible value demos

## Next Steps

1. **Immediate:** Start with Phase 1 implementation (wrap_anthropic + @traceable)
2. **Validation:** Test trace visibility with existing trace ID 566e82f7-f8b7-45fb-8eb4-1998ec76fc68
3. **Iteration:** Move through phases based on value delivery and team priorities
4. **Documentation:** Update team documentation with new debugging workflows

This plan transforms your LLM operations from invisible to fully observable, enabling debugging, cost optimization, and prompt engineering capabilities essential for production AI systems.