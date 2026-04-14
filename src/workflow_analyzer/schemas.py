"""Pydantic schemas for structured extraction from LLM outputs."""

from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# PROCESS METRICS SCHEMAS
# =============================================================================

class CycleTimeMetrics(BaseModel):
    """Extracted metrics from Cycle Time Analysis prompt."""
    total_cycle_time_days: float = Field(description="Total elapsed time in days")
    active_work_percent: float = Field(description="Percentage of time in active work")
    active_work_days: float = Field(description="Days spent in active work")
    wait_time_percent: float = Field(description="Percentage of time waiting")
    wait_time_days: float = Field(description="Days spent waiting")
    handoff_count: int = Field(description="Number of handoffs between people/teams")
    time_to_first_response_hours: float = Field(description="Hours until first response")
    date_calculation: str = Field(description="The date calculation shown (e.g., 'Sept 25 to Oct 10 = 15 days')")


class Bottleneck(BaseModel):
    """A single bottleneck identified in the workflow."""
    name: str = Field(description="Name/description of the bottleneck")
    wait_time_days: float = Field(description="How long work waits at this bottleneck")
    percent_of_cycle_time: float = Field(description="Percentage of total cycle time")
    reason: str = Field(description="Why this is a bottleneck")
    elimination_suggestion: str = Field(description="How to eliminate this bottleneck")


class BottleneckMetrics(BaseModel):
    """Extracted metrics from Bottleneck Identification prompt."""
    bottlenecks: list[Bottleneck] = Field(description="List of bottlenecks ranked by impact")
    top_bottleneck_name: str = Field(description="Name of the highest-impact bottleneck")
    top_bottleneck_days: float = Field(description="Days lost to top bottleneck")


class Handoff(BaseModel):
    """A single handoff in the workflow."""
    from_person: str = Field(description="Person handing off work")
    to_person: str = Field(description="Person receiving work")
    delay_hours: float = Field(description="Hours of delay in this handoff")
    information_loss: bool = Field(description="Whether context was lost")
    caused_rework: bool = Field(description="Whether this handoff caused rework")


class HandoffMetrics(BaseModel):
    """Extracted metrics from Handoff Analysis prompt."""
    total_handoffs: int = Field(description="Total number of handoffs")
    handoffs: list[Handoff] = Field(description="List of all handoffs")
    average_delay_hours: float = Field(description="Average handoff delay in hours")
    handoffs_with_info_loss: int = Field(description="Count of handoffs with information loss")
    handoffs_causing_rework: int = Field(description="Count of handoffs that caused rework")


class Decision(BaseModel):
    """A single decision point in the workflow."""
    description: str = Field(description="What was decided")
    decider: str = Field(description="Who made the decision")
    delay_hours: float = Field(description="Hours from question to decision")
    info_gathering_hours: float = Field(description="Hours spent gathering information")
    downstream_delay_days: float = Field(description="Days of downstream delay caused (0 if none)")


class DecisionMetrics(BaseModel):
    """Extracted metrics from Decision Point Mapping prompt."""
    total_decisions: int = Field(description="Total number of decisions")
    decisions: list[Decision] = Field(description="List of all decisions")
    total_decision_time_days: float = Field(description="Total time spent on decisions")
    average_decision_delay_hours: float = Field(description="Average decision delay")
    decisions_causing_rework: int = Field(description="Count of decisions that caused rework")


class ValueWasteMetrics(BaseModel):
    """Extracted metrics from Value vs Waste prompt."""
    value_creation_days: float = Field(description="Days spent on value creation")
    value_creation_percent: float = Field(description="Percentage on value creation")
    coordination_days: float = Field(description="Days spent on coordination")
    coordination_percent: float = Field(description="Percentage on coordination")
    wait_days: float = Field(description="Days spent waiting")
    wait_percent: float = Field(description="Percentage waiting")
    rework_days: float = Field(description="Days spent on rework")
    rework_percent: float = Field(description="Percentage on rework")


class InformationFlowMetrics(BaseModel):
    """Extracted metrics from Information Flow prompt."""
    repeated_questions: int = Field(description="Count of repeated questions")
    information_hunts: int = Field(description="Count of information hunt instances")
    incomplete_handoffs: int = Field(description="Count of incomplete handoffs")
    channel_switches: int = Field(description="Count of communication channel switches")
    efficiency_score: float = Field(description="Information efficiency score (0-100)")


class ExceptionMetrics(BaseModel):
    """Extracted metrics from Exception vs Standard Path prompt."""
    standard_path_days: float = Field(description="Days on standard path")
    standard_path_percent: float = Field(description="Percentage on standard path")
    exception_handling_days: float = Field(description="Days on exception handling")
    exception_handling_percent: float = Field(description="Percentage on exceptions")
    exception_count: int = Field(description="Number of exceptions")


