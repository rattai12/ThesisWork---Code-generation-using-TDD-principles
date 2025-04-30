# MBPP Experiment Runner

This project runs experiments using language models (like GPT-4) on the MBPP (Mostly Basic Programming Problems) dataset. The experiment is structured in three phases, each testing different aspects of the model's problem-solving capabilities.

## Directory Structure

```
MBPP Experiment/
├── Scripts/
│   ├── mbpp_experiment.py         # Phase 1 implementation
│   ├── mbpp_experiment_phase2.py  # Phase 2 implementation
│   ├── mbpp_experiment_phase3.py  # Phase 3 implementation
│   └── ai_code.py                 # Helper functions
├── Runs/                          # Experiment results
│   └── run_YYYYMMDD_HHMMSS/      # Timestamped run directories
├── Problems/                      # MBPP dataset
└── run_experiment.py             # Main experiment runner
```

## Getting Started

1. Ensure you have Python 3.7+ installed
2. Place the MBPP dataset in the `Problems/` directory
3. Install required dependencies (if any)

## OpenAI API Key Setup

The experiment requires an OpenAI API key to interact with GPT models. To set up your API key:

1. Get your API key from OpenAI: https://platform.openai.com/api-keys
2. Set the environment variable using PowerShell (Windows):
```powershell
SETX OPENAI_API_KEY "your-api-key-here"
```
3. **Important**: After setting the API key, you need to:
   - Close and reopen your terminal/PowerShell
   - Or restart your IDE
   - Or restart your computer

Note: Keep your API key secure and never commit it to version control.

## Running Experiments

### Basic Usage

Run all phases with default settings:
```bash
python run_experiment.py
```

### Advanced Usage

1. Run specific phases:
```bash
python run_experiment.py --phases 1 2  # Run only phases 1 and 2
```

2. Customize problem range:
```bash
python run_experiment.py --problems 50 --start 200  # Run 50 problems starting from ID 200
```

3. Choose a different model:
```bash
python run_experiment.py --model gpt-4o  # Use GPT-4
python run_experiment.py --model gpt-3.5-turbo  # Use GPT-3.5
```

### Parameters

- `--phases`: List of phases to run (default: [1, 2, 3])
- `--problems`: Number of problems to test (default: 150)
- `--start`: Starting problem ID (default: 200)
- `--model`: Model to use (default: "gpt-4o")
- `--resume`: Resume the most recent interrupted run

## Experiment Phases

### Phase 1
- Basic problem-solving capability
- Generates solutions based on problem statements
- Tests solutions against provided test cases

### Phase 2
- Enhanced problem-solving with test case analysis
- Uses test cases to guide solution generation
- Validates solutions against all test cases

### Phase 3
- Iterative refinement based on test failures
- Attempts to improve solutions that failed in previous phases
- Multiple attempts per problem if needed

## Results Structure

Each run creates a timestamped directory containing:
```
run_YYYYMMDD_HHMMSS/
├── phase1/
│   ├── solutions/      # Generated solutions
│   ├── statistics/     # Performance metrics
│   └── summary.json    # Phase 1 results
├── phase2/
│   ├── solutions/
│   ├── statistics/
│   └── summary.json
├── phase3/
│   ├── solutions/
│   ├── statistics/
│   └── summary.json
├── progress.json       # Run progress tracking
└── run_summary.json    # Combined results
```

## Progress Tracking

- Progress is automatically saved after each problem
- Interrupted runs can be resumed using `--resume`
- Progress tracking includes:
  - Completed problems
  - Last problem processed
  - Phase information
  - Model used

## Error Handling

- Graceful handling of interruptions (Ctrl+C)
- Progress saved on interruption or error
- Detailed error messages in case of failures
- Resume capability for interrupted runs

## Best Practices

1. Start with a small test run:
```bash
python run_experiment.py --problems 5 --phases 1
```

2. Monitor progress in the run directory
3. Use `--resume` if an experiment is interrupted
4. Check run_summary.json for overall results 