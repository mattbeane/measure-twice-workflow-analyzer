================================================================================
WORKFLOW ANALYSIS REPORT
Generated: 2026-04-14 10:50:29
================================================================================

SUMMARY
----------------------------------------
Total API Calls: 66
Successful: 66 (100%)
Failed: 0
Process Prompts: 8
Skill Prompts: 6
Estimated Cost: $0.242

⚠️  HIGH VARIANCE METRICS (CV > 20%):
  - approval.total_approval_wait_days
  - approval.approval_gate_count
  - approval.approvals_that_changed_direction
  - approval.perfunctory_approvals
  - challenge_calibration.appropriate_challenge_hours
  - challenge_calibration.too_easy_hours
  - challenge_calibration.challenge_bypassed_count
  - challenge_continuity.similar_challenge_repetitions
  - challenge_continuity.recovery_periods
  - challenge_continuity.avg_recovery_hours

================================================================================
PROCESS ANALYSIS RESULTS
================================================================================

### 1. Cycle Time Extraction
Runs: 5/5 successful (100%)

  active_work_days:
    Mean: 6.33 ± 3.64
    Range: 0.90 - 9.30
    95% CI: [3.14, 9.52]
    CV: 57.4% ⚠️ HIGH VARIANCE

  active_work_percent:
    Mean: 43.53 ± 22.65
    Range: 9.00 - 62.00
    95% CI: [23.68, 63.39]
    CV: 52.0% ⚠️ HIGH VARIANCE

  handoff_count:
    Mean: 8.80 ± 2.49
    Range: 7.00 - 12.00
    95% CI: [6.62, 10.98]
    CV: 28.3% ⚠️ HIGH VARIANCE

  time_to_first_response_hours:
    Mean: 7.05 ± 0.11
    Range: 7.00 - 7.25
    95% CI: [6.95, 7.15]
    CV: 1.6%

  total_cycle_time_days:
    Mean: 14.00 ± 2.24
    Range: 10.00 - 15.00
    95% CI: [12.04, 15.96]
    CV: 16.0%

  wait_time_days:
    Mean: 7.11 ± 1.39
    Range: 5.70 - 8.90
    95% CI: [5.89, 8.33]
    CV: 19.6%

  wait_time_percent:
    Mean: 53.93 ± 16.79
    Range: 38.00 - 75.00
    95% CI: [39.22, 68.65]
    CV: 31.1% ⚠️ HIGH VARIANCE


### 2. Bottleneck Identification
Runs: 3/3 successful (100%)

  top_bottleneck_days:
    Mean: 4.00 ± 0.00
    Range: 4.00 - 4.00
    95% CI: [4.00, 4.00]
    CV: 0.0%


### 3. Handoff Analysis
Runs: 5/5 successful (100%)

  average_delay_hours:
    Mean: 19.36 ± 7.03
    Range: 14.50 - 31.44
    95% CI: [13.20, 25.53]
    CV: 36.3% ⚠️ HIGH VARIANCE

  handoffs_causing_rework:
    Mean: 6.00 ± 0.71
    Range: 5.00 - 7.00
    95% CI: [5.38, 6.62]
    CV: 11.8%

  handoffs_with_info_loss:
    Mean: 5.00 ± 0.71
    Range: 4.00 - 6.00
    95% CI: [4.38, 5.62]
    CV: 14.1%

  total_handoffs:
    Mean: 12.00 ± 0.00
    Range: 12.00 - 12.00
    95% CI: [12.00, 12.00]
    CV: 0.0%


### 4. Decision Point Mapping
Runs: 5/5 successful (100%)

  average_decision_delay_hours:
    Mean: 17.36 ± 7.12
    Range: 8.60 - 26.47
    95% CI: [11.12, 23.60]
    CV: 41.0% ⚠️ HIGH VARIANCE

  decisions_causing_rework:
    Mean: 2.40 ± 0.89
    Range: 2.00 - 4.00
    95% CI: [1.62, 3.18]
    CV: 37.3% ⚠️ HIGH VARIANCE

  total_decision_time_days:
    Mean: 5.27 ± 4.21
    Range: 0.36 - 10.32
    95% CI: [1.57, 8.96]
    CV: 80.0% ⚠️ HIGH VARIANCE

  total_decisions:
    Mean: 6.40 ± 0.89
    Range: 5.00 - 7.00
    95% CI: [5.62, 7.18]
    CV: 14.0%


