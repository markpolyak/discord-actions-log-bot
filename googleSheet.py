import re
import enum

# Предусловия:
# ФИО - каждая составляющая ФИО начинается с большой буквы, остальные маленькие
# Нет чувствительности к отчеству (в случае, если нет инициалов)
# Допускается форматы записи:
# Фамилия Имя Отчество, Имя Отчество Фамилия, Фамилия И О, И О Фамилия, Фамилия Имя, Имя Фамилия
# Группа может быть встроена в любое место
# ФИО обязательно должно быть русскоязычным
# Допускаются несовпадения по схожестям букв. Главное, чтобы введенная группа совпадала с наименованием таблицы.
# Везде предполагается, что в качестве пробельных знаков используются только пробелы (не табуляции и т.п.)

#Замену английских в именах на русские не производим. т.к. Если кто-то напишет Петров А. В. z 
# - то мы не можем воспринять, что это Петров А. В.
# Алгоритм пытается соотнести содержимое никнейма и результата
  
        
# Класс, определяющий парсинг информации с гугл sheet
class GoogleSheetInfo:
    
    def __init__(self, group, positionInGoogleList, arrayOfPartsFIOs, attendanceArray):
        self.__group = group # example: '4933'
        self.__positionInGoogleList = positionInGoogleList # position in google Sheet - example: [A, 0] or [0, 0]
        self.__arrayOfPartsFIOs = arrayOfPartsFIOs
        self.__attendanceArray = attendanceArray
        
    
    def getGroup(self):
        return self.__group
    
    def getPositionInGoogleList(self):
        return self.__positionInGoogleList
    
    def getArrayOfPartsFIOs(self):
        return self.__arrayOfPartsFIOs
    
    def getArrayOfPartsFIOByIndex(self, index):
        if (index>=0 and index<len(self.__arrayOfPartsFIOs)):
            return self.__arrayOfPartsFIOs[index]
        else:
            return ''
    
    def getAttendanceArray(self):
        return self.__attendanceArray    
        
    def getAttendanceArrayByIndex(self, index):
        return self.__attendanceArray[index]    
    
    def setGroup(self, group):
        self.__group = group
    
    def setPositionInGoogleList(self, positionInGoogleList):
        self.__positionInGoogleList = positionInGoogleList
    
    def setArrayOfPartsFIOs(self, arrayOfPartsFIOs):
        self.__arrayOfPartsFIOs = arrayOfPartsFIOs
    
    def setAttendanceArray(self, attendanceArray):
        self.__attendanceArray = attendanceArray

    def setAttendanceArrayByIndex(self, index, attendanceArrayElement=1):
        if index in range(len(self.__attendanceArray)):
            self.__attendanceArray[index] = attendanceArrayElement
 
# special variants, which is not similar in lower in upper  
exceptionsFromEngToRus=['t', 'b','r']

# defaul variants, which is similar in lower and in upper? or only an upper (for exceptions variants) 
fromEngToRusDefault={'K':'К', 'M':'М', 'E':'Е', 'C':'С', 'X':'Х', 'Y':'У', 'O':'О', 'A':'А', 'T':'Т', 'B':'В', 'P':'Р'}
# Предупреждения
resultErrors=[]
# Ошибки
resultWarnings=[]

# DELETE GROUPS
groups=['в4933', '4933']

googleSheetInfoArray=[]


#DELETE UPPEND
googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Семенов', 'Павел', 'Александрович']], [1, 0]))

googleSheetInfoArray.append(GoogleSheetInfo('4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Коваленко', 'Игорь']], [0, 1]))




# класс перечислений вариантов алгоритма
class variantsOfAlgoritm(enum.Enum):
        withSpace = 1 # приводим к пробелам
        withUpperBegin = 2 # приводим к верхнему регистру начало
        withUpperBeginAndLowerAnother = 3 # приводим к верхнему регистру начало, остальное к нижнему

