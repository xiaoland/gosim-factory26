### 0 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-6533a6edafdd94",
  "experiment_id": "exp-20260928-103626-22953b",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "186b7198e7a3aa0bd9b03d05",
  "controller": "controller-62835de08efe",
  "phase": "cancelled",
  "created_at": 1790562998.1347134,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "venue": "official-local-generation",
    "operation": "generate",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "7957f5517a3eaee695ad2227425818051f49f778243b4cd707bec8bbd70599bd",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/agent.zip",
      "sha256": "b377e0f2ae2739e55d1198e2b4b004e489d22cf4d6d1bcddaddbf60168ab8e4a",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0003/agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0009/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0010/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/agent/agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": [
    "workspace/official-generation/template/.arc/traceability",
    "workspace/official-generation/template/.arc/runner-events.jsonl",
    "workspace/official-generation/template/.arc/runtime-reporting"
  ],
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94",
        "--run-id",
        "pi-braid--hackathon--sheet-6533a6edafdd94"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94",
        "--run-id",
        "pi-braid--hackathon--sheet-6533a6edafdd94"
      ]
    ]
  },
  "started_at": 1790563010.966845,
  "pid": 124727,
  "process_start": "5595454",
  "pgid": 124727,
  "finished_at": 1790567071.6632085,
  "runner_exit_code": -15,
  "result_contract": "invalid",
  "result_error": "FileNotFoundError: /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/workspace/experiment-result.json",
  "artifacts": [
    {
      "path": "workspace/official-generation/template/.arc/traceability",
      "status": "available",
      "location": "workspace/official-generation/template/.arc/traceability",
      "kind": "directory"
    },
    {
      "path": "workspace/official-generation/template/.arc/runner-events.jsonl",
      "status": "available",
      "location": "workspace/official-generation/template/.arc/runner-events.jsonl",
      "kind": "file"
    },
    {
      "path": "workspace/official-generation/template/.arc/runtime-reporting",
      "status": "available",
      "location": "workspace/official-generation/template/.arc/runtime-reporting",
      "kind": "directory"
    }
  ],
  "telemetry": {
    "status": "received",
    "database": "workspace/official-generation/template/.factory26/20260928-025746-66feadac/telemetry.sqlite",
    "batches": 469,
    "until_batch_id": 469,
    "signals": {
      "traces": 25,
      "logs": 398,
      "metrics": 46
    }
  }
}

### 1 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-8b17a98231417f",
  "experiment_id": "exp-20260928-114834-41a5ca",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "26059230572ce5f1a110154a",
  "controller": "controller-b0f12c1c5dbb",
  "phase": "finished",
  "created_at": 1790567343.522673,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "venue": "official-local-generation",
    "operation": "generate",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "03-input-repair"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "da951896f651c77672fcb98534f2fa49d0011dd76a90eb0270f6d7412dadca4f",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/sheet-agent.zip",
      "sha256": "ff3efe48dde242b9bbb2e688ee350d285ddbafead1451e0c95a05d45ab30601c",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0009/sheet-agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/agent/sheet-agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f",
        "--run-id",
        "pi-braid--hackathon--sheet-8b17a98231417f"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/generation/runs/pi-braid--hackathon--sheet-8b17a98231417f",
        "--run-id",
        "pi-braid--hackathon--sheet-8b17a98231417f"
      ]
    ]
  },
  "started_at": 1790567344.655201,
  "pid": 188758,
  "process_start": "6028843",
  "pgid": 188758,
  "finished_at": 1790567938.844023,
  "runner_exit_code": 1,
  "result": {
    "schema_version": 1,
    "status": "failed",
    "stage": "generation",
    "generation_exit_code": 1,
    "generation": {
      "status": "failed",
      "exit_code": 1,
      "process_group_cleanup": "already-exited"
    },
    "image_id": "sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d",
    "error": "Agent generation did not produce a complete application"
  },
  "result_contract": "present",
  "artifacts": {
    "EXACT_SAME_AS": "0.artifacts"
  },
  "telemetry": {
    "status": "received",
    "database": "workspace/official-generation/template/.factory26/20260928-025746-66feadac/telemetry.sqlite",
    "batches": 492,
    "until_batch_id": 492,
    "signals": {
      "traces": 29,
      "logs": 415,
      "metrics": 48
    }
  }
}

