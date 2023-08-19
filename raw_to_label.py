import json,argparse
import re,io

# parser = argparse.ArgumentParser(description='Some parameters.')
# #parser.add_argument('--folder-path', metavar='N', type=str, nargs='+', help='an integer for the accumulator')
# parser.add_argument('--read-file-path', type=str, help='path to the files to be parsed')
# parser.add_argument('--save-file-path', type=str, help='path to save the result')

# args = parser.parse_args()


several_list = ['several', 'several', 'only', 'mere', 'a few', 'final', 'remaining']

blacklist = ["Charteris spent 55 years - 1928 to 1983 - as either writer of or custodian of Simon Templar 's literary adventures , one of the longest uninterrupted spans of a single author in the history of mystery fiction , equalling that of Agatha Christie , who wrote her novels and stories featuring the detective Hercule Poirot over a similar 55-year period.Personal life and death"]

def label_extract(json_content):
    labels = []
    for one in json_content["result_list"]:
        labels.append(one["label"][0]["element"])
    return labels




def text2int(textnum, numwords={}):
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)


    current = result = 0
    for word in textnum.split():

        if word not in numwords:
          raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current

def num_to_continuous(num_list):
    if len(num_list) > 1:
        num_list = sorted(num_list)
        for i in range(0, num_list[-1] - num_list[0]):
            if num_list[0]+i not in num_list:
                num_list.append(num_list[0]+i)
    num_list = sorted(num_list)
    return num_list

def unit_extract(label):
    unit_list = []
    label = label.split()
    for unit in duration_units:
        for idx, word in enumerate(label):
            if unit in word.lower():
                unit_list.append((unit, idx))

    if len(unit_list) > 1:
        return (None, None)
    # else:
    #     return unit_list[0]
    elif len(unit_list) == 1:
        return unit_list[-1]
    elif len(unit_list) == 0:
        return (None, None)

        
def frac_to_float(str1):
    str_list = str1.split('/')
    return float(str_list[0])/(float(str_list[1]))

def number_extract(label):
    pattern1 = re.compile(r"\d+\/?\.?\d*")
    label = label.replace(',', '')
    label = label.replace('-', ' ')
    duration = []
    num = []
    unit = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen","twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion", "trillion"]
    scales = ["ten", "hundred", "thousand", "million", "billion", "trillion"]
    scales2 = ["hundred", "thousand", "million", "billion", "trillion"]

    if re.findall(pattern1, label):
        for item in re.findall(pattern1, label):
            if '/' in item:
                num.append(frac_to_float(item))
            else:
                num.append(float(item))
        return num
    else:
        label_list = label.split()
        i = 0
        while i < len(label_list):
            if label_list[i][:-1] in scales:
                duration.append('five' + ' ' + label_list[i][:-1])
                
            
            if label_list[i] in unit:
                element = None
                while i < len(label_list) and label_list[i] in unit:
                    element = element + " " + label_list[i] if element is not None else label_list[i]
                    i += 1
                if element in scales2:
                    element = 'one' + ' ' + element
                duration.append(element)
                break
            else:
                i += 1
            
        if len(duration) > 0:
            for textnum in duration:
                textnum = text2int(textnum)
                num.append(textnum)
            return num
        if len(duration) == 0:
            return None


def second_classify(label, idx):
    second_label = ["1 Second", "Several Seconds", "30 Seconds", "Many Seconds"]
    nums = []
    num_list = number_extract(label)

    if (label.split()[idx].lower() == 'second' and 'half' not in label) or 'millisecond' in label.split()[idx].lower():

        index = 0
        nums.append(index)
    elif label.split()[idx].lower() == 'seconds' and 'half' in label:
        index = 1
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        if num_list is None:
            if 'many' in label:
                index = 3
            else:
                index = 1
            nums.append(index)
        else:
            for num in num_list:
                if num < 30:
                    index = 1
                elif num == 30:
                    index = 2
                elif num > 30 and num < 60:
                    index = 3
                else:
                    if num/60 == 1:
                        index = 4
                    elif num/60 < 30:
                        index = 5
                if index not in nums:
                    nums.append(index)
    if 'more than' in label or 'more' in label:
        for i in range(len(nums)):
            if nums[i] == 0 or nums[i] == 2 or nums[i] == 4:
                nums[i] += 1

    elif 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 2 or nums[i] == 4:
                nums[i] -= 1
    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 0 or nums[i] == 2 or nums[i] == 4:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 2 or nums[i] == 4:
                nums.append(nums[i]-1)
        nums = list(set(nums))
                
    nums = num_to_continuous(nums)

    duration = [label_[i] for i in nums]
    return duration


