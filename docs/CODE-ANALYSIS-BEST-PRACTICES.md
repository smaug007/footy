# Code Analysis Best Practices: Universal Guidelines

**Purpose:** Universal guidelines for analyzing code accurately and avoiding common mistakes  
**Applies To:** Any code analysis, assessment, or technical review  
**Origin:** Lessons from migration analysis (Jan 2025), generalized for all situations  
**Last Updated:** January 13, 2025

---

## 🎯 WHEN TO USE THIS DOCUMENT

**Use this guide whenever you need to:**
- Analyze existing code to understand how it works
- Assess completion percentage of any feature
- Determine which code paths are active vs unused
- Verify claims about code behavior
- Perform technical due diligence
- Review another developer's work
- Make architectural decisions
- Debug production issues

**In other words:** Anytime you need to make claims about code based on analysis.

---

## ⚡ THE GOLDEN RULE

> **"Code that exists in the repository is not the same as code that executes in production."**

**Always verify:**
- What code exists (static analysis)
- What code actually runs (dynamic analysis)
- What code is called from where (call graph)

**Never assume:**
- Existence implies usage
- File/class name indicates implementation
- Comments reflect reality
- Previous helper's analysis is complete

---

## 🚫 THE FIVE DEADLY SINS OF CODE ANALYSIS

### Sin #1: Assuming Existence = Usage

**The Mistake:**
```
"This method exists in the codebase
   → Therefore it must be used
   → Wrong!"
```

**The Reality:**
```
Codebase contains:
├─ Active code (runs in production)
├─ Dead code (never called)
├─ Deprecated code (kept for compatibility)
├─ Test code (only in tests)
└─ Future code (not yet wired up)
```

**How to Avoid:**
1. Find method/class definition ✓
2. **Search for all usages** ✓✓✓
3. If zero usages → probably dead code
4. If found usages → verify they're in production paths

**Universal Check:**
```bash
# Always search for actual usage
grep -r "methodName(" src/
grep -r "ClassName(" src/
grep -r "\.functionName\(" src/
```

---

### Sin #2: Trusting Names Instead of Reading Code

**The Mistake:**
```
"This is called LegacyRepository
   → So it must use legacy system
   → Wrong!"
```

**The Reality:**
```kotlin
class LegacyRepository {  // Name says "legacy"
    fun process() {
        newSystemManager.handle()  // But uses new system!
    }
}
```

**How to Avoid:**
1. Never judge by name alone
2. **Always read the actual implementation**
3. Names can be outdated, misleading, or ironic
4. Code is truth, names are hints

**Universal Rule:**
> "Don't trust the sign on the door. Look inside the room."

---

### Sin #3: Static Analysis Without Call Graph Verification

**The Mistake:**
```
"This method calls the old API
   → Wrong assumption: This method runs in production"
```

**The Reality:**
```
Method exists and calls old API ✓
But method is never called ✗
Therefore old API not used ✓
```

**How to Avoid:**
```
┌─────────────────────┐
│ 1. Find definition  │
│ 2. Check what it does│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. WHO CALLS THIS?  │ ← CRITICAL STEP
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Trace call path  │
│ 5. Make conclusion  │
└─────────────────────┘
```

**Universal Pattern:**
```
Definition → Usage → Call Path → Conclusion
(not: Definition → Conclusion)
```

---

### Sin #4: Generalizing From Limited Evidence

**The Mistake:**
```
"I found 3 examples of pattern X
   → Therefore entire system uses pattern X
   → Wrong!"
```

**The Reality:**
```
Found 3 examples of X ✓
Didn't search for Y ✗
System actually uses mix of X and Y
```

**How to Avoid:**
1. Search exhaustively, not selectively
2. Look for counter-examples
3. Search for alternatives
4. Count total instances

**Universal Rule:**
> "Don't stop at first evidence. Search for ALL evidence."

**Example:**
```bash
# Not just this:
grep -r "oldMethod(" src/

# Also search for alternatives:
grep -r "newMethod(" src/
grep -r "alternativeMethod(" src/

# Then compare counts
```

---

### Sin #5: Not Verifying When Claims Conflict

**The Mistake:**
```
Person A: "System uses approach X"
Person B: "System uses approach Y"
You: Pick one to believe → Wrong!
```

**The Reality:**
```
Both could be right (system uses both)
Both could be wrong (system uses Z)
One could be right (partial knowledge)
```

**How to Avoid:**
1. Don't pick sides
2. **Go to source code independently**
3. Verify both claims with evidence
4. Document what you find
5. Draw your own conclusion

**Universal Rule:**
> "When analyses conflict, trust nobody. Verify everything."

---

## ✅ THE VERIFICATION METHODOLOGY

### Step 1: Define Your Question

**Bad Question:**
"How does this work?"

**Good Question:**
"When user clicks button X in screen Y, which database table gets updated?"

**Template:**
```
WHEN: [trigger/entry point]
WHO: [what component/actor]
DOES: [what action]
TO: [what target/affected component]
```

---

### Step 2: Identify Entry Points

**Common Entry Points:**
- User actions (UI clicks, API calls)
- Scheduled jobs (cron, workers)
- Event handlers (listeners, callbacks)
- Lifecycle methods (onCreate, init)
- Public APIs (exposed endpoints)

**Find them:**
```bash
# UI entry points
grep -r "onClick" src/
grep -r "@GetMapping" src/
grep -r "eventListener" src/

# Background entry points
grep -r "@Scheduled" src/
grep -r "Worker" src/
```

---

### Step 3: Trace The Execution Path

**Complete Trace Template:**
```
Entry Point:
├─ File: [EntryPointFile.ext]
├─ Line: [123]
└─ Calls: [methodA()]

Step 1:
├─ File: [ComponentA.ext]
├─ Line: [456]
└─ Calls: [methodB()]

Step 2:
├─ File: [ComponentB.ext]
├─ Line: [789]
└─ Calls: [databaseUpdate()]

Final Action:
├─ File: [DAO.ext]
├─ Line: [101]
└─ Affects: [table_name]
```

**Verification at Each Step:**
```bash
# Verify each call exists
grep -n "methodA(" src/ComponentA.ext
grep -n "methodB(" src/ComponentB.ext
```

---

### Step 4: Document Evidence

