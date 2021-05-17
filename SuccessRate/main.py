import pickle
from datetime import datetime
import multiprocessing as mp


with open("./../../Pickles/IRR_Confidence_class_only.pickle", "rb") as p:
    IRR = pickle.load(p)
with open("./../../Pickles/IRR.pickle", "rb") as p:
    IRR1 = pickle.load(p)
with open("./../../Pickles/IRRv2.pickle", "rb") as p:
    IRR2 = pickle.load(p)
with open("./../../Pickles/IRRv3.pickle", "rb") as p:
    IRR3 = pickle.load(p)
with open("./../../Pickles/Ref.pickle", "rb") as p:
    Ref = pickle.load(p)


def LOG(log, str):
    log.write(str)


def phase_comparison():
    correct = 0
    not_correct = 0
    global IRR, IRR1
    for key in IRR.keys():
        if key in IRR1.keys() and key in Ref.keys():
            if IRR1[key] == Ref[key] and IRR[key] == IRR[key]:
                correct += 1
            if IRR1[key] == Ref[key] and IRR[key] != IRR1[key] and IRR[key] != "P2P":
                not_correct += 1
    return correct, not_correct


def coverage(given_IRR, key, AS_coverage_set1, AS_coverage_set2):
    if given_IRR[key] == 'Unknown': return
    AS_coverage_set1.add(key[0])
    for AS in key:
        AS_coverage_set2.add(AS)


def key_analysis(given_dicts, key1, reverse=False):
    dict1, dict2 = given_dicts
    key2 = key1[::-1] if reverse else key1
    if key1 not in dict1.keys() or key2 not in dict2.keys():
        return 0, 0
    if dict1[key1] == 'Unknown' or dict2[key2] == 'Unknown':
        return 0, 0
    val1 = dict1[key1]
    val2 = dict2[key2][::-1] if reverse else dict2[key2]
    match = val1 == val2
    return 1, match


def add_key_to_set(dic, key, condition=True):
    if condition:
        temp_set = dic.get(key[0], set())
        temp_set.add(key)
        dic[key[0]] = temp_set