def minute_classify(label, idx):
    minute_label = ["1 Minute", "Several Minute", "30 Minutes", "Many minutes"]
    nums = []
    num_list = number_extract(label)
    if 'quarter' in label.split()[idx]:
        num_list = number_extract(label)

        
        if num_list is None:
                index = 7
                nums.append(index)
        else:
            for num in num_list:
                if num < 2:
                    index = 5
                elif num == 2:
                    index = 6
                elif num > 2:
                    index = 7
                if index not in nums:
                    nums.append(index)
    elif label.split()[idx].lower() == 'minute' and 'half' not in label:

        index = 4
        nums.append(index)
    elif label.split()[idx].lower() == 'minutes' and 'half' in label:
        index = 5
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        if num_list is None:

            if 'many' in label:
                index = 7
            else:
                index = 5
            nums.append(index)
        else:
            for num in num_list:
                if num == 0.5:
                    index = 2
                elif num == 1:
                    index = 4
                elif num < 30 and num > 1:
                    index = 5
                elif num == 30:
                    index = 6
                elif num > 30 and num < 60:
                    index = 7
                else:
                    if num/60 == 1:
                        index = 8
                    elif num/60 > 1 and num/60 < 24:
                        index = 9
                if index not in nums:
                    nums.append(index)

    if 'more than' in label or 'more' in label:
        for i in range(len(nums)):
            if nums[i] == 4 or nums[i] == 6 or nums[i] == 8:
                index += 1
    if 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 4 or nums[i] == 6 or nums[i] == 8:
                nums[i] -= 1

    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 4 or nums[i] == 6 or nums[i] == 8:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 4 or nums[i] == 6 or nums[i] == 8:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)
    duration = [label_[i] for i in nums]
    return duration

def hour_classify(label, idx):
    hour_label = ["1 Hour", "Several Hour", "12 Hours", "Many Hours"]
    nums = []
    num_list = number_extract(label)
    

    if label.split()[idx].lower() == 'hour' and 'half' not in label:

        index = 8
        nums.append(index)
    elif label.split()[idx].lower() == 'hours' and 'half' in label:
        index = 9
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)
        if num_list is None:
            if 'many' in label:
                index = 11
            else:
                index = 9
            nums.append(index)
        else:
            for num in num_list:
                if num == 0.5:
                    index = 6
                if num == 1:
                    index = 8
                if num < 12 and num > 1:
                    index = 9
                if num == 12:
                    index = 10
                if num > 12 and num < 24:
                    index = 11
                else:
                    if num/24 == 1:
                        index = 12
                    elif num/24 > 1 and num/24 <7:
                        index = 13
                    elif num/24 == 7:
                        index = 14
                    elif num/24 > 7 and num/24 < 30:
                        index = 15
                    elif num/24 == 30:
                        index = 16
                    elif num/24 > 30 and num/24 < 180:
                        index = 17
                    elif num/24 > 180 and num/24 < 365:
                        index = 19
                if index not in nums:
                    nums.append(index)

    if 'more than' in label or 'more' in label:
        for i in range(len(nums)):
            if nums[i] == 8 or nums[i] == 10 or nums[i] == 12:
                nums[i] += 1
    if 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 8 or nums[i] == 10 or nums[i] == 12:
                nums[i] -= 1
    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 8 or nums[i] == 10 or nums[i] == 12:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 8 or nums[i] == 10 or nums[i] == 12:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)

    duration = [label_[i] for i in nums]
    return duration

