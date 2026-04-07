# Analysis: ml_service and mios Control Mechanism

This document explains how the `ml_service` component interacts with and controls the [mios](file:///Users/chengchung.lee/sources/mios/ml_service/ml_service.py#34-48) service within the robotics framework.

## Task vs. Trial

In this architecture, "Task" and "Trial" represent different layers of abstraction:

### **Trial** (`ml_service` Context)
-   **Purpose**: A single iteration of a machine learning experiment (e.g., testing one set of optimizer parameters).
-   **Container**: Managed by the [Engine](file:///Users/chengchung.lee/sources/mios/ml_service/engine/engine.py#73-623) in `ml_service`.
-   **Contents**: Includes the experiment parameters ($\theta$), the robot instructions to execute, and the logic for resetting/rescuing the robot.
-   **Output**: A `TaskResult` summarizing cost, success, and performance for the ML model.

### **Task** ([mios](file:///Users/chengchung.lee/sources/mios/ml_service/ml_service.py#34-48) Context)
-   **Purpose**: The actual program or sequence of physical actions executed by the robot.
-   **Container**: Managed by the [mios](file:///Users/chengchung.lee/sources/mios/ml_service/ml_service.py#34-48) service on the robot controller.
-   **Contents**: A list of **Skills** (e.g., `Grasp`, `Wiggle`, `Move`) with specific control parameters (forces, positions, speeds).
-   **Output**: Telemetry, execution status, and low-level results.

**Relationship**: A single **Trial** typically involves executing multiple **Tasks** on the robot (e.g., one task for the experimental trial and another task for the post-trial reset).

## Architecture Overview

The `ml_service` is a Python-based component designed for machine learning and optimization tasks applied to robot control. It acts as a high-level controller that uses [mios](file:///Users/chengchung.lee/sources/mios/ml_service/ml_service.py#34-48) as its execution engine for physical robot movements and skill execution.

### Key Components

1.  **Interface ([ml_service/interface/interface.py](file:///Users/chengchung.lee/sources/mios/ml_service/interface/interface.py))**: Provides an RPC server to remotely control the `ml_service`. It manages various learning services and their lifecycles.
2.  **Services (`ml_service/services/`)**: Implements specific ML algorithms (e.g., `CMAESService`, `SVMService`). These services inherit from `BaseService` and define the logic for parameter optimization.
3.  **Engine (`ml_service/engine/engine.py`)**: The core communication bridge. It manages a pool of "agents" (robots running `mios`) and handles the queuing and execution of trials.
4.  **WebSocket Client (`ml_service/utils/ws_client.py`)**: Provides the low-level communication layer using WebSockets to send commands and receive feedback from `mios`.

## Querying Trials

Trial data is stored in **MongoDB** and can be queried using either the low-level `MongoDBClient` or the high-level `KnowledgeManager`.

### 1. Direct MongoDB Query (Raw Trials)
All trials are stored in the `ml_results` database. Each collection within this database is named after a `skill_class` (e.g., `HeavyInsertion`).

```python
from mongodb_client.mongodb_client import MongoDBClient

client = MongoDBClient(host='localhost', port=27017)
# Query all documents (learning sessions) for a specific skill
sessions = client.read(db="ml_results", collection="HeavyInsertion", search_param={})
```

Each session document contains individual trials as nested fields: `n0`, `n1`, `n2`, etc.

### 2. High-Level Query (`KnowledgeManager`)
The `KnowledgeManager` provides a structured way to fetch trials, often filtering by tags or task identity.

```python
from knowledge_processor.knowledge_manager import KnowledgeManager

km = KnowledgeManager(host='localhost')
skill_identifier = {
    "tags": ["experiment_tag_1"],
    "skill_class": "HeavyInsertion"
}

# Returns a list of docs containing the trials
trials_data = km.collect_data(km.DBclient, skill_identifier)
```

**Common Query Filters**:
-   `meta.tags`: Filter by experimental batch.
-   `meta.skill_class`: Filter by robot action type.
-   `meta.uuid`: Filter by specific learning session.

## Communication Protocol

Control is achieved primarily through **WebSockets**, using a JSON-RPC-style message format.

-   **Port**: `mios` typically listens on port `12000`.
-   **Endpoints**: The main endpoint used is `mios/core`.
-   **Methods**: Common methods called on `mios` include:
    -   `start_task`: Initiates a robot task with specific parameters.
    -   `wait_for_task`: Blocks until a task completes and returns results.
    -   `stop_task`: Aborts the current execution.
    -   `is_busy`: Checks the current status of the robot.
    -   `get_state`: Retrieves the internal state/telemetry of the robot.

## Task Execution Flow

The typical control loop for a machine learning trial follows these steps:

1.  **Parameter Generation**: The ML service (e.g., CMA-ES) generates a new set of parameters ($\theta$).
2.  **Context Mapping**: These parameters are mapped into a `task_context` which contains one or more **Skills** (e.g., `HeavyInsertion`, `Grasp`).
3.  **Trial Submission**: The `Engine` picks an available agent and sends the `task_context` via `start_task`.
4.  **Execution and Monitoring**: `mios` executes the skill on the physical robot. The `Engine` waits for the `task_uuid` to complete.
5.  **Result Retrieval**: Once finished, `mios` returns a `task_result` containing success/failure status and quality metrics (e.g., forces, duration).
6.  **Cost Calculation**: `ml_service` calculates a cost/reward based on the result, which is then used to update the ML model for the next iteration.
7.  **Reset**: Between trials, the `Engine` executes `reset_instructions` (also via `mios` tasks) to ensure the robot returns to a consistent starting state.

## Trial Tracking

The `ml_service` uses several mechanisms to track individual trials throughout the learning process:

1.  **Unique Identifiers (UUIDs)**:
    -   Each `Trial` is assigned a `trial_uuid` (UUIDv4) when created.
    -   When `mios` starts a task, it returns a `task_uuid`, which the `Engine` uses to correlate the robot's execution with the ML trial.

2.  **Internal State Management (`Engine` class)**:
    -   `queued_trials`: A queue that holds trials waiting for an available agent.
    -   `completed_trials`: A dictionary that stores finished `Trial` objects, indexed by their `trial_uuid`.
    -   `cnt_trial`: A monotonic counter used as the trial number (e.g., `n1`, `n2`).

## Taking a New Task

The `ml_service` accepts new learning tasks primarily through its **RPC Interface** or via script-based initialization.

### 1. RPC Submission (`Interface` class)
The standard way to start a new task is via the XML-RPC server (default port 8000). The most important method is **`start_service`**:

```python
interface.start_service(problem_definition, configuration, agents, knowledge)
```

1.  **Request Parsing**: The `Interface` receives the task details and checks for validity.
2.  **Service Selection**: Based on the `configuration`, it instantiates the correct ML algorithm (e.g., `CMAESService`).
3.  **Thread Execution**: It launches a dedicated `learn_task` thread so the main RPC server remains responsive.
4.  **UUID Assignment**: A unique `task_uuid` is returned to the client to track the session.

### 2. Defining a Task (`ProblemDefinition`)
A "Task" is technically defined by the **`ProblemDefinition`** object, which acts as a complete blueprint:
-   **Skill Class**: The underlying robot action (`Grasp`, `Insert`).
-   **Domain**: The search space (e.g., "search for force between 5N and 50N").
-   **Cost Function**: The weights used to calculate the trial's score.
-   **Instructions**: The sequences for setup, reset, and rescue.

### 3. Execution (The Engine)
Once the task is submitted, the **`Engine`** takes over. It maps the `ProblemDefinition` to real commands sent to the `mios` agents provided in the request.
3.  **Persistence and Monitoring**:
    -   **MongoDB**: Every completed trial is logged to a MongoDB collection (`ml_results`). Each trial is stored as a nested object (e.g., `n_12`) within the main session document, containing parameters, costs, and timing data.
    -   **Redis**: High-level summaries (success/failure, trial count, agent ID) are pushed to a Redis list (`ml_result`) for real-time monitoring.

4.  **Quality Metrics**:
    -   The `TaskResult` object tracks specific performance data (forces, durations, success/failure) for each trial, which is used to calculate the cost function for the optimizer.

## Safety and Robustness

-   **Rescue Instructions**: If a reset fails (e.g., robot gets stuck), the `Engine` can execute "rescue" movements to recover.
-   **Error Handling**: The system monitors for `RealTimeError`, `TaskError`, or `UserStopped` signals from `mios` and handles them by repeating trials or stopping the service.
