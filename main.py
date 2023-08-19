from spend_extract import iter_spend_extract
from take_extract import iter_take_extract
from raw_to_label import json_label_add
import argparse,io
import os,json
from os.path import join,isfile
from shutil import copyfile

parser = argparse.ArgumentParser(description="parameters")
parser.add_argument("--text-folder", type=str, help="path to the folder to be parsed")
parser.add_argument("--save-file", type=str, help="path to save the result")
args = parser.parse_args()


filename = 'F://Verbduration//parsed_sentences//enwiki-20181001-corpus.parsed.1080000-1085000.json'

result_labeled = 'result_labeled'
result_without_labeled = 'result_without_labeled'

def get_all_files(folder_path):
    onlyfiles = [join(folder_path, f) for f in os.listdir(folder_path) if isfile(join(folder_path, f))]
    return onlyfiles

def jsonfile_read(file_name):
    file=open(str(file_name),encoding='utf-8')
    file_list=json.load(file)
    annotator = file_list["result_list"]
    print(len(annotator))
    return annotator


def extract(file_name):
    i = 0
    spend_list = take_list = []
    result = []
    annotator = jsonfile_read(file_name)
    while i < len(annotator):
        corefs = annotator[i]["corefs"]
        sentence_num = 1
        for one_sentence in annotator[i]["sentences"]:
            tokens = one_sentence["tokens"]
            if iter_spend_extract(one_sentence, sentence_num, corefs) is not None:
                one = iter_spend_extract(one_sentence, sentence_num, corefs)
                if one not in spend_list:
                    spend_list.append(one)
            if iter_take_extract(one_sentence, sentence_num, corefs) is not None:
                one = iter_take_extract(one_sentence, sentence_num, corefs)
                if one not in take_list:
                    take_list.append(one)
            sentence_num += 1
        i += 1
    result = spend_list + take_list
    return result

def main():
    
    result = []
    result_with_label = []
    files = get_all_files(args.text_folder)

    if not os.path.exists(result_labeled):
        os.makedirs(result_labeled)
    if not os.path.exists(result_without_labeled):
        os.makedirs(result_without_labeled)

    for file in files:
        print('start extract file:{}'.format(file))
        #dst = "processed_files" + "/" + file.split("/")[-1]
        #copyfile(file, dst)
        json_list = extract(file)
        result.extend(json_list)
        result_with_label.extend(json_label_add(result))

    #result_label = json_label_add(result)

    json.dump({"result_list":result}, io.open(join(result_without_labeled, args.save_file), "w", encoding='utf-8'))
    #result_label = json_label_add(result)
    #json.dump({"result_list":result_label}, io.open(join(result_labeled, args.save_file), "w", encoding='utf-8'))
    json.dump({"result_list": result_with_label}, io.open(join(result_labeled, args.save_file), "w", encoding='utf-8'))


if __name__ == '__main__':
    main()
