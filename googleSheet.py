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

NOT_EXIST_SIMILAR=False

# notExistSimilar - определяет, не существуют ли группы, которые можно получить из других групп
# если существуют - False (более строгий), иначе True. По умолчанию - существуют
# Например, существует ли группа M911 и 911 или 4933 и 933
# Пример проблемы: ПетровМаксим911 -> Петров Макси 911? или Петров максим 911? А если предложить, что оба таких человека бы существовали...
# Или человек с именем Надыргулов Иль9  написал в Шутку: Надыргулов Иль9 а потом написал 433, а существуют группы 9433 и 433
notExistSimilar=NOT_EXIST_SIMILAR

class namePersonState(enum.Enum):
        UnknownName = 1 # не удалось получить имя
        NotExist = 2 # не нашли совпадения
        NotUnique = 3 # не уникален
        UniqueButNotEnough = 4 # мало информации, но уникален - Петров А или Петров
        # следующий вариант пока не проверяется
        #differentVariantsByGroup = 5 # есть группы 4933 и 933 и нашелся человек, который есть в обоих группах - но будет добавлен в 4933
        SuccessfulCompare = 6 # значение удачного выполнения
        
        
        # UnknownFIO = 2 # ФИО некорректно - нужно ли для преподавателя?
  
 
class groupState(enum.Enum):
        SuccessGroup = 1 # группа успешно извлечена
        UnknownGroup = 2 # не удалось извлечь группу

   
        # С помощью find можно искать относительно начала, то
        
        # Наименование, 2 символа
        # Наименование, 1 символ
        # Наименование
        # 2 Наименования и 1 символ
        # 2 Наименования
        # 3 Наименования
def getErrorOrWarning(enumValue, nick):
    return {
        enumValue == groupState.UnknownGroup: "Error: " + nick + " have wrong group or group doesn't exists in google sheet",
        enumValue == namePersonState.NotExist: "Error: " + nick + ' not Exist in google sheet',
        enumValue == namePersonState.NotUnique: "Error: " + nick + ' not unique in google sheet',
        enumValue == namePersonState.UniqueButNotEnough: "Warning: " + nick + ' have bad nick, but we find an unique FIO',     
        enumValue == namePersonState.SuccessfulCompare or enumValue == groupState.SuccessGroup: ''
    }[True]    
    
#def compareToErrorAndWarnings(enumValue, nick):   
#    match enumValue:
#        case groupState.UnknownGroup:
#            return "Error: " + nick + " have wrong group or group doesn't exists in google sheet"            
#        case namePersonState.NotExist:
#            return "Error " + nick + ' not Exist in google sheet'
#        case namePersonState.NotUnique:
#            return "Error: " + nick + ' not unique in google sheet'
#        case UniqueButNotEnough:
#            return "Warning: " + nick + ' have bad nick, but we set '            
    
        
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


# привести к пробелам знаки
def turnToSpacesSigns(stroka):
    return re.sub(r'[^a-zA-Zа-яА-Я0-9]', " ",  stroka)
    
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
    # russian case
    # T=T, но т!=t!
    if (symbGroup == 'т'):
        return 't'
    #  В=В, но  в!=b
    if (symbGroup == 'в'):
        return 'b'
        
    if (symbGroup == 'р'):
        return 'r'
   
    # to Up register
    symbGroupConverted = symbGroup.upper()
     # replace is too long
    #group=group.replace("С", "C")
   
    # массивы русских и английских эквивалент
    arrayRussian=['Т', 'В', 'К', 'М', 'Е', 'С', 'Х', 'Р', 'У', 'О', 'А']
    arrayEnglish=['T', 'B', 'K', 'M', 'E', 'C', 'X', 'P', 'Y', 'O', 'A']
    
    for index in range(len(arrayRussian)):
        if (symbGroupConverted==arrayRussian[index]):
            return arrayEnglish[index]
    # если же не особый случай, то возвращаем конвертированный символ
    return symbGroupConverted
    
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
    # заменяем все символы на пробелы
    stroka=turnToSpacesAllWthoutName(stroka)
    # все символы начала приводим к верхнему регистру (т.е. после пробелов)
    stroka=beginOfWordToUpRegister(stroka)
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
    return resultArr;
    
        
    
# получить группу из имени          
# на вход - получаем стандартную группу, nick и nick без спец. символов, массив соответствия индексов последних двух
def getNickWthoutGroupFromNick(group, nick, parseNick, indices):  
    # получаем индекс начала для группы - группа обязательно должна содержать числа, иначе может возникнуть очень много неточностей парсинга
    startDigitGroup=getIndexFirstDigit(group)
    if (startDigitGroup<0):
        return groupState.UnknownGroup
    
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
    return groupState.UnknownGroup

