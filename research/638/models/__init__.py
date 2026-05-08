from .model_basic_heuristic import MODEL as BASIC_HEURISTIC_MODEL
from .model_bayesian_smoothing import MODEL as BAYESIAN_SMOOTHING_MODEL
from .model_deficit_only import MODEL as DEFICIT_ONLY_MODEL
from .model_gap_deficit_lr import MODEL as GAP_DEFICIT_LR_MODEL
from .model_gap_deficit_recent_lr import MODEL as GAP_DEFICIT_RECENT_LR_MODEL
from .model_gap_deficit_recent_time_lr_v2 import MODEL as GAP_DEFICIT_RECENT_TIME_LR_V2_MODEL
from .model_gap_only import MODEL as GAP_ONLY_MODEL
from .model_historical_frequency import MODEL as HISTORICAL_FREQUENCY_MODEL
from .model_markov_transition import MODEL as MARKOV_TRANSITION_MODEL
from .model_recent_window import MODEL as RECENT_WINDOW_MODEL
from .model_time_decay import MODEL as TIME_DECAY_MODEL
from .model_uniform_random import MODEL as UNIFORM_RANDOM_MODEL


ALL_MODELS = [
    UNIFORM_RANDOM_MODEL,
    HISTORICAL_FREQUENCY_MODEL,
    BAYESIAN_SMOOTHING_MODEL,
    RECENT_WINDOW_MODEL,
    TIME_DECAY_MODEL,
    MARKOV_TRANSITION_MODEL,
    GAP_ONLY_MODEL,
    DEFICIT_ONLY_MODEL,
    GAP_DEFICIT_LR_MODEL,
    GAP_DEFICIT_RECENT_LR_MODEL,
    GAP_DEFICIT_RECENT_TIME_LR_V2_MODEL,
    BASIC_HEURISTIC_MODEL,
]