### 2 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-bb12af664cce56",
  "experiment_id": "exp-20260928-121933-f7f473",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "6e3b9a269cf95c7f9d8a3303",
  "controller": "controller-3e713e135dc3",
  "phase": "finished",
  "created_at": 1790569193.2579355,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "venue": "official-local-generation",
    "operation": "generate",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "04-native-material-hotfix"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "acf8bc45b1c2c656691ca326db3bbf70e778b70ae9d156d036cb6c3fda8aa506",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/sheet-agent.zip",
      "sha256": "22ffdb80a16e0f1d093c80b33f976656f4f2ee6632b37494681da7f8a06a4e22",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0009/sheet-agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/agent/sheet-agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56",
        "--run-id",
        "pi-braid--hackathon--sheet-bb12af664cce56"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-04/generation/runs/pi-braid--hackathon--sheet-bb12af664cce56",
        "--run-id",
        "pi-braid--hackathon--sheet-bb12af664cce56"
      ]
    ]
  },
  "started_at": 1790569194.4954586,
  "pid": 194730,
  "process_start": "6213830",
  "pgid": 194730,
  "finished_at": 1790569474.8670447,
  "runner_exit_code": 1,
  "result": {
    "EXACT_SAME_AS": "1.result"
  },
  "result_contract": "present",
  "artifacts": [
    {
      "EXACT_SAME_AS": "0.artifacts[0]"
    },
    {
      "EXACT_SAME_AS": "0.artifacts[1]"
    },
    {
      "path": "workspace/official-generation/template/.arc/runtime-reporting",
      "status": "missing"
    }
  ],
  "telemetry": {
    "EXACT_SAME_AS": "1.telemetry"
  }
}

### 3 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-d40c0b57bb4a78",
  "experiment_id": "exp-20260928-122838-01f36b",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "f7ad899ddaa014713b96e3cb",
  "controller": "controller-6c2f2d9c5041",
  "phase": "finished",
  "created_at": 1790569737.2817075,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "venue": "official-local-generation",
    "operation": "generate",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "05-package-metadata-hotfix"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "d74d59cf0f9c13ce3cd574fb87a93cb62f51b58547dcd45f1ab0e6898d6ae9ff",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/sheet-agent.zip",
      "sha256": "8c652339d0e403ea694e2bb81799d4a268fbbba7271c64df1688f90a476f0298",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0009/sheet-agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/agent/sheet-agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78",
        "--run-id",
        "pi-braid--hackathon--sheet-d40c0b57bb4a78"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-05/generation/runs/pi-braid--hackathon--sheet-d40c0b57bb4a78",
        "--run-id",
        "pi-braid--hackathon--sheet-d40c0b57bb4a78"
      ]
    ]
  },
  "started_at": 1790569738.333357,
  "pid": 196488,
  "process_start": "6268217",
  "pgid": 196488,
  "finished_at": 1790570022.6124015,
  "runner_exit_code": 1,
  "result": {
    "EXACT_SAME_AS": "1.result"
  },
  "result_contract": "present",
  "artifacts": {
    "EXACT_SAME_AS": "2.artifacts"
  },
  "telemetry": {
    "status": "received",
    "database": "workspace/official-generation/template/.factory26/20260928-025746-66feadac/telemetry.sqlite",
    "batches": 511,
    "until_batch_id": 511,
    "signals": {
      "traces": 33,
      "logs": 428,
      "metrics": 50
    }
  }
}

### 4 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-e1454bb0055129",
  "experiment_id": "exp-20260928-124507-c581d8",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "590d2fdc47e2f1343a0e8f55",
  "controller": "controller-eccc0b464826",
  "phase": "cancelled",
  "created_at": 1790570727.5735338,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "venue": "official-local-generation",
    "operation": "generate",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "06-recovery-boundary-hotfix"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "d74d59cf0f9c13ce3cd574fb87a93cb62f51b58547dcd45f1ab0e6898d6ae9ff",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/sheet-agent.zip",
      "sha256": "121b27d09758e1cdd63c264e366b62dff84c35771a140273f579387414407bd6",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0009/sheet-agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/agent/sheet-agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129",
        "--run-id",
        "pi-braid--hackathon--sheet-e1454bb0055129"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129",
        "--run-id",
        "pi-braid--hackathon--sheet-e1454bb0055129"
      ]
    ]
  },
  "started_at": 1790570734.5018742,
  "pid": 199598,
  "process_start": "6367839",
  "pgid": 199598,
  "finished_at": 1790572749.9859948,
  "runner_exit_code": -15,
  "result_contract": "invalid",
  "result_error": "FileNotFoundError: /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/pi-braid--hackathon--sheet-e1454bb0055129/workspace/experiment-result.json",
  "artifacts": {
    "EXACT_SAME_AS": "2.artifacts"
  },
  "telemetry": {
    "status": "received",
    "database": "workspace/official-generation/template/.factory26/20260928-025746-66feadac/telemetry.sqlite",
    "batches": 862,
    "until_batch_id": 862,
    "signals": {
      "traces": 45,
      "logs": 738,
      "metrics": 79
    }
  }
}

