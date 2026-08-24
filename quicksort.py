def quicksort(arr):
    """
    快速排序算法实现

    Parameters:
    arr (list): 待排序的列表

    Returns:
    list: 排序后的列表
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quicksort(left) + middle + quicksort(right)


if __name__ == "__main__":
    test_arr = [3, 6, 8, 10, 1, 2, 1]
    print(f"原始数组: {test_arr}")
    sorted_arr = quicksort(test_arr)
    print(f"排序后数组: {sorted_arr}")
    assert sorted_arr == sorted(test_arr), "排序结果错误"
    print("快速排序测试通过!")