### 5. Value vs. Waste
Runs: 5/5 successful (100%)

  coordination_days:
    Mean: 1.25 ± 0.81
    Range: 0.23 - 2.50
    95% CI: [0.53, 1.96]
    CV: 65.2% ⚠️ HIGH VARIANCE

  coordination_percent:
    Mean: 14.62 ± 10.41
    Range: 1.20 - 28.30
    95% CI: [5.49, 23.75]
    CV: 71.2% ⚠️ HIGH VARIANCE

  rework_days:
    Mean: 1.77 ± 1.54
    Range: 0.28 - 4.00
    95% CI: [0.42, 3.13]
    CV: 87.0% ⚠️ HIGH VARIANCE

  rework_percent:
    Mean: 12.32 ± 6.35
    Range: 6.20 - 21.60
    95% CI: [6.76, 17.88]
    CV: 51.5% ⚠️ HIGH VARIANCE

  value_creation_days:
    Mean: 4.21 ± 1.46
    Range: 2.06 - 5.50
    95% CI: [2.93, 5.49]
    CV: 34.7% ⚠️ HIGH VARIANCE

  value_creation_percent:
    Mean: 41.14 ± 14.73
    Range: 28.00 - 63.50
    95% CI: [28.23, 54.05]
    CV: 35.8% ⚠️ HIGH VARIANCE

  wait_days:
    Mean: 3.93 ± 3.09
    Range: 0.63 - 7.50
    95% CI: [1.22, 6.63]
    CV: 78.7% ⚠️ HIGH VARIANCE

  wait_percent:
    Mean: 27.70 ± 12.64
    Range: 11.30 - 40.50
    95% CI: [16.62, 38.78]
    CV: 45.6% ⚠️ HIGH VARIANCE


### 6. Information Flow
Runs: 3/3 successful (100%)

  channel_switches:
    Mean: 6.33 ± 0.58
    Range: 6.00 - 7.00
    95% CI: [5.68, 6.99]
    CV: 9.1%

  incomplete_handoffs:
    Mean: 5.00 ± 0.00
    Range: 5.00 - 5.00
    95% CI: [5.00, 5.00]
    CV: 0.0%

  information_hunts:
    Mean: 4.00 ± 0.00
    Range: 4.00 - 4.00
    95% CI: [4.00, 4.00]
    CV: 0.0%

  repeated_questions:
    Mean: 3.00 ± 0.00
    Range: 3.00 - 3.00
    95% CI: [3.00, 3.00]
    CV: 0.0%


### 7. Exception vs. Standard Path
Runs: 5/5 successful (100%)

  exception_count:
    Mean: 4.20 ± 1.10
    Range: 3.00 - 6.00
    95% CI: [3.24, 5.16]
    CV: 26.1% ⚠️ HIGH VARIANCE

  exception_handling_days:
    Mean: 7.85 ± 1.88
    Range: 6.00 - 10.75
    95% CI: [6.20, 9.50]
    CV: 24.0% ⚠️ HIGH VARIANCE

  exception_handling_percent:
    Mean: 57.28 ± 10.89
    Range: 44.00 - 71.40
    95% CI: [47.74, 66.82]
    CV: 19.0%

  standard_path_days:
    Mean: 5.90 ± 1.77
    Range: 4.25 - 8.50
    95% CI: [4.35, 7.45]
    CV: 30.1% ⚠️ HIGH VARIANCE

  standard_path_percent:
    Mean: 42.64 ± 11.02
    Range: 28.20 - 56.00
    95% CI: [32.98, 52.30]
    CV: 25.8% ⚠️ HIGH VARIANCE


### 8. Approval Overhead
Runs: 5/5 successful (100%)

  approval_gate_count:
    Mean: 7.20 ± 2.17
    Range: 6.00 - 11.00
    95% CI: [5.30, 9.10]
    CV: 30.1% ⚠️ HIGH VARIANCE

  approvals_that_changed_direction:
    Mean: 4.40 ± 2.07
    Range: 3.00 - 8.00
    95% CI: [2.58, 6.22]
    CV: 47.1% ⚠️ HIGH VARIANCE

  perfunctory_approvals:
    Mean: 2.80 ± 0.84
    Range: 2.00 - 4.00
    95% CI: [2.07, 3.53]
    CV: 29.9% ⚠️ HIGH VARIANCE

  total_approval_wait_days:
    Mean: 6.46 ± 3.61
    Range: 1.75 - 11.76
    95% CI: [3.30, 9.63]
    CV: 55.9% ⚠️ HIGH VARIANCE


================================================================================
SKILL DEVELOPMENT ANALYSIS RESULTS
================================================================================