def IRR_analysis(given_IRR, log):
    matching_classifications = 0
    two_sided_classifications = 0
    two_sided_agreements = 0
    ToR_count = 0
    prev = -1
    unknown = list(given_IRR.values()).count('Unknown')
    AS_coverage_set_1_side = set()
    AS_coverage_set_2_side = set()
    number_of_ToRs_in_our_IRR = len(list(given_IRR.keys())) - unknown
    number_of_ToRs_in_ref_IRR = len(list(Ref.keys()))
    known_keys_in_both = 0
    mistakes = dict()
    classifications = dict()
    classifications_2_sided = dict()
    #correct, not_correct = phase_comparison()
    confusion_matrix = {
        'P2P': {
            'P2P': 0,
            'P2C': 0,
            'C2P': 0
        },
        'P2C': {
            'P2P': 0,
            'P2C': 0,
            'C2P': 0
        },
        'C2P': {
            'P2P': 0,
            'P2C': 0,
            'C2P': 0
        }
    }
    for key in given_IRR.keys():
        ToR_count += 1
        # one_over_percent = 100
        # p = int(one_over_percent * ToR_count/len(given_IRR.keys()))
        # if p != prev:
        #     print(str(100 * p / one_over_percent) + '%')
        # prev = p
        key_in_both_dicts, key_match = key_analysis((given_IRR, Ref), key)
        known_keys_in_both += key_in_both_dicts
        matching_classifications += key_match
        key_2_sided, key_2_sided_match = key_analysis((given_IRR, given_IRR), key, True)
        two_sided_classifications += key_2_sided
        two_sided_agreements += key_2_sided_match
        coverage(given_IRR, key, AS_coverage_set_1_side, AS_coverage_set_2_side)
        add_key_to_set(mistakes, key, key_2_sided and not key_2_sided_match)
        add_key_to_set(classifications_2_sided, key, key_2_sided)
        add_key_to_set(classifications, key)
        if key_in_both_dicts:
            confusion_matrix[Ref[key]][given_IRR[key]] += 1
    P2P = [confusion_matrix['P2P']['P2P'], confusion_matrix['P2P']['P2C'], confusion_matrix['P2P']['C2P']]
    P2C = [confusion_matrix['P2C']['P2P'], confusion_matrix['P2C']['P2C'], confusion_matrix['P2C']['C2P']]
    C2P = [confusion_matrix['C2P']['P2P'], confusion_matrix['C2P']['P2C'], confusion_matrix['C2P']['C2P']]

    # print(str(round(float(P2P[0])/(P2P[0] + P2P[1] + P2P[2]) * 100, 2)) + "%")
    padding = 12
    LOG(log, '\tP2P matching rate (relative to CAIDA) is %s\n' % (str(round(float(P2P[0]) / (sum(P2P)) * 100, 2)) + "%"))
    LOG(log, '\tP2C matching rate (relative to CAIDA) is %s\n' % (str(round(float(P2C[1]) / (sum(P2C)) * 100, 2)) + "%"))
    LOG(log, '\tC2P matching rate (relative to CAIDA) is %s\n' % (str(round(float(C2P[2]) / (sum(C2P)) * 100, 2)) + "%"))
    LOG(log, '\tConfusion matrix is:               %s, %s, %s\n'
        % ('IRR P2P'.ljust(padding), 'IRR P2C'.ljust(12), 'IRR C2P'.ljust(padding)))
    LOG(log, '\t' + ' ' * len('Confusion matrix is:\t') + '%s, %s, %s, %s\n' % ('CAIDA P2P'.rjust(padding),
        str(P2P[0]).rjust(padding), str(P2P[1]).rjust(padding), str(P2P[2]).rjust(padding)))
    LOG(log, '\t' + ' ' * len('Confusion matrix is:\t') + '%s, %s, %s, %s\n' % ('CAIDA P2C'.rjust(padding),
        str(P2C[0]).rjust(padding), str(P2C[1]).rjust(padding), str(P2C[2]).rjust(padding)))
    LOG(log, '\t' + ' ' * len('Confusion matrix is:\t') + '%s, %s, %s, %s\n' % ('CAIDA C2P'.rjust(padding),
        str(C2P[0]).rjust(padding), str(C2P[1]).rjust(padding), str(C2P[2]).rjust(padding)))

    LOG(log, '\tWe can classify %s ToRs\n' % (ToR_count - unknown))
    LOG(log, '\tWe can classify %s, %s ASNs\n' % (len(AS_coverage_set_1_side), len(AS_coverage_set_2_side)))
    LOG(log, '\tUnknown is %s\n' % unknown)
    LOG(log, '\tThere are %s 2-sided classifications\n' % two_sided_classifications)
    LOG(log, '\tThere are %s 1-sided classifications\n' % (ToR_count - two_sided_classifications - unknown))
    LOG(log, '\toverall matching rate is: %s%%\n' % round(float(matching_classifications) / known_keys_in_both * 100, 2))
    LOG(log, "\tNumber of Matching Classifications: %s\n" % matching_classifications)
    LOG(log, "\tNumber of Known ToRs in this and CAIDA's IRR: %s\n" % known_keys_in_both)
    LOG(log, "\tNumber of ToRs in Ref IRR: %s\n" % number_of_ToRs_in_ref_IRR)
    LOG(log, '\tratio of 2-sided agreements is %s%%\n' % round(100 * two_sided_agreements/two_sided_classifications, 2))
    LOG(log, '\tratio of conflicts is %s%%\n' % round(100 * (1 - two_sided_agreements/two_sided_classifications), 2))
    return mistakes, classifications_2_sided, classifications


def log_IRR(IRR, msg):
    log = open(f'./../../Example Files/Logs/%s {msg[:-1]}.txt' % datetime.now().strftime('%d.%m.%y %H;%M;%S'), 'w')
    LOG(log, msg + '\n')
    mistakes, classifications_2_sided, classifications = IRR_analysis(IRR, log)
    with open(f'./../../Pickles/Mistakes/{msg[:-1]} Mistakes.pickle', 'wb') as p:
        pickle.dump(mistakes, p)
    with open(f'./../../Pickles/Classifications/{msg[:-1]} Classifications 2-Sided.pickle', 'wb') as p:
        pickle.dump(classifications_2_sided, p)
    with open(f'./../../Pickles/Classifications/{msg[:-1]} Classifications.pickle', 'wb') as p:
        pickle.dump(classifications, p)
    LOG(log, '\n')
    print(f'{msg[:-1]} Process Finished.')
    log.close()


if __name__ == '__main__':
    args_list = [
        (IRR1, 'I_E Dictionary:'),
        (IRR2, 'Remarks Dictionary:'),
        (IRR3, 'Sets Dictionary:'),
        (IRR, 'Overall Dictionary:')
    ]
    processes = list()
    for arg in args_list:
        msg = arg[1]
        current_arg = (arg[0], arg[1])
        processes.append(mp.Process(target=log_IRR, args=current_arg))

    for process in processes:
        process.start()
    for process in processes:
        process.join()



