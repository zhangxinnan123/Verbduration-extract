import json
import io
import os
import sys,argparse
# os.chdir('F://Verbduration//code')
# sys.path.append('F://Verbduration//code')
from utlis import dependency_search,mod_obj_extract,mod_subj_extract,mod_verb_extract ,list_dict_duplicate_removal,check_coref

parser = argparse.ArgumentParser(description="parameters")
parser.add_argument("--text-folder", type = str, help = "path to the folder to be parsed")
parser.add_argument("--save-file", type = str, help = "path to save the result")
args = parser.parse_args()


def jsonfile_read(file_name):
    file=open(str(file_name),encoding='utf-8')
    file_list=json.load(file)
    annotator = file_list["result_list"]
    print(len(annotator))
    return annotator

def spend_pattern_judge(sentence_annotator):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    for one_dependency in dependency_plus:
        if one_dependency["dep"] == 'dobj' or one_dependency["dep"].startswith('nmod'):
            num_1 = one_dependency["governor"] 
            num_2 = one_dependency["dependent"] 
            token_1 = sentence_annotator["tokens"][num_1 - 1]
            token_2 = sentence_annotator["tokens"][num_2 - 1]
            if token_1["lemma"] == 'spend' and token_2["ner"] == 'DURATION':
                if dependency_search('xcomp',num_1,dependency_plus,1):
                    num = dependency_search('xcomp',num_1,dependency_plus,1)[0]["dependent"]
                    if sentence_annotator["tokens"][num - 1]["pos"].startswith("VB"):
                        return num_1
                if dependency_search('advcl',num_1,dependency_plus,1):
                    num = dependency_search('advcl',num_1,dependency_plus,1)[0]["dependent"]
                    if sentence_annotator["tokens"][num - 1]["pos"].startswith('VB'):
                        return num_1
    return None



def label_extract(sentence_annotator,spend_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]
    label_list = []
    dependency_list = []

    for one_dependency in dependency_plus:
        if one_dependency["dep"] == 'dobj' and one_dependency["governor"] == spend_num:
            num  = one_dependency["dependent"]
            if tokens[num-1]["ner"] == "DURATION":
                dependency_list.append(one_dependency)
        if one_dependency["dep"].startswith("nmod") and one_dependency["governor"] == spend_num:
            num = one_dependency["dependent"]
            if tokens[num-1]["ner"] == "DURATION":
                dependency_list.append(one_dependency)
    for dependency in dependency_list:
        # duration = ""
        # index = dependency["dependent"]
        # mod = []
        # for dependency in dependency_plus:
        #     if (dependency["dep"] in ['nummod','amod']) and dependency["governor"] == index:
        #         mod.append(dependency)
        # mod = sorted(mod,key=lambda item: item.__getitem__("dependent"),reverse=True)
        # num = index

        # if tokens[index - 2]["ner"] == "DURATION":
        #     flag = 1
        #     while tokens[index-1]["ner"] == "DURATION":
        #         duration = tokens[index-1]["originalText"] + " " + duration if len(duration) > 0 else tokens[index-1]["originalText"]
        #         index -= 1
        # elif tokens[index]["ner"] == "DURATION":
        #     flag = 0
        #     while tokens[index - 1]["ner"] == "DURATION":
        #         duration = duration + " " + tokens[index-1]["originalText"] if len(duration) > 0 else tokens[index-1]["originalText"]
        #         index += 1
        # else:
        #     flag = 0
        #     duration = tokens[index - 1]["originalText"]
        # if len(mod) > 0:
        #     for item in mod:
        #         if duration.find(item["dependentGloss"]) == -1:
        #             if dependency_search('cc', item["dependent"], dependency_plus, 1):
        #                 duration = item["dependentGloss"] + " " + dependency_search('cc', item["dependent"], dependency_plus, 1)[0]["dependentGloss"] + " " + duration
        #             else:
        #                 duration = item["dependentGloss"] + " " + duration
        # element = {}
        # element["element"] = duration
        # element["startIndex"] = num if flag == 0 else num - len(duration.split(' ')) + 1
        # element["endIndex"] = element["startIndex"] + len(duration.split(' '))
        # label_list.append(element)
        words = []
        index = dependency["dependent"]
        for dependency in dependency_plus:
            if (dependency["dep"] in ['nummod','amod']) and dependency["governor"] == index:
                words.append((dependency["dependentGloss"], dependency["dependent"]))
        num = index
        while tokens[index-1]["ner"] == "DURATION":
            words.append((tokens[index-1]["originalText"], index))
            index -= 1
        while tokens[num]["ner"] == "DURATION":
            words.append((tokens[num]["originalText"], num+1))
            num += 1
        for word in words:
            if dependency_search('cc', word[1], dependency_plus, 1):
                one = dependency_search('cc', word[1], dependency_plus, 1)[0]
                if one["dependent"] < sorted(words, key = lambda x: x[1])[-1][1]:
                    words.append((one["dependentGloss"], one["dependent"]))
        
        words = list(set(words))
        words = sorted(words, key = lambda x: x[1])
        sent = [item[0] for item in words]
        duration = ' '.join(sent)
        startIndex = words[0][1]
        endIndex = words[-1][1] + 1

        element = {}
        element["element"] = duration
        element["startIndex"] = startIndex
        element["endIndex"] = endIndex
        label_list.append(element)
    label_list = list_dict_duplicate_removal(label_list)
    return label_list

