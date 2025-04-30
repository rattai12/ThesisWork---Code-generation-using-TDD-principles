from mbpp_experiment import MBPPExperiment, TestResult, ProblemResult
from typing import Dict, Any, Tuple, List
import time
from datetime import datetime
from dataclasses import asdict

class MBPPExperimentPhase3(MBPPExperiment):
    def generate_solution_phase3(self, problem: Dict[str, Any], failed_tests: List[Dict[str, Any]] = None, 
                               previous_code: str = None, attempt: int = 1) -> Tuple[str, Dict[str, int]]:
        """Generate solution using problem statement, test cases, and feedback from failures"""
        try:
            # Extract function name from first test case
            first_test = problem['test_cases'][0]
            function_name = first_test.split('(')[0].split()[-1]
            
            # Format test cases for the prompt
            test_cases_str = "\n".join([
                f"Test {i+1}: {test}" for i, test in enumerate(problem['test_cases'])
            ])
            
            # Create feedback message if there are failed tests
            feedback_str = ""
            if failed_tests and previous_code:
                feedback_str = "\nPrevious attempt failed these tests:\n"
                for i, test in enumerate(failed_tests, 1):
                    feedback_str += f"Test {i}:\n"
                    feedback_str += f"Input: {test['input']}\n"
                    feedback_str += f"Expected: {test['expected']}\n"
                    feedback_str += f"Got: {test['actual']}\n"
                    if test['error_message']:
                        feedback_str += f"Error: {test['error_message']}\n"
                feedback_str += "\nPrevious code:\n```python\n{previous_code}\n```\n"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Python code generator. Respond ONLY with working Python code.
                        Your solution must pass all the provided test cases.
                        Handle all edge cases. Validate inputs. No explanations, no comments, no markdown.
                        If shown previous failed attempts, carefully analyze the failures and fix the issues."""
                    },
                    {
                        "role": "user",
                        "content": f"""Write a Python function named '{function_name}' that solves this problem:

Problem Statement:
{problem['problem_statement']}

The function must pass these test cases:
{test_cases_str}
{feedback_str}

This is attempt {attempt}/3. Please ensure all test cases pass."""
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

    def run_phase3(self, start_id: int = 7, num_problems: int = 3):
        """Run Phase 3 of the experiment with iterative refinement"""
        problems = self.load_problems(start_id, num_problems)
        
        print(f"\nStarting Phase 3 - Testing {len(problems)} problems")
        print("=" * 50)

        for problem in problems:
            print(f"\nProblem {problem['problem_id']}")
            print("-" * 30)
            
            # Track attempts
            max_attempts = 3
            current_attempt = 1
            best_result = None
            best_code = None
            best_usage = None
            total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
            while current_attempt <= max_attempts:
                print(f"\nAttempt {current_attempt}/{max_attempts}")
                
                # Generate solution
                start_time = time.time()
                
                # Get failed tests from previous attempt
                failed_tests = None
                if best_result:
                    failed_tests = [
                        {
                            "input": test_case.split('assert ')[-1].split('==')[0].strip() if '==' in test_case else test_case,
                            "expected": r["expected_output"],
                            "actual": r["actual_output"],
                            "error_message": r["error_message"]
                        }
                        for r, test_case in zip(best_result.test_results, problem['test_cases'])
                        if not r["passed"]
                    ]
                
                # Generate new solution
                generated_code, usage = self.generate_solution_phase3(
                    problem,
                    failed_tests=failed_tests,
                    previous_code=best_code,
                    attempt=current_attempt
                )
                
                # Update total token usage
                for key in usage:
                    total_usage[key] += usage[key]
                
                if not generated_code:
                    print(f"Failed to generate code for problem {problem['problem_id']}")
                    break

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
                    phase=3,  # This is Phase 3
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

                # Update best result if this attempt is better
                if not best_result or result.passed_tests > best_result.passed_tests:
                    best_result = result
                    best_code = generated_code
                    best_usage = usage

                # Print progress
                print(f"Tests Passed: {passed_tests}/{len(test_results)}")
                print(f"Execution Time: {execution_time:.2f}s")
                print(f"Token Usage: {usage['total_tokens']}")

                # Break if all tests pass
                if passed_tests == len(test_results):
                    break
                
                current_attempt += 1
            
            # Save the best result
            if best_result:
                # Update with total token usage across all attempts
                best_result.token_usage = total_usage
                self.save_results(best_result)

def main():
    experiment = MBPPExperimentPhase3()
    experiment.run_phase3(start_id=1, num_problems=20)

if __name__ == "__main__":
    main() 