import pandas as pd
import re
import os

from happy.elm_main2 import parse_stata_string

def parse_stata_file(file_path):
    with open(file_path, "r", encoding='utf-8') as f:
      data = f.read()
    return parse_stata_string(data)




current_dir = os.getcwd()
input_file_path = os.path.join(current_dir, "ch06.log")
df = parse_stata_file(input_file_path)

print(df[0])