class ApprovalMetrics(BaseModel):
    """Extracted metrics from Executive Approval Overhead prompt."""
    total_approval_wait_days: float = Field(description="Total days waiting for approvals")
    approval_wait_percent: float = Field(description="Percentage of cycle time on approvals")
    approval_gate_count: int = Field(description="Number of approval gates")
    approvals_that_changed_direction: int = Field(description="Approvals that added value")
    perfunctory_approvals: int = Field(description="Rubber-stamp approvals")


# =============================================================================
# SKILL METRICS SCHEMAS
# =============================================================================

class SkillTransferMoment(BaseModel):
    """A single knowledge/skill transfer moment."""
    from_person: str = Field(description="Person sharing knowledge")
    to_person: str = Field(description="Person receiving knowledge")
    what_learned: str = Field(description="What was learned/transferred")
    timestamp: str = Field(description="When this occurred")


class CollaborationMetrics(BaseModel):
    """Extracted metrics from Collaboration Pattern Detection prompt."""
    cross_level_mentoring_count: int = Field(description="Count of mentoring instances")
    knowledge_transfer_moments: int = Field(description="Count of knowledge transfer moments")
    transfer_details: list[SkillTransferMoment] = Field(description="Details of each transfer")
    complex_collaborative_percent: float = Field(description="% time on complex collaborative work")
    complex_solo_percent: float = Field(description="% time on complex solo work")
    routine_percent: float = Field(description="% time on routine work")
    high_skill_yield_percent: float = Field(description="% time in high skill yield")
    medium_skill_yield_percent: float = Field(description="% time in medium skill yield")
    low_skill_yield_percent: float = Field(description="% time in low skill yield")


class ComplexityMetrics(BaseModel):
    """Extracted metrics from Problem Complexity Analysis prompt."""
    complex_hours: float = Field(description="Hours on complex problems")
    complex_percent: float = Field(description="Percentage on complex problems")
    moderate_hours: float = Field(description="Hours on moderate problems")
    moderate_percent: float = Field(description="Percentage on moderate problems")
    routine_hours: float = Field(description="Hours on routine tasks")
    routine_percent: float = Field(description="Percentage on routine tasks")
    people_stretched: bool = Field(description="Whether people are stretched beyond capability")
    people_below_capability: bool = Field(description="Whether people are below capability level")


class ExpertiseTransfer(BaseModel):
    """A single expertise transfer instance."""
    expert: str = Field(description="Person with expertise")
    learner: str = Field(description="Person learning")
    what_taught: str = Field(description="What was taught")
    duration_hours: float = Field(description="Duration in hours")
    applied: bool = Field(description="Whether learner applied the knowledge")


class ExpertiseTransferMetrics(BaseModel):
    """Extracted metrics from Expertise Transfer Moments prompt."""
    transfers: list[ExpertiseTransfer] = Field(description="List of expertise transfers")
    total_mentoring_hours: float = Field(description="Total hours of mentoring")
    distinct_skills_transferred: int = Field(description="Number of distinct skills transferred")
    application_instances: int = Field(description="Times knowledge was applied")


class PersonStretchMetrics(BaseModel):
    """Stretch vs cruise metrics for one person."""
    person: str = Field(description="Person's name")
    stretch_hours: float = Field(description="Hours in stretch zone")
    stretch_percent: float = Field(description="Percentage in stretch zone")
    cruise_hours: float = Field(description="Hours in cruise zone")
    cruise_percent: float = Field(description="Percentage in cruise zone")


class StretchCruiseMetrics(BaseModel):
    """Extracted metrics from Skill Stretch vs Cruise prompt."""
    people_metrics: list[PersonStretchMetrics] = Field(description="Metrics per person")
    people_in_stretch: int = Field(description="Count of people in stretch zone")
    people_in_cruise: int = Field(description="Count of people in cruise zone")


class CrossFunctionalMetrics(BaseModel):
    """Extracted metrics from Cross-Functional Learning prompt."""
    team_exposure_percent: float = Field(description="% of team with cross-functional exposure")
    functions_involved: list[str] = Field(description="List of functions involved")
    collaboration_depth: str = Field(description="Superficial/Meaningful")
    building_breadth: bool = Field(description="Whether people are building breadth")


class PersonAutonomy(BaseModel):
    """Autonomy metrics for one person."""
    person: str = Field(description="Person's name")
    autonomous_decisions: int = Field(description="Count of autonomous decisions")
    escalations_needed: int = Field(description="Count of escalations")
    wait_time_hours: float = Field(description="Hours waiting for approvals")
    autonomy_ratio: float = Field(description="Autonomy ratio (0-100)")


class AutonomyMetrics(BaseModel):
    """Extracted metrics from Autonomy vs Dependency prompt."""
    people_metrics: list[PersonAutonomy] = Field(description="Metrics per person")
    high_autonomy_count: int = Field(description="People with >80% autonomy")
    medium_autonomy_count: int = Field(description="People with 50-80% autonomy")
    low_autonomy_count: int = Field(description="People with <50% autonomy")