def day_classify(label, idx):
    day_label = ["1 Day", "Several Days"]
    nums = []
    num_list = number_extract(label)
    if label.split()[idx].lower() == 'day' and 'half' not in label:

        index = 12
        nums.append(index)
    elif label.split()[idx].lower() == 'days' and 'half' in label:
        index = 13
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        
        if num_list is None:

            if 'many' in label:
                index = 15
            else:
                index = 13
            nums.append(index)
        else:
            for num in num_list:
                if num == 1:
                    index = 12
                if num == 0.5:
                    index = 10
                if num > 1 and num < 7:
                    index = 13
                else:
                    if num/7 == 1:
                        index = 14
                    elif num > 7 and num < 30:
                        index = 15
                    elif num == 30:
                        index = 16
                    elif num/30 > 1 and num/30 < 6:
                        index = 17
                    elif num/30 == 6:
                        index = 18
                    elif num/30 > 6 and num/30 < 12:
                        index = 19
                    elif num/365 == 1:
                        index = 20
                    elif num/365 > 1 and num/365 < 10:
                        index = 21
                    elif num/365 == 10:
                        index = 22
                    elif num/365 > 10:
                        index = 23
                if index not in nums:
                    nums.append(index)
    if 'more than' in label or 'more' in label:
         for i in range(len(nums)):
            if nums[i] == 12 or nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums[i] += 1
    if 'less than' in label:
         for i in range(len(nums)):
            if nums[i] == 12 or nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums[i] -= 1
    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 12 or nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 12 or nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)
    duration = [label_[i] for i in nums]
    return duration


def week_classify(label, idx):
    week_label = ["1 week", "Several Weeks"]
    nums = []
    num_list = number_extract(label)
    if label.split()[idx].lower() == 'week' and 'half' not in label:

        index = 14
        nums.append(index)
    elif label.split()[idx].lower() == 'weeks' and 'half' in label:
        index = 15
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        
        if num_list is None:

            if 'many' in label:
                index = 17
            else:
                index = 15
            nums.append(index)
        else:
            for num in num_list:
                if num == 0.5:
                    index = 13
                if num > 1 and num < 4:
                    index = 15
                else:
                    if num/4 == 1:
                        index = 16
                    elif num/4 > 1 and num/4 < 6:
                        index = 17
                    elif num/4 == 6:
                        index = 18
                    elif num/4 > 6 and num/4 < 13:
                        index = 19
                    elif num/4 == 13:
                        index = 20
                    elif num/4 > 12:
                        index = 21
                if index not in nums:
                    nums.append(index)
    if 'more than' in label or ('more' in label and 'more or' not in label):
        for i in range(len(nums)):
            if nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums[i] += 1
    if 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums[i] -= 1

    elif 'at least' in label or 'more or' in label:
        for i in range(len(nums)):
            if nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 14 or nums[i] == 16 or nums[i] == 18 or nums[i] == 20:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)
    duration = [label_[i] for i in nums]
    return duration

def month_classify(label, idx):
    month_label = ["1 Month", "Several Months", "6 Months", "Many Months"]
    nums = []
    num_list = number_extract(label)
    if label.split()[idx].lower() == 'month' and 'half' not in label:

        index = 16
        nums.append(index)
    elif label.split()[idx].lower() == 'months' and 'half' in label:
        index = 17
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        if num_list is None:

            if 'many' in label:
                index = 19
            else:
                index = 17
            nums.append(index)
        else:
            for num in num_list:
                if num == 0.5:
                    index = 15
                if num > 1 and num < 6:
                    index = 17
                elif num == 6:
                    index = 18
                elif num > 6 and num < 12:
                    index = 19
                else:
                    if num/12 == 1:
                        index = 20
                    elif num/12 > 1 and num/12 < 10:
                        index = 21
                    elif num/12 == 10:
                        index = 22
                if index not in nums:
                    nums.append(index)
    if 'more than' in label or 'more' in label:
        for i in range(len(nums)):
            if nums[i] == 16 or nums[i] == 18 or nums[i] == 20 or nums[i] == 22:
                nums[i] += 1
    if 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 16 or nums[i] == 18 or nums[i] == 20 or nums[i] == 22:
                nums[i] -= 1
    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 16 or nums[i] == 18 or nums[i] == 20 or nums[i] == 22:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 16 or nums[i] == 18 or nums[i] == 20 or nums[i] == 22:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)
    duration = [label_[i] for i in nums]
    return duration

