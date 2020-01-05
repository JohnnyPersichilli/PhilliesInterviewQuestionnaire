def is_palindrone(s):
    end = len(s)-1                  #makes looping variable starting at end of s
    palindroneBool = True           #boolean to determine if true or fals
    for x in range(0, int(len(s)/2)):   #loop through half the string(can cast as int 
                                        #because half value will either be the same index or the indexs will cross at this point)
        if s[x] != s[end]:              #if any of the letters differ its not a palindrone, return false and break
            palindroneBool = False
            break
        end -=1                         #decrement end and increment x
    return palindroneBool

print(is_palindrone("racecar"))
print(is_palindrone("aracecara"))
print(is_palindrone("a"))
print(is_palindrone("ada"))
print(is_palindrone("av"))
print(is_palindrone("racr"))