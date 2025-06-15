#pip install openpyxl


import pandas as pd
import json
import os

def jsonize(input_file, output_file, force=False):


    # output_file이 존재하고, 강제 실행이 아닌 경우
    if not force and os.path.exists(output_file):
        # 각각의 수정 시간을 불러와서 비교하는 과정임
        input_mtime = os.path.getmtime(input_file)
        output_mtime = os.path.getmtime(output_file)
        if output_mtime>input_mtime:
            print("It's newest version.")
            return
    # excel을 읽어와서 pandas dataframe으로 저장함
    df = pd.read_excel(input_file, engine='openpyxl')

    # 저장할 dictionary를 선언함
    json_dict = {}


    for index, row in df.iterrows():
        # varname열, meaning열, unit열, source열에 해당하는 값을 가져와서 source 변수에 저장함
        varname = row['varname']
        meaning = row['meaning']
        unit = row['unit']
        source = row['source']

        if varname not in json_dict:
            json_dict[varname] = []


        # 중복되는 meaning, unit이 있을 경우, 이를 제거함
        existing_entry = None

        for entry in json_dict[varname]:
            if entry['meaning'] == meaning and entry['unit'] == unit:
                existing_entry = entry
                break

        # source는 없을 경우 source는 넣어줌
        if existing_entry:
            if source not in existing_entry['source']:
                existing_entry['source'] += f"; {source}"

        # 중복되지 않을 경우 추가해줌
        else:
            json_dict[varname].append({
                'meaning' : meaning,
                'unit' : unit,
                'source' : source
            })

    # JSON 형태의 파일로 저장함.
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

current_dir = os.getcwd()
input_file = os.path.join(current_dir, "variables.xlsx")
output_file = os.path.join(current_dir, "variables.json")

jsonize(input_file, output_file, force=False)