# we can choose only few of them
dictVariantsOfAlgoritm = {
    0 : [variantsOfAlgoritm.withSpace],
    1 : [variantsOfAlgoritm.withSpace, variantsOfAlgoritm.withUpperBegin],
    2 : [variantsOfAlgoritm.withSpace, variantsOfAlgoritm.withUpperBeginAndLowerAnother],
    3 : [variantsOfAlgoritm.withUpperBegin],
    4 : [variantsOfAlgoritm.withUpperBeginAndLowerAnother]
}       

# State of successful result
class successState(enum.Enum):
    SuccessfulCompare = 1
  
# State of warning result  
class warningState(enum.Enum):
    CompareButNotEqual = 1 # мало информации, но уникален - Петров А или Петров, Петров А В, или Петров Андр
    # корректный вариант - Петров Андрей, Петров Андрей Владимирович
    AlreadySetAttendance = 2 # уже стоит не 0 в google sheet

# State of error result  
class errorState(enum.Enum):
    UnknownGroup = 1 # не удалось извлечь группу
    NotExist = 3 # не нашли совпадения
    NotUnique = 4 # не уникален в группе
    NotUniqueByGroup = 2 # при парсинге нашлось несколько групп, в которые можно проставить посещаемость

# преобразует массив вида [group, [arrfio, arrfio]] в строку вида "'group': 'f i o' 'f i o'; "
def getStringForErrorsAndWarnings(info):
    groupFIO=info[0]
    FIOs=info[1]
    # set group
    result = "'" + info[0]+ "'" + ": "
    # для каждого arrfio
    for index in range(len(FIOs)):
        if (index!=0):
            result+=' '
        result+="'"+' '.join(FIOs[index])+"'"
    result+=';'
    return result

# Получить предупреждение или ошибку        
def getErrorOrWarning(enumValue, nick, info=[]):
    nick=str(nick)
# info =[[group, [arrfio, arrfio]]...] - NotUniqueByGroup
# info =[group, [arrfio, arrfio]] - errorState.NotUnique
# info =[group, [arrfio]] - warningState.CompareButNotEqual
    if (enumValue == errorState.UnknownGroup):
        return "Error: '" + nick + "' have wrong group or group doesn't exists in google sheet"
    elif (enumValue ==  enumValue == errorState.NotUniqueByGroup):
        result = "Error: '" + nick + "' have more than one coincidence in different groups - "
        for indexGroupFIO in range(len(info)):
            result+= " in group " +  getStringForErrorsAndWarnings(info[indexGroupFIO])
        return result
    elif (enumValue == errorState.NotExist):
        return "Error: '" + nick + "' not Exist in google sheet;"
    elif (enumValue == errorState.NotUnique):
        return "Error: '" + nick + "' not unique in google sheet - in group " + getStringForErrorsAndWarnings(info)       
    elif (enumValue == warningState.CompareButNotEqual):
        return "Warning: nick '" + nick + "' is short, but we find an unique - in group " + getStringForErrorsAndWarnings(info)
    elif (enumValue == warningState.AlreadySetAttendance):
        return "Warning: for nick '" + nick + "' attendance has been already set - in group " + getStringForErrorsAndWarnings(info)
    else:
        return ''


# привести к пробелам знаки
def turnToSpacesSigns(stroka):
    return re.sub(r'[^a-zA-Zа-яА-Я]', " ",  stroka)
    
# удаляем все, кроме букв, чисел
def delSigns(stroka):
    return re.sub(r'[^a-zA-Zа-яА-Я0-9]', "",  stroka)


# заменяем все на русские буквы и пробелы
# Петров А.В. -> ПетровАВ
def turnToSpacesAllWthoutName(stroka):
    return re.sub(r'[^а-яА-Я\s]', " ",  stroka)

# оставляем только буквы русского алфавита
def delAllWthoutName(stroka):
    return re.sub(r'[^а-яА-Я]', "",  stroka)    