### 5 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-28ca9afab308e8",
  "experiment_id": "exp-20260928-132728-d04f45",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "19ea8be0e38d0fd27ec15d1a",
  "controller": "controller-354e41eda673",
  "phase": "cancelled",
  "created_at": 1790573270.3862207,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "venue": "official-local-generation",
    "operation": "generate",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "07-visual-observability-hotfix",
    "local_resources": "4GiB-2CPU"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "b928653f2861352a90b3ae7b41c66448013b36511fcf34f2f5ac1ec4e673bf38",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/sheet-agent.zip",
      "sha256": "268f90b91ea6240afd4af37d8678bddaf1294f5ae24cba1200fbb5da4b2c9b59",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0009/sheet-agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/agent/sheet-agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only",
    "--memory",
    "4g",
    "--cpus",
    "2"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8",
        "--run-id",
        "pi-braid--hackathon--sheet-28ca9afab308e8"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8",
        "--run-id",
        "pi-braid--hackathon--sheet-28ca9afab308e8"
      ]
    ]
  },
  "started_at": 1790573271.3709483,
  "pid": 231705,
  "process_start": "6621550",
  "pgid": 231705,
  "finished_at": 1790576820.028518,
  "runner_exit_code": -15,
  "result_contract": "invalid",
  "result_error": "FileNotFoundError: /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/pi-braid--hackathon--sheet-28ca9afab308e8/workspace/experiment-result.json",
  "artifacts": {
    "EXACT_SAME_AS": "2.artifacts"
  },
  "telemetry": {
    "status": "received",
    "database": "workspace/official-generation/template/.factory26/20260928-025746-66feadac/telemetry.sqlite",
    "batches": 1349,
    "until_batch_id": 1349,
    "signals": {
      "traces": 193,
      "logs": 1024,
      "metrics": 132
    }
  }
}

### 6 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-d478f7dc8ff84f",
  "experiment_id": "exp-20260928-143632-3b9193",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "c5c7bc9791313e6b30e80102",
  "controller": "controller-e5aeaba7123a",
  "phase": "cancelled",
  "created_at": 1790577422.3243341,
  "labels": {
    "EXACT_SAME_AS": "5.labels"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "b928653f2861352a90b3ae7b41c66448013b36511fcf34f2f5ac1ec4e673bf38",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/sheet-agent-v2.zip",
      "sha256": "1ec2948d0f7982aba3872608e270c7ced2107452f37d61dc0c4d7b3286f200be",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0009/sheet-agent-v2.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/agent/sheet-agent-v2.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only",
    "--memory",
    "4g",
    "--cpus",
    "2"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f",
        "--run-id",
        "pi-braid--hackathon--sheet-d478f7dc8ff84f"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f",
        "--run-id",
        "pi-braid--hackathon--sheet-d478f7dc8ff84f"
      ]
    ]
  },
  "started_at": 1790577423.3416831,
  "pid": 354319,
  "process_start": "7036833",
  "pgid": 354319,
  "finished_at": 1790583170.8592472,
  "runner_exit_code": -15,
  "result_contract": "invalid",
  "result_error": "FileNotFoundError: /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace/experiment-result.json",
  "artifacts": {
    "EXACT_SAME_AS": "2.artifacts"
  },
  "telemetry": {
    "status": "received",
    "database": "workspace/official-generation/template/.factory26/20260928-025746-66feadac/telemetry.sqlite",
    "batches": 2180,
    "until_batch_id": 2180,
    "signals": {
      "traces": 342,
      "logs": 1618,
      "metrics": 220
    }
  }
}