def year_classify(label, idx):
    year_label = ["1 Year", "Several Years"]
    nums = []
    num_list = number_extract(label)
    if label.split()[idx].lower() == 'year' and 'half' not in label:

        index = 20
        nums.append(index)
    elif label.split()[idx].lower() == 'years' and 'half' in label:
        index = 21
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        
        if num_list is None:
            index = 21
            nums.append(index)
        else:
            for num in num_list:
                if num == 1:
                    index = 20
                if num == 0.5:
                    index = 18
                if num > 1 and num < 10:
                    index = 21
                elif num == 10:
                    index = 22
                elif num > 10 and num < 100:
                    index = 23
                elif num == 100:
                    index = 24
                elif num > 100:
                    index = 25
                if index not in nums:
                    nums.append(index)
    if 'more than' in label or 'more' in label:
        for i in range(len(nums)):
            if nums[i] == 20 or nums[i] == 22:
                nums[i] += 1
    if 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 20 or nums[i] == 22:
                nums[i] -= 1
    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 20 or nums[i] == 22:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 20 or nums[i] == 22:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)
    duration = [label_[i] for i in nums]
    return duration

def decade_classify(label ,idx):
    decade_label = ["1 dacade", "Several Decades"]
    nums = []
    num_list = number_extract(label)
    if label.split()[idx].lower() == 'decade' and 'half' not in label:

        index = 22
        nums.append(index)
    elif label.split()[idx].lower() == 'decades' and 'half' in label:
        index = 23
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        if num_list is None:
            index = 23
            nums.append(index)
        else:
            for num in num_list:
                if num > 1 and num < 10:
                    index = 23
                elif num > 10:
                    index = 24
                if index not in nums:
                    nums.append(index)
    if 'more than' in label or 'more' in label:
        for i in range(len(nums)):
            if nums[i] == 22 or nums[i] == 24:
                nums[i] += 1
    if 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 22 or nums[i] == 24:
                nums[i] -= 1
    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 22 or nums[i] == 24:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 22 or nums[i] == 24:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)
    duration = [label_[i] for i in nums]
    return duration

def century_classify(label, idx):
    century_label = ["1 Century", "Centuries"]
    nums = []
    num_list = number_extract(label)
    if label.split()[idx].lower() == 'century' and 'half' not in label:

        index = 24
        nums.append(index)
    elif label.split()[idx] == 'centuries':
        index = 25
        nums.append(index)
    else:
        if label.split()[0] == 'half':    
            label = label.replace('half', '0.5')
        num_list = number_extract(label)

        if num_list is None:
            index = 25
            nums.append(index)

    if 'more than' in label or 'more' in label:
        for i in range(len(nums)):
            if nums[i] == 24:
                nums[i] += 1
    if 'less than' in label:
        for i in range(len(nums)):
            if nums[i] == 24:
                nums[i] -= 1
    elif 'at least' in label:
        for i in range(len(nums)):
            if nums[i] == 24:
                nums.append(nums[i]+1)
        nums = list(set(nums))
    elif 'up to' in label:
        for i in range(len(nums)):
            if nums[i] == 24:
                nums.append(nums[i]-1)
        nums = list(set(nums))
    nums = num_to_continuous(nums)
    duration = [label_[i] for i in nums]
    return duration


duration_units = ["second", "minute", "hour", "day", "week", "month", "year", "decade", "century", "centuries"]

label_ = ["1 Second", "Several Seconds", "30 Seconds", "Many Seconds", "1 Minute", "Several Minutes", "30 Minutes", "Many minutes", "1 Hour", "Several Hours", "12 Hours", "Many Hours", "1 Day", "Several Days", "1 Week", "Several Weeks", "1 Month", "Several Months", "6 Months", "Many Months", "1 Year", "Several Years", "1 Dacade", "Several Decades", "1 Century", "Centuries", "else"]