**Evidence Template:**
```markdown
## Claim: [What you're claiming]

### Evidence Chain:
1. **Entry Point**
   - File: path/to/file.ext:123
   - Code: `onClick { viewModel.action() }`

2. **ViewModel**
   - File: path/to/ViewModel.ext:456
   - Code: `repository.update()`

3. **Repository**
   - File: path/to/Repository.ext:789
   - Code: `dao.insert()`

4. **DAO**
   - File: path/to/DAO.ext:101
   - Code: `database.table.insert()`

### Verification:
- Search pattern: `\.action\(`
- Results: 3 call sites
- All verified: ✓

### Conclusion:
[Based on evidence above, conclude...]

### Confidence: [X/10]
```

---

## 🔍 UNIVERSAL SEARCH PATTERNS

### For Method Calls

```bash
# Find where methodName is called
grep -r "\.methodName\(" src/

# Case insensitive
grep -ri "\.methodName\(" src/

# With line numbers
grep -rn "\.methodName\(" src/

# Count occurrences
grep -rc "\.methodName\(" src/
```

### For Class Instantiation

```bash
# Find where ClassName is instantiated
grep -r "new ClassName\(" src/
grep -r "ClassName(" src/  # Kotlin style
```

### For Import/Usage

```bash
# Find files that import something
grep -r "import.*ClassName" src/

# Find actual usage after import
grep -r "ClassName\." src/
```

### For Complete Analysis

```bash
# 1. Find all definitions
grep -rn "fun methodName" src/

# 2. Find all usages
grep -rn "\.methodName\(" src/

# 3. Find all references (includes both)
grep -rn "methodName" src/
```

---

## 📋 UNIVERSAL VERIFICATION CHECKLIST

**Before making ANY claim about code:**

### ✅ Evidence Collection
- [ ] I have identified the specific code in question
- [ ] I know the file path and line numbers
- [ ] I have read the actual implementation (not just assumed)
- [ ] I have searched for all usages of this code
- [ ] I have documented my search patterns
- [ ] I have verified search results manually

### ✅ Call Path Verification
- [ ] I know the entry point (where execution starts)
- [ ] I have traced the complete call path
- [ ] I have verified each step in the path
- [ ] I have confirmed the final action/effect
- [ ] I have documented the complete chain

### ✅ Alternative Checking
- [ ] I have searched for alternative implementations
- [ ] I have checked for deprecated vs new versions
- [ ] I have looked for edge cases
- [ ] I have searched for test code separately
- [ ] I have verified which version is active

### ✅ Conclusion Quality
- [ ] My claim is specific (not vague)
- [ ] My claim is qualified (states certainty level)
- [ ] My claim separates facts from interpretation
- [ ] My claim acknowledges what I didn't check
- [ ] My claim includes evidence references

---

## 🎓 UNIVERSAL PRINCIPLES

### Principle 1: Code Is Truth, Everything Else Is Opinion

**Priority Order:**
```
1. Actual code (highest truth)
2. Tests (shows expected behavior)
3. Recent documentation
4. Comments (can be outdated)
5. Variable/class names (hints only)
6. People's recollections (lowest truth)
```

**Rule:**
> "When code and documentation conflict, trust the code."

---

### Principle 2: Absence of Evidence ≠ Evidence of Absence

**Wrong:**
```
"I don't see calls to oldMethod
   → Therefore oldMethod is not used"
```

**Right:**
```
"I searched in [these directories] using [these patterns]
   → Found zero matches
   → Therefore oldMethod not used [in searched areas]"
```

**Always specify:**
- What you searched
- Where you searched
- How you searched
- What you didn't search

---

### Principle 3: Verify, Then Trust

**For any claim made by anyone (including yourself):**

```
1. Ask: "What's the evidence?"
2. Ask: "How was it verified?"
3. Ask: "What wasn't checked?"
4. Verify critical claims yourself
5. Then and only then, trust
```

**Even for your own work:**
- Write down your claim
- Sleep on it
- Re-verify next day
- Revise if needed

---

### Principle 4: Qualify All Claims

**Bad Claims (Absolute):**
- "This system uses X"
- "All operations do Y"
- "Nobody calls Z"

**Good Claims (Qualified):**
- "This system uses X for [specific operations] (verified)"
- "All UI operations do Y (verified). Background operations not checked."
- "I found zero calls to Z in [searched directories] (search pattern: [...])"

**Template:**
```
"[System/Component] does [action] 
  in [these cases] (verified)
  [these cases] not verified yet"
```

---

### Principle 5: Document Your Methodology

**Always include:**
- How you analyzed
- What tools you used
- What patterns you searched
- What you found
- What you concluded

**Why:**
- Others can verify your work
- You can retrace your steps
- Errors are easier to catch
- Analysis is reproducible

---

### Principle 6: Quantify Your Findings

**Bad (Vague):**
- "Most operations use new system"
- "Some legacy code remains"
- "Partially migrated"

**Good (Quantified):**
- "8/10 operations use new system (80%)"
- "3 legacy methods remain (15% of total methods)"
- "Runtime: 100% migrated, UI: 80% migrated"

**Always Count:**
```
Total instances: [N]
├─ Using approach A: [X] ([X/N]%)
├─ Using approach B: [Y] ([Y/N]%)
└─ Unknown/Unchecked: [Z] ([Z/N]%)
```

**Template for Completion Analysis:**
```markdown
## Feature X Analysis

### Operations Inventory:
1. Operation A: ✓ Uses new system
2. Operation B: ✓ Uses new system  
3. Operation C: ✗ Uses legacy system
4. Operation D: ? Not yet verified

### Quantified Status:
- Total operations: 4
- Using new system: 2 (50%)
- Using legacy: 1 (25%)
- Unverified: 1 (25%)

### Conclusion:
System is 50% migrated (verified)
25% requires migration
25% needs verification
```

**Red Flag:**
⚠️ If you use words like "mostly", "some", "partially" without numbers, quantify them!

**Why Quantify:**
- Numbers are falsifiable (others can verify)
- Forces complete analysis (can't count without finding all)
- Prevents vague claims
- Shows actual progress
- Easy to track over time

---

## 🛠️ UNIVERSAL TOOLS & TECHNIQUES

### Code Search Tools

**Command Line:**
```bash
# grep (universal)
grep -r "pattern" directory/

# ripgrep (faster)
rg "pattern" directory/

# ag (silver searcher)
ag "pattern" directory/
```

**IDE Tools:**
- Find Usages / Find References
- Call Hierarchy / Caller Hierarchy
- Find in Files / Global Search
- Go to Implementation

**Use Both:**
- Command line for broad searches
- IDE for precise navigation
- Manual reading for verification

---

### Analysis Techniques

**1. Top-Down Analysis:**
```
Start: User entry point
↓
Trace: Call by call downward
↓
End: Final action/side effect
```

**2. Bottom-Up Analysis:**
```
Start: Database/file/API
↓
Trace: Who calls this?
↓
End: Entry points
```

**3. Dependency Analysis:**
```
Component A
├─ uses B
├─ uses C
└─ B uses D

Map all dependencies
Find critical paths
```

**4. Diff Analysis:**
```
Compare:
- Old vs New implementation
- Version A vs Version B
- Expected vs Actual

Find: What changed?
```

---

## 💬 UNIVERSAL COMMUNICATION GUIDELINES

### How to State Findings

**Structure:**
```markdown
## Finding: [What you discovered]

### Evidence:
- [Specific file:line references]
- [Code snippets]
- [Search results]

### Methodology:
- [How you found it]
- [What you searched]
- [Tools used]

### Confidence: [X/10]
- Certain about: [...]
- Uncertain about: [...]
- Didn't check: [...]
```

---

### How to Handle Conflicting Information

**When Claims Conflict:**

```markdown
## Conflict Analysis

### Claim A (Source: [person/doc])
"[The claim]"

### Claim B (Source: [person/doc])
"[The claim]"

### Independent Verification:
[Your analysis]

### Findings:
- Claim A: [Accurate/Inaccurate because...]
- Claim B: [Accurate/Inaccurate because...]

### Actual State:
[What code actually does]
```

---

### How to Admit Uncertainty

**Good Uncertainty Statements:**
- "I verified X, but haven't checked Y yet"
- "My analysis covers [scope]. Outside that: unknown"
- "I'm confident about A (10/10), uncertain about B (5/10)"
- "I need to verify C before making claims about D"

**Bad Uncertainty Avoidance:**
- "It probably works like X" (qualify this!)
- "I think it uses Y" (verify before claiming!)
- "It seems to do Z" (vague and unverified)

---

## 🎯 APPLYING TO NEW SITUATIONS

### Generic Application Template

**1. Define the Question**
```
What am I trying to determine?
- Specific enough to verify? ✓/✗
- Falsifiable? ✓/✗
- Clear scope? ✓/✗
```

**2. Plan the Analysis**
```
Entry points: [where to start]
Search patterns: [what to look for]
Expected findings: [what would prove/disprove]
```

**3. Execute the Analysis**
```
For each component:
- Read implementation ✓
- Find all usages ✓
- Trace call paths ✓
- Document findings ✓
```

**4. Verify the Findings**
```
Cross-check with:
- Multiple search methods
- Multiple sources
- Edge cases
- Counter-examples
```

**5. State the Conclusion**
```
Based on: [evidence]
I conclude: [finding]
Confidence: [level]
Didn't check: [scope limits]
```

---

## 🚨 RED FLAGS & WARNING SIGNS

### Code Analysis Red Flags

**⚠️ You might be wrong if:**
- You can't find the actual code for your claim
- Your evidence is "I think" or "probably"
- You didn't search for alternative implementations
- You didn't verify call sites
- You can't provide file:line references
- Your analysis relies on names, not code
- You found evidence but didn't count occurrences
- Claims conflict and you didn't verify both

### Methodology Red Flags

**⚠️ Your analysis might be flawed if:**
- You made conclusions quickly (<30 min analysis)
- You didn't use multiple search methods
- You didn't trace complete call paths
- You assumed instead of verified
- You stopped at first evidence found
- You didn't check for dead code
- You relied on someone else's analysis
- You can't reproduce your findings

---

## 📚 UNIVERSAL EXAMPLES

### Example 1: Determining Feature Usage

**Question:** "Is feature X still used in production?"

**Wrong Approach:**
```
1. Find FeatureX code
2. See it exists
3. Conclude: "Yes, used in production" ❌
```

**Right Approach:**
```
1. Find FeatureX code
2. Search for:
   - FeatureX instantiation
   - FeatureX method calls
   - FeatureX imports
3. Trace each call to entry point
4. Check if entry points are active
5. Conclude: "Used in [these paths], not used in [these paths]" ✓
```

---

### Example 2: Assessing Migration Completion

**Question:** "Is migration from System A to System B complete?"

**Wrong Approach:**
```
1. See new System B code
2. See some A→B conversions
3. Conclude: "Migration complete" ❌
```

**Right Approach:**
```
1. List all operations (add, remove, update, etc.)
2. For each operation:
   - Find implementation
   - Find usage
   - Check if uses A or B
   - Document findings
3. Count: X% uses B, Y% uses A
4. Conclude: "X% complete, Y% remaining" ✓
```

---

### Example 3: Understanding Code Flow

**Question:** "What happens when user clicks button X?"

**Wrong Approach:**
```
1. Find onClick handler
2. See it calls methodY
3. Conclude: "methodY executes" ❌
(Missed: What does methodY do?)
```

**Right Approach:**
```
1. Find onClick handler
2. Trace: onClick → methodY
3. Trace: methodY → methodZ
4. Trace: methodZ → database.update
5. Document complete path
6. Conclude: "Clicking X updates database table T" ✓
```

---

## 🎓 FINAL WISDOM

### The Three Questions

**Before claiming anything, ask:**

1. **"What's my evidence?"**
   - Specific files and line numbers
   - Actual code snippets
   - Search results

2. **"How did I verify it?"**
   - Search patterns used
   - Tools employed
   - Manual checks performed

3. **"What didn't I check?"**
   - Scope limitations
   - Alternative implementations
   - Edge cases

**If you can't answer all three, your analysis is incomplete.**

---

### The Core Truth

> **"In code analysis, there are no shortcuts to verification."**

**You must:**
- Read the actual code
- Search for actual usage
- Trace actual paths
- Document actual evidence

**You cannot:**
- Trust names
- Assume usage
- Skip verification
- Rely only on others' analysis

---

### When to Use This Document

**Use this checklist for:**
- ✅ Code reviews
- ✅ Feature assessments
- ✅ Migration analysis
- ✅ Bug investigations
- ✅ Performance optimization
- ✅ Security audits
- ✅ Technical due diligence
- ✅ Architecture decisions
- ✅ **ANY situation requiring code analysis**

---

## 📖 HOW TO REFERENCE THIS DOCUMENT

### For Yourself:

**Before any analysis:**
> "Let me review CODE-ANALYSIS-BEST-PRACTICES.md to avoid common mistakes"

**When uncertain:**
> "Does my analysis follow the verification methodology?"

**After analysis:**
> "Did I complete the Universal Verification Checklist?"

---

### For Others:

**When requesting analysis:**
> "Please analyze X following CODE-ANALYSIS-BEST-PRACTICES.md"

**When reviewing analysis:**
> "Does this meet the standards in CODE-ANALYSIS-BEST-PRACTICES.md?"

**When providing feedback:**
> "Review CODE-ANALYSIS-BEST-PRACTICES.md section on [topic]"

---

## 🔄 MAINTAINING THIS DOCUMENT

**Add to this document when:**
- You discover a new analysis mistake
- You find a better verification method
- You encounter a new edge case
- You develop a useful template
- You find a better tool

**Keep it:**
- Universal (not project-specific)
- Practical (actionable advice)
- Evidence-based (real examples)
- Up-to-date (review quarterly)

---

## ✅ QUICK START GUIDE

**For any code analysis task:**

1. **Read this document** (15 minutes)
2. **Complete the checklist** (as you work)
3. **Document using templates** (evidence-based)
4. **Review before claiming** (self-check)
5. **Revise if needed** (continuous improvement)

**Remember:**
> "Taking 30 minutes to verify properly is better than spending 3 hours correcting wrong analysis."

---

**Document Version:** 1.1  
**Last Updated:** January 13, 2025  
**Based On:** Real analysis mistakes, generalized for universal application  
**Applies To:** Any code analysis situation in any programming language or framework

---

# 📎 APPENDICES: DOMAIN-SPECIFIC GUIDANCE

**Note:** The following appendices provide specialized guidance for specific environments. They are **optional** and should only be applied when relevant to your context. The core principles in the main document are universal and always apply.

---

## APPENDIX A: Data Flow Analysis 🗄️

### When This Appendix Applies:

Use this guidance when working in:
- **ETL/Data Pipeline Systems** - Data transformations, aggregations, migrations
- **Financial Systems** - Money flow, transaction processing, audit trails
- **Data-Intensive Applications** - Large data processing, analytics systems
- **Database Migration Projects** - Moving data between systems
- **API Integration** - Data format conversions, mapping between systems
- **GDPR/Privacy Compliance** - Tracking personal data through system

**If your analysis involves understanding WHERE data goes and HOW it transforms, use this appendix.**

---

### Core Principle: Data ≠ Code

**The Key Difference:**
```
Code Execution Flow:
User clicks → Method A → Method B → Method C
(Focuses on WHAT code runs)

Data Flow:
User Input → Validation → Transform → Store
(Focuses on WHAT HAPPENS TO DATA)
```

**Why Both Matter:**
- Code flow: Shows which methods execute
- Data flow: Shows what data gets modified where
- **You need both for complete analysis** ✅

---

### The Data Flow Verification Method

**Step 1: Identify Data Origin**

**Questions to Answer:**
- Where does the data come from?
- What triggers data creation?
- What format is it in?
- What are the data's properties?

**Search Patterns:**
```bash
# Find data creation points
grep -r "new DataObject" src/
grep -r "create.*Data" src/
grep -r "UserInput\|FormData\|RequestBody" src/

# Find data reads (database/API)
grep -r "\.get.*\|\.fetch.*\|\.read.*" src/
grep -r "SELECT.*FROM" src/
```

**Documentation Template:**
```markdown
## Data Origin: [DataName]

### Source:
- Entry Point: [file.ext:line]
- Trigger: [User action/Event/Schedule]
- Initial Format: [JSON/XML/Object/Raw]
- Fields: [field1, field2, ...]

### Example:
```language
val userData = UserRegistrationForm(
    email = input.email,
    password = input.password,
    name = input.name
)
```
```

---

**Step 2: Trace Data Transformations**

**Questions to Answer:**
- How is data modified?
- What validations are applied?
- What fields are added/removed/changed?
- Are there side effects?

**Search Patterns:**
```bash
# Find transformations
grep -r "\.map\|\.transform\|\.convert" src/
grep -r "validate.*\|sanitize.*\|normalize.*" src/

# Find mutations
grep -r "\.set.*\|\.update.*\|\.modify.*" src/
```

**Documentation Template:**
```markdown
## Data Transformation Chain

### Step 1: Validation
- File: [path/to/validator.ext:line]
- Action: Email format check, password strength
- Changes: None (validation only)
- On Failure: Throws ValidationException

### Step 2: Sanitization
- File: [path/to/sanitizer.ext:line]
- Action: Trim whitespace, escape HTML
- Changes: email and name fields modified
- Result: Safe for database storage

### Step 3: Enrichment
- File: [path/to/enricher.ext:line]
- Action: Add timestamp, generate UUID
- Changes: Added `id`, `createdAt`, `updatedAt`
- Result: Complete user entity

### Example Flow:
```language
// Original
{ email: " user@test.com ", password: "pass123" }

// After validation ✓
{ email: " user@test.com ", password: "pass123" }

// After sanitization
{ email: "user@test.com", password: "[HASHED]" }

// After enrichment
{ 
  id: "uuid-123",
  email: "user@test.com",
  password: "[HASHED]",
  createdAt: 1234567890,
  updatedAt: 1234567890
}
```
```

---

**Step 3: Identify Data Destinations**

**Questions to Answer:**
- Where does data end up?
- What storage systems are involved?
- Is data sent to external services?
- Are there multiple destinations?

**Search Patterns:**
```bash
# Database writes
grep -r "\.insert\|\.save\|\.create\|\.update" src/
grep -r "INSERT INTO\|UPDATE.*SET" src/

# External calls
grep -r "\.post\|\.put\|\.send" src/
grep -r "httpClient\|apiService\|restTemplate" src/

# File writes
grep -r "\.write\|\.writeFile\|\.append" src/
```

**Documentation Template:**
```markdown
## Data Destinations

### Primary Storage: Database
- Table: `users`
- Columns: `id`, `email`, `password_hash`, `name`, `created_at`
- File: [path/to/dao.ext:line]
- Method: `userDao.insert(user)`

### Secondary Storage: Cache
- System: Redis
- Key: `user:{id}`
- TTL: 3600 seconds
- File: [path/to/cache.ext:line]
- Method: `cache.set("user:${id}", user, 3600)`

### External Service: Email System
- Service: SendGrid API
- Endpoint: POST /v3/mail/send
- Data Sent: email, name (NOT password)
- File: [path/to/email-service.ext:line]
- Method: `emailService.sendWelcome(user.email, user.name)`
```

---

**Step 4: Verify Data Consistency**

**Critical Questions:**
- Is the same data stored in multiple places?
- Are all destinations getting the same data?
- Is there potential for data inconsistency?
- What happens if one destination fails?

**Verification Template:**
```markdown
## Data Consistency Check

### Data: User Registration

#### Destination 1: PostgreSQL `users` table
- Fields stored: id, email, password_hash, name, created_at
- Transaction: Yes
- Rollback on error: Yes ✓

#### Destination 2: Redis cache
- Fields stored: id, email, name (no password)
- Transaction: No
- Rollback on error: No ✗

#### Destination 3: Elasticsearch `users` index
- Fields stored: id, email, name (for search)
- Transaction: No
- Async: Yes (queue-based)
- Rollback on error: No ✗

### Consistency Analysis:
⚠️ **RISK: Potential inconsistency detected**

Scenario: PostgreSQL succeeds, Redis fails
- Database has user ✓
- Cache missing user ✗
- Elasticsearch eventually consistent ⚠️

**Mitigation:** 
- Cache miss falls back to database ✓
- Elasticsearch rebuild scheduled nightly ✓
- Acceptable risk for non-critical data ✓
```

---

### Complete Data Flow Template

```markdown
## Data Flow Analysis: [Feature/Operation Name]

### Overview:
[Brief description of what data flows through the system]

---

### 1. DATA ORIGIN

**Entry Point:**
- File: [path/to/file.ext:123]
- Trigger: [User action/Event/API call]
- Format: [Initial data structure]

**Initial Data:**
```language
{
  field1: value1,
  field2: value2
}
```

**Verification:**
- [ ] Identified all entry points
- [ ] Documented initial format
- [ ] Verified data source authenticity

---

### 2. TRANSFORMATION CHAIN

**Transform 1: [Name]**
- File: [path/to/transformer1.ext:line]
- Action: [What it does]
- Input: [Data structure before]
- Output: [Data structure after]
- Side Effects: [Any side effects]

**Transform 2: [Name]**
- File: [path/to/transformer2.ext:line]
- Action: [What it does]
- Input: [Data structure before]
- Output: [Data structure after]
- Side Effects: [Any side effects]

**Verification:**
- [ ] Traced all transformations
- [ ] Documented format changes
- [ ] Identified side effects
- [ ] Checked validation logic

---

### 3. DATA DESTINATIONS

**Destination 1: [Storage System 1]**
- Type: [Database/Cache/File/API]
- Location: [Table/Key/Path/Endpoint]
- Fields: [What gets stored]
- File: [path/to/storage.ext:line]
- Transactional: [Yes/No]

**Destination 2: [Storage System 2]**
- Type: [Database/Cache/File/API]
- Location: [Table/Key/Path/Endpoint]
- Fields: [What gets stored]
- File: [path/to/storage.ext:line]
- Transactional: [Yes/No]

**Verification:**
- [ ] Identified all destinations
- [ ] Documented what gets stored where
- [ ] Checked transaction boundaries
- [ ] Verified error handling

---

### 4. CONSISTENCY ANALYSIS

**Multiple Destinations:** [Yes/No]

**If Yes:**
- Consistency Model: [Strong/Eventual/Best-effort]
- Transaction Scope: [Which destinations are transactional]
- Failure Handling: [What happens if one fails]
- Rollback Strategy: [How inconsistencies are handled]

**Risks Identified:**
- ⚠️ [Risk 1 description]
- ⚠️ [Risk 2 description]

**Mitigations:**
- ✅ [Mitigation 1]
- ✅ [Mitigation 2]

**Verification:**
- [ ] Identified consistency requirements
- [ ] Checked transaction boundaries
- [ ] Verified rollback mechanisms
- [ ] Documented acceptable risks

---

### 5. COMPLETE FLOW DIAGRAM

```
[User Input]
     ↓
[Validation] → file.ext:line
     ↓
[Sanitization] → file.ext:line
     ↓
[Enrichment] → file.ext:line
     ↓
     ├─→ [Database] → file.ext:line
     ├─→ [Cache] → file.ext:line
     └─→ [External API] → file.ext:line
```

---

### 6. CRITICAL FINDINGS

**Data Sensitivity:**
- Contains PII: [Yes/No]
- Contains passwords: [Yes/No]
- GDPR applicable: [Yes/No]

**Security Concerns:**
- [ ] Passwords properly hashed
- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit
- [ ] PII properly masked in logs

**Performance Concerns:**
- [ ] Large data transformations identified
- [ ] Blocking operations noted
- [ ] Async opportunities identified

---

### Confidence: [X/10]

**Certain About:**
- [What was thoroughly verified]

**Uncertain About:**
- [What needs more investigation]

**Didn't Check:**
- [Out of scope items]
```

---

### Data Flow Checklist

**Before claiming you understand data flow:**

#### ✅ Origin Verification
- [ ] I know where data enters the system
- [ ] I know the initial format
- [ ] I know what triggers data creation
- [ ] I have documented the entry points

#### ✅ Transformation Verification
- [ ] I have traced all transformations
- [ ] I understand what each transformation does
- [ ] I know the format at each stage
- [ ] I have identified all side effects
- [ ] I have checked validation logic

#### ✅ Destination Verification
- [ ] I know all places data gets stored
- [ ] I know what fields go where
- [ ] I have verified database tables/columns
- [ ] I have checked external API calls
- [ ] I have documented storage methods

#### ✅ Consistency Verification
- [ ] I know if data goes to multiple places
- [ ] I understand the consistency model
- [ ] I have checked transaction boundaries
- [ ] I have verified error handling
- [ ] I have identified inconsistency risks

#### ✅ Security/Privacy Verification
- [ ] I have identified sensitive data
- [ ] I have checked encryption
- [ ] I have verified password handling
- [ ] I have checked PII handling
- [ ] I have reviewed audit trail

---

### Common Data Flow Mistakes

**❌ Mistake #1: Assuming Single Destination**
```
Wrong: "Data goes to database"
Right: "Data goes to:
  - PostgreSQL users table ✓
  - Redis cache ✓  
  - Elasticsearch index ✓
  - Email service API ✓"
```

**❌ Mistake #2: Missing Transformations**
```
Wrong: "User input → Database"
Right: "User input → Validation → Sanitization → 
       Password Hashing → Enrichment → Database"
```

**❌ Mistake #3: Ignoring Side Effects**
```
Wrong: "Data gets validated"
Right: "Data gets validated AND:
  - Failed validation logged to monitoring ✓
  - Metrics counter incremented ✓
  - User notified via email ✓"
```

**❌ Mistake #4: Not Checking Data Loss**
```
Wrong: "10 fields input, 8 fields stored - looks fine"
Right: "10 fields input, 8 fields stored:
  - Which 2 fields dropped? password (correct), confirmPassword (correct)
  - Why dropped? Password hashed, confirm not needed ✓
  - Intentional or bug? Intentional ✓"
```

---

### Integration With Core Principles

**Data flow analysis STILL requires:**
- ✅ Sin #1 Prevention: Verify code that handles data actually runs
- ✅ Sin #3 Prevention: Trace complete call path for each transformation
- ✅ Principle 2: Document what data flows you didn't trace
- ✅ Principle 4: Qualify claims ("Data flows to X when Y condition")
- ✅ Principle 5: Document your methodology
- ✅ Principle 6: Quantify (8/10 data fields persisted, 2/10 dropped)

**This appendix provides:** Data-specific templates and questions  
**Core document provides:** Universal verification principles

---

## APPENDIX B: Configuration & Environment-Dependent Code Analysis ⚙️

### When This Appendix Applies:

Use this guidance when working in:
- **Feature Flag Systems** - A/B testing, gradual rollouts, remote config
- **Multi-Tenant Applications** - Different behavior per customer/tenant
- **Multi-Environment Systems** - Different behavior in dev/staging/prod
- **Enterprise Software** - Customer-specific configurations
- **SaaS Platforms** - Dynamic feature enablement
- **Mobile Apps** - Remote configuration, phased rollouts
- **Microservices** - Service-specific configuration

**If code behavior changes based on configuration, environment, or feature flags, use this appendix.**

---

### Core Principle: Code ≠ Behavior

**The Key Problem:**
```kotlin
// This code exists in repository:
fun processPayment() {
    if (FeatureFlags.NEW_PAYMENT_SYSTEM) {
        newPaymentProcessor.process()  // ← Might not run!
    } else {
        legacyPaymentProcessor.process()  // ← Might be what runs!
    }
}

// But which branch actually executes?
// Depends on: Environment, tenant, user, time, etc.
```

**The Trap:**
```
Analyst sees both code paths
Analyst assumes both are active
Analyst analyzes both systems
Reality: Only ONE is active in production
Result: 50% wasted effort analyzing dead code
```

---

### The Configuration-Aware Analysis Method

**Step 1: Identify Configuration Points**

**Common Patterns to Search For:**

```bash
# Feature flags
grep -r "FeatureFlag\|isEnabled\|featureToggle" src/
grep -r "if.*FLAG.*{" src/

# Environment checks
grep -r "BuildConfig\|Environment\|ENV" src/
grep -r "isDevelopment\|isProduction\|isStaging" src/

# Conditional compilation
grep -r "#ifdef\|#if.*DEBUG" src/
grep -r "@VisibleForTesting" src/

# Runtime configuration
grep -r "getConfig\|getProperty\|getSetting" src/
grep -r "SharedPreferences\|UserDefaults" src/

# A/B testing
grep -r "experiment\|variant\|abTest" src/
```

**Documentation Template:**
```markdown
## Configuration Points Identified

### Feature Flags:
1. `FEATURE_NEW_PAYMENT` (file.ext:123)
   - Controls: Payment processor selection
   - Default: false
   - Production value: [UNKNOWN - need to verify]

2. `FEATURE_ENHANCED_SEARCH` (file.ext:456)
   - Controls: Search algorithm version
   - Default: true
   - Production value: true ✓

### Environment Variables:
1. `API_BASE_URL` (file.ext:789)
   - Dev: https://dev-api.example.com
   - Staging: https://staging-api.example.com
   - Prod: https://api.example.com
   
### Build-Time Configuration:
1. `BuildConfig.DEBUG` (file.ext:101)
   - Debug builds: true
   - Release builds: false
   - Production: false ✓
```

---

**Step 2: Determine Active Configuration**

**Questions to Answer:**
- What's the configuration in the environment I'm analyzing?
- How is configuration set? (Code, file, remote, database)
- Can configuration change at runtime?
- Who can change configuration?

**Verification Methods:**

**Method 1: Code Inspection**
```kotlin
// Look for default values
const val DEFAULT_PAYMENT_SYSTEM = "legacy"  // ← Default!

// Look for initialization
init {
    featureFlags = RemoteConfig.getFlags()  // ← Runtime!
}
```

**Method 2: Configuration Files**
```bash
# Search config files
find . -name "*.properties" -o -name "*.yaml" -o -name "*.json"
grep -r "FEATURE_FLAG\|feature.*:" config/

# Check environment-specific configs
ls config/dev.properties
ls config/prod.properties
```

**Method 3: Remote Configuration**
```bash
# Check remote config services
grep -r "FirebaseRemoteConfig\|LaunchDarkly\|ConfigCat" src/

# Check admin panels, configuration APIs
```

**Method 4: Ask/Verify**
- Check production dashboard
- Ask DevOps/SRE team
- Check deployment scripts
- Review environment variables in deployment

**Documentation Template:**
```markdown
## Active Configuration Determination

### Feature: NEW_PAYMENT_SYSTEM

**Configuration Source:**
- Type: Remote (Firebase Remote Config)
- File: PaymentConfig.kt:45
- Refresh: Every 12 hours

**How to Verify:**
1. Check Firebase Console → Remote Config
2. Filter by app: production-android
3. Look for key: "new_payment_system_enabled"

**Current Value (Verified on: 2025-01-13):**
- Production: `false` ✗
- Staging: `true` ✓
- Dev: `true` ✓

**Conclusion:**
Production uses LEGACY payment system.
Staging/Dev use NEW payment system.

**Impact on Analysis:**
⚠️ Analyzing NEW payment system for production = analyzing inactive code!
✅ Focus on LEGACY payment system for production analysis.
```

---

**Step 3: Analyze Active Code Paths Only**

**The Strategy:**
```markdown
1. Determine target environment (usually production)
2. Identify active configuration for that environment
3. Analyze ONLY code that executes with that configuration
4. Document what wasn't analyzed
```

**Example:**

```kotlin
// Code:
fun handlePayment(amount: Double) {
    if (ConfigManager.isEnabled("new_payment_system")) {
        // Branch A: New system
        newPaymentProcessor.process(amount)
        analyticsService.track("new_payment_used")
    } else {
        // Branch B: Legacy system
        legacyPaymentProcessor.process(amount)
        logger.log("legacy_payment", amount)
    }
}
```

**Analysis (Production config: flag = false):**
```markdown
## Payment Processing Analysis (Production)

### Active Configuration:
- new_payment_system: false (verified)

### Active Code Path:
Branch B: Legacy system executes ✓

### Analysis:
- File: PaymentHandler.kt:123
- Method: `legacyPaymentProcessor.process(amount)`
- Destination: [Continue tracing legacy processor]
- Side Effects: Logger writes to file

### NOT Analyzed:
Branch A: New payment system (inactive in production)
- newPaymentProcessor.process() - NOT ANALYZED
- analyticsService.track() - NOT ANALYZED

### If Analyzing New System:
Switch analysis to staging environment where flag = true
```

**Efficiency Gain:**
```
Without config awareness:
- Analyze both branches (2x work)
- 50% of analysis wasted on inactive code

With config awareness:
- Analyze only active branch (1x work)
- 0% wasted effort ✓
```

---

**Step 4: Handle Multi-Configuration Scenarios**

**Complex Configuration Examples:**

**Scenario 1: Per-Tenant Configuration**
```kotlin
fun getFeatures(tenantId: String): Features {
    val tenantConfig = configService.getForTenant(tenantId)
    return Features(
        advancedAnalytics = tenantConfig.hasFeature("analytics"),
        customBranding = tenantConfig.hasFeature("branding")
    )
}
```

**Analysis Approach:**
```markdown
## Multi-Tenant Analysis

### Configuration Model:
- Per-tenant feature flags
- Stored in: tenant_features table
- Retrieved at: Runtime per request

### Analysis Strategy:
Option A: Analyze for specific tenant
  - Choose representative tenant (e.g., largest customer)
  - Document which tenant analyzed
  - State limitations

Option B: Analyze all variations
  - List all unique configurations
  - Analyze each variation
  - Document which combinations tested

### Example (Option A):
Analyzing for Tenant: "enterprise-client-001"
- Advanced Analytics: true ✓
- Custom Branding: true ✓
- Beta Features: false ✗

Code paths analyzed:
- advancedAnalytics branch ✓
- customBranding branch ✓
- Beta features branch ✗ (not analyzed)

Limitations:
- Analysis specific to this tenant configuration
- Other tenants may have different behavior
- 12 other tenant configurations not analyzed
```

**Scenario 2: Gradual Rollout**
```kotlin
fun shouldUseNewFeature(userId: String): Boolean {
    val rolloutPercentage = remoteConfig.getInt("new_feature_rollout")
    val userBucket = userId.hashCode() % 100
    return userBucket < rolloutPercentage
}
```

**Analysis Approach:**
```markdown
## Gradual Rollout Analysis

### Configuration:
- Feature: NEW_SEARCH_ALGORITHM
- Rollout: 25% of users (verified 2025-01-13)
- Mechanism: User ID hash bucketing

### Analysis Decision:
**Option 1:** Analyze both paths (comprehensive)
- New algorithm (25% of users)
- Old algorithm (75% of users)
- Time: 2x effort

**Option 2:** Analyze majority path (efficient)
- Old algorithm (75% of users)
- Time: 1x effort
- Risk: Miss new algorithm issues

**Chosen:** Option 1 (both paths)
**Reason:** Feature rolling out, need to verify both work

### Documentation:
New algorithm path:
- Executes when: userId.hashCode() % 100 < 25
- Analyzed: ✓
- Findings: [...]

Old algorithm path:
- Executes when: userId.hashCode() % 100 >= 25
- Analyzed: ✓
- Findings: [...]
```

---

### Complete Configuration-Aware Analysis Template

```markdown
## Configuration-Aware Analysis: [Feature/Component]

### Target Environment: [Production/Staging/Dev]

---

### 1. CONFIGURATION IDENTIFICATION

**Feature Flags Found:**
1. `FLAG_NAME_1` (file.ext:line)
   - Controls: [What it affects]
   - Type: [Boolean/String/Int/Enum]
   - Source: [Remote/Local/Build-time]
   
2. `FLAG_NAME_2` (file.ext:line)
   - Controls: [What it affects]
   - Type: [Boolean/String/Int/Enum]
   - Source: [Remote/Local/Build-time]

**Environment Variables Found:**
1. `ENV_VAR_1` (file.ext:line)
   - Purpose: [What it configures]
   - Possible Values: [val1, val2, val3]

**Build Configuration Found:**
1. `BUILD_CONFIG_1` (file.ext:line)
   - Debug Value: [value]
   - Release Value: [value]

**Verification:**
- [ ] Identified all configuration points
- [ ] Documented configuration sources
- [ ] Listed possible values

---

### 2. ACTIVE CONFIGURATION DETERMINATION

**For Environment: [Production]**

**FLAG_NAME_1:**
- Verification Method: [Firebase Console/Config file/API call]
- Verified On: [Date]
- Current Value: `[value]`
- Source: [Screenshot/API response/Config file]

**FLAG_NAME_2:**
- Verification Method: [Firebase Console/Config file/API call]
- Verified On: [Date]
- Current Value: `[value]`
- Source: [Screenshot/API response/Config file]

**ENV_VAR_1:**
- Verification Method: [Deployment config/kubectl get/Environment]
- Verified On: [Date]
- Current Value: `[value]`

**Verification:**
- [ ] Verified all config values for target environment
- [ ] Documented verification method
- [ ] Noted verification date
- [ ] Saved verification evidence

---

### 3. CODE PATHS BASED ON CONFIGURATION

**Code Location:** [file.ext:line]

**Branch A: [When FLAG_NAME_1 = true]**
```language
if (config.flag1) {
    // This code
}
```
- Executes in: [Which environments]
- Active in target: [Yes/No]
- Analysis Priority: [High/Low]

**Branch B: [When FLAG_NAME_1 = false]**
```language
else {
    // This code
}
```
- Executes in: [Which environments]
- Active in target: [Yes/No]
- Analysis Priority: [High/Low]

**Decision:**
- Analyzing: Branch [A/B/Both]
- Reason: [Why this choice]

**Verification:**
- [ ] Identified all conditional branches
- [ ] Determined which are active
- [ ] Prioritized analysis effort

---

### 4. ACTIVE PATH ANALYSIS

**Analyzing Branch:** [A/B/Both]

**For Active Configuration:** [config values]

[Standard code analysis follows here - use main document methodology]

- Entry point: [...]
- Call path: [...]
- Data flow: [...]
- Conclusion: [...]

---

### 5. INACTIVE PATH DOCUMENTATION

**NOT Analyzed (Inactive in Target Environment):**

**Branch A:**
- Reason: FLAG_NAME_1 = false in production
- Code: [Brief description]
- Would need to analyze if: FLAG_NAME_1 changes to true

**Branch C:**
- Reason: Only executes in dev environment
- Code: [Brief description]
- Would need to analyze for: Development environment analysis

**Verification:**
- [ ] Documented all inactive paths
- [ ] Explained why not analyzed
- [ ] Noted conditions for future analysis

---

### 6. CONFIGURATION CHANGE IMPACT

**If FLAG_NAME_1 Changes:**
- Current: false → New: true
- Impact: Activates Branch A (currently inactive)
- Requires: Re-analysis of Branch A
- Risk: [Potential issues]

**If ENV_VAR_1 Changes:**
- Current: production-api → New: staging-api
- Impact: All API calls go to different environment
- Requires: Complete re-analysis
- Risk: [Potential issues]

**Verification:**
- [ ] Identified config change impacts
- [ ] Documented re-analysis triggers
- [ ] Noted risks of config changes

---

### Confidence: [X/10]

**Certain About:**
- Configuration values verified for [environment]
- Active code paths traced
- [What was thoroughly verified]

**Uncertain About:**
- Configuration in [other environments]
- Behavior if config changes
- [What needs more investigation]

**Scope Limitations:**
- Analysis valid only for configuration verified on [date]
- Other environments not analyzed
- Configuration drift possible

**Re-verification Needed:**
- If analyzing different environment
- If more than [timeframe] has passed
- If configuration has changed
```

---

### Configuration-Aware Checklist

**Before claiming you understand configuration-dependent behavior:**

#### ✅ Configuration Discovery
- [ ] I have searched for all feature flags
- [ ] I have searched for all environment variables
- [ ] I have searched for all build-time configuration
- [ ] I have identified runtime configuration
- [ ] I have documented configuration sources

#### ✅ Configuration Verification
- [ ] I know the target environment I'm analyzing
- [ ] I have verified configuration values for that environment
- [ ] I have documented verification method
- [ ] I have saved verification evidence
- [ ] I have noted verification date

#### ✅ Branch Analysis
- [ ] I have identified all conditional branches
- [ ] I know which branches are active
- [ ] I have analyzed only active branches (or documented why analyzing inactive)
- [ ] I have documented inactive branches
- [ ] I have noted conditions that would activate inactive branches

#### ✅ Scope Documentation
- [ ] I have stated which environment was analyzed
- [ ] I have stated which configuration was used
- [ ] I have noted when configuration was verified
- [ ] I have documented what would require re-analysis
- [ ] I have qualified all claims with configuration context

---

### Common Configuration Analysis Mistakes

**❌ Mistake #1: Analyzing Wrong Environment**
```
Wrong: Analyzed dev environment, claimed production behavior
Right: "In development (config verified 2025-01-13):
       - Behavior is X
       Production behavior: NOT ANALYZED"
```

**❌ Mistake #2: Assuming Static Configuration**
```
Wrong: "Flag is disabled, so code never runs"
Right: "Flag is disabled as of 2025-01-13.
       If flag enabled, code at line 123 would execute."
```

**❌ Mistake #3: Missing Configuration Dependencies**
```
Wrong: "Feature A is enabled"
Right: "Feature A is enabled AND:
       - Requires ENV = production ✓
       - Requires TIER = premium ✓
       - Requires REGION = US ✗
       Result: Feature A inactive due to REGION"
```

**❌ Mistake #4: Analyzing Inactive Code**
```
Wrong: Spent 4 hours analyzing new payment system
Reality: New payment system disabled in production
Result: 4 hours wasted

Right: Verify configuration first, analyze active code
```

**❌ Mistake #5: Not Documenting Configuration State**
```
Wrong: "System behaves like X"
Right: "When CONFIG_Y = true (production as of 2025-01-13),
       system behaves like X.
       When CONFIG_Y = false, behavior: NOT ANALYZED"
```

---

### Configuration Matrix Template

**For Complex Multi-Configuration Systems:**

```markdown
## Configuration Matrix

### Variables:
- Feature Flag A: [true/false]
- Feature Flag B: [true/false]  
- Environment: [dev/staging/prod]
- Tenant Tier: [free/premium/enterprise]

### Combinations:

| Flag A | Flag B | Environment | Tier | Behavior | Analyzed |
|--------|--------|-------------|------|----------|----------|
| false  | false  | prod | free | Legacy Flow | ✓ Yes |
| false  | false  | prod | premium | Legacy Flow | ✓ Yes |
| true   | false  | prod | free | New Flow A | ✗ No (flag disabled) |
| true   | false  | prod | premium | New Flow A | ✗ No (flag disabled) |
| false  | true   | staging | free | Test Flow B | ⚠️ Partial |
| true   | true   | staging | premium | Combined Flow | ✗ No (not in scope) |

### Analysis Coverage:
- Total combinations: 24
- Analyzed: 2 (8%)
- Partially analyzed: 1 (4%)
- Not analyzed: 21 (88%)

### Primary Focus:
**Configuration:** Flag A=false, Flag B=false, Environment=prod, Tier=free
**Reason:** Most common production configuration (65% of users)
**Coverage:** Represents behavior for 65% of user base
```

---

### Integration With Core Principles

**Configuration-aware analysis STILL requires:**
- ✅ Sin #1 Prevention: Verify code with active config actually runs
- ✅ Sin #3 Prevention: Trace complete path (in active configuration)
- ✅ Principle 2: Document which configurations you didn't check
- ✅ Principle 4: Qualify claims ("When flag X=true, system does Y")
- ✅ Principle 5: Document verification methodology
- ✅ Principle 6: Quantify (analyzed 3/10 configurations = 30%)

**This appendix adds:**
- Configuration discovery methods
- Configuration verification process
- Branch selection strategy
- Configuration-specific templates

**Core document provides:** Universal verification principles  
**This appendix provides:** Configuration-specific guidance

---

### Quick Reference: When to Use Each Appendix

```
Analyzing code execution flow? → Use MAIN DOCUMENT

Tracking WHERE data goes? → Use APPENDIX A (Data Flow)

Code has if(config) branches? → Use APPENDIX B (Configuration)

Both data flow AND config? → Use BOTH APPENDICES + MAIN DOCUMENT
```

---

**End of Appendices**

**Remember:** Appendices are optional domain-specific guidance. Core principles in main document always apply.
