import json
import io
import os
import argparse


from utlis import dependency_search,mod_obj_extract,mod_subj_extract,mod_verb_extract,list_dict_duplicate_removal,check_coref

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

def take_pattern_judge(sentence_annotator):
    '''
    Choose the take pattern from the four patterns below
    return the location of take
    
    '''
    dependency_plus = sentence_annotator["enhancedDependencies"]
    for one_dependency in dependency_plus:
        if one_dependency["dep"].find('dobj') > -1 or one_dependency["dep"].find('nmod') > -1:
            num_1 = one_dependency["governor"] 
            num_2 = one_dependency["dependent"] 
            token_1 = sentence_annotator["tokens"][num_1-1]
            token_2 = sentence_annotator["tokens"][num_2-1]
            if token_1["lemma"] == 'take' and token_2["ner"] == 'DURATION':
                if dependency_search('advcl:to',num_1,dependency_plus,1):
                    num = dependency_search('advcl:to',num_1,dependency_plus,1)[0]["dependent"]
                    if sentence_annotator["tokens"][num - 1]["pos"].startswith("VB"):
                        PT = 1
                        return num_1,PT
                if dependency_search('xcomp',num_1,dependency_plus,1): 
                    num = dependency_search('xcomp',num_1,dependency_plus,1)[0]["dependent"]
                    if sentence_annotator["tokens"][num - 1]["pos"].startswith("VB"):
                        PT = 1
                        return num_1,PT
                if dependency_search('csubj',num_1,dependency_plus,1):
                    num = dependency_search('csubj',num_1,dependency_plus,1)[0]["dependent"]
                    if sentence_annotator["tokens"][num - 1]["pos"] == 'VBG':
                        if dependency_search('dobj',num_1,dependency_plus,1):
                            PT = 2
                            return num_1,PT

    return None

def label_extract(sentence_annotator,origin_take_num):

    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]
    label_list = []
    dependency_list = []
    element = {}

    for one_dependency in dependency_plus:
        if one_dependency["dep"] == 'dobj' and one_dependency["governor"] == origin_take_num:
            num  = one_dependency["dependent"]
            if tokens[num-1]["ner"] == "DURATION":
                dependency_list.append(one_dependency)
        if one_dependency["dep"].startswith("nmod") and one_dependency["governor"] == origin_take_num:
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
        #     num2 = 0
        #     for item in mod:
        #         if duration.find(item["dependentGloss"]) == -1:
        #             if dependency_search('cc', item["dependent"], dependency_plus, 1):
        #                 duration = item["dependentGloss"] + " " + dependency_search('cc', item["dependent"], dependency_plus, 1)[0]["dependentGloss"] + " " + duration
        #             else:
        #                 duration = item["dependentGloss"] + " " + duration
        #             num2 += 1
        # element["element"] = duration
        # element["startIndex"] = num if flag == 0 else num - len(duration.split(' ')) + 1
        # element["endIndex"] = element["startIndex"] + len(duration.split(' '))
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

        label_list.append(element)
    label_list = list_dict_duplicate_removal(label_list)
    return label_list