def verb_extract(sentence_annotator,spend_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]

    if dependency_search('xcomp',spend_num,dependency_plus,1):
        verb_num = dependency_search('xcomp',spend_num,dependency_plus,1)[0]["dependent"]
    else:
        verb_num = dependency_search('advcl',spend_num,dependency_plus,1)[0]["dependent"]
    verb = tokens[verb_num - 1]["lemma"]
    while dependency_search('xcomp',verb_num,dependency_plus,1):
        
        verb_num = dependency_search('xcomp',verb_num,dependency_plus,1)[0]["dependent"]
        verb = tokens[verb_num - 1]["lemma"]
    if dependency_search('compound:prt',verb_num,dependency_plus,1) is not None:
        verb = tokens[verb_num-1]["lemma"] + ' ' + tokens[dependency_search('compound:prt',verb_num,dependency_plus,1)[0]["dependent"]-1]["lemma"]
    else:
        verb = tokens[verb_num-1]["lemma"]

    if spend_num > verb_num:
        return None
    else:
        element = {}
        element["element"] = verb
        element["startIndex"] = verb_num
        element["endIndex"] = verb_num + len(verb.split(' '))
        return element,verb_num

def subj_extract(sentence_annotator,spend_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]
    subject = None
    subject_num = None
    startIndex = None
    if dependency_search('nsubj',spend_num,dependency_plus,1):
        subject = dependency_search('nsubj',spend_num,dependency_plus,1)[0]["dependentGloss"]
        subject_num = dependency_search('nsubj',spend_num,dependency_plus,1)[0]["dependent"]
    else:
        verb_num = spend_num
        if dependency_search('xcomp',verb_num,dependency_plus,2) or dependency_search('advcl',verb_num,dependency_plus,2) or dependency_search('dep',verb_num,dependency_plus,2):
            if dependency_search('xcomp',spend_num,dependency_plus,2):
                num = dependency_search('xcomp',spend_num,dependency_plus,2)[0]["governor"]
            elif dependency_search('advcl',spend_num,dependency_plus,2):
                num = dependency_search('advcl',spend_num,dependency_plus,2)[0]["governor"]
            elif dependency_search('dep',verb_num,dependency_plus,2):
                num = dependency_search('dep',verb_num,dependency_plus,2)[0]["governor"]

            if dependency_search('nsubj',num,dependency_plus,1):
                subject_num = dependency_search('nsubj',num,dependency_plus,1)[0]["dependent"]
                subject = tokens[subject_num-1]["originalText"]
            
    if subject is None:
        for i in range(1,len(tokens)+1):
            for dependency in dependency_plus:
                if dependency["dependent"] == i and dependency["dep"].startswith('nsubj'):
                    if tokens[i-1]["pos"].startswith("NN"):
                        subject = tokens[i-1]["originalText"]
                        subject_num = i

    if subject is not None:
        if dependency_search('compound',subject_num,dependency_plus,1):
            dependencies = dependency_search('compound',subject_num,dependency_plus,1)
            dependencies = sorted(dependencies,key=lambda dependency: dependency.__getitem__("dependent"),reverse=True)
            startIndex = dependencies[-1]["dependent"]
            for dependency in dependencies:
                subject = dependency["dependentGloss"] + " " + subject
    if subject is None:
        return subject,subject_num
    else:
        element = {}
        element["element"] = subject
        element["startIndex"] = startIndex if startIndex else subject_num
        element["endIndex"] = subject_num + 1
        return element,subject_num