class PersonCognitiveLoad(BaseModel):
    """Cognitive load metrics for one person."""
    person: str = Field(description="Person's name")
    high_load_hours: float = Field(description="Hours on high cognitive load work")
    high_load_percent: float = Field(description="Percentage high load")
    medium_load_hours: float = Field(description="Hours on medium cognitive load work")
    medium_load_percent: float = Field(description="Percentage medium load")
    low_load_hours: float = Field(description="Hours on low cognitive load work")
    low_load_percent: float = Field(description="Percentage low load")


class CognitiveLoadMetrics(BaseModel):
    """Extracted metrics from Cognitive Load Distribution prompt."""
    people_metrics: list[PersonCognitiveLoad] = Field(description="Metrics per person")
    seniors_doing_low_load: bool = Field(description="Whether seniors are doing low-load work")
    juniors_overwhelmed: bool = Field(description="Whether juniors are doing too much high-load")


class ErrorInstance(BaseModel):
    """A single error that occurred."""
    description: str = Field(description="What went wrong")
    people_involved: list[str] = Field(description="Who was involved")
    correction: str = Field(description="How it was fixed")
    learning_outcome: str = Field(description="What was learned")
    time_cost_hours: float = Field(description="Hours lost to error + fix")


class ErrorLearningMetrics(BaseModel):
    """Extracted metrics from Error-Driven Learning prompt."""
    errors: list[ErrorInstance] = Field(description="List of errors")
    errors_with_learning: int = Field(description="Errors that led to learning")
    errors_just_fixed: int = Field(description="Errors just fixed without learning")
    learning_ratio: float = Field(description="Learning ratio (0-100)")


class KnowledgeAccessMetrics(BaseModel):
    """Extracted metrics from Knowledge Access Patterns prompt."""
    ask_expert_count: int = Field(description="Times asked an expert")
    ask_expert_avg_minutes: float = Field(description="Average time to get answer from expert")
    documentation_count: int = Field(description="Times looked up documentation")
    documentation_avg_minutes: float = Field(description="Average time for doc lookup")
    experimentation_count: int = Field(description="Times used trial and error")
    experimentation_avg_hours: float = Field(description="Average time for experimentation")
    internalization_rate: float = Field(description="Knowledge internalization rate (0-100)")
    expert_dependency: str = Field(description="High/Medium/Low")


class FutureCapabilityMetrics(BaseModel):
    """Extracted metrics from Future Capability Gaps prompt."""
    skills_at_risk: list[str] = Field(description="Skills at risk of degradation")
    skills_held_by_single_person: list[str] = Field(description="Skills only one person has")
    junior_gaps: list[str] = Field(description="Skills juniors aren't getting exposure to")
    team_will_be_better_at: list[str] = Field(description="Skills improving in 12 months")
    team_will_be_worse_at: list[str] = Field(description="Skills degrading in 12 months")


# =============================================================================
# UNIFIED RUN RESULT
# =============================================================================

class PromptRunResult(BaseModel):
    """Result of a single prompt run."""
    prompt_id: str = Field(description="Prompt identifier (e.g., 'cycle_time')")
    prompt_title: str = Field(description="Human-readable prompt title")
    run_number: int = Field(description="Which run (1-N)")
    raw_response: str = Field(description="Raw LLM response text")
    extracted_metrics: Optional[dict] = Field(description="Extracted metrics as dict", default=None)
    extraction_success: bool = Field(description="Whether extraction succeeded")
    error_message: Optional[str] = Field(description="Error if extraction failed", default=None)
    model: str = Field(description="Model used")
    input_tokens: int = Field(description="Input tokens used")
    output_tokens: int = Field(description="Output tokens used")
    latency_ms: int = Field(description="Latency in milliseconds")
    confidence: str = Field(description="Confidence level (high/medium/low)", default="medium")


# =============================================================================
# SCHEMA MAPPING
# =============================================================================

PROMPT_SCHEMAS = {
    "cycle_time": CycleTimeMetrics,
    "bottleneck": BottleneckMetrics,
    "handoff": HandoffMetrics,
    "decision": DecisionMetrics,
    "value_waste": ValueWasteMetrics,
    "information_flow": InformationFlowMetrics,
    "exception": ExceptionMetrics,
    "approval": ApprovalMetrics,
    "collaboration": CollaborationMetrics,
    "complexity": ComplexityMetrics,
    "expertise_transfer": ExpertiseTransferMetrics,
    "stretch_cruise": StretchCruiseMetrics,
    "cross_functional": CrossFunctionalMetrics,
    "autonomy": AutonomyMetrics,
    "cognitive_load": CognitiveLoadMetrics,
    "error_learning": ErrorLearningMetrics,
    "knowledge_access": KnowledgeAccessMetrics,
    "future_capability": FutureCapabilityMetrics,
}