def verb_extract(sentence_annotator,origin_take_num,PT):
    '''
    extract the verb in take pattern
    '''
    special_list = ['complete','finish']
    pronoun_list = ['them','it']


    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]
    element = {}
    if PT == 1:
        verb_num = dependency_search('advcl:to',origin_take_num,dependency_plus,1)[0]["dependent"] if dependency_search('advcl:to',origin_take_num,dependency_plus,1) else dependency_search('xcomp',origin_take_num,dependency_plus,1)[0]["dependent"]
        if dependency_search('xcomp',verb_num,dependency_plus,1):
            verb_num = dependency_search('xcomp',verb_num,dependency_plus,1)[0]["dependent"]

        if dependency_search('compound:prt',verb_num,dependency_plus,1) is not None:
            verb = tokens[verb_num-1]["lemma"] + ' ' + tokens[dependency_search('compound:prt',verb_num,dependency_plus,1)[0]["dependent"]-1]["lemma"]
        else:
            verb = tokens[verb_num-1]["lemma"]

        flag_5 = 0
        if verb in special_list and dependency_search('dobj',verb_num,dependency_plus,1):
            for dependency in dependency_search('dobj',verb_num,dependency_plus,1):
                if dependency["dependentGloss"] in pronoun_list:
                    flag_5 = 1
        verb_num_new = None
        if flag_5 == 1 and dependency_search('conj:and',origin_take_num,dependency_plus,2):
            verb_num_new = dependency_search('conj:and',origin_take_num,dependency_plus,2)[0]["governor"]
            if dependency_search('xcomp',verb_num_new,dependency_plus,1):
                verb_num_new = dependency_search('xcomp',verb_num_new,dependency_plus,1)[0]["dependent"]
        if verb_num_new is not None:
            verb = tokens[verb_num_new - 1]["lemma"]
            verb_num = verb_num_new


        if verb in special_list and dependency_search('acl:relcl',origin_take_num,dependency_plus,2):
            obj_num = dependency_search('acl:relcl',origin_take_num,dependency_plus,2)[0]["governor"]

            if dependency_search('dobj',obj_num,dependency_plus,2):

                verb_num = dependency_search('dobj',obj_num,dependency_plus,2)[0]["governor"]
                verb = tokens[verb_num-1]["lemma"]
            else:
                return None
    elif PT == 2:
        verb_num = dependency_search('csubj',origin_take_num,dependency_plus,1)[0]["dependent"]
        verb = tokens[verb_num - 1]["originalText"]
        if dependency_search('compound:prt',verb_num,dependency_plus,1) is not None:
            verb = tokens[verb_num-1]["lemma"] + ' ' + tokens[dependency_search('compound:prt',verb_num,dependency_plus,1)[0]["dependent"]-1]["lemma"]
        else:
            verb = tokens[verb_num-1]["lemma"]
    element["element"] = verb
    element["startIndex"] = verb_num
    element["endIndex"] = verb_num + len(verb.split(' '))
    return element,verb_num



