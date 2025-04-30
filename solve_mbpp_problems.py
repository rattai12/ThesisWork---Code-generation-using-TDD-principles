def problem1_check_number():
    """Check whether a number is positive, negative or zero"""
    def check_number(num):
        if num > 0:
            return "Positive"
        elif num < 0:
            return "Negative"
        else:
            return "Zero"
    
    # Run tests
    print("Problem 1 tests:")
    print(check_number(23) == "Positive")
    print(check_number(-23) == "Negative")
    print(check_number(0) == "Zero")

def problem2_max_of_three():
    """Find maximum of three numbers"""
    def max_of_three(a, b, c):
        return max(a, b, c)
    
    # Run tests
    print("\nProblem 2 tests:")
    print(max_of_three(1, 2, 3) == 3)
    print(max_of_three(5, 7, 2) == 7)
    print(max_of_three(9, 3, 6) == 9)

def problem3_sum_list():
    """Find the sum of elements in a list"""
    def sum_list(lst):
        return sum(lst)
    
    # Run tests
    print("\nProblem 3 tests:")
    print(sum_list([1, 2, 3]) == 6)
    print(sum_list([15, 12, 13, 10]) == 50)
    print(sum_list([0, 1, 2]) == 3)

def problem4_multiply_list():
    """Find the product of elements in a list"""
    def multiply_list(lst):
        result = 1
        for num in lst:
            result *= num
        return result
    
    # Run tests
    print("\nProblem 4 tests:")
    print(multiply_list([1, 2, 3]) == 6)
    print(multiply_list([3, 2, 4]) == 24)
    print(multiply_list([1, 2, 3, 4]) == 24)

def problem5_reverse_string():
    """Reverse a string"""
    def reverse_string(str1):
        return str1[::-1]
    
    # Run tests
    print("\nProblem 5 tests:")
    print(reverse_string("python") == "nohtyp")
    print(reverse_string("java") == "avaj")
    print(reverse_string("ruby") == "ybur")

if __name__ == "__main__":
    problem1_check_number()
    problem2_max_of_three()
    problem3_sum_list()
    problem4_multiply_list()
    problem5_reverse_string() 