### 7 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-6aa15927132124",
  "experiment_id": "exp-20260928-164648-ffb8b1",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "8ea221e7196c761b5e210e78",
  "controller": "controller-bc5767341fe5",
  "phase": "finished",
  "created_at": 1790585213.193232,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "operation": "continue-generation",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "09-continuation-01",
    "local_resources": "4GiB-2CPU",
    "source_run_id": "pi-braid--hackathon--sheet-984a08e3155e3e",
    "retained_generation": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation",
    "mode": "local-workspace-continuation"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": null,
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "6d814e366985ab2a1d66ef3ab6b1d9d0e4331535b48952cd1bb715660587b1d3",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0001/content"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0009/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0010/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0004/hackathon_gateway.py"
    },
    "launcher": {
      "path": "inputs/launcher/continue-container.py",
      "sha256": "b5ef8da5a6922d91dfd84e672281b10a82e67110a7ef613d6d29bf0a33b23933",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0005/continue-container.py"
    },
    "entry": {
      "path": "inputs/entry/continue-in-place.py",
      "sha256": "f228164f1569bc53fdcffe168e361103ef9743c895924b5e12d1e000bdb908ff",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0006/continue-in-place.py"
    },
    "binary": {
      "path": "inputs/binary/braid-linux-provider-error-v1",
      "sha256": "9eddeac8c66549e78f247ad380ccc04bcd0020cbadfa8911b16e6726e250abf8",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0007/braid-linux-provider-error-v1"
    },
    "braid_source": {
      "path": "inputs/braid_source/braid-source-provider-error-v1.tar.gz",
      "sha256": "ef1d463f6d42d9222db4052be1ea70f6e0779228c969301cb44f7570e0bfe758",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/inputs/input-0008/braid-source-provider-error-v1.tar.gz"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/launcher/continue-container.py",
    "--source-run",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/workspace",
    "--binary",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/binary/braid-linux-provider-error-v1",
    "--entry",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/entry/continue-in-place.py",
    "--adapter",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/adapter"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": [
    "workspace/official-generation/.lab-artifacts/receipt.json",
    "workspace/generation.resource.json",
    "workspace/container-cleanup.json"
  ],
  "adapter_kind": "local-braid-continuation",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124",
        "--run-id",
        "pi-braid--hackathon--sheet-6aa15927132124"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-01/generation/runs/pi-braid--hackathon--sheet-6aa15927132124",
        "--run-id",
        "pi-braid--hackathon--sheet-6aa15927132124"
      ]
    ]
  },
  "started_at": 1790585214.7569027,
  "pid": 504968,
  "process_start": "7816023",
  "pgid": 504968,
  "finished_at": 1790585250.383127,
  "runner_exit_code": 1,
  "result": {
    "schema_version": 1,
    "status": "failed",
    "mode": "local-workspace-continuation",
    "source_run_id": "pi-braid--hackathon--sheet-984a08e3155e3e",
    "retained_braid_run_id": "20260928-025746-66feadac",
    "image_id": "sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d",
    "container_exit_code": 1,
    "error": "RuntimeError: Continuation container exited 1"
  },
  "result_contract": "present",
  "artifacts": [
    {
      "path": "workspace/official-generation/.lab-artifacts/receipt.json",
      "status": "missing"
    },
    {
      "path": "workspace/generation.resource.json",
      "status": "available",
      "location": "workspace/generation.resource.json",
      "kind": "file"
    },
    {
      "path": "workspace/container-cleanup.json",
      "status": "available",
      "location": "workspace/container-cleanup.json",
      "kind": "file"
    }
  ],
  "telemetry": {
    "status": "absent",
    "database": "telemetry.sqlite",
    "batches": 0,
    "until_batch_id": null,
    "signals": {
      "traces": 0,
      "logs": 0,
      "metrics": 0
    }
  }
}

