from collections import defaultdict
import pickle

#%% load dictionary
with open('data/fang2yao_jczs.pkl', 'rb') as f:
    dict_f2y_jczs = pickle.load(f)
with open('data/yao2fang_jczs.pkl', 'rb') as f:
    dict_y2f_jczs = pickle.load(f)


def match_zhongyao(th, ori):
    '''
    两字符串的匹配，存在包含或被包含关系时认为两字符串同义，如“熟地”和“熟地黄”
    :param th: 理论（匹配字典）方剂的中药组成
    :param ori: 医嘱开方中包含的中药
    :return: 如果匹配，返回True，否则返回False
    '''
    has_ac = False
    if ori in th or th in ori:
        has_ac = True
    return has_ac

def find_ac(list_ori, thy):
    '''
    查找医嘱中与当前方剂匹配的君/臣/佐/使药，返回相应列表
    :param list_ori: 医嘱包含的所有中药
    :param thy: theory_yao,理论的君/臣/佐/使药
    :return: 医嘱中能匹配当前方剂的君/臣/佐/使药列表
    '''
    list_yao = []
    for th in thy:
        for ori in list_ori:
            has_ac = match_zhongyao(th, ori)
            if has_ac:
                list_yao.append(ori)
    list_yao = list(set(list_yao))

    return list_yao

# %%单方识别
weight=[0.2238, 0.3418, 0.2477, 0.1636, 0.0231]
#weight=[0.2238, 0.3418, 0.2477, 0.1636, 0.0231]

def search_match(meds, method=1, weight=weight, cons=0.6):
    '''
    全匹配算法
    :param meds:中药名序列
    :param cons:匹配度
    :param method:方法，1:ISR，2:SIAP-ALL, 3:SIAP+ALL
    :param weight: 权重
    :return:
    '''
    list_fang = []  # 可能识别出多个方
    list_fang_name = []  # 多个方名

    list_ori = meds
    list_rem = meds
    list_use = []
    while list_rem:
        yao = list_rem[0]
        list_use.append(yao)
        # list_ = dict_y2f[yao]
        list_ = dict_y2f_jczs[yao]
        # list_ratio = []
        for fang in list_:
            dict_fang = {}

            # 君臣佐使匹配
            yao_th_jczs = dict_f2y_jczs[fang]  # 数据库中当前方剂中药组成
            juny = yao_th_jczs['jun']  # 完全匹配
            cheny = yao_th_jczs['chen']  # 至少匹配3/4
            zuoy = yao_th_jczs['zuo']  # 至少匹配1/2
            shiy = yao_th_jczs['shi']  # 无需匹配，有为加分项
            yao_ac = defaultdict(list)  # 医嘱中包含的当前方剂相关的中药
            yao_ac['jun'] = find_ac(list_ori, juny) if juny else []
            yao_ac['chen'] = find_ac(list_ori, cheny) if cheny else []
            yao_ac['zuo'] = find_ac(list_ori, zuoy) if zuoy else []
            yao_ac['shi'] = find_ac(list_ori, shiy) if shiy else []

            ratio_jun = len(yao_ac['jun']) / len(yao_th_jczs['jun']) if yao_th_jczs['jun'] else 0.5
            ratio_chen = len(yao_ac['chen']) / len(yao_th_jczs['chen']) if yao_th_jczs['chen'] else 0.5
            ratio_zuo = len(yao_ac['zuo']) / len(yao_th_jczs['zuo']) if yao_th_jczs['zuo'] else 0.5
            ratio_shi = len(yao_ac['shi']) / len(yao_th_jczs['shi']) if yao_th_jczs['shi'] else 0.5

            # 查找匹配
            # yao_th = dict_f2y[fang]
            yao_th = yao_th_jczs['jun'] + yao_th_jczs['chen'] + yao_th_jczs['zuo'] + yao_th_jczs['shi']

            # yao_ac = list(set(yao_th).intersection(set(list_ori))) # 字符串完全匹配
            # 字符串存在包含的关系即可
            yao_ac = []
            for th in yao_th:
                for ori in list_ori:
                    has_ac = match_zhongyao(th, ori)
                    if has_ac:
                        yao_ac.append(ori)
            yao_ac = list(set(yao_ac))
            ratio = len(yao_ac) / len(yao_th)
            for m in yao_th:
                if m in fang and m not in yao_ac:
                    ratio = 0
            # list_ratio.append(ratio)
            r0 = ratio * weight[0]  # 0.22 #0.37
            r1 = ratio_jun * weight[1]  # 0.44 #0.29
            r2 = ratio_chen * weight[2]  # 0.32 #0.23
            r3 = ratio_zuo * weight[3]  # 0.21 #0.09
            r4 = ratio_shi * weight[4]  # 0.03 #0.03
            ratio_jczs = (r1 + r2 + r3 + r4) if method == 2 else (r0 + r1 + r2 + r3 + r4)

            ration_condition = 0
            if method == 1:
                ration_condition = ratio
            elif method == 2:
                ration_condition = (r1 + r2 + r3 + r4)
            else:
                ration_condition = (r0 + r1 + r2 + r3 + r4)

            if ration_condition >= cons:
                list_use.extend(yao_ac)
                dict_fang['方剂'] = fang
                # dict_fang['匹配度'] = '{}|{}'.format(len(yao_ac),len(yao_th))
                dict_fang['共同药味数'] = '{}'.format(len(yao_ac))
                dict_fang['成方总药味数'] = '{}'.format(len(yao_th))
                dict_fang['比率'] = format(ratio, '.4f')
                dict_fang['比率jczs'] = format(ratio_jczs, '.4f')
                dict_fang['比率-君'] = format(ratio_jun, '.4f')
                dict_fang['比率-臣'] = format(ratio_chen, '.4f')
                dict_fang['比率-佐'] = format(ratio_zuo, '.4f')
                dict_fang['比率-使'] = format(ratio_shi, '.4f')
                # yao_dif = list(set(yao_th)-set(yao_ac))
                # yao_acc = yao_ac
                # yao_acc.extend(yao_dif) #if yao_dif else yao_ac
                # dict_fang['依据'] = yao_acc # 前len(yao_ac)个是匹配到的，后len(yao_th-yao_ac)是未匹配到的
                dict_fang['依据原方中药'] = yao_ac
                dict_fang['实际成方中药'] = yao_th
                dict_fang['实际成方中药-君'] = yao_th_jczs['jun']
                dict_fang['实际成方中药-臣'] = yao_th_jczs['chen']
                dict_fang['实际成方中药-佐'] = yao_th_jczs['zuo']
                dict_fang['实际成方中药-使'] = yao_th_jczs['shi']

                list_fang_name.append(fang)
                list_fang.append(dict_fang)

        list_use = list(set(list_use))
        list_rem = list(set(list_ori).difference(list_use))

    return list_fang, list_fang_name