def obj_extract(sentence_annotator,verb_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]

    obj = None
    prepositions = None
    obj_num = None
    startIndex = None
    if dependency_search('dobj',verb_num,dependency_plus,1):
        obj_num = dependency_search('dobj',verb_num,dependency_plus,1)[0]["dependent"]
        obj = sentence_annotator["tokens"][obj_num-1]["originalText"]
        
    else:
        for one_dependency in dependency_plus:
            if one_dependency["dep"].startswith("nmod") and one_dependency["governor"] == verb_num:
                obj_num = one_dependency["dependent"]
                obj = sentence_annotator["tokens"][obj_num-1]["originalText"]
                if dependency_search('case',obj_num,dependency_plus,1):
                    prepositions = dependency_search('case',obj_num,dependency_plus,1)[0]["dependentGloss"]
                    element_p = {}
                    element_p["element"] = prepositions
                    element_p["startIndex"] = dependency_search('case',obj_num,dependency_plus,1)[0]["dependent"]
                    element_p["endIndex"] = element_p["startIndex"] + 1
                break
                
    if obj_num is not None:
        if dependency_search('compound',obj_num,dependency_plus,1):
            dependencies = dependency_search('compound',obj_num,dependency_plus,1)
            dependencies = sorted(dependencies,key=lambda dependency: dependency["dependent"],reverse=True)
            startIndex = dependencies[-1]["dependent"]
            for dependency in dependencies:
                obj = dependency["dependentGloss"] + " " + obj

    if obj is not None:
        element = {}
        element["element"] = obj
        element["startIndex"] = startIndex if startIndex else obj_num
        element["endIndex"] = obj_num + 1
        if prepositions is None:
            return element,obj_num,prepositions
        else:
            return element,obj_num,element_p
    else:
        return obj,obj_num,prepositions




def pattern_select(sentence_annotator,spend_num,prepositions):
    '''
    PS1.someone spend sometime doing something
    PS2.someone spend sometime doing at/in/on/for/.. something
    PS3.someone spend sometime in someplace, doing something
    PS4.someone spend sometime in someplace, doing at/in/on/for/.. something

    '''
    dependency_plus = sentence_annotator["enhancedDependencies"]
    if prepositions is not None:
        relation = []
        for dependency in dependency_plus:
            if dependency["dep"].startswith('nmod:in') and dependency["governor"] == spend_num:
                relation.append(dependency["dep"])

        pattern = 'PS2a' if len(relation) > 0 else 'PS1a'
    else:
        relation = []
        for dependency in dependency_plus:
            if (dependency["dep"] == 'nmod:in') and dependency["governor"] == spend_num:
                relation.append(dependency["dep"])

        pattern = 'PS2' if len(relation) > 0 else 'PS1'
    return pattern