### 8 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-2295267a737e43",
  "experiment_id": "exp-20260928-165109-e225f7",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "d175083f5ee358a4a64b84e2",
  "controller": "controller-4c5cc100214f",
  "phase": "finished",
  "created_at": 1790585474.1401918,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "operation": "continue-generation",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "09-continuation-02",
    "local_resources": "4GiB-2CPU",
    "source_run_id": "pi-braid--hackathon--sheet-984a08e3155e3e",
    "retained_generation": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation",
    "mode": "local-workspace-continuation",
    "retry_of_continuation": "continuation-01"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": null,
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "6d814e366985ab2a1d66ef3ab6b1d9d0e4331535b48952cd1bb715660587b1d3",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0001/content"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0009/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0010/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0004/hackathon_gateway.py"
    },
    "launcher": {
      "path": "inputs/launcher/continue-container.py",
      "sha256": "b5ef8da5a6922d91dfd84e672281b10a82e67110a7ef613d6d29bf0a33b23933",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0005/continue-container.py"
    },
    "entry": {
      "path": "inputs/entry/continue-in-place.py",
      "sha256": "f228164f1569bc53fdcffe168e361103ef9743c895924b5e12d1e000bdb908ff",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0006/continue-in-place.py"
    },
    "binary": {
      "path": "inputs/binary/braid-linux-provider-error-v1",
      "sha256": "9eddeac8c66549e78f247ad380ccc04bcd0020cbadfa8911b16e6726e250abf8",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0007/braid-linux-provider-error-v1"
    },
    "braid_source": {
      "path": "inputs/braid_source/braid-source-provider-error-v1.tar.gz",
      "sha256": "ef1d463f6d42d9222db4052be1ea70f6e0779228c969301cb44f7570e0bfe758",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/inputs/input-0008/braid-source-provider-error-v1.tar.gz"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/launcher/continue-container.py",
    "--source-run",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/workspace",
    "--binary",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/binary/braid-linux-provider-error-v1",
    "--entry",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/entry/continue-in-place.py",
    "--adapter",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/adapter"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "7.artifact_paths"
  },
  "adapter_kind": "local-braid-continuation",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43",
        "--run-id",
        "pi-braid--hackathon--sheet-2295267a737e43"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-02/generation/runs/pi-braid--hackathon--sheet-2295267a737e43",
        "--run-id",
        "pi-braid--hackathon--sheet-2295267a737e43"
      ]
    ]
  },
  "started_at": 1790585475.803947,
  "pid": 505859,
  "process_start": "7842129",
  "pgid": 505859,
  "finished_at": 1790585510.3198934,
  "runner_exit_code": 1,
  "result": {
    "EXACT_SAME_AS": "7.result"
  },
  "result_contract": "present",
  "artifacts": {
    "EXACT_SAME_AS": "7.artifacts"
  },
  "telemetry": {
    "EXACT_SAME_AS": "7.telemetry"
  }
}

### 9 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-22730f82778f3a",
  "experiment_id": "exp-20260928-172000-391108",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "01bd8e4ca8cb3e5a1fb76800",
  "controller": "controller-5f5b3e18d655",
  "phase": "cancelled",
  "created_at": 1790587202.6883433,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "operation": "continue-generation",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "09-continuation-03",
    "local_resources": "4GiB-2CPU",
    "source_run_id": "pi-braid--hackathon--sheet-984a08e3155e3e",
    "retained_generation": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation",
    "mode": "local-workspace-continuation",
    "retry_of_continuation": "continuation-02"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": null,
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "6d814e366985ab2a1d66ef3ab6b1d9d0e4331535b48952cd1bb715660587b1d3",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0001/content"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0004/hackathon_gateway.py"
    },
    "launcher": {
      "path": "inputs/launcher/continue-container.py",
      "sha256": "a4733eedd31c84aab51490ab303b68ccde6e7ea759b87359b95b5fd0a3346b0a",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0005/continue-container.py"
    },
    "entry": {
      "path": "inputs/entry/continue-in-place.py",
      "sha256": "3a36d22c96dff4d5a633600999b0cfefe1b893f1b5bd57d8b6810fb32193002f",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0006/continue-in-place.py"
    },
    "binary": {
      "path": "inputs/binary/braid-linux-roles-v1",
      "sha256": "74739b9d330eb5649d3d3b8624d5da8507a36ba094a2aadf4ba9a8f389f12b38",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0007/braid-linux-roles-v1"
    },
    "braid_source": {
      "path": "inputs/braid_source/braid-source-roles-v1.tar.gz",
      "sha256": "70e867ee3c3d1e19645c6907eb35c446e0b62ad11c7a774e1d9aa2088971c82d",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0008/braid-source-roles-v1.tar.gz"
    },
    "native_increment": {
      "path": "inputs/native_increment/native-increment.tar.gz",
      "sha256": "ae82105c5c9421dc203ba23d484a3f797f5b270dfe1275189a7c62080659f4dd",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/inputs/input-0009/native-increment.tar.gz"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/launcher/continue-container.py",
    "--source-run",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/workspace",
    "--binary",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/binary/braid-linux-roles-v1",
    "--entry",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/entry/continue-in-place.py",
    "--adapter",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/adapter"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "7.artifact_paths"
  },
  "adapter_kind": "local-braid-continuation",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a",
        "--run-id",
        "pi-braid--hackathon--sheet-22730f82778f3a"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a",
        "--run-id",
        "pi-braid--hackathon--sheet-22730f82778f3a"
      ]
    ]
  },
  "started_at": 1790587203.7069578,
  "pid": 509790,
  "process_start": "8014920",
  "pgid": 509790,
  "finished_at": 1790600503.7542427,
  "runner_exit_code": -15,
  "result_contract": "invalid",
  "result_error": "FileNotFoundError: /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a/workspace/experiment-result.json",
  "artifacts": [
    {
      "path": "workspace/official-generation/.lab-artifacts/receipt.json",
      "status": "missing"
    },
    {
      "EXACT_SAME_AS": "7.artifacts[1]"
    },
    {
      "path": "workspace/container-cleanup.json",
      "status": "missing"
    }
  ],
  "telemetry": {
    "EXACT_SAME_AS": "7.telemetry"
  }
}

