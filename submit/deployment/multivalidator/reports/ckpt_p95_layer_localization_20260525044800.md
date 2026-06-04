# Checkpoint long-gap localization — two_validator_pressure rep10

- Generated (UTC): 2026-05-25T04:48:00+00:00
- Source: existing INFO-level sui-node logs from rep10 evidence/container_state/
- Fullnode checkpoint events parsed: 872
- Consecutive (seq, seq+1) intervals analysed: 871
- Gap distribution (ms): min=1.4, p50=217.9, p95=285.5, max=2679.6

## Top 10 longest checkpoint gaps

| rank | from_seq | to_seq | gap_ms | from_ts (UTC) |
| ---: | ---: | ---: | ---: | --- |
| 1 | 789 | 790 | 2679.6 | 2026-05-24T12:47:08.942+00:00 |
| 2 | 528 | 529 | 2639.9 | 2026-05-24T12:46:08.911+00:00 |
| 3 | 266 | 267 | 2617.5 | 2026-05-24T12:45:08.902+00:00 |
| 4 | 1 | 2 | 2510.1 | 2026-05-24T12:44:09.064+00:00 |
| 5 | 268 | 269 | 770.1 | 2026-05-24T12:45:11.629+00:00 |
| 6 | 0 | 1 | 687.0 | 2026-05-24T12:44:08.377+00:00 |
| 7 | 338 | 339 | 646.8 | 2026-05-24T12:45:27.530+00:00 |
| 8 | 791 | 792 | 536.3 | 2026-05-24T12:47:11.733+00:00 |
| 9 | 583 | 584 | 534.0 | 2026-05-24T12:46:23.800+00:00 |
| 10 | 295 | 296 | 508.0 | 2026-05-24T12:45:17.598+00:00 |

## Per-validator activity counts during each long-gap window
(window = [from_ts - 200ms, to_ts + 200ms]; counts are log-line matches per layer pattern)

### Gap #1: seq 789→790, 2679.6 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 45 | 2 | 1 | 1 | 0 | 0 | 0 |
| validator-2 | 45 | 2 | 1 | 1 | 0 | 0 | 0 |
| validator-3 | 45 | 2 | 1 | 1 | 0 | 0 | 0 |

### Gap #2: seq 528→529, 2639.9 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 47 | 2 | 1 | 1 | 0 | 0 | 0 |
| validator-2 | 47 | 2 | 1 | 1 | 0 | 0 | 0 |
| validator-3 | 47 | 2 | 1 | 1 | 0 | 0 | 0 |

### Gap #3: seq 266→267, 2617.5 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 48 | 2 | 1 | 1 | 0 | 0 | 0 |
| validator-2 | 45 | 2 | 1 | 1 | 0 | 0 | 0 |
| validator-3 | 48 | 2 | 1 | 1 | 0 | 0 | 0 |

### Gap #4: seq 1→2, 2510.1 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 56 | 4 | 1 | 1 | 0 | 0 | 0 |
| validator-2 | 56 | 4 | 1 | 1 | 0 | 0 | 0 |
| validator-3 | 56 | 4 | 1 | 1 | 0 | 0 | 0 |

### Gap #5: seq 268→269, 770.1 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 33 | 1 | 0 | 0 | 0 | 0 | 0 |
| validator-2 | 29 | 1 | 0 | 0 | 0 | 0 | 0 |
| validator-3 | 29 | 1 | 0 | 0 | 0 | 0 | 0 |

### Gap #6: seq 0→1, 687.0 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 24 | 3 | 0 | 0 | 0 | 0 | 0 |
| validator-2 | 24 | 3 | 0 | 0 | 0 | 0 | 0 |
| validator-3 | 24 | 2 | 0 | 0 | 0 | 0 | 0 |

### Gap #7: seq 338→339, 646.8 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |
| validator-2 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |
| validator-3 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |

### Gap #8: seq 791→792, 536.3 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 15 | 1 | 0 | 0 | 0 | 0 | 0 |
| validator-2 | 13 | 1 | 0 | 0 | 0 | 0 | 0 |
| validator-3 | 13 | 1 | 0 | 0 | 0 | 0 | 0 |

### Gap #9: seq 583→584, 534.0 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |
| validator-2 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |
| validator-3 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |

### Gap #10: seq 295→296, 508.0 ms
| validator | consensus_round | mysticeti_block | rbc_certify | checkpoint_builder | narwhal_dag | warn_or_error | network_io |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| validator-1 | 28 | 0 | 0 | 0 | 0 | 0 | 0 |
| validator-2 | 24 | 0 | 0 | 0 | 0 | 0 | 0 |
| validator-3 | 24 | 0 | 0 | 0 | 0 | 0 | 0 |