years_class = ['hundred years', 'thousand years', 'million years', 'billion years', 'millennium']

# def label_convert(label_list):
#     f = open('raw_to_label3.txt', 'w')
#     label_ = ["1 Second", "Several Seconds", "30 Seconds", "Many Seconds", "1 Minute", "Several Minutes", "30 Minutes", "Many minutes", "1 Hour", "Several Hours", "12 Hours", "Many Hours", "1 Day", "Several Days", "1 Week", "Several Weeks", "1 Month", "Several Months", "6 Months", "Many Months", "1 Year", "Several Years", "1 Dacade", "Several Decades", "1 Century", "Centuries", "else"]
#     for label in label_list:
#         label2 = label
#         if label == 'the next couple' or label == '1942-1945':
#             continue

#         for item in years_class:
#             if item in label:
#                 label2 = label.replace(item, 'centuries')

#         # label = "".join(label.split())
#         label = re.sub('\s', ' ', label)
#         label2 = re.sub('\s', ' ', label2)
#         unit, idx = unit_extract(label2)
#         if unit is None:
#             continue

#         if unit == duration_units[0]:
#             index = second_classify(label2, idx)
#         elif unit == duration_units[1]:
#             index = minute_classify(label2, idx)
#         elif unit == duration_units[2]:
#             index = hour_classify(label2, idx)
#         elif unit == duration_units[3]:
#             index = day_classify(label2, idx)
#         elif unit == duration_units[4]:
#             index = week_classify(label2, idx)
#         elif unit == duration_units[5]:
#             index = month_classify(label2, idx)
#         elif unit == duration_units[6]:
#             index = year_classify(label2, idx)
#         elif unit == duration_units[7]:
#             index = decade_classify(label2, idx) 
#         elif unit == duration_units[8] or unit == duration_units[9]:
#             index = century_classify(label2, idx)

#         f.write("%25s\t\t\t %6s\n"%(label, index))
#     f.close()


def json_label_add(json_content):
    result = []
    filtered = []
    # json_content = json.load(open(filename))["result_list"]
    for one in json_content:
        if len(one["label"]) > 1:
            filtered.append(one)
            continue
        if one["sentence"] in blacklist:
            filtered.append(one)
            continue
        label = one["label"][0]["element"]
        label2 = label

        for item in years_class:
            if item in label:
                label2 = label.replace(item, 'centuries')

        label = re.sub('\s', ' ', label)
        label2 = re.sub('\s', ' ', label2)
        unit, idx = unit_extract(label2)
        if unit is None:
            filtered.append(one)
            continue
        if unit == duration_units[0]:
            index = second_classify(label2, idx)
        elif unit == duration_units[1]:
            index = minute_classify(label2, idx)
        elif unit == duration_units[2]:
            index = hour_classify(label2, idx)
        elif unit == duration_units[3]:
            index = day_classify(label2, idx)
        elif unit == duration_units[4]:
            index = week_classify(label2, idx)
        elif unit == duration_units[5]:
            index = month_classify(label2, idx)
        elif unit == duration_units[6]:
            index = year_classify(label2, idx)
        elif unit == duration_units[7]:
            index = decade_classify(label2, idx) 
        elif unit == duration_units[8] or unit == duration_units[9]:
            index = century_classify(label2, idx)
        one["label_class"] = index
        result.append(one)
    return result


def main():
    file = 'F://Verbduration//extract_1.json'
    save_file_name = 'F://Verbduration//extract_final_1.json'
    # save_file_name2 = 'F://Verbduration//extract_filter_0.json'
    # json_content = json.load(open(file))
    # label_list = label_extract(json_content)

    # label_convert(label_list)

    result, filtered = json_label_add(file)
    json.dump({"result_list":result}, io.open(save_file_name, "w", encoding='utf-8'))
    # json.dump({"result_list":filtered}, io.open(save_file_name2, "w", encoding='utf-8'))
    # print(number_extract('year two'))
    # print(week_classify("more or one week", 3))




if __name__ == '__main__':
    main()
