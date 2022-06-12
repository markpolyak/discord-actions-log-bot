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

class namePersonState(enum.Enum):
        UnknownName = 1 # не удалось получить имя
        NotExist = 2 # не нашли совпадения
        NotUnique = 3 # не уникален
        UniqueButNotEnough = 4 # мало информации, но уникален - Петров А или Петров
        SuccessfulCompare = 5 # значение удачного выполнения
        
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

# получить индекс первого числа группы
def getIndexFirstDigit(group):
    for index in range(len(group)):
        if (group[index].isdigit()):
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
    
# получить группу из имени            
def getGroupFromNick(group, nick):
    # получаем индекс начала для группы
    startDigitGroup=getIndexFirstDigit(group)
    if (startDigitGroup<0):
        return groupState.UnknownGroup
    # для никнейма
    startDigitNick=getIndexFirstDigit(nick)
    # если нету чисел
    if(startDigitGroup<0 or startDigitNick<0):
        return groupState.UnknownGroup
    # если в никнейме не помещется искомая группа слева
    if (startDigitNick-startDigitGroup<0):
        return groupState.UnknownGroup
        
    # если в никнейме не помещется искомая группа справа
    if (len(nick)-startDigitNick<len(group)-startDigitGroup):
        return groupState.UnknownGroup
     
    # извлекаем срезом символа для никнейма
    return nick[startDigitNick-startDigitGroup:startDigitNick+(len(group)-startDigitGroup)]

# получаем группу, которая соответствует и строку, которая записана в качестве группы в нике
# [исходная группа, группа в нике] or groupState.UnknownGroup
def getGroupFormGroupsForNick(groups, nick):
    for index in range(len(groups)):
        groupNick=getGroupFromNick(groups[index], nick)
        # если группу получили и она равна искомой
        if (groupNick!=groupState.UnknownGroup and compareFormatSymb(groups[index], groupNick)):
            return [groups[index], groupNick]
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
   
   
# производит поиск по всем ФИО
# Принимает на вход массив массив групп, массив класса данных, никнейм
# Возвращает результат обработки, массив значений расстановки оценок
# результатом возвращает 
def findFIOfromFIOsToNick(groups, googleSheetInfoArray, nick, isLower=False):
    # приводим к пробелам
    nick=turnToSpacesSigns(nick)
    print(nick)
    # все символы начала приводим к верхнему регистру (т.е. после пробелов)
    parseNick=beginOfWordToUpRegister(nick, isLower)
    # приводим все, что не в начале, к нижнему регистру
    
    print(parseNick)
    # убираем все ненужное (знаки, спец. символы, пробелы)
    parseNick=delSigns(parseNick)
    print(parseNick)
    # получаем группу
    groupArr=getGroupFormGroupsForNick(groups, parseNick)
    print(groupArr)
    # если группа неизвестная
    if (groupArr == groupState.UnknownGroup):
        return (groupState.UnknownGroup, googleSheetInfoArray)

    # извлекаем соответствующую группу
    group=groupArr[0]
    # извлекаем группу из самого массива
    groupNick=groupArr[1]
    
    #убираем группу из массива
    parseNick=parseNick.replace(groupNick, " ")
    
    # все символы начала приводим к верхнему регистру (т.е. после пробелов)
    parseNick=beginOfWordToUpRegister(nick)
    print(parseNick)
    # Получаем составные части никнейма
    parseNick=parseNameToParts(parseNick)
    print(parseNick)
    
    resultArray=[]
    
    FIOs=googleSheetInfoArray[groups.index(group)].getArrayOfPartsFIOs()  
    for indexFIO in range(len(FIOs)):
        #  если для ФИО не проставлена посещаемость
        if (googleSheetInfoArray[groups.index(group)].getAttendanceArrayByIndex(indexFIO)==0):
            # если никнейм существует - добавляем в конец рассматриваемого массива
            if (compareFIOandNick(FIOs[indexFIO], parseNick)):
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
            result, googleSheetInfoArray = findFIOfromFIOsToNick(groups, googleSheetInfoArray, nicks[indexNick], True)
        
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
    


groups=['в4931', '4933']

googleSheetInfoArray=[]
googleSheetInfoArray.append(GoogleSheetInfo('в4933', ['A', 1], [['Петров', 'Андрей', 'Владимирович'], ['Семенов', 'Павел', 'Александрович']], [0, 0]))

googleSheetInfoArray.append(GoogleSheetInfo('4933', ['A', 1], [['Петров', 'Борис', 'Аристархович'], ['Коваленко', 'Игорь']], [0, 0]))

nicks=['df@49#3$3№петровАндрейВладимирович', 'игор4933']

# проставляем посещаемость по никнеймам
resultWarnings, resultErrors, googleSheetInfoArray=setActualAttendance(groups, googleSheetInfoArray, nicks)

print(resultWarnings)
print(resultErrors)
print(googleSheetInfoArray[0].getAttendanceArray())
print(googleSheetInfoArray[1].getAttendanceArray())
