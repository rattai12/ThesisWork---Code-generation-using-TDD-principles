import os
import sys
import json
import argparse
import shutil
from datetime import datetime

# Add Scripts directory to Python path
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Scripts")
sys.path.append(SCRIPTS_DIR)

from mbpp_experiment import MBPPExperiment
from mbpp_experiment_phase2 import MBPPExperimentPhase2
from mbpp_experiment_phase3 import MBPPExperimentPhase3

# Constants for directory paths
RUNS_DIR = "Runs"
PROBLEMS_DIR = "Problems"

def create_timestamped_dir(base_dir: str, phases: list) -> str:
    """Create a timestamped directory for this run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RUNS_DIR, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    
    # Create phase directories
    for phase in phases:
        phase_dir = os.path.join(run_dir, f"phase{phase}")
        os.makedirs(os.path.join(phase_dir, "solutions"), exist_ok=True)
        os.makedirs(os.path.join(phase_dir, "statistics"), exist_ok=True)
    
    # Create progress tracking file
    with open(os.path.join(run_dir, "progress.json"), "w") as f:
        json.dump({
            "start_id": None,
            "num_problems": None,
            "phases": phases,
            "completed_problems": [],
            "last_problem_id": None,
            "timestamp": timestamp
        }, f, indent=2)
    
    return run_dir

def find_latest_run():
    """Find the most recent experiment run that might need to be resumed"""
    if not os.path.exists(RUNS_DIR):
        return None
    
    runs = [d for d in os.listdir(RUNS_DIR) if d.startswith("run_")]
    if not runs:
        return None
    
    latest_run = max(runs)
    run_dir = os.path.join(RUNS_DIR, latest_run)
    
    if os.path.exists(os.path.join(run_dir, "progress.json")):
        with open(os.path.join(run_dir, "progress.json")) as f:
            progress = json.load(f)
            if progress["last_problem_id"] is not None and progress["last_problem_id"] < progress["start_id"] + progress["num_problems"] - 1:
                return run_dir
    return None 

def run_experiment(num_problems: int = 150, start_id: int = 200, phases: list = None, resume: bool = False, model: str = "gpt-4o"):
    """Run specified phases of the experiment"""
    if phases is None:
        phases = [1, 2, 3]
    
    # Ensure required directories exist
    os.makedirs(RUNS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    
    # Check for resumable run
    run_dir = None
    if resume:
        run_dir = find_latest_run()
        if run_dir:
            with open(os.path.join(run_dir, "progress.json")) as f:
                progress = json.load(f)
                # Override input parameters with saved progress
                start_id = progress["start_id"]
                num_problems = progress["num_problems"]
                phases = progress["phases"]
                completed = set(progress["completed_problems"])
                last_problem = progress["last_problem_id"]
                print(f"\nResuming previous run from: {run_dir}")
                print(f"Completed problems: {len(completed)}/{num_problems}")
                print(f"Last problem processed: {last_problem}")
                print(f"Continuing from problem: {last_problem + 1}")
    
    # Create new run directory if not resuming
    if not run_dir:
        run_dir = create_timestamped_dir(RUNS_DIR, phases)
        completed = set()
        last_problem = start_id - 1
        print(f"\nStarting new experiment run in: {run_dir}")
    
    print(f"Running phases: {phases}")
    print(f"Starting problem ID: {start_id}")
    print(f"Number of problems: {num_problems}")
    print(f"Using model: {model}")
    
    try:
        # Run selected phases
        if 1 in phases:
            print("\nStarting Phase 1...")
            phase1 = MBPPExperiment(output_dir=run_dir, model=model)
            for problem_id in range(last_problem + 1, start_id + num_problems):
                if problem_id not in completed:
                    print(f"\nProblem {problem_id} ({len(completed)}/{num_problems} completed)")
                    phase1.run_phase1(start_id=problem_id, num_problems=1)
                    update_progress(run_dir, start_id, num_problems, problem_id)
        
        if 2 in phases:
            print("\nStarting Phase 2...")
            phase2 = MBPPExperimentPhase2(output_dir=run_dir, model=model)
            for problem_id in range(last_problem + 1, start_id + num_problems):
                if problem_id not in completed:
                    print(f"\nProblem {problem_id} ({len(completed)}/{num_problems} completed)")
                    phase2.run_phase2(start_id=problem_id, num_problems=1)
                    update_progress(run_dir, start_id, num_problems, problem_id)
        
        if 3 in phases:
            print("\nStarting Phase 3...")
            phase3 = MBPPExperimentPhase3(output_dir=run_dir, model=model)
            for problem_id in range(last_problem + 1, start_id + num_problems):
                if problem_id not in completed:
                    print(f"\nProblem {problem_id} ({len(completed)}/{num_problems} completed)")
                    phase3.run_phase3(start_id=problem_id, num_problems=1)
                    update_progress(run_dir, start_id, num_problems, problem_id)
        
        # Create a run summary
        create_run_summary(run_dir, phases)
        print(f"\nExperiment completed. Results saved in: {run_dir}")
        
    except KeyboardInterrupt:
        print("\nExperiment interrupted by user. Progress has been saved.")
        print(f"To resume, run: python run_experiment.py --resume")
        return
    except Exception as e:
        print(f"\nError during experiment: {e}")
        print(f"Progress has been saved. To resume, run: python run_experiment.py --resume")
        raise

def update_progress(run_dir: str, start_id: int, num_problems: int, current_problem: int):
    """Update progress tracking file"""
    progress_file = os.path.join(run_dir, "progress.json")
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            progress = json.load(f)
    else:
        progress = {
            "start_id": None,
            "num_problems": None,
            "phases": [],
            "completed_problems": [],
            "last_problem_id": None,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    progress["start_id"] = start_id
    progress["num_problems"] = num_problems
    progress["last_problem_id"] = current_problem
    if current_problem not in progress["completed_problems"]:
        progress["completed_problems"].append(current_problem)
    
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)

def create_run_summary(run_dir: str, phases: list):
    """Create a summary comparing phases"""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "phases": {}
    }
    
    # Load summaries from each phase
    for phase in phases:
        phase_dir = os.path.join(run_dir, f"phase{phase}")
        for file in os.listdir(phase_dir):
            if file.startswith("summary_") and file.endswith(".json"):
                with open(os.path.join(phase_dir, file), 'r') as f:
                    phase_data = json.load(f)
                    summary["phases"][f"phase{phase}"] = phase_data
    
    # Save combined summary
    with open(os.path.join(run_dir, "run_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

def parse_args():
    parser = argparse.ArgumentParser(description='Run MBPP Experiment Phases')
    parser.add_argument('--phases', type=int, nargs='+', default=[1, 2, 3],
                      help='Phases to run (e.g., --phases 1 2 for phases 1 and 2)')
    parser.add_argument('--problems', type=int, default=150,
                      help='Number of problems to test')
    parser.add_argument('--start', type=int, default=200,
                      help='Starting problem ID')
    parser.add_argument('--resume', action='store_true',
                      help='Resume the most recent interrupted run')
    parser.add_argument('--model', type=str, default="gpt-4o",
                      help='Model to use (e.g., gpt-4o, gpt-3.5-turbo)')
    return parser.parse_args()

def main():
    # Ensure all required directories exist
    os.makedirs(RUNS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    os.makedirs(PROBLEMS_DIR, exist_ok=True)
    
    args = parse_args()
    
    try:
        run_experiment(
            num_problems=args.problems,
            start_id=args.start,
            phases=args.phases,
            resume=args.resume,
            model=args.model
        )
    except KeyboardInterrupt:
        print("\nExperiment interrupted by user. Progress has been saved.")
    except Exception as e:
        print(f"\nError during experiment: {e}")
        raise

if __name__ == "__main__":
    main() 