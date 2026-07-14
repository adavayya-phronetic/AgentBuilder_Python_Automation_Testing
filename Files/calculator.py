"""
Simple Calculator
Performs addition, subtraction, multiplication, and division on two numbers.
"""

import tool


@tool
def add(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a: The first number
        b: The second number

    Returns:
        The sum of a and b
    """
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first.

    Args:
        a: The first number
        b: The second number

    Returns:
        The result of a minus b
    """
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together.

    Args:
        a: The first number
        b: The second number

    Returns:
        The product of a and b
    """
    return a * b


@tool
def divide(a: float, b: float) -> str:
    """Divide the first number by the second.

    Args:
        a: The numerator
        b: The denominator

    Returns:
        The division result, or an error message if b is zero
    """
    if b == 0:
        return "Error: Division by zero is not allowed"
    return a / b


def main():
    print("=== Simple Calculator ===")

    try:
        num1 = float(input("Enter the first number: "))
        num2 = float(input("Enter the second number: "))
    except ValueError:
        print("Invalid input. Please enter numeric values.")
        return

    print(f"\nAddition:       {num1} + {num2} = {add(num1, num2)}")
    print(f"Subtraction:    {num1} - {num2} = {subtract(num1, num2)}")
    print(f"Multiplication: {num1} * {num2} = {multiply(num1, num2)}")
    print(f"Division:       {num1} / {num2} = {divide(num1, num2)}")


if __name__ == "__main__":
    main()