# получаем группу, которая соответствует и строку, которая записана в качестве группы в нике
# [исходная группа, ник] or groupState.UnknownGroup

def getGroupAndNickWthoutGroup(groups, nick):
    # получаем массив для случая удаления всех знаков nick
    indices=getIndicesNickWithoutSignes(nick)
    # получаем никнейм без спец. символов и пробелов
    parseNick = delSigns(nick)
    # для каждой группы - пытаемся сопоставить ее
    for index in range(len(groups)):
        nickWthoutGroup=getNickWthoutGroupFromNick(groups[index], nick,  parseNick, indices)
        # если группу получили (она равна искомой)
        if (nickWthoutGroup!=groupState.UnknownGroup):
            return [groups[index], nickWthoutGroup]
    # если мы не нашли группу
    return groupState.UnknownGroup

# TO DO: можно также перед всеми действиями (но группа должна быть удалена) если начало дальше идет русская буква,
#, то мы приводим её к верхнему регистру



# сопоставляем ФИО и полученные фрагменты никнейма
# принимаем FIO и Nick в формате массивов
def compareFIOandNick(FIOArr, nickArr):
    # создаем массив заполненный нулями - нальчальное значение эквиваленты сравнения
    compareResult = [[0] * len(nickArr) for i in range(len(FIOArr))]
    for indexFIO in range(len(FIOArr)):
        for indexNick in range(len(nickArr)):
            # начинается ли FIO со строки nick - сравнение в одинаковом регистре (необзательно приведение)
            if (re.match(nickArr[indexNick].lower(), FIOArr[indexFIO].lower())!=None):
                compareResult[indexFIO][indexNick]=1
    # проверяем - существует ли комбинация, при которой возможна идентичность        
    return isExistFioCombination(compareResult)
    
 
# Случаи корректности Петр Петров Петров А - недостаточно данных для однозначной идентификации (особые случаи)
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
   
   
# Функция, которая пытается найти сопоставления путем приведения к Верхнему регистру начальных символов, а остальных к нижнему регистру
def getPartsFormNickSpaceAlgoritm(nick):
    # приводим к пробелам все знаки
    nick=turnToSpacesSigns(nick)
    # все символы начала приводим к верхнему регистру (т.е. после пробелов), остальные к нижнему
    nick=beginOfWordToUpRegister(nick, True)
    # убираем все ненужное (знаки, спец. символы, пробелы) - достаточно было только пробелы
    nick=delSigns(nick)
    # Получаем составные части никнейма
    return parseNameToParts(nick)
    
    
# Функция, которая пытается найти сопоставления путем приведения к  Верхнему регистру начальных символов и слития
def getPartsFormNickSequenceAlgoritm(nick):
    # все символы начала приводим к верхнему регистру (т.е. после пробелов)
    nick=beginOfWordToUpRegister(nick)
    # убираем все ненужное (знаки, спец. символы, пробелы) - достаточно было только пробелы
    nick=delSigns(nick)
    # Получаем составные части никнейма
    return parseNameToParts(nick)


#  
   
   
# Функция сопоставления никнейма по массиву фамилий
def compareNickAndFIOs(group, nickArr, googleSheetInfoArray):    
    resultArray=[]
    # Получаем для данной группы массив массивов составных частей ФИО
    FIOs=googleSheetInfoArray[groups.index(group)].getArrayOfPartsFIOs()  
    # Сопостоавляем для каждого ФИО
    for indexFIO in range(len(FIOs)):
        #  если для ФИО не проставлена посещаемость
        if (googleSheetInfoArray[groups.index(group)].getAttendanceArrayByIndex(indexFIO)==0):
            # если никнейм существует - добавляем в конец рассматриваемого массива
            if (compareFIOandNick(FIOs[indexFIO], nickArr)):
                resultArray.append(indexFIO)
    # рассматриваем различные случаи результата
    # если единственное -> уникально, записываем его
    if (len(resultArray)==1):
        googleSheetInfoArray[groups.index(group)].setAttendanceArrayByIndex(resultArray[0])
        # если недостаточно данных
        return (namePersonState.SuccessfulCompare, googleSheetInfoArray)
    elif (len(resultArray)==0):
        return (namePersonState.NotExist, googleSheetInfoArray)
    else:
        return (namePersonState.NotUnique, googleSheetInfoArray) 
 
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
def findFIOfromFIOsToNick(groups, googleSheetInfoArray, nick):  
    # получаем группу и никнейм с вырезанной группой
    groupAndNick=getGroupAndNickWthoutGroup(groups, nick)

    # если группа неизвестная
    if (groupAndNick == groupState.UnknownGroup):
        return (groupState.UnknownGroup, googleSheetInfoArray)
    
    print(nick)
        # извлекаем соответствующую группу
    group=groupAndNick[0]
    print(group)
    # извлекаем никнейм без группы из самого массива
    parseNick=groupAndNick[1]
    print(parseNick)
    
    # получаем никнейм по первому алгоритму
    nickArr = getPartsFormNickSpaceAlgoritm(parseNick)
    print(nickArr)
    # получаем результат   
    result, googleSheetInfoArray = compareNickAndFIOs(group, nickArr, googleSheetInfoArray)

    # Если результат не Not exist - возвращаем результат
    if (result != namePersonState.NotExist):
        return result, googleSheetInfoArray
    
    nickArrPrev=nickArr;
    # пробуем второй вариант алгоритма     
    nickArr = getPartsFormNickSequenceAlgoritm(parseNick)
    print(nickArr)
    # если полученные варианты равны, то возвращаем имеющийся результат
    if (compareArrsWthoutRegister(nickArrPrev, nickArr)):
        return result, googleSheetInfoArray
    
    # получаем результат   
    result, googleSheetInfoArray = compareNickAndFIOs(group, nickArr, googleSheetInfoArray)

    # возвращаем результат
    return result, googleSheetInfoArray
   
   # В случае, если алогиритмов будет много, то их можно занести в цикл, который будет надстройкой над втроым случаем...
   

    

    
   