# получить индекс первого числа в строке
def getIndexFirstDigit(stroka, startPosition = 0):
    # если начальная позиция находится за границами
    if (startPosition>=len(stroka) or startPosition<0):
        return -1
    for index in range(startPosition, len(stroka)):
        if (stroka[index].isdigit()):
            return index
    # иначе нет нет чисел - возвращаем -1
    return -1



# приводим к нижнему регистру и к английскому алфавиту подобные
def toGroupStandartSymb(symbGroup):
    if symbGroup in exceptionsFromEngToRus:
       return symbGroup.upper()
    
    # to Up register   
    symbGroup = symbGroup.upper()
    if symbGroup in fromEngToRusDefault:
        return fromEngToRusDefault[symbGroup]
    else:
        return symbGroup
    
# сравниваем формат символов и их значения - для всех символов группы
def compareFormatSymb(group, groupNick):
    # если размеры не равны
    if (len(group)!=len(groupNick)):
        return False
        
    # для каждого элемента производим проверку
    for index in range(len(group)):
        if (group[index].isdigit()):
            if (group[index]!=groupNick[index]):
                return False
        else:
            # здесь нужна более жестка функция проверки
            if (toGroupStandartSymb(group[index])!=toGroupStandartSymb(groupNick[index])):
                return False
    # если дошли до сюда, то они равны по признаку значений
    return True
    
    
    
# все символы начала приводим к верхнему регистру (т.е. после пробелов)
# позволяет решить проблему петров андрейВладимирович-> Петров АндрейВладимирович, а далее парсинг по большим буквам
def beginOfWordToUpRegister(stroka, toLower=False):
    # убираем крайние пробелы
    stroka=stroka.strip()
    if (len(stroka)<1):
        return ''
    parseStroka=''
    isSpace = True
    for index in range(len(stroka)):
        # если пробел
        if (stroka[index]==' '):
            isSpace=True
            parseStroka+=stroka[index]
        # если есть тригер на увлеичение
        elif (isSpace==True):
                parseStroka+=stroka[index].upper()
                isSpace=False
        elif (toLower==True):
            parseStroka+=stroka[index].lower()
        else:
            parseStroka+=stroka[index]
    # возвращаем результат парсинга
    return parseStroka

    
# получаем составные части    
def parseNameToParts(stroka):
    # убираем все символы, кроме ФИО (пробелы также удаляются)
    stroka=delAllWthoutName(stroka)
    # парсим и получаем части ФИО
    parseArr=[stroka[0].upper()]
    currentName=0
    for index in range(1, len(stroka)):
        # если в верхнем регистре
        if (stroka[index].upper()==stroka[index]):
            #добавляем в конец
            parseArr.append(stroka[index])
            # текущий индекс - следующий
            currentName+=1
        else:
            #добавляем в конец текущего - нет смысла в lower
            parseArr[currentName]+=stroka[index]
    return parseArr
    
# получить массив нумерации массива по индексам без пробелов относительно начального     
def getIndicesNickWithoutSignes(nick):
    resultArr=[]
    for index in range(len(nick)):
        if (delSigns(nick[index])!=''):
            resultArr.append(index)
    return resultArr
    
        
    
