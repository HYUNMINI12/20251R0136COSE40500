import pandas as pd
import re
import os

def parse(input_string):
    columns = ["source", "command", "regno", "depvar", "varname", "coef", "se", "t", "p", "nobs", "rsq", "adj_rsq", "se_type"]

    dataframes = []

    with open(input_string, "r") as f:
        data = f.read()
        #sections = re.findall(r'(\*!!.*?)(?=\. \*!!|\Z)', data, re.DOTALL)
        sections = re.findall(r'(Example \d+\.\d+.*?)(?=Example \d+\.\d+|$)', data, re.DOTALL)

        for section in sections:

            # print(a)
            # print(section)
            # a = a + 1

            # Source, Part, Command, Regno의 정보

            example_pattern = re.compile(r'Example\s+\d+\.\d+')
            example_match = example_pattern.findall(section)
            source = example_match[0] if example_match else None
            regno = 0

            command = None
            lines = section.splitlines()
            for line in lines:
                match = re.search(r'\b(reg|regr|regre|regres|regress)\b', line)
                if match:
                    command = match.group(0)
                    break
            # print(command)

            # print(example_match)
            # regressions = re.findall(r'(\. reg .*?)(?=\. \*!!|\.\n|$)', section, re.DOTALL)

            regressions = re.findall(fr'\. {command}.*?(?=\n\. |\n$)', section, re.DOTALL)

            for regression in regressions:
                df = pd.DataFrame(columns=columns)
                """
                print(b)
                print(regression)
                b = b + 1
                """

                variables = re.search(fr'{command}\s+(.+)', regression)

                variables = variables.group(1).split()

                dependent_variable = variables[0]
                first_independent_variable = variables[1]

                independent_variables_match = re.findall(rf'^\s+(\w+)\s+\|', regression, re.MULTILINE)
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

                # number of obs, r_squared, adj_r_squared 추출하기
                number_of_obs = re.search(r'Number of obs\s+=\s+([\d,]+)', regression)
                r_squared = re.search(r'R-squared\s+=\s+([\d.]+)', regression)
                # adj_r_squared = re.search(r'Adj R-squared\s+=\s+([\d.]+)', regression)

                if re.search(r'Adj R-squared\s+=\s+([-.\d]+)', regression):
                    adj_r_squared = re.search(r'Adj R-squared\s+=\s+([-.\d]+)', regression)
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

                header = re.search(fr"{re.escape(dependent_variable)}\s+\|([\w\s.>|]+)", regression)

                if header:
                    headers = header.group(1)

                    # Robust가 있는지 확인
                    robust_check = re.search(r"Robust", regression)
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
                                      regression)

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
                        "source": source,
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


                dataframes.append(df)

                regno = regno + 1
                # dictionary로 구축하기

    return dataframes

# 예제 사용
current_dir = os.getcwd()
input_file_path = os.path.join(current_dir, "ch08.log")
df = parse(input_file_path)

print(df[2])