def spend_extract(file_name):
    i = 0
    json_list = []
    annotator = jsonfile_read(file_name)
    while i < len(annotator):
        corefs = annotator[i]["corefs"]
        sentence_num = 1
        for one_sentence in annotator[i]["sentences"]:
            tokens = one_sentence["tokens"]
            json_dic = {}
            if spend_pattern_judge(one_sentence) is not None:
                spend_num = spend_pattern_judge(one_sentence)

                sentence = ""
                for one_token in tokens:
                    sentence = sentence + " " + one_token["originalText"]
                if verb_extract(one_sentence,spend_num = spend_num) is None:
                    continue
                print("spend_success")
                json_dic["sentence"] = sentence
                json_dic["verb"],verb_num = verb_extract(one_sentence,spend_num = spend_num)
                json_dic["label"] = label_extract(one_sentence,spend_num = spend_num)
                json_dic["subject"],subj_num = subj_extract(one_sentence,spend_num)
                json_dic["object"],obj_num,json_dic["prepositions"] = obj_extract(one_sentence,verb_num)
                json_dic["mod_subj"] = mod_subj_extract(one_sentence,subj_num)
                json_dic["mod_obj"] = mod_obj_extract(one_sentence,obj_num)
                json_dic["mod_verb"] = mod_verb_extract(one_sentence,verb_num)
                json_dic["pattern"] = pattern_select(one_sentence,spend_num,json_dic["prepositions"])
                check_coref(json_dic["subject"],sentence_num,corefs,tokens)
                check_coref(json_dic["object"],sentence_num,corefs,tokens)


                if json_dic not in json_list:
                    json_list.append(json_dic)
            sentence_num += 1
        i += 1
    return json_list

def iter_spend_extract(one_sentence, sentence_num, corefs):
    json_dic = {}
    tokens = one_sentence["tokens"]
    if spend_pattern_judge(one_sentence) is not None:
        spend_num = spend_pattern_judge(one_sentence)

        sentence = ""
        for one_token in tokens:
            sentence = sentence + " " + one_token["originalText"]
        if verb_extract(one_sentence,spend_num = spend_num) is None:
            return None
        print("spend_success")
        json_dic["sentence"] = sentence
        json_dic["verb"],verb_num = verb_extract(one_sentence,spend_num = spend_num)
        json_dic["label"] = label_extract(one_sentence,spend_num = spend_num)
        json_dic["subject"],subj_num = subj_extract(one_sentence,spend_num)
        json_dic["object"],obj_num,json_dic["prepositions"] = obj_extract(one_sentence,verb_num)
        json_dic["mod_subj"] = mod_subj_extract(one_sentence,subj_num)
        json_dic["mod_obj"] = mod_obj_extract(one_sentence,obj_num)
        json_dic["mod_verb"] = mod_verb_extract(one_sentence,verb_num)
        json_dic["pattern"] = pattern_select(one_sentence,spend_num,json_dic["prepositions"])
        check_coref(json_dic["subject"],sentence_num,corefs,tokens)
        check_coref(json_dic["object"],sentence_num,corefs,tokens)
        return json_dic
    else:
        return None

def main():
    result = []
    # path = 'F://Verbduration//parsed_sentences'
    path = args.text_folder
    files = os.listdir(path)
    i = 0
    # file_name = "F://Verbduration//parsed_sentences//enwiki-20181001-corpus.parsed.1080000-1085000.json"
    # file_list = extract(file_name)
    for file in files:
        file_name = str(path + '//' + file)
        print('start extract file:{}'.format(file_name))
        file_list = spend_extract(file_name)
        result.extend(file_list)


    # save_file_name = "F://Verbduration//extract_quality//spend_extract_0.json"
    json.dump({"result_list":result}, io.open(args.save_file, "w", encoding='utf-8'))


if __name__ == '__main__':
    main()