# получить группу из имени          
# на вход - получаем стандартную группу, nick и nick без спец. символов, массив соответствия индексов последних двух
def getNickWthoutGroupFromNick(group, nick, parseNick, indices):  
    # получаем индекс начала для группы - группа обязательно должна содержать числа, иначе может возникнуть очень много неточностей парсинга
    startDigitGroup=getIndexFirstDigit(group)
    if (startDigitGroup<0):
        return errorState.UnknownGroup
    
    # для никнейма получаем индекс начала числа
    startDigitNick=getIndexFirstDigit(parseNick)
    
    # пока не конец
    while (startDigitNick>=0 and startDigitNick<len(parseNick)):
        # левая граница группы в нике
        leftBorder=startDigitNick-startDigitGroup
        # правая граница группы в нике
        rightBorder=leftBorder+len(group)-1
        
        # если в никнейме не помещется искомая группа слева
        if  (leftBorder<0 or
                # если в никнейме не помещется искомая группа справа
                rightBorder>=len(parseNick)):
            # то пытаемся пойти дальше - сдвигаемся на величину до начала группы
            startDigitNick=getIndexFirstDigit(parseNick, startDigitNick+startDigitGroup+1)
        # если группа равна
        else:
            # извлекаем группу срезом строки для никнейма
            parseGroup = parseNick[leftBorder:rightBorder+1]
            # если группы равны
            if (compareFormatSymb(group, parseGroup)):
                # находим соответствие левой границы для стандартного ника
                leftBorder=indices[leftBorder]
                # находим соответствие правой границы для стандартного ника
                rightBorder=indices[rightBorder]
                # возвращаем срез никнейма без группы:
                # срез не чувствителен к превышению лимита - возвращает пустоту
                return nick[:leftBorder]+' '+ nick[rightBorder+1:]
            else:
                # иначе пытаемся пойти дальше - сдвигаемся на величину до начала группы
                startDigitNick=getIndexFirstDigit(parseNick, startDigitNick+startDigitGroup+1)
    
    # если мы здесь, значит не нашли совпадение для группы
    return errorState.UnknownGroup

# получаем группу, которая соответствует и строку, которая записана в качестве группы в нике
# [исходная группа, ник] or errorState.UnknownGroup
def getGroupAndNickWthoutGroup(group, nick):
    # получаем массив для случая удаления всех знаков nick
    indices=getIndicesNickWithoutSignes(nick)
    # получаем никнейм без спец. символов и пробелов
    parseNick = delSigns(nick)
    # пытаемся сопоставить группу с ником
    nickWthoutGroup=getNickWthoutGroupFromNick(group, nick,  parseNick, indices)
    # если группу получили (она равна искомой)
    if (nickWthoutGroup!=errorState.UnknownGroup):
        return [group, nickWthoutGroup]
    # если мы не нашли группу
    return errorState.UnknownGroup

# TO DO: можно также перед всеми действиями (но группа должна быть удалена) если начало дальше идет русская буква,
#, то мы приводим её к верхнему регистру



# сопоставляем ФИО и полученные фрагменты никнейма
# принимаем FIO и Nick в формате массивов
def compareFIOandNick(FIOArr, nickArr, isEqual=False):
    # создаем массив заполненный нулями - нальчальное значение эквиваленты сравнения
    compareResult = [[0] * len(nickArr) for i in range(len(FIOArr))]
    for indexFIO in range(len(FIOArr)):
        for indexNick in range(len(nickArr)):
            # равно ли FIO строке nick - сравнение в одинаковом регистре (необзательно приведение)
            if (isEqual==True 
                and nickArr[indexNick].lower() == FIOArr[indexFIO].lower()):
                compareResult[indexFIO][indexNick]=1
            # начинается ли FIO со строки nick - сравнение в одинаковом регистре (необзательно приведение)
            elif (isEqual==False
                 and re.match(nickArr[indexNick].lower(), FIOArr[indexFIO].lower())!=None):
                compareResult[indexFIO][indexNick]=1
    # проверяем - существует ли комбинация, при которой возможна идентичность        
    return isExistFioCombination(compareResult)
 
# Случаи корректности Петр Петров, Петров А - недостаточно данных для однозначной идентификации (особые случаи)
def isCorrectFIO():
    return ''
    
    

