export type ExperimentSummary = {
  id: string;
  experiment_id: string;
  status: string;
  git_commit: string | null;
  git_dirty: boolean | null;
  parent_experiment_id: string | null;
  val_bpb: number | null;
  duration_seconds: number | null;
  num_params: number | null;
  depth: number | null;
  vocab_size: number | null;
  max_seq_len: number | null;
  window_pattern: string | null;
  checkpoint_path: string | null;
  created_at: string;
};

export type Metric = {
  id: string;
  metric_name: string;
  metric_value: number;
  step: number | null;
  recorded_at: string;
};

export type Checkpoint = {
  id: string;
  checkpoint_path: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export type ExperimentDetail = ExperimentSummary & {
  started_at: string | null;
  completed_at: string | null;
  configuration: Record<string, unknown> | null;
  crash_message: string | null;
  metrics: Metric[];
  checkpoints: Checkpoint[];
};

export type ExperimentListResponse = {
  items: ExperimentSummary[];
  total: number;
  limit: number;
  offset: number;
};
