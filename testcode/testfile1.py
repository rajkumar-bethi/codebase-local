def swap_numbers_arithmetic(a, b):
    a = a + b
    b = a - b
    a = a - b
    return a, b

# Example usage:
x = 5
y = 10
x, y = swap_numbers_arithmetic(x, y)
print("After swapping: x =", x, ", y =", y)