def subj_extract(sentence_annotator,verb_num,origin_take_num,PT):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]
    subject = None
    pattern = None
    subject_num = None
    startIndex = None
    if PT == 1:
        flag = 0
        if dependency_search('xcomp',verb_num,dependency_plus,2):
            num3 = dependency_search('xcomp',verb_num,dependency_plus,2)[0]["governor"]
            if tokens[num3 -1]["lemma"] != 'take' and dependency_search('nsubj',num3,dependency_plus,1):
                flag = 1

        if dependency_search('nsubj',verb_num,dependency_plus,1) or flag == 1:
            num = dependency_search('nsubj',verb_num,dependency_plus,1)[0]["dependent"] if flag == 0 else dependency_search('nsubj',num3,dependency_plus,1)[0]["dependent"]
            if tokens[num-1]["pos"].startswith("NN"):
                subject = tokens[num-1]["originalText"]
                subject_num  = num
                if dependency_search('advcl:to',origin_take_num,dependency_plus,1):
                    nums = dependency_search('advcl:to',origin_take_num,dependency_plus,1)[0]["dependent"]
                elif dependency_search('xcomp',origin_take_num,dependency_plus,1):
                    nums = dependency_search('xcomp',origin_take_num,dependency_plus,1)[0]["dependent"]
                if nums:
                    if tokens[nums-1]["originalText"] in ['complete','finish']:
                    
                        if tokens[nums] in ['it']:
                            pattern = 'PT1d'
                        else:
                            pattern = 'PT1f'
                    elif dependency_search('mark',verb_num,dependency_plus,1):
                        for dependency in dependency_search('mark',verb_num,dependency_plus,1):
                            if tokens[dependency["dependent"] - 1]["lemma"] == 'for':
                                pattern = 'PT1b'

        if subject is None:
            if dependency_search('nsubj',origin_take_num,dependency_plus,1):
                num = dependency_search('nsubj',origin_take_num,dependency_plus,1)[0]["dependent"]
                if tokens[num-1]["pos"].startswith('NN'):
                    dependency_list = []
                    for dependency in dependency_plus:
                        if dependency["dependentGloss"] == tokens[num-1]["originalText"]:
                            if dependency["dep"] == 'dobj' or (dependency["dep"].find('nmod') >= 0):
                                dependency_list.append(dependency)
                    if len(dependency_list) > 0:
                        pattern = 'PT1e'
                        for dependency in dependency_list:
                            new_num = dependency["governor"]
                            if dependency_search('nsubj',new_num,dependency_plus,1) or dependency_search('nsubjpass',new_num,dependency_plus,1):
                                subject_num = dependency_search('nsubj',new_num,dependency_plus,1)[0]["dependent"] if dependency_search('nsubj',new_num,dependency_plus,1) else dependency_search('nsubjpass',new_num,dependency_plus,1)[0]["dependent"]
                                subject = tokens[subject_num-1]["originalText"]
                                
                    else:
                        subject = tokens[num-1]["originalText"]
                        subject_num = num
                        pattern = 'PT1'

                elif not tokens[num-1]["pos"].startswith('NN') and not tokens[num-1]["pos"] == 'JJ':
                    if dependency_search('conj:and',origin_take_num,dependency_plus,2) and  not tokens[dependency_search('conj:and',origin_take_num,dependency_plus,2)[0]["governor"]-1]["pos"].startswith('NN'):
                        pattern = 'PT1c'
                    else:

                        pattern = 'PT1a'
                    if dependency_search('iobj',origin_take_num,dependency_plus,1):
                        number  = dependency_search('iobj',origin_take_num,dependency_plus,1)[0]["dependent"]
                        if (tokens[number-1]["pos"] == 'PRP' or tokens[number-1]["pos"].startswith('NN')) and tokens[number-1]["ner"] != 'DURATION':
                            subject_num = number
                            subject = tokens[subject_num-1]["originalText"]
                    elif dependency_search('dobj',origin_take_num,dependency_plus,1):
                        number = dependency_search('dobj',origin_take_num,dependency_plus,1)[0]["dependent"]
                        if (tokens[number-1]["pos"] == 'PRP' or tokens[number-1]["pos"].startswith('NN')) and tokens[number-1]["ner"] != 'DURATION':
                            subject_num = number
                            subject = tokens[subject_num-1]["originalText"]

            elif not dependency_search('nsubj',origin_take_num,dependency_plus,1) or subject_num is None:
                if pattern is None and (dependency_search('advcl:to',origin_take_num,dependency_plus,1) or dependency_search('xcomp',origin_take_num,dependency_plus,1)):
                    pattern = 'PT1'
                for i in range(1,len(tokens)+1):
                    for dependency in dependency_plus:
                        if dependency["dependent"] == i and dependency["dep"].startswith('nsubj'):
                            if tokens[i-1]["pos"].startswith("NN"):
                                subject = tokens[i-1]["originalText"]
                                subject_num = i
                                break
        if dependency_search('compound',subject_num,dependency_plus,1):
            dependencies = dependency_search('compound',subject_num,dependency_plus,1)
            dependencies = sorted(dependencies,key=lambda dependency: dependency.__getitem__("dependent"),reverse=True)
            startIndex = dependencies[-1]["dependent"]
            
            for dependency in dependencies:
                subject = dependency["dependentGloss"] + " " + subject
    if PT == 2:
        pattern = 'PT2'
    if subject_num is None:
        return subject,subject_num,pattern
    else:
        element = {}
        element["element"] = subject
        element['startIndex'] = startIndex if startIndex else subject_num
        element['endIndex'] = subject_num + 1
        return element,subject_num,pattern


def obj_extract(sentence_annotator,verb_num):
    dependency_plus = sentence_annotator["enhancedDependencies"]
    tokens = sentence_annotator["tokens"]
    obj = None
    prepositions = None
    obj_num = None
    startIndex = None
    if dependency_search('dobj',verb_num,dependency_plus,1):
        obj_num = dependency_search('dobj',verb_num,dependency_plus,1)[0]["dependent"]
        obj = tokens[obj_num-1]["originalText"]
        if dependency_search('compound',obj_num,dependency_plus,1):
            dependencies = dependency_search('compound',obj_num,dependency_plus,1)
            dependencies = sorted(dependencies,key=lambda dependency: dependency["dependent"],reverse=True)
            startIndex = dependencies[-1]["dependent"]
            for dependency in dependencies:
                obj = dependency["dependentGloss"] + " " + obj

    else:
        for one_dependency in dependency_plus:
            if one_dependency["dep"].startswith("nmod") and one_dependency["governor"] == verb_num:
                obj_num = one_dependency["dependent"]
                obj = one_dependency["dependentGloss"]
                if dependency_search('compound',obj_num,dependency_plus,1):
                    dependencies = dependency_search('compound',obj_num,dependency_plus,1)
                    dependencies = sorted(dependencies,key=lambda dependency: dependency["dependent"],reverse=True)
                    startIndex = dependencies[-1]["dependent"]
                    for dependency in dependencies:
                        obj = dependency["dependentGloss"] + " " + obj
                if dependency_search('case',obj_num,dependency_plus,1):
                    element_p = {}
                    prepositions = dependency_search('case',obj_num,dependency_plus,1)[0]["dependentGloss"]
                    element_p["element"] = prepositions
                    element_p["startIndex"] = dependency_search('case',obj_num,dependency_plus,1)[0]["dependent"]
                    element_p["endIndex"] = element_p["startIndex"] + 1
    if obj is None:
        return obj,obj_num,prepositions
    else:
        element = {}
        element["element"] = obj
        element["startIndex"] = startIndex if startIndex else obj_num
        element["endIndex"] = obj_num + 1
        if prepositions is None:
            return element,obj_num,prepositions
        else:
            return element,obj_num,element_p






