import pandas as pd
import re
import os

current_dir = os.getcwd()

input_file_path = os.path.join(current_dir, "ch03.log")
output_file_path = os.path.join(current_dir, "output03.xlsx")

#  ‘cmdline’: 명령줄, ‘cmd’: 명령줄의 첫 명령, ‘depvar’: 종속변수명, ‘rsq’: R-squared, ‘f’: F값, ‘pf’: F통계와 관련된 p값, ’table’: 회귀결과 테이블(dataframe), … }
columns = ["source", "cmdline", "cmd", "regno", "depvar", "rsq", "adj_rsq", "Centered R2", "Uncentered R2", "f", "pf",
           "wald_ch2", "pchi2", "LR_chi2", "log_likelihood", "pseudo_r2",
           "coef", "first_stage", "reg_sub_desc", "margins", "heckman_secregression"]
columns_coef = ["varname", "coef", "se", "t", "p", "z", "nobs", "selected", "non_selected", "se_type", "rsq_within", "rsq_between", "rsq_overall", "dy/dx", "simga_u", "sigma_e", "rho"]
# columns_first_stage = ["coef", "se", "t", "p", "z", "nobs", "se_type", "rsq_within", "rsq_between", "rsq_overall"]
all_results_dict = {}
#기본값 None으로 설정한 dictionary 생성