def isExistFioCombination(compareResult):
    # если в фио всего один элемент - рассматриваем отдельно
    sumResultFIO=[]

    # считаем все суммы по каждому элемнту ФИО
    for indexFIO in range(len(compareResult)):
        sumResultFIO.append(sum(compareResult[indexFIO][i] for i in range(len(compareResult[indexFIO]))))
    
    # никнейм
    sumResultNick=[]
    # считаем все суммы по каждому элементу никнейма  
    for indexNick in range(len(compareResult[0])):
        sumResultNick.append(0)
        for indexFIO in range(len(compareResult)):
            sumResultNick[len(sumResultNick)-1]+=compareResult[indexFIO][indexNick]
    
    cntNonZero=0
    
    if (len(sumResultFIO)<len(sumResultNick)):
        if 0 in sumResultFIO:
            return False
        elif sumResultNick.count(1)<len(sumResultFIO):
            return False
        else:
            return True
    else:
        if 0 in sumResultNick:
            return False
        elif sumResultFIO.count(1)<len(sumResultNick):
            return False
        else:
            return True
   
   
# Функция, которая пытается найти сопоставления путем приведения к Верхнему регистру начальных символов,
# остальных к нижнему регистру, а также путем дальнейшего удаления знаков
def getPartsFormNickAlgoritm(nick, variants):
     # приводим к пробелам все знаки
    if variantsOfAlgoritm.withSpace in variants:
        nick=turnToSpacesSigns(nick)
    # все символы начала приводим к верхнему регистру (т.е. после пробелов), остальные к нижнему
    if variantsOfAlgoritm.withUpperBeginAndLowerAnother in variants:
        nick=beginOfWordToUpRegister(nick, True)   
    # все символы начала приводим к верхнему регистру (т.е. после пробелов), остальные к нижнему
    elif variantsOfAlgoritm.withUpperBegin in variants:
        nick=beginOfWordToUpRegister(nick)  

    # Получаем составные части никнейма
    return parseNameToParts(nick)
   
   
# Функция сопоставления никнейма по массиву фамилий
# Получаем посещаемость для ускорения работы
def compareNickAndFIOs(group, nickArr, FIOs):    
    resultArray=[] # массив результата - записывает индексы ФИО
    isEqual=False # Флаг - было ли равенство
    # Сопостоавляем для каждого ФИО
    for indexFIO in range(len(FIOs)):
         # если никнейм существует по равенству - добавляем в конец рассматриваемого массива
        if (compareFIOandNick(FIOs[indexFIO], nickArr, True)):
            isEqual=True
            resultArray.append(indexFIO)
        # если никнейм существует по вхождению   
        elif (compareFIOandNick(FIOs[indexFIO], nickArr)):
            resultArray.append(indexFIO)
    # рассматриваем различные случаи результата
    # если единственное -> уникально, записываем его
    if (len(resultArray)==1):
        
        # если найден по равенству и размер больше 1
        if (isEqual and len(nickArr)>1):
            # возвращаем успешное выполнение
            return successState.SuccessfulCompare, resultArray
        # иначе недостаточно уникален по данным   
        else:
            return warningState.CompareButNotEqual, resultArray   
        
        # возвращаем ФИО
        return successState.SuccessfulCompare, resultArray
    # если не существует
    elif (len(resultArray)<=0):
        return errorState.NotExist, resultArray
    # если не уникален
    else:
        return errorState.NotUnique, resultArray
 
# вспомогательная функция сравнения двух массивов на равенство (без учета регистров)
def compareArrsWthoutRegister(arr1, arr2):
    # если размеры не равны:
    if (len(arr1)!=len(arr2)):
        return False
    # по каждому элементу
    for index in range(len(arr1)):
        # если элементы не равны
        if (arr1[index].lower()!=arr2[index].lower()):
            return False
    # списки равны
    return True  
    
   
