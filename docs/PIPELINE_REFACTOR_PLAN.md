# SoBored Event Extraction Pipeline Refactor Plan

## Executive Summary

This document outlines the comprehensive refactor of SoBored's event extraction system from a ReAct agent-based approach to an optimized smart pipeline, targeting a **75% performance improvement** (18.37s → <5s) while maintaining or improving accuracy through enhanced LangSmith-based evaluation.

## Current State Analysis

### Performance Issues Identified (LangSmith Trace: 8a19b3ae-0cb3-48ee-9920-e9234125d5c1)
- **Total Execution Time**: 18.37s for simple URL processing
- **Overhead**: 40 LangChain runs for 4 sequential operations
- **Inefficient ReAct Pattern**: Full thought/action/observation cycles for deterministic tasks
- **Unnecessary Classification**: LLM calls for obvious URL inputs
- **Tool Wrapping Overhead**: Simple operations wrapped in complex agent tools

### Architecture Problems
1. **Over-engineered for Simple Tasks**: ReAct agent reasoning for deterministic operations
2. **Sequential Processing**: No parallelization where possible
3. **Redundant Operations**: Multiple prompt templates and parsers per step
4. **Classification Bottleneck**: Always using LLM for input type detection

## Proposed Solution Architecture

### New Smart Pipeline System
```
Input → Smart Classifier → Specialized Processor → Enhanced Tracking → Output
         (3-tier)         (URL/Text/Image)      (LangSmith)
```

### Three-Tier Classification Strategy
1. **Tier 1 - Regex/Heuristic (Instant)**: 95% accuracy for obvious cases
2. **Tier 2 - Simple ML Classifier (Fast)**: 99% accuracy for edge cases  
3. **Tier 3 - LLM Classification (Complex)**: Reserved for truly ambiguous inputs

### Specialized Processors
- **URLProcessor**: Direct fetch → parse → save pipeline
- **TextProcessor**: NLP extraction → save (no agent needed)
- **ImageProcessor**: OCR → structured parsing → save

## Implementation Plan - 4 Phases

### Phase 1: Foundation (1-2 days, Low Risk)
**Objective**: Create new pipeline alongside existing system with feature flags

#### Tasks:
1. **Create New Pipeline Structure**
   ```
   langgraph/pipeline/
   ├── __init__.py
   ├── smart_pipeline.py          # Main pipeline router
   ├── classifiers/
   │   ├── smart_classifier.py    # 3-tier classification
   │   └── patterns.py            # Regex patterns
   ├── processors/
   │   ├── base_processor.py      # Abstract base
   │   ├── url_processor.py       # Optimized URL processing
   │   └── text_processor.py      # Direct text parsing
   └── utils/
       ├── cache.py              # Caching layer
       └── metrics.py            # Performance tracking
   ```

2. **Implement SmartClassifier**
   - Regex patterns for obvious cases (URLs, emails, phone numbers)
   - Fallback to existing classify_input tool
   - A/B test classification accuracy

3. **Create Base Pipeline Classes**
   - `BasePipeline` abstract class with common functionality
   - Shared error handling and logging infrastructure
   - Feature flag integration (`USE_SMART_PIPELINE=true/false`)

4. **Enhanced LangSmith Integration**
   - Structured metadata for easier review
   - Automatic tagging for pipeline comparison
   - Confidence scoring for review prioritization

#### Deliverables:
- Working smart classifier with 95%+ accuracy on obvious inputs
- Base pipeline infrastructure with feature flag support
- Enhanced tracing for both systems
- Initial performance benchmarks

### Phase 2: URL Pipeline Optimization (2-3 days, Medium Risk)
**Objective**: Optimize the highest-impact use case (URL processing)

#### Tasks:
1. **Streamlined URL Processing**
   - Combine fetch + parse operations where possible
   - Async HTTP requests with intelligent retry logic
   - Smart content extraction (structured data first, then LLM fallback)

2. **Intelligent Parsing Strategies**
   ```python
   def parse_url_content_smart(content, title):
       # 1. Try structured data extraction (JSON-LD, microdata)
       structured_data = extract_structured_data(content)
       if structured_data and structured_data.confidence > 0.8:
           return structured_data
           
       # 2. Pattern-based extraction for common event sites
       pattern_result = extract_with_patterns(content, title)
       if pattern_result and pattern_result.confidence > 0.7:
           return pattern_result
           
       # 3. Fallback to LLM parsing for complex cases
       return llm_parse_content(content, title)
   ```

3. **Parallel Processing Implementation**
   - Concurrent URL fetching for multiple links
   - Background Notion saves with confirmation
   - Async processing where possible

4. **Confidence Scoring System**
   - Extraction confidence based on method used
   - Quality indicators for review prioritization
   - Automatic flagging of low-confidence extractions

#### Deliverables:
- URLProcessor with <3s average processing time
- Confidence scoring for all extractions
- 90%+ accuracy maintained or improved
- Parallel processing capabilities

### Phase 3: Advanced Features (3-4 days, Medium Risk)
**Objective**: Add intelligence and performance optimizations

#### Tasks:
1. **Intelligent Caching Layer**
   ```python
   class SmartCache:
       def __init__(self):
           self.url_content_cache = {}  # URL → content mapping
           self.parsed_events_cache = {}  # content_hash → parsed_data
           
       def get_cached_content(self, url):
           # Check if URL content is cached and still valid
           return self.url_content_cache.get(url)
           
       def cache_parsed_event(self, content_hash, parsed_data):
           # Cache parsed results to avoid re-parsing similar content
           self.parsed_events_cache[content_hash] = parsed_data
   ```