# TODO Функция, которая проставляет посещемость для никнейма по заданной группе, никнейму и массиву частей ФИО
  
  
  
# TODO Функция, которая для данного никнейма определяет его группу и запускает функцию проставления посещемости для никнейма
  
  

# TODO функция формирования для группы объекта класса GoogleSheetInfo 



# TODO функция получения всех групп
def getGroupsFromGoogleSheet():
    return ''
    
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
    resultWarnings=[]
    resultErrors=[]
    for indexNick in range(len(nicks)):
        result, googleSheetInfoArray = findFIOfromFIOsToNick(groups, googleSheetInfoArray, nicks[indexNick])
        if (result==namePersonState.NotExist):
            result, googleSheetInfoArray = findFIOfromFIOsToNick(groups, googleSheetInfoArray, nicks[indexNick])
        
        if (result == namePersonState.SuccessfulCompare):
            continue
        elif (result == namePersonState.UniqueButNotEnough):
            resultWarnings.append(getErrorOrWarning(result, nicks[indexNick]))
        else:
            resultErrors.append(getErrorOrWarning(result, nicks[indexNick]))
   
    return resultWarnings, resultErrors, googleSheetInfoArray
        

# функция, которая проставляет новую посещаемость в гугл таблице
def setAttendanceGoogleSheet(googleSheetInfoArray):
    return ''
    
    
    

# Ппринимает дату и массив никнеймов - выполняет все действия с гугл таблицей - начиная от получения данных, заканчивая их записью
def getAndSetGoogleSheet(date, nicks):
    # TO DO: Функция получения всех групп
    groups=[]
    
    # DELETE получаем группы
    groups=['4933', 'M911']
    
    # сортируем группы по длине строки, начиная от большей строки (иначе если будут группы M911 и 911,
    # то для 'Петров M911' если 911 первее - то будет ошибочно воспринято, что Петров из 911 группы)
    groups=groups.sort(key=sortByLength, reverse=True)
    
    # Получаем массив данных по дате:
    googleSheetInfoArray=parseGoogleSheet(date, groups)
    
    # проставляем посещаемость по никнеймам
    resultWarnings, resultErrors, googleSheetInfoArray=setActualAttendance(groups, googleSheetInfoArray, nicks)
    
    # записываем результат в google таблицу
    setAttendanceGoogleSheet(googleSheetInfoArray)
    
    # возвращаем массив ошибок и предупреждений
    return resultWarnings, resultErrors
    


groups=['в4933', '4933']

googleSheetInfoArray=[]
googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Семенов', 'Павел', 'Александрович']], [0, 0]))

googleSheetInfoArray.append(GoogleSheetInfo('4933', ['A', 1], [['Петров', 'Борис', 'Аристархович'], ['Коваленко', 'Игорь']], [0, 0]))

nicks=['dfв@49#3$3№петров андрей владимирович', 'игор4933']
#nicks=['dfв@49#3$3№петровАндрейАладимирович', 'игор4933']

# проставляем посещаемость по никнеймам
resultWarnings, resultErrors, googleSheetInfoArray=setActualAttendance(groups, googleSheetInfoArray, nicks)

print(resultWarnings)
print(resultErrors)
print(googleSheetInfoArray[0].getAttendanceArray())
print(googleSheetInfoArray[1].getAttendanceArray())
