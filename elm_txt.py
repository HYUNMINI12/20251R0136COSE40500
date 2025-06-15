import pandas as pd
import re
import os


def parse_txt(input_string):
    # 컬럼 정의
    columns = ["source", "command", "regno", "depvar", "varname", "coef", "se", "t", "p", "nobs", "rsq", "adj_rsq",
               "se_type"]
    dataframes = []

    regno = 0

    with open(input_string, "r", encoding='utf-8') as f:
        data = f.read()

        # 각 섹션 추출
        sections = re.findall(r'(Example \d+\.\d+.*?)(?=Example \d+\.\d+|$)', data, re.DOTALL)
        #sections = re.findall(r'(?<=\#\!\!)(.*?)(?=\#\!\!|$)', data, re.DOTALL)

        for section in sections:
            # Source 정보 추출
            example_pattern = re.compile(r'Example\s+\d+\.\d+')
            example_match = example_pattern.findall(section)
            source = example_match[0] if example_match else None

            # command, regressions 추출
            command = None

            lines = section.splitlines()
            for line in lines:
                match = re.search(r'\b(reg|regr|regre|regres|regress|lm)\b', line)
                if match:
                    command = match.group(0)
                    break

            regressions = re.findall(rf'({re.escape(command)}.*?)(?={re.escape(command)}|$)', section, re.DOTALL)

            for regression in regressions:
                df = pd.DataFrame(columns=columns)

                # formula에서 종속 변수와 독립 변수 추출
                formula = re.search(r'lm\(formula\s*=\s*(.*?),\s*data', regression)
                if formula:
                    formula = formula.group(1)
                    variables = re.findall(r'\b\w+\b', formula)

                dependent_variable = variables[0]
                independent_variables = variables[1:]
                independent_variables.insert(0, '(Intercept)')

                depvar = dependent_variable

                # Number of obs, R-squared, Adj R-squared 추출
                number_of_obs = re.search(r'on (\d+) degrees of freedom', regression)
                number_of_obs = int(number_of_obs.group(1)) if number_of_obs else None

                r_squared = re.search(r'Multiple R-squared:\s+([\d.]+)', regression)
                r_squared = float(r_squared.group(1)) if r_squared else None

                adj_r_squared = re.search(r'Adjusted R-squared:\s+([\d.]+)', regression)
                adj_r_squared = float(adj_r_squared.group(1)) if adj_r_squared else None

                nobs = number_of_obs
                rsq = r_squared
                adj_rsq = adj_r_squared

                # Headers 추출
                matches = re.findall(r'(Estimate|Std\. Error|t value|Pr\(>\|t\|\))', regression)

                # 독립 변수의 각각의 값들 추출
                for independent_variable in independent_variables:
                    varname = independent_variable
                    value = re.search(
                        rf'{re.escape(independent_variable)}\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+<?\s*([\d.e+-]+)',
                        regression)

                    if value:
                        r_list = [value.group(i) for i in range(1, value.lastindex + 1)]

                    stats = dict(zip(matches, r_list))

                    coef = float(stats['Estimate'])
                    se = float(stats['Std. Error'])
                    t = float(stats['t value'])
                    string = stats['Pr(>|t|)']

                    if 'e' in string:
                        string = string.replace('e^-0', 'e-')
                        stats['Pr(>|t|)'] = float(string)
                    else:
                        stats['Pr(>|t|)'] = float(string)

                    p = stats['Pr(>|t|)']

                    # DataFrame에 새로운 행 추가
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
                        "se_type": ' '
                    }
                    df = df.append(new_row, ignore_index=True)

                dataframes.append(df)

                regno += 1

    return dataframes


# 예시
current_dir = os.getcwd()
input_file_path = os.path.join(current_dir, "ch03.txt")

parse_txt(input_file_path)