### C1. Challenge Calibration
Runs: 5/5 successful (100%)

  appropriate_challenge_hours:
    Mean: 17.60 ± 3.58
    Range: 16.00 - 24.00
    95% CI: [14.46, 20.74]
    CV: 20.3% ⚠️ HIGH VARIANCE

  challenge_bypassed_count:
    Mean: 1.60 ± 0.55
    Range: 1.00 - 2.00
    95% CI: [1.12, 2.08]
    CV: 34.2% ⚠️ HIGH VARIANCE

  challenge_calibration_score:
    Mean: 66.40 ± 5.05
    Range: 60.00 - 72.50
    95% CI: [61.97, 70.83]
    CV: 7.6%

  too_easy_hours:
    Mean: 0.40 ± 0.89
    Range: 0.00 - 2.00
    95% CI: [-0.38, 1.18]
    CV: 223.6% ⚠️ HIGH VARIANCE

  too_hard_hours:
    Mean: 0.00 ± 0.00
    Range: 0.00 - 0.00
    95% CI: [0.00, 0.00]
    CV: 0.0%


### C2. Challenge Continuity
Runs: 5/5 successful (100%)

  avg_recovery_hours:
    Mean: 30.36 ± 7.74
    Range: 17.00 - 36.50
    95% CI: [23.58, 37.14]
    CV: 25.5% ⚠️ HIGH VARIANCE

  challenge_avoiding_instances:
    Mean: 0.80 ± 1.10
    Range: 0.00 - 2.00
    95% CI: [-0.16, 1.76]
    CV: 136.9% ⚠️ HIGH VARIANCE

  challenge_continuity_score:
    Mean: 21.90 ± 22.18
    Range: 5.50 - 50.00
    95% CI: [2.46, 41.34]
    CV: 101.3% ⚠️ HIGH VARIANCE

  challenge_seeking_instances:
    Mean: 4.40 ± 1.34
    Range: 3.00 - 6.00
    95% CI: [3.22, 5.58]
    CV: 30.5% ⚠️ HIGH VARIANCE

  next_challenges_setup:
    Mean: 1.00 ± 0.00
    Range: 1.00 - 1.00
    95% CI: [1.00, 1.00]
    CV: 0.0%

  recovery_periods:
    Mean: 2.60 ± 0.55
    Range: 2.00 - 3.00
    95% CI: [2.12, 3.08]
    CV: 21.1% ⚠️ HIGH VARIANCE

  similar_challenge_repetitions:
    Mean: 2.20 ± 0.45
    Range: 2.00 - 3.00
    95% CI: [1.81, 2.59]
    CV: 20.3% ⚠️ HIGH VARIANCE


### C3. Complexity Exposure
Runs: 5/5 successful (100%)

  attention_directing_instances:
    Mean: 2.80 ± 1.10
    Range: 2.00 - 4.00
    95% CI: [1.84, 3.76]
    CV: 39.1% ⚠️ HIGH VARIANCE

  complexity_exposure_score:
    Mean: 39.44 ± 14.78
    Range: 22.50 - 62.50
    95% CI: [26.48, 52.40]
    CV: 37.5% ⚠️ HIGH VARIANCE

  context_dimensions_exposed:
    Mean: 2.90 ± 1.14
    Range: 1.50 - 4.00
    95% CI: [1.90, 3.90]
    CV: 39.3% ⚠️ HIGH VARIANCE

  explicit_instruction_instances:
    Mean: 3.60 ± 0.89
    Range: 3.00 - 5.00
    95% CI: [2.82, 4.38]
    CV: 24.8% ⚠️ HIGH VARIANCE

  interpreting_for_novice_instances:
    Mean: 5.00 ± 1.22
    Range: 3.00 - 6.00
    95% CI: [3.93, 6.07]
    CV: 24.5% ⚠️ HIGH VARIANCE

  learning_by_doing_instances:
    Mean: 4.80 ± 0.84
    Range: 4.00 - 6.00
    95% CI: [4.07, 5.53]
    CV: 17.4%

  orientation_hours:
    Mean: 0.75 ± 0.00
    Range: 0.75 - 0.75
    95% CI: [0.75, 0.75]
    CV: 0.0%

  reflection_time_hours:
    Mean: 0.10 ± 0.22
    Range: 0.00 - 0.50
    95% CI: [-0.10, 0.30]
    CV: 223.6% ⚠️ HIGH VARIANCE


