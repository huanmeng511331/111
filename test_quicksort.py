"""
quicksort.py 的单元测试

覆盖场景：
- 正常排序、已排序、逆序、空数组、单元素、重复元素、负数混合
"""

from quicksort import quicksort


def test_normal_unsorted():
    """正常乱序数组排序"""
    arr = [3, 6, 8, 10, 1, 2, 1]
    assert quicksort(arr) == sorted(arr)


def test_already_sorted():
    """已排序数组"""
    arr = [1, 2, 3, 4, 5]
    assert quicksort(arr) == [1, 2, 3, 4, 5]


def test_reverse_sorted():
    """完全逆序数组"""
    arr = [5, 4, 3, 2, 1]
    assert quicksort(arr) == [1, 2, 3, 4, 5]


def test_empty():
    """空数组"""
    assert quicksort([]) == []


def test_single_element():
    """单元素数组"""
    assert quicksort([42]) == [42]


def test_duplicates():
    """含重复元素的数组"""
    arr = [4, 2, 4, 1, 3, 2]
    assert quicksort(arr) == sorted(arr)


def test_mixed_negative_positive():
    """负数与正数混合"""
    arr = [-3, 5, 0, -1, 2, -8]
    assert quicksort(arr) == sorted(arr)


def test_returns_list():
    """验证返回类型为 list"""
    result = quicksort([3, 1, 2])
    assert isinstance(result, list)