# производит поиск по всем ФИО
# Принимает на вход массив массив групп, массив класса данных, никнейм
# Возвращает результат обработки, массив значений расстановки оценок
# результатом возвращает 
def findFIOfromFIOsToNick(group, nick, FIOs):  
    # получаем группу и никнейм с вырезанной группой
    groupAndNick=getGroupAndNickWthoutGroup(group, nick)
    # если группа неизвестная
    if (groupAndNick == errorState.UnknownGroup):
        return (errorState.UnknownGroup, [])
    
    # извлекаем соответствующую группу
    group=groupAndNick[0]
    
    # извлекаем никнейм без группы из самого массива
    parseNick=groupAndNick[1]

    prevNickArrs=[]
    nickArr=[]
    indexFIOs=[]
    # пробегаемся по всем вариантам словаря
    for variantIndex in range(len(dictVariantsOfAlgoritm)):
        nickArr = getPartsFormNickAlgoritm(parseNick, dictVariantsOfAlgoritm[variantIndex])
        print(nickArr)
        # если количество элементов, полученных из ника слишком большое или слишком малое
        if (len(nickArr)>3 or len(nickArr)<1):
            continue
        for prevNick in prevNickArrs:
            if (compareArrsWthoutRegister(prevNick, nickArr)):
                prevNickArrs.append(nickArr)
                continue
        # если здесь, то не было одинаковых
        # получаем результат   
        result, indexFIOs = compareNickAndFIOs(group, nickArr, FIOs)
        # Если результат не Not exist - возвращаем результат
        if (result != errorState.NotExist):
            return result, indexFIOs
        indexFIOs=[]
    # если здесь, то не нашли
    return errorState.NotExist, indexFIOs

# функция, которая проставляет посещения
def setActualAttendance(groups, group, googleSheetInfoArray, indexFIO):
    # проставляем посещаемость
    googleSheetInfoArray[groups.index(group)].setAttendanceArrayByIndex(indexFIO)

# заменить в результате все индексы ФИО на ФИО
def changeIndexOfFIOsResultToFIOs(groups, result, googleSheetInfoArray):
    # get group from result
    group=result[0]
    # get FIO from result
    FIOs=result[1]
    # For all FIOs get from index - FIO
    for indexFIO  in range(len(FIOs)):
        # заменяем индекс ФИО на ФИО
        FIOs[indexFIO]=googleSheetInfoArray[groups.index(group)].getArrayOfPartsFIOByIndex(FIOs[indexFIO])
    result[1]=FIOs
    return result

    
    
# from ['group', [fio, fio]] set attendance to googleSheetInfoArray
def setAttendanceByResult(groups, results, googleSheetInfoArray):
        group = results[0][0]
        indexFIO=results[0][1][0]
        if (googleSheetInfoArray[groups.index(group)].getAttendanceArrayByIndex(indexFIO)!=0):
            return False
        else:
            googleSheetInfoArray[groups.index(group)].setAttendanceArrayByIndex(indexFIO)  
            return True
 