2. **Enhanced Text/Image Processing**
   - Direct NLP processing for text inputs (no agent overhead)
   - OCR + structured parsing pipeline for images
   - Batch processing capabilities for multiple inputs

3. **Performance Monitoring Integration**
   - Real-time pipeline execution metrics
   - Performance comparison dashboards
   - Resource usage tracking and optimization

4. **Pattern Learning System**
   - Automatically learn extraction patterns from successful reviews
   - Update regex patterns based on common event formats
   - Adaptive confidence scoring

#### Deliverables:
- Caching system reducing redundant processing by 50%+
- Text and image processors with <2s processing time
- Performance monitoring dashboard
- Adaptive pattern learning system

### Phase 4: Production Readiness (2-3 days, Low Risk)
**Objective**: Complete testing, migration, and cleanup

#### Tasks:
1. **Comprehensive Testing Suite**
   ```python
   # Performance benchmark tests
   def test_pipeline_performance():
       test_cases = [
           "https://eventbrite.com/event/123",
           "Concert tonight at 8PM downtown", 
           "https://facebook.com/events/456"
       ]
       
       for case in test_cases:
           # Compare old vs new system
           assert new_pipeline_time < old_pipeline_time * 0.5
           assert new_accuracy >= old_accuracy
   ```

2. **Migration Strategy**
   - Gradual rollout with user-based feature flags
   - Fallback mechanisms for edge cases
   - Performance monitoring and alerting

3. **Documentation and Cleanup**
   - Update README.md and CLAUDE.md
   - Remove deprecated ReAct agent code
   - Performance optimization guide

4. **Team Training**
   - LangSmith review process training
   - Performance monitoring dashboard usage
   - Troubleshooting guide for new system

#### Deliverables:
- Complete test suite with 95%+ coverage
- Production-ready system with monitoring
- Migration completed successfully
- Team trained on new processes

## LangSmith Integration Strategy

### Enhanced Feedback Collection
1. **Annotation Queues Setup**
   - "Event Extraction Quality Review" queue for all extractions
   - "Urgent Review Queue" for low-confidence extractions
   - Custom rubrics for structured feedback

2. **Automated Dataset Building**
   - High-quality reviews (4-5 stars) → training datasets
   - Failed extractions → improvement targets
   - Edge cases → specialized test cases

3. **Experiment Comparison Framework**
   - Side-by-side comparison of ReAct vs Smart Pipeline
   - Performance metrics tracking over time
   - User satisfaction analysis

### Review Workflow for Internal Teams
1. **Daily Reviews**: Team members review extractions in LangSmith UI
2. **Structured Feedback**: Custom rubrics ensure consistent evaluation
3. **Automatic Improvement**: High-quality examples become training data
4. **Weekly Analysis**: Performance reports and trend analysis

## Expected Outcomes

### Performance Improvements
- **Latency**: 18.37s → <5s (75% improvement)
- **Throughput**: 3x more extractions per minute
- **Resource Usage**: 60% reduction in LLM API calls
- **Reliability**: 99%+ uptime with fallback mechanisms

### Accuracy Improvements
- **Structured Data**: 20% improvement from direct JSON-LD extraction
- **Pattern Recognition**: 15% improvement from learned patterns
- **Confidence Scoring**: Better handling of edge cases
- **User Feedback**: Continuous improvement through LangSmith reviews

### Operational Benefits
- **Easier Debugging**: Clear pipeline stages vs complex agent reasoning
- **Better Monitoring**: Detailed metrics at each processing stage
- **Scalability**: Parallel processing and caching support growth
- **Maintainability**: Simpler codebase with focused responsibilities

## Risk Management

### Technical Risks
- **Accuracy Regression**: Mitigated by A/B testing and gradual rollout
- **Edge Case Handling**: Fallback to ReAct agent for complex cases
- **Integration Issues**: Feature flags allow instant rollback

### Operational Risks  
- **Team Adoption**: Comprehensive training and documentation
- **Review Overhead**: Streamlined LangSmith interface reduces burden
- **Performance Monitoring**: Automated alerts for system health

## Success Metrics

### Performance KPIs
- Average processing time: <5s (target: 3s)
- 95th percentile processing time: <8s
- System uptime: >99.5%
- Error rate: <1%

### Quality KPIs
- Extraction accuracy: >95% (measured via LangSmith reviews)
- User satisfaction: >4.0/5.0 average rating
- Review completion rate: >90% of extractions reviewed within 24h
- Dataset growth: 100+ high-quality examples per week

### Operational KPIs
- Code complexity: 50% reduction in lines of code
- API costs: 60% reduction in LLM usage
- Developer velocity: 2x faster feature development
- Time to resolution: 75% faster debugging

## Timeline Summary

| Phase | Duration | Risk Level | Key Deliverables |
|-------|----------|------------|------------------|
| Phase 1 | 1-2 days | Low | Foundation, Smart Classifier, Feature Flags |
| Phase 2 | 2-3 days | Medium | URL Pipeline, Confidence Scoring |
| Phase 3 | 3-4 days | Medium | Caching, Advanced Features, Monitoring |
| Phase 4 | 2-3 days | Low | Testing, Migration, Documentation |
| **Total** | **8-12 days** | **Low-Medium** | **Production-Ready Smart Pipeline** |

## Conclusion

This refactor addresses the core inefficiencies identified in the current ReAct agent system while maintaining the sophisticated evaluation and feedback capabilities through LangSmith integration. The phased approach ensures minimal risk while delivering significant performance improvements and better user experience.

The combination of technical optimization and enhanced evaluation processes positions SoBored for improved accuracy, scalability, and maintainability as the system grows.