### C4. Expert Guidance Quality
Runs: 5/5 successful (100%)

  ask_before_tell:
    Mean: 1.60 ± 0.89
    Range: 1.00 - 3.00
    95% CI: [0.82, 2.38]
    CV: 55.9% ⚠️ HIGH VARIANCE

  expert_guidance_score:
    Mean: 36.74 ± 18.03
    Range: 5.20 - 50.00
    95% CI: [20.94, 52.54]
    CV: 49.1% ⚠️ HIGH VARIANCE

  guidance_task_match:
    Mean: 3.40 ± 1.14
    Range: 2.00 - 5.00
    95% CI: [2.40, 4.40]
    CV: 33.5% ⚠️ HIGH VARIANCE

  guidance_task_mismatch:
    Mean: 2.20 ± 0.45
    Range: 2.00 - 3.00
    95% CI: [1.81, 2.59]
    CV: 20.3% ⚠️ HIGH VARIANCE

  help_appropriate_timing:
    Mean: 2.60 ± 0.89
    Range: 2.00 - 4.00
    95% CI: [1.82, 3.38]
    CV: 34.4% ⚠️ HIGH VARIANCE

  help_too_early:
    Mean: 1.20 ± 0.84
    Range: 0.00 - 2.00
    95% CI: [0.47, 1.93]
    CV: 69.7% ⚠️ HIGH VARIANCE

  help_too_late:
    Mean: 1.60 ± 0.55
    Range: 1.00 - 2.00
    95% CI: [1.12, 2.08]
    CV: 34.2% ⚠️ HIGH VARIANCE

  questions_dismissed:
    Mean: 3.80 ± 0.45
    Range: 3.00 - 4.00
    95% CI: [3.41, 4.19]
    CV: 11.8%

  questions_welcomed:
    Mean: 3.40 ± 0.55
    Range: 3.00 - 4.00
    95% CI: [2.92, 3.88]
    CV: 16.1%

  tell_without_asking:
    Mean: 7.40 ± 0.89
    Range: 6.00 - 8.00
    95% CI: [6.62, 8.18]
    CV: 12.1%


### C5. Relationship Health
Runs: 5/5 successful (100%)

  attunement_breaks:
    Mean: 4.00 ± 1.00
    Range: 3.00 - 5.00
    95% CI: [3.12, 4.88]
    CV: 25.0% ⚠️ HIGH VARIANCE

  attunement_signals:
    Mean: 5.80 ± 0.45
    Range: 5.00 - 6.00
    95% CI: [5.41, 6.19]
    CV: 7.7%

  relationship_health_score:
    Mean: 15.38 ± 21.60
    Range: 4.80 - 54.00
    95% CI: [-3.55, 34.31]
    CV: 140.4% ⚠️ HIGH VARIANCE

  respect_signals:
    Mean: 4.80 ± 0.45
    Range: 4.00 - 5.00
    95% CI: [4.41, 5.19]
    CV: 9.3%

  significance_signals:
    Mean: 2.60 ± 0.89
    Range: 1.00 - 3.00
    95% CI: [1.82, 3.38]
    CV: 34.4% ⚠️ HIGH VARIANCE

  trust_signals:
    Mean: 3.80 ± 0.45
    Range: 3.00 - 4.00
    95% CI: [3.41, 4.19]
    CV: 11.8%

  warmth_signals:
    Mean: 2.00 ± 0.00
    Range: 2.00 - 2.00
    95% CI: [2.00, 2.00]
    CV: 0.0%


### C6. Developmental Trajectory
Runs: 5/5 successful (100%)

  developmental_trajectory_score:
    Mean: 35.30 ± 4.60
    Range: 28.50 - 38.50
    95% CI: [31.26, 39.34]
    CV: 13.0%

  external_advocacy:
    Mean: 0.00 ± 0.00
    Range: 0.00 - 0.00
    95% CI: [0.00, 0.00]
    CV: 0.0%

  graduation_signals:
    Mean: 1.00 ± 0.00
    Range: 1.00 - 1.00
    95% CI: [1.00, 1.00]
    CV: 0.0%

  joint_goal_setting:
    Mean: 0.00 ± 0.00
    Range: 0.00 - 0.00
    95% CI: [0.00, 0.00]
    CV: 0.0%

  novice_authorship:
    Mean: 1.00 ± 0.00
    Range: 1.00 - 1.00
    95% CI: [1.00, 1.00]
    CV: 0.0%

  novice_teaching_others:
    Mean: 0.00 ± 0.00
    Range: 0.00 - 0.00
    95% CI: [0.00, 0.00]
    CV: 0.0%

  pure_execution:
    Mean: 4.60 ± 0.89
    Range: 4.00 - 6.00
    95% CI: [3.82, 5.38]
    CV: 19.4%

