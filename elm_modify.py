# directory independent 하도록!
# pip install pandas
# pip install pandas openpyxl

import pandas as pd
import re
import os

current_dir = os.getcwd()

input_file_path = os.path.join(current_dir, "myway1.log")
#output_file_path = os.path.join(current_dir, "elice.xlsx")

columns = ["command", "regno", "depvar", "varname", "coef", "se", "t", "p", "nobs", "rsq", "adj_rsq",
           "se_type"]
df = pd.DataFrame(columns=columns)

a = 1
b = 1
with open(input_file_path, "r") as f:
    data = f.read()

    pattern = r'(reg .*?_cons[^\n]*\n|Source.*?_cons[^\n]*\n)'
    sections = re.findall(pattern, data, re.DOTALL)
    regno = 0

    for section in sections:


        command = None
        lines = section.splitlines()
        for line in lines:
            match = re.search(r'\b(reg|regr|regre|regres|regress)\b', line)
            if match:
                command = match.group(0)
                break
        if match:
            variables = re.search(fr'{command}\s+(.+)', section)
            variables = variables.group(1).split()

            dependent_variable = variables[0]
            first_independent_variable = variables[1]

            #independent_variables_match = re.findall(rf'^\s+(\w+)\s+\|', section, re.MULTILINE)
            independent_variables_match = re.findall(r'^\s*(\w+[#\w.]*\w+)\s+\|', section, re.MULTILINE)
            if independent_variables_match:
                independent_variables = []
                capture = False
                for var in independent_variables_match:
                    if var == first_independent_variable:
                        capture = True
                    if capture:
                        independent_variables.append(var)
                    if var == '_cons':
                        break

            # depvar 정의하기
            depvar = dependent_variable
        if match == None:
            #first_words = re.findall(r'^\s*([a-zA-Z0-9_]+)\s*\|', section, re.MULTILINE)
            first_words = re.findall(r'^\s*(\w+[#\w.]*\w+)\s+\|', section, re.MULTILINE)
            variables = [word for word in first_words if word not in ("Source", "Model", "Residual", "Total")]
            dependent_variable = variables[0]

            depvar = dependent_variable
            independent_variables = variables[1:]

        # number of obs, r_squared, adj_r_squared 추출하기
        number_of_obs = re.search(r'Number of obs\s+=\s+([\d,]+)', section)
        r_squared = re.search(r'R-squared\s+=\s+([\d.]+)', section)
        # adj_r_squared = re.search(r'Adj R-squared\s+=\s+([\d.]+)', section)

        if re.search(r'Adj R-squared\s+=\s+([-.\d]+)', section):
            adj_r_squared = re.search(r'Adj R-squared\s+=\s+([-.\d]+)', section)
        else:
            adj_r_squared = None

        number_of_obs = number_of_obs.group(1)
        r_squared = r_squared.group(1)

        if adj_r_squared:
            adj_r_squared = adj_r_squared.group(1)

        nobs = number_of_obs
        rsq = r_squared
        adj_rsq = adj_r_squared

        # 항목들 순서 추출하기

        header = re.search(fr"{re.escape(dependent_variable)}\s+\|([\w\s.>|]+)", section)

        if header:
            headers = header.group(1)

            # Robust가 있는지 확인
            robust_check = re.search(r"Robust", section)
            if robust_check:
                headers = re.findall(r"std\.\s+err\.|[\w.>|]+", headers)
                headers = [item.replace('std. err.', 'Std. err.') for item in headers]
                se_type = 'Robust'
            # 'Std. err.'을 하나의 토큰으로 처리하기 위해 고급 정규 표현식 사용
            else:
                headers = re.findall(r"Std\.\s+err\.|[\w.>|]+", headers)
                se_type = ' '


        else:
            print("Header not found")

        # 독립 변수의 각각의 값들 추출하기
        # print(independent_variables)

        for independent_variable in independent_variables:
            # varname 정의하기
            varname = independent_variable

            value = re.search(fr"{independent_variable}\s+\|\s+([-.\d]+)\s+([-.\d]+)\s+([-.\d]+)\s+([-.\d]+)",
                                  section)

            if value:
                # 매치된 전체 결과를 리스트로 변환
                r_list = [value.group(i) for i in range(1, value.lastindex + 1)]
                # r_list.insert(0, independent_variable)
                # print(r_list)
            stats = dict(zip(headers, r_list))

            coef = float(stats['Coefficient'])
            # print(stats['Std.err.'])
            se = float(stats['Std. err.'])
            t = float(stats['t'])
            p = float(stats['P>|t|'])

            # column을 생성하고 추가하기
            new_row = {
                "command": command,
                "regno": regno,
                "depvar": depvar,
                "varname": varname,
                "coef": coef,
                "se": se,
                "t": t,
                "p": p,
                "nobs": nobs,
                "rsq": rsq,
                "adj_rsq": adj_rsq,
                "se_type": se_type
            }
            df = df.append(new_row, ignore_index=True)
            # print(stats)

        regno = regno + 1
        # dictionary로 구축하기


#df.to_excel(output_file_path, index=False)
print(df[0])
#print(df[1])
#print(df[2])
#print(df[3])