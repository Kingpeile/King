import re

# CJK Unified Ideographs + Extension A + Compatibility Ideographs
_CHINESE_PATTERN = re.compile(r'[一-鿿㐀-䶿豈-﫿]+')


def extract_chinese(text: str) -> str:
    """Extract all Chinese characters from the given text."""
    matches = _CHINESE_PATTERN.findall(text)
    return ''.join(matches)


if __name__ == '__main__':
    sample = "Hello, 你好世界! This is a test. 今天天气很好。Python is great, 学习编程很有趣。"
    result = extract_chinese(sample)
    print(f"原文:    {sample}")
    print(f"提取结果: {result}")
