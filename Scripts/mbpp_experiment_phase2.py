from mbpp_experiment import MBPPExperiment, TestResult, ProblemResult
from typing import Dict, Any, Tuple
import time
from datetime import datetime
from dataclasses import asdict

class MBPPExperimentPhase2(MBPPExperiment):
    def generate_solution_phase2(self, problem: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
        """Generate solution using problem statement AND test cases (Phase 2)"""
        try:
            # Extract function name from first test case
            first_test = problem['test_cases'][0]
            function_name = first_test.split('(')[0].split()[-1]
            
            # Format test cases for the prompt
            test_cases_str = "\n".join([
                f"Test {i+1}: {test}" for i, test in enumerate(problem['test_cases'][:2])
            ])
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Python code generator. Respond ONLY with working Python code.
                        Your solution must pass all the provided test cases.
                        Handle all edge cases. Validate inputs. No explanations, no comments, no markdown."""
                    },
                    {
                        "role": "user",
                        "content": f"""Write a Python function named '{function_name}' that solves this problem:

Problem Statement:
{problem['problem_statement']}

The function must pass these test cases:
{test_cases_str}"""
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

    def run_phase2(self, start_id: int = 1, num_problems: int = 20):
        """Run Phase 2 of the experiment"""
        problems = self.load_problems(start_id, num_problems)
        
        print(f"\nStarting Phase 2 - Testing {len(problems)} problems")
        print("=" * 50)

        for problem in problems:
            print(f"\nProblem {problem['problem_id']}")
            print("-" * 30)
            
            # Generate solution
            start_time = time.time()
            generated_code, usage = self.generate_solution_phase2(problem)
            
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
                phase=2,  # This is Phase 2
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
    experiment = MBPPExperimentPhase2()
    experiment.run_phase2(start_id=1, num_problems=100)

if __name__ == "__main__":
    main() 