# TODO пока что возвращаем, но возможно лучше здесь же проставлять посещаемость, записывать ошибки и предупреждения
# основная функция поиска ника серди всех групп и всех фамилий
def findNickFromGroupAndFIO(groups, googleSheetInfoArray, nick):
    isCompareButNotEqual = False # для случая недостаточной уникальности
    isExistGroup = False # если группа существует
    results=[] # содержит группу и ФИО

    # пробег по всем группам
    for indexGroup in range(len(groups)):
        result, indexFIOs = findFIOfromFIOsToNick(groups[indexGroup], 
        nick,
        googleSheetInfoArray[indexGroup].getArrayOfPartsFIOs()
        )
        # если не уникален
        if (result==errorState.NotUnique):
            # clear all, that we have before and set not unique result
            results=[groups[indexGroup], indexFIOs]
            # convert result to string
            results = changeIndexOfFIOsResultToFIOs(groups, results, googleSheetInfoArray)
            return  getErrorOrWarning(errorState.NotUnique, nick, results), googleSheetInfoArray
        
        # Если резльтат успешное совпадение, то добавляем в конец
        if (result==successState.SuccessfulCompare):
            results.append([groups[indexGroup], indexFIOs])
            
        # Если резльтат "уникально и совпало, но не равно"
        if (result==warningState.CompareButNotEqual):
            isCompareButNotEqual=True
            results.append([groups[indexGroup], indexFIOs])
            
        if (result!=errorState.UnknownGroup):
            isExistGroup = True
   
    # если ровно одно совпадение
    if (len(results)==1):      
        # проставляем посещаемость
        # если посещаемость уже была проставлена
        if (setAttendanceByResult(groups, results, googleSheetInfoArray) == False):
            results=changeIndexOfFIOsResultToFIOs(groups, results[0], googleSheetInfoArray)
            resultWarnings.append(getErrorOrWarning(warningState.AlreadySetAttendance, nick, results))  
        else:
            # преобразум все индексы ФИО в ФИО
            results=changeIndexOfFIOsResultToFIOs(groups, results[0], googleSheetInfoArray)
        
        # случаи равенства
        if (isCompareButNotEqual):
            resultWarnings.append(getErrorOrWarning(warningState.CompareButNotEqual, nick, results))
            
        return

    for indexResult in range(len(results)):
        results[indexResult]=changeIndexOfFIOsResultToFIOs(groups, results[indexResult], googleSheetInfoArray)      
    
    # если не найдено совпадений
    if (len(results)<=0):
        # если группа существует
        if (isExistGroup):
            resultErrors.append(getErrorOrWarning(errorState.NotExist, nick, results))
        # если же не существует
        else:
            resultErrors.append(getErrorOrWarning(errorState.UnknownGroup, nick))
    # если найдено больше двух совпадений (поиск по двум группам)
    else:
        resultErrors.append(getErrorOrWarning(errorState.NotUniqueByGroup, nick, results))

# TODO функция формирования для группы объекта класса GoogleSheetInfo 

    
# функция, которая записывает информацию из googleSheet в массив класса GoogleSheetInfo - возвращает этот массив
# Причем, при записи ФИО сразу преобразует в формат частей ФИО
# также заносит все никнеймы в гугл таблицу - принимает массивы
# date - дата, по которой и будет происходить запись
def parseGoogleSheet(date, groups):
    # массив данных
    googleSheetInfoArray=[]
    
    
    # получаем данные для каждой группы
    for index in range(len(groups)):
        # TODO получаем массив всех данных - лист Google sheet, соответствующий группе
        googleSheetArray = []
        
        # TODO функция  получения всех студентов
        arrayOfPartsFIOs = []
        
        # Функция получения позиции начала списка по дате и группе
        positionInGoogleList = []
        
        
        # TODO Фнукция получения массива посещаемости по размеру массива студентов и поизиции
        attendanceArray=[]
        
        # TODO заносим данные в список
        #googleSheetInfoArray.append(googleSheetInfo(groups[index], positionInGoogleList, arrayOfPartsFIOs, attendanceArray))
    
    return googleSheetInfoArray

# функция, которая проставляет новую информацию по посещениям
def setActualAttendance(groups, googleSheetInfoArray, nicks):
    # Предупреждения и ошибки
    resultWarnings=[]
    resultErrors=[]
    
    for indexNick in range(len(nicks)):
        # в качестве результата принимаем строку ошибки либо пустую строку, если все хороошо
        findNickFromGroupAndFIO(groups, googleSheetInfoArray, nicks[indexNick])
    return resultWarnings, resultErrors
        



# Ппринимает дату и массив никнеймов - выполняет все действия с гугл таблицей - начиная от получения данных, заканчивая их записью
def getAndSetGoogleSheet(date, nicks):
    # TO DO: Функция получения всех групп
    groups=[]
    
    # DELETE получаем группы
    groups=['в4933', '4933']
    
    # Получаем массив данных по дате:
    googleSheetInfoArray=parseGoogleSheet(date, groups)
    
    # проставляем посещаемость по никнеймам
    resultErrorsAndWarnings, googleSheetInfoArray=setActualAttendance(groups, googleSheetInfoArray, nicks)
    
    # записываем результат в google таблицу
    setAttendanceGoogleSheet(googleSheetInfoArray)
    
    # возвращаем массив ошибок и предупреждений
    return resultErrorsAndWarnings