### 10 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-984a08e3155e3e",
  "experiment_id": "exp-20260928-162001-28cd28",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "c95783a8bd8c338ccadccfea",
  "controller": "controller-8c71659321ef",
  "phase": "cancelled",
  "created_at": 1790583647.5854726,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "venue": "official-local-generation",
    "operation": "generate",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "09-feedback-delegation-hotfix",
    "local_resources": "4GiB-2CPU"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "6d814e366985ab2a1d66ef3ab6b1d9d0e4331535b48952cd1bb715660587b1d3",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/sheet-agent.zip",
      "sha256": "b14eaee01633fa8970fa2b7a7e5a10230f5ee18781a099f13e7436129574093b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0009/sheet-agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0010/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0011/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/agent/sheet-agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only",
    "--memory",
    "4g",
    "--cpus",
    "2"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e",
        "--run-id",
        "pi-braid--hackathon--sheet-984a08e3155e3e"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e",
        "--run-id",
        "pi-braid--hackathon--sheet-984a08e3155e3e"
      ]
    ]
  },
  "started_at": 1790583648.803395,
  "pid": 490734,
  "process_start": "7659413",
  "pgid": 490734,
  "finished_at": 1790584547.3984783,
  "runner_exit_code": -15,
  "result_contract": "invalid",
  "result_error": "FileNotFoundError: /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/experiment-result.json",
  "artifacts": {
    "EXACT_SAME_AS": "2.artifacts"
  },
  "telemetry": {
    "status": "received",
    "database": "workspace/official-generation/template/.factory26/20260928-025746-66feadac/telemetry.sqlite",
    "batches": 2304,
    "until_batch_id": 2304,
    "signals": {
      "traces": 375,
      "logs": 1704,
      "metrics": 225
    }
  }
}

