from functools import reduce

def mod_subj_extract(sentence_annotator,subject_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]
    dependency_list = []

    if subject_num is not None:

        for dependency in dependency_plus:
            if dependency["dep"].endswith('mod') and dependency["governor"] == subject_num:
                dependency_list.append(dependency)
    mod_subject = []
    if len(dependency_list) > 0 :
        for dependency in dependency_list:
            element = {}
            element["element"] = dependency["dependentGloss"]
            element["startIndex"] = dependency["dependent"]
            element["endIndex"] = element["startIndex"] + 1
            mod_subject.append(element)
    elif subject_num is not None and len(tokens) > subject_num and tokens[subject_num]["pos"] in ['VBZ','VBS']:
        if dependency_search('nsubj',subject_num,dependency_plus,2):
            for dependency in dependency_search('nsubj',subject_num,dependency_plus,2):
                if tokens[dependency["governor"]-1]["pos"] == 'JJ':
                    element = {}
                    element["element"] = dependency["governorGloss"]
                    element["startIndex"] = dependency["governor"]
                    element["endIndex"] = element["startIndex"] + 1
                    mod_subject.append(element)
    if len(mod_subject) > 0:
        return mod_subject
    else:
        return None

def mod_verb_extract(sentence_annotator,verb_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    verb = sentence_annotator["tokens"][verb_num - 1]["originalText"]
    dependency_list = []
    mod_verb = []
    for dependency in dependency_plus:
        if dependency["dep"].endswith('mod') and dependency["governorGloss"] == verb:
            dependency_list.append(dependency)
    if len(dependency_list) > 0:
        for dependency in dependency_list:
            element = {}
            element["element"] = dependency["dependentGloss"]
            element["startIndex"] = dependency["dependent"]
            element["endIndex"] = element["startIndex"] + 1
            mod_verb.append(element)
    if len(mod_verb) > 0:
        return mod_verb
    else:
        return None

def mod_obj_extract(sentence_annotator,obj_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    dependency_list = []
    if obj_num is not None:
        for dependency in dependency_plus:
            if dependency["dep"].endswith('mod') and dependency["governor"] == obj_num:
                dependency_list.append(dependency)
    mod_obj = []
    if len(dependency_list) > 0:
        for dependency in dependency_list:
            element = {}
            element["element"] = dependency["dependentGloss"]
            element["startIndex"] = dependency["dependent"]
            element["endIndex"] = element["startIndex"] + 1
            mod_obj.append(element)
        return mod_obj
    else:
        return None


def dependency_search(types,word_num,dependencies,pattern):
    '''
    pattern 1:search dependency by relation governor
    pattern 2:search dependency by relation dependent
    '''
    dependency_list = []
    for one_dependency in dependencies:
        if pattern == 1:
            if one_dependency["dep"] == types and one_dependency["governor"] == word_num:
                dependency_list.append(one_dependency)
        if pattern == 2:
            if one_dependency["dep"] == types and one_dependency["dependent"] == word_num:
                dependency_list.append(one_dependency)
    if len(dependency_list) > 0 :
        return dependency_list
    else:
        return None


def list_dict_duplicate_removal(list):
    run_function = lambda x, y: x if y in x else x + [y]
    return reduce(run_function,[[],] + list)


def check_coref(word,sent_num,corefs,tokens):
    if word:
        for _,value in corefs.items():
            for item in value:
                if item["sentNum"] == sent_num and item["startIndex"] == word["startIndex"] and item["isRepresentativeMention"] == False:
                    for i in range(len(value)):
                        if value[i]["sentNum"] == sent_num and  ('NN' in tokens[value[i]["startIndex"]-1]["pos"]) and value[i]["startIndex"] != word["startIndex"]:
                            word["startIndex"] = value[i]["startIndex"]
                            word["endIndex"] = value[i]["endIndex"]
                            word["element"] = value[i]["text"]
                            return