a = 1
b = 1
with open(input_file_path, "r", encoding='utf-8') as f:

    data = f.read()
    sections = re.findall(r'(\*!!.*?)(?=\. \*!!|\Z)', data, re.DOTALL)
    # sections = re.findall(r'(reg .*?_cons[^\n]*\n|Source.*?_cons[^\n]*\n)', data, re.DOTALL)
    # sections = re.findall(r'(\*!!)(\*!!)', data, re.DOTALL)
    marginal_variable = None
    regression_num = 0
    for section in sections:

        # print(a)
        # print(section)
        # a = a + 1
        # Source, Part, Command, Regno의 정보
        regno = 0

        example_pattern = re.compile(r'Example\s+\d+\.\d+')
        example_match = example_pattern.findall(section)
        source = example_match[0] if example_match else None
        # regressions = re.findall(r'(reg .*?_cons[^\n]*\n|Source.*?_cons[^\n]*\n)', data, re.DOTALL)
        # regressions = re.findall(r'(reg .*?_cons[^\n]*\n|newey .*?_cons[^\n]*\n|Source.*?_cons[^\n]*\n)', data,
        # re.DOTALL)

        finals = re.findall(
            r'(regress .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|xtreg .*?(?:, noconstant|rho)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|probit .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|tobit .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|Poisson .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|logit .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|cnreg .*?(?:, noconstant|/sigma)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|ivregress .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|ivreg2 .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|ivreg .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|reg .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|newey .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|prais .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|heckman .*?(?:, noconstant|sigma)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|Source .*?_cons[^\n]*\n(?:[^\n]*?\n)*?'
            r'|(?<!\w\s)effects .*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?'
            r'|(?:IV .*?\()?2SLS(?:\)?.*?(?:, noconstant|_cons)[^\n]*\n(?:[^\n]*?\n)*?))',
            section, re.DOTALL)

        regressions = []
        mar_regressions = []

        for reg_block in finals:
            # noconstant 있는 경우
            if 'noconstant' in reg_block:
                last_var_match = re.search(r'(\w+), noconstant', reg_block)

                if last_var_match:
                    last_var = last_var_match.group(1)

                    # 원본 텍스트에서 reg_block 위치를 찾기
                    block_position = section.index(reg_block)
                    remaining_section = section[block_position:]

                    noconstant_position = remaining_section.index('noconstant') + len('noconstant')
                    remaining_section_after_noconstant = remaining_section[noconstant_position:]

                    last_var_position = re.search(rf'^\s*{last_var}\b.*?\n', remaining_section_after_noconstant,
                                                  re.MULTILINE)
                    if last_var_position:
                        # 해당 블록을 추출해서 regressions에 추가
                        end_position = last_var_position.end()
                        regression_block = remaining_section[:noconstant_position] + remaining_section_after_noconstant[
                                                                                     :end_position]

                        regressions.append(regression_block)

            else:
                # _cons가 있는 경우 그대로 블록으로 추가
                regressions.append(reg_block)

        for regression in regressions:

            multi_rsq = 0
            if re.search(r'\b(L|D)\.\w+', regression) or re.search(r'\bu_hat\b', regression):
                # lagged_variable_present = re.search(r'\bL\.\w+', regression)
                lagged_variable_present = re.search(r'\b(L|D)\.\w+', regression) or re.search(r'\bu_hat\b', regression)
            else:
                lagged_variable_present = None

            if re.search(r'\bi\.year\b', regression):
                years_variable_present = re.search(r'\bi\.year\b', regression)
            else:
                years_variable_present = None

            cmd = None
            cmdLine = None
            lines = regression.splitlines()
            for line in lines:
                match = re.search(
                    r'\b(Poisson|logit|cnreg|heckman|newey|prais|reg|regr|regre|regres|regress|ivreg|ivreg2|ivregress|tobit|probit|xtreg)\b',
                    line)
                if match:
                    cmd = match.group(0)
                    cmdline = line
                    break

            if match:

                # heckman의 두 번째 depvar 뽑아내기
                second_depvar = None
                if cmd == 'heckman':
                    second_depvar = re.search(r"sel\(\s*(\w+)", cmdline)
                    second_depvar = second_depvar.group(1)

                first_words = re.findall(r'^\s*(\w+[#\w.]*\w+)\s+\|', regression, re.MULTILINE)

                variables = [word for word in first_words if
                             word not in ("Source", "Model", "Residual", "Total")]
                dependent_variable = variables[0]

                first_independent_variable = variables[1]

                # lagged인지의 여부

                lagged = 0
                i_year = 0

                if lagged_variable_present:
                    independent_variables_match = re.findall(r'^\s*((L\d+\.\w+)|(\w+[#\w.]*))\s+\|', regression,
                                                             re.MULTILINE)
                    independent_variables_match = [match[0] for match in independent_variables_match]  # 첫 번째 그룹만 가져오기
                    lagged = 1

                elif years_variable_present:
                    pattern = r'^\s*([^\s|]+)\s*\|\s*([+-]?\d*\.\d+|\d+)\s+([+-]?\d*\.\d+)'
                    independent_variables_match = re.findall(pattern, regression, re.MULTILINE)

                    independent_variables_match = [match[0] for match in independent_variables_match]

                    i_year = 1

                else:
                    numsign_check_lines = regression.split('\n')
                    independent_variables_match = []
                    i = 0
                    year_index = None  # 'year' 변수의 인덱스를 추적
                    years_to_combine = []  # 합칠 연도들을 저장

                    while i < len(numsign_check_lines):
                        # regression의 각 줄마다 체크함
                        numsign_check_line = numsign_check_lines[i].strip()
                        # 현재 줄에서 variables 추출
                        # current_var = re.search(r'^\s*(\w+(?:\.\w+)*[#]?)(?:\s+\|)?', numsign_check_line)
                        current_var = re.search(r'^\s*(\w+(?:\.\w+)*(?:#\w+(?:\.\w+)*)?)', numsign_check_line)

                        # variables가 존재할 경우
                        if current_var:
                            # variable 맨 뒤에 #이 붙은 경우
                            var_name = current_var.group(1).strip('#')
                            # '#'으로 끝나는 경우, 다음 줄과 연결
                            if var_name.endswith('#'):
                                if i + 1 < len(numsign_check_lines):  # 다음 줄 확인
                                    next_line = numsign_check_lines[i + 1].strip()
                                    # 다음 줄에서 변수명 추출
                                    next_var_match = re.search(r'^\s*(\w+(?:\.\w+)*)', next_line)
                                    if next_var_match:
                                        next_var = next_var_match.group(0)
                                        var_name = var_name[:-1] + next_var  # '#' 제거 후 변수명 결합
                                        i += 1  # 다음 줄 처리
                            if var_name == "year":
                                year_index = i  # 'year'의 위치 저장
                                years_to_combine = []  # 다음 연도들을 저장할 리스트 초기화
                            elif year_index is not None and re.match(r'^\d{4}$', var_name):  # 연도 판별
                                years_to_combine.append(var_name)
                            # 결과 리스트에 변수명 추가, heckman일 경우에는 2번이기에, 변수 중복 허용

                            if cmd == 'heckman':
                                independent_variables_match.append(var_name)
                            elif var_name not in independent_variables_match:
                                independent_variables_match.append(var_name)

                        i += 1

                    # 'year'와 해당 연도들을 결과 리스트에서 제거하고, 'year == 연도' 형태로 추가
                    if year_index is not None and years_to_combine:
                        # 'year' 변수를 제거하고 'year == 연도' 형태로 추가
                        year_vars = [f'year == {year}' for year in years_to_combine]
                        # 기존의 'year' 및 이후 년도 변수들 제거
                        independent_variables_match = [var for var in independent_variables_match if
                                                       var != 'year' and not re.match(r'^\d{4}$', var)]
                        independent_variables_match.extend(year_vars)  # 새 형식 추가

                if independent_variables_match:
                    independent_variables = []

                    capture = False
                    for var in independent_variables_match:
                        if var == dependent_variable:
                            capture = True
                        if capture:
                            independent_variables.append(var)

                if lagged == 1:
                    adjusted_independent_variables = []
                    base_variable = None  # lag와 결합할 변수 저장

                    for var in independent_variables:
                        # 'L'로 시작하고 '.'으로 끝나는 원소일 경우
                        if (var.startswith('L') and var.endswith('.')) or (var.startswith('D') and var.endswith('.')):
                            # lag와 결합할 변수와 결합하여 추가
                            if adjusted_independent_variables and adjusted_independent_variables[-1] == base_variable:
                                adjusted_independent_variables.pop()
                            adjusted_independent_variables.append(f"{var}{base_variable}")

                        else:
                            # 결합할 첫 번째 변수를 지정
                            base_variable = var  # lag와 결합할 변수 설정
                            adjusted_independent_variables.append(var)

                    adjusted_independent_variables = list(dict.fromkeys(adjusted_independent_variables))
                    independent_variables = adjusted_independent_variables

                if i_year == 1:
                    independent_variables = independent_variables_match
                    # elif 'dy/dx' in regression:
                    #    print('hello')
                    #    independent_variables = independent_variables
                else:
                    independent_variables.pop(0)

                sigma_e = None
                sigma_u = None
                rho = None
                if cmd == 'xtreg':
                    independent_variables = independent_variables[:independent_variables.index('_cons') + 1]
                    sigma_u = re.search(r'sigma_u\s+\|\s+([0-9.-]+)', regression).group(1)
                    sigma_e = re.search(r'sigma_e\s+\|\s+([0-9.-]+)', regression).group(1)
                    rho = re.search(r'rho\s+\|\s+([0-9.-]+)', regression).group(1)

                # depvar 정의하기
                depvar = dependent_variable

                sec_independent_variables = []
                sec_variables_parameter = 0

                # heckman일 경우, 두 차례의 회귀에 대비함
                if cmd == 'heckman':
                    if second_depvar in independent_variables:
                        index = independent_variables.index(second_depvar)
                        index_2 = independent_variables.index('lambda')

                        sec_independent_variables = independent_variables[index + 1:index_2 + 1]
                        sec_variables_parameter = 1
                        independent_variables = independent_variables[:index]

            regression_stage = None

            if match == None:
                # first_words = re.findall(r'^\s*([a-zA-Z0-9_#]+)\s*\|', section, re.MULTILINE)

                first_words = re.findall(r'^\s*(\w+[#\w.]*\w+)\s+\|', regression, re.MULTILINE)

                variables = [word for word in first_words if
                             word not in ("Source", "Model", "Residual", "Total")]
                # print(variables)
                # dependent_variable = variables[0]

                # dy/dx일 경우에는 차별화
                # if 'dy/dx' not in regression:
                # depvar = dependent_variable
                if 'dy/dx' in regression:
                    independent_variables = variables
                else:
                    independent_variables = variables[1:]
                    dependent_variable = variables[0]
                    depvar = dependent_variable

            if cmd == 'logit':
                marginal_variable = independent_variables[-2]
                # print(marginal_variable)
            elif cmd == 'probit':
                marginal_variable = independent_variables[-2]
                # print(marginal_variable)
            elif cmd == 'tobit':
                marginal_variable = independent_variables[-2]
                # print(marginal_variable)
            else:
                marginal_variable = None

            if marginal_variable:
                # 매칭되는 부분을 찾기
                marginal_regressions = re.search(rf'\|\s+dy/dx.*?({marginal_variable}\s+\|.*?\n)', section, re.DOTALL)
                # marginal_regressions = re.search(rf'\|\s+dy/dx.*?{marginal_variable}', section, re.DOTALL)

                # 매칭된 부분 처리 (여기서는 print로 예시)
                # 이미 처리한 부분을 제거
                section = re.sub(re.escape(marginal_regressions.group(0)), '', section, count=1)
                marginal_regressions = marginal_regressions.group(0)
                i = 0
                while i < len(regressions):
                    if regressions[i] == regression:
                        regressions.insert(i + 1, marginal_regressions)
                    i = i + 1

            # number of obs, r_squared, adj_r_squared 추출하기
            if re.search(r'Number of obs\s+=\s+([\d,]+)', regression):

                number_of_obs = re.search(r'Number of obs\s+=\s+([\d,]+)', regression)
                number_of_obs = number_of_obs.group(1)
            else:
                number_of_obs = 'margins'

            if re.search(r'R-squared\s+=\s+([\d.]+)', regression):
                r_squared = re.search(r'R-squared\s+=\s+([\d.]+)', regression)
                r_squared = r_squared.group(1)

            else:
                r_squared = 'Group Variable'

            # adj_r_squared = re.search(r'Adj R-squared\s+=\s+([\d.]+)', section)

            if re.search(r'Adj R-squared\s+=\s+([-.\d]+)', regression):
                adj_r_squared = re.search(r'Adj R-squared\s+=\s+([-.\d]+)', regression)
            else:
                adj_r_squared = None

            centered_R2 = None
            uncentered_R2 = None

            if cmd == 'ivreg2':
                centered_R2 = re.search(r'Centered R2\s+=\s+([-.\d]+)', regression)
                centered_R2 = centered_R2.group(1)
                uncentered_R2 = re.search(r'Uncentered R2\s+=\s+([-.\d]+)', regression)
                uncentered_R2 = uncentered_R2.group(1)

            # number_of_obs = number_of_obs.group(1)

            if adj_r_squared:
                adj_r_squared = adj_r_squared.group(1)
            else:
                adj_r_squared = None

            if "Group variable:" in regression:

                multi_rsq = 1
                within_match = re.search(r'Within\s*=\s*([0-9.]+)', regression)
                between_match = re.search(r'Between\s*=\s*([0-9.]+)', regression)
                overall_match = re.search(r'Overall\s*=\s*([0-9.]+)', regression)

                rsq_within = float(within_match.group(1))
                rsq_between = float(between_match.group(1))
                rsq_overall = float(overall_match.group(1))

            else:
                rsq_within = None
                rsq_between = None
                rsq_overall = None

            nobs = number_of_obs
            rsq = r_squared
            adj_rsq = adj_r_squared

            # F와 PF의 추출

            # F 값 추출
            f_stat_match = re.search(r'F\(\d+,\s*\d+\)\s+=\s+([\d.]+)', regression)
            if f_stat_match:
                f_stat = f_stat_match.group(1)
            else:
                f_stat = None

            # Prob > F 값 추출
            prob_f_match = re.search(r'Prob > F\s+=\s+([\d.]+)', regression)
            if prob_f_match:
                prob_f = prob_f_match.group(1)
            else:
                prob_f = None

            # Wald chi2 값 추출
            wald_chi2 = re.search(r'Wald chi2\(\d+\)\s+=\s+([\d.]+)', regression)
            wald_chi2 = wald_chi2.group(1) if wald_chi2 else None

            # Prob > chi2 값 추출
            prob_chi2 = re.search(r'Prob > chi2\s+=\s+([\d.]+)', regression)
            prob_chi2 = prob_chi2.group(1) if prob_chi2 else None

            # LR chi2 값 추출
            LR_chi2 = re.search(r'LR chi2\(\d+\)\s+=\s+([\d.]+)', regression)
            LR_chi2 = LR_chi2.group(1) if LR_chi2 else None

            # Pseudo R2 값 추출
            Pseudo_R2 = re.search(r'Pseudo R2\s+=\s+([\d.]+)', regression)
            Pseudo_R2 = Pseudo_R2.group(1) if Pseudo_R2 else None

            # Log likelihood 값 추출
            Log_likelihood = re.search(r'Log likelihood\s*=\s*(-?\d+\.\d+)', regression)
            Log_likelihood = Log_likelihood.group(1) if Log_likelihood else None

            # selected, non_selected 값 추출
            selected = re.search(r'Selected\s+=\s+([\d.]+)', regression)
            selected = selected.group(1) if selected else None
            non_selected = re.search(r'Nonselected\s+=\s+([\d.]+)', regression)
            non_selected = non_selected.group(1) if non_selected else None

            # 항목들 순서 추출하기

            if 'dy/dx' in regression:
                # header = re.search(r"(dy/dx\s+[\w/.>\|]+\s+[\w/.>\|]+\s+[\w/.>\|]+\s+[\w/.>\|]+)", regression)
                # header = re.search(r"(\s+[\w/.>\|]+\s+[\w/.>\|]+\s+[\w/.>\|]+\s+[\w/.>\|]+\s+[\w/.>\|]+)", regression)
                header = re.search(r"(\s+[\w/.>\\|]+\s+[\w/.>\\|]+\s+[\w/.>\\|]+\s+[\w/.>\\|]+\s+[\w/.>\\|]+)",
                                   regression)
            elif cmd == 'heckman':
                # header = re.search(r"^\s*\|(.+)\|", regression, re.MULTILINE)
                # header = re.search(r"\|\s+([\w/.]+)\s+([\w/.]+)\s+([\w/.]+)\s+([\w/.]+)\s+([\w/.]+\|)", regression)
                header = re.search(r"(\s+[\w/.>\\|]+\s+[\w/.>\\|]+\s+[\w/.>\\|]+\s+[\w/.>\\|]+\s+[\w/.>\\|]+\|)",
                                   regression)
            else:
                header = re.search(fr"{re.escape(dependent_variable)}\s+\|([\w\s.>|]+)", regression)

            if header:
                headers = header.group(1)

                # Robust 혹은 margin이 있는지 확인
                robust_check = re.search(r"Robust", regression)
                Newey_check = re.search(r"newey", regression)
                margin_check = re.search(r"dy/dx(?!.*Std)", regression)

                if robust_check or Newey_check or margin_check:
                    headers = re.findall(r"std\.\s+err\.|[\w.>|]+", headers)
                    headers = [item.replace('std. err.', 'Std. err.') for item in headers]
                    if robust_check:
                        se_type = 'Robust'
                    if margin_check:
                        dy_index = headers.index('dy')
                        dx_index = headers.index('dx')
                        headers[dy_index:dx_index + 1] = ['dy/dx']

                # 'Std. err.'을 하나의 토큰으로 처리하기 위해 고급 정규 표현식 사용
                else:
                    headers = re.findall(r"Std\.\s+err\.|[\w.>|]+", headers)
                    se_type = ' '
                    if 'dy/dx' in regression:
                        dy_index = headers.index('dy')
                        dx_index = headers.index('dx')
                        headers[dy_index:dx_index + 1] = ['dy/dx']
            else:
                print("Header not found")


            # 독립 변수의 각각의 값들 추출하기
            # print(independent_variables)
            # 현재 처리 중인 섹션을 추적할 변수
            process_parameter = 0

            new_regression = []

            if not isinstance(all_results_dict.get(regression_num), list):
                all_results_dict[regression_num] = []

            temporary = None

            while process_parameter == 0:

                results_dict = {}
                # regression 텍스트를 줄 단위로 나누기
                lines = regression.splitlines()

                for line in lines:
                    # 각 줄에 대해 independent_variable을 처리
                    for independent_variable in independent_variables:

                        # varname 정의
                        varname = independent_variable

                        if_lagged = 0
                        # 만약 lagged일 경우
                        if re.match(r'^(L|D)\w*\.', independent_variable):
                            temp = independent_variable
                            independent_variable = independent_variable.split('.')[0] + '.'
                            if_lagged = 1

                        value = re.search(
                            fr"{independent_variable}\s+\|\s+([-+]?\d*\.?\d+(?:e[-+]?\d+)?)\s+([-+]?\d*\.?\d+(?:e[-+]?\d+)?)\s+([-+]?\d*\.?\d+(?:e[-+]?\d+)?)\s+([-+]?\d*\.?\d+(?:e[-+]?\d+)?)",
                            line
                        )

                        if value:
                            if if_lagged == 1:
                                if temp in independent_variables:
                                    independent_variables.remove(temp)
                            elif regression_stage == 'second':
                                 independent_variables = independent_variables
                            else:
                                if independent_variable in independent_variables:
                                    independent_variables.remove(independent_variable)
                            # 매치된 전체 결과를 리스트로 변환
                            r_list = [float(value.group(i)) for i in range(1, value.lastindex + 1)]
                            # r_list = [float(num) for num in re.findall(r'-?\d+\.\d+(?:e[-+]?\d+)?|-?\d+', line)[:4]]
                            stats = dict(zip(headers, r_list))

                            # Coefficient, dy/dx, Std. err. 등 값을 추출
                            if 'Coefficient' in stats:
                                coef = float(stats['Coefficient'])
                            else:
                                coef = None
                            if 'dy/dx' in stats:
                                dy_dx = float(stats['dy/dx'])
                            else:
                                dy_dx = None
                            if 'Std. err.' in stats:
                                se = float(stats['Std. err.'])
                            if 'z' in stats:
                                z = float(stats['z'])
                                p = float(stats['P>|z|'])
                                t = None
                            elif 't' in stats:
                                t = float(stats['t'])
                                p = float(stats['P>|t|'])
                                z = None
                            else:
                                z = None
                                p = None
                                t = None

                            if temporary != None:
                                all_results_dict[regression_num].append(temporary)

                            new_coef_row = ({
                                "varname": varname,
                                "coef": coef,
                                "se": se,
                                "t": t,
                                "p": p,
                                "z": z,
                                "nobs": nobs,
                                "selected": selected,
                                "non_selected": non_selected,
                                "se_type": se_type,
                                "rsq_within": rsq_within,
                                "rsq_between": rsq_between,
                                "rsq_overall": rsq_overall,
                                "dy/dx": dy_dx,
                                "sigma_e": sigma_e,
                                "sigma_u": sigma_u,
                                "rho": rho
                            })

                            new_row = ({
                                "source": source,
                                "cmdline": cmdline,
                                "cmd": cmd,
                                "regno": regno,
                                "depvar": depvar,
                                "rsq": rsq,
                                "adj_rsq": adj_rsq,
                                "Centered R2": centered_R2,
                                "Uncentered R2": uncentered_R2,
                                "f": f_stat,
                                "pf": prob_f,
                                "wald_chi2": wald_chi2,
                                "pchi2": prob_chi2,
                                "LR_chi2": LR_chi2,
                                "log_likelihood": Log_likelihood,
                                "pseudo_r2": Pseudo_R2,
                                "coef": new_coef_row,
                                "first_stage": None,
                                "reg_sub_desc": None,
                                "margins": None,
                                "heckman_secregression": None
                            })

                            if 'first' in cmdline:
                                new_row = ({
                                    "coef": None,
                                    "first_stage": new_coef_row,
                                    "reg_sub_desc": 'first stage'
                                })
                            elif 'dy/dx' in regression:
                                new_row = ({
                                    "coef": None,
                                    "margins": new_coef_row
                                })
                            if regression_stage == 'second':
                                new_row = ({
                                    "coef": None,
                                    "heckman_secregression": new_coef_row
                                })
                                sec_variables_parameter = 0

                            all_results_dict[regression_num].append(new_row)


                # sec_variables_parameter에 따라 다음 섹션을 처리
                if sec_variables_parameter == 1:
                    depvar = second_depvar
                    independent_variables = sec_independent_variables

                    regression_stage = 'second'
                    process_parameter = 0

                    reinitialize_from = re.search(
                        r"_cons\s+\|\s+[-\d.]+\s+[\d.]+\s+[-\d.]+\s+[\d.]+\s+[-\d.]+\s+[-\d.]+", regression)
                    if reinitialize_from:
                        regression = regression[reinitialize_from.end():].strip()
                else:
                    process_parameter = 1

            regno = regno + 1
            regression_num = regression_num + 1


for key, value in enumerate(all_results_dict[0]):
    print(f"{key}: {value}\n")