def take_extract(file_name):
    i = 0
    json_list = []
    annotator = jsonfile_read(file_name)
    while i < len(annotator):
        corefs = annotator[i]["corefs"]
        sentence_num = 1

        for one_sentence in annotator[i]["sentences"]:
            tokens = one_sentence["tokens"]

            json_dic = {}
            if take_pattern_judge(one_sentence) is not None:
                num,PT = take_pattern_judge(one_sentence)

                sentence = ""
                for one_token in one_sentence["tokens"]:
                    sentence = sentence + " " + one_token["originalText"]
                
                json_dic["sentence"] = sentence
                if verb_extract(one_sentence,origin_take_num = num,PT=PT) is None:
                    break
                print('success')
                json_dic["verb"],verb_num = verb_extract(one_sentence,origin_take_num = num,PT=PT)
                json_dic["label"]= label_extract(one_sentence,origin_take_num = num)
                json_dic["subject"],subj_num,json_dic["pattern"] = subj_extract(one_sentence,verb_num,num,PT=PT)
                json_dic["object"],obj_num,json_dic["prepositions"] = obj_extract(one_sentence,verb_num)
                json_dic["mod_subj"] = mod_subj_extract(one_sentence,subj_num)
                json_dic["mod_verb"] = mod_verb_extract(one_sentence,verb_num)
                json_dic["mod_obj"] = mod_obj_extract(one_sentence,obj_num)
                check_coref(json_dic["subject"],sentence_num,corefs,tokens)
                check_coref(json_dic["object"],sentence_num,corefs,tokens)

                if json_dic not in json_list:
                    json_list.append(json_dic)
            sentence_num += 1
        i += 1
    return json_list

def iter_take_extract(one_sentence, sentence_num, corefs):
    json_dic = {}
    tokens = one_sentence["tokens"]
    if take_pattern_judge(one_sentence) is not None:
        num,PT = take_pattern_judge(one_sentence)

        sentence = ""
        for one_token in one_sentence["tokens"]:
            sentence = sentence + " " + one_token["originalText"]
        
        json_dic["sentence"] = sentence
        if verb_extract(one_sentence,origin_take_num = num,PT=PT) is None:
            return None
        print('take_success')
        json_dic["verb"],verb_num = verb_extract(one_sentence,origin_take_num = num,PT=PT)
        json_dic["label"]= label_extract(one_sentence,origin_take_num = num)
        json_dic["subject"],subj_num,json_dic["pattern"] = subj_extract(one_sentence,verb_num,num,PT=PT)
        json_dic["object"],obj_num,json_dic["prepositions"] = obj_extract(one_sentence,verb_num)
        json_dic["mod_subj"] = mod_subj_extract(one_sentence,subj_num)
        json_dic["mod_verb"] = mod_verb_extract(one_sentence,verb_num)
        json_dic["mod_obj"] = mod_obj_extract(one_sentence,obj_num)
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
        file_list = take_extract(file_name)
        result.extend(file_list)



    # save_file_name = "F://Verbduration//extract_quality//take_extract_0.json"
    json.dump({"result_list":result}, io.open(args.save_file, "w", encoding='utf-8'))


if __name__ == '__main__':
    main()