### 11 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-640297261bdf0c",
  "experiment_id": "exp-20260928-103445-16a125",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "8b2c5431761df9ac9e3cfe89",
  "controller": "controller-b84e3ae36801",
  "phase": "cancelled",
  "created_at": 1790562908.9215944,
  "labels": {
    "EXACT_SAME_AS": "0.labels"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": "official-local-generation",
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "7957f5517a3eaee695ad2227425818051f49f778243b4cd707bec8bbd70599bd",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0001/content"
    },
    "runner": {
      "path": "inputs/runner",
      "sha256": "73f2aa69fc735328f67490ab23734dc1317521b997c6402ee03c2db2d716b282",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0002/content"
    },
    "agent": {
      "path": "inputs/agent/agent.zip",
      "sha256": "ab43e59a7db44c71df13493522f0a06022bffeca057dff75bbeaed5d0b69a2e7",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0003/agent.zip"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0009/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0010/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0006/hackathon_gateway.py"
    },
    "gateway_service": {
      "path": "inputs/gateway_service/service.json",
      "sha256": "1a56b754d702c0cd0ec6ef87b6cc52a23f25158e9123a8566a57e5b3e1b78ed3",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0007/service.json"
    },
    "gateway_callback": {
      "path": "inputs/gateway_callback/hackathon_gateway_compat.py",
      "sha256": "0ddd309a389ac23df0d0fd8c3e51346750dcd9b31cc15bdfe857672638b1e799",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/inputs/input-0008/hackathon_gateway_compat.py"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/adapter/arc_bench_adapter.py",
    "--runner",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/runner",
    "--agent",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/agent/agent.zip",
    "--requirements",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/requirements",
    "--workspace",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/workspace",
    "--competition",
    "hackathon",
    "--task",
    "sheet",
    "--image",
    "arcbench-local-submit:latest",
    "--requirements-only"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "0.artifact_paths"
  },
  "adapter_kind": "arc-bench",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c",
        "--run-id",
        "pi-braid--hackathon--sheet-640297261bdf0c"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c",
        "--run-id",
        "pi-braid--hackathon--sheet-640297261bdf0c"
      ]
    ]
  },
  "started_at": 1790562912.5555308,
  "pid": 124172,
  "process_start": "5585584",
  "pgid": 124172,
  "finished_at": 1790562915.9515574,
  "runner_exit_code": -15,
  "result_contract": "invalid",
  "result_error": "FileNotFoundError: /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/generation/runs/pi-braid--hackathon--sheet-640297261bdf0c/workspace/experiment-result.json",
  "artifacts": [
    {
      "path": "workspace/official-generation/template/.arc/traceability",
      "status": "missing"
    },
    {
      "path": "workspace/official-generation/template/.arc/runner-events.jsonl",
      "status": "missing"
    },
    {
      "path": "workspace/official-generation/template/.arc/runtime-reporting",
      "status": "missing"
    }
  ],
  "telemetry": {
    "EXACT_SAME_AS": "7.telemetry"
  }
}

