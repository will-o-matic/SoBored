# LangSmith User Guide for SoBored Event Extraction Review

This guide explains how internal team members will use LangSmith's web interface to review and improve the accuracy of our event extraction system.

## Overview

As an internal reviewer, you'll help improve our AI event extraction system by:
- **Reviewing extracted event data** for accuracy
- **Providing structured feedback** through LangSmith's annotation interface  
- **Building high-quality datasets** that improve system performance over time

## Getting Started

### 1. Access LangSmith
- Navigate to [LangSmith](https://smith.langchain.com)
- Login with your team credentials
- You should see the "SoBored" workspace

### 2. Understanding the Interface
The main areas you'll work with:
- **Annotation Queues**: Review pending event extractions
- **Datasets**: View curated examples and ground truth data
- **Experiments**: Compare system performance before/after improvements
- **Traces**: Detailed logs of individual processing runs

## Daily Review Workflow

### Step 1: Access Annotation Queue
1. Navigate to **Annotation Queues** in the left sidebar
2. Select **"Event Extraction Quality Review"** queue
3. You'll see a list of pending reviews with:
   - Original input (URL or text)
   - Extracted event details
   - Confidence scores

### Step 2: Review Event Extraction
For each item in the queue:

**Original Input Display:**
- Source URL or raw text input
- User ID and timestamp
- Processing method used

**Extracted Data Review:**
- **Event Title**: Check if the title is accurate and complete
- **Date/Time**: Verify the date and time are correct
- **Location**: Confirm venue/location is properly extracted  
- **Description**: Assess if description is relevant and complete

### Step 3: Provide Structured Feedback
Use the feedback form on the right side:

#### Title Accuracy
- ✅ **Correct**: Perfect extraction
- ⚠️ **Partially Correct**: Minor issues (e.g., truncated, extra words)
- ❌ **Incorrect**: Wrong title extracted
- 🚫 **Missing**: No title found when one exists

#### Date/Time Accuracy  
- ✅ **Correct**: Accurate date and time
- ⚠️ **Partially Correct**: Right date, wrong time (or vice versa)
- ❌ **Incorrect**: Wrong date/time
- 🚫 **Missing**: No date found when one exists

#### Location Accuracy
- ✅ **Correct**: Accurate venue/location
- ⚠️ **Partially Correct**: Close but incomplete (e.g., missing address)
- ❌ **Incorrect**: Wrong location
- 🚫 **Missing**: No location found when one exists

#### Overall Quality (1-5 Rating)
- **5**: Excellent - All information perfectly extracted
- **4**: Good - Minor issues that don't affect usability
- **3**: Fair - Some important information missing/incorrect
- **2**: Poor - Significant problems with extraction
- **1**: Very Poor - Mostly incorrect or unusable

#### Corrections Needed (Text Field)
Provide specific corrections:
```
Title should be: "David Zinn Chalk Art Workshop"
Date should be: "June 15, 2025 at 5:00 PM" (not just "June 15")  
Location should include: "Top of the Park, Ann Arbor, MI"
```

### Step 4: Complete Review
1. Click **"Mark as Done"** when finished
2. High-quality examples (rating 4-5) automatically become training data
3. Items needing corrections will be flagged for system improvement

## Advanced Features

### Priority Queue
Items requiring urgent review appear in **"Urgent Review Queue"**:
- Low confidence extractions (< 70%)
- Complex or unusual input formats
- Previously flagged problematic patterns

### Dataset Building
Your reviews help build datasets:
- **High Quality Extractions**: Examples rated 4-5 stars
- **Common Failure Patterns**: Examples needing improvement
- **Edge Cases**: Unusual inputs that challenge the system

### Experiment Participation
You may be asked to review during A/B tests:
- **ReAct Agent Baseline**: Current system results
- **Smart Pipeline**: New optimized system results  
- Side-by-side comparison to measure improvement

## Review Best Practices

### What Makes Good Feedback
1. **Be Specific**: Instead of "wrong date", write "should be June 15, 2025"
2. **Consider Context**: Some venues have multiple locations - specify which one
3. **Check Original Source**: Review the source URL/text to understand available information
4. **Note Patterns**: If you see repeated issues, mention them in corrections

### Common Issues to Watch For
- **Date Formats**: MM/DD vs DD/MM confusion
- **Time Zones**: EST vs local time handling
- **Venue Names**: Official names vs common names
- **Recurring Events**: Multiple dates vs single occurrence
- **Virtual Events**: Online vs physical location handling

### Quality Standards
- **Title**: Should be the official event name as it appears on the source
- **Date/Time**: Must include both date and time when available
- **Location**: Should be specific enough for someone to find the venue
- **Description**: Should capture key event details without excessive marketing copy

## Metrics and Impact

### Your Review Impact
- **Accuracy Improvement**: Track how your feedback improves extraction quality
- **Dataset Growth**: Watch the training dataset grow from your reviews
- **System Performance**: See overall system speed and accuracy improvements

### Weekly Reports
You'll receive summaries showing:
- Number of reviews completed
- Quality trends in extractions
- Common improvement areas identified
- System performance improvements

## Getting Help

### Questions About Reviews
- **Unclear extractions**: If you're unsure about accuracy, err on the side of "partially correct" and explain in comments
- **Missing information**: If source doesn't contain certain details, that's not an extraction error
- **Technical issues**: Contact the development team for LangSmith access problems

### Feedback on This Process
- Suggest improvements to the review interface
- Request additional feedback categories
- Report any recurring patterns that need attention

---

**Remember**: Your reviews directly improve the system for all users. Quality feedback helps build better event extraction and saves everyone time in the long run!