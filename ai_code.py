import json
import os
from typing import Dict, List, Any, Tuple
from openai import OpenAI
import tempfile
import subprocess
import sys
import time

class AICodeTester:
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI()  # Will use OPENAI_API_KEY from environment

    def load_mbpp_problems(self, start_id: int = 1, num_problems: int = 20) -> List[Dict[str, Any]]:
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
                        'test_cases': [
                            {'input': test.split('assert ')[-1].split('==')[0].strip(),
                             'output': test.split('==')[1].strip()}
                            for test in problem['test_list']
                        ],
                        'test_setup_code': problem['test_setup_code'],
                        'reference_code': problem['code']
                    })
        return problems
            
    def generate_code_phase1(self, problem: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
        """Generate code using only the problem statement"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Python code generator. Respond ONLY with working Python code.
                        Handle all edge cases. Validate inputs. No explanations, no comments, no markdown."""
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Write ONLY the Python code solution for this problem:

                        Problem Statement:
                        {problem['problem_statement']}

                        Test Cases:
                        {problem['test_cases'][:2]}

                        Requirements:
                        1. Code must be a function that matches the test cases
                        2. Handle all edge cases (empty input, invalid input, etc.)
                        3. Include input validation
                        4. No comments or explanations
                        5. Start directly with the code
                        """
                    }
                ]
            )
            
            # Clean the response
            code = response.choices[0].message.content.strip()
            if code.startswith("```python"):
                code = code[code.find("\n")+1:code.rfind("```")]
            elif code.startswith("```"):
                code = code[code.find("\n")+1:code.rfind("```")]
            
            # Get token usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return code, usage

        except Exception as e:
            print(f"Error generating code: {e}")
            return None, {}
        
    def run_test_case(self, code: str, test_case: Dict[str, str], setup_code: str = "") -> Tuple[bool, str, str]:
        """Run a single test case and return (passed, actual_output, error_message)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write setup code if any
            if setup_code:
                f.write(setup_code + "\n")
            
            # Write the solution code
            f.write(code + "\n")
            
            # Write test code
            f.write(f"\nresult = {test_case['input']}\n")
            f.write(f"print(result)")
            temp_file = f.name
        
        try:
            # Run the code
            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            actual_output, error_output = process.communicate()
            
            # Clean up outputs
            actual_output = actual_output.strip()
            expected_output = test_case['output'].strip()
            
            # Compare outputs
            try:
                # Try to evaluate both as Python expressions
                actual_val = eval(actual_output)
                expected_val = eval(expected_output)
                passed = actual_val == expected_val
            except:
                # Fall back to string comparison if eval fails
                passed = actual_output == expected_output
                
            return passed, actual_output, error_output
            
        except Exception as e:
            return False, "", str(e)
        finally:
            os.unlink(temp_file)
    
    def run_tests(self, code: str, test_cases: List[Dict[str, str]], setup_code: str = "") -> Dict[str, Any]:
        """Run all test cases and return results"""
        results = {
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "failed_tests": [],
        }
        
        for i, test_case in enumerate(test_cases, 1):
            passed, actual_output, error = self.run_test_case(
                code, 
                test_case,
                setup_code
            )
            
            if passed:
                results["passed_tests"] += 1
            else:
                results["failed_tests"].append({
                    "test_number": i,
                    "input": test_case["input"],
                    "expected": test_case["output"],
                    "actual": actual_output,
                    "error": error
                })
                
        return results

def save_solution(problem_id: int, code: str, results: Dict[str, Any], usage: Dict[str, int]):
    """Save the solution and its results to a file"""
    output_dir = "solutions"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"{output_dir}/solution_{problem_id:03d}.py"
    results_file = f"{output_dir}/solution_{problem_id:03d}_results.json"
    
    # Save the code
    with open(filename, 'w') as f:
        f.write(f"# Problem {problem_id:03d}\n")
        f.write(f"# Tests Passed: {results['passed_tests']}/{results['total_tests']}\n")
        f.write(f"# Token Usage: {usage['total_tokens']}\n\n")
        f.write(code)
    
    # Save the results
    results_data = {
        "problem_id": problem_id,
        "tests_passed": results['passed_tests'],
        "total_tests": results['total_tests'],
        "token_usage": usage,
        "failed_tests": results['failed_tests']
    }
    
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

def test_mbpp_problems(start_id: int = 1, num_problems: int = 20):
    """Test the first num_problems from MBPP dataset"""
    # Initialize without explicit API key - it will use environment variable
    tester = AICodeTester()
    
    # Load problems
    problems = tester.load_mbpp_problems(start_id, num_problems)
    
    # Summary statistics
    total_stats = {
        "total_problems": len(problems),
        "solved_problems": 0,
        "total_tests": 0,
        "passed_tests": 0,
        "total_tokens": 0
    }
    
    # Test each problem
    for problem in problems:
        print(f"\n{'='*50}")
        print(f"Testing Problem {problem['problem_id']}")
        print(f"{'='*50}")
        
        try:
            print("\nProblem Statement:")
            print(problem['problem_statement'])
            
            generated_code, usage = tester.generate_code_phase1(problem)
            
            if generated_code:  
                print("\nGenerated Solution:")
                print("-" * 40)
                print(generated_code)
                print("-" * 40)
                
                # Run tests
                results = tester.run_tests(generated_code, problem["test_cases"], problem["test_setup_code"])
                
                # Save the solution
                save_solution(problem['problem_id'], generated_code, results, usage)
                print(f"\nSolution saved to solutions/solution_{problem['problem_id']:03d}.py")
                print(f"Results saved to solutions/solution_{problem['problem_id']:03d}_results.json")
                
                # Update token usage
                total_stats["total_tokens"] += usage["total_tokens"]
                
                # Update statistics
                total_stats["total_tests"] += results["total_tests"]
                total_stats["passed_tests"] += results["passed_tests"]
                if results["passed_tests"] == results["total_tests"]:
                    total_stats["solved_problems"] += 1
                    
                # Print results
                print(f"\nResults for Problem {problem['problem_id']}:")
                print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
                print(f"Token Usage: {usage['total_tokens']}")
                
                if results['failed_tests']:
                    print("\nFailed Tests:")
                    for test in results['failed_tests']:
                        print(f"\nTest {test['test_number']}:")
                        print(f"Input: {test['input']}")
                        print(f"Expected: {test['expected']}")
                        print(f"Actual: {test['actual']}")
                        if test['error']:
                            print(f"Error: {test['error']}")
        except Exception as e:
            print(f"Error processing problem {problem['problem_id']}: {e}")
    
    # Print final summary
    print(f"\n{'='*50}")
    print("Final Summary:")
    print(f"{'='*50}")
    print(f"Problems Solved: {total_stats['solved_problems']}/{total_stats['total_problems']}")
    print(f"Total Tests Passed: {total_stats['passed_tests']}/{total_stats['total_tests']}")
    print(f"Total Tokens Used: {total_stats['total_tokens']}")

if __name__ == "__main__":
    test_mbpp_problems(51, 10)  # Test first 20 problems 