import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import traceback
from openai import OpenAI

@dataclass
class TestResult:
    passed: bool
    actual_output: str
    expected_output: str
    error_message: str = ""
    execution_time: float = 0.0

@dataclass
class ProblemResult:
    problem_id: int
    phase: int
    timestamp: str
    model: str
    problem_statement: str
    generated_code: str
    test_results: List[Dict[str, Any]]
    total_tests: int
    passed_tests: int
    execution_time: float
    token_usage: Dict[str, int]
    error_analysis: Dict[str, Any]

class MBPPExperiment:
    def __init__(self, output_dir: str = "results", model: str = "gpt-4o"):
        """Initialize experiment runner"""
        self.client = OpenAI()
        self.base_dir = output_dir
        self.model = model
        self.setup_directories()

    def setup_directories(self):
        """Create directory structure for results"""
        for phase in [1, 2, 3]:
            phase_dir = os.path.join(self.base_dir, f"phase{phase}")
            os.makedirs(os.path.join(phase_dir, "solutions"), exist_ok=True)
            os.makedirs(os.path.join(phase_dir, "statistics"), exist_ok=True)

    def load_problems(self, start_id: int, num_problems: int) -> List[Dict[str, Any]]:
        """Load problems from MBPP dataset"""
        problems = []
        with open('Problems/mbpp.jsonl', 'r') as f:
            for i, line in enumerate(f):
                if i >= start_id + num_problems:
                    break
                if i >= start_id:
                    problem = json.loads(line)
                    problems.append({
                        'problem_id': problem['task_id'],
                        'problem_statement': problem['text'],
                        'test_cases': problem['test_list'],
                        'test_setup_code': problem['test_setup_code'],
                        'reference_code': problem['code']
                    })
        return problems

    def generate_solution_phase1(self, problem: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
        """Generate solution using only problem statement (Phase 1)"""
        try:
            # Extract function name from first test case
            first_test = problem['test_cases'][0]
            function_name = first_test.split('(')[0].split()[-1]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Python code generator. Respond ONLY with working Python code.
                        Handle all edge cases. Validate inputs. No explanations, no comments, no markdown."""
                    },
                    {
                        "role": "user",
                        "content": f"""Write a Python function named '{function_name}' that solves this problem:
                        {problem['problem_statement']}"""
                    }
                ]
            )
            
            code = response.choices[0].message.content.strip()
            if code.startswith("```python"):
                code = code[code.find("\n")+1:code.rfind("```")]
            elif code.startswith("```"):
                code = code[code.find("\n")+1:code.rfind("```")]
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return code, usage
        except Exception as e:
            print(f"Error generating code: {e}")
            return None, {}

    def run_test_case(self, code: str, test_case: str, setup_code: str = "") -> TestResult:
        """Run a single test case and return detailed results"""
        # Clean up the test case - remove 'assert' if present
        if test_case.startswith('assert '):
            test_case = test_case[7:]

        # Split test case into function call and expected output
        test_parts = test_case.split('==')
        function_call = test_parts[0].strip()
        expected_output = test_parts[1].strip().strip("'").strip('"').strip()

        # Create namespace for execution
        namespace = {}
        
        try:
            start_time = time.time()
            
            # Execute setup code if any
            if setup_code:
                exec(setup_code, namespace)
            
            # Execute the function definition
            exec(code, namespace)
            
            # Execute the test case
            exec(f"result = {function_call}", namespace)
            actual_output = repr(namespace['result'])
            
            execution_time = time.time() - start_time
            
            # Compare outputs
            try:
                # Try to evaluate both as Python expressions
                actual_val = eval(actual_output)
                expected_val = eval(expected_output)
                passed = actual_val == expected_val
            except:
                # Fall back to string comparison if eval fails
                passed = actual_output.strip("'\"") == expected_output.strip("'\"")
            
            return TestResult(
                passed=passed,
                actual_output=actual_output.strip("'\""),
                expected_output=expected_output,
                error_message="",
                execution_time=execution_time
            )
            
        except Exception as e:
            return TestResult(
                passed=False,
                actual_output="ERROR",
                expected_output=expected_output,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def save_results(self, result: ProblemResult):
        """Save problem results to appropriate files"""
        phase_dir = os.path.join(self.base_dir, f"phase{result.phase}")
        
        # Save solution
        solution_file = os.path.join(phase_dir, "solutions", f"problem_{result.problem_id:03d}.py")
        with open(solution_file, 'w') as f:
            f.write(f"# Problem {result.problem_id:03d}\n")
            f.write(f"# Generated on: {result.timestamp}\n")
            f.write(f"# Model: {result.model}\n")
            f.write(f"# Tests Passed: {result.passed_tests}/{result.total_tests}\n\n")
            f.write(result.generated_code)

        # Save statistics
        stats_file = os.path.join(phase_dir, "statistics", f"problem_{result.problem_id:03d}_stats.json")
        with open(stats_file, 'w') as f:
            json.dump(asdict(result), f, indent=2)

        # Update summary
        self.update_summary(result)

    def update_summary(self, result: ProblemResult):
        """Update the phase summary with new result"""
        # Include model name in summary file
        model_name = self.model.replace('.', '_').replace('-', '_')
        summary_file = os.path.join(self.base_dir, f"phase{result.phase}", f"summary_{model_name}.json")
        
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
        except FileNotFoundError:
            summary = {
                "phase": result.phase,
                "model": self.model,
                "total_problems": 0,
                "total_tests": 0,
                "passed_tests": 0,
                "perfect_solutions": 0,
                "total_execution_time": 0.0,
                "total_token_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "error_types": {}
            }

        # Update statistics
        summary["total_problems"] += 1
        summary["total_tests"] += result.total_tests
        summary["passed_tests"] += result.passed_tests
        if result.passed_tests == result.total_tests:
            summary["perfect_solutions"] += 1
        summary["total_execution_time"] += result.execution_time
        
        for key in result.token_usage:
            summary["total_token_usage"][key] += result.token_usage[key]

        # Update error types
        for error_type, count in result.error_analysis.get("error_types", {}).items():
            if error_type in summary["error_types"]:
                summary["error_types"][error_type] += count
            else:
                summary["error_types"][error_type] = count

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

    def analyze_errors(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Analyze errors from test results"""
        error_types = {}
        error_messages = []

        for result in test_results:
            if not result.passed:
                if "TimeoutError" in result.error_message:
                    error_type = "timeout"
                elif "AssertionError" in result.error_message:
                    error_type = "logic_error"
                elif "SyntaxError" in result.error_message:
                    error_type = "syntax_error"
                elif "NameError" in result.error_message or "ImportError" in result.error_message:
                    error_type = "dependency_error"
                else:
                    error_type = "other"

                error_types[error_type] = error_types.get(error_type, 0) + 1
                error_messages.append(result.error_message)

        return {
            "error_types": error_types,
            "error_messages": error_messages
        }

    def run_phase1(self, start_id: int = 1, num_problems: int = 20):
        """Run Phase 1 of the experiment"""
        problems = self.load_problems(start_id, num_problems)
        
        print(f"\nStarting Phase 1 - Testing {len(problems)} problems")
        print("=" * 50)

        for problem in problems:
            print(f"\nProblem {problem['problem_id']}")
            print("-" * 30)
            
            # Generate solution
            start_time = time.time()
            generated_code, usage = self.generate_solution_phase1(problem)
            
            if not generated_code:
                print(f"Failed to generate code for problem {problem['problem_id']}")
                continue

            # Run tests
            test_results = []
            for test_case in problem['test_cases']:
                result = self.run_test_case(
                    generated_code,
                    test_case,
                    problem['test_setup_code']
                )
                test_results.append(asdict(result))

            execution_time = time.time() - start_time
            
            # Analyze results
            passed_tests = sum(1 for r in test_results if r['passed'])
            error_analysis = self.analyze_errors([TestResult(**r) for r in test_results])

            # Create result object
            result = ProblemResult(
                problem_id=problem['problem_id'],
                phase=1,
                timestamp=datetime.now().isoformat(),
                model=self.model,
                problem_statement=problem['problem_statement'],
                generated_code=generated_code,
                test_results=test_results,
                total_tests=len(test_results),
                passed_tests=passed_tests,
                execution_time=execution_time,
                token_usage=usage,
                error_analysis=error_analysis
            )

            # Save results
            self.save_results(result)

            # Print progress
            print(f"Tests Passed: {passed_tests}/{len(test_results)}")
            print(f"Execution Time: {execution_time:.2f}s")
            print(f"Token Usage: {usage['total_tokens']}")

def main():
    experiment = MBPPExperiment()
    experiment.run_phase1(start_id=1, num_problems=100)

if __name__ == "__main__":
    main() 