### 12 /home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/run.json
{
  "schema_version": 2,
  "record_type": "lab.run",
  "run_id": "pi-braid--hackathon--sheet-130e238edd5a6a",
  "experiment_id": "exp-20260928-210800-64ceb0",
  "job_id": "pi-braid--hackathon--sheet",
  "attempt": 1,
  "retry_of": null,
  "trigger_operation": "bef2448532ae8792f53c135e",
  "controller": "controller-f189af3186ee",
  "phase": "finished",
  "created_at": 1790600882.1914427,
  "labels": {
    "competition": "hackathon",
    "variant": "pi-braid",
    "task": "sheet",
    "operation": "continue-generation",
    "experiment_key": "e20260928-02",
    "declared_variant": "pi-braid",
    "recovery_attempt": "09-sheet-materialization-recovery",
    "local_resources": "4GiB-2CPU",
    "source_run_id": "pi-braid--hackathon--sheet-22730f82778f3a",
    "retained_generation": "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation",
    "mode": "local-workspace-continuation",
    "retry_of_continuation": "continuation-02",
    "recovery_reason": "interrupted materialization without provider",
    "stopped_execution_run_id": "pi-braid--hackathon--sheet-22730f82778f3a"
  },
  "competition": "hackathon",
  "variant": "pi-braid",
  "task": "sheet",
  "venue": null,
  "inputs": {
    "adapter": {
      "path": "inputs/adapter",
      "sha256": "9f6cee29f7bd81f5976fb0f645a630bc6dcaf26c6cc32cdd2ea2add1760734d8",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0001/content"
    },
    "requirements": {
      "path": "inputs/requirements",
      "sha256": "e6ce667c8e40c7b5cffdc69e108776d233ea3cdf9ad287b7a9878d8af63c3644",
      "algorithm": "tree-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0002/content"
    },
    "source": {
      "path": "inputs/source/source.json",
      "sha256": "7430aa4c58e8e2553118f6d1b9ac0f7262714fbb5fc9a7421ea75887aa65ce69",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0003/source.json"
    },
    "gateway": {
      "path": "inputs/gateway/hackathon_gateway.py",
      "sha256": "55a1fe3a4f12a2d52a5e1e6ee1d795b806f65b609bb1a770726e1eb4072d545b",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0004/hackathon_gateway.py"
    },
    "launcher": {
      "path": "inputs/launcher/continue-container.py",
      "sha256": "606d507a16cac35630c38c3bf7a4051e8f62d30a583e5fd29fbea3187ff5e162",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0005/continue-container.py"
    },
    "entry": {
      "path": "inputs/entry/continue-in-place.py",
      "sha256": "352cd6cbd75ac0090b691c7f236d3f326c2babc8e6fc10358afb524536e82d23",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0006/continue-in-place.py"
    },
    "binary": {
      "path": "inputs/binary/braid-linux",
      "sha256": "e80b0f7bac73bf1e3fde4de9cfc370eda8a79a7428f95d7abccd6c196a6b96c6",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0007/braid-linux"
    },
    "braid_source": {
      "path": "inputs/braid_source/braid-source.tar.gz",
      "sha256": "268d6d4202aac46cbc5e48a85666ee57956b2c58f5b857e62b67c8e408050c17",
      "algorithm": "file-bytes-sha256-v1",
      "source": "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/inputs/input-0008/braid-source.tar.gz"
    }
  },
  "command": [
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
    "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/gateway/hackathon_gateway.py",
    "wrap",
    "--service-state",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
    "--url-env",
    "OPENAI_BASE_URL",
    "--key-env",
    "OPENAI_API_KEY",
    "--env-file-var",
    "ARC_MODEL_ENV_FILE",
    "--",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/venv/bin/python",
    "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/launcher/continue-container.py",
    "--source-run",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a",
    "--workspace",
    "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/workspace",
    "--binary",
    "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/binary/braid-linux",
    "--entry",
    "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/entry/continue-in-place.py",
    "--adapter",
    "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/adapter",
    "--retained-generation",
    "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation"
  ],
  "result_path": "workspace/experiment-result.json",
  "artifact_paths": {
    "EXACT_SAME_AS": "7.artifact_paths"
  },
  "adapter_kind": "local-braid-continuation",
  "resource_handlers": {
    "inspect": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "inspect",
        "--workspace",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/gateway/hackathon_gateway.py",
        "resource",
        "inspect",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a",
        "--run-id",
        "pi-braid--hackathon--sheet-130e238edd5a6a"
      ]
    ],
    "cleanup": [
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/adapter/arc_bench_adapter.py",
        "resource",
        "cleanup",
        "--workspace",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/workspace"
      ],
      [
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code/../venv/bin/python",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a/inputs/gateway/hackathon_gateway.py",
        "resource",
        "cleanup",
        "--service-state",
        "/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/gateway",
        "--run-dir",
        "/home/yyh/Development/factory26/runs/sheet-materialization-recovery/generation/runs/pi-braid--hackathon--sheet-130e238edd5a6a",
        "--run-id",
        "pi-braid--hackathon--sheet-130e238edd5a6a"
      ]
    ]
  },
  "started_at": 1790600883.135395,
  "pid": 709549,
  "process_start": "9382963",
  "pgid": 709549,
  "finished_at": 1790600980.2070072,
  "runner_exit_code": 0,
  "result": {
    "schema_version": 1,
    "status": "completed",
    "mode": "local-workspace-continuation",
    "source_run_id": "pi-braid--hackathon--sheet-22730f82778f3a",
    "retained_braid_run_id": "20260928-025746-66feadac",
    "image_id": "sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d",
    "container_exit_code": 0,
    "generation": {
      "status": "completed",
      "exit_code": 0,
      "process_group_cleanup": "already-exited",
      "application_sha256": "9022b53b7a827a3dd29df7477a5645e2207450fb0aa25efd97ae0a527ac7f28f"
    },
    "application_sha256": "9022b53b7a827a3dd29df7477a5645e2207450fb0aa25efd97ae0a527ac7f28f"
  },
  "result_contract": "present",
  "artifacts": [
    {
      "path": "workspace/official-generation/.lab-artifacts/receipt.json",
      "status": "available",
      "location": "workspace/official-generation/.lab-artifacts/receipt.json",
      "kind": "file"
    },
    {
      "EXACT_SAME_AS": "7.artifacts[1]"
    },
    {
      "EXACT_SAME_AS": "7.artifacts[2]"
    },
    {
      "path": "workspace/official-generation/.lab-artifacts/receipt.json",
      "status": "published",
      "kind": "application",
      "receipt": "workspace/official-generation/.lab-artifacts/receipt.json"
    }
  ],
  "telemetry": {
    "EXACT_SAME_AS": "7.telemetry"
  }
}