#  Основная Функция
def setAttendanceInGoogleSheet(nicks):
    return ''
    # получаем информацию из googleSheet
    
    # Преобразуем информацию (возможнос в предыдущей функции)
    
    # возращаем массив ошибок и массив предупреждений, а также массив результата - обновлено, уже было обновлено
    

# DELETE NICKS, BUT ON DISCORD STAGE
nicks=['ПетровАндрdfB@49#3$3№ейВлад23432имирович', 'игор4933']

setActualAttendance(groups, googleSheetInfoArray, nicks)

print(resultWarnings)
print(resultErrors)
print(googleSheetInfoArray[0].getAttendanceArray())
print(googleSheetInfoArray[1].getAttendanceArray())    
    
#Good -----------
#groups=['в4933', '4933']

#googleSheetInfoArray=[]
#googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Семенов', 'Павел', 'Александрович']], [0, 0]))

#googleSheetInfoArray.append(GoogleSheetInfo('4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Коваленко', 'Игорь']], [0, 0]))
#nicks=['ПетровАндрdfв@49#3$3№ейВлад23432имирович', 'игор4933']


#Not unique by qroups -----------
#groups=['в4933', '4933']

#googleSheetInfoArray=[]
#googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Семенов', 'Павел', 'Александрович']], [0, 0]))

#googleSheetInfoArray.append(GoogleSheetInfo('4933', ['A', 1], [['Петров', 'Андрвей', 'Владимирович'], ['Коваленко', 'Игорь']], [0, 0]))
#nicks=['ПетровАндрdfв@49#3$3№ейВлад23432имирович', 'игор4933']

# Not Unique and not unique by qroups - check only situation, when not unique (it's worse)-----------------
#groups=['в4933', '4933']

#googleSheetInfoArray=[]
#googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Петров', 'Андрей', 'Владимирович']], [0, 0]))

#googleSheetInfoArray.append(GoogleSheetInfo('4933', ['A', 1], [['Петров', 'Андрвей', 'Владимирович'], ['Коваленко', 'Игорь']], [0, 0]))
#nicks=['ПетровАндрdfв@49#3$3№ейВлад23432имирович', 'игор4933']

# bad group  ----------------------
#groups=['г4933', 'д4933']

#googleSheetInfoArray=[]
#googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Петров', 'Андрей', 'Владимирович']], [0, 0]))

#googleSheetInfoArray.append(GoogleSheetInfo('д4933', ['A', 1], [['Петров', 'Андрвей', 'Владимирович'], ['Коваленко', 'Игорь']], [0, 0]))
#nicks=['ПетровАндрdfв@49#3$3№ейВлад23432имирович', 'игорд4933']


# not exist  ----------------------
#groups=['д4933', 'в4933']

#googleSheetInfoArray=[]
#googleSheetInfoArray.append(GoogleSheetInfo('д4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Петров', 'Андрей', 'Владимирович']], [0, 0]))

#googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрвей', 'Владимирович'], ['Коваленко', 'Игорь']], [0, 0]))
#nicks=['ПетровАндрdfв@49#3$3№ейВлад23432имирович', 'игорв4933']

# !!! Порядок group Четко соответствует порядку Google Sheet (это будет автоматически реализовано при считывании)




#nicks=['dfв@49#3$3№петров андрей владимирович', 'игор4933']
#nicks=['dfв@49#3$3№петровАндрейВладимирович', 'игор4933']
#nicks=['Петров Андрей в4933', 'игор4933']
# проставляем посещаемость по никнеймам

