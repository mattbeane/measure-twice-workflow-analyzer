"""Prompt definitions for workflow analysis."""

from dataclasses import dataclass


@dataclass
class PromptDefinition:
    """A prompt definition with its extraction schema."""
    id: str
    title: str
    category: str  # "process" or "skill"
    prompt_template: str
    extraction_prompt: str  # Prompt to extract structured data from raw response


SYSTEM_MESSAGE = """You are a workflow analyst providing quantitative metrics.
Rules:
- Provide EXACT numbers only (no ranges like "2-3 days" - pick one)
- Show your date/time calculations explicitly (e.g., "Sept 25 to Oct 10 = 15 days")
- If data is ambiguous, state your assumption and proceed
- Follow the output format template exactly"""


# Process Prompts
PROCESS_PROMPTS = [
    PromptDefinition(
        id="cycle_time",
        title="1. Cycle Time Extraction",
        category="process",
        prompt_template="""Analyze this workflow data and extract QUANTIFIED cycle time metrics:

1. Total elapsed time from start to completion (IN DAYS)
2. Active work time vs wait time (AS PERCENTAGES and IN DAYS)
3. Number of handoffs (COUNT - each time work passes between people/teams)
4. Approval/decision delays (IN DAYS for each delay)
5. Time to first response (IN HOURS - initial request to first action)

IMPORTANT CONSTRAINTS:
- Show date calculations explicitly (e.g., "Sept 25 to Oct 10 = 15 days")
- Provide EXACT numbers, not ranges
- If multiple interpretations exist, pick the most conservative
- Percentages must add to 100%
- Use this EXACT output format:

CYCLE TIME METRICS:
- Total cycle time: X days [show calculation: start date to end date]
- Active work: Y% (Z days)
- Wait time: W% (V days)
- Handoffs: N count
- Time to first response: H hours

Here is the workflow data to analyze:

{workflow_data}""",
        extraction_prompt="""Extract the following metrics from this workflow analysis as JSON:
- total_cycle_time_days (float)
- active_work_percent (float, 0-100)
- active_work_days (float)
- wait_time_percent (float, 0-100)
- wait_time_days (float)
- handoff_count (int)
- time_to_first_response_hours (float)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="bottleneck",
        title="2. Bottleneck Identification",
        category="process",
        prompt_template="""Identify all bottlenecks in this workflow data.

For each bottleneck, provide:
1. What is the bottleneck? (specific step, person, or approval)
2. How long does work wait here? (in hours/days)
3. Why does it bottleneck? (capacity, dependencies, approval chains)
4. What % of total cycle time is spent here?

Rank bottlenecks from highest to lowest impact.

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this bottleneck analysis as JSON:
- bottlenecks: array of objects with {name, wait_time_days, percent_of_cycle_time, reason}
- top_bottleneck_name (string)
- top_bottleneck_days (float)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="handoff",
        title="3. Handoff Analysis",
        category="process",
        prompt_template="""Map ALL handoffs in this workflow (every time work passes from one person/team to another).

For EACH handoff, extract:
- Duration (time between handoff sent and received: IN HOURS or DAYS)
- Information loss (YES/NO - did context get lost?)
- Rework caused (YES/NO - did handoff cause backtracking?)

Present as:

HANDOFF COUNT: N total handoffs

HANDOFF DETAILS:
1. [Person A] → [Person B]: X hours delay, [info loss: Y/N], [rework: Y/N]
2. [Person B] → [Person C]: X hours delay, [info loss: Y/N], [rework: Y/N]

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this handoff analysis as JSON:
- total_handoffs (int)
- handoffs: array of {from_person, to_person, delay_hours, information_loss (bool), caused_rework (bool)}
- average_delay_hours (float)
- handoffs_with_info_loss (int)
- handoffs_causing_rework (int)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="decision",
        title="4. Decision Point Mapping",
        category="process",
        prompt_template="""Identify every decision point in this workflow.

For EACH decision, extract QUANTIFIED data:
- Decision delay (time from question raised to decision made: IN HOURS/DAYS)
- Information gathering time (time spent collecting data to decide)
- Downstream impact (did decision cause delays or rework? IN DAYS if yes)

Present as:

DECISION COUNT: N total decisions

DECISION METRICS:
Decision #1: [What was decided]
- Who decided: [person/role]
- Decision delay: X hours/days
- Info gathering time: Y hours
- Downstream delay caused: Z days (or "none")

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this decision analysis as JSON:
- total_decisions (int)
- decisions: array of {description, decider, delay_hours, info_gathering_hours, downstream_delay_days}
- total_decision_time_days (float)
- average_decision_delay_hours (float)
- decisions_causing_rework (int)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="value_waste",
        title="5. Value vs. Waste",
        category="process",
        prompt_template="""Categorize EVERY step in this workflow and calculate TIME SPENT in each category:

- VALUE CREATION: directly moves toward end goal (IN DAYS or HOURS)
- COORDINATION: necessary communication/alignment (IN DAYS or HOURS)
- WAIT: delays for approval, response, availability (IN DAYS or HOURS)
- REWORK: fixing errors or revisiting decisions (IN DAYS or HOURS)

Present as percentages AND absolute time:

TIME ALLOCATION:
- Value creation: X days (Y%)
- Coordination: X days (Y%)
- Wait: X days (Y%)
- Rework: X days (Y%)

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this value/waste analysis as JSON:
- value_creation_days (float)
- value_creation_percent (float)
- coordination_days (float)
- coordination_percent (float)
- wait_days (float)
- wait_percent (float)
- rework_days (float)
- rework_percent (float)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="information_flow",
        title="6. Information Flow",
        category="process",
        prompt_template="""Track how information moves through this workflow and QUANTIFY information problems:

Count these specific issues:
- Repeated questions (COUNT - same question asked multiple times)
- Information hunt instances (COUNT - someone had to search for context)
- Missing handoff context (COUNT - incomplete information transferred)
- Communication channel switches (COUNT - email→Slack→meeting→doc)

Present as:

INFORMATION FLOW METRICS:
- Repeated questions: N count
- Information hunts: M count
- Incomplete handoffs: P count
- Channel switches: Q count

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this information flow analysis as JSON:
- repeated_questions (int)
- information_hunts (int)
- incomplete_handoffs (int)
- channel_switches (int)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="exception",
        title="7. Exception vs. Standard Path",
        category="process",
        prompt_template="""Analyze whether this workflow followed standard process or required exceptions.

Categorize each step and QUANTIFY time:
- Standard/routine steps: X hours (Y% of time)
- Exception/custom problem-solving: Z hours (W% of time)

For exceptions, extract:
- Count of exceptions: N total
- Time consumed by exceptions: X days

Present as:

PROCESS ADHERENCE:
- Standard path time: X days (Y%)
- Exception handling: Z days (W%)
- Exception count: N instances

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this exception analysis as JSON:
- standard_path_days (float)
- standard_path_percent (float)
- exception_handling_days (float)
- exception_handling_percent (float)
- exception_count (int)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="approval",
        title="8. Approval Overhead",
        category="process",
        prompt_template="""Identify ALL points where work waited for approval or sign-off.

For EACH approval point, extract:
- Wait time (IN DAYS or HOURS)
- Value add assessment (DID the approval change direction significantly? YES/NO)

Present as:

APPROVAL OVERHEAD:
- Total approval wait time: X days
- Number of approval gates: N count
- Approvals that changed direction: M count
- Approvals that were perfunctory: Q count

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this approval analysis as JSON:
- total_approval_wait_days (float)
- approval_gate_count (int)
- approvals_that_changed_direction (int)
- perfunctory_approvals (int)

Respond with ONLY valid JSON, no other text."""
    ),
]


# Skill Prompts - Based on the 3 Cs Framework (Challenge, Complexity, Connection)
# From "The Skill Code" by Matt Beane

SKILL_PROMPTS = [
    # CHALLENGE PROMPTS
    PromptDefinition(
        id="challenge_calibration",
        title="C1. Challenge Calibration",
        category="skill",
        prompt_template="""Analyze this workflow for CHALLENGE calibration in skill development.

For each person who appears to be learning/developing (not just executing routine work), assess:

1. WORK AT THE EDGE: Was work assigned near their capability edge?
   - Signs of edge work: requires near-total focus, can perform well but not at best
   - Signs of too easy: routine execution, no struggle visible
   - Signs of too hard: drowning, excessive help needed, unable to progress

2. SMALL FAILURES + RECOVERY: Did they experience small failures and recover?
   - Count specific instances of struggle/failure in the communications
   - Did they recover from each? How long did recovery take?

3. EXPERT HELP CALIBRATION: When experts helped, was it calibrated correctly?
   - Good: Help on tasks just beyond novice's reach, then stepped back
   - Bad: Expert did it for them (novice cut out of challenge)
   - Bad: Expert left them to drown (no support when needed)

4. FRUSTRATION MANAGEMENT: Did experts acknowledge stretch/remind of payoff?
   - Look for encouragement, acknowledgment of difficulty, reminders of learning value

For EACH novice-expert pair, provide:
- Novice name, Expert name
- Work edge assessment (too easy / appropriate / too hard)
- Small failure count and recovery count
- Help calibration instances (appropriate help / over-helped / under-helped)
- Frustration management signals (present / absent)

QUANTIFY:
- Hours of appropriately-challenging work
- Hours of work that was too easy (cruise/routine for this person)
- Hours of work that was too hard (overwhelmed, unable to progress)
- Instances where expert did work that novice could have done (challenge bypassed)

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this challenge analysis as JSON:
- pairs: array of {novice, expert, edge_assessment (string: "too_easy"/"appropriate"/"too_hard"), small_failures (int), recoveries (int), help_appropriate (int), help_over (int), help_under (int), frustration_mgmt_present (bool)}
- appropriate_challenge_hours (float)
- too_easy_hours (float)
- too_hard_hours (float)
- challenge_bypassed_count (int) - times expert did work novice could have done
- challenge_calibration_score (float, 0-100) - overall assessment

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="challenge_continuity",
        title="C2. Challenge Continuity",
        category="skill",
        prompt_template="""Analyze this workflow for CHALLENGE CONTINUITY - whether learning opportunities were sustained.

Look for:

1. REPEAT OPPORTUNITIES: Did the novice face similar challenges multiple times?
   - Skill builds through repetition at the edge
   - One-off challenges don't build durable skill
   - Count instances of similar challenge types

2. RECOVERY TIME: Was there time between intense challenge bursts?
   - Some straightforward work or off-time between stretches
   - Constant stretch = burnout risk
   - All cruise = no growth

3. CHALLENGE SEEKING: Did novices seek/create challenge or avoid it?
   - Proactive: volunteering for hard work, asking for stretch assignments
   - Passive: waiting to be assigned, avoiding difficulty
   - Look for explicit asks or offers in the communications

4. FUTURE CHALLENGE SETUP: Were next challenges identified/prepared?
   - Expert setting up next learning opportunity
   - Pipeline of appropriately-difficult work visible

QUANTIFY:
- Similar challenge repetitions (count)
- Recovery periods between stretches (count, and average duration in hours)
- Challenge-seeking instances by novice (count)
- Challenge-avoiding instances by novice (count)
- Next challenges explicitly set up (count)

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this challenge continuity analysis as JSON:
- similar_challenge_repetitions (int)
- recovery_periods (int)
- avg_recovery_hours (float)
- challenge_seeking_instances (int)
- challenge_avoiding_instances (int)
- next_challenges_setup (int)
- challenge_continuity_score (float, 0-100)

Respond with ONLY valid JSON, no other text."""
    ),

    # COMPLEXITY PROMPTS
    PromptDefinition(
        id="complexity_exposure",
        title="C3. Complexity Exposure",
        category="skill",
        prompt_template="""Analyze this workflow for COMPLEXITY EXPOSURE in skill development.

Look for:

1. JUST-IN-TIME ORIENTATION: Did novices learn basics close to when they started work?
   - Good: Brief orientation then hands-on
   - Bad: Long front-loaded training before doing
   - Bad: Thrown in with zero orientation

2. IMPLICIT vs EXPLICIT LEARNING: How did learning happen?
   - Good: Learning by doing, figuring things out
   - Bad: Excessive explicit instruction before trying
   - Count instances of each

3. ATTENTION DIRECTION vs INTERPRETATION: When experts guided, did they:
   - Good: Point to where to look, ask what novice notices
   - Bad: Interpret/explain everything for the novice
   - Count "look at X" vs "here's what X means" instances

4. REFLECTION TIME: Was there slack time to reflect on the work?
   - Away from active work initially
   - During work as expertise develops
   - Look for debrief, retrospective, or thinking time

5. CONTEXT BREADTH: Did novice engage with full work context or narrow slice?
   - Good: Exposure to customer, business, technical dimensions
   - Bad: Siloed to just their technical piece

QUANTIFY:
- Orientation time before work started (hours)
- Learning-by-doing instances (count)
- Explicit-instruction-before-trying instances (count)
- Attention-directing instances by expert (count)
- Interpreting-for-novice instances by expert (count)
- Reflection/debrief time (hours)
- Context dimensions exposed to (count: technical, customer, business, etc.)

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this complexity exposure analysis as JSON:
- orientation_hours (float)
- learning_by_doing_instances (int)
- explicit_instruction_instances (int)
- attention_directing_instances (int)
- interpreting_for_novice_instances (int)
- reflection_time_hours (float)
- context_dimensions_exposed (int)
- complexity_exposure_score (float, 0-100)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="expert_guidance_quality",
        title="C4. Expert Guidance Quality",
        category="skill",
        prompt_template="""Analyze the QUALITY OF EXPERT GUIDANCE in this workflow.

For each expert-novice interaction, assess:

1. ASK BEFORE TELL: Did expert solicit novice's assessment before sharing theirs?
   - Good: "What do you think is happening?" before explaining
   - Bad: Immediately telling/explaining
   - Count instances of each

2. NAIVE QUESTIONS ENCOURAGED: Were "silly" questions treated as assets?
   - Good: Welcoming basic questions, using them to teach
   - Bad: Dismissing, rushing past, or showing impatience
   - Look for question-asking patterns and responses

3. GUIDANCE MATCHED TO TASK: Did guidance style match task structure?
   - Structured task = more structured guidance appropriate
   - Unstructured task = more fluid/exploratory guidance appropriate
   - Was there mismatch?

4. HELP RESERVED FOR STRETCH: Did expert reserve help for tasks just beyond novice's reach?
   - Good: Helping only when novice genuinely stuck
   - Bad: Jumping in too early (novice could have figured it out)
   - Bad: Waiting too long (novice wasted significant time)

QUANTIFY:
- "Ask before tell" instances (count)
- "Tell without asking" instances (count)
- Questions welcomed (count)
- Questions dismissed or rushed (count)
- Guidance-task match instances (count)
- Guidance-task mismatch instances (count)
- Help appropriately timed (count)
- Help too early (count)
- Help too late (count)

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this expert guidance analysis as JSON:
- ask_before_tell (int)
- tell_without_asking (int)
- questions_welcomed (int)
- questions_dismissed (int)
- guidance_task_match (int)
- guidance_task_mismatch (int)
- help_appropriate_timing (int)
- help_too_early (int)
- help_too_late (int)
- expert_guidance_score (float, 0-100)

Respond with ONLY valid JSON, no other text."""
    ),

    # CONNECTION PROMPTS
    PromptDefinition(
        id="relationship_health",
        title="C5. Relationship Health",
        category="skill",
        prompt_template="""Analyze RELATIONSHIP HEALTH for skill development in this workflow.

For each expert-novice relationship, assess:

1. WARMTH AND CARE: Is there evidence of bonding beyond transactional work?
   - Encouragement, praise for effort (not just results)
   - Personal acknowledgment
   - Concern for wellbeing/development

2. SIGNIFICANCE: Does each person seem to feel their work matters to the other?
   - Recognition of contributions
   - Explicit acknowledgment of value
   - Being kept in the loop vs cut out

3. TRUST SIGNALS: Willingness to be vulnerable because they expect delivery
   - Novice admitting confusion or mistakes
   - Expert delegating real responsibility
   - Honest feedback exchange

4. RESPECT SIGNALS: Willingness to give valuable resources (time, access, opportunities)
   - Expert investing time in teaching
   - Novice given access to important work/people
   - Ideas taken seriously regardless of source

5. ATTUNEMENT: Were both parties focused and present during interactions?
   - Limiting distractions during teaching moments
   - Responsive to questions/needs
   - vs. Distracted, delayed, or unavailable

QUANTIFY:
- Warmth signals (count: encouragement, praise, care expressions)
- Significance signals (count: recognition, acknowledgment, inclusion)
- Trust signals (count: vulnerability shown, responsibility given)
- Respect signals (count: time invested, access granted, ideas adopted)
- Attunement signals (count: focused interactions, responsive exchanges)
- Attunement breaks (count: delayed responses, unavailability, distraction)

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this relationship health analysis as JSON:
- warmth_signals (int)
- significance_signals (int)
- trust_signals (int)
- respect_signals (int)
- attunement_signals (int)
- attunement_breaks (int)
- relationship_health_score (float, 0-100)

Respond with ONLY valid JSON, no other text."""
    ),
    PromptDefinition(
        id="developmental_trajectory",
        title="C6. Developmental Trajectory",
        category="skill",
        prompt_template="""Analyze the DEVELOPMENTAL TRAJECTORY visible in this workflow.

Look for signals about where this expert-novice relationship is heading:

1. JOINT GOAL-SETTING: Were learning/development goals discussed together?
   - Good: Collaborative discussion of what novice should learn
   - Bad: Top-down assignment with no input
   - Look for explicit goal conversations

2. AUTHORSHIP: Does novice have ownership over their work and learning path?
   - Good: Novice's ideas adopted, approach respected
   - Bad: Just executing expert's plan with no agency
   - Count instances of novice authorship vs pure execution

3. TEACHING OTHERS: Any signs novice is starting to help/teach others?
   - This signals significant skill development
   - Even small instances count (explaining to peers, documenting for others)

4. EXTERNAL ADVOCACY: Did expert advocate for novice outside their shared work?
   - Recommending for opportunities
   - Praising to others
   - Building novice's reputation

5. GRADUATION SIGNALS: Evidence relationship is evolving toward independence?
   - Expert stepping back on tasks novice has mastered
   - Novice taking on work without expert involvement
   - Planning for novice to lead

QUANTIFY:
- Joint goal-setting instances (count)
- Novice authorship instances (count)
- Pure execution instances (count)
- Novice teaching others instances (count)
- External advocacy instances (count)
- Graduation/independence signals (count)

TRAJECTORY ASSESSMENT:
- Positive: Clear evidence of growth trajectory
- Neutral: Insufficient signal to assess
- Concerning: Signs of stagnation or regression

Here is the workflow data:

{workflow_data}""",
        extraction_prompt="""Extract the following from this trajectory analysis as JSON:
- joint_goal_setting (int)
- novice_authorship (int)
- pure_execution (int)
- novice_teaching_others (int)
- external_advocacy (int)
- graduation_signals (int)
- trajectory_assessment (string: "positive"/"neutral"/"concerning")
- developmental_trajectory_score (float, 0-100)

Respond with ONLY valid JSON, no other text."""
    ),
]


ALL_PROMPTS = PROCESS_PROMPTS + SKILL_PROMPTS

PROMPT_BY_ID = {p.id: p for p in ALL_PROMPTS}
